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
        match command, state:
            case C.InitializeSolver(grid=grid), S.Initial():
                board = SudokuBoard(values=grid)
                return [E.BoardInitialized(board=board)]

            case C.RunSolverStep(), S.Valid(board=board) | S.Solving(board=board):
                step = SudokuEvaluator.find_next_single_step(board)
                if step:
                    row, col, value = step
                    idx = row * 9 + col
                    return [E.StepCompleted(idx=idx, value=value)]

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
                return [
                    E.ErrorDetected(message=f"Unhandled: {command=} with {state=}.")
                ]

    def evolve(self, state: S.Base, event: E.Base) -> S.Base:
        match event, state:
            case E.BoardInitialized(board=board), S.Initial():
                return S.Solving(board=board)

            case E.StepCompleted(idx=idx, value=value), S.Solving(
                board=board
            ) | S.Valid(board=board):
                values = board.values[:]
                values[idx] = value
                new_board = SudokuBoard(values=values)
                return S.Solving(board=new_board)

            case E.BoardValidated(board=new_board), (S.Initial() | S.Solving()):
                return S.Valid(board=new_board)

            case E.SolutionFound(board=new_board), (S.Valid() | S.Solving()):
                return S.Solved(board=new_board)

            case E.SolutionFailed(board=new_board), (S.Solving() | S.Valid()):
                return S.Unsolvable(board=new_board)

            case E.ErrorDetected(message=msg), _:
                return S.Error(message=msg)

            # If no match, return the current state
            case _:
                return state
