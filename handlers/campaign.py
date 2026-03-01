from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes
from db import campaigns, events as events_db
from dm import context_builder, memory_manager
from dm.deepseek_client import chat
import config


async def cmd_newgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    existing = campaigns.get_active_campaign(chat_id)
    if existing:
        await update.message.reply_text(
            "已有進行中的戰役！輸入 /status 查看狀態，或 /endgame 結束目前戰役。"
        )
        return
    campaign = campaigns.create_campaign(chat_id, module="lmop")
    from dm.module_lmop import get_act_intro
    intro = get_act_intro(1)
    opening = (
        "⚔️ **失落的芬德爾礦坑** 開始！\n\n"
        f"{intro}\n\n"
        "請每位玩家輸入 /newchar 建立你的角色。\n"
        "所有人準備好後，輸入 /startadventure 開始冒險！"
    )
    await update.message.reply_text(opening, parse_mode="Markdown")
    events_db.log_event(campaign["id"], "系統", "新戰役開始", event_type="system")


async def cmd_startadventure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        await update.message.reply_text("尚未開始戰役，請先輸入 /newgame。")
        return
    from db.characters import get_characters
    chars = get_characters(campaign["id"])
    if not chars:
        await update.message.reply_text("還沒有任何角色！請先輸入 /newchar 建立角色。")
        return
    campaigns.update_campaign(campaign["id"], {"status": "active"})
    char_names = "、".join(c["name"] for c in chars)
    opening_msg = [
        {
            "role": "system",
            "content": context_builder.build_system_prompt(),
        },
        {
            "role": "user",
            "content": (
                f"冒險者：{char_names}\n"
                "請用廣東話繁體中文，以DM身份，用生動電影感描述開場場景：\n"
                "冒險者們正護送一輛貨物車前往法達林，在路上發現了兩匹死馬橫陳路中。\n"
                "描述要有氣圍感，讓玩家感受到危險將至。最後問玩家「你哋會點做？」\n"
                "不超過200字。"
            ),
        },
    ]
    response = await chat(opening_msg, temperature=0.9, max_tokens=600)
    await update.message.reply_text(response, parse_mode="Markdown")
    events_db.log_event(campaign["id"], "DM", response, event_type="narrative")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        await update.message.reply_text("目前沒有進行中的戰役。輸入 /newgame 開始！")
        return
    from db.characters import get_characters
    chars = get_characters(campaign["id"])
    from dm.context_builder import build_character_block
    blocks = "\n\n".join(build_character_block(c) for c in chars)
    world = campaigns.get_world_state(campaign["id"])
    world_text = "\n".join(f"• {k}：{v}" for k, v in world.items()) or "（尚無重要記錄）"
    location = campaign.get("current_location", "未知")
    act = campaign.get("act", 1)
    status_text = (
        f"📜 **戰役狀態**\n"
        f"地點：{location}  幕：第{act}幕\n\n"
        f"**冒險者**：\n{blocks}\n\n"
        f"**世界狀態**：\n{world_text}"
    )
    await update.message.reply_text(status_text, parse_mode="Markdown")


async def cmd_recap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        await update.message.reply_text("目前沒有進行中的戰役。")
        return
    await update.message.reply_text("📖 生成回顧中...")
    recap = await memory_manager.generate_recap(campaign["id"])
    await update.message.reply_text(f"📖 **之前的故事...**\n\n{recap}", parse_mode="Markdown")


async def cmd_endgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        await update.message.reply_text("目前沒有進行中的戰役。")
        return
    campaigns.end_campaign(campaign["id"])
    await update.message.reply_text(
        "🏁 戰役已結束。感謝各位冒險者！\n輸入 /newgame 開始新的冒險。"
    )


async def cmd_setlocation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """DM-only: set current location. Usage: /setlocation <location_key>"""
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        await update.message.reply_text("目前沒有進行中的戰役。")
        return
    if not context.args:
        from dm.module_lmop import LOCATIONS
        locs = "\n".join(f"• `{k}` — {v['name']}" for k, v in LOCATIONS.items())
        await update.message.reply_text(f"用法：`/setlocation <地點代碼>`\n\n可用地點：\n{locs}", parse_mode="Markdown")
        return
    loc_key = context.args[0].lower()
    from dm.module_lmop import LOCATIONS
    if loc_key not in LOCATIONS:
        await update.message.reply_text(f"未知地點：{loc_key}")
        return
    loc_data = LOCATIONS[loc_key]
    campaigns.update_campaign(campaign["id"], {
        "current_location": loc_key,
        "act": loc_data["act"],
    })
    events_db.log_event(campaign["id"], "系統", f"地點更改為：{loc_data['name']}", event_type="system")
    await update.message.reply_text(f"✅ 地點已設為：**{loc_data['name']}**（第{loc_data['act']}幕）", parse_mode="Markdown")