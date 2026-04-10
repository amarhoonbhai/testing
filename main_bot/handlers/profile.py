"""
Profile handler for Main Bot — KURUP ADS.
Displays user profile with Telegram info, plan, and account statistics.
"""

from core.config import MAIN_BOT_USERNAME
from telegram import Update
from telegram.ext import ContextTypes
import datetime

from models.user import get_user_profile_data
from main_bot.utils.keyboards import get_profile_keyboard
from core.utils import escape_markdown


async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile button callback — show user profile card."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "User"
    last_name = user.last_name or ""
    username = escape_markdown(f"@{user.username}" if user.username else "Not set")
    full_name = escape_markdown(f"{first_name} {last_name}".strip())

    # Fetch aggregated profile data safely
    try:
        data = await get_user_profile_data(user_id)
    except Exception:
        data = {}

    # ─── Branding Status ───
    is_branded = data.get("is_branded", False)
    branding_line = "🟢 BRANDING ACTIVE" if is_branded else "🔴 BRANDING MISSING"
    status_line = "🆓 FREE FOREVER (Enforced Branding)"

    # ─── Sessions ───
    sessions = data.get("sessions", [])
    accounts_count = len(sessions)

    # ─── Stats ───
    total_sent = data.get("total_sent", 0)
    success_rate = data.get("success_rate", 0)
    total_groups = data.get("total_groups", 0)
    enabled_groups = data.get("enabled_groups", 0)

    # ─── Config ───
    config = data.get("config") or {}

    # ─── Referral ───
    user_data = data.get("user") or {}
    referral_code = user_data.get("referral_code", "N/A")
    referrals_count = user_data.get("referrals_count", 0)

    profile_text = f"""
👤 *YOUR PROFILE — KURUP ADS*

*Name:* {full_name}
*Username:* {username}
*User ID:* `{user_id}`

*SERVICE STATUS*
  {status_line}
  {branding_line}

*ACCOUNTS:* {accounts_count} connected
*GROUPS:* {enabled_groups}/{total_groups} active

*FORWARDING STATS*
  📤 Total Sent: {total_sent}
  🎯 Success Rate: {success_rate}%

*REFERRALS*
  Code: `{referral_code}`
  Invited: {referrals_count} users
"""

    await query.edit_message_text(
        profile_text,
        parse_mode="Markdown",
        reply_markup=get_profile_keyboard(),
    )
