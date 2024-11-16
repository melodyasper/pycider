import dataclasses


@dataclasses.dataclass(frozen=True)
class SudokuBoard:
    values: list[int | None]
