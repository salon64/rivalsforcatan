from typing import Protocol, Any

class Mediator(Protocol):
    def ask_decision(self, player, decision_type: str, payload: Any) -> Any:
        ...
