from __future__ import annotations
import random
from typing import Optional


def roll(dice: str) -> tuple[int, list[int]]:
    """Parse and roll a dice expression like '2d6', '1d20', 'd8'.
    Returns (total, [individual_rolls])."""
    dice = dice.strip().lower()
    if dice.startswith("d"):
        dice = "1" + dice
    count_str, sides_str = dice.split("d")
    count = int(count_str)
    sides = int(sides_str)
    rolls = [random.randint(1, sides) for _ in range(count)]
    return sum(rolls), rolls


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def attack_roll(attack_bonus: int, advantage: bool = False, disadvantage: bool = False) -> tuple[int, int, bool]:
    """Roll an attack. Returns (d20_result, total, is_crit)."""
    r1 = random.randint(1, 20)
    r2 = random.randint(1, 20)
    if advantage and not disadvantage:
        d20 = max(r1, r2)
    elif disadvantage and not advantage:
        d20 = min(r1, r2)
    else:
        d20 = r1
    is_crit = d20 == 20
    total = d20 + attack_bonus
    return d20, total, is_crit


def damage_roll(dice_expr: str, modifier: int = 0, is_crit: bool = False) -> tuple[int, list[int]]:
    """Roll damage, doubling dice on a critical hit."""
    if is_crit:
        total1, rolls1 = roll(dice_expr)
        total2, rolls2 = roll(dice_expr)
        return total1 + total2 + modifier, rolls1 + rolls2
    total, rolls = roll(dice_expr)
    return total + modifier, rolls


def saving_throw(dc: int, save_bonus: int, advantage: bool = False, disadvantage: bool = False) -> tuple[bool, int]:
    """Return (success, roll_total)."""
    r1 = random.randint(1, 20)
    r2 = random.randint(1, 20)
    if advantage and not disadvantage:
        d20 = max(r1, r2)
    elif disadvantage and not advantage:
        d20 = min(r1, r2)
    else:
        d20 = r1
    total = d20 + save_bonus
    return total >= dc, total


def death_save() -> tuple[str, int]:
    """Roll a death saving throw. Returns ('success'|'failure'|'stable'|'dead', roll)."""
    result = random.randint(1, 20)
    if result == 20:
        return "stable", result  # Regain 1 HP
    if result == 1:
        return "critical_failure", result  # Counts as 2 failures
    if result >= 10:
        return "success", result
    return "failure", result


def skill_check(dc: int, skill_bonus: int, advantage: bool = False, disadvantage: bool = False) -> tuple[bool, int]:
    """Return (success, roll_total)."""
    r1 = random.randint(1, 20)
    r2 = random.randint(1, 20)
    if advantage and not disadvantage:
        d20 = max(r1, r2)
    elif disadvantage and not advantage:
        d20 = min(r1, r2)
    else:
        d20 = r1
    total = d20 + skill_bonus
    return total >= dc, total


def calculate_ac(base_armor: int, dex_mod: int, shield: bool = False, magic_bonus: int = 0) -> int:
    return base_armor + dex_mod + (2 if shield else 0) + magic_bonus


def xp_for_cr(cr: float) -> int:
    table = {
        0: 10, 0.125: 25, 0.25: 50, 0.5: 100,
        1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800,
        6: 2300, 7: 2900, 8: 3900, 9: 5000, 10: 5900,
    }
    return table.get(cr, 0)


MONSTER_STATS: dict[str, dict] = {
    "goblin": {
        "name_zh": "地精", "hp": 7, "max_hp": 7, "ac": 15, "speed": 30,
        "attack": "+4", "damage": "1d6+2", "damage_type": "刺擊",
        "str": 8, "dex": 14, "con": 10, "int": 10, "wis": 8, "cha": 8,
        "cr": 0.25, "emoji": "👺",
        "actions": ["短劍攻擊", "躲避（躲入掩體）"],
        "traits": ["靈巧逃脫：可用附贈行動脱離接戰"],
    },
    "hobgoblin": {
        "name_zh": "地獄地精", "hp": 11, "max_hp": 11, "ac": 18, "speed": 30,
        "attack": "+3", "damage": "1d8+1", "damage_type": "斬擊",
        "str": 13, "dex": 12, "con": 12, "int": 10, "wis": 10, "cha": 9,
        "cr": 0.5, "emoji": "👹",
        "actions": ["長劍攻擊", "長弓攻擊（遠程，1d8+1）"],
        "traits": ["軍事優勢：對側翼目標+2d6傷害"],
    },
    "bugbear": {
        "name_zh": "蟲熊人", "hp": 27, "max_hp": 27, "ac": 16, "speed": 30,
        "attack": "+4", "damage": "2d8+2", "damage_type": "穿刺",
        "str": 15, "dex": 14, "con": 13, "int": 8, "wis": 11, "cha": 9,
        "cr": 1, "emoji": "🐻",
        "actions": ["晨星攻擊 × 2", "標槍（遠程）"],
        "traits": ["突然襟擊：驚訝目標+2d6傷害", "長臂：近戰範圍10呎"],
    },
    "wolf": {
        "name_zh": "狼", "hp": 11, "max_hp": 11, "ac": 13, "speed": 40,
        "attack": "+4", "damage": "2d4+2", "damage_type": "穿刺",
        "str": 12, "dex": 15, "con": 12, "int": 3, "wis": 12, "cha": 6,
        "cr": 0.25, "emoji": "🐺",
        "actions": ["撕咬攻擊"],
        "traits": ["群體戰術：當盟友相鄰時獲得優勢", "撲倒：命中DC11力量豁免否則倒地"],
    },
    "skeleton": {
        "name_zh": "骷髏", "hp": 13, "max_hp": 13, "ac": 13, "speed": 30,
        "attack": "+4", "damage": "1d6+2", "damage_type": "穿刺",
        "str": 10, "dex": 14, "con": 15, "int": 6, "wis": 8, "cha": 5,
        "cr": 0.25, "emoji": "💀",
        "actions": ["短弓攻擊（遠程，1d6+2）", "短劍攻擊"],
        "traits": ["不死免疫：毒素、疲勞、恐懼", "弱點：鈣擊傷害"],
    },
    "zombie": {
        "name_zh": "僵屍", "hp": 22, "max_hp": 22, "ac": 8, "speed": 20,
        "attack": "+3", "damage": "1d6+1", "damage_type": "鈣擊",
        "str": 13, "dex": 6, "con": 16, "int": 3, "wis": 6, "cha": 5,
        "cr": 0.25, "emoji": "🧟",
        "actions": ["鐵拳攻擊"],
        "traits": ["不死韌性：當HP歸零時DC5體質豁免維持1HP（每輪一次）"],
    },
    "nothic": {
        "name_zh": "獨眼怪", "hp": 45, "max_hp": 45, "ac": 15, "speed": 30,
        "attack": "+4", "damage": "1d6+3", "damage_type": "斬擊",
        "str": 14, "dex": 16, "con": 16, "int": 13, "wis": 10, "cha": 8,
        "cr": 2, "emoji": "👁️",
        "actions": ["爪擊 × 2", "腐蝕凝視（遠程法術，目標DC12體質豁免否則受3d6壞死傷害）"],
        "traits": ["詭異洞察：可用附贈行動獲知目標秘密（感知對抗洞察）"],
    },
    "redbrand": {
        "name_zh": "紅幫傭兵", "hp": 16, "max_hp": 16, "ac": 14, "speed": 30,
        "attack": "+3", "damage": "1d8+1", "damage_type": "斬擊",
        "str": 13, "dex": 12, "con": 12, "int": 10, "wis": 10, "cha": 8,
        "cr": 0.5, "emoji": "🔴",
        "actions": ["長劍攻擊", "短弓攻擊（遠程，1d6+1）"],
        "traits": ["組織紀律：相鄰盟友時+1命中"],
    },
    "glasstaff": {
        "name_zh": "格拉斯塔（法師）", "hp": 22, "max_hp": 22, "ac": 12, "speed": 30,
        "attack": "+5", "damage": "1d10", "damage_type": "閃電",
        "str": 9, "dex": 14, "con": 11, "int": 17, "wis": 12, "cha": 11,
        "cr": 2, "emoji": "🧙",
        "actions": [
            "火焰射線（遠程法術，+5命中，2d6火焰）",
            "震盪術（20呎半徑，DC13體質豁免否則眩暈）",
            "魔法飛彈（3枚，每枚1d4+1力場傷害，自動命中）",
        ],
        "traits": ["法術迴避：DC13豁免+1AC", "撤退：HP低於10時嘗試逃跑"],
        "spell_slots": {"1st": 4, "2nd": 3},
    },
    "king_grol": {
        "name_zh": "King Grol（豺狼人首領）", "hp": 55, "max_hp": 55, "ac": 15, "speed": 30,
        "attack": "+5", "damage": "2d8+3", "damage_type": "斬擊",
        "str": 17, "dex": 12, "con": 15, "int": 10, "wis": 11, "cha": 8,
        "cr": 3, "emoji": "👹",
        "actions": ["大斧攻擊 × 2", "投擲斧（遠程，1d8+3）"],
        "traits": ["狂暴：HP低於27時進入狂暴狀態，攻擊+2傷害+3但AC-2", "恐嚇嚀叫：附贈行動，30呎內敵人DC12感知豁免或恐懼"],
    },
    "nezznar": {
        "name_zh": "Nezznar（Black Spider）", "hp": 66, "max_hp": 66, "ac": 14, "speed": 30,
        "attack": "+5", "damage": "1d8+3", "damage_type": "毒素",
        "str": 11, "dex": 14, "con": 13, "int": 18, "wis": 14, "cha": 16,
        "cr": 4, "emoji": "🕷️",
        "actions": [
            "毒蜘攻擊（+5命中，1d8+3毒素，DC13體質豁免否則中毒）",
            "蜘網射擊（遠程，DC12力量豁免否則束縛）",
            "黑暗術（60呎半徑，無光）",
            "魔法飛彈（3枚，1d4+1）",
        ],
        "traits": ["蜘蛛感應：感知附近蜘蛛", "黑暗視覺：120呎", "聪明戰術：優先攻擊施法者"],
        "spell_slots": {"1st": 4, "2nd": 3, "3rd": 2},
    },
}


def get_monster_stats(monster_key: str) -> Optional[dict]:
    return MONSTER_STATS.get(monster_key.lower())


def format_monster_stat_block(key: str) -> str:
    m = MONSTER_STATS.get(key)
    if not m:
        return f"（未知怪物：{key}）"
    actions = "、".join(m.get("actions", []))
    traits = "、".join(m.get("traits", []))
    return (
        f"【{m['name_zh']}】HP:{m['hp']}  AC:{m['ac']}  速度:{m['speed']}呎\n"
        f"  攻擊：{m['attack']} {m['damage']}({m['damage_type']})\n"
        f"  行動：{actions}\n"
        f"  特性：{traits}"
    )