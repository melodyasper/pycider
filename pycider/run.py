from pycider.deciders import (
    Bulb,
    BulbCommandFit,
    BulbCommandSwitchOff,
    BulbCommandSwitchOn,
    BulbEventSwitchedOn,
    Cat,
    CatCommandGetToSleep,
    CatCommandWakeUp,
    CatEventWokeUp,
    Command,
    ComposeDecider,
    Event,
    ManyDecider,
    State,
)
from pycider.infra import InMemory
from pycider.procs import (
    CatLight,
    CatLightCommandWakeUp,
    CatLightEventSwitchedOn,
    CatLightEventWokeUp,
    Process,
    ProcessCombineWithDecider,
)
from pycider.types import Left, Right


def cat_and_bulb() -> None:

    cnb = InMemory(ComposeDecider.compose(Cat(), Bulb()))

    cnb(Left(CatCommandWakeUp()))
    cnb(Left(CatCommandGetToSleep()))
    cnb(Right(BulbCommandFit(max_uses=5)))
    cnb(Right(BulbCommandSwitchOn()))
    cnb(Right(BulbCommandSwitchOff()))

    print(f"{cnb.state=}")


def in_memory_many_cats() -> None:
    in_memory = InMemory(ManyDecider[str, Event, Command, State](Cat))

    in_memory(("boulette", CatCommandGetToSleep()))
    in_memory(("boulette", CatCommandWakeUp()))

    in_memory(("guevara", CatCommandWakeUp()))
    in_memory(("guevara", CatCommandGetToSleep()))

    print(f"{in_memory.state=}")


def compose_process() -> None:
    cat_and_bulb = ComposeDecider.compose(Cat(), Bulb())

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

    adapted_process = Process.adapt(select_event, command_converter, CatLight())
    cat_bulb = ProcessCombineWithDecider.combine(adapted_process, cat_and_bulb)
    cat_b = InMemory(cat_bulb)
    cat_b(Right(BulbCommandFit(max_uses=5)))
    cat_b(Left(CatCommandGetToSleep()))
    cat_b(Left(CatCommandWakeUp()))
    cat_b(Right(BulbCommandSwitchOn()))
    cat_b(Right(BulbCommandSwitchOff()))

    print(f"{cat_b.state=}")
