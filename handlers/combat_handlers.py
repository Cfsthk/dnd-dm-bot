from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes
from db import campaigns, events as events_db
from db.characters import get_characters, get_character_by_user
from db import combat as combat_db
from combat import mechanics, initiative, grid
from dm.deepseek_client import chat
from dm import context_builder
import config


async def cmd_startcombat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Begin a combat encounter. Usage: /startcombat [monster_key] [count]"""
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        await update.message.reply_text("目前沒有進行中的戰役。")
        return
    if combat_db.get_active_combat(campaign["id"]):
        await update.message.reply_text("已有進行中的戰鬥！輸入 /combatgrid 查看。")
        return

    args = context.args or []
    monster_key = args[0].lower() if args else "goblin"
    count = int(args[1]) if len(args) > 1 and args[1].isdigit() else 2
    monster_stats = mechanics.get_monster_stats(monster_key)
    if not monster_stats:
        await update.message.reply_text(
            f"未知怪物：`{monster_key}`\n可用怪物：{', '.join(mechanics.MONSTER_STATS.keys())}",
            parse_mode="Markdown",
        )
        return

    chars = get_characters(campaign["id"])
    if not chars:
        await update.message.reply_text("沒有角色！請先建立角色。")
        return

    combat = combat_db.create_combat_session(campaign["id"])
    combatants_for_init = []

    # Add player characters
    player_emojis = config.PLAYER_EMOJIS[:]
    for i, char in enumerate(chars):
        emoji = char.get("emoji", player_emojis[i % len(player_emojis)])
        combat_db.add_entity(
            combat["id"], "player", char["name"],
            x=2, y=i + 1,
            hp=char["hp"], max_hp=char["max_hp"],
            ac=char["armor_class"],
            user_id=str(char["user_id"]),
            char_id=char["id"],
            emoji=emoji,
        )
        combatants_for_init.append({
            "id": char["id"], "name": char["name"],
            "dex": char["stats"].get("dex", 10),
            "entity_type": "player",
            "emoji": emoji,
        })

    # Add monsters
    monster_emoji = config.MONSTER_EMOJIS.get(monster_key, config.MONSTER_EMOJIS["default"])
    for i in range(count):
        m_name = f"{monster_stats['name_zh']}{i+1}"
        combat_db.add_entity(
            combat["id"], "monster", m_name,
            x=7, y=i + 2,
            hp=monster_stats["hp"], max_hp=monster_stats["max_hp"],
            ac=monster_stats["ac"],
            emoji=monster_emoji,
        )
        combatants_for_init.append({
            "id": f"monster_{i}",
            "name": m_name,
            "dex": monster_stats.get("dex", 10),
            "entity_type": "monster",
            "emoji": monster_emoji,
        })

    order = initiative.build_initiative_order(combatants_for_init)
    order_for_db = [
        {"name": c["name"], "entity_type": c["entity_type"],
         "initiative": c["initiative_total"], "emoji": c["emoji"]}
        for c in order
    ]
    combat_db.update_combat(combat["id"], {
        "initiative_order": order_for_db,
        "current_turn": 0,
        "status": "active",
    })

    entities = combat_db.get_entities(combat["id"])
    grid_str = grid.render_combat_status(entities, round_num=1, current_name=order[0]["name"])
    init_str = initiative.format_initiative_list(order)

    await update.message.reply_text(
        f"⚔️ **戰鬥開始！** {count}隻{monster_stats['name_zh']}出現！\n\n"
        f"{init_str}\n\n{grid_str}",
        parse_mode="Markdown",
    )
    events_db.log_event(
        campaign["id"], "系統",
        f"戰鬥開始：{count}隻{monster_stats['name_zh']}",
        event_type="combat",
    )


async def cmd_attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Player declares attack. Usage: /attack <target_name> <d20_roll> [damage_roll]"""
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        return
    combat = combat_db.get_active_combat(campaign["id"])
    if not combat:
        await update.message.reply_text("目前沒有進行中的戰鬥。")
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("用法：`/attack <目標名稱> <d20擲骺結果> [傷害骺結果]`", parse_mode="Markdown")
        return

    target_name = args[0]
    try:
        d20_roll = int(args[1])
    except ValueError:
        await update.message.reply_text("請提供有效的數字骺子結果。")
        return

    entities = combat_db.get_entities(combat["id"])
    target = next((e for e in entities if target_name.lower() in e["name"].lower()), None)
    if not target:
        names = "、".join(e["name"] for e in entities if e["entity_type"] == "monster")
        await update.message.reply_text(f"找不到目標：{target_name}\n可攻擊目標：{names}")
        return

    char = get_character_by_user(campaign["id"], update.effective_user.id)
    attack_bonus = 0
    if char:
        str_mod = (char["stats"].get("str", 10) - 10) // 2
        dex_mod = (char["stats"].get("dex", 10) - 10) // 2
        attack_bonus = max(str_mod, dex_mod) + config.PROFICIENCY_BONUS

    total_attack = d20_roll + attack_bonus
    is_crit = d20_roll == 20
    is_hit = total_attack >= target["ac"] or is_crit
    is_fumble = d20_roll == 1

    attacker_name = char["name"] if char else update.effective_user.first_name

    if is_fumble:
        result_text = (
            f"💨 **大失手！** {attacker_name} 攻擊 {target['name']} 時手滑失誤！\n"
            f"（擲出1，自動失敗）"
        )
    elif not is_hit:
        result_text = (
            f"❌ **未命中！** {attacker_name} 攻擊 {target['name']}\n"
            f"攻擊骺：{d20_roll}+{attack_bonus}={total_attack} vs AC {target['ac']} — 未命中"
        )
    else:
        crit_text = " 💥**暴擊！**" if is_crit else ""
        if len(args) >= 3:
            try:
                raw_dmg = int(args[2])
                damage = raw_dmg + max(
                    (char["stats"].get("str", 10) - 10) // 2 if char else 0,
                    (char["stats"].get("dex", 10) - 10) // 2 if char else 0,
                )
                if is_crit:
                    damage += raw_dmg  # double dice on crit
            except ValueError:
                damage = 1
        else:
            damage = 1

        new_hp = max(0, target["hp"] - damage)
        combat_db.damage_entity(target["id"], new_hp)

        if new_hp <= 0:
            combat_db.remove_entity(target["id"])
            death_text = f"\n💀 **{target['name']} 倒下了！**"
        else:
            death_text = f"\n{target['emoji']} {target['name']} 剩餘 HP：{new_hp}/{target['max_hp']}"

        result_text = (
            f"⚔️{crit_text} **{attacker_name}** 攻擊 **{target['name']}**！\n"
            f"攻擊骺：{d20_roll}+{attack_bonus}={total_attack} vs AC {target['ac']} — **命中！**\n"
            f"傷害：**{damage}**{death_text}"
        )
        events_db.log_event(
            campaign["id"], attacker_name,
            f"攻擊{target['name']}，造成{damage}傷害，剩餘HP:{new_hp}",
            event_type="combat",
        )

    await update.message.reply_text(result_text, parse_mode="Markdown")

    # Check if all monsters defeated
    remaining_entities = combat_db.get_entities(combat["id"])
    monsters_alive = [e for e in remaining_entities if e["entity_type"] == "monster"]
    if not monsters_alive:
        combat_db.end_combat(combat["id"])
        await update.message.reply_text(
            "🎉 **戰鬥勝利！** 所有敵人已被擊敗！\n\nDM將繼續故事...",
            parse_mode="Markdown",
        )
        events_db.log_event(campaign["id"], "系統", "戰鬥結束：玩家勝利", event_type="combat")


async def cmd_nextturn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Advance to the next turn in combat."""
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        return
    combat = combat_db.get_active_combat(campaign["id"])
    if not combat:
        await update.message.reply_text("目前沒有進行中的戰鬥。")
        return

    order = combat["initiative_order"]
    current = combat["current_turn"]
    round_num = combat["round_num"]
    next_turn, round_inc = initiative.advance_turn(current, len(order))
    new_round = round_num + (1 if round_inc else 0)

    combat_db.update_combat(combat["id"], {
        "current_turn": next_turn,
        "round_num": new_round,
    })

    next_combatant = order[next_turn]
    entities = combat_db.get_entities(combat["id"])
    grid_str = grid.render_combat_status(entities, round_num=new_round, current_name=next_combatant["name"])

    round_msg = f"\n🔔 **第{new_round}輪開始！**" if round_inc else ""
    await update.message.reply_text(
        f"{round_msg}\n{grid_str}",
        parse_mode="Markdown",
    )

    # If it's a monster's turn, DM narrates the monster action
    if next_combatant["entity_type"] == "monster":
        players = [e for e in entities if e["entity_type"] == "player"]
        if players:
            import random
            target = random.choice(players)
            monster_stats = None
            for key in mechanics.MONSTER_STATS:
                if mechanics.MONSTER_STATS[key]["name_zh"] in next_combatant["name"]:
                    monster_stats = mechanics.MONSTER_STATS[key]
                    break
            if monster_stats:
                d20, total, is_crit = mechanics.attack_roll(
                    int(monster_stats["attack"].replace("+", ""))
                )
                hit = total >= target["ac"]
                if hit:
                    dmg, _ = mechanics.damage_roll(monster_stats["damage"], is_crit=is_crit)
                    new_hp = max(0, target["hp"] - dmg)
                    combat_db.damage_entity(target["id"], new_hp)
                    hit_text = f"命中！造成 **{dmg}** 傷害，{target['name']} 剩餘 HP：{new_hp}"
                else:
                    hit_text = f"未命中（擲出{total} vs AC {target['ac']}）"
                await update.message.reply_text(
                    f"👾 **{next_combatant['name']}** 攻擊 **{target['name']}**！\n"
                    f"攻擊骺：{d20}+{total-d20}={total} — {hit_text}",
                    parse_mode="Markdown",
                )
                events_db.log_event(
                    campaign["id"], next_combatant["name"],
                    f"攻擊{target['name']}，{'命中' if hit else '未命中'}",
                    event_type="combat",
                )


async def cmd_combatgrid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current combat grid."""
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        return
    combat = combat_db.get_active_combat(campaign["id"])
    if not combat:
        await update.message.reply_text("目前沒有進行中的戰鬥。")
        return
    entities = combat_db.get_entities(combat["id"])
    order = combat["initiative_order"]
    current = combat["current_turn"]
    current_name = order[current]["name"] if order else "？"
    grid_str = grid.render_combat_status(
        entities, round_num=combat["round_num"], current_name=current_name
    )
    await update.message.reply_text(grid_str, parse_mode="Markdown")


async def cmd_move(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Move your character. Usage: /move <x> <y>"""
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        return
    combat = combat_db.get_active_combat(campaign["id"])
    if not combat:
        await update.message.reply_text("目前沒有進行中的戰鬥。")
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("用法：`/move <x坐標> <y坐標>`", parse_mode="Markdown")
        return
    try:
        x, y = int(args[0]), int(args[1])
    except ValueError:
        await update.message.reply_text("請提供有效的數字坐標。")
        return
    entities = combat_db.get_entities(combat["id"])
    user_id = str(update.effective_user.id)
    entity = next((e for e in entities if e.get("user_id") == user_id), None)
    if not entity:
        await update.message.reply_text("找不到你的戰鬥角色。")
        return
    if not (0 <= x < combat["grid_width"] and 0 <= y < combat["grid_height"]):
        await update.message.reply_text(f"坐標超出範圍（0-{combat['grid_width']-1}, 0-{combat['grid_height']-1}）。")
        return
    combat_db.move_entity(entity["id"], x, y)
    await update.message.reply_text(
        f"✅ **{entity['name']}** 移動至 ({x}, {y})",
        parse_mode="Markdown",
    )


async def cmd_endcombat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End combat manually (DM command)."""
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        return
    combat = combat_db.get_active_combat(campaign["id"])
    if not combat:
        await update.message.reply_text("目前沒有進行中的戰鬥。")
        return
    combat_db.end_combat(combat["id"])
    await update.message.reply_text("🏳️ 戰鬥已結束。故事繼續...")
    events_db.log_event(campaign["id"], "系統", "戰鬥結束（DM指令）", event_type="system")