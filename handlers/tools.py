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
    explain_code,
    debug_code,
)
from services.strategy_tools import decide, negotiate, whatif, brief
from services.search_service import search_web, format_search_results
from services.memory import add_fact, get_user_profile, clear_facts
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

    args = " ".join(context.args) if context.args else ""
    if args.strip():
        return args.strip()

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
        cmd = update.effective_message.text.split()[0] if update.effective_message else ""
        usage = format_usage(cmd.replace("/", ""), usage_hint, usage_hint)
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
        cmd_name = update.effective_message.text.split()[0] if update.effective_message else "unknown"
        logger.error("Tool %s error: %s", cmd_name, e)
        result = f"⚠️ Error: {e}"

    for chunk in split_long_message(result):
        await update.effective_message.reply_text(chunk, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# STRATEGY TOOLS
# ---------------------------------------------------------------------------

async def cmd_decide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Structured decision analysis — /decide <question>"""
    text = await _get_input(update, context)
    if not text:
        await update.effective_message.reply_text(
            "⚠️ **Usage:** `/decide should I take the job or stay?`\n\n"
            "I'll run a full decision analysis — trade-offs, criteria, recommendation.",
            parse_mode="Markdown",
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await update.effective_message.reply_text(
        "🧠 **Analyzing your decision...**\n\n_Let me work through this methodically._",
        parse_mode="Markdown",
    )

    result = await decide(text)
    for chunk in split_long_message(result):
        await update.effective_message.reply_text(chunk, parse_mode="Markdown")

    # Log the decision
    user = update.effective_user
    if user:
        from services.memory import add_decision
        add_decision(user.id, text, "Decision analysis completed")


async def cmd_negotiate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Negotiation analysis — /negotiate <situation>"""
    text = await _get_input(update, context)
    if not text:
        await update.effective_message.reply_text(
            "⚠️ **Usage:** `/negotiate negotiating salary for a senior role`\n\n"
            "I'll map leverage, BATNA, and your best opening move.",
            parse_mode="Markdown",
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await update.effective_message.reply_text(
        "🎯 **Mapping the negotiation...**",
        parse_mode="Markdown",
    )

    result = await negotiate(text)
    for chunk in split_long_message(result):
        await update.effective_message.reply_text(chunk, parse_mode="Markdown")


async def cmd_whatif(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scenario planning — /whatif <scenario>"""
    text = await _get_input(update, context)
    if not text:
        await update.effective_message.reply_text(
            "⚠️ **Usage:** `/whatif what if I quit my job to start a SaaS?`\n\n"
            "I'll model best case, worst case, most likely, and what to test first.",
            parse_mode="Markdown",
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await update.effective_message.reply_text(
        "🔮 **Running the scenario...**",
        parse_mode="Markdown",
    )

    result = await whatif(text)
    for chunk in split_long_message(result):
        await update.effective_message.reply_text(chunk, parse_mode="Markdown")


async def cmd_brief(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Daily strategic brief — /brief"""
    user = update.effective_user
    if not user:
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await update.effective_message.reply_text(
        "📬 **Your daily brief is ready.**",
        parse_mode="Markdown",
    )

    content, meta = await brief(user.id)
    for chunk in split_long_message(content):
        await update.effective_message.reply_text(chunk, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# MEMORY TOOLS
# ---------------------------------------------------------------------------

async def cmd_remember(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Store a fact — /remember <fact>"""
    text = await _get_input(update, context)
    if not text:
        await update.effective_message.reply_text(
            "⚠️ **Usage:** `/remember I'm building a SaaS for freelancers`\n\n"
            "I'll remember this and use it in our conversations.",
            parse_mode="Markdown",
        )
        return

    user = update.effective_user
    if user:
        add_fact(user.id, text)

    await update.effective_message.reply_text(
        "✅ **Got it.** I'll keep that in mind.",
        parse_mode="Markdown",
    )


async def cmd_recap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recall what Edith knows — /recap"""
    user = update.effective_user
    if not user:
        return

    prof = get_user_profile(user.id)
    facts = prof.get("facts", [])
    decisions = prof.get("decisions", [])

    if not facts and not decisions:
        await update.effective_message.reply_text(
            "🤔 **I don't know much about you yet.**\n\n"
            "Tell me things with `/remember <fact>` and I'll build a profile.",
            parse_mode="Markdown",
        )
        return

    lines = ["📋 **What I know about you**\n"]
    if facts:
        lines.append(f"**Facts** ({len(facts)} total):")
        for f in facts[-8:]:
            lines.append(f"  • {f['text']}")
        lines.append("")
    if decisions:
        lines.append(f"**Decisions analyzed** ({len(decisions)} total):")
        for d in decisions[-5:]:
            q = d["question"][:70]
            lines.append(f"  • {q}")

    await update.effective_message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------------
# WEB SEARCH
# ---------------------------------------------------------------------------

async def cmd_web(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search the web — /web <query>"""
    query = await _get_input(update, context)
    if not query:
        await update.effective_message.reply_text(
            "⚠️ **Usage:** `/web latest AI news 2026`",
            parse_mode="Markdown",
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await update.effective_message.reply_text(
        "🔍 Searching...",
        parse_mode="Markdown",
    )

    results = await search_web(query)
    if not results:
        await update.effective_message.reply_text(
            "😕 **No results found.** Try a different search term.",
            parse_mode="Markdown",
        )
        return

    formatted = format_search_results(results, query)
    for chunk in split_long_message(formatted):
        await update.effective_message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=False)


# ---------------------------------------------------------------------------
# TEXT ANALYSIS (kept from original)
# ---------------------------------------------------------------------------

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


async def cmd_explain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_tool(update, context, explain_code, usage_hint="/explain <code> (reply to a code message)")

async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_tool(update, context, debug_code, usage_hint="/debug <code>")
