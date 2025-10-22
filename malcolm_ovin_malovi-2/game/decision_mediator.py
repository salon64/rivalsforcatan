# decision_mediator.py
from typing import Any
from .interfaces.mediator import Mediator

class DecisionMediator(Mediator):
    def ask_decision(self, player, decision_type: str, payload: Any) -> Any:
        return player.on_decision(decision_type, payload)
