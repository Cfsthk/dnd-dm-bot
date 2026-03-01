import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
DEEPSEEK_API_KEY: str = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY: str = os.environ["SUPABASE_SERVICE_KEY"]
MAX_RECENT_EVENTS: int = int(os.getenv("MAX_RECENT_EVENTS", "15"))
MEMORY_COMPRESSION_THRESHOLD: int = int(os.getenv("MEMORY_COMPRESSION_THRESHOLD", "20"))
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

ABILITY_NAMES = ["str", "dex", "con", "int", "wis", "cha"]
ABILITY_NAMES_ZH = {
    "str": "力量", "dex": "敏捷", "con": "體質",
    "int": "智力", "wis": "感知", "cha": "魅力",
}
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

CLASS_HIT_DICE = {
    "戰士": 10, "蠻族": 12, "遊俠": 10, "盜賊": 8,
    "術士": 6, "法師": 6, "牧師": 8, "德魯伊": 8,
    "聖武士": 10, "武僧": 8, "魔能劍士": 8, "吟遊詩人": 8,
}
CLASS_PRIMARY_SAVES = {
    "戰士": ["str", "con"], "蠻族": ["str", "con"], "遊俠": ["str", "dex"],
    "盜賊": ["dex", "int"], "術士": ["con", "cha"], "法師": ["int", "wis"],
    "牧師": ["wis", "cha"], "德魯伊": ["int", "wis"], "聖武士": ["wis", "cha"],
    "武僧": ["str", "dex"], "魔能劍士": ["con", "int"], "吟遊詩人": ["dex", "cha"],
}
PROFICIENCY_BONUS = 2

PLAYER_EMOJIS = ["🧙", "🗡️", "🏹", "🛡️", "🔮", "🪄"]
MONSTER_EMOJIS = {
    "goblin": "👺", "hobgoblin": "👹", "bugbear": "🐻", "wolf": "🐺",
    "skeleton": "💀", "zombie": "🧟", "dragon": "🐉", "nothic": "👁️",
    "redbrand": "🔴", "bandit": "🏴", "default": "👾",
}
EMPTY_CELL = "⬛"
WALL_CELL = "🟫"
DOOR_CELL = "🚪"
TRAP_CELL = "⚠️"
CHEST_CELL = "📦"
STAIRS_CELL = "🪜"
ACTIVE_MODULE = "lmop"