"""
Dashboard handler — shows the main control panel with live stats.
Force-join is enforced via @require_join decorator.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.database.models import get_user, get_account_count, get_group_count, upsert_user
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join

logger = logging.getLogger(__name__)


@require_join
async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the dashboard with live user stats."""
    user_id = update.effective_user.id

    user = await get_user(user_id)
    if not user:
        user = await upsert_user(user_id, update.effective_user.username or "")

    account_count = await get_account_count(user_id)
    group_count = await get_group_count(user_id)
    max_accounts = user.get("max_accounts", 5)
    ad_set = bool(user.get("ad_message") or user.get("ad_media_file_id"))
    interval = user.get("interval_seconds", 1200)
    ads_status = user.get("ads_status", "paused")
    night_paused = user.get("night_mode_paused", False)

    text = messages.dashboard_text(
        account_count=account_count,
        max_accounts=max_accounts,
        ad_set=ad_set,
        interval=interval,
        ads_status=ads_status,
        group_count=group_count,
        night_paused=night_paused,
    )

    await _send_menu(
        update, context,
        text,
        keyboards.dashboard_keyboard(),
    )
