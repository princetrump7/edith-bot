"""
Tool commands handler — routes /command to the right tool service.
"""

import logging
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from services.tool_service import (
    TOOL_CATEGORIES,
    get_all_tools_markdown,
    summarize,
    translate,
    grammar_check,
    analyze_sentiment,
    explain_code,
    debug_code,
    format_code,
    word_count,
    extract_urls,
    current_time,
)
from utils.helpers import split_long_message, extract_reply_text, format_usage

logger = logging.getLogger(__name__)


async def cmd_tools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display all available tools — /tools"""
    msg = get_all_tools_markdown()
    await update.effective_message.reply_text(
        msg + "\n\n_Reply to a message with a tool command to use it on that message._",
        parse_mode="Markdown",
    )


async def _get_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """
    Get the text input for a tool command.
    Priority: command args > replied-to message text > None.
    """
    message = update.effective_message
    if not message:
        return None

    # Text after the command
    args = " ".join(context.args) if context.args else ""
    if args.strip():
        return args.strip()

    # Reply text
    reply = extract_reply_text(message)
    if reply:
        return reply.strip()

    return None


async def _run_tool(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    tool_fn: Any,
    arg_name: str = "text",
    extra_args: dict | None = None,
    usage_hint: str = "",
) -> None:
    """Generic runner for a tool command."""
    text = await _get_input(update, context)
    if not text:
        usage = format_usage(context.invoked_from or "", usage_hint, usage_hint)
        await update.effective_message.reply_text(
            f"⚠️ Please provide text or reply to a message.\n\n{usage}",
            parse_mode="Markdown",
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    kwargs = {arg_name: text}
    if extra_args:
        kwargs.update(extra_args)

    try:
        result = await tool_fn(**kwargs)
    except Exception as e:
        logger.error("Tool %s error: %s", context.invoked_from, e)
        result = f"⚠️ Error: {e}"

    for chunk in split_long_message(result):
        await update.effective_message.reply_text(chunk, parse_mode="Markdown")


# --- Individual tool commands ---

async def cmd_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_tool(update, context, summarize, usage_hint="/summarize <text to summarize>")

async def cmd_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = await _get_input(update, context)
    if not text:
        await update.effective_message.reply_text(
            "⚠️ Usage: `/translate <language> <text>` or reply to a message.\n\n"
            "Example: `/translate Spanish Hello, how are you?`",
            parse_mode="Markdown",
        )
        return
    # Parse language from start of text
    parts = text.split(" ", 1)
    target_lang = "English"
    rest = text
    if len(parts) > 1:
        target_lang = parts[0]
        rest = parts[1]
    await _run_tool(update, context, translate, extra_args={"target_lang": target_lang},
                    usage_hint="/translate <language> <text>")

async def cmd_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_tool(update, context, grammar_check, usage_hint="/grammar <text>")

async def cmd_sentiment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_tool(update, context, analyze_sentiment, usage_hint="/sentiment <text>")

async def cmd_explain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_tool(update, context, explain_code, usage_hint="/explain <code> (reply to a code message)")

async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_tool(update, context, debug_code, usage_hint="/debug <code>")

async def cmd_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_tool(update, context, format_code, usage_hint="/format <code>")

async def cmd_wordcount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = await _get_input(update, context)
    if not text:
        await update.effective_message.reply_text(
            "⚠️ Usage: `/wordcount <text>` or reply to a message.",
            parse_mode="Markdown",
        )
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = word_count(text)
    await update.effective_message.reply_text(result, parse_mode="Markdown")

async def cmd_extracturls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = await _get_input(update, context)
    if not text:
        await update.effective_message.reply_text(
            "⚠️ Usage: `/extracturls <text>` or reply to a message.",
            parse_mode="Markdown",
        )
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = extract_urls(text)
    await update.effective_message.reply_text(result, parse_mode="Markdown")

async def cmd_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = current_time()
    await update.effective_message.reply_text(result, parse_mode="Markdown")
