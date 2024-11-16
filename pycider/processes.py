from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, Sequence, TypeVar

from pycider.deciders import Decider

E = TypeVar("E")
C = TypeVar("C")
S = TypeVar("S")


class IProcess(ABC, Generic[E, C, S]):
    """Prototype for Process implementations.

    All Processes should be implemented using this prototype.
    """

    @abstractmethod
    def evolve(self, state: S, event: E) -> S:
        """Returns an updated state based on the current event.

        Paramters
            state: State of the current process
            event: Event generated from commands procesed

        Returns
            An updated state.
        """
        pass

    @abstractmethod
    def resume(self, state: S) -> Sequence[C]:
        """Returns a sequence of commands to resume a process from a given state.

        Parameters
            state: State of the current process

        Returns
            An sequence of commands to act on.
        """
        pass

    @abstractmethod
    def react(self, state: S, event: E) -> Sequence[C]:
        """Returns a sequence of commands as a reaction to an event.

        Parameters
            state: State of the current process
            event: Event currently being processed

        Returns
            A sequence of commands to act on.
        """
        pass

    @abstractmethod
    def initial_state(self) -> S:
        """Returns the starting state for a process.

        Returns
            A state representing the start of a process.
        """
        pass

    @abstractmethod
    def is_terminal(self, state: S) -> bool:
        """Returns if a process's state is terminal.

        Parameters
            state: State of the current process

        Returns
            A boolean indicating if a process has run till completion.
        """
        pass


EI = TypeVar("EI")
CI = TypeVar("CI")
EO = TypeVar("EO")
CO = TypeVar("CO")


class ProcessAdapt(Generic[EI, CI, S, EO, CO]):
    """Adapt process Commands / Events into new output Commands and Events."""

    @classmethod
    def adapt(
        cls,
        select_event: Callable[[EI], EO | None],
        convert_command: Callable[[CO], CI],
        p: IProcess[EO, CO, S],
    ) -> IProcess[EI, CI, S]:
        """Convert Commands/Events into output variants.

        Parameters:
            select_event: A callaback that converts input Events to output Events.
            convert_command: A callback that converts input Commands to output Commands.

        Returns:
            A new Process that can given input Events/Commands return new output variants.
        """

        class InternalProcess(IProcess[EI, CI, S]):
            def evolve(self, state: S, event: EI) -> S:
                new_event = select_event(event)
                if new_event is None:
                    return state
                return p.evolve(state, new_event)

            def resume(self, state: S) -> Sequence[CI]:
                return list(map(convert_command, p.resume(state)))

            def react(self, state: S, event: EI) -> Sequence[CI]:
                new_event = select_event(event)
                if new_event is None:
                    return []
                return list(map(convert_command, p.react(state, new_event)))

            def initial_state(self) -> S:
                return p.initial_state()

            def is_terminal(self, state: S) -> bool:
                return p.is_terminal(state)

        return InternalProcess()


def process_collect_fold(
    proc: IProcess[E, C, S], state: S, events: list[E]
) -> Sequence[C]:
    def loop(state: S, events: list[E], all_commands: list[C]):
        if len(events) == 0:
            return all_commands

        event = events.pop(0)
        new_state = proc.evolve(state, event)
        commands = proc.react(new_state, event)
        all_commands.extend(commands)
        return loop(new_state, events, all_commands)

    return loop(state, events, [])


PS = TypeVar("PS")
DS = TypeVar("DS")


class ProcessCombineWithDecider(Generic[E, C, PS, DS]):
    """Combine a Processor with a Decider together."""

    @classmethod
    def combine(
        cls, proc: IProcess[E, C, PS], decider: Decider[E, C, DS]
    ) -> Decider[E, C, tuple[DS, PS]]:
        """Combine a Process and a Decider into a single Decider.

        Parameters:
            proc: The process being combined.
            decider: The decider its being combined with.

        Results:
            A single Decider.

        Note: This function's generated `decide` function deviates from the model used by the original material. `decide` in this code takes a command and state tuple.

        For each command issued this code will do the following:
        1. create a command list `commands` initialized as [commands]
        2. create a event list `events` initialized as []
        2. run `decider.decide` on a popped entry from commands
        2. append the results to events array
        3. create a copy of state and run `decider.evolve` on it
        4. run `process.react` to generate new commands appended to the commands list.
        3. run `process.evolve` on each new event.
        4. loop back to 2 with remaining commands and the copy of decider's state.
        4. one commands is empty, return all events collected during the above.

        The state of neither process nor decider is actually changed by `decide`. You will still need to call `evolve` to reach the final end states.
        """

        class InternalDecider(Decider[E, C, tuple[DS, PS]]):
            def decide(self, command: C, state: tuple[DS, PS]) -> Sequence[E]:
                # NOTE: This is a deviation.
                decider_state = state[0]

                def loop(decider_state: DS, commands: list[C], all_events: list[E]):
                    if len(commands) == 0:
                        return all_events
                    command = commands.pop(0)
                    new_events = list(decider.decide(command, decider_state))
                    # NOTE: This is a deviation.
                    for event in new_events:
                        decider_state = decider.evolve(decider_state, event)
                    new_commands = process_collect_fold(
                        proc, state[1], new_events.copy()
                    )
                    commands.extend(new_commands)
                    all_events.extend(new_events)
                    return loop(decider_state, commands, all_events)

                return loop(decider_state, [command], [])

            def evolve(self, state: tuple[DS, PS], event: E) -> tuple[DS, PS]:
                return (decider.evolve(state[0], event), proc.evolve(state[1], event))

            def initial_state(self) -> tuple[DS, PS]:
                return (decider.initial_state(), proc.initial_state())

            def is_terminal(self, state: tuple[DS, PS]) -> bool:
                return decider.is_terminal(state[0]) and proc.is_terminal(state[1])

        return InternalDecider()
