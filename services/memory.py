"""
User memory — stores facts, decisions, and profiles via the SQLite persistence layer.

All functions keep their existing public signatures so callers in handlers and
tools require no changes.  The implementation has been migrated from JSON files
to the ``persistence`` module so data survives restarts.
"""

import logging
from typing import Any

from persistence import (
    get_facts,
    get_decisions,
    save_fact,
    save_decision,
    clear_all_facts,
    get_profile,
    upsert_profile,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------


def add_fact(user_id: int, fact: str) -> None:
    """Store a fact Edith knows about this user.

    Args:
        user_id: Telegram user ID.
        fact: The fact text to remember.
    """
    save_fact(user_id, fact)


def clear_facts(user_id: int) -> None:
    """Delete all stored facts for a user.

    Args:
        user_id: Telegram user ID.
    """
    clear_all_facts(user_id)
    logger.info("Facts cleared for user %s", user_id)


def get_user_profile(user_id: int) -> dict[str, Any]:
    """Return the full user profile (facts and decisions).

    Args:
        user_id: Telegram user ID.

    Returns:
        Dict with ``facts`` and ``decisions`` keys, each a list of records.
    """
    facts = get_facts(user_id)
    decisions = get_decisions(user_id)
    db_profile = get_profile(user_id)
    return {
        "facts": [{"text": f["text"], "timestamp": f.get("created_at", "")} for f in facts],
        "decisions": [
            {
                "question": d["question"],
                "outcome": d.get("summary", ""),
                "timestamp": d.get("created_at", ""),
            }
            for d in decisions
        ],
        "preferences": (db_profile or {}).get("preferences", "{}"),
    }


def get_user_summary(user_id: int) -> str:
    """Format what Edith knows as a context block for the system prompt.

    Args:
        user_id: Telegram user ID.

    Returns:
        A plain-text string suitable for prepending to an AI prompt, or an
        empty string if nothing is known about the user.
    """
    facts = get_facts(user_id)
    decisions = get_decisions(user_id)

    lines: list[str] = []

    if facts:
        lines.append("[EDITH'S MEMORY OF THIS USER]")
        for f in facts[:10]:
            lines.append(f"  • {f['text']}")

    if decisions:
        if not lines:
            lines.append("[EDITH'S MEMORY OF THIS USER]")
        lines.append("  Previous decisions analyzed:")
        for d in decisions[:5]:
            q = d.get("question", "")[:80]
            lines.append(f"  • Decided: {q}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


def add_decision(user_id: int, question: str, outcome: str) -> None:
    """Log a decision analysis that was performed for this user.

    Args:
        user_id: Telegram user ID.
        question: The decision question that was analysed.
        outcome: Summary of the recommendation or outcome.
    """
    save_decision(user_id, question, outcome)
