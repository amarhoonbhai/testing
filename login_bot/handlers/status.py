"""
Status command handler for Login Bot.
Shows the user's current connected account summary.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from models.session import get_all_user_sessions
from core.config import MAIN_BOT_USERNAME


def get_status_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Account", callback_data="add_account"),
            InlineKeyboardButton("📱 Manage", callback_data="manage_accounts"),
        ],
        [
            InlineKeyboardButton("🏠 Home", callback_data="login_home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - shows user's account summary."""
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "User"

    accounts = await get_all_user_sessions(user_id)
    total = len(accounts)
    active = sum(1 for a in accounts if a.get("connected"))
    paused = sum(1 for a in accounts if a.get("paused_until"))

    if total == 0:
        status_body = (
            "⚪ *No accounts connected yet.*\n\n"
            "Tap *Add Account* below to link your first Telegram session."
        )
    else:
        lines = []
        for i, acc in enumerate(accounts, 1):
            phone = acc.get("phone", "Unknown")
            if acc.get("paused_until"):
                icon = "⏸️"
                state = "Paused"
            elif acc.get("connected"):
                icon = "🟢"
                state = "Active"
            else:
                icon = "🔴"
                state = "Disconnected"
            lines.append(f"  {i}. {icon} `{phone}` — _{state}_")

        account_list = "\n".join(lines)
        status_body = (
            f"📊 *Account Summary*\n\n"
            f"{account_list}\n\n"
            f"┌ Total   : `{total}`\n"
            f"├ Active  : `{active}`\n"
            f"├ Paused  : `{paused}`\n"
            f"└ Offline : `{total - active - paused}`"
        )

    text = (
        f"👤 *{first_name}'s Status*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{status_body}"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_status_keyboard(),
    )
