from abc import ABC, abstractmethod
from typing import Generic, Sequence, TypeVar

from pycider.deciders import Command, Decider, Event, State

E = TypeVar("E")
C = TypeVar("C")
S = TypeVar("S")


class IProcess(ABC, Generic[E, C, S]):

    @abstractmethod
    def evolve(self, state: S, event: E) -> S:
        """Update the process state based on the current event.

        Paramters
            state: State of the current process
            event: Event

        Returns
            An sequence of commands to act on.
        """
        pass

    @abstractmethod
    def resume(self, state: S) -> Sequence[C]:
        """Resume to the next command from a starting state.

        Parameters
            state: State of the current process

        Returns
            An iterable set of commands to act on.
        """
        pass

    @abstractmethod
    def react(self, state: S, event: E) -> Sequence[C]:
        """React to an event by generating new commands.

        Parameters
            state: State of the current process
            event: Event being reacted to

        Returns
            A sequence of commands to act on.
        """
        pass

    @abstractmethod
    def initial_state(self) -> S:
        """Starting state for a process.

        Returns
            The base state to begin the process with
        """
        pass

    @abstractmethod
    def is_terminal(self, state: S) -> bool:
        """Checks if the current state is the end state for the process.

        Parameters
            state: State of the current process

        Returns
            A boolean indicating if a process is finished.
        """
        pass


class CatLightEventSwitchedOn(Event):
    pass


class CatLightEventWokeUp(Event):
    pass


class CatLightCommandWakeUp(Command):
    pass


class CatLightStateIdle(State):
    pass


class CatLightStateWakingUp(State):
    pass


class CatLight(IProcess[Event, Command, State]):
    def evolve(self, state: State, event: Event) -> State:
        match event:
            case CatLightEventSwitchedOn():
                return CatLightStateWakingUp()
            case CatLightEventWokeUp():
                return CatLightStateIdle()
            case _:
                return state

    def resume(self, state: State) -> Sequence[Command]:
        match state:
            case CatLightStateWakingUp():
                return [CatLightCommandWakeUp()]
            case _:
                return []

    def react(self, state: State, event: Event) -> Sequence[Command]:
        match state, event:
            case CatLightStateWakingUp(), CatLightEventSwitchedOn():
                return [CatLightCommandWakeUp()]
            case _:
                return []

    def initial_state(self) -> State:
        return CatLightStateIdle()

    def is_terminal(self, state: State) -> bool:
        return isinstance(state, CatLightStateIdle)


class Process(Generic[E, C, S]):
    @classmethod
    def adapt(
        cls, select_event, convert_command, p: IProcess[E, C, S]
    ) -> IProcess[E, C, S]:
        class AnonymousProcess(IProcess[E, C, S]):
            def evolve(self, state: S, event: E) -> S:
                event = select_event(event)
                if event is None:
                    return state
                return p.evolve(state, event)

            def resume(self, state: S) -> Sequence[C]:
                return list(map(convert_command, p.resume(state)))

            def react(self, state: S, event: E) -> Sequence[C]:
                event = select_event(event)
                if event is None:
                    return []
                return list(map(convert_command, p.react(state, event)))

            def initial_state(self) -> S:
                return p.initial_state()

            def is_terminal(self, state: S) -> bool:
                return p.is_terminal(state)

        return AnonymousProcess()


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

    @classmethod
    def combine(
        cls, proc: IProcess[E, C, PS], decider: Decider[E, C, DS]
    ) -> Decider[E, C, tuple[DS, PS]]:

        class AnonymousDecider(Decider[E, C, tuple[DS, PS]]):
            def decide(self, command: C, state: tuple[DS, PS]) -> Sequence[E]:
                def loop(commands: list[C], all_events: list[E]):
                    if len(commands) == 0:
                        return all_events
                    command = commands.pop(0)
                    new_events = list(decider.decide(command, state[0]))
                    new_commands = process_collect_fold(
                        proc, state[1], new_events.copy()
                    )
                    commands.extend(new_commands)
                    all_events.extend(new_events)
                    return loop(commands, all_events)

                return loop([command], [])

            def evolve(self, state: tuple[DS, PS], event: E) -> tuple[DS, PS]:
                return (decider.evolve(state[0], event), proc.evolve(state[1], event))

            def initial_state(self) -> tuple[DS, PS]:
                return (decider.initial_state(), proc.initial_state())

            def is_terminal(self, state: tuple[DS, PS]) -> bool:
                return decider.is_terminal(state[0]) and proc.is_terminal(state[1])

        return AnonymousDecider()
