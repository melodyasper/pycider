from pycider import processes, utils

from sudoku_solver import aggregate, process
from sudoku_solver.types import Command, State


def print_sudoku_board(board: list[int | None]) -> None:
    for column in range(0, 9):
        for row in range(0, 9):
            value = str(board[column * 9 + row])
            if value == "None":
                value = "_"
            print(f"{value}", end=" ")
            if row in [2, 5]:
                print("|", end=" ")
        print()
        if column in [2, 5]:
            print("------+-------+-------")


if __name__ == "__main__":
    processor = process.SudokuProcess()
    decider = aggregate.SudokuBoardAggregate()

    program = processes.ProcessCombineWithDecider.build(processor, decider)
    solver = utils.InMemory(program)

    grid = [
        4,
        None,
        None,
        7,
        None,
        None,
        3,
        8,
        2,
        None,
        8,
        None,
        None,
        None,
        None,
        None,
        7,
        None,
        None,
        3,
        None,
        None,
        8,
        None,
        9,
        None,
        None,
        None,
        None,
        4,
        None,
        None,
        8,
        5,
        2,
        None,
        None,
        None,
        None,
        2,
        7,
        None,
        None,
        None,
        None,
        None,
        7,
        2,
        9,
        4,
        None,
        None,
        6,
        None,
        9,
        2,
        6,
        5,
        1,
        None,
        None,
        3,
        None,
        1,
        None,
        8,
        3,
        6,
        None,
        None,
        4,
        None,
        3,
        None,
        None,
        8,
        2,
        9,
        6,
        None,
        1,
    ]
    events = solver(Command.InitializeSolver(grid=grid))

    state = decider.initial_state()
    for event in events:
        state = decider.evolve(state, event)

    match state:
        case State.Solved(board=board):
            print("Solved board:")
            print_sudoku_board(board.values)
        case State.Unsolvable(board=board):
            print("Board could not be solved:")
            print_sudoku_board(board.values)
        case _:
            print(f"Board in unknown {state=}")
