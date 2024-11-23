from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

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
    def resume(self, state: S) -> Iterator[C]:
        """Returns an iterator of commands to resume a process from a given state.

        Parameters
            state: State of the current process

        Returns
            An iterator of commands to act on.
        """
        pass

    @abstractmethod
    def react(self, state: S, event: E) -> Iterator[C]:
        """Returns an iterator of commands as a reaction to an event.

        Parameters
            state: State of the current process
            event: Event currently being processed

        Returns
            An iterator of commands to act on.
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

    def __init__(
        self,
        select_event: Callable[[EI], EO | None],
        convert_command: Callable[[CO], CI],
        p: IProcess[EO, CO, S],
    ) -> None:
        """Convert Commands/Events into output variants.

        Parameters:
            select_event: A callaback that converts input Events to output Events.
            convert_command: A callback that converts input Commands to output Commands.
        """
        self._p = p
        self._select_event = select_event
        self._convert_command = convert_command

    def build(self) -> IProcess[EI, CI, S]:
        """Convert Commands/Events into output variants.

        Returns:
            A new Process that can given input Events/Commands return new output variants.
        """
        InnerEI = TypeVar("InnerEI")
        InnerEO = TypeVar("InnerEO")
        InnerCO = TypeVar("InnerCO")
        InnerCI = TypeVar("InnerCI")
        InnerS = TypeVar("InnerS")

        class InternalProcess(IProcess[InnerEI, InnerCI, InnerS]):
            def evolve(self, state: InnerS, event: InnerEI) -> InnerS:
                new_event = self._event_converter(event)
                if new_event is None:
                    return state
                return self._process.evolve(state, new_event)

            def resume(self, state: InnerS) -> Iterator[InnerCI]:
                yield from map(self._command_converter, self._process.resume(state))

            def react(self, state: InnerS, event: InnerEI) -> Iterator[InnerCI]:
                new_event = self._event_converter(event)
                if new_event is None:
                    yield from []
                else:
                    yield from map(
                        self._command_converter, self._process.react(state, new_event)
                    )

            def initial_state(self) -> InnerS:
                return self._process.initial_state()

            def is_terminal(self, state: InnerS) -> bool:
                return self._process.is_terminal(state)

            def __init__(
                self,
                process: IProcess[InnerEO, InnerCO, InnerS],
                event_converter: Callable[[InnerEI], InnerEO | None],
                command_converter: Callable[[InnerCO], InnerCI],
            ) -> None:
                self._process = process
                self._event_converter = event_converter
                self._command_converter = command_converter

        return InternalProcess(self._p, self._select_event, self._convert_command)


def process_collect_fold(
    proc: IProcess[E, C, S], state: S, events: list[E]
) -> Iterator[C]:
    new_state = state
    while len(events) > 0:
        event = events.pop(0)
        new_state = proc.evolve(state, event)
        commands = proc.react(new_state, event)
        yield from commands


PS = TypeVar("PS")
DS = TypeVar("DS")


class ProcessCombineWithDecider(Generic[E, C, PS, DS]):
    """Combine a Processor with a Decider together."""

    def __init__(self, proc: IProcess[E, C, PS], decider: Decider[E, C, DS]) -> None:
        """Combine a Process and a Decider into a single Decider.

        Parameters:
            proc: The process being combined.
            decider: The decider its being combined with.
        """
        self._proc = proc
        self._decider = decider

    def build(self) -> Decider[E, C, tuple[DS, PS]]:
        """Combine a Process and a Decider into a single Decider.

        Results:
            A single Decider.

        Note: This function's generated `decide` function deviates from the model used by the original material. `decide` in this code takes a command and state tuple.

        For each command issued this code will do the following:

        #. create a command list `commands` initialized as [commands]
        #. create a event list `events` initialized as []
        #. run `decider.decide` on a popped entry from commands
        #. append the results to events array
        #. create a copy of state and run `decider.evolve` on it
        #. run `process.react` to generate new commands appended to the commands list.
        #. run `process.evolve` on each new event.
        #. loop back to 2 with remaining commands and the copy of decider's state.
        #. one commands is empty, return all events collected during the above.

        The state of neither process nor decider is actually changed by `decide`. You will still need to call `evolve` to reach the final end states.
        """

        InnerE = TypeVar("InnerE")  # Event type for the inner class
        InnerC = TypeVar("InnerC")  # Command type for the inner class
        InnerPS = TypeVar("InnerPS")  # Process state type for the inner class
        InnerDS = TypeVar("InnerDS")  # Decider state type for the inner class

        class InternalDecider(Decider[InnerE, InnerC, tuple[InnerDS, InnerPS]]):
            def __init__(
                self,
                process: IProcess[InnerE, InnerC, InnerPS],
                decision: Decider[InnerE, InnerC, InnerDS],
            ):
                self._proc = process
                self._decider = decision

            def decide(
                self, command: InnerC, state: tuple[InnerDS, InnerPS]
            ) -> Iterator[InnerE]:

                # NOTE: This is a deviation.
                decider_state = state[0]
                commands = [command]
                while len(commands) > 0:
                    command = commands.pop(0)
                    new_events = list(self._decider.decide(command, decider_state))
                    # NOTE: This is a deviation.
                    for event in new_events:
                        decider_state = self._decider.evolve(decider_state, event)
                    new_commands = process_collect_fold(
                        self._proc, state[1], new_events.copy()
                    )
                    commands.extend(new_commands)
                    yield from new_events

            def evolve(
                self, state: tuple[InnerDS, InnerPS], event: InnerE
            ) -> tuple[InnerDS, InnerPS]:
                return (
                    self._decider.evolve(state[0], event),
                    self._proc.evolve(state[1], event),
                )

            def initial_state(self) -> tuple[InnerDS, InnerPS]:
                return (self._decider.initial_state(), self._proc.initial_state())

            def is_terminal(self, state: tuple[InnerDS, InnerPS]) -> bool:
                return self._decider.is_terminal(state[0]) and self._proc.is_terminal(
                    state[1]
                )

        return InternalDecider(self._proc, self._decider)
