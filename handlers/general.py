from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes
from db import campaigns, events as events_db
from db.characters import get_character_by_user
from db import combat as combat_db
from dm import context_builder, memory_manager
from dm.deepseek_client import chat
from combat import grid as combat_grid
import config


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "⚔️ **失落的芬德爾礦坑 DM Bot** 🐉\n\n"
        "歡迎嚟到龍與地下城！我係你嘅AI地下城主。\n\n"
        "**開始遊戲**\n"
        "• `/newgame` — 開始新戰役\n"
        "• `/newchar` — 建立角色\n"
        "• `/startadventure` — 所有角色準備好後開始冒險\n\n"
        "**遊戲中**\n"
        "• 直接輸入行動描述（例如：「我要偵察前方」）\n"
        "• `/status` — 查看戰役狀態\n"
        "• `/mychar` — 查看我的角色\n"
        "• `/recap` — 回顧故事\n\n"
        "**戰鬥**\n"
        "• `/startcombat [怪物] [數量]` — 開始戰鬥\n"
        "• `/attack <目標> <d20> [傷害]` — 攻擊\n"
        "• `/move <x> <y>` — 移動\n"
        "• `/nextturn` — 下一輪\n"
        "• `/combatgrid` — 查看戰鬥地圖\n\n"
        "**DM工具**\n"
        "• `/setlocation <地點>` — 更改地點\n"
        "• `/setworld <鍵> <值>` — 設定世界狀態\n"
        "• `/roll <骰子>` — 擲骰（例如 `/roll 2d6`）\n",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main message handler — passes player input to the DM only when @mentioned."""
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign or campaign["status"] == "character_creation":
        return  # Not in active adventure

    user = update.effective_user
    user_message = update.message.text.strip()
    if not user_message:
        return

    # In group chats, only respond when the bot is @mentioned
    if update.effective_chat.type in ("group", "supergroup"):
        bot_username = context.bot.username
        if f"@{bot_username}" not in user_message:
            return
        # Strip the @mention from the message before passing to DM
        user_message = user_message.replace(f"@{bot_username}", "").strip()
        if not user_message:
            return

    # Don't process if in active combat and it's not the player's turn
    combat = combat_db.get_active_combat(campaign["id"])
    if combat and combat["status"] == "active":
        order = combat["initiative_order"]
        current_turn = combat["current_turn"]
        if order:
            current = order[current_turn]
            if current["entity_type"] == "monster":
                await update.message.reply_text(
                    "⏳ 等等！現在係怪物的回合，請等待輪到你。（輸入 /nextturn 推進）"
                )
                return

    # Log player action
    events_db.log_event(
        campaign["id"], user.first_name, user_message, event_type="player_action"
    )

    # Build context and call DM
    await update.message.chat.send_action("typing")
    messages = await context_builder.build_context(campaign, user_message, user.first_name)
    response = await chat(messages, temperature=0.85, max_tokens=1024)

    # Log DM response
    events_db.log_event(campaign["id"], "DM", response, event_type="narrative")

    # Compress memory if needed
    await memory_manager.maybe_compress_memory(campaign["id"])

    # Auto-start combat if DM included a [COMBAT:monster:count] tag
    import re
    combat_tag = re.search(r'\[COMBAT:(\w+):(\d+)\]', response)
    if combat_tag and not (combat and combat["status"] == "active"):
        monster_key = combat_tag.group(1)
        count = int(combat_tag.group(2))
        # Strip the tag from the displayed response
        response = re.sub(r'\n?\[COMBAT:\w+:\d+\]', '', response).strip()
        # Auto-initialize combat
        from combat import mechanics as _mech, initiative as _init
        from db.characters import get_characters as _get_chars
        monster_stats = _mech.get_monster_stats(monster_key)
        chars = _get_chars(campaign["id"])
        if monster_stats and chars:
            new_combat = combat_db.create_combat_session(campaign["id"])
            combatants_for_init = []
            player_emojis = config.PLAYER_EMOJIS[:]
            for i, char in enumerate(chars):
                emoji = char.get("emoji", player_emojis[i % len(player_emojis)])
                combat_db.add_entity(
                    new_combat["id"], "player", char["name"],
                    x=2, y=i + 1,
                    hp=char["hp"], max_hp=char["max_hp"],
                    ac=char["armor_class"],
                    user_id=str(char["user_id"]),
                    username=char.get("username", ""),
                    char_id=char["id"],
                    emoji=emoji,
                )
                combatants_for_init.append({
                    "id": char["id"], "name": char["name"],
                    "dex": char["stats"].get("dex", 10),
                    "entity_type": "player", "emoji": emoji,
                })
            monster_emoji = config.MONSTER_EMOJIS.get(monster_key, config.MONSTER_EMOJIS["default"])
            for i in range(count):
                m_name = f"{monster_stats['name_zh']}{i+1}"
                combat_db.add_entity(
                    new_combat["id"], "monster", m_name,
                    x=7, y=i + 2,
                    hp=monster_stats["hp"], max_hp=monster_stats["max_hp"],
                    ac=monster_stats["ac"],
                    emoji=monster_emoji,
                )
                combatants_for_init.append({
                    "id": f"monster_{i}", "name": m_name,
                    "dex": monster_stats.get("dex", 10),
                    "entity_type": "monster", "emoji": monster_emoji,
                })
            order = _init.build_initiative_order(combatants_for_init)
            order_for_db = [
                {"name": c["name"], "entity_type": c["entity_type"],
                 "initiative": c["initiative_total"], "emoji": c["emoji"]}
                for c in order
            ]
            combat_db.update_combat(new_combat["id"], {
                "initiative_order": order_for_db,
                "current_turn": 0,
                "status": "active",
            })
            events_db.log_event(
                campaign["id"], "系統",
                f"自動戰鬥開始：{count}隻{monster_stats['name_zh']}",
                event_type="combat",
            )
            # Refresh combat object for grid rendering below
            combat = combat_db.get_active_combat(campaign["id"])

    # In active combat, always prepend the emoji grid above the DM narrative
    if combat and combat["status"] == "active":
        try:
            entities = combat_db.get_entities(combat["id"])
            # Try to get items, fall back to empty list if not available
            try:
                items = combat_db.get_items(combat["id"])
            except AttributeError:
                items = []
            order = combat.get("initiative_order", [])
            current_turn = combat.get("current_turn", 0)
            round_num = combat.get("round_num", 1)
            current_name = order[current_turn]["name"] if order and len(order) > current_turn else "？"
            grid_str = combat_grid.render_combat_status(
                entities, round_num=round_num, current_name=current_name, items=items
            )
            full_reply = f"{grid_str}\n\n{response}"
        except Exception as e:
            # Log the error but don't fail the message
            import logging
            logging.getLogger(__name__).warning(f"Failed to render combat grid: {e}")
            full_reply = response  # fall back gracefully if grid fails
    else:
        full_reply = response

    await update.message.reply_text(full_reply, parse_mode="Markdown")


async def cmd_roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Roll dice. Usage: /roll 2d6, /roll d20, /roll 4d6"""
    from combat.mechanics import roll as dice_roll
    args = context.args or []
    expr = args[0].lower() if args else "d20"
    try:
        total, rolls = dice_roll(expr)
        rolls_str = " + ".join(str(r) for r in rolls)
        await update.message.reply_text(
            f"🎲 **{expr}** → [{rolls_str}] = **{total}**",
            parse_mode="Markdown",
        )
    except Exception:
        await update.message.reply_text(f"無效的骰子格式：`{expr}`\n例如：`2d6`、`d20`、`4d6`", parse_mode="Markdown")


async def cmd_setworld(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set a world state key-value. Usage: /setworld <key> <value>"""
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        await update.message.reply_text("目前沒有進行中的戰役。")
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("用法：`/setworld <鍵> <值>`\n例：`/setworld 西爾達已獲救 是`", parse_mode="Markdown")
        return
    key = args[0]
    value = " ".join(args[1:])
    campaigns.set_world_state(campaign["id"], key, value)
    await update.message.reply_text(f"✅ 世界狀態已更新：**{key}** = {value}", parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    import logging
    logger = logging.getLogger(__name__)
    logger.error("Exception while handling update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "⚠️ 發生錯誤，請稍後再試。如問題持續請聯絡DM。"
        )
