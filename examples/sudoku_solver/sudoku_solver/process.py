from pycider import processes

from sudoku_solver import aggregate
from sudoku_solver.types import Command as C
from sudoku_solver.types import Event as E
from sudoku_solver.types import State as S


class SudokuProcess(processes.IProcess[E.Base, C.Base, S.Base]):
    def react(self, state: S.Base, event: E.Base) -> processes.Sequence[C.Base]:
        """Returns a sequence of commands as a reaction to an event."""
        match event, state:

            # Event: StepCompleted -> Generate the next step command
            case E.StepCompleted() | E.BoardInitialized(), _:
                return [C.CheckCompletion()]

            # Event: BoardValidated -> Start solving if the board is valid
            case E.BoardValidated(), _:
                return [C.RunSolverStep()]

            # Event: BoardNotYetComplete -> The board is not yet complete
            case E.BoardNotYetComplete(), _:
                return [C.RunSolverStep()]

            # Event: SolutionFound -> No further action needed, board is solved
            case E.SolutionFound(), _:
                return []

            # Event: SolutionFailed -> No further action, board is unsolvable
            case E.SolutionFailed(), _:
                return []

            # Event: ErrorDetected -> No further action, handle the error externally
            case E.ErrorDetected(), _:
                return []

            # Default case: No action for unhandled events
            case _:
                return []

    def evolve(self, state: S.Base, event: E.Base) -> S.Base:
        return state

    def resume(self, state: S.Base) -> processes.Sequence[C.Base]:
        return []

    def initial_state(self) -> S.Base:
        return aggregate.SudokuBoardAggregate().initial_state()

    def is_terminal(self, state: S.Base) -> bool:
        return True
