"""
Group model — CRUD for the groups collection.
Each group is now strictly linked to an account_phone for per-account management.
"""

from datetime import datetime
from typing import Optional, List

from core.database import get_database
from core.config import MAX_GROUPS_PER_USER


async def add_group(
    user_id: int,
    chat_id: int,
    chat_title: str,
    account_phone: str, # Mandatory now
    chat_username: str = None,
) -> dict:
    """Add or update a group linked to a specific account phone."""
    db = get_database()
    now = datetime.utcnow()

    # Pre-check group count if needed
    
    result = await db.groups.find_one_and_update(
        {"user_id": user_id, "chat_id": chat_id, "account_phone": account_phone},
        {
            "$set": {
                "chat_title": chat_title,
                "chat_username": chat_username,
                "enabled": True,
                "updated_at": now,
            },
            "$setOnInsert": {
                "user_id": user_id,
                "chat_id": chat_id,
                "account_phone": account_phone,
                "created_at": now,
            },
        },
        upsert=True,
        return_document=True,
    )
    return result


async def get_user_groups(
    user_id: int,
    phone: str = None, # Mandatory for per-account management UI
    enabled_only: bool = False,
) -> List[dict]:
    """Get all groups for user (filtered by phone)."""
    db = get_database()
    query: dict = {"user_id": user_id}
    if phone:
        query["account_phone"] = phone
    if enabled_only:
        query["enabled"] = True
    
    cursor = db.groups.find(query)
    return await cursor.to_list(length=1000)


async def remove_group(user_id: int, chat_id: int, phone: str = None):
    """Remove a group."""
    db = get_database()
    query = {"user_id": user_id, "chat_id": chat_id}
    if phone:
        query["account_phone"] = phone
    await db.groups.delete_one(query)


async def toggle_group(
    user_id: int,
    chat_id: int,
    enabled: bool,
    phone: str = None,
    reason: str = None,
):
    """Enable or disable a group."""
    db = get_database()
    query = {"user_id": user_id, "chat_id": chat_id}
    if phone:
        query["account_phone"] = phone
        
    update: dict = {
        "enabled": enabled,
        "updated_at": datetime.utcnow(),
    }
    if reason:
        update["pause_reason"] = reason
    elif enabled:
        update["pause_reason"] = None

    await db.groups.update_one(
        query,
        {"$set": update},
    )


async def get_group_count(user_id: int, phone: str = None) -> int:
    """Get count of user's groups (optionally for a specific phone)."""
    db = get_database()
    query = {"user_id": user_id}
    if phone:
        query["account_phone"] = phone
    return await db.groups.count_documents(query)


async def get_group_by_id(user_id: int, chat_id: int, phone: str = None) -> Optional[dict]:
    """Get a single group document by user_id + chat_id."""
    db = get_database()
    query = {"user_id": user_id, "chat_id": chat_id}
    if phone:
        query["account_phone"] = phone
    return await db.groups.find_one(query)


async def mark_group_failing(user_id: int, chat_id: int, reason: str):
    """Mark a group as failing."""
    db = get_database()
    await db.groups.update_one(
        {"user_id": user_id, "chat_id": chat_id, "first_fail_at": {"$exists": False}},
        {"$set": {
            "first_fail_at": datetime.utcnow(),
            "fail_reason": reason,
            "enabled": False,
            "pause_reason": reason,
        }},
    )
    # If already marked, just update reason
    await db.groups.update_one(
        {"user_id": user_id, "chat_id": chat_id, "first_fail_at": {"$exists": True}},
        {"$set": {"fail_reason": reason, "enabled": False, "pause_reason": reason}},
    )


async def clear_group_fail(user_id: int, chat_id: int):
    """Clear failing status after a successful send."""
    db = get_database()
    await db.groups.update_one(
        {"user_id": user_id, "chat_id": chat_id},
        {"$unset": {"first_fail_at": "", "fail_reason": ""},
         "$set": {"enabled": True, "pause_reason": None}},
    )


async def get_all_failing_groups() -> List[dict]:
    """Get all groups currently marked as failing."""
    db = get_database()
    cursor = db.groups.find({"first_fail_at": {"$exists": True}})
    return await cursor.to_list(length=1000)


async def remove_stale_failing_groups(user_id: int) -> int:
    """Remove groups failing for more than 24 hours. Returns count removed."""
    from datetime import timedelta
    db = get_database()
    cutoff = datetime.utcnow() - timedelta(hours=24)
    result = await db.groups.delete_many({
        "user_id": user_id,
        "first_fail_at": {"$lte": cutoff},
    })
    return result.deleted_count
