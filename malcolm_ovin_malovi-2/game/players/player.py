from enum import Enum, auto
from typing import Any
from .strategies import PlayerStrategy



class Player:
    def __init__(self, name: str, strategy: PlayerStrategy):
        self.name = name
        self.strategy = strategy
        self.card_hand = []
        # tracking total amount of resources that player owns
        self.gold = 0
        self.fighting_points = 0

    def on_event(self, event_type: str, payload: Any):
        print(f"{self.name} received event {event_type}: {payload}")

    def on_decision(self, decision_type: str, payload: Any):
        return self.strategy.make_decision(decision_type, payload)
    
