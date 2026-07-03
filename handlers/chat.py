"""
AI Chat handler — handles free-form text messages by routing them to the AI.
Supports streaming reply, image descriptions (without generating), and context.
"""

import logging

from telegram import Update, Message
from telegram.ext import ContextTypes, filters

from services.ai_service import chat_completion
from config import BOT_NAME
from utils.helpers import split_long_message, extract_reply_text

logger = logging.getLogger(__name__)

# In-memory conversation history: user_id -> list of messages
_conversations: dict[int, list[dict]] = {}


def _get_history(user_id: int) -> list[dict]:
    return _conversations.setdefault(user_id, [])


def _append(user_id: int, role: str, content: str):
    history = _get_history(user_id)
    history.append({"role": role, "content": content})
    # Trim to avoid unbounded growth
    if len(history) > 100:
        _conversations[user_id] = history[-50:]


def _clear_history(user_id: int):
    _conversations.pop(user_id, None)


async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-form text (not a command)."""
    user = update.effective_user
    message = update.effective_message
    if not message or not message.text:
        return

    user_id = user.id if user else 0
    text = message.text.strip()

    # Check if this is a reply to a previous bot message (continuation context)
    reply_text = extract_reply_text(message)

    # Build the user message — include replied-to text if any
    user_content = text
    if reply_text:
        user_content = (
            f"[Continuing from a previous message that said:\n"
            f"\"{reply_text[:500]}\"\n\n"
            f"---\n{text}]"
        )

    # Send typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Get AI response
    history = _get_history(user_id)
    response = await chat_completion(user_content, history)

    if not response:
        response = "🤔 I'm not sure what to say. Could you rephrase?"

    # Store in history
    _append(user_id, "user", text)
    _append(user_id, "assistant", response)

    # Split and send
    chunks = split_long_message(response)
    for i, chunk in enumerate(chunks):
        await message.reply_text(
            chunk,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )


async def handle_image_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photos sent by the user — describe/analyze without generating images."""
    user = update.effective_user
    message = update.effective_message
    if not message or not message.photo:
        return

    user_id = user.id if user else 0
    caption = message.caption or "Describe this image in detail."

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Use AI to analyze based on caption
    user_content = (
        f"The user sent an image with the caption/request: \"{caption}\"\n\n"
        f"Analyze and respond based on what you can determine from context. "
        f"Do NOT claim you can see the image. Instead, help based on the caption."
    )

    history = _get_history(user_id)
    response = await chat_completion(user_content, history)

    _append(user_id, "user", f"[Image] {caption}")
    _append(user_id, "assistant", response)

    await message.reply_text(response, parse_mode="Markdown")


async def cmd_newchat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear conversation history — /newchat"""
    user = update.effective_user
    if user:
        _clear_history(user.id)
    await update.effective_message.reply_text(
        "🧹 **Conversation reset!**\n\nI've forgotten our previous chat. "
        "What would you like to talk about?",
        parse_mode="Markdown",
    )


async def cmd_chat_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current chat stats — /chatstat"""
    user = update.effective_user
    if not user:
        return
    history = _get_history(user.id)
    msg_count = len(history)
    await update.effective_message.reply_text(
        f"💬 **Chat Stats**\n\n"
        f"• Messages in history: `{msg_count}`\n"
        f"• Model: `{BOT_NAME}`\n"
        f"• Context limit: recent messages only",
        parse_mode="Markdown",
    )
