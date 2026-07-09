"""
AI service — wraps the Groq / OpenAI-compatible API for chat completions and vision analysis.
"""

import asyncio
import base64
import logging
import time
from collections import deque
from typing import AsyncIterator

from openai import AsyncOpenAI
from openai import RateLimitError

from config import AI_API_KEY, AI_BASE_URL, AI_MODEL, SYSTEM_PROMPT, MAX_HISTORY_LENGTH

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

VISION_MODEL = "llama-3.2-11b-vision-preview"

# ── Simple token-bucket rate limiter ──────────────────────────────────────
_RATE_LIMIT_RPM = 25  # leave headroom under Groq's 30 RPM
_window: deque[float] = deque(maxlen=_RATE_LIMIT_RPM)


async def _wait_for_slot():
    """Wait until we're under the rate limit, then record a new slot."""
    while True:
        now = time.monotonic()
        # Drop timestamps older than 60 seconds
        while _window and _window[0] < now - 60:
            _window.popleft()

        if len(_window) < _RATE_LIMIT_RPM:
            _window.append(now)
            return

        # Full — sleep until the oldest slot expires
        wait = _window[0] + 60 - now
        logger.info("Rate limit hit, sleeping %.1fs", wait)
        await asyncio.sleep(max(wait, 0.5))


async def _call_with_retry(client_call, max_retries=3):
    """Call the API, retrying on 429 with exponential backoff."""
    for attempt in range(max_retries + 1):
        await _wait_for_slot()
        try:
            return await client_call()
        except RateLimitError as e:
            if attempt >= max_retries:
                raise
            wait = min(2 ** attempt * 5, 30)
            logger.warning("Groq 429 (attempt %d/%d), sleeping %ds", attempt + 1, max_retries, wait)
            await asyncio.sleep(wait)
    raise RuntimeError("Unreachable — _call_with_retry exhausted")


def _get_client() -> AsyncOpenAI:
    """Return a lazily-initialised OpenAI-compatible client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client


def _build_messages(user_message: str, history: list[dict]) -> list[dict]:
    """Construct the messages array from history + new message."""
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-MAX_HISTORY_LENGTH:]:
        msgs.append(h)
    msgs.append({"role": "user", "content": user_message})
    return msgs


async def chat_completion(
    user_message: str,
    history: list[dict] | None = None,
) -> str:
    """Send a message to the AI and return the reply.

    Args:
        user_message: The user's latest message text.
        history: Prior conversation messages (role/content dicts).

    Returns:
        The AI response text, or an error message prefixed with a warning emoji.
    """
    client = _get_client()
    messages = _build_messages(user_message, history or [])

    try:
        resp = await _call_with_retry(
            lambda: client.chat.completions.create(
                model=AI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        logger.error("AI chat error: %s", e)
        return f"⚠️ Sorry, I hit an error: {e}"


async def chat_completion_stream(
    user_message: str,
    history: list[dict] | None = None,
) -> AsyncIterator[str]:
    """Stream a chat completion chunk by chunk.

    Yields:
        Content fragments as they arrive from the API.
    """
    client = _get_client()
    messages = _build_messages(user_message, history or [])

    try:
        stream = await _call_with_retry(
            lambda: client.chat.completions.create(
                model=AI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                stream=True,
            )
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error("AI stream error: %s", e)
        yield f"⚠️ Error: {e}"


async def vision_analysis(image_data: str, caption: str = "") -> str:
    """Analyse an image using Groq's vision model (llama-3.2-11b-vision-preview).

    Args:
        image_data: Base64-encoded JPEG image bytes.
        caption: Optional user caption or question about the image.

    Returns:
        The AI's description or analysis, or an error message.
    """
    client = _get_client()
    prompt_text = caption or "Describe this image in detail."
    try:
        resp = await _call_with_retry(
            lambda: client.chat.completions.create(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0.3,
                max_tokens=1024,
            )
        )
        return resp.choices[0].message.content or "Could not analyse the image."
    except Exception as e:
        logger.error("Vision analysis error: %s", e)
        return f"Vision analysis unavailable: {e}"
