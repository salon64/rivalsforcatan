import json
from pathlib import Path
from typing import Dict, Any

from .interfaces.card import Card

TEMPLATES_PATH = Path(__file__).with_name("card_templates.json")


def _stack_for_archetype(archetype: str) -> str:
    a = (archetype or "").lower()
    if a == "region":
        return "regions"
    if a in ("settlements", "settlement"):
        return "settlements"
    if a == "cities":
        return "cities"
    if a == "roads":
        return "roads"
    return "misc"


def load_templates(path: Path | None = None) -> list[Dict[str, Any]]:
    p = Path(path) if path is not None else TEMPLATES_PATH
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def create_card_instances_from_templates(templates: list[Dict[str, Any]]):
    """Return list of Card instances (not placed)."""
    instances = []
    for tpl in templates:
        copies = int(tpl.get("copies", 1))
        backs = tpl.get("card_backs", [None] * copies)
        positions = tpl.get("position", [None] * copies)
        for i in range(copies):
            runtime_id = f"{tpl['id']}-{i}"
            name = tpl.get("name", tpl["id"]) + (f" #{i+1}" if copies > 1 else "")
            card_type = tpl.get("archetype", tpl.get("id"))
            c = Card(id=runtime_id, name=name, card_type=card_type)
            # attach template refs for later behavior
            c.template_id = tpl.get("id")
            c.template = tpl
            # record which back and position correspond to this copy
            c.back = backs[i] if i < len(backs) else None
            c.template_position = positions[i] if i < len(positions) else None
            # populate template-driven fields
            c.resource = tpl.get("resource")
            c.base_yield = int(tpl.get("base_yield", 0))
            c.max_capacity = int(tpl.get("max_capacity", 0) or 0)
            dv = tpl.get("die_values")
            if isinstance(dv, list):
                try:
                    c.die_value = dv[i] if i < len(dv) else None
                except Exception:
                    c.die_value = None
            else:
                c.die_value = dv
            c.die_values = dv
            # initialize starting resources if provided
            start = tpl.get("starting_amount_resource")
            if isinstance(start, list) and tpl.get("resource"):
                # assign the ith starting amount if list length matches copies logic
                try:
                    amount = start[i] if i < len(start) else 0
                except Exception:
                    amount = 0
                if amount:
                    # use Card.add_resource which will respect max_capacity
                    c.add_resource(tpl["resource"], int(amount))
            instances.append(c)
    return instances


def setup_cards_into_game(game, templates_path: Path | None = None):
    """Load templates and place/create instances into game.game_state draw stacks or player boards.

    Rules used here:
    - Create draw stacks for: regions, settlements, cities, roads, misc
    - For each template copy: if its back is 'red' or 'blue' and it has a position, place it on that player's board at that position (owner_id set to the color string).
    - Otherwise, put the card instance into the draw stack determined by its archetype.

    Note: this uses color strings as player ids (e.g., 'red' or 'blue'). If your players have different ids, adapt accordingly.
    """
    templates = load_templates(templates_path)
    instances = create_card_instances_from_templates(templates)

    # ensure draw_stacks exist
    ds = game.game_state.draw_stacks
    for name in ("regions", "settlements", "cities", "roads", "misc"):
        ds.setdefault(name, [])

    for c in instances:
        back = getattr(c, "back", None)
        pos = getattr(c, "template_position", None)
        # place on player board if back indicates player color and position provided
        if isinstance(back, str) and back.lower() in ("red", "blue") and isinstance(pos, list) and len(pos) == 2:
            player_id = back.lower()
            x, y = pos
            c.owner_id = player_id
            c.position = (x, y)
            game.game_state.place_on_board(player_id, x, y, c)
        else:
            # push onto appropriate draw stack
            stack_name = _stack_for_archetype(getattr(c, "template", {}).get("archetype", "misc"))
            ds.setdefault(stack_name, []).append(c)

    # return created instances for inspection
    return instances


def print_game_state_summary(game) -> None:
    """Print a compact summary of draw stacks, player boards and card registry."""
    gs = game.game_state
    print("--- GameState Summary ---")
    # draw stacks
    print("Draw stacks:")
    for name, stack in gs.draw_stacks.items():
        print(f"  {name}: {len(stack)} cards")
        # print first few ids
        for c in stack[:10]:
            print(f"    - {getattr(c, 'id', None)}: {getattr(c, 'name', None)}")

    # player boards
    print("Player boards:")
    for pid, board in gs.player_boards.items():
        print(f"  player {pid}: {len(board)} placed cards")
        for (x, y), c in board.items():
            print(f"    - at ({x},{y}): {getattr(c, 'id', None)} {getattr(c, 'name', None)} owner={getattr(c,'owner_id',None)} die={getattr(c,'die_value',None)} resources={getattr(c,'stored_resources',{})}")

    # cards registry
    print("All cards (registry):")
    for cid, c in gs.cards.items():
        print(
            f"  {cid}: name={getattr(c,'name',None)} owner={getattr(c,'owner_id',None)} pos={getattr(c,'position',None)} "
            f"resource={getattr(c,'resource',None)} base_yield={getattr(c,'base_yield',None)} max_capacity={getattr(c,'max_capacity',None)} resources={getattr(c,'stored_resources',{})}"
        )

    # players in game state
    if getattr(gs, 'players', None):
        print("PlayerStates:")
        for pid, ps in gs.players.items():
            print(f"  {pid}: name={ps.name}")

    print("--- end summary ---")