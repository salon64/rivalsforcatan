# Event base class
from abc import ABC, abstractmethod
from ..game_state import GameState


class Event(ABC):
    @abstractmethod
    def execute(self, game, game_state: GameState) -> None:
        """Execute the event on the given game instance."""
        
