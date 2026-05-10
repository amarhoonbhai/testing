"""
Database models — CRUD operations for the Group Broadcaster.

Single 'users' collection stores everything: user info, message, session, groups, stats.
All functions operate on the shared Motor database instance.
"""

from datetime import datetime
from typing import Optional

from app.database.mongo import get_db
from app.config import DEFAULT_INTERVAL


# ═══════════════════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════════════════

async def upsert_user(telegram_user_id: int, username: str = "") -> dict:
    """Create or update a user record."""
    db = get_db()
    now = datetime.utcnow()

    default_doc = {
        "telegram_user_id": telegram_user_id,
        "message": None,                # {text, media_type, media_file_id}
        "session_encrypted": None,       # Encrypted Telethon session string
        "phone_masked": None,            # Masked phone for display
        "groups": [],                    # List of group link strings
        "group_fails": {},               # {group_link: consecutive_fail_count}
        "interval_seconds": DEFAULT_INTERVAL,
        "is_broadcasting": False,
        "total_sent": 0,
        "total_failed": 0,
        "last_sent_at": None,
        "created_at": now,
    }

    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {
            "$setOnInsert": default_doc,
            "$set": {"username": username, "last_seen": now},
        },
        upsert=True,
    )

    return await get_user(telegram_user_id)


async def get_user(telegram_user_id: int) -> Optional[dict]:
    """Get user by Telegram user ID."""
    db = get_db()
    return await db.users.find_one({"telegram_user_id": telegram_user_id})


async def update_user(telegram_user_id: int, **fields) -> dict:
    """Partial update on user document."""
    db = get_db()
    fields["updated_at"] = datetime.utcnow()
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$set": fields},
    )
    return await get_user(telegram_user_id)


# ═══════════════════════════════════════════════════════════════════════════════
#  MESSAGE
# ═══════════════════════════════════════════════════════════════════════════════

async def set_message(telegram_user_id: int, text: str = None,
                      media_type: str = None, media_file_id: str = None) -> dict:
    """Save the broadcast message for a user."""
    msg = {
        "text": text,
        "media_type": media_type,       # "photo", "video", or None
        "media_file_id": media_file_id,  # Telegram file_id
    }
    return await update_user(telegram_user_id, message=msg)


async def clear_message(telegram_user_id: int) -> dict:
    """Clear the broadcast message."""
    return await update_user(telegram_user_id, message=None)


# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION (Single Account)
# ═══════════════════════════════════════════════════════════════════════════════

async def set_session(telegram_user_id: int, encrypted_session: str,
                      phone_masked: str) -> dict:
    """Save the encrypted Telethon session."""
    return await update_user(
        telegram_user_id,
        session_encrypted=encrypted_session,
        phone_masked=phone_masked,
    )


async def clear_session(telegram_user_id: int) -> dict:
    """Remove the stored session."""
    return await update_user(
        telegram_user_id,
        session_encrypted=None,
        phone_masked=None,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

async def add_groups(telegram_user_id: int, links: list[str]) -> dict:
    """Add group links. Deduplicates against existing groups."""
    db = get_db()
    user = await get_user(telegram_user_id)
    existing = set(user.get("groups", [])) if user else set()

    new_links = [link for link in links if link not in existing]
    if not new_links:
        return {"added": 0, "total": len(existing)}

    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {
            "$push": {"groups": {"$each": new_links}},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )

    return {"added": len(new_links), "total": len(existing) + len(new_links)}


async def get_groups(telegram_user_id: int) -> list[str]:
    """Get all group links for a user."""
    user = await get_user(telegram_user_id)
    return user.get("groups", []) if user else []


async def get_group_count(telegram_user_id: int) -> int:
    """Get total group count for a user."""
    groups = await get_groups(telegram_user_id)
    return len(groups)


async def clear_groups(telegram_user_id: int) -> int:
    """Remove all groups. Returns count removed."""
    user = await get_user(telegram_user_id)
    count = len(user.get("groups", [])) if user else 0
    await update_user(telegram_user_id, groups=[], group_fails={})
    return count


# ═══════════════════════════════════════════════════════════════════════════════
#  BROADCAST STATE
# ═══════════════════════════════════════════════════════════════════════════════

async def set_broadcasting(telegram_user_id: int, is_broadcasting: bool) -> dict:
    """Set the broadcasting state."""
    return await update_user(telegram_user_id, is_broadcasting=is_broadcasting)


async def set_interval(telegram_user_id: int, seconds: int) -> dict:
    """Set the broadcast cycle interval."""
    return await update_user(telegram_user_id, interval_seconds=seconds)


async def get_broadcasting_users() -> list[dict]:
    """Get all users who are currently broadcasting (for auto-resume)."""
    db = get_db()
    cursor = db.users.find({"is_broadcasting": True})
    return await cursor.to_list(length=10000)


# ═══════════════════════════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════════════════════════

async def increment_sent(telegram_user_id: int) -> None:
    """Increment total sent counter."""
    db = get_db()
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {
            "$inc": {"total_sent": 1},
            "$set": {"last_sent_at": datetime.utcnow()},
        },
    )


async def increment_failed(telegram_user_id: int) -> None:
    """Increment total failed counter."""
    db = get_db()
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$inc": {"total_failed": 1}},
    )


async def increment_group_fail(telegram_user_id: int, group_link: str) -> int:
    """Increment consecutive failure count for a group. Returns new count."""
    db = get_db()
    # Use dot notation for nested dict update
    safe_key = group_link.replace(".", "_DOT_").replace("$", "_DOLLAR_")
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$inc": {f"group_fails.{safe_key}": 1}},
    )
    user = await get_user(telegram_user_id)
    return user.get("group_fails", {}).get(safe_key, 0)


async def reset_group_fail(telegram_user_id: int, group_link: str) -> None:
    """Reset consecutive failure count for a group (on success)."""
    db = get_db()
    safe_key = group_link.replace(".", "_DOT_").replace("$", "_DOLLAR_")
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$set": {f"group_fails.{safe_key}": 0}},
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

async def get_all_users_count() -> int:
    """Get total user count."""
    db = get_db()
    return await db.users.count_documents({})


async def get_global_stats() -> dict:
    """Get global broadcast statistics."""
    db = get_db()

    total_users = await db.users.count_documents({})
    broadcasting = await db.users.count_documents({"is_broadcasting": True})

    pipeline = [
        {"$group": {
            "_id": None,
            "total_sent": {"$sum": "$total_sent"},
            "total_failed": {"$sum": "$total_failed"},
        }}
    ]
    agg = await db.users.aggregate(pipeline).to_list(1)

    total_sent = agg[0]["total_sent"] if agg else 0
    total_failed = agg[0]["total_failed"] if agg else 0
    total = total_sent + total_failed
    success_rate = f"{(total_sent / total * 100):.1f}%" if total > 0 else "N/A"

    return {
        "total_users": total_users,
        "broadcasting": broadcasting,
        "total_sent": total_sent,
        "total_failed": total_failed,
        "success_rate": success_rate,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  INDEXES
# ═══════════════════════════════════════════════════════════════════════════════

async def init_db_indexes():
    """Initialize MongoDB indexes."""
    db = get_db()
    from pymongo import ASCENDING

    await db.users.create_index([("telegram_user_id", ASCENDING)], unique=True)
    await db.users.create_index([("is_broadcasting", ASCENDING)])

    print("Database indexes initialized.")
