from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator, MutableMapping
from typing import Generic, TypeVar

from pycider.types import Either, Left, Right

E = TypeVar("E")
C = TypeVar("C")
S = TypeVar("S")
SI = TypeVar("SI")
SO = TypeVar("SO")


class BaseDecider(ABC, Generic[E, C, SI, SO]):
    """This decider allows for a different input and output state type.

    BaseDecider should only be used when the input and output state type
    should be different. Otherwise use Decider.
    """

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
    def decide(self, command: C, state: SI) -> Iterator[E]:
        """Return a set of events from a command and state.

        Parameters
            command: Action to be performed
            state: State of the current decider

        Returns
            An iterator of events resulting from the command.
        """
        pass


class Decider(BaseDecider[E, C, S, S], Generic[E, C, S]):
    """This is a BaseDecider where the input and output state are the same.

    This is the Decider that should preferably be used unless you explcitly
    need control over a different input and output type for the state.
    """

    pass


CX = TypeVar("CX")
EX = TypeVar("EX")
SX = TypeVar("SX")
CY = TypeVar("CY")
EY = TypeVar("EY")
SY = TypeVar("SY")


class ComposeDecider(Generic[EX, CX, SX, EY, CY, SY]):
    """Combine two deciders into a single decider.

    This creates a Decider that is combined into a Left and Right
    side. There is a type for Left or Right in `pycider.types`.
    To execute commands after composing two targets you need
    to pass in commands in the following shape:

    `Left(C)` or `Right(C)` where C is the command to be executed.
    This code will make sure the proper decider receives the command.
    """

    @classmethod
    def build(
        cls, left_dx: Decider[EX, CX, SX], right_dy: Decider[EY, CY, SY]
    ) -> Decider[Either[EX, EY], Either[CX, CY], tuple[SX, SY]]:
        """Given two deciders return a single one.

        Parameters:
            dx: Decider for the Left side of the combined decider
            dy: Decider for the Right side of the combined decider

        Returns:
            A single decider made of two deciders."""

        InnerEX = TypeVar("InnerEX")
        InnerEY = TypeVar("InnerEY")
        InnerCX = TypeVar("InnerCX")
        InnerCY = TypeVar("InnerCY")
        InnerSX = TypeVar("InnerSX")
        InnerSY = TypeVar("InnerSY")

        class InternalDecider(
            Decider[
                Either[InnerEX, InnerEY],
                Either[InnerCX, InnerCY],
                tuple[InnerSX, InnerSY],
            ]
        ):

            def __init__(
                self,
                dx: Decider[InnerEX, InnerCX, InnerSX],
                dy: Decider[InnerEY, InnerCY, InnerSY],
            ) -> None:
                self._dx = dx
                self._dy = dy

            def decide(
                self, command: Either[InnerCX, InnerCY], state: tuple[InnerSX, InnerSY]
            ) -> Iterator[Either[InnerEX, InnerEY]]:
                match command:
                    case Left():
                        yield from map(
                            lambda v: Left(v), self._dx.decide(command.value, state[0])
                        )
                    case Right():
                        yield from map(
                            lambda v: Right(v), self._dy.decide(command.value, state[1])
                        )

            def evolve(
                self,
                state: tuple[InnerSX, InnerSY],
                event: Left[InnerEX] | Right[InnerEY],
            ) -> tuple[InnerSX, InnerSY]:
                match event:
                    case Left():
                        return (self._dx.evolve(state[0], event.value), state[1])
                    case Right():
                        return (state[0], self._dy.evolve(state[1], event.value))

            def initial_state(self) -> tuple[InnerSX, InnerSY]:
                return (self._dx.initial_state(), self._dy.initial_state())

            def is_terminal(self, state: tuple[InnerSX, InnerSY]) -> bool:
                return self._dx.is_terminal(state[0]) and self._dy.is_terminal(state[1])

        return InternalDecider(left_dx, right_dy)


class NeutralDecider:
    """For demonostration purposes."""

    @classmethod
    def build(cls):
        """Returns a demonstration neutral decider.

        Returns:
            A decider which is always terminal and returns nothing.
        """

        class InternalDecider(Decider[None, None, tuple[()]]):
            def decide(self, command: None, state: tuple[()]) -> Iterator[None]:
                yield from []

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
    """Manage many instances of the same Decider using a Identifier.

    This Decider is useful if you have multiple of the same Decider that
    can be differentiated by a unique element. For example a list of
    transaction Deciders which all have a unique transaction key, or a
    list of clients that all have a unique client id. Using this you
    can execute commands by executing with a many decider commands in
    a tuple of (I, C) where I is the unique identifier and C is the
    desired command to be executed.
    """

    def __init__(self, decider: type[Decider[E, C, S]]) -> None:
        """Create an instance of ManyDecider.

        Parameters:
            decider: The type of decider we are holding multiples of.
        """
        super().__init__()
        self.decider = decider

    def evolve(
        self, state: MutableMapping[I, S], event: tuple[I, E]
    ) -> MutableMapping[I, S]:

        identifier = event[0]
        current_event = event[1]

        current_state = state.get(identifier)
        if current_state is None:
            current_state = self.decider().initial_state()

        current_state = self.decider().evolve(current_state, current_event)
        state[identifier] = current_state

        return state

    def decide(
        self, command: tuple[I, C], state: MutableMapping[I, S]
    ) -> Iterator[tuple[I, E]]:
        identifier = command[0]
        current_command = command[1]

        current_state = state.get(identifier)
        if current_state is None:
            current_state = self.decider().initial_state()

        yield from map(
            lambda event: (identifier, event),
            self.decider().decide(current_command, current_state),
        )

    def is_terminal(self, state: MutableMapping[I, S]) -> bool:
        for member_state in state.values():
            if not self.decider().is_terminal(member_state):
                return False
        return True

    def initial_state(self) -> MutableMapping[I, S]:
        return {}


EO = TypeVar("EO")
CO = TypeVar("CO")
FEO = TypeVar("FEO")
FSI = TypeVar("FSI")


class AdaptDecider(Generic[E, C, S, EO, CO, SO]):
    """A decider that translates from one set of events/commands/states to another.

    The AdaptDecider takes in a decider and makes a translation layer
    between the commands, events, and state internally and a new
    resulting type of command, event, and map. The purpose of this is
    to allow a Decider of one type to interact with a Decider of
    another type through translation.
    """

    @classmethod
    def build(
        cls,
        fci: Callable[[C], CO | None],
        fei: Callable[[E], EO | None],
        feo: Callable[[EO], E],
        fsi: Callable[[S], SO],
        decider: Decider[EO, CO, SO],
    ) -> BaseDecider[E, C, S, SO]:
        """Create an adapted decider.

        Parameters:
            fci: A callable function that takes a Command as input and
                returns an output command of a different type.
            fei: A callable function that takes an Event as an input and
                returns an output event of a different type.
            feo: A callable function that takes an output event type and
                translates it back into an internal event type.
            fsi: A callable function takes a state and translates it to
                a target output  state of a different type.

        Returns:
            A Decider with its functions wrapped by translation functions.
        """

        class InternalDecider(BaseDecider[E, C, S, SO]):
            def decide(self, command: C, state: S) -> Iterator[E]:
                new_command = fci(command)
                if new_command is None:
                    return
                yield from map(feo, decider.decide(new_command, fsi(state)))

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
    """Map allows the translation of a Decider's state into a different state."""

    @classmethod
    def build(
        f: Callable[[SA], SB], d: BaseDecider[E, C, SI, SA]
    ) -> BaseDecider[E, C, SI, SB]:
        """Build a whose state is represented as the function `f(state)`.

        Parameters:
            f: A function to transform the state.
            d: The Decider we are using.

        Returns:
            A new Decider where `evolve` and `initial_state` both
            return `f(state_operation)`.
        """

        class InternalDecider(BaseDecider[E, C, SI, SB]):
            def decide(self, command: C, state: SI) -> Iterator[E]:
                yield from d.decide(command, state)

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
            def decide(self, command: C, state: SI) -> Iterator[E]:
                yield from dx.decide(command, state)
                yield from dy.decide(command, state)

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
