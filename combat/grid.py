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


def render_grid(entities: list[dict], width: int = 10, height: int = 8) -> str:
    """Render the combat grid as an emoji string."""
    grid = build_empty_grid(width, height)
    grid = place_entities(grid, entities)

    col_labels = "　" + "".join(str(i) for i in range(width))
    rows = [col_labels]
    for y, row in enumerate(grid):
        row_label = str(y)
        rows.append(row_label + "".join(row))
    return "\n".join(rows)


def render_combat_status(entities: list[dict], round_num: int, current_name: str) -> str:
    """Render the full combat panel: grid + HP bars."""
    grid_str = render_grid(entities)
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
        hp_lines.append(
            f"{e['emoji']} **{e['name']}** [{bar}] {hp}/{max_hp} HP{status}{cond_str}"
        )
    hp_block = "\n".join(hp_lines)
    return f"```\n{grid_str}\n```\n{hp_block}\n\n▶️ 現在輪到：**{current_name}**  第{round_num}輪"


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