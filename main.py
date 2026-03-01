from __future__ import annotations
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
import config
from handlers.campaign import (
    cmd_newgame,
    cmd_startadventure,
    cmd_status,
    cmd_recap,
    cmd_endgame,
    cmd_setlocation,
)
from handlers.character import cmd_mychar, get_char_conv_handler
from handlers.combat_handlers import (
    cmd_startcombat,
    cmd_attack,
    cmd_nextturn,
    cmd_combatgrid,
    cmd_move,
    cmd_endcombat,
)
from handlers.general import (
    cmd_start,
    cmd_roll,
    cmd_setworld,
    cmd_help,
    handle_message,
    error_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG if config.DEBUG else logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(get_char_conv_handler())

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("newgame", cmd_newgame))
    app.add_handler(CommandHandler("startadventure", cmd_startadventure))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("recap", cmd_recap))
    app.add_handler(CommandHandler("endgame", cmd_endgame))
    app.add_handler(CommandHandler("setlocation", cmd_setlocation))
    app.add_handler(CommandHandler("mychar", cmd_mychar))
    app.add_handler(CommandHandler("startcombat", cmd_startcombat))
    app.add_handler(CommandHandler("attack", cmd_attack))
    app.add_handler(CommandHandler("nextturn", cmd_nextturn))
    app.add_handler(CommandHandler("combatgrid", cmd_combatgrid))
    app.add_handler(CommandHandler("move", cmd_move))
    app.add_handler(CommandHandler("endcombat", cmd_endcombat))
    app.add_handler(CommandHandler("roll", cmd_roll))
    app.add_handler(CommandHandler("setworld", cmd_setworld))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("DnD DM Bot starting...")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()