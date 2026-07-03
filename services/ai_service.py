"""
AI service — wraps the OPENCODE / DeepSeek API for chat completions.
"""

import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from config import AI_API_KEY, AI_BASE_URL, AI_MODEL, SYSTEM_PROMPT, MAX_HISTORY_LENGTH

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client


def _build_messages(user_message: str, history: list[dict]) -> list[dict]:
    """Construct the messages array from history + new message."""
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Trim history to last N rounds
    for h in history[-MAX_HISTORY_LENGTH:]:
        msgs.append(h)
    msgs.append({"role": "user", "content": user_message})
    return msgs


async def chat_completion(
    user_message: str,
    history: list[dict] | None = None,
) -> str:
    """Send a message to the AI and return the reply."""
    client = _get_client()
    messages = _build_messages(user_message, history or [])

    try:
        resp = await client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        logger.error("AI chat error: %s", e)
        return f"⚠️ Sorry, I hit an error: {e}"


async def chat_completion_stream(
    user_message: str,
    history: list[dict] | None = None,
) -> AsyncIterator[str]:
    """Stream a chat completion chunk by chunk."""
    client = _get_client()
    messages = _build_messages(user_message, history or [])

    try:
        stream = await client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error("AI stream error: %s", e)
        yield f"⚠️ Error: {e}"
