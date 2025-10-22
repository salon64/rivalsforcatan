# Import only Python built-ins
from dataclasses import dataclass
from typing import List, TYPE_CHECKING
from ..core import Game
from game.interfaces.event import Event
from ..game_state import GameState
from ..card_factory import setup_cards_into_game
import random

if TYPE_CHECKING:
    from game.players.player import Player
    from game.interfaces.card import RegionCard

# examples 
class ReadyCheckEvent(Event):
    def execute(self, game: Game, game_state: GameState):
        ready: List[bool] = []
        for p in game.players:
            ans = None
            while ans not in (0, 1):
                ans = game.ask_decision(
                    p,
                    "list",
                    {
                        "message": f"{p.name}, are you ready?",
                        "options": ["No", "Yes"],
                    }
                )
                if ans not in (0, 1):
                    print(f"{p.name} gave invalid response. Asking again...")

            ready.append(bool(ans))  # 0 → False, 1 → True

        if all(ready):
            game.notify_observers(
                "game_starting",
                {"players": [p.name for p in game.players]}
            )

class NumberChoiceEvent(Event):
    def execute(self, game: Game, game_state: GameState):
        player = game.current_player
        ans = None
        while ans is None or not (0 <= ans <= 9):
            ans = game.ask_decision(
                player,
                "quantity",
                {
                    "message": f"{player.name}, choose a number between 0 and 9:",
                    "min": 0,
                    "max": 9,
                }
            )
            if ans is None or not (0 <= ans <= 9):
                print(f"{player.name} gave invalid response. Asking again...")

        game.notify_observers(
            "number_chosen",
            {"player": player.name, "value": ans}
        )


class ExampleChoiceEvent(Event):
    """Presents the player with 5 choices; selected choice enqueues a PrintEvent or other events."""
    def execute(self, game: Game, game_state: GameState):
        player = game.current_player
        options = [f"Option {i+1}" for i in range(5)]
        choice = game.ask_choice(player, f"{player.name}, pick an option:", options)
        if choice is None:
            # a modifier may have handled the decision
            return

        # for demonstration, enqueue a PrintEvent describing the choice
        game.enqueue_event(PrintEvent(f"{player.name} chose {options[choice]}"))


class PrintEvent(Event):
    message: str

    def __init__(self, message: str):
        self.message = message

    def execute(self, game: Game, game_state: GameState):
        print(self.message)


class SetUpCardsEvent(Event):
    """Populate the game's draw stacks and player boards from card templates."""
    def execute(self, game: Game, game_state: GameState):
        instances = setup_cards_into_game(game)
        # print a debug summary so the developer can inspect what was added
        try:
            from ..card_factory import print_game_state_summary
            print_game_state_summary(game)
        except Exception:
            pass
        game.notify_observers("cards_setup", {"count": len(instances)})


@dataclass
class ProduceResourceEvent(Event):
    """A production event caused by a production die: the source card
    produces `amount` of `resource` and stores it on the card itself.
    """
    player: "Player"
    source_card: "RegionCard"
    resource: str
    amount: int

    def execute(self, game: Game, game_state: GameState):
        src = self.source_card
        if hasattr(src, "add_resource"):
            src.add_resource(self.resource, self.amount)
        else:
            if not hasattr(src, "stored_resources"):
                src.stored_resources = {}
            src.stored_resources[self.resource] = src.stored_resources.get(self.resource, 0) + self.amount


class EventProductionDie(Event):
    """Roll two production dice and enqueue ProduceResourceEvent for every placed
    card whose `die_value` equals a roll. Doubles produce twice (two enqueues).

    This intentionally ignores event-dice logic for now and focuses only on
    production dice handling.
    """
    def execute(self, game: Game, game_state: GameState):
        rng = random.Random()
        # Roll two dice: one for production effects, one reserved for "event" dice
        production_die = rng.randint(1, 6)
        event_die = rng.randint(1, 6)
        print(f"Production die: {production_die}, Event die: {event_die}")

        # Only process production_die for now (event_die is ignored)
        for pid, board in game_state.player_boards.items():
            for (x, y), card in board.items():
                dv = getattr(card, "die_value", None)
                if dv is None:
                    continue
                try:
                    if int(dv) == int(production_die):
                        resource = getattr(card, "resource", None)
                        amount = getattr(card, "base_yield", 0) or 0
                        if resource and amount > 0:
                            # find behavioral player object
                            beh = None
                            for p in game.players:
                                if getattr(p, "name", None) == pid:
                                    beh = p
                                    break
                            game.enqueue_event(ProduceResourceEvent(beh, card, resource, amount))
                except Exception:
                    continue

