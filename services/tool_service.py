"""
Tool services — utility functions powering the /tools commands.
"""

import datetime
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from config import AI_API_KEY, AI_BASE_URL, AI_MODEL

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_ai() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client


# ---------------------------------------------------------------------------
# TEXT ANALYSIS
# ---------------------------------------------------------------------------

async def summarize(text: str, style: str = "concise") -> str:
    """Summarize the given text."""
    prompt = (
        f"Summarize the following text in a {style} style. "
        f"Preserve key facts and actionable points:\n\n{text}"
    )
    try:
        resp = await _get_ai().chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=1024,
        )
        return resp.choices[0].message.content or "No summary generated."
    except Exception as e:
        logger.error("summarize error: %s", e)
        return f"⚠️ Error: {e}"


async def translate(text: str, target_lang: str = "English") -> str:
    """Translate text to the target language."""
    prompt = f"Translate the following text to {target_lang}. Return only the translation:\n\n{text}"
    try:
        resp = await _get_ai().chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}],
            temperature=0.2, max_tokens=2048,
        )
        return resp.choices[0].message.content or "No translation generated."
    except Exception as e:
        logger.error("translate error: %s", e)
        return f"⚠️ Error: {e}"


async def grammar_check(text: str) -> str:
    """Check and correct grammar in the text."""
    prompt = (
        "Proofread the following text. List any grammar, spelling, or style issues, "
        "then provide a corrected version:\n\n" + text
    )
    try:
        resp = await _get_ai().chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=2048,
        )
        return resp.choices[0].message.content or "No corrections."
    except Exception as e:
        logger.error("grammar error: %s", e)
        return f"⚠️ Error: {e}"


async def analyze_sentiment(text: str) -> str:
    """Analyze the sentiment of the text."""
    prompt = (
        "Analyze the sentiment of the following text. Rate it as positive, negative, "
        "or neutral on a scale of -10 to +10. Explain key emotional signals:\n\n" + text
    )
    try:
        resp = await _get_ai().chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}],
            temperature=0.2, max_tokens=512,
        )
        return resp.choices[0].message.content or "No analysis."
    except Exception as e:
        logger.error("sentiment error: %s", e)
        return f"⚠️ Error: {e}"


# ---------------------------------------------------------------------------
# CODE TOOLS
# ---------------------------------------------------------------------------

async def explain_code(code: str, language: str = "") -> str:
    """Explain what a piece of code does."""
    lang_hint = f" ({language})" if language else ""
    prompt = (
        f"Explain the following code{lang_hint} in plain English. Cover what it does, "
        f"key functions, and any notable patterns:\n\n```\n{code}\n```"
    )
    try:
        resp = await _get_ai().chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=1024,
        )
        return resp.choices[0].message.content or "No explanation."
    except Exception as e:
        logger.error("explain_code error: %s", e)
        return f"⚠️ Error: {e}"


async def debug_code(code: str, language: str = "") -> str:
    """Debug the given code and suggest fixes."""
    lang_hint = f" ({language})" if language else ""
    prompt = (
        f"Review the following code{lang_hint} for bugs, issues, or improvements. "
        f"List each issue with the line number, severity, and suggested fix:\n\n```\n{code}\n```"
    )
    try:
        resp = await _get_ai().chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}],
            temperature=0.2, max_tokens=2048,
        )
        return resp.choices[0].message.content or "No issues found."
    except Exception as e:
        logger.error("debug_code error: %s", e)
        return f"⚠️ Error: {e}"


async def format_code(code: str, language: str = "") -> str:
    """Format/beautify code."""
    lang_hint = f" {language}" if language else ""
    prompt = (
        f"Format the following{lang_hint} code according to best practices. "
        f"Return only the formatted code in a code block:\n\n```\n{code}\n```"
    )
    try:
        resp = await _get_ai().chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}],
            temperature=0.1, max_tokens=2048,
        )
        return resp.choices[0].message.content or "No formatted code."
    except Exception as e:
        logger.error("format_code error: %s", e)
        return f"⚠️ Error: {e}"


# ---------------------------------------------------------------------------
# TEXT UTILITIES
# ---------------------------------------------------------------------------

def word_count(text: str) -> str:
    """Count words, characters, sentences, and paragraphs."""
    words = len(text.split())
    chars = len(text)
    sentences = len(re.findall(r'[.!?]+', text)) or 1
    paragraphs = len([p for p in text.split('\n\n') if p.strip()]) or 1
    reading_time = max(1, round(words / 200))
    return (
        f"📊 **Text Statistics**\n\n"
        f"• Words: `{words:,}`\n"
        f"• Characters: `{chars:,}`\n"
        f"• Sentences: `{sentences:,}`\n"
        f"• Paragraphs: `{paragraphs:,}`\n"
        f"• Reading time: ~{reading_time} min"
    )


def extract_urls(text: str) -> str:
    """Extract URLs from text."""
    urls = re.findall(r'https?://[^\s]+', text)
    if not urls:
        return "🔗 No URLs found in the text."
    lines = "\n".join(f"• {u}" for u in urls)
    return f"🔗 **Found {len(urls)} URL(s):**\n\n{lines}"


# ---------------------------------------------------------------------------
# INFORMATION TOOLS
# ---------------------------------------------------------------------------

def current_time(timezone: str = "UTC") -> str:
    """Get the current time info."""
    now = datetime.datetime.utcnow()
    return (
        f"🕐 **Current Time**\n\n"
        f"• UTC: `{now.strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"• Timestamp: `{int(now.timestamp())}`\n"
        f"• ISO: `{now.isoformat()}Z`\n"
    )


# ---------------------------------------------------------------------------
# TOOL LISTING
# ---------------------------------------------------------------------------

TOOL_CATEGORIES: dict[str, list[dict[str, Any]]] = {
    "📝 Text Analysis": [
        {"name": "summarize", "desc": "Summarize text", "usage": "/summarize <text>"},
        {"name": "translate", "desc": "Translate text", "usage": "/translate <lang> <text>"},
        {"name": "grammar", "desc": "Check grammar & style", "usage": "/grammar <text>"},
        {"name": "sentiment", "desc": "Analyze sentiment", "usage": "/sentiment <text>"},
    ],
    "💻 Code Tools": [
        {"name": "explain", "desc": "Explain code", "usage": "/explain <code>"},
        {"name": "debug", "desc": "Debug & review code", "usage": "/debug <code>"},
        {"name": "format", "desc": "Format code", "usage": "/format <code>"},
    ],
    "📊 Utilities": [
        {"name": "wordcount", "desc": "Word & character count", "usage": "/wordcount <text>"},
        {"name": "extracturls", "desc": "Extract URLs from text", "usage": "/extracturls <text>"},
        {"name": "time", "desc": "Current time info", "usage": "/time"},
    ],
}


def get_all_tools_markdown() -> str:
    """Return a formatted listing of all tools by category."""
    lines = ["🤖 **Edith Tools**\n"]
    for category, tools in TOOL_CATEGORIES.items():
        lines.append(f"\n**{category}**")
        for t in tools:
            lines.append(f"  `/{t['name']}` — {t['desc']}")
    lines.append("\n💬 **AI Chat** — just send any message")
    lines.append("\n_Reply to a message with a tool command to use it on that message._")
    return "\n".join(lines)
