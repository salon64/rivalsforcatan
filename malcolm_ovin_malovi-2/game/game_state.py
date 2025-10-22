from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass
class PlayerState:
    id: str
    name: str
    # other persistent per-player fields may be added here


@dataclass
class GameState:
    """Shared, overall game state passed into events.

    draw_stacks: a mapping of stack name to list (top at end)
    player_board: a mapping of (x, y) coordinates to occupying object (card, token, etc.)
    """
    draw_stacks: Dict[str, list] = field(default_factory=dict)
    # boards: mapping player_id -> mapping coordinate -> placed object
    player_boards: Dict[str, Dict[Tuple[int, int], Any]] = field(default_factory=dict)
    # registry of all placed cards by id
    cards: Dict[str, Any] = field(default_factory=dict)
    # persistent per-player state
    players: Dict[str, "PlayerState"] = field(default_factory=dict)

    # helper methods to manipulate the board
    def place_on_board(self, player_id: str, x: int, y: int, obj: Any) -> None:
        board = self.player_boards.setdefault(player_id, {})
        board[(x, y)] = obj
        # if obj has id register it
        if hasattr(obj, "id"):
            self.cards[obj.id] = obj

    def remove_from_board(self, player_id: str, x: int, y: int) -> None:
        board = self.player_boards.get(player_id, {})
        obj = board.pop((x, y), None)
        if obj is not None and hasattr(obj, "id"):
            self.cards.pop(obj.id, None)

    def get_at(self, player_id: str, x: int, y: int) -> Any | None:
        return self.player_boards.get(player_id, {}).get((x, y))

    def neighbors(self, x: int, y: int):
        # 4-neighbors; change to hex adjacency if needed later
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yield (x + dx, y + dy)


def make_default_game_state() -> GameState:
    """Return a minimal default GameState with one draw stack prefilled.

    The user said to add one draw stack initially; we'll create a 'development' stack as an example.
    """
    gs = GameState()
    gs.draw_stacks["development"] = []
    return gs
