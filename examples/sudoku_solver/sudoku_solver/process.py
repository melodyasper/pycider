from collections.abc import Iterator
from dataclasses import dataclass

from sudoku_solver.types import Command, Event, State

from pycider import processes


@dataclass(frozen=True)
class SudokuProcessCommand(Command):
    pass


@dataclass(frozen=True)
class SudokuProcessEvent(Event):
    pass


@dataclass(frozen=True)
class SudokuProcessState(State):
    pass


@dataclass(frozen=True)
class ProcessInitialState(SudokuProcessState):
    pass


@dataclass(frozen=True)
class ProcessStepCompleted(SudokuProcessEvent):
    pass


@dataclass(frozen=True)
class ProcessBoardValidated(SudokuProcessEvent):
    pass


@dataclass(frozen=True)
class ProcessCheckCompletion(SudokuProcessCommand):
    pass


@dataclass(frozen=True)
class ProcessRunSolverStep(SudokuProcessCommand):
    pass


@dataclass(frozen=True)
class ProcessBoardNotYetComplete(SudokuProcessEvent):
    pass


class SudokuProcess(
    processes.IProcess[SudokuProcessEvent, SudokuProcessCommand, SudokuProcessState]
):
    def react(
        self, state: SudokuProcessState, event: SudokuProcessEvent
    ) -> Iterator[SudokuProcessCommand]:
        """Returns an iterator of commands as a reaction to an event."""
        match event, state:

            # Event: StepCompleted -> Generate the next step command
            case ProcessStepCompleted(), _:
                yield from [ProcessCheckCompletion()]

            # Event: BoardValidated -> Start solving if the board is valid
            case ProcessBoardValidated(), _:
                yield from [ProcessRunSolverStep()]

            # Event: BoardNotYetComplete -> The board is not yet complete
            case ProcessBoardNotYetComplete(), _:
                yield from [ProcessRunSolverStep()]

            # Default case: No action for unhandled events
            case _:
                yield from []

    def evolve(
        self, state: SudokuProcessState, event: SudokuProcessEvent
    ) -> SudokuProcessState:
        return state

    def resume(self, state: SudokuProcessState) -> Iterator[SudokuProcessCommand]:
        yield from []

    def initial_state(self) -> SudokuProcessState:
        return ProcessInitialState()

    def is_terminal(self, state: SudokuProcessState) -> bool:
        return True
