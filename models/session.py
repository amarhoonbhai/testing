"""
Telegram session model — CRUD for the sessions collection.

Each document represents one Telegram account (phone) linked to a user.
"""

from datetime import datetime, timedelta
from typing import Optional, List

from core.database import get_database


async def create_session(
    user_id: int,
    phone: str,
    session_string: str,
    api_id: int = None,
    api_hash: str = None,
) -> dict:
    """Create or update a user session with per-user API credentials."""
    db = get_database()
    now = datetime.utcnow()

    update_doc = {
        "$set": {
            "session_string": session_string,
            "connected": True,
            "connected_at": now,
            "last_active_at": now,
            "worker_disabled": False,
            "auth_fail_count": 0,
        },
        "$setOnInsert": {
            "user_id": user_id,
            "phone": phone,
            "created_at": now,
            "current_msg_index": 0,
            "is_active": True,
        },
    }

    if api_id:
        update_doc["$set"]["api_id"] = api_id
    if api_hash:
        update_doc["$set"]["api_hash"] = api_hash

    result = await db.sessions.find_one_and_update(
        {"user_id": user_id, "phone": phone},
        update_doc,
        upsert=True,
        return_document=True,
    )
    return result


async def get_session(user_id: int, phone: str = None) -> Optional[dict]:
    """Get session by user ID (and optionally phone)."""
    db = get_database()
    query = {"user_id": user_id, "connected": True}
    if phone:
        query["phone"] = phone
    return await db.sessions.find_one(query)


async def get_all_user_sessions(user_id: int) -> List[dict]:
    """Get all connected sessions for a specific user."""
    db = get_database()
    cursor = db.sessions.find({"user_id": user_id, "connected": True})
    return await cursor.to_list(length=100)


async def get_all_connected_sessions() -> List[dict]:
    """Get all connected sessions across all users (for worker sync)."""
    db = get_database()
    cursor = db.sessions.find({"connected": True})
    return await cursor.to_list(length=10_000)


async def update_session_activity(user_id: int, phone: str):
    """Update last active timestamp for a session."""
    db = get_database()
    await db.sessions.update_one(
        {"user_id": user_id, "phone": phone},
        {"$set": {"last_active_at": datetime.utcnow()}},
    )


async def update_current_msg_index(user_id: int, phone: str, index: int):
    """Update current message index for a specific account (phone)."""
    db = get_database()
    await db.sessions.update_one(
        {"user_id": user_id, "phone": phone},
        {"$set": {"current_msg_index": index, "updated_at": datetime.utcnow()}},
        upsert=True
    )


async def disconnect_session(user_id: int, phone: str = None):
    """Mark session(s) as disconnected."""
    db = get_database()
    query = {"user_id": user_id}
    if phone:
        query["phone"] = phone
    await db.sessions.update_many(query, {"$set": {"connected": False}})


async def is_account_active(user_id: int, phone: str) -> bool:
    """Check if a specific account is connected."""
    db = get_database()
    doc = await db.sessions.find_one({"user_id": user_id, "phone": phone, "connected": True})
    return doc is not None


async def mark_session_auth_failed(user_id: int, phone: str) -> int:
    """Record a failed auth attempt. Returns new total fail count."""
    db = get_database()
    result = await db.sessions.find_one_and_update(
        {"user_id": user_id, "phone": phone},
        {
            "$inc": {"auth_fail_count": 1},
            "$set": {"last_auth_fail": datetime.utcnow()},
        },
        return_document=True,
    )
    return result.get("auth_fail_count", 1) if result else 1


async def mark_session_disabled(user_id: int, phone: str, reason: str):
    """Permanently disable a session."""
    db = get_database()
    await db.sessions.update_one(
        {"user_id": user_id, "phone": phone},
        {"$set": {
            "connected": False,
            "worker_disabled": True,
            "disabled_reason": reason,
            "disabled_at": datetime.utcnow(),
        }},
    )



async def pause_session(user_id: int, phone: str, duration_hours: int = 24):
    """Temporarily pause a session (auto-cooldown)."""
    db = get_database()
    paused_until = datetime.utcnow() + timedelta(hours=duration_hours)
    await db.sessions.update_one(
        {"user_id": user_id, "phone": phone},
        {"$set": {"paused_until": paused_until}}
    )


async def is_session_paused(user_id: int, phone: str) -> bool:
    """Check if session is currently in cooldown."""
    db = get_database()
    doc = await db.sessions.find_one({"user_id": user_id, "phone": phone})
    if not doc or "paused_until" not in doc:
        return False
    return datetime.utcnow() < doc["paused_until"]


async def reset_session_auth_fails(user_id: int, phone: str):
    """Clear auth failure counter after successful connection."""
    db = get_database()
    await db.sessions.update_one(
        {"user_id": user_id, "phone": phone},
        {
            "$set": {"auth_fail_count": 0},
            "$unset": {"last_auth_fail": ""},
        },
    )


async def get_session_paused_until(user_id: int, phone: str) -> Optional[datetime]:
    """Get the cooldown expiration timestamp."""
    db = get_database()
    doc = await db.sessions.find_one({"user_id": user_id, "phone": phone})
    return doc.get("paused_until") if doc else None


async def toggle_session_ads(user_id: int, phone: str, is_active: bool):
    """Toggle ads for a specific account."""
    db = get_database()
    await db.sessions.update_one(
        {"user_id": user_id, "phone": phone},
        {"$set": {"is_active": is_active}}
    )


async def update_session_original_profile(user_id: int, phone: str, first: str, last: str = "", bio: str = ""):
    """Store the original profile (name/bio) if not already stored."""
    db = get_database()
    await db.sessions.update_one(
        {"user_id": user_id, "phone": phone, "original_first_name": {"$exists": False}},
        {"$set": {
            "original_first_name": first, 
            "original_last_name": last,
            "original_bio": bio,
            "profile_captured_at": datetime.utcnow()
        }},
    )


async def archive_session(user_id: int, phone: str, reason: str):
    """
    Archive a session by moving it to 'archived_sessions' and deleting it from 'sessions'.
    Used for deactivated or permanently revoked accounts.
    """
    import logging
    logger = logging.getLogger(__name__)
    db = get_database()
    
    # 1. Fetch the existing session
    session = await db.sessions.find_one({"user_id": user_id, "phone": phone})
    if not session:
        return
        
    # 2. Add archive metadata
    session["archived_at"] = datetime.utcnow()
    session["archive_reason"] = reason
    session["connected"] = False
    
    # 3. Save to archives
    await db.archived_sessions.insert_one(session)
    
    # 4. Remove from active sessions
    await db.sessions.delete_one({"user_id": user_id, "phone": phone})
    
    logger.info(f"📦 Archived invalid session: {phone} (User: {user_id}) | Reason: {reason}")
