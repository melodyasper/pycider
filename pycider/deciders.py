from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator, MutableMapping
from typing import Generic, Type, TypeVar

from pycider.types import Either, Left, Right

E = TypeVar("E")
C = TypeVar("C")
S = TypeVar("S")
SI = TypeVar("SI")
SO = TypeVar("SO")
CX = TypeVar("CX")
EX = TypeVar("EX")
SX = TypeVar("SX")
CY = TypeVar("CY")
EY = TypeVar("EY")
SY = TypeVar("SY")
SA = TypeVar("SA")
SB = TypeVar("SB")
EO = TypeVar("EO")
CO = TypeVar("CO")
FEO = TypeVar("FEO")
FSI = TypeVar("FSI")


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


class ComposeDecider(Generic[EX, CX, SX, EY, CY, SY]):
    """Combine two deciders into a single decider.

    This creates a Decider that is combined into a Left and Right
    side. There is a type for Left or Right in `pycider.types`.
    To execute commands after composing two targets you need
    to pass in commands in the following shape:

    `Left(C)` or `Right(C)` where C is the command to be executed.
    This code will make sure the proper decider receives the command.
    """

    def __init__(
        self, left_dx: Decider[EX, CX, SX], right_dy: Decider[EY, CY, SY]
    ) -> None:
        """Combine two deciders into a single decider.

        Parameters:
            dx: Decider for the Left side of the combined decider
            dy: Decider for the Right side of the combined decider
        """

        self._left_dx = left_dx
        self._right_dy = right_dy

    def build(self) -> Decider[Either[EX, EY], Either[CX, CY], tuple[SX, SY]]:
        """Given two deciders return a single one.

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

        return InternalDecider(self._left_dx, self._right_dy)


class NeutralDecider:
    """For demonostration purposes."""

    def build(self):
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


class ManyDecider(Generic[I]):
    """Manage many instances of the same Decider using a Identifier.

    This Decider is useful if you have multiple of the same Decider that
    can be differentiated by a unique element. For example a list of
    transaction Deciders which all have a unique transaction key, or a
    list of clients that all have a unique client id. Using this you
    can execute commands by executing with a many decider commands in
    a tuple of (I, C) where I is the unique identifier and C is the
    desired command to be executed.
    """

    def _build(self):
        """Returns a many decider decider.

        Returns:
            A decider which is always terminal and returns nothing.
        """
        InnerI = TypeVar("InnerI")
        InnerE = TypeVar("InnerE")
        InnerC = TypeVar("InnerC")
        InnerS = TypeVar("InnerS")

        class InternalDecider(
            Decider[
                tuple[InnerI, InnerE],
                tuple[InnerI, InnerC],
                MutableMapping[InnerI, InnerS],
            ],
            Generic[InnerI, InnerE, InnerC, InnerS],
        ):
            def __init__(self, decider: Decider[InnerE, InnerC, InnerS]) -> None:
                """Create an instance of ManyDecider.

                Parameters:
                    decider: The type of decider we are holding multiples of.
                """
                self.decider = decider

            def evolve(
                self,
                state: MutableMapping[InnerI, InnerS],
                event: tuple[InnerI, InnerE],
            ) -> MutableMapping[InnerI, InnerS]:

                identifier = event[0]
                current_event = event[1]

                current_state = state.get(identifier)
                if current_state is None:
                    current_state = self.decider.initial_state()

                current_state = self.decider.evolve(current_state, current_event)
                state[identifier] = current_state

                return state

            def decide(
                self,
                command: tuple[InnerI, InnerC],
                state: MutableMapping[InnerI, InnerS],
            ) -> Iterator[tuple[InnerI, InnerE]]:
                identifier = command[0]
                current_command = command[1]

                current_state = state.get(identifier)
                if current_state is None:
                    current_state = self.decider.initial_state()

                yield from map(
                    lambda event: (identifier, event),
                    self.decider.decide(current_command, current_state),
                )

            def is_terminal(self, state: MutableMapping[InnerI, InnerS]) -> bool:
                for member_state in state.values():
                    if not self.decider.is_terminal(member_state):
                        return False
                return True

            def initial_state(self) -> MutableMapping[InnerI, InnerS]:
                return {}

        def constructor(decider: Decider[InnerE, InnerC, InnerS]):
            return InternalDecider[I, InnerE, InnerC, InnerS](decider)

        return constructor

    def __init__(self, identifier_type: Type[I]) -> None:
        self.identifier_type = identifier_type
        self.build = self._build()


class AdaptDecider(Generic[E, C, S, EO, CO, SO]):
    """A decider that translates from one set of events/commands/states to another.

    The AdaptDecider takes in a decider and makes a translation layer
    between the commands, events, and state internally and a new
    resulting type of command, event, and map. The purpose of this is
    to allow a Decider of one type to interact with a Decider of
    another type through translation.
    """

    def __init__(
        self,
        fci: Callable[[C], CO | None],
        fei: Callable[[E], EO | None],
        feo: Callable[[EO], E],
        fsi: Callable[[S], SO],
        decider: Decider[EO, CO, SO],
    ) -> None:
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
        """
        self._fci = fci
        self._fei = fei
        self._feo = feo
        self._fsi = fsi
        self._decider = decider

    def build(
        self,
    ) -> BaseDecider[E, C, S, SO]:
        """Create an adapted decider.

        Returns:
            A Decider with its functions wrapped by translation functions.
        """
        InnerE = TypeVar("InnerE")
        InnerC = TypeVar("InnerC")
        InnerS = TypeVar("InnerS")
        InnerSO = TypeVar("InnerSO")
        InnerCO = TypeVar("InnerCO")
        InnerEO = TypeVar("InnerEO")

        class InternalDecider(
            BaseDecider[InnerE, InnerC, InnerS, InnerSO],
            Generic[InnerE, InnerC, InnerS, InnerSO, InnerCO, InnerEO],
        ):
            def decide(self, command: InnerC, state: InnerS) -> Iterator[InnerE]:
                new_command = self._fci(command)
                if new_command is None:
                    return
                yield from map(
                    self._feo, self._decider.decide(new_command, self._fsi(state))
                )

            def evolve(self, state: InnerS, event: InnerE) -> InnerSO:
                new_event = self._fei(event)
                if new_event is None:
                    return self._fsi(state)
                return self._decider.evolve(self._fsi(state), new_event)

            def initial_state(self) -> InnerSO:
                return self._decider.initial_state()

            def is_terminal(self, state: InnerS) -> bool:
                return self._decider.is_terminal(self._fsi(state))

            def __init__(
                self,
                fci: Callable[[InnerC], InnerCO | None],
                fei: Callable[[InnerE], InnerEO | None],
                feo: Callable[[InnerEO], InnerE],
                fsi: Callable[[InnerS], InnerSO],
                decider: Decider[InnerEO, InnerCO, InnerSO],
            ) -> None:
                self._fci = fci
                self._fei = fei
                self._feo = feo
                self._fsi = fsi
                self._decider = decider

        return InternalDecider(
            self._fci, self._fei, self._feo, self._fsi, self._decider
        )


class MapDecider(Generic[E, C, SI, SA, SB]):
    """Map allows the translation of a Decider's state into a different state."""

    def __init__(self, f: Callable[[SA], SB], d: BaseDecider[E, C, SI, SA]) -> None:
        """Build a whose state is represented as the function `f(state)`.

        Parameters:
            f: A function to transform the state.
            d: The Decider we are using.
        """
        self._f = f
        self._d = d

    def build(self) -> BaseDecider[E, C, SI, SB]:
        """Build a whose state is represented as the function `f(state)`.

        Returns:
            A new Decider where `evolve` and `initial_state` both
            return `f(state_operation)`.
        """
        InnerE = TypeVar("InnerE")
        InnerC = TypeVar("InnerC")
        InnerSI = TypeVar("InnerSI")
        InnerSA = TypeVar("InnerSA")
        InnerSB = TypeVar("InnerSB")

        class InternalDecider(BaseDecider[InnerE, InnerC, InnerSI, InnerSB]):
            def decide(self, command: InnerC, state: InnerSI) -> Iterator[InnerE]:
                yield from self._d.decide(command, state)

            def evolve(self, state: InnerSI, event: InnerE) -> InnerSB:
                return self._f(self._d.evolve(state, event))

            def initial_state(self) -> InnerSB:
                return self._f(self._d.initial_state())

            def is_terminal(self, state: InnerSI) -> bool:
                return self._d.is_terminal(state)

            def __init__(
                self,
                f: Callable[[InnerSA], InnerSB],
                d: BaseDecider[InnerE, InnerC, InnerSI, InnerSA],
            ) -> None:
                self._f = f
                self._d = d

        return InternalDecider(self._f, self._d)


class Map2Decider(Generic[E, C, S, SX, SY, SI]):
    def __init__(
        self,
        f: Callable[[SX, SY], S],
        dx: BaseDecider[E, C, SI, SX],
        dy: BaseDecider[E, C, SI, SY],
    ) -> None:
        self._f = f
        self._dx = dx
        self._dy = dy

    def build(self) -> BaseDecider[E, C, SI, S]:

        InnerE = TypeVar("InnerE")
        InnerC = TypeVar("InnerC")
        InnerS = TypeVar("InnerS")
        InnerSX = TypeVar("InnerSX")
        InnerSY = TypeVar("InnerSY")
        InnerSI = TypeVar("InnerSI")

        class InternalDecider(BaseDecider[InnerE, InnerC, InnerSI, InnerS]):
            def decide(self, command: InnerC, state: InnerSI) -> Iterator[InnerE]:
                yield from self._dx.decide(command, state)
                yield from self._dy.decide(command, state)

            def evolve(self, state: InnerSI, event: InnerE) -> InnerS:
                sx = self._dx.evolve(state, event)
                sy = self._dy.evolve(state, event)
                return self._f(sx, sy)

            def initial_state(self) -> InnerS:
                return self._f(self._dx.initial_state(), self._dy.initial_state())

            def is_terminal(self, state: InnerSI) -> bool:
                return self._dx.is_terminal(state) and self._dy.is_terminal(state)

            def __init__(
                self,
                f: Callable[[InnerSX, InnerSY], InnerS],
                dx: BaseDecider[InnerE, InnerC, InnerSI, InnerSX],
                dy: BaseDecider[InnerE, InnerC, InnerSI, InnerSY],
            ) -> None:
                self._f = f
                self._dx = dx
                self._dy = dy

        return InternalDecider(self._f, self._dx, self._dy)
