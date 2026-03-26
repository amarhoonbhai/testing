"""
Plans model — plan CRUD (free, paid, referral bonus).

Users start with a permanent Free plan (no expiry).
Paid plans are weekly/monthly overlays on top.
"""

from datetime import datetime, timedelta
from typing import Optional

from core.database import get_database
from core.config import (
    PLAN_DURATIONS, DEFAULT_INTERVAL_MINUTES, TIMEZONE
)

import pytz

IST = pytz.timezone(TIMEZONE)


async def grant_free_plan(user_id: int):
    """Grant permanent free plan if user doesn't have one."""
    db = get_database()
    existing = await db.plans.find_one({"user_id": user_id})
    if existing:
        return

    now = datetime.utcnow()
    await db.plans.insert_one({
        "user_id": user_id,
        "plan_type": "free",
        "status": "active",
        "started_at": now,
        "expires_at": None,  # Free plan never expires
    })


# Backward-compatible alias
grant_trial_if_new = grant_free_plan


async def get_plan(user_id: int) -> Optional[dict]:
    """Get user's plan. Free plans never expire."""
    db = get_database()
    plan = await db.plans.find_one({"user_id": user_id})
    if plan:
        expires_at = plan.get("expires_at")
        # Only check expiry for paid plans (free plan has None)
        if expires_at and expires_at < datetime.utcnow():
            # Paid plan expired — downgrade back to free
            await db.plans.update_one(
                {"user_id": user_id},
                {"$set": {
                    "status": "active",
                    "plan_type": "free",
                    "expires_at": None,
                }},
            )
            plan["status"] = "active"
            plan["plan_type"] = "free"
            plan["expires_at"] = None
    return plan


async def is_plan_active(user_id: int) -> bool:
    """Check if user has active plan. Free plan is always active."""
    plan = await get_plan(user_id)
    return plan is not None and plan.get("status") == "active"


async def is_trial_user(user_id: int) -> bool:
    """Legacy check — now returns True for free plan users."""
    plan = await get_plan(user_id)
    if not plan:
        return False
    return plan.get("plan_type") in ("trial", "free") and plan.get("status") == "active"


async def extend_plan(user_id: int, days: int, upgrade_to_paid: bool = True):
    """Extend user's plan by days."""
    db = get_database()
    plan = await db.plans.find_one({"user_id": user_id})
    now = datetime.utcnow()

    if plan:
        current_expiry = plan.get("expires_at") or now
        if current_expiry < now:
            current_expiry = now
        new_expiry = current_expiry + timedelta(days=days)

        update = {
            "expires_at": new_expiry,
            "status": "active",
        }
        if upgrade_to_paid:
            update["plan_type"] = "premium"

        await db.plans.update_one({"user_id": user_id}, {"$set": update})
    else:
        await db.plans.insert_one({
            "user_id": user_id,
            "plan_type": "premium" if upgrade_to_paid else "free",
            "status": "active",
            "started_at": now,
            "expires_at": now + timedelta(days=days) if upgrade_to_paid else None,
        })


async def activate_plan(user_id: int, plan_type: str):
    """Activate a paid plan for user."""
    days = PLAN_DURATIONS.get(plan_type, 30)
    await extend_plan(user_id, days, upgrade_to_paid=True)
