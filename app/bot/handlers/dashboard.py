"""
Dashboard handler — shows the main control panel with live stats.
Force-join is enforced via @require_join decorator.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.config import OWNER_ID
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
    
    # Check if user is the owner
    is_owner = (user_id == OWNER_ID)

    # Fetch extended stats
    groups = await get_user_groups(user_id)
    active_groups = sum(1 for g in groups if g.get("status") == "active")
    
    accounts = await get_user_accounts(user_id)
    healthy_accounts = sum(1 for a in accounts if a.get("status") == "active")

    # Get active tasks count
    from app.services.broadcast_service import get_active_broadcast_count
    active_in_cycle = get_active_broadcast_count() if ads_status == "running" else 0

    text = messages.dashboard_text(
        account_count=account_count,
        max_accounts=max_accounts,
        ad_set=ad_set,
        interval=interval,
        ads_status=ads_status,
        group_count=len(groups),
        night_paused=night_paused,
        active_in_cycle=active_in_cycle,
    )

    # Try to fetch user profile photo for dashboard too
    photo = None
    try:
        profile_photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if profile_photos.total_count > 0:
            photo = profile_photos.photos[0][-1].file_id
    except Exception:
        pass

    await _send_menu(
        update, context,
        text,
        keyboards.dashboard_keyboard(is_owner=is_owner),
        photo=photo,
    )
