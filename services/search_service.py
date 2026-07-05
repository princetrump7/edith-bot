"""
Web search service — uses DuckDuckGo (free, no API key).
"""

import logging
from typing import Any

from ddgs import DDGS

logger = logging.getLogger(__name__)


async def search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search the web and return results as a list of {title, url, snippet}."""
    try:
        results = []
        # DDGS is synchronous — run in a thread to avoid blocking
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=max_results)):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        logger.info("Web search for '%s' returned %d results", query, len(results))
        return results
    except Exception as e:
        logger.error("Web search error for '%s': %s", query, e)
        return []


def format_search_results(results: list[dict[str, Any]], query: str) -> str:
    """Format search results into a context block for the AI."""
    if not results:
        return ""

    lines = [
        "🔍 **Web Search Results**",
        f"Query: _{query}_",
        "",
    ]
    for i, r in enumerate(results, 1):
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        lines.append(f"**{i}. [{title}]({url})**")
        lines.append(f"   {snippet}")
        lines.append("")

    return "\n".join(lines)


def needs_web_search(text: str) -> bool:
    """Heuristic check if a query likely needs current info."""
    triggers = [
        "latest", "news", "current", "today", "yesterday", "this week",
        "what happened", "update", "recent", "breaking", "headlines",
        "what's new", "what is new", "weather", "stock", "price of",
        "who is", "tell me about", "search for", "find out",
    ]
    text_lower = text.lower()
    return any(t in text_lower for t in triggers)
