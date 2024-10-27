from typing import Generic, Sequence, TypeVar

from pycider.deciders import Decider

E = TypeVar("E")
C = TypeVar("C")
S = TypeVar("S")


class InMemory(Generic[E, C, S]):
    def __init__(self, decider: Decider[E, C, S]) -> None:
        self.decider = decider
        self.state: S = self.decider.initial_state()

    def command(self, command: C):
        events = self.decider.decide(command, self.state)
        for event in events:
            self.state = self.decider.evolve(self.state, event)
        return events

    def __call__(self, command: C) -> Sequence[E]:
        return self.command(command)
