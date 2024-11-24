from sudoku_solver import decider, process

from pycider import processes, utils


def test_sudoku_solver_can_solve_simple_puzzle() -> None:
    test_process = process.SudokuProcess()
    test_decider = decider.SudokuDecider()

    def convert_command(
        command_out: process.Command,
    ) -> decider.Command:
        print(f"{command_out=}")
        match command_out:
            case process.CheckCompletion():
                return decider.CheckCompletion()
            case process.RunSolverStep():
                return decider.RunSolverStep()
            case _:
                raise RuntimeError("Impossible area reached")

    def select_event(
        event_in: decider.Event,
    ) -> process.Event | None:
        print(f"{event_in=}")
        match event_in:
            case decider.BoardInitialized():
                return process.StepCompleted()
            case decider.StepCompleted():
                return process.StepCompleted()
            case decider.BoardValidated():
                return process.BoardValidated()
            case decider.BoardNotYetComplete():
                return process.BoardNotYetComplete()
            case _:
                return None

    adapted_process = processes.ProcessAdapt(
        select_event, convert_command, test_process
    ).build()
    program = processes.ProcessCombineWithDecider(adapted_process, test_decider).build()
    solver = utils.InMemory(program)

    grid: list[int | None] = [
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

    events = solver(decider.InitializeSolver(grid=grid))

    state = test_decider.initial_state()
    for event in events:
        state = test_decider.evolve(state, event)

    assert isinstance(state, decider.Solved)
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
