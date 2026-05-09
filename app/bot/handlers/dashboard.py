"""
Dashboard handler — shows the main control panel with live stats.
Force-join is enforced via @require_join decorator.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.config import OWNER_ID
from app.database.models import (
    get_user, get_account_count, get_group_count, upsert_user,
    get_user_groups, get_user_accounts,
)
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
    ads = user.get("ads", [])
    ad_set = len(ads) > 0
    interval = user.get("interval_seconds", 1200)
    ads_status = user.get("ads_status", "paused")
    night_paused = user.get("night_mode_paused", False)
    
    # Check if user is the owner
    is_owner = (user_id == OWNER_ID)

    # Fetch extended stats
    groups = await get_user_groups(user_id)
    accounts = await get_user_accounts(user_id)
    
    from datetime import datetime
    now = datetime.utcnow()
    
    health_stats = {
        "limited_accounts": sum(1 for a in accounts if a.get("status") == "limited" or (a.get("limited_until") and a.get("limited_until") > now)),
        "forbidden_groups": sum(1 for g in groups if g.get("can_send") is False or g.get("status") == "restricted"),
        "cooldown_groups": sum(1 for g in groups if g.get("next_allowed_at") and g.get("next_allowed_at") > now),
    }

    # Fetch analytics for "Today's Report"
    from app.database.models import get_analytics
    analytics = await get_analytics(user_id)

    # Get active tasks count (pending or locked jobs for this user)
    from app.database.mongo import get_db
    db = get_db()
    active_in_cycle = await db.broadcast_jobs.count_documents({
        "user_id": user_id,
        "status": "pending",
        "locked_until": {"$gt": now}
    })

    text = messages.dashboard_text(
        account_count=len([a for a in accounts if a.get("status") == "active"]),
        max_accounts=max_accounts,
        ad_set=ad_set,
        interval=interval,
        ads_status=ads_status,
        group_count=len(groups),
        night_paused=night_paused,
        active_in_cycle=active_in_cycle,
        health_stats=health_stats,
        analytics=analytics,
    )

    # Keyboards
    reply_markup = keyboards.dashboard_keyboard(ads_status=ads_status, is_owner=is_owner)

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
        reply_markup,
        photo=photo,
    )
