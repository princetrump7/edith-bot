"""
Screens Showcase handler — /showcase command.

Sends the 6 pre-generated premium Telegram Mini App showcase screens
as media groups, giving users a visual tour of the bot's capabilities.
"""

import logging
import os
from typing import List

from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

# Path to generated screen assets
ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "screens",
    "assets",
)

SCREEN_FILES = [
    ("01_bot_profile.png",      "🤖 **Bot Profile** — Command hub with GPT-5 integration, "
                                 "user stats, and quick actions to power your workflow."),
    ("02_start_menu.png",       "🚀 **Welcome Menu** — Interactive /start interface with "
                                 "all core features at your fingertips."),
    ("03_features_commands.png", "⚡ **Features & Commands** — Free & Premium AI models "
                                 "including text, image, slides, video, and music generation."),
    ("04_how_to_create.png",    "📖 **How to Create** — Step-by-step guide to generating "
                                 "content with text, search, image, slides, video & music tools."),
    ("05_capabilities_green.png", "🌿 **AI Capabilities** — Full model suite with smart "
                                   "category grids and quick-access start button."),
    ("06_capabilities_purple.png", "💜 **Capabilities Pro** — Premium overview of all "
                                    "generation engines available in Mira Bot."),
]

COLLAGE_FILE = "_collage_preview.png"


async def cmd_showcase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send all 6 showcase screens as media groups — /showcase"""
    sent = await update.effective_message.reply_text(
        "🎨 **Mira Bot — Showcase**\n\n"
        "Here's a quick visual tour of what I can do!\n"
        "_Sending screens..._",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Load valid screen paths
    screens: List[InputMediaPhoto] = []
    for filename, caption in SCREEN_FILES:
        path = os.path.join(ASSETS_DIR, filename)
        if os.path.isfile(path):
            screens.append(
                InputMediaPhoto(media=open(path, "rb"), caption=caption, parse_mode=ParseMode.MARKDOWN)
            )
        else:
            logger.warning("Showcase screen not found: %s", path)

    if not screens:
        await sent.edit_text(
            "⚠️ Showcase screens are not available right now. "
            "They may not have been generated yet.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Telegram allows max 10 media per group — send in batches of 6
    # (all 6 fit in one group, but split into 2 groups of 3 for readability)
    batch_size = 3
    for i in range(0, len(screens), batch_size):
        batch = screens[i : i + batch_size]
        # Open fresh file handles for each batch (files close after send)
        for media in batch:
            if hasattr(media.media, "seek"):
                media.media.seek(0)
        await update.effective_message.reply_media_group(
            media=batch,
            write_timeout=30,
        )

    # Clean up open handles
    for media in screens:
        if hasattr(media.media, "close"):
            media.media.close()

    await sent.edit_text(
        "✨ **Mira Bot Showcase** — That's the tour!\n\n"
        "Try any feature:\n"
        "• Send me a message to chat\n"
        "• Use `/tools` to see all utilities\n"
        "• `/settings` to customize your experience",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_collage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the collage preview — /collage"""
    collage_path = os.path.join(ASSETS_DIR, COLLAGE_FILE)
    if not os.path.isfile(collage_path):
        await update.effective_message.reply_text(
            "⚠️ Collage preview not found.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await update.effective_message.reply_photo(
        photo=open(collage_path, "rb"),
        caption=(
            "🎯 **Mira Bot — Full Showcase**\n\n"
            "6 premium screens preview. Use `/showcase` for detailed views."
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
