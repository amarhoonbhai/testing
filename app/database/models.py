"""
Database models — CRUD operations for the Group Broadcaster.

Single 'users' collection stores everything: user info, session, groups, stats, entity cache, diagnostics.
All functions operate on the shared Motor database instance.
"""

from datetime import datetime
import random
from typing import Optional

from app.database.mongo import get_db
from app.config import DEFAULT_INTERVAL



# ═══════════════════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════════════════

# Realistic devices for Telethon connection parameter rotation
DEVICES = [
    {"device_model": "iPhone 14 Pro", "system_version": "iOS 16.5", "app_version": "10.0.1"},
    {"device_model": "Samsung Galaxy S23", "system_version": "Android 13", "app_version": "10.0.2"},
    {"device_model": "Google Pixel 7 Pro", "system_version": "Android 13", "app_version": "10.0.0"},
    {"device_model": "iPad Pro", "system_version": "iOS 16.4.1", "app_version": "9.6.5"},
    {"device_model": "Xiaomi 13 Ultra", "system_version": "Android 13", "app_version": "10.1.0"},
    {"device_model": "iPhone 15 Pro Max", "system_version": "iOS 17.0.3", "app_version": "10.2.2"},
    {"device_model": "OnePlus 11", "system_version": "Android 13", "app_version": "10.0.5"},
    {"device_model": "MacBook Pro", "system_version": "macOS 13.5", "app_version": "9.7.0"},
]

def generate_random_device() -> dict:
    """Returns a randomly selected device configuration from DEVICES."""
    return random.choice(DEVICES)


async def upsert_user(telegram_user_id: int, username: str = "") -> dict:
    """Create or update a user record."""
    db = get_db()
    now = datetime.utcnow()

    device = generate_random_device()
    default_doc = {
        "telegram_user_id": telegram_user_id,
        "session_encrypted": None,       # Encrypted Telethon session string
        "phone_masked": None,            # Masked phone for display
        "groups": [],                    # List of group link strings
        "group_fails": {},               # {group_link: consecutive_fail_count}
        "group_reasons": {},             # {group_link: str_reason}
        "entity_cache": {},              # {group_link: dict_input_peer}
        "interval_seconds": DEFAULT_INTERVAL,
        "is_broadcasting": False,
        "progress_message_id": None,     # ID of the live progress message
        "progress_chat_id": None,        # Chat ID for the live progress message
        "total_sent": 0,
        "total_failed": 0,
        "last_sent_at": None,
        "created_at": now,
        "is_premium": False,
        "original_bio": None,
        "original_last_name": None,
        "group_dead_since": {},
        "auto_responder_enabled": False,
        "auto_responder_message": "Hello! I am currently busy. I will get back to you soon.",
        "auto_responder_rules": {
            "only_during_broadcast": True,
            "exclude_contacts": True,
        },
        "auto_responder_cooldown_seconds": 21600,   # default 6 hours
        "auto_responder_persistent_cooldowns": {},  # {peer_id: UNIX_timestamp}
        "auto_responder_keywords": {},              # {keyword: reply_msg}
        "sleep_mode_enabled": True,
        "sleep_mode_start_hour": 0,                 # 12:00 AM
        "sleep_mode_end_hour": 5,                   # 5:00 AM
        "activity_logs": [],                        # last 20 events
        "health_status": "Not Checked",
        "last_health_check": None,
        "custom_api_id": None,
        "custom_api_hash": None,
        "device_model": device["device_model"],
        "system_version": device["system_version"],
        "app_version": device["app_version"],
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
#  GROUPS & DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════════

async def add_groups(telegram_user_id: int, links: list[str]) -> dict:
    """Add group links. Deduplicates against existing groups and enforces 50 limit."""
    db = get_db()
    user = await get_user(telegram_user_id)
    existing = set(user.get("groups", [])) if user else set()

    new_links = [link for link in links if link not in existing]
    if not new_links:
        return {"added": 0, "total": len(existing), "limit_reached": False}

    max_limit = 50
    if len(existing) >= max_limit:
        return {"added": 0, "total": len(existing), "limit_reached": True}

    available_slots = max_limit - len(existing)
    links_to_add = new_links[:available_slots]
    limit_reached = len(new_links) > available_slots

    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {
            "$push": {"groups": {"$each": links_to_add}},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )

    return {
        "added": len(links_to_add),
        "total": len(existing) + len(links_to_add),
        "limit_reached": limit_reached
    }


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
    await update_user(telegram_user_id, groups=[], group_fails={}, group_reasons={}, entity_cache={}, group_dead_since={})
    return count


async def set_group_reason(telegram_user_id: int, group_link: str, reason: str) -> None:
    """Set exact failure reason for a group."""
    db = get_db()
    safe_key = group_link.replace(".", "_DOT_").replace("$", "_DOLLAR_")
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$set": {f"group_reasons.{safe_key}": reason}},
    )


async def get_group_reasons(telegram_user_id: int) -> dict:
    """Get all failure reasons for a user's groups."""
    user = await get_user(telegram_user_id)
    return user.get("group_reasons", {}) if user else {}


async def prune_dead_groups(telegram_user_id: int, max_fails: int) -> int:
    """Remove all groups that have failed >= max_fails times. Returns count removed."""
    db = get_db()
    user = await get_user(telegram_user_id)
    if not user:
        return 0

    groups = user.get("groups", [])
    group_fails = user.get("group_fails", {})
    dead_groups = [g for g in groups if group_fails.get(g.replace(".", "_DOT_").replace("$", "_DOLLAR_"), 0) >= max_fails]

    if not dead_groups:
        return 0

    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {
            "$pull": {"groups": {"$in": dead_groups}},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )

    unset_dict = {}
    for g in dead_groups:
        safe_key = g.replace(".", "_DOT_").replace("$", "_DOLLAR_")
        unset_dict[f"group_fails.{safe_key}"] = ""
        unset_dict[f"group_reasons.{safe_key}"] = ""
        unset_dict[f"entity_cache.{safe_key}"] = ""
        unset_dict[f"group_dead_since.{safe_key}"] = ""

    if unset_dict:
        await db.users.update_one(
            {"telegram_user_id": telegram_user_id},
            {"$unset": unset_dict}
        )

    return len(dead_groups)


async def auto_prune_dead_groups(telegram_user_id: int) -> int:
    """
    Automatically remove groups that have been in a dead state (fails >= MAX_FAIL_SKIP)
    for more than 6 hours (21,600 seconds). Returns count of pruned groups.
    """
    import time
    db = get_db()
    user = await get_user(telegram_user_id)
    if not user:
        return 0

    groups = user.get("groups", [])
    group_dead_since = user.get("group_dead_since", {})
    now = time.time()
    
    # 6 hours = 21600 seconds
    COOLDOWN = 21600
    
    dead_groups_to_prune = []
    for g in groups:
        safe_key = g.replace(".", "_DOT_").replace("$", "_DOLLAR_")
        dead_timestamp = group_dead_since.get(safe_key)
        if dead_timestamp and (now - dead_timestamp >= COOLDOWN):
            dead_groups_to_prune.append(g)

    if not dead_groups_to_prune:
        return 0

    # Pull dead groups from the main groups list
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {
            "$pull": {"groups": {"$in": dead_groups_to_prune}},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )

    # Unset related diagnostic fields
    unset_dict = {}
    for g in dead_groups_to_prune:
        safe_key = g.replace(".", "_DOT_").replace("$", "_DOLLAR_")
        unset_dict[f"group_fails.{safe_key}"] = ""
        unset_dict[f"group_reasons.{safe_key}"] = ""
        unset_dict[f"entity_cache.{safe_key}"] = ""
        unset_dict[f"group_dead_since.{safe_key}"] = ""

    if unset_dict:
        await db.users.update_one(
            {"telegram_user_id": telegram_user_id},
            {"$unset": unset_dict}
        )

    # Add activity log for pruned groups
    for g in dead_groups_to_prune:
        await add_activity_log(
            telegram_user_id,
            "skipped",
            g,
            "Auto-pruned after failing for 6 hours"
        )

    return len(dead_groups_to_prune)


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTITY CACHE (Telethon InputPeer optimization)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_cached_entity(telegram_user_id: int, group_link: str) -> Optional[dict]:
    """Get cached Telethon InputPeer dictionary for a group."""
    user = await get_user(telegram_user_id)
    if not user:
        return None
    safe_key = group_link.replace(".", "_DOT_").replace("$", "_DOLLAR_")
    return user.get("entity_cache", {}).get(safe_key)


async def set_cached_entity(telegram_user_id: int, group_link: str, entity_dict: dict) -> None:
    """Cache a Telethon InputPeer dictionary for a group."""
    db = get_db()
    safe_key = group_link.replace(".", "_DOT_").replace("$", "_DOLLAR_")
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$set": {f"entity_cache.{safe_key}": entity_dict}},
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  BROADCAST STATE
# ═══════════════════════════════════════════════════════════════════════════════

async def set_broadcasting(telegram_user_id: int, is_broadcasting: bool) -> dict:
    """Set the broadcasting state."""
    return await update_user(telegram_user_id, is_broadcasting=is_broadcasting)


async def set_interval(telegram_user_id: int, seconds: int) -> dict:
    """Set the broadcast cycle interval."""
    return await update_user(telegram_user_id, interval_seconds=seconds)


async def set_progress_message(telegram_user_id: int, chat_id: int, message_id: int) -> dict:
    """Save the current progress message details to update it live."""
    return await update_user(
        telegram_user_id,
        progress_chat_id=chat_id,
        progress_message_id=message_id,
    )


async def clear_progress_message(telegram_user_id: int) -> dict:
    """Clear the progress message details."""
    return await update_user(
        telegram_user_id,
        progress_chat_id=None,
        progress_message_id=None,
    )


async def get_broadcasting_users() -> list[dict]:
    """Get all users who are currently broadcasting (for auto-resume)."""
    db = get_db()
    cursor = db.users.find({"is_broadcasting": True})
    return await cursor.to_list(length=10000)


async def get_active_users() -> list[dict]:
    """Get all users who have an active session and configured groups (for autonomous broadcast)."""
    db = get_db()
    cursor = db.users.find({
        "session_encrypted": {"$ne": None},
        "groups": {"$not": {"$size": 0}}
    })
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
    safe_key = group_link.replace(".", "_DOT_").replace("$", "_DOLLAR_")
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$inc": {f"group_fails.{safe_key}": 1}},
    )
    user = await get_user(telegram_user_id)
    new_fails = user.get("group_fails", {}).get(safe_key, 0)
    
    # If the group is now dead (fails >= MAX_FAIL_SKIP), set dead timestamp if not already set
    from app.config import MAX_FAIL_SKIP
    if new_fails >= MAX_FAIL_SKIP:
        group_dead_since = user.get("group_dead_since", {})
        if safe_key not in group_dead_since:
            import time
            await db.users.update_one(
                {"telegram_user_id": telegram_user_id},
                {"$set": {f"group_dead_since.{safe_key}": time.time()}}
            )
            
    return new_fails


async def reset_group_fail(telegram_user_id: int, group_link: str) -> None:
    """Reset consecutive failure count for a group (on success)."""
    db = get_db()
    safe_key = group_link.replace(".", "_DOT_").replace("$", "_DOLLAR_")
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {
            "$set": {
                f"group_fails.{safe_key}": 0,
                f"group_reasons.{safe_key}": "Operational",
            },
            "$unset": {
                f"group_dead_since.{safe_key}": ""
            }
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

async def get_all_users() -> list[dict]:
    """Get all user documents."""
    db = get_db()
    cursor = db.users.find({})
    return await cursor.to_list(length=10000)


async def update_user_premium(telegram_user_id: int, is_premium: bool) -> dict:
    """Update premium status for a user."""
    return await update_user(telegram_user_id, is_premium=is_premium)


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
#  ENHANCEMENTS: ACTIVITY LOGS, QUIET HOURS & CUSTOM COOLDOWNS
# ═══════════════════════════════════════════════════════════════════════════════

async def add_activity_log(telegram_user_id: int, log_type: str, group: str, details: str) -> None:
    """Add a broadcast log entry, keeping only the last 20 entries."""
    db = get_db()
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": log_type,
        "group": group,
        "details": details
    }
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {
            "$push": {
                "activity_logs": {
                    "$each": [entry],
                    "$slice": -20  # Keep only the last 20 elements
                }
            }
        }
    )


async def set_responder_persistent_cooldown(telegram_user_id: int, peer_id: int, timestamp: float) -> None:
    """Save the last reply timestamp for a peer to prevent spamming."""
    db = get_db()
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$set": {f"auto_responder_persistent_cooldowns.{peer_id}": timestamp}}
    )


async def add_keyword_rule(telegram_user_id: int, keyword: str, reply: str) -> dict:
    """Add or update a keyword reply rule (case-insensitive keyword stored clean)."""
    db = get_db()
    clean_keyword = keyword.strip().lower()
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$set": {f"auto_responder_keywords.{clean_keyword}": reply}}
    )
    return await get_user(telegram_user_id)


async def delete_keyword_rule(telegram_user_id: int, keyword: str) -> dict:
    """Remove a keyword rule."""
    db = get_db()
    clean_keyword = keyword.strip().lower()
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$unset": {f"auto_responder_keywords.{clean_keyword}": ""}}
    )
    return await get_user(telegram_user_id)


async def update_user_api_credentials(telegram_user_id: int, api_id: int, api_hash: str) -> dict:
    """Update custom API ID and Hash for a user."""
    return await update_user(
        telegram_user_id,
        custom_api_id=api_id,
        custom_api_hash=api_hash,
    )


async def clear_user_api_credentials(telegram_user_id: int) -> dict:
    """Clear custom API credentials (revert to default server keys)."""
    return await update_user(
        telegram_user_id,
        custom_api_id=None,
        custom_api_hash=None,
    )



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
