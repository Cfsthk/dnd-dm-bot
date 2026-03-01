# DnD AI DM Bot — 失落的芬德爾礦坑

A Cantonese-language AI Dungeon Master Telegram bot for **Lost Mine of Phandelver** (DnD 5e 2024).
Powered by **DeepSeek**, **Supabase**, and **python-telegram-bot v20**.

---

## Features

- Full Cantonese (Traditional Chinese) DM narration via DeepSeek
- Persistent campaign memory with automatic compression
- Character creation wizard (class, race, background, AI-generated stats)
- Combat system with emoji grid, initiative tracker, and auto monster turns
- Complete LMOP module data: all 6 locations, 15 NPCs, 12 monster stat blocks
- World state tracking (key-value flags for campaign decisions)
- Per-session memory summaries (rolling compression past threshold)

---

## Project Structure

```
dnd-dm-bot/
├── main.py
├── config.py
├── schema.sql
├── requirements.txt
├── env.example
├── Dockerfile
├── fly.toml
├── db/
│   ├── supabase_client.py
│   ├── campaigns.py
│   ├── characters.py
│   ├── events.py
│   └── combat.py
├── dm/
│   ├── deepseek_client.py
│   ├── context_builder.py
│   ├── memory_manager.py
│   └── module_lmop.py
├── combat/
│   ├── mechanics.py
│   ├── initiative.py
│   └── grid.py
└── handlers/
    ├── campaign.py
    ├── character.py
    ├── combat_handlers.py
    └── general.py
```

---

## Setup

### 1. Clone and install
```bash
git clone https://github.com/YOUR_USERNAME/dnd-dm-bot
cd dnd-dm-bot
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp env.example .env
```

| Variable | Where to get it |
|---|---|
| `TELEGRAM_BOT_TOKEN` | @BotFather → /newbot |
| `DEEPSEEK_API_KEY` | platform.deepseek.com |
| `SUPABASE_URL` | Supabase → Settings → API |
| `SUPABASE_SERVICE_KEY` | Supabase → Settings → API → service_role |

### 3. Set up Supabase
Run `schema.sql` in your Supabase SQL Editor. Creates 7 tables: campaigns, characters, events, memory_summaries, world_state, combat_sessions, combat_entities.

### 4. Run
```bash
python main.py
```

---

## Deploy to Fly.io
```bash
fly auth login
fly launch --no-deploy
fly secrets set TELEGRAM_BOT_TOKEN=x DEEPSEEK_API_KEY=x SUPABASE_URL=x SUPABASE_SERVICE_KEY=x
fly deploy
```

---

## Commands

| Command | Description |
|---|---|
| `/newgame` | Start a new campaign |
| `/newchar` | Create your character |
| `/startadventure` | Begin the adventure |
| `/status` | View all character sheets |
| `/recap` | AI-generated session summary |
| `/roll 2d6` | Roll dice |
| `/startcombat goblin 3` | Start combat vs 3 goblins |
| `/attack goblin1 18 7` | Attack: d20=18, damage=7 |
| `/combatgrid` | Show emoji battle grid |
| `/nextturn` | Advance turn (monsters auto-act) |
| `/endcombat` | End combat |