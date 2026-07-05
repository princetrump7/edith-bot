"""
Help & About handler — /start, /help, /about commands.
"""

from telegram import Update, __version__ as TG_VERSION
from telegram.ext import ContextTypes

from config import BOT_NAME


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message — /start"""
    user = update.effective_user
    name = user.first_name if user else "there"

    msg = (
        f"👋 **Hey {name}!**\n\n"
        f"I'm **{BOT_NAME}** — your AI-powered Telegram assistant.\n\n"
        f"**What I can do:**\n"
        f"💬 **Chat** — Just send me a message to chat\n"
        f"🛠️ **Tools** — `/tools` to see all utilities\n"
        f"📝 **Analyze** — `/summarize`, `/translate`, `/grammar`\n"
        f"💻 **Code** — `/explain`, `/debug`\n"
        f"⚙️ **Settings** — `/settings` to customize me\n\n"
        f"📌 **Tips:**\n"
        f"• Reply to a message with a tool command\n"
        f"• Use `/newchat` to reset conversation\n"
        f"• `/help` for detailed help\n\n"
        f"Let's build something great! 🚀"
    )
    await update.effective_message.reply_text(msg, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detailed help — /help"""
    msg = (
        f"🆘 **{BOT_NAME} Help**\n\n"
        f"**Chat Commands**\n"
        f"`/start` — Welcome & quick start\n"
        f"`/help` — This help message\n"
        f"`/newchat` — Reset conversation history\n"
        f"`/chatstat` — Show chat statistics\n"
        f"`/tools` — List all available tools\n\n"

        f"**Text Tools**\n"
        f"`/summarize <text>` — Summarize text\n"
        f"`/translate <lang> <text>` — Translate text\n"
        f"`/grammar <text>` — Check grammar\n\n"

        f"**Code Tools**\n"
        f"`/explain <code>` — Explain code\n"
        f"`/debug <code>` — Debug code\n\n"

        f"**Information**\n"
        f"`/profile` — Your profile\n"
        f"`/settings` — Configure preferences\n"
        f"`/about` — About this bot\n\n"

        f"**Tips**\n"
        f"• Reply to any message with a command to use it on that text\n"
        f"• Send me a photo with a caption and I'll help based on it\n"
        f"• Use `/newchat` if I lose track of context\n"
        f"• Adjust response style in `/settings`\n\n"

        f"_Built with python-telegram-bot v{TG_VERSION}_"
    )
    await update.effective_message.reply_text(msg, parse_mode="Markdown")


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """About the bot — /about"""
    msg = (
        f"🤖 **About {BOT_NAME}**\n\n"
        f"An AI-powered Telegram bot that helps with chat, text analysis, "
        f"code review, translation, and more.\n\n"
        f"**Tech Stack:**\n"
        f"• Python + python-telegram-bot\n"
        f"• DeepSeek via OPENCODE API\n"
        f"• Modular tool system\n\n"
        f"**Features:**\n"
        f"• Natural conversation with context memory\n"
        f"• Text summarization & translation\n"
        f"• Code explanation & debugging\n"
        f"• Grammar checking & text analysis\n"
        f"• Customizable settings & profile\n\n"
        f"_Version 1.0.0_"
    )
    await update.effective_message.reply_text(msg, parse_mode="Markdown")
