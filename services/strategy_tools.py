"""
Strategy tools — decision analysis, negotiation prep, scenario planning, daily brief.
Uses the AI model for each analysis so Edith stays in character.
"""

import logging
import random

from openai import AsyncOpenAI

from config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from services.memory import get_user_summary, add_decision, get_user_profile

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_ai() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client


async def _ask_edith(prompt: str, temperature: float = 0.6) -> str:
    """Send a prompt to Edith and return the response."""
    try:
        resp = await _get_ai().chat.completions.create(
            model=AI_MODEL,
            messages=[{
                "role": "system",
                "content": (
                    "You are Edith, a strategic intelligence. Be direct, sharp, and useful. "
                    "Use clear structure (bold headers, bullet points) when it helps clarity. "
                    "Never be generic. Always push toward actionable insight."
                )
            }, {
                "role": "user",
                "content": prompt,
            }],
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


async def decide(question: str, options: str = "") -> str:
    """Run a structured decision analysis."""
    prompt = (
        f"I need to make a decision about: {question}\n"
        f"{'Options/context I'm considering: ' + options if options else ''}\n\n"
        f"Run a structured decision analysis:\n"
        f"1. First, restate the real question — what am I actually deciding?\n"
        f"2. List the options with their trade-offs\n"
        f"3. Pick the best framework and apply it\n"
        f"4. Give me a clear recommendation with reasoning\n"
        f"5. End with one question I should ask myself before deciding"
    )
    return await _ask_edith(prompt)


# ---------------------------------------------------------------------------
# Negotiation Prep
# ---------------------------------------------------------------------------

async def negotiate(situation: str) -> str:
    """Analyze a negotiation scenario."""
    prompt = (
        f"Here's a negotiation situation I'm in:\n{situation}\n\n"
        f"Walk me through:\n"
        f"1. What leverage does each side have?\n"
        f"2. What's the other side's likely BATNA (best alternative)?\n"
        f"3. What's my opening move?\n"
        f"4. What concessions can I offer that cost me little but mean a lot to them?\n"
        f"5. What's my walk-away point?\n"
        f"Be specific — no generic advice."
    )
    return await _ask_edith(prompt)


# ---------------------------------------------------------------------------
# Scenario Planner
# ---------------------------------------------------------------------------

async def whatif(scenario: str) -> str:
    """Model outcomes of a scenario."""
    prompt = (
        f"Let me describe a scenario I'm considering:\n{scenario}\n\n"
        f"Walk me through:\n"
        f"1. **Best case** — what happens if everything goes right?\n"
        f"2. **Most likely** — what's the realistic outcome?\n"
        f"3. **Worst case** — what's the downside, and can I survive it?\n"
        f"4. **Unknowns** — what don't I know that would change the picture?\n"
        f"5. **One thing to test** — what small action would tell me the most before committing?"
    )
    return await _ask_edith(prompt)


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


async def brief(user_id: int) -> tuple[str, dict]:
    """Generate a personalized daily strategic brief."""
    summary = get_user_summary(user_id)
    profile = get_user_profile(user_id)
    fact_count = len(profile.get("facts", []))

    framework = random.choice(FRAMEWORKS)
    insight = random.choice(INSIGHTS)

    # Build memory-aware opener
    if summary:
        user_context = (
            f"Based on what I know about this user:\n{summary}\n\n"
            f"Incorporate their context naturally where relevant."
        )
    else:
        user_context = "I don't know much about this user yet — start building rapport."

    prompt = (
        f"Generate a short, sharp daily strategic brief for this user.\n"
        f"{user_context}\n\n"
        f"Include:\n"
        f"1. A one-line insight tailored to their context\n"
        f"2. A framework to apply today: {framework}\n"
        f"3. A challenge question they should answer today\n\n"
        f"Keep it under 300 words. Be warm but direct. Make it feel personal, not templated."
    )

    content = await _ask_edith(prompt)
    return content, {"framework": framework}
