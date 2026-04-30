"""
Analytics handler — display broadcasting statistics.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.database.models import get_user, get_analytics, get_user_accounts, get_group_count
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu

logger = logging.getLogger(__name__)


async def analytics_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show analytics dashboard."""
    user_id = update.effective_user.id

    user = await get_user(user_id)
    stats = await get_analytics(user_id)
    accounts = await get_user_accounts(user_id)
    group_count = await get_group_count(user_id)

    active_accounts = sum(1 for a in accounts if a.get("status") == "active")

    last_broadcast = "Never"
    if stats.get("last_broadcast_at"):
        last_broadcast = stats["last_broadcast_at"].strftime("%Y-%m-%d %H:%M UTC")

    current_status = user.get("ads_status", "paused") if user else "paused"
    if user and user.get("night_mode_paused"):
        current_status = "night_paused"

    text = messages.analytics_text(
        total_sent=stats.get("total_sent", 0),
        failed_count=stats.get("failed_count", 0),
        active_accounts=active_accounts,
        last_broadcast=last_broadcast,
        current_status=current_status,
        group_count=group_count,
    )

    await _send_menu(update, context, text, keyboards.analytics_keyboard())
