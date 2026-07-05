"""
Strategy tools — decision analysis, negotiation prep, scenario planning, daily brief.

Each tool prompts the AI for a structured JSON response, then formats the
output into human-readable markdown.  If JSON extraction fails the raw text
is returned as a fallback so the bot never silently drops content.
"""

import json
import logging
import random
import re
from typing import Any

from openai import AsyncOpenAI

from config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from services.memory import get_user_summary

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_ai() -> AsyncOpenAI:
    """Return a lazily-initialised OpenAI-compatible client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client


def _extract_json(text: str) -> dict[str, Any] | None:
    """Try to extract and parse a JSON object from a text response.

    Looks for a `````json ... `````` code block first, then falls back to
    the first bare ``{...}`` block found in the text.

    Returns:
        Parsed dict on success, *None* if no valid JSON is found.
    """
    # Try ```json ... ``` block first
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Try bare { ... }
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


async def _ask_edith(prompt: str, temperature: float = 0.6) -> str:
    """Send a prompt to Edith and return the response."""
    try:
        resp = await _get_ai().chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Edith, a strategic intelligence. Be direct, sharp, and useful. "
                        "Use clear structure (bold headers, bullet points) when it helps clarity. "
                        "Never be generic. Always push toward actionable insight."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=2048,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        logger.error("Strategy tool error: %s", e)
        return f"⚠️ Error processing request: {e}"


# ---------------------------------------------------------------------------
# Decision Engine
# ---------------------------------------------------------------------------

DECISION_FRAMEWORKS = [
    "Weighted Decision Matrix — score each option against your criteria",
    "Opportunity Cost Analysis — what you gain vs what you give up",
    "Pre-Mortem — assume it failed, why?",
    "Second-Order Effects — what happens next, and after that?",
    "Regret Minimization — which choice minimizes future regret?",
]


async def decide(question: str) -> str:
    """Run a structured decision analysis and return a formatted result.

    Args:
        question: The decision to analyse (e.g. *"Should I take the job?"*).

    Returns:
        Formatted markdown with options, recommendation, reasoning, risks,
        and next steps.  Falls back to raw AI text if JSON parsing fails.
    """
    prompt = (
        f"I need to make a decision about: {question}\n\n"
        f"Run a structured decision analysis.\n\n"
        f"Format your response as a valid JSON object:\n"
        f"{{\n"
        f'    "options": ["...", "..."],\n'
        f'    "recommendation": "...",\n'
        f'    "reasoning": ["...", "..."],\n'
        f'    "risks": ["...", "..."],\n'
        f'    "next_steps": ["...", "..."]\n'
        f"}}\n"
        f"Then add a human-readable summary below the JSON."
    )
    response = await _ask_edith(prompt)
    json_data = _extract_json(response)
    if json_data:
        formatted = (
            f"**Decision Analysis**\n\n"
            f"**Recommendation:** {json_data.get('recommendation', 'Consider options below')}\n\n"
            f"**Options:**\n"
        )
        for opt in json_data.get("options", []):
            formatted += f"  • {opt}\n"
        if json_data.get("reasoning"):
            formatted += "\n**Why:**\n" + "\n".join(
                f"  • {r}" for r in json_data["reasoning"]
            )
        return formatted
    return response  # fallback to raw text


# ---------------------------------------------------------------------------
# Negotiation Prep
# ---------------------------------------------------------------------------


async def negotiate(situation: str) -> str:
    """Analyse a negotiation scenario and return structured insights.

    Args:
        situation: Description of the negotiation context.

    Returns:
        Formatted markdown with leverage analysis, BATNA, opening move,
        concessions, and walk-away point.
    """
    prompt = (
        f"Here is a negotiation situation I am in:\n{situation}\n\n"
        f"Analyse it thoroughly.\n\n"
        f"Format your response as a valid JSON object:\n"
        f"{{\n"
        f'    "leverage": ["...", "..."],\n'
        f'    "their_batna": "...",\n'
        f'    "my_batna": "...",\n'
        f'    "opening_move": "...",\n'
        f'    "concessions": ["...", "..."],\n'
        f'    "walk_away": "..."\n'
        f"}}\n"
        f"Then add a human-readable summary below the JSON."
    )
    response = await _ask_edith(prompt)
    json_data = _extract_json(response)
    if json_data:
        formatted = (
            f"**Negotiation Analysis**\n\n"
            f"**Opening Move:** {json_data.get('opening_move', 'Assess the situation')}\n\n"
            f"**Your Leverage:**\n"
        )
        for item in json_data.get("leverage", []):
            formatted += f"  • {item}\n"
        formatted += (
            f"\n**Their BATNA:** {json_data.get('their_batna', 'Unknown')}\n"
            f"**Your BATNA:** {json_data.get('my_batna', 'Unknown')}\n\n"
            f"**Concessions to offer:**\n"
        )
        for c in json_data.get("concessions", []):
            formatted += f"  • {c}\n"
        formatted += f"\n**Walk-away point:** {json_data.get('walk_away', 'Define your limit')}"
        return formatted
    return response  # fallback to raw text


# ---------------------------------------------------------------------------
# Scenario Planner
# ---------------------------------------------------------------------------


async def whatif(scenario: str) -> str:
    """Model best / worst / most-likely outcomes for a scenario.

    Args:
        scenario: Description of the hypothetical situation.

    Returns:
        Formatted markdown with best case, most likely, worst case,
        unknowns, and a small test action.
    """
    prompt = (
        f"Let me describe a scenario I am considering:\n{scenario}\n\n"
        f"Model the outcomes.\n\n"
        f"Format your response as a valid JSON object:\n"
        f"{{\n"
        f'    "best_case": "...",\n'
        f'    "most_likely": "...",\n'
        f'    "worst_case": "...",\n'
        f'    "unknowns": ["...", "..."],\n'
        f'    "one_test": "..."\n'
        f"}}\n"
        f"Then add a human-readable summary below the JSON."
    )
    response = await _ask_edith(prompt)
    json_data = _extract_json(response)
    if json_data:
        formatted = (
            f"**Scenario Analysis**\n\n"
            f"**Best Case:**\n{json_data.get('best_case', 'Hope for the best')}\n\n"
            f"**Most Likely:**\n{json_data.get('most_likely', 'Somewhere in between')}\n\n"
            f"**Worst Case:**\n{json_data.get('worst_case', 'Plan for it')}\n\n"
            f"**Unknowns:**\n"
        )
        for u in json_data.get("unknowns", []):
            formatted += f"  • {u}\n"
        formatted += (
            f"\n**One thing to test:**\n"
            f"{json_data.get('one_test', 'Take a small step to learn more')}"
        )
        return formatted
    return response  # fallback to raw text


# ---------------------------------------------------------------------------
# Daily Brief
# ---------------------------------------------------------------------------

FRAMEWORKS = [
    "**Inversion:** Instead of asking how to succeed, ask what would guarantee failure — then avoid those things.",
    "**Pareto Principle (80/20):** Identify the 20% of effort that drives 80% of results. Double down there.",
    "**Occam's Razor:** The simplest explanation is usually right. Don't add complexity unless the evidence demands it.",
    "**Hedgehog Concept:** What are you deeply passionate about, what can you be best in the world at, and what drives your economic engine? The overlap is your focus.",
    "**Circle of Control:** Focus only on what you can directly control. Influence what you can. Ignore the rest.",
    "**Parkinson's Law:** Work expands to fill the time available. Set tighter deadlines intentionally.",
    "**Sunk Cost Fallacy:** What you've already invested doesn't matter. Only future outcomes should guide decisions.",
    "**Hick's Law:** More choices = harder decisions. Cut options ruthlessly.",
]

INSIGHTS = [
    "The quality of your decisions determines the quality of your life.",
    "Speed of execution is a competitive advantage most people don't use.",
    "If you wouldn't recommend it to a friend, don't do it yourself.",
    "The best time to plant a tree was 20 years ago. The second best time is now.",
    "You don't need a better strategy. You need better execution of a decent strategy.",
    "Clarity > Certainty. You'll never be certain. Get clear on what matters and move.",
]


async def brief(user_id: int) -> tuple[str, dict[str, Any]]:
    """Generate a personalised daily strategic brief.

    Args:
        user_id: Telegram user ID (used to fetch stored facts and decisions).

    Returns:
        Tuple of (formatted brief text, metadata dict with the chosen framework).
    """
    summary = get_user_summary(user_id)

    framework = random.choice(FRAMEWORKS)
    insight = random.choice(INSIGHTS)

    user_context = (
        f"Based on what I know about this user:\n{summary}\n\n"
        f"Incorporate their context naturally where relevant."
        if summary
        else "I don't know much about this user yet — start building rapport."
    )

    prompt = (
        f"Generate a short, sharp daily strategic brief for this user.\n"
        f"{user_context}\n\n"
        f"Format your response as a valid JSON object:\n"
        f"{{\n"
        f'    "insight": "...",\n'
        f'    "framework_of_the_day": "{framework}",\n'
        f'    "challenge_question": "..."\n'
        f"}}\n"
        f"Then add a personal note below the JSON.\n\n"
        f"Keep it under 300 words. Be warm but direct. Make it feel personal."
    )

    response = await _ask_edith(prompt, temperature=0.8)
    json_data = _extract_json(response)

    if json_data:
        formatted = (
            f"**📬 Your Daily Strategic Brief**\n\n"
            f"**Insight:**\n> {json_data.get('insight', insight)}\n\n"
            f"**Framework to apply today:**\n{json_data.get('framework_of_the_day', framework)}\n\n"
            f"**Challenge question:**\n> {json_data.get('challenge_question', 'What matters most today?')}"
        )
        return formatted, {"framework": framework}

    # Fallback: wrap raw response in brief header
    fallback = f"**📬 Your Daily Strategic Brief**\n\n{response}"
    return fallback, {"framework": framework}
