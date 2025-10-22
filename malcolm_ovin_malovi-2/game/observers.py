# observers.py
from typing import Protocol, Any

class Observer(Protocol):
    def on_event(self, event_type: str, payload: Any) -> None:
        ...
