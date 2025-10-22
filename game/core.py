# Import internal classes (absolute or relative)
from typing import List, Any
from game.modifierengine import ModifierEngine
from game.players.player import Player
from game.interfaces.event import Event
from .observers import Observer 
from .decision_mediator import DecisionMediator
from game.interfaces.game_phase import GamePhase
from .game_state import GameState, make_default_game_state
from .game_state import PlayerState



class Game:
    def __init__(self, initial_phase: GamePhase, victory_points_to_win:int=10):
        # behavioral player objects
        self.players: list[Player] = []
        self.active_player: Player | None = None
        self.observers: List[Observer] = []
        self.event_queue: List[Event] = []
        self.game_state: GameState = make_default_game_state()
        self.modifier_engine = ModifierEngine()
        self.mediator = DecisionMediator()
        self.phase: GamePhase = initial_phase
        self.current_player: Player | None = None
        self.victory_points_to_win = victory_points_to_win

    @property
    def finished(self):
        # check player victory points stored in GameState.players
        for ps in self.game_state.players.values():
            if ps.victory_points >= self.victory_points_to_win:
                # find behavior object for reporting winner (best effort)
                for p in self.players:
                    if getattr(p, "name", None) == ps.name:
                        self.winner = p
                        break
                return True
        return False
    
    # handle the observer pattern
    def add_observer(self, observer: Observer):
        self.observers.append(observer)

    def remove_observer(self, observer: Observer):
        self.observers.remove(observer)

    def notify_observers(self, event_type: str, payload: Any):
        for obs in list(self.observers):   # copy to avoid modification issues
            obs.on_event(event_type, payload)

    # game acts as mediator asking "players" for decitions
    def ask_decision(self, player, decision_type: str, payload: Any):
        return self.mediator.ask_decision(player, decision_type, payload)

    # small helper wrappers for common decision types
    def ask_choice(self, player, message: str, options: list) -> int | None:
        """Ask player to pick one option from `options`.

        Returns the chosen index (0-based) or None if a modifier handled the choice.
        """
        attempts = 0
        while True:
            choice = self.ask_decision(player, "list", {"message": message, "options": options})
            # allow modifiers to return None to indicate they handled the option
            if choice is None:
                return None
            try:
                if isinstance(choice, int) and 0 <= choice < len(options):
                    return choice
            except Exception:
                pass
            attempts += 1
            if attempts >= 3:
                return None

    def ask_quantity(self, player, message: str, minimum: int, maximum: int) -> int | None:
        """Ask player to pick a quantity between minimum and maximum inclusive.

        Returns the chosen integer or None if a modifier handled/aborted.
        """
        attempts = 0
        while True:
            ans = self.ask_decision(player, "quantity", {"message": message, "min": minimum, "max": maximum})
            if ans is None:
                return None
            try:
                if isinstance(ans, int) and minimum <= ans <= maximum:
                    return ans
            except Exception:
                pass
            attempts += 1
            if attempts >= 3:
                return None

    # player management
    def register_player(self, player: Player, color: str | None = None):
        """Register behavioral Player and create a PlayerState in game_state.

        Uses player's name as id by default; if you have explicit ids, adapt.
        """
        pid = getattr(player, "name")
        self.players.append(player)
        # create a PlayerState if one doesn't already exist (or was set to None)
        if pid not in self.game_state.players or self.game_state.players.get(pid) is None:
            from .game_state import PlayerState
            self.game_state.players[pid] = PlayerState(id=pid, name=player.name, color=color)

    def get_player_state(self, player_or_id) -> "PlayerState":
        pid = player_or_id if isinstance(player_or_id, str) else getattr(player_or_id, "name", None)
        return self.game_state.players.get(pid)

    def add_player(self, player: Player, color: str | None = None):
        """Compatibility wrapper used by main: registers player behavior and PlayerState."""
        self.register_player(player, color=color)
        if self.current_player is None:
            self.current_player = player

    # helpers for card-based resource model
    def get_player_cards(self, player_or_id) -> list:
        pid = player_or_id if isinstance(player_or_id, str) else getattr(player_or_id, "name", None)
        return [c for c in self.game_state.cards.values() if getattr(c, "owner_id", None) == pid]

    def get_player_total_resources(self, player_or_id) -> dict:
        totals = {}
        for c in self.get_player_cards(player_or_id):
            for r, amt in getattr(c, "stored_resources", {}).items():
                totals[r] = totals.get(r, 0) + amt
        return totals

    def spend_resource_from_card(self, player_or_id, resource: str, amount: int, preferred_card_id: str | None = None) -> int:
        """Attempt to remove up to `amount` of `resource` from one of the player's placed cards.

        If preferred_card_id is provided it will be attempted first. Returns the actual removed amount.
        """
        # normalize id and find behavioral player if possible
        behavioral_player = None
        if isinstance(player_or_id, str):
            pid = player_or_id
            # try to find behavioral player object by name
            for p in self.players:
                if getattr(p, "name", None) == pid:
                    behavioral_player = p
                    break
        else:
            behavioral_player = player_or_id
            pid = getattr(player_or_id, "name", None)

        # try preferred card first
        if preferred_card_id:
            card = self.game_state.cards.get(preferred_card_id)
            if card and getattr(card, "owner_id", None) == pid:
                removed = card.remove_resource(resource, amount)
                if removed:
                    return removed

        # gather candidate cards
        candidates = [c for c in self.get_player_cards(pid) if getattr(c, "stored_resources", {}).get(resource, 0) > 0]
        if not candidates:
            return 0

        # single candidate -> use it
        if len(candidates) == 1:
            return candidates[0].remove_resource(resource, amount)

        # multiple candidates -> ask the player which card to spend from
        if behavioral_player is not None:
            options = []
            id_map = []
            for c in candidates:
                label = f"{c.name} (id={getattr(c, 'id', None)}) at {getattr(c, 'position', None)}: {getattr(c, 'stored_resources', {}).get(resource, 0)} {resource}"
                options.append(label)
                id_map.append(getattr(c, "id", None))

            choice = None
            attempts = 0
            while choice is None or not (0 <= choice < len(options)):
                choice = self.ask_decision(behavioral_player, "list", {"message": f"Choose a card to spend {amount} {resource} from:", "options": options})
                attempts += 1
                if attempts >= 3:
                    break

            if isinstance(choice, int) and 0 <= choice < len(id_map):
                selected_card = self.game_state.cards.get(id_map[choice])
                if selected_card:
                    return selected_card.remove_resource(resource, amount)

        # fallback: pick first candidate
        return candidates[0].remove_resource(resource, amount)
    

    # the game handles state pattern
    def change_phase(self, next_phase: GamePhase):
        self.phase = next_phase
    
    # handle the events
    def enqueue_event(self, event: Event):
        """Enqueue an event after letting the modifier engine transform it.

        The modifier engine can cancel (return []), replace, expand, or
        decorate the event(s). Returned events are appended in order.
        """
        events = self.modifier_engine.process_event(event, self)
        for e in events:
            self.event_queue.append(e)

    def enqueue_event_front(self, event: Event):
        """Add event at the front of the queue (position 0)."""
        events = self.modifier_engine.process_event(event, self)
        # Insert so that the first returned event will be processed first
        for e in reversed(events):
            self.event_queue.insert(0, e)

    def step(self):
        """Process one event or move to the next phase."""
        # print(self.event_queue)
        if self.event_queue:
            event = self.event_queue.pop(0)
            # pass shared game_state to events
            event.execute(self, self.game_state)
        else:
            # If no events left, advance phase
            self.phase = self.phase.next_phase()
            self.phase.handle(self)

    def run_until(self, condition=None):
        """Run steps until condition(game) is True.

        If condition is None the loop runs indefinitely (until KeyboardInterrupt).
        """
        if condition is None:
            try:
                while True:
                    self.step()
            except KeyboardInterrupt:
                return
        else:
            while not condition(self):
                self.step()
    
    
    