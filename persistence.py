"""
SQLite persistence layer — conversations, facts, decisions, and profiles survive restarts.

All operations are transactional (commit on success, rollback on error).
Every function logs errors rather than raising, so the bot degrades gracefully.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("MIRA_DB", "mira.db")


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------


@contextmanager
def _conn() -> Generator[sqlite3.Connection, None, None]:
    """Context manager providing a committed-or-rolled-back database connection."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    """Create all tables and indexes if they do not exist.

    Safe to call repeatedly — uses IF NOT EXISTS everywhere.
    """
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);

            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_facts_user ON facts(user_id);

            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_decisions_user ON decisions(user_id);

            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                preferences TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                command TEXT,
                tokens_estimated INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_log(user_id);
        """)
    logger.info("Database ready at %s", DB_PATH)


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


def save_conversation(user_id: int, role: str, content: str) -> None:
    """Persist one chat message (user or assistant).

    Args:
        user_id: Telegram user ID.
        role: ``"user"`` or ``"assistant"``.
        content: The message text.
    """
    try:
        with _conn() as con:
            con.execute(
                "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content),
            )
    except Exception as exc:
        logger.error("Failed to save conversation for user %s: %s", user_id, exc)


def get_conversation_history(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    """Return recent conversation messages in chronological order.

    Args:
        user_id: Telegram user ID.
        limit: Maximum number of messages to return.

    Returns:
        List of ``{role, content}`` dicts sorted oldest-first.
    """
    try:
        with _conn() as con:
            rows = con.execute(
                "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]
    except Exception as exc:
        logger.error("Failed to load conversation for user %s: %s", user_id, exc)
        return []


def clear_conversations(user_id: int) -> None:
    """Delete all stored chat messages for a user.

    Args:
        user_id: Telegram user ID.
    """
    try:
        with _conn() as con:
            con.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
    except Exception as exc:
        logger.error("Failed to clear conversations for user %s: %s", user_id, exc)


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------


def save_fact(user_id: int, text: str) -> None:
    """Store a fact about a user.

    Args:
        user_id: Telegram user ID.
        text: The fact to remember.
    """
    try:
        with _conn() as con:
            con.execute(
                "INSERT INTO facts (user_id, text) VALUES (?, ?)",
                (user_id, text),
            )
    except Exception as exc:
        logger.error("Failed to save fact for user %s: %s", user_id, exc)


def get_facts(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    """Return the most recent facts for a user.

    Args:
        user_id: Telegram user ID.
        limit: Maximum number of facts to return.

    Returns:
        List of ``{text, created_at}`` dicts sorted newest-first.
    """
    try:
        with _conn() as con:
            rows = con.execute(
                "SELECT text, created_at FROM facts WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Failed to load facts for user %s: %s", user_id, exc)
        return []


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


def save_decision(user_id: int, question: str, summary: str = "") -> None:
    """Log a decision analysis performed for a user.

    Args:
        user_id: Telegram user ID.
        question: The decision that was analysed.
        summary: Short outcome or recommendation.
    """
    try:
        with _conn() as con:
            con.execute(
                "INSERT INTO decisions (user_id, question, summary) VALUES (?, ?, ?)",
                (user_id, question, summary),
            )
    except Exception as exc:
        logger.error("Failed to save decision for user %s: %s", user_id, exc)


def get_decisions(user_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """Return the most recent decisions for a user.

    Args:
        user_id: Telegram user ID.
        limit: Maximum number of decisions to return.

    Returns:
        List of ``{question, summary, created_at}`` dicts sorted newest-first.
    """
    try:
        with _conn() as con:
            rows = con.execute(
                "SELECT question, summary, created_at FROM decisions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Failed to load decisions for user %s: %s", user_id, exc)
        return []


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


def get_profile(user_id: int) -> dict[str, Any] | None:
    """Return the stored profile for a user, or *None*.

    Args:
        user_id: Telegram user ID.
    """
    try:
        with _conn() as con:
            row = con.execute(
                "SELECT * FROM profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
        return dict(row) if row else None
    except Exception as exc:
        logger.error("Failed to load profile for user %s: %s", user_id, exc)
        return None


def upsert_profile(
    user_id: int, name: str = "", preferences: str = "{}"
) -> None:
    """Create or update a user profile.

    Only non-empty / non-default values are written.  Existing values are
    preserved when the new value is empty or the default.

    Args:
        user_id: Telegram user ID.
        name: Display name.
        preferences: JSON-encoded preferences dict.
    """
    try:
        with _conn() as con:
            con.execute(
                """
                INSERT INTO profiles (user_id, name, preferences, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    name = COALESCE(NULLIF(?, ''), profiles.name),
                    preferences = COALESCE(NULLIF(?, '{}'), profiles.preferences),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, name, preferences, name, preferences),
            )
    except Exception as exc:
        logger.error("Failed to upsert profile for user %s: %s", user_id, exc)


# ---------------------------------------------------------------------------
# Usage logging
# ---------------------------------------------------------------------------


def log_usage(user_id: int, command: str, tokens: int = 0) -> None:
    """Record a command invocation for analytics.

    Args:
        user_id: Telegram user ID.
        command: The command name (e.g. ``"decide"``).
        tokens: Estimated token count for the request.
    """
    try:
        with _conn() as con:
            con.execute(
                "INSERT INTO usage_log (user_id, command, tokens_estimated) VALUES (?, ?, ?)",
                (user_id, command, tokens),
            )
    except Exception as exc:
        logger.error("Failed to log usage for user %s: %s", user_id, exc)


# ---------------------------------------------------------------------------
# Aggregated stats (used by /status)
# ---------------------------------------------------------------------------


def get_usage_stats() -> dict[str, int]:
    """Return aggregate statistics about bot usage.

    Returns:
        Dict with ``total_users`` and ``total_facts`` keys.
    """
    try:
        with _conn() as con:
            total_users = (
                con.execute(
                    "SELECT COUNT(DISTINCT user_id) FROM conversations"
                ).fetchone()[0]
                or 0
            )
            total_facts = (
                con.execute("SELECT COUNT(*) FROM facts").fetchone()[0] or 0
            )
        return {"total_users": total_users, "total_facts": total_facts}
    except Exception as exc:
        logger.error("Failed to get usage stats: %s", exc)
        return {"total_users": 0, "total_facts": 0}


# ---------------------------------------------------------------------------
# Bulk operations
# ---------------------------------------------------------------------------


def clear_all_facts(user_id: int) -> None:
    """Delete all stored facts for a user.

    Args:
        user_id: Telegram user ID.
    """
    try:
        with _conn() as con:
            con.execute("DELETE FROM facts WHERE user_id = ?", (user_id,))
    except Exception as exc:
        logger.error("Failed to clear facts for user %s: %s", user_id, exc)
