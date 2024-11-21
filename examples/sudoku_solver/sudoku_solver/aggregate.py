from collections.abc import Iterator
from dataclasses import dataclass

from pycider.deciders import Decider

from sudoku_solver.sudoku.evaluator import SudokuEvaluator
from sudoku_solver.sudoku.model import SudokuBoard
from sudoku_solver.types import Command, Event, State


@dataclass(frozen=True)
class SudokuBoardCommand(Command):
    pass


@dataclass(frozen=True)
class SudokuBoardEvent(Event):
    pass


@dataclass(frozen=True)
class SudokuBoardState(State):
    pass


@dataclass(frozen=True)
class InitializeSolver(SudokuBoardCommand):
    """Start the solver with the provided initial board."""

    grid: list[int | None]


@dataclass(frozen=True)
class RunSolverStep(SudokuBoardCommand):
    """Perform a step in the solving algorithm."""

    pass


@dataclass(frozen=True)
class ValidateBoardState(SudokuBoardCommand):
    """Check if the current state of the board is valid."""

    pass


@dataclass(frozen=True)
class CheckCompletion(SudokuBoardCommand):
    """Verify if the board is completely solved."""

    pass


@dataclass(frozen=True)
class HandleError(SudokuBoardCommand):
    """Process any detected error during solving."""

    message: str


@dataclass(frozen=True)
class BoardInitialized(SudokuBoardEvent):
    """Initialized"""

    board: SudokuBoard


@dataclass(frozen=True)
class StepCompleted(SudokuBoardEvent):
    """A step in the solving process was successfully completed."""

    idx: int
    value: int


@dataclass(frozen=True)
class BoardValidated(SudokuBoardEvent):
    """The board was checked and found to be valid."""

    pass


@dataclass(frozen=True)
class BoardNotYetComplete(SudokuBoardEvent):
    """The board was checked for completion but is not yet complete."""

    pass


@dataclass(frozen=True)
class SolutionFound(SudokuBoardEvent):
    """The solver has successfully found a solution."""

    pass


@dataclass(frozen=True)
class SolutionFailed(SudokuBoardEvent):
    """The solver was unable to solve the board."""

    pass


@dataclass(frozen=True)
class ErrorDetected(SudokuBoardEvent):
    """An error was encountered during the solving process."""

    message: str


@dataclass(frozen=True)
class Initial(SudokuBoardState):
    """The solver is initialized with the provided board."""

    pass


@dataclass(frozen=True)
class InitializedBase(SudokuBoardState):
    """The solver is now inialized."""

    board: SudokuBoard


@dataclass(frozen=True)
class Solving(InitializedBase):
    """The solver is actively processing and attempting to solve the board."""

    pass


@dataclass(frozen=True)
class Valid(InitializedBase):
    """The board is currently in a valid state according to Sudoku rules."""

    pass


@dataclass(frozen=True)
class Invalid(InitializedBase):
    """The board state has been found invalid (e.g., contradicting numbers)."""

    pass


@dataclass(frozen=True)
class Solved(InitializedBase):
    """The board has been solved successfully."""

    pass


@dataclass(frozen=True)
class Unsolvable(InitializedBase):
    """The board was determined to be unsolvable after processing."""

    pass


@dataclass(frozen=True)
class Error(SudokuBoardState):
    """An error occurred during the solving process, requiring attention."""

    message: str


class SudokuBoardAggregate(
    Decider[SudokuBoardEvent, SudokuBoardCommand, SudokuBoardState]
):
    def initial_state(self) -> SudokuBoardState:
        return Initial()

    def is_terminal(self, state: SudokuBoardState) -> bool:
        return isinstance(state, Unsolvable) or isinstance(state, Solved)

    def decide(
        self, command: SudokuBoardCommand, state: SudokuBoardState
    ) -> Iterator[SudokuBoardEvent]:
        match command, state:
            case InitializeSolver(grid=grid), Initial():
                board = SudokuBoard(values=grid)
                yield from [BoardInitialized(board=board)]

            case RunSolverStep(), Valid(board=board) | Solving(board=board):
                step = SudokuEvaluator.find_next_single_step(board)
                if step:
                    row, col, value = step
                    idx = row * 9 + col
                    yield from [StepCompleted(idx=idx, value=value)]
                else:
                    yield from [SolutionFailed()]

            case ValidateBoardState(), Solving(board=board):
                if SudokuEvaluator.is_board_valid(board):
                    yield from [BoardValidated()]
                else:
                    yield from [SolutionFailed()]

            case CheckCompletion(), Solving(board=board):
                if SudokuEvaluator.is_board_complete(board):
                    yield from [SolutionFound()]
                else:
                    yield from [BoardNotYetComplete()]

            case _:
                yield from [
                    ErrorDetected(message=f"Unhandled: {command=} with {state=}.")
                ]

    def evolve(
        self, state: SudokuBoardState, event: SudokuBoardEvent
    ) -> SudokuBoardState:
        match event, state:
            case BoardInitialized(board=board), Initial():
                return Solving(board=board)

            case StepCompleted(idx=idx, value=value), Solving(board=board) | Valid(
                board=board
            ):
                values = board.values[:]
                values[idx] = value
                new_board = SudokuBoard(values=values)
                return Solving(board=new_board)

            case BoardValidated(), Solving(board=board):
                return Valid(board=board)

            case SolutionFound(), (Valid(board=board) | Solving(board=board)):
                return Solved(board=board)

            case SolutionFailed(), (Solving(board=board) | Valid(board=board)):
                return Unsolvable(board=board)

            case ErrorDetected(message=msg), _:
                return Error(message=msg)

            # If no match, return the current state
            case _:
                return state
