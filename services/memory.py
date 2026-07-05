"""
Persistent user memory — stores facts, decisions, and preferences per user.
Persists across sessions via a JSON file.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

MEMORY_FILE = "edith_memory.json"
logger = logging.getLogger(__name__)


def _load() -> dict[str, Any]:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load memory file: %s", e)
            return {}
    return {}


def _save(data: dict[str, Any]) -> None:
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        logger.error("Failed to save memory file: %s", e)


def _ensure_user(uid: str) -> dict:
    data = _load()
    if uid not in data:
        data[uid] = {
            "facts": [],
            "decisions": [],
            "briefs_sent": [],
            "created": datetime.utcnow().isoformat(),
        }
        _save(data)
    return data


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------

def add_fact(user_id: int, fact: str) -> None:
    """Store a fact Edith knows about this user."""
    uid = str(user_id)
    data = _ensure_user(uid)
    data = _load()
    data[uid]["facts"].append({
        "text": fact,
        "timestamp": datetime.utcnow().isoformat(),
    })
    # Keep last 50 facts max
    data[uid]["facts"] = data[uid]["facts"][-50:]
    _save(data)


def clear_facts(user_id: int) -> None:
    """Clear all facts for a user."""
    uid = str(user_id)
    data = _load()
    if uid in data:
        data[uid]["facts"] = []
        data[uid]["decisions"] = []
        _save(data)


def get_user_profile(user_id: int) -> dict:
    """Get full user profile."""
    uid = str(user_id)
    data = _load()
    return data.get(uid, {"facts": [], "decisions": []})


def get_user_summary(user_id: int) -> str:
    """Format what Edith knows as a context block for the system prompt."""
    prof = get_user_profile(user_id)
    lines = []

    if prof.get("facts"):
        lines.append("[EDITH'S MEMORY OF THIS USER]")
        for f in prof["facts"][-10:]:
            lines.append(f"  • {f['text']}")

    if prof.get("decisions"):
        if not lines:
            lines.append("[EDITH'S MEMORY OF THIS USER]")
        lines.append("  Previous decisions analyzed:")
        for d in prof["decisions"][-5:]:
            q = d.get("question", "")[:80]
            o = d.get("outcome", "")[:60]
            lines.append(f"  • Decided: {q} → {o}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------

def add_decision(user_id: int, question: str, outcome: str) -> None:
    """Log a decision analysis."""
    uid = str(user_id)
    _ensure_user(uid)
    data = _load()
    data[uid]["decisions"].append({
        "question": question,
        "outcome": outcome,
        "timestamp": datetime.utcnow().isoformat(),
    })
    data[uid]["decisions"] = data[uid]["decisions"][-20:]
    _save(data)
