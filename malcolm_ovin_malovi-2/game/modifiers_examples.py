from typing import List, TYPE_CHECKING
from .interfaces.modifier import Modifier
from .interfaces.event import Event
from .game_state import GameState

if TYPE_CHECKING:
    from .core import Game


class AddDecisionOptionModifier(Modifier):
    """Example modifier that decorates events which call ask_decision.

    It temporarily wraps game.ask_decision to augment the payload/options passed
    to players during a specific event.
    """

    def apply_to_event(self, event: Event, game: "Game") -> List[Event]:
        original_execute = event.execute

        def wrapped_execute(g: "Game", game_state: GameState):
            orig_ask = g.ask_decision

            def decorated_ask(player, decision_type: str, payload):
                if decision_type == "list" and isinstance(payload, dict) and "options" in payload:
                    new_payload = dict(payload)
                    new_payload["options"] = list(new_payload["options"]) + ["Extra option"]
                    return orig_ask(player, decision_type, new_payload)
                return orig_ask(player, decision_type, payload)

            try:
                g.ask_decision = decorated_ask
                return original_execute(g, game_state)
            finally:
                g.ask_decision = orig_ask

        event.execute = wrapped_execute
        return [event]


class BrickFactoryModifier(Modifier):
    """If a production event produces BRICK from a region adjacent to a Brick Factory
    placed on the board, increase the amount produced by 1.

    This is an example only — it assumes production events expose:
      - resource: a string or enum name like 'BRICK'
      - source_card: an object with a (x,y) coordinate or 'position' attribute
      - amount: integer amount produced
    The modifier returns modified events (here we modify in-place and return same event).
    """

    def apply_to_event(self, event: Event, game: "Game") -> List[Event]:
        # quick duck-typing check for a production event
        if not hasattr(event, "resource"):
            return [event]

        try:
            resource = getattr(event, "resource")
            # match canonical resource name 'brick'
            if str(resource).lower() == "brick":
                src = getattr(event, "source_card", None)
                if src is not None and hasattr(src, "position"):
                    x, y = src.position
                    # check neighbors for a brick factory across all player boards
                    for board in game.game_state.player_boards.values():
                        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                            obj = board.get((nx, ny))
                            if obj is not None and (
                                getattr(obj, "template_id", None) == "brick_factory" or
                                getattr(obj, "name", "").lower().startswith("brick factory")
                            ):
                                # increase amount
                                if hasattr(event, "amount"):
                                    event.amount = getattr(event, "amount") + 1
                                    return [event]
        except Exception:
            # be conservative: if anything goes wrong, leave the event unchanged
            return [event]

        return [event]


class ExampleAddOptionModifier(Modifier):
    """Adds an extra option to list decisions during the target event.

    If the extra option is selected, the modifier will handle it (print a message)
    and prevent the event's normal handling by causing ask_decision to return None
    to the wrapped event execute.
    """

    def apply_to_event(self, event: Event, game: "Game") -> List[Event]:
        original_execute = event.execute

        def wrapped_execute(g: "Game", game_state: GameState):
            orig_ask = g.ask_decision

            def decorated_ask(player, decision_type: str, payload):
                if decision_type == "list" and isinstance(payload, dict) and "options" in payload:
                    new_payload = dict(payload)
                    new_payload["options"] = list(new_payload["options"]) + ["Extra modifier option"]
                    choice = orig_ask(player, decision_type, new_payload)
                    # if player chose the extra option
                    if isinstance(choice, int) and choice == len(new_payload["options"]) - 1:
                        print(f"Modifier handled extra option for {player.name}")
                        # indicate modifier handled it by returning None to the caller
                        return None
                    return choice
                return orig_ask(player, decision_type, payload)

            try:
                g.ask_decision = decorated_ask
                return original_execute(g, game_state)
            finally:
                g.ask_decision = orig_ask

        event.execute = wrapped_execute
        return [event]
