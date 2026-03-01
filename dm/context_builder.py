from __future__ import annotations
import json
from db import campaigns, characters, events
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
        f"  HP：{char['hp']}/{char['max_hp']}  AC：{char['armor_class']}  速度：{char['speed']}呆\n"
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

    context_body = (
        f"=== 模組背景（地點：{current_location}，第{act}幕）===\n{module_context}\n\n"
        f"=== 冒險者資料 ===\n{char_blocks}\n\n"
        f"=== 世界狀態 ===\n{world_text}\n\n"
        f"=== 記憶摘要 ===\n{summary_text}\n\n"
        f"=== 最近對話 ===\n{format_events_for_context(recent)}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context_body},
        {"role": "assistant", "content": "明白，我已掌握所有情況，準備好繼續擔任地下城主。"},
        {"role": "user", "content": f"[玩家 {user_name}]：{user_message}"},
    ]


def build_system_prompt() -> str:
    return """你是一位精通龍與地下城第五版（2024年版）規則的地下城主（DM），所有對話必須使用繁體中文廣東話進行。

【你的角色】
- 充滿創意、公正、戲劇性的DM，擅長描述場景、推動故事發展
- 記住玩家的所有決定，讓這些決定對世界產生真實影響
- 在適當時機加入劇情轉折，保持冒險的緊張感和趣味性
- 永遠不會破壞沉浸感，除非需要解釋規則

【語言要求】
- 全程使用繁體中文廣東話
- 場景描述要生動，使用電影感語言
- NPC對話要有獨特個性
- 自然地使用廣東話口語（你哋、係咔、點解等）

【規則執行 - DnD 5e 2024】
- 攻擊：玩家報未修正d20 → 加修正值 → 判斷命中（對比AC）
- 傷害：玩家報未修正傷害骰 → 加修正值 → 扣HP
- 先攻：d20 + 敏捷修正，高至低排序
- 死亡豁免：HP=0時，每回合擲d20，10+成功，3次成功穩定，3次失敗死亡
- 優勢/劣勢：擲兩粒d20取高/低

【戰鬥職責】
- 控制所有怪物行動，描述攻擊效果
- 追蹤所有生物HP、狀態效應、集中法術
- 怪物使用智慧戰術，不要總是衝向最近目標

【故事節奏】
- 每隔30-40分鐘加入轉折或驚喜
- 在關鍵決定點給玩家明確選擇
- 適時提醒玩家可用能力和法術

【輸出格式】
- 場景描述用普通文字
- 重要NPC名稱用【方括號】
- 規則裁決用（圓括號）說明
- 戰鬥結果清晰列出：命中/未命中，傷害值，剩餘HP

你的目標是讓玩家有難忘的冒險體驗！"""