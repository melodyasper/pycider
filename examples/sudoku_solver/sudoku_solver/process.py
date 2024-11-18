from collections.abc import Iterator

from sudoku_solver import aggregate
from sudoku_solver.types import Command as C
from sudoku_solver.types import Event as E
from sudoku_solver.types import State as S

from pycider import processes


class SudokuProcess(processes.IProcess[E.Base, C.Base, S.Base]):
    def react(self, state: S.Base, event: E.Base) -> Iterator[C.Base]:
        """Returns an iterator of commands as a reaction to an event."""
        match event, state:

            # Event: StepCompleted -> Generate the next step command
            case E.StepCompleted() | E.BoardInitialized(), _:
                yield from [C.CheckCompletion()]

            # Event: BoardValidated -> Start solving if the board is valid
            case E.BoardValidated(), _:
                yield from [C.RunSolverStep()]

            # Event: BoardNotYetComplete -> The board is not yet complete
            case E.BoardNotYetComplete(), _:
                yield from [C.RunSolverStep()]

            # Event: SolutionFound -> No further action needed, board is solved
            case E.SolutionFound(), _:
                yield from []

            # Event: SolutionFailed -> No further action, board is unsolvable
            case E.SolutionFailed(), _:
                yield from []

            # Event: ErrorDetected -> No further action
            case E.ErrorDetected(), _:
                yield from []

            # Default case: No action for unhandled events
            case _:
                yield from []

    def evolve(self, state: S.Base, event: E.Base) -> S.Base:
        return state

    def resume(self, state: S.Base) -> Iterator[C.Base]:
        yield from []

    def initial_state(self) -> S.Base:
        return aggregate.SudokuBoardAggregate().initial_state()

    def is_terminal(self, state: S.Base) -> bool:
        return True
