from pycider import processes, utils

from sudoku_solver import aggregate, process
from sudoku_solver.types import Command, State


def test_sudoku_solver_can_solve_simple_puzzle():
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

    assert isinstance(state, State.Solved)
    assert state.board.values == [
        4,
        6,
        9,
        7,
        5,
        1,
        3,
        8,
        2,
        2,
        8,
        1,
        6,
        9,
        3,
        4,
        7,
        5,
        7,
        3,
        5,
        4,
        8,
        2,
        9,
        1,
        6,
        6,
        9,
        4,
        1,
        3,
        8,
        5,
        2,
        7,
        5,
        1,
        3,
        2,
        7,
        6,
        8,
        9,
        4,
        8,
        7,
        2,
        9,
        4,
        5,
        1,
        6,
        3,
        9,
        2,
        6,
        5,
        1,
        4,
        7,
        3,
        8,
        1,
        5,
        8,
        3,
        6,
        7,
        2,
        4,
        9,
        3,
        4,
        7,
        8,
        2,
        9,
        6,
        5,
        1,
    ]
