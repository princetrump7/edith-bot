"""
Web search service — uses the AI model's built-in knowledge (no external API needed).
"""

import logging

from openai import AsyncOpenAI

from config import AI_API_KEY, AI_BASE_URL, AI_MODEL

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_ai() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client


async def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Answer a search query using the AI model's training data."""
    try:
        prompt = (
            f"You are a web search engine. Answer the following query using your training data. "
            f"Provide up to {max_results} distinct, relevant pieces of information. "
            f"For each, include a realistic source title and a placeholder URL. "
            f"Format each result as:\n"
            f"TITLE: <title>\nURL: <url>\nSNIPPET: <snippet>\n---\n"
            f"Query: {query}"
        )
        resp = await _get_ai().chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        content = resp.choices[0].message.content or ""

        results = []
        blocks = content.split("---")
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            title = ""
            url = ""
            snippet = ""
            for line in block.split("\n"):
                line = line.strip()
                if line.upper().startswith("TITLE:"):
                    title = line[6:].strip()
                elif line.upper().startswith("URL:"):
                    url = line[4:].strip()
                elif line.upper().startswith("SNIPPET:"):
                    snippet = line[8:].strip()
            if title or snippet:
                results.append({"title": title, "url": url, "snippet": snippet})

        logger.info("AI search for '%s' returned %d results", query, len(results))
        return results
    except Exception as e:
        logger.error("AI search error for '%s': %s", query, e)
        return []


def format_search_results(results: list[dict[str, str]], query: str) -> str:
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
        lines.append(f"**{i}. [{title}]({url})**" if url else f"**{i}. {title}**")
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
