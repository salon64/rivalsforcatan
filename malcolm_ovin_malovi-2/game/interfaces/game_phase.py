from abc import ABC, abstractmethod

class GamePhase(ABC):
    @abstractmethod
    def handle(self, game) -> None:
        """Handle the game logic for this phase."""

    @abstractmethod
    def next_phase(self) -> "GamePhase":
        """Return the next phase class"""