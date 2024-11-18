import dataclasses
from abc import ABC
from collections.abc import Iterator
from typing import cast

from pycider.deciders import ComposeDecider, Decider, ManyDecider
from pycider.processes import IProcess, ProcessAdapt, ProcessCombineWithDecider
from pycider.types import Left, Right
from pycider.utils import InMemory


class State(ABC):
    pass


class Event(ABC):
    pass


class Command(ABC):
    pass


class CatLightEventSwitchedOn(Event):
    pass


class CatLightEventWokeUp(Event):
    pass


class CatLightCommandWakeUp(Command):
    pass


class CatLightStateIdle(State):
    pass


class CatLightStateWakingUp(State):
    pass


class CatLight(IProcess[Event, Command, State]):
    def evolve(self, state: State, event: Event) -> State:
        match event:
            case CatLightEventSwitchedOn():
                return CatLightStateWakingUp()
            case CatLightEventWokeUp():
                return CatLightStateIdle()
            case _:
                return state

    def resume(self, state: State) -> Iterator[Command]:
        match state:
            case CatLightStateWakingUp():
                yield from [CatLightCommandWakeUp()]
            case _:
                yield from []

    def react(self, state: State, event: Event) -> Iterator[Command]:
        match state, event:
            case CatLightStateWakingUp(), CatLightEventSwitchedOn():
                yield from [CatLightCommandWakeUp()]
            case _:
                yield from []

    def initial_state(self) -> State:
        return CatLightStateIdle()

    def is_terminal(self, state: State) -> bool:
        return isinstance(state, CatLightStateIdle)


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

    def decide(self, command: Command, state: State) -> Iterator[Event]:
        match (command, state):
            case (CatCommandWakeUp(), CatStateAsleep()):
                yield from [CatEventWokeUp()]
            case CatCommandGetToSleep(), CatStateAwake():
                yield from [CatEventGotToSleep()]
            case _:
                yield from []

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
    def decide(self, command: Command, state: State) -> Iterator[Event]:
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


def test_cat_and_bulb() -> None:
    cnb = InMemory(ComposeDecider.build(Cat(), Bulb()))

    cnb(Left(CatCommandWakeUp()))
    cnb(Left(CatCommandGetToSleep()))
    cnb(Right(BulbCommandFit(max_uses=5)))
    cnb(Right(BulbCommandSwitchOn()))
    cnb(Right(BulbCommandSwitchOff()))

    assert len(cnb.state) == 2
    assert type(cnb.state[0]) is CatStateAsleep
    assert type(cnb.state[1]) is BulbStateWorking
    assert cast(BulbStateWorking, cnb.state[1]).is_on is False
    assert cast(BulbStateWorking, cnb.state[1]).remaining_uses == 4


def test_in_memory_many_cats() -> None:
    in_memory = InMemory(ManyDecider[str, Event, Command, State](Cat))

    in_memory(("boulette", CatCommandGetToSleep()))
    in_memory(("boulette", CatCommandWakeUp()))
    in_memory(("guevara", CatCommandWakeUp()))
    in_memory(("guevara", CatCommandGetToSleep()))

    assert type(in_memory.state["boulette"]) is CatStateAwake
    assert type(in_memory.state["guevara"]) is CatStateAsleep


def test_compose_process() -> None:
    cat_and_bulb = ComposeDecider.build(Cat(), Bulb())

    def select_event(event):
        match event:
            case Left(CatEventWokeUp()):
                return CatLightEventWokeUp()
            case Right(BulbEventSwitchedOn()):
                return CatLightEventSwitchedOn()
            case _:
                return None

    def command_converter(command):
        match command:
            case CatLightCommandWakeUp():
                return Left(CatCommandWakeUp())
            case _:
                raise RuntimeError("Improper state")

    adapted_process = ProcessAdapt.build(select_event, command_converter, CatLight())
    cat_bulb = ProcessCombineWithDecider.build(adapted_process, cat_and_bulb)

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
    assert cast(BulbStateWorking, cat_b.state[0][1]).is_on is False
    assert cast(BulbStateWorking, cat_b.state[0][1]).remaining_uses == 4
    assert type(cat_b.state[1]) is CatLightStateWakingUp
