from __future__ import annotations
import json
from db import campaigns, characters, events
from db import combat as combat_db
from dm import module_lmop
import config


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def fmt_mod(mod: int) -> str:
    return f"+{mod}" if mod >= 0 else str(mod)


def build_character_block(char: dict) -> str:
    stats = char.get("stats", {})
    mods = {k: ability_modifier(v) for k, v in stats.items()}
    cond = "、".join(char.get("conditions", [])) or "無"
    spells = char.get("spells", {})
    spell_slots = char.get("spell_slots", {})
    spell_text = ""
    if spells:
        spell_text = (
            f"\n  法術：{json.dumps(spells, ensure_ascii=False)}"
            f"\n  法術位：{json.dumps(spell_slots, ensure_ascii=False)}"
        )
    return (
        f"【{char['name']}】({char['race']} {char['class']} Lv{char['level']}) "
        f"玩家：@{char['username']} {char['emoji']}\n"
        f"  HP：{char['hp']}/{char['max_hp']}  AC：{char['armor_class']}  速度：{char['speed']}呎\n"
        f"  力量{stats.get('str',10)}({fmt_mod(mods.get('str',0))}) "
        f"敏捷{stats.get('dex',10)}({fmt_mod(mods.get('dex',0))}) "
        f"體質{stats.get('con',10)}({fmt_mod(mods.get('con',0))}) "
        f"智力{stats.get('int',10)}({fmt_mod(mods.get('int',0))}) "
        f"感知{stats.get('wis',10)}({fmt_mod(mods.get('wis',0))}) "
        f"魅力{stats.get('cha',10)}({fmt_mod(mods.get('cha',0))})\n"
        f"  狀態：{cond}  背包：{', '.join(char.get('inventory', [])) or '空'}"
        f"{spell_text}"
    )


def format_events_for_context(event_list: list[dict]) -> str:
    lines = []
    for e in event_list:
        etype = e["event_type"]
        speaker = e["speaker"]
        content = e["content"]
        if etype == "player_action":
            lines.append(f"[玩家 {speaker}]：{content}")
        elif etype == "combat":
            lines.append(f"[戰鬥]：{content}")
        elif etype == "system":
            lines.append(f"[系統]：{content}")
        else:
            lines.append(f"[DM]：{content}")
    return "\n".join(lines)


def build_combat_context(campaign_id: str) -> str:
    """Return a text block describing the live combat state (entities + items + positions).
    Returns empty string if no active combat."""
    combat = combat_db.get_active_combat(campaign_id)
    if not combat:
        return ""

    entities = combat_db.get_entities(combat["id"])
    items = combat_db.get_items(combat["id"]) if hasattr(combat_db, "get_items") else []
    order = combat.get("initiative_order", [])
    current_turn = combat.get("current_turn", 0)
    round_num = combat.get("round_num", 1)
    current_name = order[current_turn]["name"] if order else "？"

    # Entity positions table
    entity_lines = []
    for e in entities:
        username_str = f" (@{e['username']})" if e.get("username") else ""
        conds = "、".join(e.get("conditions", [])) or "無"
        entity_lines.append(
            f"  {e['emoji']} {e['name']}{username_str} — 位置:({e['x']},{e['y']})  "
            f"HP:{e['hp']}/{e['max_hp']}  AC:{e['ac']}  狀態:{conds}"
        )

    # Item positions table
    item_lines = []
    for i in items:
        if not i.get("active", True):
            continue
        if i.get("owner_id"):
            continue  # in someone's inventory, not on map
        itype = {"env": "環境", "loot": "戰利品", "hazard": "危險"}.get(i.get("item_type", "env"), "物件")
        desc = f" ({i['description']})" if i.get("description") else ""
        item_lines.append(
            f"  {i.get('emoji','📦')} {i['name']} [{itype}] 位置:({i['x']},{i['y']}){desc}"
        )

    entity_block = "\n".join(entity_lines) or "  （無戰鬥實體）"
    item_block = ("\n場景物件：\n" + "\n".join(item_lines)) if item_lines else ""

    return (
        f"=== 戰鬥狀態（第{round_num}輪，現在輪到：{current_name}）===\n"
        f"戰鬥實體位置：\n{entity_block}"
        f"{item_block}\n"
    )


async def build_context(campaign: dict, user_message: str, user_name: str) -> list[dict]:
    campaign_id = campaign["id"]
    current_location = campaign.get("current_location", "phandalin_outskirts")
    act = campaign.get("act", 1)

    system_prompt = build_system_prompt()
    module_context = module_lmop.get_location_context(current_location, act)

    chars = characters.get_characters(campaign_id)
    char_blocks = "\n\n".join(build_character_block(c) for c in chars)

    world = campaigns.get_world_state(campaign_id)
    world_text = "\n".join(f"- {k}：{v}" for k, v in world.items()) or "（尚未記錄重要事件）"

    summary = events.get_latest_summary(campaign_id)
    summary_text = summary["summary_text"] if summary else "（這是冒險的開始）"

    recent = events.get_recent_events(campaign_id, config.MAX_RECENT_EVENTS)

    # Live combat context (empty string outside combat)
    combat_context = build_combat_context(campaign_id)

    context_body = (
        f"=== 模組背景（地點：{current_location}，第{act}幕）===\n{module_context}\n\n"
        f"=== 冒險者資料 ===\n{char_blocks}\n\n"
        f"=== 世界狀態 ===\n{world_text}\n\n"
        f"=== 記憶摘要 ===\n{summary_text}\n\n"
        + (f"{combat_context}\n" if combat_context else "")
        + f"=== 最近對話 ===\n{format_events_for_context(recent)}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context_body},
        {"role": "assistant", "content": "明白，我已掌握所有情況，準備好繼續擔任地下城主。"},
        {"role": "user", "content": f"[玩家 {user_name}]：{user_message}"},
    ]


def build_system_prompt() -> str:
    return """你是一位精通龍與地下城第五版（2024年版）規則的地下城主（DM），所有對話必須使用繁體中文廣東話進行。

【絕對語言規定 — 最高優先級】
- 你只能用繁體中文廣東話回應，任何情況下都不可使用英文、普通話或其他語言
- 即使玩家用英文或普通話發言，你依然必須用廣東話回應
- 所有場景描述、NPC對話、規則裁決、戰鬥播報，全部廣東話
- 違反此規定即視為嚴重錯誤，絕對不可發生

【你的角色】
- 充滿創意、公正、戲劇性的DM，擅長描述場景、推動故事發展
- 記住玩家的所有決定，讓這些決定對世界產生真實影響
- 在適當時機加入劇情轉折，保持冒險的緊張感和趣味性
- 永遠不會破壞沉浸感，除非需要解釋規則

【語言要求】
- 全程使用繁體中文廣東話，絕無例外
- 場景描述要生動，使用電影感語言
- NPC對話要有獨特個性
- 大量使用廣東話口語：你哋、係咪、點解、唔係、梗係、即係、而家、跟住、搞掂、冇問題等

【規則執行 - DnD 5e 2024】
- 攻擊：玩家報未修正d20 → 加修正值 → 判斷命中（對比AC）
- 傷害：玩家報未修正傷害骰 → 加修正值 → 扣HP
- 先攻：d20 + 敏捷修正，高至低排序
- 死亡豁免：HP=0時，每回合擲d20，10+成功，3次成功穩定，3次失敗死亡
- 優勢/劣勢：擲兩粒d20取高/低

【擲骰請求規定 — 非常重要】
當劇情需要玩家擲骰時，你必須：
1. 用 @用戶名 直接點名該玩家（格式：@username）
2. 清楚說明要擲哪種骰子和修正值
3. 說明DC（如適用）
格式範例：
  @alice 請擲感知檢定 (d20+感知修正)  DC 15
  @bob 請擲力量豁免 (d20+力量修正)  DC 13
  @charlie 請擲欺騙檢定 (d20+魅力修正)
規則：
- 只有真正需要擲骰的情況才請求（不要過度要求）
- 必須根據「戰鬥狀態」區塊的實體資料，識別係邊個玩家做緊乜嘢行動
- 若情況明顯不需要擲骰（例如普通對話），直接繼續故事

【戰鬥格格識別】
- 你可以在「戰鬥狀態」區塊看到所有人的位置座標
- 根據玩家位置判斷：誰在近戰範圍、誰能被捲入AoE、誰可以援護
- 描述戰鬥時主動提及玩家的相對位置（例如：「你同地精只係差一格之隔」）
- 場景物件（環境物件、危險區域、戰利品）亦列於戰鬥狀態，請將之融入場景描述

【場景物件互動】
- 玩家接近loot（戰利品）時，提醒佢哋可以拾取
- 玩家踏入hazard（危險）時，立即要求豁免骰
- 玩家利用env（環境物件）時，根據描述決定效果（掩體+2AC、桶子可推倒等）

【戰鬥職責】
- 控制所有怪物行動，描述攻擊效果
- 追蹤所有生物HP、狀態效應、集中法術
- 怪物使用智慧戰術，不要總是衝向最近目標
- 怪物會優先攻擊HP低或孤立的玩家

【故事節奏】
- 每隔30-40分鐘加入轉折或驚喜
- 在關鍵決定點給玩家明確選擇
- 適時提醒玩家可用能力和法術

【輸出格式】
- 場景描述用普通文字
- 重要NPC名稱用【方括號】
- 規則裁決用（圓括號）說明
- 戰鬥結果清晰列出：命中/未命中，傷害值，剩餘HP

【自動戰鬥觸發 — 非常重要】
當故事中出現新的戰鬥遭遇（怪物突然出現、伏擊、談判破裂變衝突等），你必須在回應的最後一行加入以下標籤：
格式：[COMBAT:怪物key:數量]
怪物key對照表：
  goblin = 哥布林
  skeleton = 骷髏
  zombie = 殭屍
  orc = 獸人
  wolf = 狼
  bandit = 盜賊
例子：
  [COMBAT:goblin:3]   → 出現3隻哥布林
  [COMBAT:skeleton:2] → 出現2隻骷髏
規則：
- 只在全新戰鬥開始時加（已有戰鬥進行中則不加）
- 標籤放在回應最後一行，獨立一行
- 只選一種最主要的怪物類型
- 若遭遇混合怪物，選數量最多的那種

你的目標是讓玩家有難忘的冒險體驗！"""
