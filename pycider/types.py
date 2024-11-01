from typing import Generic, TypeVar

TA = TypeVar("TA")
TB = TypeVar("TB")


class Left(Generic[TA]):
    """Left-hand side container that holds a value."""

    __match_args__ = ("value",)

    def __init__(self, value: TA) -> None:
        """Create a Left-hand side container with a value.

        Parameters:
            value: The value to be held by this method
        """
        self.value = value  #: The stored value.


class Right(Generic[TB]):
    """Right-hand side container that holds a value."""

    __match_args__ = ("value",)

    def __init__(self, value: TB) -> None:
        """Create a Right-hand side container with a value.

        Parameters:
            value: The value to be held by this method
        """
        self.value = value  #: The stored value.


Either = Left[TA] | Right[TB]  #: Combined type representing Left or Right.
