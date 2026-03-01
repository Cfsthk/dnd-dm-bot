from __future__ import annotations
import random
from combat.mechanics import ability_modifier


def roll_initiative(dex_score: int) -> tuple[int, int]:
    """Roll initiative for a character. Returns (d20_roll, total)."""
    dex_mod = ability_modifier(dex_score)
    d20 = random.randint(1, 20)
    return d20, d20 + dex_mod


def build_initiative_order(combatants: list[dict]) -> list[dict]:
    """
    Each combatant dict: {id, name, dex, entity_type, user_id (opt), emoji}
    Returns sorted list with initiative scores added.
    """
    result = []
    for c in combatants:
        dex = c.get("dex", 10)
        d20, total = roll_initiative(dex)
        result.append({**c, "initiative_roll": d20, "initiative_total": total})
    # Sort by total desc, ties broken by dex desc, then random
    result.sort(key=lambda x: (x["initiative_total"], x.get("dex", 10), random.random()), reverse=True)
    return result


def format_initiative_list(order: list[dict]) -> str:
    lines = ["🎲 **先攻順序**"]
    for i, c in enumerate(order):
        marker = "▶️" if i == 0 else f"{i+1}."
        lines.append(
            f"{marker} {c['emoji']} **{c['name']}** — 先攻 {c['initiative_total']} "
            f"（擲出{c['initiative_roll']}+{c['initiative_total']-c['initiative_roll']}）"
        )
    return "\n".join(lines)


def advance_turn(current_turn: int, order_length: int) -> tuple[int, int, bool]:
    """Advance to next turn. Returns (new_turn_index, new_round, round_incremented)."""
    next_turn = (current_turn + 1) % order_length
    round_inc = next_turn == 0
    return next_turn, round_inc


def format_turn_header(combatant: dict, round_num: int) -> str:
    return (
        f"⚔️ **第{round_num}輪** — 輪到 {combatant['emoji']} **{combatant['name']}**！\n"
        f"HP：{combatant.get('hp', '?')}/{combatant.get('max_hp', '?')}  "
        f"AC：{combatant.get('ac', '?')}"
    )