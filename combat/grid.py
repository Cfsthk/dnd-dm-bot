from __future__ import annotations
import config


def build_empty_grid(width: int, height: int) -> list[list[str]]:
    return [[config.EMPTY_CELL for _ in range(width)] for _ in range(height)]


def place_entities(grid: list[list[str]], entities: list[dict]) -> list[list[str]]:
    """Place entity emojis on a copy of the grid."""
    import copy
    g = copy.deepcopy(grid)
    for e in entities:
        x, y = e.get("x", 0), e.get("y", 0)
        if 0 <= y < len(g) and 0 <= x < len(g[0]):
            g[y][x] = e.get("emoji", config.MONSTER_EMOJIS["default"])
    return g


def place_items(grid: list[list[str]], items: list[dict], entities: list[dict]) -> tuple[list[list[str]], dict[tuple[int, int], list[dict]]]:
    """Stamp item emojis onto the grid.

    If a cell is already occupied by an entity, the entity emoji takes priority
    and the item is recorded in `overlaps` so it can be shown in the legend.
    Returns (updated_grid, overlaps) where overlaps maps (x,y) -> [item, ...].
    """
    import copy
    g = copy.deepcopy(grid)
    # Build a set of occupied cells
    entity_cells: set[tuple[int, int]] = {
        (e.get("x", 0), e.get("y", 0)) for e in entities
    }
    overlaps: dict[tuple[int, int], list[dict]] = {}

    for item in items:
        if not item.get("active", True):
            continue
        if item.get("owner_id"):      # picked up — not on the grid
            continue
        x, y = item.get("x", 0), item.get("y", 0)
        if not (0 <= y < len(g) and 0 <= x < len(g[0])):
            continue
        cell = (x, y)
        if cell in entity_cells:
            # Entity takes the cell; record overlap for the legend
            overlaps.setdefault(cell, []).append(item)
        else:
            g[y][x] = item.get("emoji", "📦")
    return g, overlaps


def render_grid(
    entities: list[dict],
    width: int = 10,
    height: int = 8,
    items: list[dict] | None = None,
) -> tuple[str, dict[tuple[int, int], list[dict]]]:
    """Render the combat grid as an emoji string.

    Returns (grid_string, overlaps) where overlaps holds items sharing a cell
    with an entity (to be shown in the item legend below the grid).
    """
    items = items or []
    grid = build_empty_grid(width, height)
    grid = place_entities(grid, entities)
    grid, overlaps = place_items(grid, items, entities)

    col_labels = "\u3000" + "".join(str(i) for i in range(width))
    rows = [col_labels]
    for y, row in enumerate(grid):
        row_label = str(y)
        rows.append(row_label + "".join(row))
    return "\n".join(rows), overlaps


def render_combat_status(
    entities: list[dict],
    round_num: int,
    current_name: str,
    items: list[dict] | None = None,
) -> str:
    """Render the full combat panel: grid + HP bars + item legend."""
    items = items or []
    grid_str, overlaps = render_grid(entities, items=items)

    # ── HP bars ──────────────────────────────────────────────
    hp_lines = []
    for e in entities:
        hp = e.get("hp", 0)
        max_hp = e.get("max_hp", 1)
        pct = hp / max_hp if max_hp > 0 else 0
        bar_len = 8
        filled = round(pct * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        status = ""
        if hp <= 0:
            status = " 💀倒下"
        elif pct <= 0.25:
            status = " 🩸瀕死"
        elif pct <= 0.5:
            status = " ❤️受傷"
        conds = "、".join(e.get("conditions", [])) or ""
        cond_str = f" [{conds}]" if conds else ""

        # Show item overlap indicator next to entity name
        cell = (e.get("x", 0), e.get("y", 0))
        overlap_str = ""
        if cell in overlaps:
            overlap_emojis = "".join(i.get("emoji", "📦") for i in overlaps[cell])
            overlap_str = f" ⚠️{overlap_emojis}"

        is_monster = e.get("entity_type") == "monster"
        if is_monster:
            # Hide exact HP numbers for foes — show bar + status only
            hp_lines.append(
                f"{e['emoji']} **{e['name']}** [{bar}]{status}{cond_str}{overlap_str}"
            )
        else:
            hp_lines.append(
                f"{e['emoji']} **{e['name']}** [{bar}] {hp}/{max_hp} HP{status}{cond_str}{overlap_str}"
            )
    hp_block = "\n".join(hp_lines)

    # ── Item legend (ground items only) ──────────────────────
    ground_items = [i for i in items if i.get("active", True) and not i.get("owner_id")]
    item_lines = []
    for i in ground_items:
        itype_label = {"env": "環境", "loot": "戰利品", "hazard": "危險"}.get(i.get("item_type", "env"), "物件")
        desc = f" — {i['description']}" if i.get("description") else ""
        item_lines.append(
            f"{i.get('emoji','📦')} **{i['name']}** ({itype_label}) 位置:({i['x']},{i['y']}){desc}"
        )
    item_block = ("\n🗺️ **場景物件**\n" + "\n".join(item_lines)) if item_lines else ""

    return (
        f"```\n{grid_str}\n```\n"
        f"{hp_block}"
        f"{item_block}\n\n"
        f"▶️ 現在輪到：**{current_name}**  第{round_num}輪"
    )


def get_adjacent_cells(x: int, y: int, width: int, height: int) -> list[tuple[int, int]]:
    """Return all cells within 5 feet (adjacent + diagonal)."""
    cells = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                cells.append((nx, ny))
    return cells


def is_in_melee_range(e1: dict, e2: dict) -> bool:
    """Check if two entities are within melee range (5 feet = 1 cell)."""
    return abs(e1["x"] - e2["x"]) <= 1 and abs(e1["y"] - e2["y"]) <= 1


def distance_between(e1: dict, e2: dict) -> int:
    """Chebyshev distance in cells (each = 5 feet)."""
    return max(abs(e1["x"] - e2["x"]), abs(e1["y"] - e2["y"]))
