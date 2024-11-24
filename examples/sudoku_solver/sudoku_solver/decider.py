import abc
from collections.abc import Iterator
from dataclasses import dataclass

from pycider.deciders import Decider

from sudoku_solver.sudoku.evaluator import SudokuEvaluator
from sudoku_solver.sudoku.model import SudokuBoard


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
class InitializeSolver(Command):
    """Start the solver with the provided initial board."""

    grid: list[int | None]


@dataclass(frozen=True)
class RunSolverStep(Command):
    """Perform a step in the solving algorithm."""

    pass


@dataclass(frozen=True)
class ValidateBoardState(Command):
    """Check if the current state of the board is valid."""

    pass


@dataclass(frozen=True)
class CheckCompletion(Command):
    """Verify if the board is completely solved."""

    pass


@dataclass(frozen=True)
class HandleError(Command):
    """Process any detected error during solving."""

    message: str


@dataclass(frozen=True)
class BoardInitialized(Event):
    """Initialized"""

    board: SudokuBoard


@dataclass(frozen=True)
class StepCompleted(Event):
    """A step in the solving process was successfully completed."""

    idx: int
    value: int


@dataclass(frozen=True)
class BoardValidated(Event):
    """The board was checked and found to be valid."""

    pass


@dataclass(frozen=True)
class BoardNotYetComplete(Event):
    """The board was checked for completion but is not yet complete."""

    pass


@dataclass(frozen=True)
class SolutionFound(Event):
    """The solver has successfully found a solution."""

    pass


@dataclass(frozen=True)
class SolutionFailed(Event):
    """The solver was unable to solve the board."""

    pass


@dataclass(frozen=True)
class ErrorDetected(Event):
    """An error was encountered during the solving process."""

    message: str


@dataclass(frozen=True)
class Initial(State):
    """The solver is initialized with the provided board."""

    pass


@dataclass(frozen=True)
class InitializedBase(State):
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
class Error(State):
    """An error occurred during the solving process, requiring attention."""

    message: str


class SudokuDecider(Decider[Event, Command, State]):
    def initial_state(self) -> State:
        return Initial()

    def is_terminal(self, state: State) -> bool:
        return isinstance(state, Unsolvable) or isinstance(state, Solved)

    def decide(self, command: Command, state: State) -> Iterator[Event]:
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

    def evolve(self, state: State, event: Event) -> State:
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
