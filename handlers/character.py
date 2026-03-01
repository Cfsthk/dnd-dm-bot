from __future__ import annotations
import json
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from db import campaigns
from db.characters import create_character, get_character_by_user, update_character
from dm.deepseek_client import chat_json
import config

# Conversation states
CHOOSING_NAME, CHOOSING_CLASS, CHOOSING_RACE, CHOOSING_BACKGROUND, CONFIRMING = range(5)

CLASSES = list(config.CLASS_HIT_DICE.keys())
RACES = ["人類", "精靈", "矮人", "半身人", "半獸人", "侏儒", "提夫林", "龍裔"]
BACKGROUNDS = ["民間英雄", "賤民", "犯罪者", "學者", "貴族", "士兵", "水手", "遊促"]


async def cmd_newchar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        await update.message.reply_text("請先輸入 /newgame 開始戰役。")
        return ConversationHandler.END
    user_id = update.effective_user.id
    existing = get_character_by_user(campaign["id"], user_id)
    if existing:
        await update.message.reply_text(
            f"你已有角色：**{existing['name']}**（{existing['race']} {existing['class']}）\n"
            "輸入 /mychar 查看詳情。",
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    context.user_data["campaign_id"] = campaign["id"]
    await update.message.reply_text(
        "⚔️ **建立新角色**\n\n請輸入你的角色名稱："
    )
    return CHOOSING_NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 1 or len(name) > 30:
        await update.message.reply_text("名稱長度需在1-30字之間，請重新輸入：")
        return CHOOSING_NAME
    context.user_data["char_name"] = name
    class_list = "\n".join(f"{i+1}. {c}" for i, c in enumerate(CLASSES))
    await update.message.reply_text(
        f"好的，**{name}**！\n\n請選擇職業（輸入數字或職業名稱）：\n{class_list}",
        parse_mode="Markdown",
    )
    return CHOOSING_CLASS


async def receive_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    chosen = None
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(CLASSES):
            chosen = CLASSES[idx]
    else:
        for c in CLASSES:
            if text in c or c in text:
                chosen = c
                break
    if not chosen:
        await update.message.reply_text("請輸入有效的職業數字或名稱。")
        return CHOOSING_CLASS
    context.user_data["char_class"] = chosen
    race_list = "\n".join(f"{i+1}. {r}" for i, r in enumerate(RACES))
    await update.message.reply_text(
        f"職業：**{chosen}** ✓\n\n請選擇種族：\n{race_list}",
        parse_mode="Markdown",
    )
    return CHOOSING_RACE


async def receive_race(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    chosen = None
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(RACES):
            chosen = RACES[idx]
    else:
        for r in RACES:
            if text in r or r in text:
                chosen = r
                break
    if not chosen:
        await update.message.reply_text("請輸入有效的種族數字或名稱。")
        return CHOOSING_RACE
    context.user_data["char_race"] = chosen
    bg_list = "\n".join(f"{i+1}. {b}" for i, b in enumerate(BACKGROUNDS))
    await update.message.reply_text(
        f"種族：**{chosen}** ✓\n\n請選擇背景：\n{bg_list}",
        parse_mode="Markdown",
    )
    return CHOOSING_BACKGROUND


async def receive_background(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    chosen = None
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(BACKGROUNDS):
            chosen = BACKGROUNDS[idx]
    else:
        for b in BACKGROUNDS:
            if text in b or b in text:
                chosen = b
                break
    if not chosen:
        await update.message.reply_text("請輸入有效的背景數字或名稱。")
        return CHOOSING_BACKGROUND
    context.user_data["char_background"] = chosen
    await update.message.reply_text("⏳ 正在根據你的選擇生成角色屬性…")
    sheet = await _generate_character_sheet(context.user_data)
    context.user_data["generated_sheet"] = sheet
    preview = _format_sheet_preview(sheet)
    await update.message.reply_text(
        f"{preview}\n\n確認建立此角色？輸入 **是** 確認，**否** 重新開始。",
        parse_mode="Markdown",
    )
    return CONFIRMING


async def confirm_char(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text in ("是", "yes", "Yes", "YES", "確認", "ok", "OK"):
        sheet = context.user_data["generated_sheet"]
        campaign_id = context.user_data["campaign_id"]
        user = update.effective_user
        char = create_character(campaign_id, user.id, user.username or user.first_name, sheet)
        await update.message.reply_text(
            f"✅ **{char['name']}** 已建立！\n使用 /mychar 查看完整角色卡。",
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("已取消。請重新輸入 /newchar 建立角色。")
        return ConversationHandler.END


async def cmd_mychar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    campaign = campaigns.get_active_campaign(chat_id)
    if not campaign:
        await update.message.reply_text("目前沒有進行中的戰役。")
        return
    char = get_character_by_user(campaign["id"], update.effective_user.id)
    if not char:
        await update.message.reply_text("你還沒有角色，輸入 /newchar 建立。")
        return
    from dm.context_builder import build_character_block
    block = build_character_block(char)
    inventory = "、".join(char.get("inventory", [])) or "（空）"
    await update.message.reply_text(
        f"{block}\n背包：{inventory}",
        parse_mode="Markdown",
    )


async def _generate_character_sheet(user_data: dict) -> dict:
    import random
    name = user_data["char_name"]
    char_class = user_data["char_class"]
    race = user_data["char_race"]
    background = user_data["char_background"]
    messages = [
        {
            "role": "system",
            "content": (
                "你是DnD 5e角色生成器。根據給定的職業、種族、背景，生成一個完整的1級角色屬性。\n"
                "必須以JSON格式回應，包含以下欄位：\n"
                "- stats: {str, dex, con, int, wis, cha} (用標準陣刷15,14,13,12,10,8分配，種族加成已包含)\n"
                "- hp: integer (職業命運骺最大值 + 體質修正)\n"
                "- armor_class: integer\n"
                "- speed: integer (通常30)\n"
                "- inventory: list of strings (職業/背景起始裝備，6-8件）\n"
                "- skills: {skill_name: bonus} (職業+背景技能，4-6個)\n"
                "- saving_throws: {ability: bonus} (職業主要豁免)\n"
                "- spells: {} (施法職業填入0環法術2-3個，非施法填{})\n"
                "- spell_slots: {} (施法職業填入1st:2，非施法填{})\n"
                "- personality: string (一句話性格描述，廣東話)\n"
                "- emoji: string (一個最能代表此角色的emoji)\n"
            ),
        },
        {
            "role": "user",
            "content": f"生成角色：名字={name}，職業={char_class}，種族={race}，背景={background}",
        },
    ]
    raw = await chat_json(messages)
    sheet = json.loads(raw)
    sheet["name"] = name
    sheet["class"] = char_class
    sheet["race"] = race
    sheet["background"] = background
    hit_die = config.CLASS_HIT_DICE.get(char_class, 8)
    con_mod = (sheet["stats"].get("con", 10) - 10) // 2
    sheet["hp"] = hit_die + con_mod
    sheet["max_hp"] = sheet["hp"]
    return sheet


def _format_sheet_preview(sheet: dict) -> str:
    stats = sheet.get("stats", {})
    def mod(s): return (s - 10) // 2
    def fmt(s): return f"+{mod(s)}" if mod(s) >= 0 else str(mod(s))
    spells_text = ""
    if sheet.get("spells"):
        spells_text = f"\n法術：{', '.join(sheet['spells'].keys() if isinstance(sheet['spells'], dict) else sheet['spells'])}"
    return (
        f"🎲 **{sheet['name']}** {sheet['emoji']}\n"
        f"{sheet['race']} {sheet['class']} | 背景：{sheet['background']}\n"
        f"HP：{sheet['hp']}  AC：{sheet.get('armor_class', 10)}  速度：{sheet.get('speed', 30)}呎\n"
        f"力{stats.get('str',10)}({fmt(stats.get('str',10))}) "
        f"敏{stats.get('dex',10)}({fmt(stats.get('dex',10))}) "
        f"體{stats.get('con',10)}({fmt(stats.get('con',10))}) "
        f"智{stats.get('int',10)}({fmt(stats.get('int',10))}) "
        f"感{stats.get('wis',10)}({fmt(stats.get('wis',10))}) "
        f"魅{stats.get('cha',10)}({fmt(stats.get('cha',10))})\n"
        f"裝備：{', '.join(sheet.get('inventory', []))}"
        f"{spells_text}\n"
        f"性格：{sheet.get('personality', '')}"
    )


def get_char_conv_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("newchar", cmd_newchar)],
        states={
            CHOOSING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            CHOOSING_CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_class)],
            CHOOSING_RACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_race)],
            CHOOSING_BACKGROUND: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_background)],
            CONFIRMING: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_char)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_chat=False,
        per_user=True,
    )