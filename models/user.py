"""
User model — CRUD operations for the users collection.

Preserves all existing functionality from db/models.py.
"""

from datetime import datetime, timedelta
from typing import Optional
import secrets

from core.database import get_database
from core.config import (
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
    """Bonus logic disabled - system is now free."""
    pass


async def get_user_config(user_id: int) -> dict:
    """Get user config, creating default if not exists."""
    db = get_database()
    
    config = await db.config.find_one({"user_id": user_id})
    
    if not config:
        config = {
            "user_id": user_id,
            "interval_min": DEFAULT_INTERVAL_MINUTES,
            "last_saved_id": 0,
            "updated_at": datetime.utcnow(),
        }
        await db.config.insert_one(config)
    
    return config


async def update_user_config(user_id: int, **kwargs) -> dict:
    """Update user config."""
    db = get_database()
    
    kwargs["updated_at"] = datetime.utcnow()
    
    await db.config.update_one(
        {"user_id": user_id},
        {"$set": kwargs},
        upsert=True
    )
    
    return await get_user_config(user_id)


async def update_last_saved_id(user_id: int, last_saved_id: int):
    """Update last processed saved message ID."""
    db = get_database()
    await db.config.update_one(
        {"user_id": user_id},
        {"$set": {"last_saved_id": last_saved_id, "updated_at": datetime.utcnow()}},
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
    
    from models.group import get_group_count
    group_count = await get_group_count(user_id)
    
    return {
        "user": user,
        "config": config,
        "group_count": group_count,
        "is_branded": await is_user_branded(user_id)
    }


async def get_all_users() -> list[int]:
    """Get all registered user IDs."""
    db = get_database()
    cursor = db.users.find({}, {"user_id": 1})
    return [u["user_id"] async for u in cursor]


async def get_all_users_for_broadcast(filter_type: str = "all") -> list[int]:
    """Get user IDs filtered for broadcast (all users)."""
    db = get_database()
    cursor = db.users.find({}, {"user_id": 1})
    return [u["user_id"] async for u in cursor]


# Alias for backward compatibility
upsert_user = create_user

