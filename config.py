"""
Bot configuration — loaded from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "edith_bot")

# --- AI Provider (OpenCode Zen) ---
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://opencode.ai/zen/v1")
AI_MODEL = os.getenv("AI_MODEL", "deepseek-v4-flash")

# --- Deployment ---
APP_URL = os.getenv("APP_URL", "")  # public URL for webhook mode
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
PORT = int(os.getenv("PORT", "8080"))

# --- Bot Personality ---
BOT_NAME = os.getenv("BOT_NAME", "Edith")
BOT_DESCRIPTION = "AI-powered assistant — chat, translate, summarize, code, and more."
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", (
    "You are Edith, a versatile AI assistant running inside a Telegram bot. "
    "You can chat, analyze text and code, translate, summarize, search the web, "
    "provide weather/time info, and help with technical tasks. "
    "You cannot generate or create images or videos. "
    "Be concise, helpful, and friendly. Use Markdown formatting when appropriate."
))

# --- Limits ---
MAX_MESSAGE_LENGTH = 4000
MAX_HISTORY_LENGTH = 50  # messages per user
