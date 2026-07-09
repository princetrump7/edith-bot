"""AI Chat handler — routes free-form messages and photos to the AI with persistence and vision.

Key behaviours:
- Chat history is stored in SQLite (via persistence module).
- Images are analysed in real time using Groq's vision model.
- User memory context is injected before every AI call.
"""

import base64
import logging

from telegram import Update
from telegram.ext import ContextTypes, filters

from persistence import (
    get_conversation_history,
    save_conversation,
    clear_conversations,
)
from services.ai_service import chat_completion, vision_analysis
from services.memory import get_user_summary
from config import BOT_NAME
from utils.helpers import split_long_message, extract_reply_text

logger = logging.getLogger(__name__)


async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-form text messages (not commands).

    Loads conversation history from the database, injects user memory,
    sends to the AI, then persists the exchange.
    """
    user = update.effective_user
    message = update.effective_message
    if not message or not message.text:
        return

    user_id = user.id if user else 0
    text = message.text.strip()

    # Build the user message — include replied-to text for continuation context
    reply_text = extract_reply_text(message)
    user_content = text
    if reply_text:
        user_content = (
            f"[Continuing from a previous message that said:\n"
            f"\"{reply_text[:500]}\"\n\n"
            f"---\n{text}]"
        )

    # Inject what Edith knows about this user
    memory_context = get_user_summary(user_id)
    if memory_context:
        user_content = f"{memory_context}\n\n---\n\n{user_content}"

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Load chat history from DB and send to AI
    history = get_conversation_history(user_id)
    response = await chat_completion(user_content, history)

    if not response:
        response = "🤔 I'm not sure what to say. Could you rephrase?"

    # Persist the exchange
    save_conversation(user_id, "user", text)
    save_conversation(user_id, "assistant", response)

    # Split and send
    chunks = split_long_message(response)
    for chunk in chunks:
        await message.reply_text(
            chunk,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )


async def handle_image_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Analyse a photo using Groq's vision model and respond intelligently.

    Downloads the largest available photo from the message, converts it to
    base64, and sends it to the vision model along with the user's caption.
    Persists both the user message and the analysis response.
    """
    user = update.effective_user
    message = update.effective_message
    if not message or not message.photo:
        return

    user_id = user.id if user else 0
    caption = message.caption or "Describe this image in detail."

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Download the largest available photo from the message
    try:
        photo = message.photo[-1]
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    except Exception as exc:
        logger.error("Failed to download photo for user %s: %s", user_id, exc)
        await message.reply_text(
            "⚠️ Sorry, I couldn't download that image. Please try again.",
            parse_mode="Markdown",
        )
        return

    # Send to vision model
    response = await vision_analysis(image_b64, caption)

    # Persist the exchange
    save_conversation(user_id, "user", f"[Image] {caption}")
    save_conversation(user_id, "assistant", response)

    await message.reply_text(response, parse_mode="Markdown")


async def cmd_newchat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear conversation history for the current user — /newchat"""
    user = update.effective_user
    if user:
        clear_conversations(user.id)
    await update.effective_message.reply_text(
        "🧹 **Conversation reset!**\n\nI've forgotten our previous chat. "
        "What would you like to talk about?",
        parse_mode="Markdown",
    )


async def cmd_chat_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current chat statistics — /chatstat"""
    user = update.effective_user
    if not user:
        return
    history = get_conversation_history(user.id)
    msg_count = len(history)
    await update.effective_message.reply_text(
        f"💬 **Chat Stats**\n\n"
        f"• Messages in history: `{msg_count}`\n"
        f"• Model: `{BOT_NAME}`\n"
        f"• Context limit: recent messages only",
        parse_mode="Markdown",
    )
