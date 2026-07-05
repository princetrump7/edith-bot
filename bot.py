"""
Edith — AI-powered Telegram Bot.

Entry point. Registers all handlers and starts polling or webhook.
"""

import logging
import os
import sys
import time

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN, APP_URL, WEBHOOK_SECRET, PORT, BOT_NAME, AI_MODEL
from persistence import init_db, get_usage_stats
from handlers.chat import (
    handle_chat,
    handle_image_caption,
    cmd_newchat,
    cmd_chat_settings,
)
from handlers.tools import (
    cmd_tools,
    cmd_summarize,
    cmd_translate,
    cmd_grammar,
    cmd_explain,
    cmd_debug,
    cmd_web,
    cmd_decide,
    cmd_negotiate,
    cmd_whatif,
    cmd_brief,
    cmd_remember,
    cmd_recap,
)
from handlers.settings import cmd_settings, cmd_profile, settings_callback
from handlers.help_handler import cmd_start, cmd_help, cmd_about

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Uptime tracking
# ---------------------------------------------------------------------------

_START_TIME = time.time()

# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------


async def error_handler(update: object, context: object) -> None:
    """Log all errors."""
    if isinstance(context, Exception):
        logger.error("Unhandled exception: %s", context)
    else:
        logger.error("Update %s caused error %s", update, context)


# ---------------------------------------------------------------------------
# System status
# ---------------------------------------------------------------------------


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot system status — uptime, users, facts, model, mode — /status"""
    uptime_seconds = int(time.time() - _START_TIME)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60

    stats = get_usage_stats()

    await update.effective_message.reply_text(
        f"**{BOT_NAME} — System Status**\n\n"
        f"  • Uptime: `{hours}h {minutes}m`\n"
        f"  • Model: `{AI_MODEL}`\n"
        f"  • Users: `{stats['total_users']}`\n"
        f"  • Facts stored: `{stats['total_facts']}`\n"
        f"  • Mode: `{os.getenv('BOT_MODE', 'polling')}`",
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def build_application() -> Application:
    """Create and configure the bot Application, returning it ready to run.

    Initialises the SQLite database before registering any handlers.
    """
    if not BOT_TOKEN:
        logger.fatal(
            "BOT_TOKEN is not set. Create a .env file with BOT_TOKEN=<your token>"
        )
        sys.exit(1)

    # Initialise the database
    init_db()

    builder = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(_post_init)
    )
    app = builder.build()

    # --- Error handler ---
    app.add_error_handler(error_handler)

    # --- Command handlers ---
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("status", cmd_status))

    # Chat management
    app.add_handler(CommandHandler("newchat", cmd_newchat))
    app.add_handler(CommandHandler("chatstat", cmd_chat_settings))

    # Tools listing
    app.add_handler(CommandHandler("tools", cmd_tools))

    # Text tools
    app.add_handler(CommandHandler("summarize", cmd_summarize))
    app.add_handler(CommandHandler("translate", cmd_translate))
    app.add_handler(CommandHandler("grammar", cmd_grammar))

    # Code tools
    app.add_handler(CommandHandler("explain", cmd_explain))
    app.add_handler(CommandHandler("debug", cmd_debug))

    # Strategy tools
    app.add_handler(CommandHandler("decide", cmd_decide))
    app.add_handler(CommandHandler("negotiate", cmd_negotiate))
    app.add_handler(CommandHandler("whatif", cmd_whatif))
    app.add_handler(CommandHandler("brief", cmd_brief))

    # Memory tools
    app.add_handler(CommandHandler("remember", cmd_remember))
    app.add_handler(CommandHandler("recap", cmd_recap))

    # Web search
    app.add_handler(CommandHandler("web", cmd_web))

    # Settings & profile
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("profile", cmd_profile))

    # Inline callbacks (settings menu)
    app.add_handler(
        CallbackQueryHandler(
            settings_callback, pattern=r"^(setting_|setval_|settings_back)$"
        )
    )

    # Message handlers (photos first, then text)
    app.add_handler(
        MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_image_caption)
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat)
    )

    logger.info("Bot application built with all handlers registered.")
    return app


async def _post_init(app: Application) -> None:
    """Called after the application is initialised."""
    bot_user = await app.bot.get_me()
    logger.info("Bot started: @%s (%s)", bot_user.username, bot_user.full_name)


# ---------------------------------------------------------------------------
# Run modes
# ---------------------------------------------------------------------------

def run_polling():
    """Run in long-polling mode (local development)."""
    app = build_application()
    logger.info("Starting polling mode...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


def run_webhook():
    """Run in webhook mode (production — Render, Railway, etc.)."""
    if not APP_URL:
        logger.warning("APP_URL not set, falling back to polling.")
        run_polling()
        return

    app = build_application()
    logger.info("Starting webhook mode on port %s with URL %s...", PORT, APP_URL)
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{APP_URL}/{BOT_TOKEN}",
        secret_token=WEBHOOK_SECRET or None,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    mode = os.getenv("BOT_MODE", "webhook").lower()
    if mode == "webhook":
        run_webhook()
    else:
        run_polling()
