from typing import Sequence

from sudoku_solver.sudoku.evaluator import SudokuEvaluator
from sudoku_solver.sudoku.model import SudokuBoard
from sudoku_solver.types import Command as C
from sudoku_solver.types import Event as E
from sudoku_solver.types import State as S

from pycider.deciders import Decider


class SudokuBoardAggregate(Decider[E.Base, C.Base, S.Base]):
    def initial_state(self) -> S.Base:
        return S.Initial()

    def is_terminal(self, state: S.Base) -> bool:
        return isinstance(state, S.Unsolvable) or isinstance(state, S.Solved)

    def decide(self, command: C.Base, state: S.Base) -> Sequence[E.Base]:
        # print(state)
        match command, state:
            case C.InitializeSolver(grid=grid), S.Initial():
                board = SudokuBoard(values=grid)
                if not SudokuEvaluator.is_board_valid(board):
                    return [E.SolutionFailed(board=board)]

                if SudokuEvaluator.is_board_complete(board):
                    return [E.SolutionFound(board=board)]

                return [E.BoardValidated(board=board)]

            case C.RunSolverStep(), S.Valid(board=board) | S.Solving(board=board):
                step = SudokuEvaluator.find_next_single_step(board)
                if step:
                    row, col, value = step
                    new_values = board.values[:]
                    new_values[row * 9 + col] = value
                    new_board = SudokuBoard(values=new_values)
                    return [E.StepCompleted(board=new_board)]

                return [E.SolutionFailed(board=board)]

            case C.ValidateBoardState(), S.Solving(board=board):
                if SudokuEvaluator.is_board_valid(board):
                    return [E.BoardValidated(board=board)]
                else:
                    return [E.SolutionFailed(board=board)]

            case C.CheckCompletion(), S.Solving(board=board):
                if SudokuEvaluator.is_board_complete(board):
                    return [E.SolutionFound(board=board)]
                return [E.BoardNotYetComplete(board)]

            case _:
                return [E.ErrorDetected(message="Unhandled command or invalid state.")]

    def evolve(self, state: S.Base, event: E.Base) -> S.Base:
        match event, state:

            # Event: StepCompleted -> Move to Solving state
            case E.StepCompleted(board=new_board), S.Solving() | S.Valid():
                return S.Solving(board=new_board)

            # Event: BoardValidated -> Move to Valid state
            case E.BoardValidated(board=new_board), (S.Initial() | S.Solving()):
                return S.Valid(board=new_board)

            # Event: SolutionFound -> Move to Solved state
            case E.SolutionFound(board=new_board), (S.Valid() | S.Solving()):
                return S.Solved(board=new_board)

            # Event: SolutionFailed -> Move to Unsolvable state
            case E.SolutionFailed(board=new_board), (S.Solving() | S.Valid()):
                return S.Unsolvable(board=new_board)

            # Event: ErrorDetected -> Move to Error state
            case E.ErrorDetected(message=msg), _:
                return S.Error(message=msg)

            # If no match, return the current state
            case _:
                return state
