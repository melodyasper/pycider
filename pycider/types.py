from typing import Generic, TypeVar

TA = TypeVar("TA")
TB = TypeVar("TB")


class Left(Generic[TA]):
    __match_args__ = ("value",)

    def __init__(self, value: TA) -> None:
        self.value = value


class Right(Generic[TB]):
    __match_args__ = ("value",)

    def __init__(self, value: TB) -> None:
        self.value = value


Either = Left[TA] | Right[TB]
