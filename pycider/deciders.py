import dataclasses
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, MutableMapping
from typing import Generic, Sequence, TypeVar

from pycider.types import Either, Left, Right

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class State(ABC):
    pass


@dataclasses.dataclass(frozen=True)
class Event:
    pass


@dataclasses.dataclass(frozen=True)
class Command:
    pass


E = TypeVar("E")
C = TypeVar("C")
S = TypeVar("S")
SI = TypeVar("SI")
SO = TypeVar("SO")


class BaseDecider(ABC, Generic[E, C, SI, SO]):
    @abstractmethod
    def initial_state(self) -> SO:
        """Starting state for a process.

        Returns
            The base state to begin the process with
        """
        pass

    @abstractmethod
    def evolve(self, state: SI, event: E) -> SO:
        """Update the process state based on the current event.

        Paramters
            state: State of the current process
            event: Event

        Returns
            An sequence of commands to act on.
        """
        pass

    @abstractmethod
    def is_terminal(self, state: SI) -> bool:
        """Checks if the current state is the end state for the process.

        Parameters
            state: State of the current process

        Returns
            A boolean indicating if a process is finished.
        """
        pass

    @abstractmethod
    def decide(self, command: C, state: SI) -> Sequence[E]:
        """React to an event by generating new commands.

        Parameters
            command: Operation to be processed
            state: State of the current process

        Returns
            A sequence of events to evolve the state on.
        """
        pass


class Decider(BaseDecider[E, C, S, S], Generic[E, C, S]):
    pass


class CatCommandWakeUp(Command):
    pass


class CatCommandGetToSleep(Command):
    pass


class CatStateAsleep(State):
    pass


class CatStateAwake(State):
    pass


class CatEventGotToSleep(Event):
    pass


class CatEventWokeUp(Event):
    pass


class Cat(Decider[Event, Command, State]):

    def initial_state(self) -> State:
        return CatStateAwake()

    def is_terminal(self, state: State) -> bool:
        return False

    def decide(self, command: Command, state: State) -> Sequence[Event]:
        match (command, state):
            case (CatCommandWakeUp(), CatStateAsleep()):
                return [CatEventWokeUp()]
            case CatCommandGetToSleep(), CatStateAwake():
                return [CatEventGotToSleep()]
            case _:
                return []

    def evolve(self, state: State, event: Event) -> State:
        match (state, event):
            case (CatStateAwake(), CatEventGotToSleep()):
                return CatStateAsleep()
            case (CatStateAsleep(), CatEventWokeUp()):
                return CatStateAwake()
            case _:
                return state


@dataclasses.dataclass(frozen=True)
class BulbCommandFit(Command):
    max_uses: int


@dataclasses.dataclass(frozen=True)
class BulbCommandSwitchOn(Command):
    pass


@dataclasses.dataclass(frozen=True)
class BulbCommandSwitchOff(Command):
    pass


@dataclasses.dataclass(frozen=True)
class BulbEventFitted(Event):
    max_uses: int


@dataclasses.dataclass(frozen=True)
class BulbEventSwitchedOn(Event):
    pass


@dataclasses.dataclass(frozen=True)
class BulbEventSwitchedOff(Event):
    pass


@dataclasses.dataclass(frozen=True)
class BulbEventBlew(Event):
    pass


@dataclasses.dataclass(frozen=True)
class BulbStateNotFitted(State):
    pass


@dataclasses.dataclass(frozen=True)
class BulbStateWorking(State):
    is_on: bool
    remaining_uses: int


@dataclasses.dataclass(frozen=True)
class BulbStateBlown(State):
    pass


class Bulb(Decider[Event, Command, State]):
    def decide(self, command: Command, state: State) -> Sequence[Event]:
        match command, state:
            case BulbCommandFit(), BulbStateNotFitted():
                return [BulbEventFitted(max_uses=command.max_uses)]
            case BulbCommandSwitchOn(), BulbStateWorking(
                is_on=False, remaining_uses=remaining_uses
            ) if remaining_uses > 0:
                return [BulbEventSwitchedOn()]
            case BulbCommandSwitchOn(), BulbStateWorking(is_on=False):
                return [BulbEventBlew()]
            case BulbCommandSwitchOff(), BulbStateWorking(is_on=True):
                return [BulbEventSwitchedOff()]
            case _:
                return []

    def evolve(self, state: State, event: Event) -> State:
        match state, event:
            case BulbStateNotFitted(), BulbEventFitted():
                return BulbStateWorking(is_on=False, remaining_uses=event.max_uses)
            case BulbStateWorking(), BulbEventSwitchedOn():
                return BulbStateWorking(
                    is_on=True, remaining_uses=state.remaining_uses - 1
                )
            case BulbStateWorking(), BulbEventSwitchedOff():
                return BulbStateWorking(
                    is_on=False, remaining_uses=state.remaining_uses
                )
            case BulbStateWorking(), BulbEventBlew():
                return BulbStateBlown()
            case _:
                return state

    def initial_state(self) -> State:
        return BulbStateNotFitted()

    def is_terminal(self, state: State) -> bool:
        return isinstance(state, BulbStateBlown)


CX = TypeVar("CX")
EX = TypeVar("EX")
SX = TypeVar("SX")
CY = TypeVar("CY")
EY = TypeVar("EY")
SY = TypeVar("SY")


class ComposeDecider(Generic[EX, CX, SX, EY, CY, SY]):
    @classmethod
    def compose(
        cls, dx: Decider[EX, CX, SX], dy: Decider[EY, CY, SY]
    ) -> Decider[Either[EX, EY], Either[CX, CY], tuple[SX, SY]]:
        class AnonymousDecider(Decider[Either[EX, EY], Either[CX, CY], tuple[SX, SY]]):
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

        return AnonymousDecider()


I = TypeVar("I")  # identifier


class ManyDecider(
    Decider[tuple[I, E], tuple[I, C], MutableMapping[I, S]], Generic[I, E, C, S]
):
    def __init__(self, aggregate: type[Decider[E, C, S]]) -> None:
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
    def adapt(
        cls,
        fci: Callable[[C], CO | None],
        fei: Callable[[E], EO | None],
        feo: Callable[[EO], E],
        fsi: Callable[[S], SO],
        decider: Decider[EO, CO, SO],
    ) -> BaseDecider[E, C, S, SO]:
        class AnonymousDecider(BaseDecider[E, C, S, SO]):
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

        return AnonymousDecider()


SA = TypeVar("SA")
SB = TypeVar("SB")


class MapDecider(Generic[E, C, SI, SA, SB]):
    @classmethod
    def map(
        f: Callable[[SA], SB], d: BaseDecider[E, C, SI, SA]
    ) -> BaseDecider[E, C, SI, SB]:
        class AnonymousDecider(BaseDecider[E, C, SI, SB]):
            def decide(self, command: C, state: SI) -> Sequence[E]:
                return d.decide(command, state)

            def evolve(self, state: SI, event: E) -> SB:
                return f(d.evolve(state, event))

            def initial_state(self) -> SB:
                return f(d.initial_state())

            def is_terminal(self, state: SI) -> bool:
                return d.is_terminal(state)

        return AnonymousDecider()


class Map2Decider(Generic[E, C, S, SX, SY, SI]):
    @classmethod
    def map(
        cls,
        f: Callable[[SX, SY], S],
        dx: BaseDecider[E, C, SI, SX],
        dy: BaseDecider[E, C, SI, SY],
    ) -> BaseDecider[E, C, SI, S]:
        class AnonymousDecider(BaseDecider[E, C, SI, S]):
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

        return AnonymousDecider()


def decider_apply(
    f: BaseDecider[E, C, SI, Callable[[SX], SO]], d: BaseDecider[E, C, SI, SX]
) -> BaseDecider[E, C, SI, SO]:
    return Map2Decider.map(lambda f, x: f(x), f, d)
