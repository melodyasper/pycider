from dataclasses import dataclass

from sudoku_solver.sudoku.model import SudokuBoard


class State:
    @dataclass(frozen=True)
    class Base:
        pass

    @dataclass(frozen=True)
    class Initial(Base):
        """The solver is initialized with the provided board."""

        pass

    @dataclass(frozen=True)
    class InitializedBase(Base):
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
    class Error(Base):
        """An error occurred during the solving process, requiring attention."""

        message: str


class Event:
    @dataclass(frozen=True)
    class Base:
        pass

    @dataclass(frozen=True)
    class BoardInitialized(Base):
        """Initialized"""

        board: SudokuBoard

    @dataclass(frozen=True)
    class StepCompleted(Base):
        """A step in the solving process was successfully completed."""

        idx: int
        value: int

    @dataclass(frozen=True)
    class BoardValidated(Base):
        """The board was checked and found to be valid."""

        pass

    @dataclass(frozen=True)
    class BoardNotYetComplete(Base):
        """The board was checked for completion but is not yet complete."""

        pass

    @dataclass(frozen=True)
    class SolutionFound(Base):
        """The solver has successfully found a solution."""

        pass

    @dataclass(frozen=True)
    class SolutionFailed(Base):
        """The solver was unable to solve the board."""

        pass

    @dataclass(frozen=True)
    class ErrorDetected(Base):
        """An error was encountered during the solving process."""

        message: str


class Command:
    @dataclass(frozen=True)
    class Base:
        pass

    @dataclass(frozen=True)
    class InitializeSolver(Base):
        """Start the solver with the provided initial board."""

        grid: list[int | None]

    @dataclass(frozen=True)
    class RunSolverStep(Base):
        """Perform a step in the solving algorithm."""

        pass

    @dataclass(frozen=True)
    class ValidateBoardState(Base):
        """Check if the current state of the board is valid."""

        pass

    @dataclass(frozen=True)
    class CheckCompletion(Base):
        """Verify if the board is completely solved."""

        pass

    @dataclass(frozen=True)
    class HandleError(Base):
        """Process any detected error during solving."""

        message: str
