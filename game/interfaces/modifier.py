from abc import ABC, abstractmethod
from typing import List

from game.interfaces.event import Event


class Modifier(ABC):
    """
    A modifier inspects a single Event and returns a list of Events to replace it.
    - Return [] to cancel.
    - Return [same_event] to leave unchanged.
    - Return multiple events to expand.
    - Return modfied events
    """
    @abstractmethod
    def apply_to_event(self, event: Event, game: "Game") -> List[Event]:
        pass