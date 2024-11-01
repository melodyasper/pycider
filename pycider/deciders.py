import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, MutableMapping
from typing import Generic, Sequence, TypeVar

from pycider.types import Either, Left, Right

logger = logging.getLogger(__name__)


E = TypeVar("E")
C = TypeVar("C")
S = TypeVar("S")
SI = TypeVar("SI")
SO = TypeVar("SO")


class BaseDecider(ABC, Generic[E, C, SI, SO]):
    @abstractmethod
    def initial_state(self) -> SO:
        """Starting state for a decider.

        Returns
            The base state a decider
        """
        pass

    @abstractmethod
    def evolve(self, state: SI, event: E) -> SO:
        """Returns an updated state based on the current event.

        Paramters
            state: State of the current decider
            event: Event

        Returns
            An updated state
        """
        pass

    @abstractmethod
    def is_terminal(self, state: SI) -> bool:
        """Returns if the current state is terminal.

        Parameters
            state: State of the current decider

        Returns
            A boolean indicating if the decider is finished.
        """
        pass

    @abstractmethod
    def decide(self, command: C, state: SI) -> Sequence[E]:
        """Return a set of events from a command and state.

        Parameters
            command: Action to be performed
            state: State of the current decider

        Returns
            A sequence of events resulting from the command.
        """
        pass


class Decider(BaseDecider[E, C, S, S], Generic[E, C, S]):
    pass


CX = TypeVar("CX")
EX = TypeVar("EX")
SX = TypeVar("SX")
CY = TypeVar("CY")
EY = TypeVar("EY")
SY = TypeVar("SY")


class ComposeDecider(Generic[EX, CX, SX, EY, CY, SY]):
    """Combine two deciders into a single decider."""

    @classmethod
    def build(
        cls, dx: Decider[EX, CX, SX], dy: Decider[EY, CY, SY]
    ) -> Decider[Either[EX, EY], Either[CX, CY], tuple[SX, SY]]:
        """Given two deciders return a single one.

        Parameters:
            dx: Decider for the Left side of the combined decider
            dy: Decider for the Right side of the combined decider

        Returns:
            A single decider made of two deciders."""

        class InternalDecider(Decider[Either[EX, EY], Either[CX, CY], tuple[SX, SY]]):
            def decide(
                self, command: Either[CX, CY], state: tuple[SX, SY]
            ) -> Sequence[Either[EX, EY]]:
                match command:
                    case Left():
                        return list(
                            map(lambda v: Left(v), dx.decide(command.value, state[0]))
                        )
                    case Right():
                        return list(
                            map(lambda v: Right(v), dy.decide(command.value, state[1]))
                        )
                    case _:
                        raise RuntimeError("Type not implemented")

            def evolve(
                self, state: tuple[SX, SY], event: Left[EX] | Right[EY]
            ) -> tuple[SX, SY]:
                match event:
                    case Left():
                        return (dx.evolve(state[0], event.value), state[1])
                    case Right():
                        return (state[0], dy.evolve(state[1], event.value))
                    case _:
                        raise RuntimeError("Type not implemented")

            def initial_state(self) -> tuple[SX, SY]:
                return (dx.initial_state(), dy.initial_state())

            def is_terminal(self, state: tuple[SX, SY]) -> bool:
                return dx.is_terminal(state[0]) and dy.is_terminal(state[1])

        return InternalDecider()


class NeutralDecider:
    """For demonostration purposes."""

    @classmethod
    def build(cls):
        """Returns a demonstration neutral decider.

        Returns:
            A decider which is always terminal and returns nothing.
        """

        class InternalDecider(Decider[None, None, tuple[()]]):
            def decide(self, command: None, state: tuple[()]) -> Sequence[None]:
                return []

            def evolve(self, state: tuple[()], event: None) -> tuple[()]:
                return ()

            def initial_state(self) -> tuple[()]:
                return ()

            def is_terminal(self, state: tuple[()]) -> bool:
                return True

        return InternalDecider()


I = TypeVar("I")  # identifier


class ManyDecider(
    Decider[tuple[I, E], tuple[I, C], MutableMapping[I, S]], Generic[I, E, C, S]
):
    """Manage many instances of the same Decider using a Identifier."""

    def __init__(self, aggregate: type[Decider[E, C, S]]) -> None:
        """Initialize the ManyDecider class.

        Parameters:
            aggregate: The type of aggregate we are holding multiples of.
        """
        super().__init__()
        self.aggregate = aggregate

    def evolve(
        self, state: MutableMapping[I, S], event: tuple[I, E]
    ) -> MutableMapping[I, S]:

        identifier = event[0]
        current_event = event[1]

        current_state = state.get(identifier)
        if current_state is None:
            current_state = self.aggregate().initial_state()

        current_state = self.aggregate().evolve(current_state, current_event)
        state[identifier] = current_state

        return state

    def decide(
        self, command: tuple[I, C], state: MutableMapping[I, S]
    ) -> Sequence[tuple[I, E]]:
        identifier = command[0]
        current_command = command[1]

        current_state = state.get(identifier)
        if current_state is None:
            current_state = self.aggregate().initial_state()

        events = list(
            map(
                lambda event: (identifier, event),
                self.aggregate().decide(current_command, current_state),
            )
        )
        return events

    def is_terminal(self, state: MutableMapping[I, S]) -> bool:
        for member_state in state.values():
            if not self.aggregate().is_terminal(member_state):
                return False
        return True

    def initial_state(self) -> MutableMapping[I, S]:
        return {}


EO = TypeVar("EO")
CO = TypeVar("CO")
FEO = TypeVar("FEO")
FSI = TypeVar("FSI")


class AdaptDecider(Generic[E, C, S, EO, CO, SO]):
    @classmethod
    def build(
        cls,
        fci: Callable[[C], CO | None],
        fei: Callable[[E], EO | None],
        feo: Callable[[EO], E],
        fsi: Callable[[S], SO],
        decider: Decider[EO, CO, SO],
    ) -> BaseDecider[E, C, S, SO]:
        class InternalDecider(BaseDecider[E, C, S, SO]):
            def decide(self, command: C, state: S) -> Sequence[E]:
                new_command = fci(command)
                if new_command is None:
                    return []
                return list(map(feo, decider.decide(new_command, fsi(state))))

            def evolve(self, state: S, event: E) -> SO:
                new_event = fei(event)
                if new_event is None:
                    return fsi(state)
                return decider.evolve(fsi(state), new_event)

            def initial_state(self) -> SO:
                return decider.initial_state()

            def is_terminal(self, state: S) -> bool:
                return decider.is_terminal(fsi(state))

        return InternalDecider()


SA = TypeVar("SA")
SB = TypeVar("SB")


class MapDecider(Generic[E, C, SI, SA, SB]):
    @classmethod
    def build(
        f: Callable[[SA], SB], d: BaseDecider[E, C, SI, SA]
    ) -> BaseDecider[E, C, SI, SB]:
        class InternalDecider(BaseDecider[E, C, SI, SB]):
            def decide(self, command: C, state: SI) -> Sequence[E]:
                return d.decide(command, state)

            def evolve(self, state: SI, event: E) -> SB:
                return f(d.evolve(state, event))

            def initial_state(self) -> SB:
                return f(d.initial_state())

            def is_terminal(self, state: SI) -> bool:
                return d.is_terminal(state)

        return InternalDecider()


class Map2Decider(Generic[E, C, S, SX, SY, SI]):
    @classmethod
    def build(
        cls,
        f: Callable[[SX, SY], S],
        dx: BaseDecider[E, C, SI, SX],
        dy: BaseDecider[E, C, SI, SY],
    ) -> BaseDecider[E, C, SI, S]:
        class InternalDecider(BaseDecider[E, C, SI, S]):
            def decide(self, command: C, state: SI) -> Sequence[E]:
                events: list[E] = []
                events.extend(dx.decide(command, state))
                events.extend(dy.decide(command, state))
                return events

            def evolve(self, state: SI, event: E) -> S:
                sx = dx.evolve(state, event)
                sy = dy.evolve(state, event)
                return f(sx, sy)

            def initial_state(self) -> S:
                return f(dx.initial_state(), dy.initial_state())

            def is_terminal(self, state: SI) -> bool:
                return dx.is_terminal(state) and dy.is_terminal(state)

        return InternalDecider()


def apply(
    f: BaseDecider[E, C, SI, Callable[[SX], SO]], d: BaseDecider[E, C, SI, SX]
) -> BaseDecider[E, C, SI, SO]:
    return Map2Decider.build(lambda f, x: f(x), f, d)
