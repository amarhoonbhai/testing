"""
Dashboard handler — shows the main control panel with live stats.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.config import OWNER_ID
from app.database.models import get_user, upsert_user
from app.services import engine
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

    has_account = bool(user.get("session_encrypted"))
    has_message = bool(user.get("message"))
    group_count = len(user.get("groups", []))
    total_sent = user.get("total_sent", 0)
    total_failed = user.get("total_failed", 0)
    interval = user.get("interval_seconds", 1200)
    phone_masked = user.get("phone_masked")

    # Check live broadcasting status (task may have crashed)
    is_broadcasting = engine.is_running(user_id)

    # Sync DB state if task died
    if user.get("is_broadcasting") and not is_broadcasting:
        from app.database.models import set_broadcasting
        await set_broadcasting(user_id, False)

    is_owner = (user_id == OWNER_ID)

    text = messages.dashboard_text(
        has_account=has_account,
        has_message=has_message,
        group_count=group_count,
        total_sent=total_sent,
        total_failed=total_failed,
        is_broadcasting=is_broadcasting,
        interval=interval,
        phone_masked=phone_masked,
    )

    reply_markup = keyboards.dashboard_keyboard(
        is_broadcasting=is_broadcasting,
        has_account=has_account,
        is_owner=is_owner,
    )

    await _send_menu(update, context, text, reply_markup)
