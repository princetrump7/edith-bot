"""
AI service — wraps the Groq / OpenAI-compatible API for chat completions and vision analysis.
"""

import base64
import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from config import AI_API_KEY, AI_BASE_URL, AI_MODEL, SYSTEM_PROMPT, MAX_HISTORY_LENGTH

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

VISION_MODEL = "llama-3.2-11b-vision-preview"


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
    """Stream a chat completion chunk by chunk.

    Yields:
        Content fragments as they arrive from the API.
    """
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
        resp = await client.chat.completions.create(
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
        return resp.choices[0].message.content or "Could not analyse the image."
    except Exception as e:
        logger.error("Vision analysis error: %s", e)
        return f"Vision analysis unavailable: {e}"
