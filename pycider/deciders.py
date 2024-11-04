from abc import ABC, abstractmethod
from collections.abc import Callable, MutableMapping
from typing import Generic, Sequence, TypeVar

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
    ) -> Sequence[tuple[I, E]]:
        identifier = command[0]
        current_command = command[1]

        current_state = state.get(identifier)
        if current_state is None:
            current_state = self.decider().initial_state()

        events = list(
            map(
                lambda event: (identifier, event),
                self.decider().decide(current_command, current_state),
            )
        )
        return events

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
