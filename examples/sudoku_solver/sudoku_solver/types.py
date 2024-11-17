from dataclasses import dataclass

from sudoku_solver.sudoku.model import SudokuBoard


# States
class State:
    @dataclass
    class Base:
        pass

    @dataclass
    class Initial(Base):
        """The solver is initialized with the provided board."""

        pass

    @dataclass
    class Solving(Base):
        """The solver is actively processing and attempting to solve the board."""

        board: SudokuBoard

    @dataclass
    class Valid(Base):
        """The board is currently in a valid state according to Sudoku rules."""

        board: SudokuBoard

    @dataclass
    class Invalid(Base):
        """The board state has been found invalid (e.g., contradicting numbers)."""

        board: SudokuBoard

    @dataclass
    class Solved(Base):
        """The board has been solved successfully."""

        board: SudokuBoard

    @dataclass
    class Unsolvable(Base):
        """The board was determined to be unsolvable after processing."""

        board: SudokuBoard

    @dataclass
    class Error(Base):
        """An error occurred during the solving process, requiring attention."""

        message: str


# Events
class Event:
    @dataclass
    class Base:
        pass

    @dataclass
    class StepCompleted(Base):
        """A step in the solving process was successfully completed."""

        idx: int
        value: int

    @dataclass
    class BoardValidated(Base):
        """The board was checked and found to be valid."""

        board: SudokuBoard

    @dataclass
    class BoardNotYetComplete(Base):
        """The board was checked for completion but is not yet complete."""

        board: SudokuBoard

    @dataclass
    class SolutionFound(Base):
        """The solver has successfully found a solution."""

        board: SudokuBoard

    @dataclass
    class SolutionFailed(Base):
        """The solver was unable to solve the board."""

        board: SudokuBoard

    @dataclass
    class ErrorDetected(Base):
        """An error was encountered during the solving process."""

        message: str


# Commands
class Command:
    @dataclass
    class Base:
        pass

    @dataclass
    class InitializeSolver(Base):
        """Start the solver with the provided initial board."""

        grid: list[int | None]

    @dataclass
    class RunSolverStep(Base):
        """Perform a step in the solving algorithm."""

        pass

    @dataclass
    class ValidateBoardState(Base):
        """Check if the current state of the board is valid."""

        pass

    @dataclass
    class CheckCompletion(Base):
        """Verify if the board is completely solved."""

        pass

    @dataclass
    class HandleError(Base):
        """Process any detected error during solving."""

        message: str
