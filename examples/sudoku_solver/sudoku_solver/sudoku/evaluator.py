from sudoku_solver.sudoku.model import SudokuBoard


class SudokuEvaluator:
    @classmethod
    def is_value_valid(cls, value: int | None) -> bool:
        return value is None or 1 <= value <= 9

    @classmethod
    def is_row_valid(cls, board: SudokuBoard, row: int) -> bool:
        """Checks if a row contains no duplicates."""
        seen = set()
        for col in range(9):
            value = board.values[row * 9 + col]
            if value is not None:
                if value in seen:
                    return False
                seen.add(value)
        return True

    @classmethod
    def is_column_valid(cls, board: SudokuBoard, col: int) -> bool:
        """Checks if a column contains no duplicates."""
        seen = set()
        for row in range(9):
            value = board.values[row * 9 + col]
            if value is not None:
                if value in seen:
                    return False
                seen.add(value)
        return True

    @classmethod
    def is_subgrid_valid(
        cls, board: SudokuBoard, start_row: int, start_col: int
    ) -> bool:
        """Checks if a 3x3 subgrid contains no duplicates."""
        seen = set()
        for row in range(3):
            for col in range(3):
                value = board.values[(start_row + row) * 9 + (start_col + col)]
                if value is not None:
                    if value in seen:
                        return False
                    seen.add(value)
        return True

    @classmethod
    def is_board_valid(cls, board: SudokuBoard) -> bool:
        """Checks if the entire board is valid."""
        # Validate rows, columns, and subgrids
        for i in range(9):
            if not cls.is_row_valid(board, i) or not cls.is_column_valid(board, i):
                return False
        for row in range(0, 9, 3):
            for col in range(0, 9, 3):
                if not cls.is_subgrid_valid(board, row, col):
                    return False
        return True

    @classmethod
    def is_board_complete(cls, board: SudokuBoard) -> bool:
        return all(value is not None for value in board.values)

    @classmethod
    def is_value_allowed(
        cls, board: SudokuBoard, row: int, col: int, value: int
    ) -> bool:
        """Checks if a value can be placed at the given row and column."""
        # Check row
        if value in (board.values[row * 9 + c] for c in range(9)):
            return False
        # Check column
        if value in (board.values[r * 9 + col] for r in range(9)):
            return False
        # Check subgrid
        start_row, start_col = row - row % 3, col - col % 3
        for r in range(3):
            for c in range(3):
                if board.values[(start_row + r) * 9 + (start_col + c)] == value:
                    return False
        return True

    @classmethod
    def find_next_single_step(cls, board: SudokuBoard) -> tuple[int, int, int] | None:
        """Finds a cell where only one value can fit."""
        for row in range(9):
            for col in range(9):
                if board.values[row * 9 + col] is None:
                    possible_values = [
                        value
                        for value in range(1, 10)
                        if cls.is_value_allowed(board, row, col, value)
                    ]
                    if len(possible_values) == 1:
                        return row, col, possible_values[0]
        return None
