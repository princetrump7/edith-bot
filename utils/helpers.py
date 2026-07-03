"""
Shared helper utilities.
"""

import html
from typing import Any

from telegram import Message
from telegram.constants import ParseMode

from config import MAX_MESSAGE_LENGTH


def safe_markdown(text: str) -> str:
    """Escape characters that break Telegram Markdown parsing."""
    # Escape special Markdown characters except inside code blocks
    if not text:
        return ""
    # Simple approach: escape all then re-allow code blocks
    text = html.escape(text)
    return text


def split_long_message(text: str, max_len: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split a long message into chunks that fit Telegram's limit."""
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to split at a newline
        split_at = text.rfind("\n", 0, max_len)
        if split_at < max_len // 2:
            split_at = text.rfind(" ", 0, max_len)
        if split_at < max_len // 2:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].strip()
    return chunks


def extract_reply_text(message: Message) -> str | None:
    """If the message is a reply, return the replied-to message text."""
    if message.reply_to_message and message.reply_to_message.text:
        return message.reply_to_message.text
    return None


def format_usage(command: str, usage: str, example: str = "") -> str:
    """Format a help response for a specific command."""
    lines = [f"**`/{command}`**"]
    if usage:
        lines.append(f"\n📋 {usage}")
    if example:
        lines.append(f"\n📌 _Example:_ `{example}`")
    return "\n".join(lines)


def truncate_text(text: str, max_chars: int = 200) -> str:
    """Truncate text with ellipsis for display."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."
