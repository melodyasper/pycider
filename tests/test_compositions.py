import dataclasses
from abc import ABC
from collections.abc import Iterator

from pycider.deciders import ComposeDecider, Decider, ManyDecider
from pycider.processes import IProcess, ProcessAdapt, ProcessCombineWithDecider
from pycider.types import Either, Left, Right
from pycider.utils import InMemory


class State(ABC):
    pass


class Event(ABC):
    pass


class Command(ABC):
    pass


class CatLightState(State):
    pass


class CatLightEvent(Event):
    pass


class CatLightCommand(Command):
    pass


class CatLightEventSwitchedOn(CatLightEvent):
    pass


class CatLightEventWokeUp(CatLightEvent):
    pass


class CatLightCommandWakeUp(CatLightCommand):
    pass


class CatLightStateIdle(CatLightState):
    pass


class CatLightStateWakingUp(CatLightState):
    pass


class CatLight(IProcess[CatLightEvent, CatLightCommand, CatLightState]):
    def evolve(self, state: CatLightState, event: CatLightEvent) -> CatLightState:
        match event:
            case CatLightEventSwitchedOn():
                return CatLightStateWakingUp()
            case CatLightEventWokeUp():
                return CatLightStateIdle()
            case _:
                return state

    def resume(self, state: CatLightState) -> Iterator[CatLightCommand]:
        match state:
            case CatLightStateWakingUp():
                yield from [CatLightCommandWakeUp()]
            case _:
                yield from []

    def react(
        self, state: CatLightState, event: CatLightEvent
    ) -> Iterator[CatLightCommand]:
        match state, event:
            case CatLightStateWakingUp(), CatLightEventSwitchedOn():
                yield from [CatLightCommandWakeUp()]
            case _:
                yield from []

    def initial_state(self) -> CatLightState:
        return CatLightStateIdle()

    def is_terminal(self, state: CatLightState) -> bool:
        return isinstance(state, CatLightStateIdle)


class CatState(State):
    pass


class CatEvent(Event):
    pass


class CatCommand(Command):
    pass


class CatCommandWakeUp(CatCommand):
    pass


class CatCommandGetToSleep(CatCommand):
    pass


class CatStateAsleep(CatState):
    pass


class CatStateAwake(CatState):
    pass


class CatEventGotToSleep(CatEvent):
    pass


class CatEventWokeUp(CatEvent):
    pass


class Cat(Decider[CatEvent, CatCommand, CatState]):

    def initial_state(self) -> CatState:
        return CatStateAwake()

    def is_terminal(self, state: CatState) -> bool:
        return False

    def decide(self, command: CatCommand, state: CatState) -> Iterator[CatEvent]:
        match (command, state):
            case (CatCommandWakeUp(), CatStateAsleep()):
                yield from [CatEventWokeUp()]
            case CatCommandGetToSleep(), CatStateAwake():
                yield from [CatEventGotToSleep()]
            case _:
                yield from []

    def evolve(self, state: CatState, event: CatEvent) -> CatState:
        match (state, event):
            case (CatStateAwake(), CatEventGotToSleep()):
                return CatStateAsleep()
            case (CatStateAsleep(), CatEventWokeUp()):
                return CatStateAwake()
            case _:
                return state


class BulbState(State):
    pass


class BulbEvent(Event):
    pass


class BulbCommand(Command):
    pass


@dataclasses.dataclass(frozen=True)
class BulbCommandFit(BulbCommand):
    max_uses: int


@dataclasses.dataclass(frozen=True)
class BulbCommandSwitchOn(BulbCommand):
    pass


@dataclasses.dataclass(frozen=True)
class BulbCommandSwitchOff(BulbCommand):
    pass


@dataclasses.dataclass(frozen=True)
class BulbEventFitted(BulbEvent):
    max_uses: int


@dataclasses.dataclass(frozen=True)
class BulbEventSwitchedOn(BulbEvent):
    pass


@dataclasses.dataclass(frozen=True)
class BulbEventSwitchedOff(BulbEvent):
    pass


@dataclasses.dataclass(frozen=True)
class BulbEventBlew(BulbEvent):
    pass


@dataclasses.dataclass(frozen=True)
class BulbStateNotFitted(BulbState):
    pass


@dataclasses.dataclass(frozen=True)
class BulbStateWorking(BulbState):
    is_on: bool
    remaining_uses: int


@dataclasses.dataclass(frozen=True)
class BulbStateBlown(BulbState):
    pass


class Bulb(Decider[BulbEvent, BulbCommand, BulbState]):
    def decide(self, command: BulbCommand, state: BulbState) -> Iterator[BulbEvent]:
        match command, state:
            case BulbCommandFit(), BulbStateNotFitted():
                yield from [BulbEventFitted(max_uses=command.max_uses)]
            case BulbCommandSwitchOn(), BulbStateWorking(
                is_on=False, remaining_uses=remaining_uses
            ) if remaining_uses > 0:
                yield from [BulbEventSwitchedOn()]
            case BulbCommandSwitchOn(), BulbStateWorking(is_on=False):
                yield from [BulbEventBlew()]
            case BulbCommandSwitchOff(), BulbStateWorking(is_on=True):
                yield from [BulbEventSwitchedOff()]
            case _:
                yield from []

    def evolve(self, state: BulbState, event: BulbEvent) -> BulbState:
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

    def initial_state(self) -> BulbState:
        return BulbStateNotFitted()

    def is_terminal(self, state: BulbState) -> bool:
        return isinstance(state, BulbStateBlown)


def test_cat_and_bulb() -> None:
    composed_decider = ComposeDecider(Cat(), Bulb()).build()
    cnb = InMemory(composed_decider)

    cnb(Left(CatCommandWakeUp()))
    cnb(Left(CatCommandGetToSleep()))
    cnb(Right(BulbCommandFit(max_uses=5)))
    cnb(Right(BulbCommandSwitchOn()))
    cnb(Right(BulbCommandSwitchOff()))

    assert len(cnb.state) == 2
    assert type(cnb.state[0]) is CatStateAsleep
    assert type(cnb.state[1]) is BulbStateWorking
    assert cnb.state[1].is_on is False
    assert cnb.state[1].remaining_uses == 4


def test_in_memory_many_cats() -> None:
    decider = ManyDecider(str).build(Cat())
    in_memory = InMemory(decider)

    in_memory(("boulette", CatCommandGetToSleep()))
    in_memory(("boulette", CatCommandWakeUp()))
    in_memory(("guevara", CatCommandWakeUp()))
    in_memory(("guevara", CatCommandGetToSleep()))

    assert type(in_memory.state["boulette"]) is CatStateAwake
    assert type(in_memory.state["guevara"]) is CatStateAsleep


def test_compose_process() -> None:
    cat_and_bulb = ComposeDecider(Cat(), Bulb()).build()

    # event in, event out
    def select_event(event: Either[CatEvent, BulbEvent]) -> CatLightEvent | None:
        match event:
            case Left(CatEventWokeUp()):
                return CatLightEventWokeUp()
            case Right(BulbEventSwitchedOn()):
                return CatLightEventSwitchedOn()
            case _:
                return None

    # command out, command in
    def command_converter(command: CatLightCommand) -> Either[CatCommand, BulbCommand]:
        match command:
            case CatLightCommandWakeUp():
                return Left(CatCommandWakeUp())
            case _:
                raise RuntimeError("Improper state")

    adapted_process = ProcessAdapt(select_event, command_converter, CatLight()).build()

    cat_bulb = ProcessCombineWithDecider(adapted_process, cat_and_bulb).build()

    cat_b = InMemory(cat_bulb)
    cat_b(Right(BulbCommandFit(max_uses=5)))
    cat_b(Left(CatCommandGetToSleep()))
    cat_b(Left(CatCommandWakeUp()))
    cat_b(Right(BulbCommandSwitchOn()))
    cat_b(Right(BulbCommandSwitchOff()))

    assert len(cat_b.state) == 2
    assert len(cat_b.state[0]) == 2
    assert type(cat_b.state[0][0]) is CatStateAwake
    assert type(cat_b.state[0][1]) is BulbStateWorking
    assert cat_b.state[0][1].is_on is False
    assert cat_b.state[0][1].remaining_uses == 4
    assert type(cat_b.state[1]) is CatLightStateWakingUp
