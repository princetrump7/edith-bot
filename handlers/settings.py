"""
Settings & Profile handlers — user preferences, language, notifications.
"""

import logging
from typing import Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# In-memory user settings (persist to DB in production)
_user_settings: dict[int, dict[str, Any]] = {}


def _get_settings(user_id: int) -> dict[str, Any]:
    return _user_settings.setdefault(user_id, {
        "language": "English",
        "response_style": "balanced",
        "notifications": True,
        "history_enabled": True,
    })


def _update_setting(user_id: int, key: str, value: Any):
    settings = _get_settings(user_id)
    settings[key] = value


SETTING_OPTIONS: dict[str, list[str]] = {
    "language": ["English", "Spanish", "French", "German", "Portuguese", "Chinese", "Japanese", "Arabic", "Hindi"],
    "response_style": ["concise", "balanced", "detailed"],
    "notifications": ["on", "off"],
    "history_enabled": ["on", "off"],
}

SETTING_LABELS: dict[str, str] = {
    "language": "🌐 Language",
    "response_style": "📝 Response Style",
    "notifications": "🔔 Notifications",
    "history_enabled": "💾 Chat History",
}

SETTING_EXPLANATIONS: dict[str, str] = {
    "language": "Preferred response language",
    "response_style": "How detailed should responses be?",
    "notifications": "Receive bot updates and notifications",
    "history_enabled": "Keep conversation history for context",
}

STYLE_OPTIONS: dict[str, str] = {
    "concise": "Short, direct answers",
    "balanced": "Moderate detail",
    "detailed": "Thorough explanations",
}


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the settings menu — /settings"""
    user_id = update.effective_user.id if update.effective_user else 0
    settings = _get_settings(user_id)

    lines = [
        "⚙️ **Edith Settings**\n",
    ]
    for key, value in settings.items():
        label = SETTING_LABELS.get(key, key)
        display = value
        if key == "notifications" or key == "history_enabled":
            display = "✅ On" if value else "❌ Off"
        lines.append(f"**{label}:** `{display}`")

    lines.append("\n_Select a setting to change:_")

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"setting_{key}")]
        for key in settings.keys()
    ]
    keyboard.append([InlineKeyboardButton("📋 My Profile", callback_data="setting_profile")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile — /profile"""
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    settings = _get_settings(user_id)

    lines = [
        f"👤 **Your Profile**\n",
        f"• ID: `{user_id}`",
        f"• Name: {user.full_name or 'N/A'}",
        f"• Username: @{user.username or 'N/A'}",
        f"\n---\n",
    ]
    for key, value in settings.items():
        label = SETTING_LABELS.get(key, key)
        lines.append(f"• {label}: `{value}`")

    await update.effective_message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button presses from settings menu."""
    query = update.callback_query
    await query.answer()

    if not query.data:
        return

    user_id = update.effective_user.id if update.effective_user else 0

    # --- Profile view ---
    if query.data == "setting_profile":
        user = update.effective_user
        settings = _get_settings(user_id)
        text = (
            f"👤 **Your Profile**\n\n"
            f"• ID: `{user_id}`\n"
            f"• Name: {user.full_name if user else 'N/A'}\n"
            f"• Handle: @{user.username if user else 'N/A'}\n\n"
            f"**Preferences:**\n"
        )
        for k, v in settings.items():
            text += f"• {SETTING_LABELS.get(k, k)}: `{v}`\n"
        text += "\n_Use /settings to change preferences._"

        await query.edit_message_text(text, parse_mode="Markdown")
        return

    # --- Setting selection ---
    if query.data.startswith("setting_"):
        setting_key = query.data.replace("setting_", "")
        options = SETTING_OPTIONS.get(setting_key)
        if not options:
            await query.edit_message_text(
                f"Unknown setting: {setting_key}",
                parse_mode="Markdown",
            )
            return

        current = _get_settings(user_id).get(setting_key, "")
        label = SETTING_LABELS.get(setting_key, setting_key)
        explanation = SETTING_EXPLANATIONS.get(setting_key, "")

        keyboard = []
        for opt in options:
            marker = "✅ " if opt == current or (isinstance(current, bool) and (
                (opt == "on" and current) or (opt == "off" and not current)
            )) else ""
            callback = f"setval_{setting_key}_{opt}"
            keyboard.append([InlineKeyboardButton(f"{marker}{opt}", callback_data=callback)])

        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="settings_back")])

        await query.edit_message_text(
            f"**{label}**\n{explanation}\n\n_Choose a value:_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # --- Set value ---
    if query.data.startswith("setval_"):
        parts = query.data.split("_", 2)
        if len(parts) == 3:
            _, setting_key, value = parts
            typed_value: Any = value
            if value == "on":
                typed_value = True
            elif value == "off":
                typed_value = False
            _update_setting(user_id, setting_key, typed_value)
            # Show updated settings
            await cmd_settings(update, context)
        return

    # --- Back to main settings ---
    if query.data == "settings_back":
        await cmd_settings(update, context)
