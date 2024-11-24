import abc
from collections.abc import Iterator
from dataclasses import dataclass

from pycider import processes


@dataclass(frozen=True)
class Command(abc.ABC):
    pass


@dataclass(frozen=True)
class Event(abc.ABC):
    pass


@dataclass(frozen=True)
class State(abc.ABC):
    pass


@dataclass(frozen=True)
class InitialState(State):
    pass


@dataclass(frozen=True)
class StepCompleted(Event):
    pass


@dataclass(frozen=True)
class BoardValidated(Event):
    pass


@dataclass(frozen=True)
class CheckCompletion(Command):
    pass


@dataclass(frozen=True)
class RunSolverStep(Command):
    pass


@dataclass(frozen=True)
class BoardNotYetComplete(Event):
    pass


class SudokuProcess(processes.IProcess[Event, Command, State]):
    def react(self, state: State, event: Event) -> Iterator[Command]:
        """Returns an iterator of commands as a reaction to an event."""
        match event, state:

            # Event: StepCompleted -> Generate the next step command
            case StepCompleted(), _:
                yield from [CheckCompletion()]

            # Event: BoardValidated -> Start solving if the board is valid
            case BoardValidated(), _:
                yield from [RunSolverStep()]

            # Event: BoardNotYetComplete -> The board is not yet complete
            case BoardNotYetComplete(), _:
                yield from [RunSolverStep()]

            # Default case: No action for unhandled events
            case _:
                yield from []

    def evolve(self, state: State, event: Event) -> State:
        return state

    def resume(self, state: State) -> Iterator[Command]:
        yield from []

    def initial_state(self) -> State:
        return InitialState()

    def is_terminal(self, state: State) -> bool:
        return True
