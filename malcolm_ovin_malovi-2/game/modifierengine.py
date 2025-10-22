from typing import List
from game.interfaces.event import Event
from game.interfaces.modifier import Modifier


class ModifierEngine:
    def __init__(self):
        self.modifiers: List[Modifier] = []

    def register(self, modifier: Modifier):
        self.modifiers.append(modifier)

    def unregister(self, modifier: Modifier):
        self.modifiers.remove(modifier)

    def process_event(self, event: Event, game: "Game") -> List[Event]:
        events: List[Event] = [event]
        for mod in list(self.modifiers):              # order matters; copy for safety
            new_events: List[Event] = []
            for e in events:
                new_events.extend(mod.apply_to_event(e, game))
            events = new_events
            if not events:
                break
        return events