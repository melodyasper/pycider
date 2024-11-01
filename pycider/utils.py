from typing import Generic, Sequence, TypeVar

from pycider.deciders import Decider

E = TypeVar("E")
C = TypeVar("C")
S = TypeVar("S")


class InMemory(Generic[E, C, S]):
    """Runs a decider in memory, performing decide and evolving the state."""

    def __init__(self, decider: Decider[E, C, S]) -> None:
        """Setup an in-memory executor for a decider.

        Parameters:
            decider: The decider to be stored internally.
        """
        self._decider = decider
        self.state: S = self._decider.initial_state()  #: State of the decider

    def command(self, command: C) -> Sequence[E]:
        """Decide over a command and evolves the internal state.

        Parameters:
            command: Command to decide over

        Returns:
            The events that were evolved over resulting from decide
        """
        events = self._decider.decide(command, self.state)
        for event in events:
            self.state = self._decider.evolve(self.state, event)
        return events

    def __call__(self, command: C) -> Sequence[E]:
        """Decide over a command and evolves the internal state.

        Parameters:
            command: Command to decide over

        Returns:
            The events that were evolved over resulting from decide
        """
        return self.command(command)
