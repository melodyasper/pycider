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
    Left,
    ManyDecider,
    Right,
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


if __name__ == "__main__":
    in_memory = InMemory(ManyDecider[str, Event, Command, State](Cat))

    in_memory(("Steve", CatCommandGetToSleep()))
    in_memory(("Steve", CatCommandWakeUp()))

    in_memory(("Joe", CatCommandGetToSleep()))
    in_memory(("Joe", CatCommandWakeUp()))

    print(f"{in_memory.state=}")

    cd = ComposeDecider.compose(ManyDecider[str, Event, Command, State](Cat), Cat())
    composed_cats_in_memory = InMemory(cd)
    composed_cats_in_memory(Left(("Steve", CatCommandGetToSleep())))
    composed_cats_in_memory(Right(CatCommandGetToSleep()))

    print(f"{composed_cats_in_memory.state=}")

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
