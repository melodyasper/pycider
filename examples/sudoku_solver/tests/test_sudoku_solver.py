from pycider import processes, utils

from sudoku_solver import aggregate, process


def test_sudoku_solver_can_solve_simple_puzzle():
    processor = process.SudokuProcess()
    decider = aggregate.SudokuBoardAggregate()

    def convert_command(
        command_out: process.SudokuProcessCommand,
    ) -> aggregate.SudokuBoardCommand:
        print(f"{command_out=}")
        match command_out:
            case process.ProcessCheckCompletion():
                return aggregate.CheckCompletion()
            case process.ProcessRunSolverStep():
                return aggregate.RunSolverStep()
            case _:
                raise RuntimeError("Impossible area reached")

    def select_event(
        event_in: aggregate.SudokuBoardEvent,
    ) -> process.SudokuProcessEvent | None:
        print(f"{event_in=}")
        match event_in:
            case aggregate.BoardInitialized():
                return process.ProcessStepCompleted()
            case aggregate.StepCompleted():
                return process.ProcessStepCompleted()
            case aggregate.BoardValidated():
                return process.ProcessBoardValidated()
            case aggregate.BoardNotYetComplete():
                return process.ProcessBoardNotYetComplete()
            case _:
                return None

    adapted_process = processes.ProcessAdapt().build(
        select_event, convert_command, processor
    )
    program = processes.ProcessCombineWithDecider.build(adapted_process, decider)
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

    events = solver(aggregate.InitializeSolver(grid=grid))
    print(events)

    state = decider.initial_state()
    for event in events:
        state = decider.evolve(state, event)

    assert isinstance(state, aggregate.Solved)
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
