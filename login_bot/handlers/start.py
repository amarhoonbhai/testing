"""
Start and welcome handler for Login Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes

from models.user import upsert_user as create_user
from models.session import get_all_user_sessions
from models.user import upsert_user as create_user
from models.session import get_all_user_sessions
from login_bot.utils.keyboards import get_login_welcome_keyboard
from core.utils import escape_markdown_v2


def build_welcome_text(first_name: str, acc_count: int) -> str:
    """Build the full welcome message dynamically."""
    from html import escape
    
    # Escape first name for HTML
    safe_name = escape(first_name)

    # Account status badge
    if acc_count == 0:
        status_badge = "⚪ <b>No accounts connected yet</b>"
        status_hint = "<i>Tap ➕ below to link your first Telegram account.</i>"
    elif acc_count == 1:
        status_badge = "🟢 <b>1 account connected</b>"
        status_hint = "<i>You're all set! You can add more accounts any time.</i>"
    else:
        status_badge = f"🟢 <b>{acc_count} accounts connected</b>"
        status_hint = f"<i>You have {acc_count} active sessions on KURUP ADS.</i>"

    return (
        f"👋 <b>Hello, {safe_name}!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔐 <b>KURUP ADS — SECURE LOGIN PORTAL</b>\n\n"
        f"📌 <b>Account Status:</b>\n"
        f"{status_badge}\n"
        f"{status_hint}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ <b>Why connect here?</b>\n\n"
        f"  ✅ High-Volume: Auto-forward to 100+ groups\n"
        f"  ✅ Official Telegram API (not unofficial)\n"
        f"  ✅ Sessions encrypted — AES-256\n"
        f"  ✅ Complete control over your data\n"
        f"  ✅ Disconnect anytime instantly\n\n"
        f"📋 <b>What you need:</b>\n\n"
        f"  1️⃣  API ID & API Hash — <a href=\"https://my.telegram.org\">my.telegram.org</a>\n"
        f"  2️⃣  Your Phone Number (with country code)\n"
        f"  3️⃣  OTP sent to your Telegram\n"
        f"  4️⃣  2FA Password (if enabled)\n\n"
        f"👇 <b>Choose an action below:</b>"
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - shows welcome and account status."""
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "User"

    # Ensure user exists in db
    await create_user(user_id)

    # Get account stats
    accounts = await get_all_user_sessions(user_id)
    acc_count = len(accounts)

    await update.message.reply_text(
        build_welcome_text(first_name, acc_count),
        parse_mode="HTML",
        reply_markup=get_login_welcome_keyboard(),
        disable_web_page_preview=True,
    )
