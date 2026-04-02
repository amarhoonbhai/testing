"""
User model — CRUD operations for the users collection.

Preserves all existing functionality from db/models.py.
"""

from datetime import datetime, timedelta
from typing import Optional
import secrets

from core.database import get_database
from core.config import (
    TRIAL_DAYS, REFERRAL_BONUS_DAYS, REFERRALS_NEEDED,
    BRANDING_NAME, BRANDING_BIO, DEFAULT_INTERVAL_MINUTES
)


async def create_user(user_id: int, referred_by: Optional[str] = None) -> dict:
    """Create a new user with optional referral tracking."""
    db = get_database()
    now = datetime.utcnow()

    referral_code = secrets.token_hex(4)

    doc = {
        "user_id": user_id,
        "referral_code": referral_code,
        "referred_by": referred_by,
        "referral_count": 0,
        "created_at": now,
    }

    await db.users.update_one(
        {"user_id": user_id},
        {"$setOnInsert": doc},
        upsert=True,
    )

    if referred_by:
        await db.users.update_one(
            {"referral_code": referred_by},
            {"$inc": {"referral_count": 1}},
        )

    return doc


async def get_user(user_id: int) -> Optional[dict]:
    """Get user by ID."""
    db = get_database()
    return await db.users.find_one({"user_id": user_id})


async def get_user_by_referral_code(code: str) -> Optional[dict]:
    """Get user by referral code."""
    db = get_database()
    return await db.users.find_one({"referral_code": code})


async def check_referral_bonus(referral_code: str):
    """Check if referrer earned bonus and apply it."""
    db = get_database()
    referrer = await db.users.find_one({"referral_code": referral_code})
    if not referrer:
        return

    if referrer.get("referral_count", 0) >= REFERRALS_NEEDED:
        from models.plan import extend_plan
        await extend_plan(referrer["user_id"], REFERRAL_BONUS_DAYS, upgrade_to_paid=False)


async def get_user_config(user_id: int) -> dict:
    """Get user settings (interval, shuffle, etc)."""
    db = get_database()
    doc = await db.user_configs.find_one({"user_id": user_id})
    if not doc:
        # Return defaults
        return {
            "user_id": user_id,
            "interval_min": DEFAULT_INTERVAL_MINUTES,
            "shuffle_mode": False,
            "copy_mode": False,
            "is_active": True,
            "auto_reply_enabled": False,
            "auto_reply_text": "Hello! I am currently away. (Auto-reply)",
        }
    return doc


async def update_user_config(user_id: int, **kwargs):
    """Update specific user settings."""
    db = get_database()
    kwargs["updated_at"] = datetime.utcnow()
    await db.user_configs.update_one(
        {"user_id": user_id},
        {"$set": kwargs},
        upsert=True
    )


async def is_user_branded(user_id: int, client=None) -> bool:
    """
    Check if a user is 'branded' (has required name/bio).
    If client is provided, it does a live check. Otherwise, it uses the database.
    """
    db = get_database()
    
    # Check live if client is provided
    if client:
        try:
            from telethon.tl.functions.users import GetFullUserRequest
            full = await client(GetFullUserRequest('me'))
            
            name_ok = BRANDING_NAME in (full.users[0].first_name or "")
            bio_ok = BRANDING_BIO in (full.full_user.about or "")
            
            is_branded = name_ok and bio_ok
            
            # Sync to DB
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"is_branded": is_branded, "last_branding_check": datetime.utcnow()}},
                upsert=True
            )
            return is_branded
        except Exception:
            pass # Fallback to DB

    # DB Lookup
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        return False
        
    return user.get("is_branded", False)


async def get_user_profile_data(user_id: int) -> dict:
    """Aggregate user data for the dashboard."""
    user = await get_user(user_id)
    config = await get_user_config(user_id)
    
    from models.plan import get_plan
    plan = await get_plan(user_id)
    
    from models.group import get_group_count
    group_count = await get_group_count(user_id)
    
    return {
        "user": user,
        "config": config,
        "plan": plan,
        "group_count": group_count,
        "is_branded": await is_user_branded(user_id)
    }


async def get_all_users() -> list[int]:
    """Get all registered user IDs."""
    db = get_database()
    cursor = db.users.find({}, {"user_id": 1})
    return [u["user_id"] async for u in cursor]


async def get_all_users_for_broadcast(filter_type: str = "all") -> list[int]:
    """Get user IDs filtered for broadcast (all, premium, trial, expired)."""
    db = get_database()
    
    if filter_type == "all":
        cursor = db.users.find({}, {"user_id": 1})
        return [u["user_id"] async for u in cursor]
        
    # For specific plans, we need to join with plans collection
    # Or just find in plans and then return user_ids
    if filter_type == "premium":
        cursor = db.plans.find({"plan_type": "premium", "status": "active"}, {"user_id": 1})
        return [u["user_id"] async for u in cursor]
    elif filter_type == "trial":
        cursor = db.plans.find({"plan_type": "trial", "status": "active"}, {"user_id": 1})
        return [u["user_id"] async for u in cursor]
    elif filter_type == "expired":
        cursor = db.plans.find({"status": "expired"}, {"user_id": 1})
        return [u["user_id"] async for u in cursor]
        
    return []


# Alias for backward compatibility
upsert_user = create_user

