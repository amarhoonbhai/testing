"""
Database models — CRUD operations for users, accounts, analytics, and groups.

All functions operate on the shared Motor database instance.
"""

from datetime import datetime
from typing import Optional
import re

from app.database.mongo import get_db
from app.config import DEFAULT_INTERVAL, MAX_ACCOUNTS


# ═══════════════════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════════════════

async def upsert_user(telegram_user_id: int, username: str = "") -> dict:
    """Create or update a user record."""
    db = get_db()
    now = datetime.utcnow()

    default_doc = {
        "telegram_user_id": telegram_user_id,
        "plan": "free",
        "max_accounts": MAX_ACCOUNTS,
        "ad_message": None,
        "ad_media_type": None,       # "photo", "video", or None
        "ad_media_file_id": None,
        "interval_seconds": DEFAULT_INTERVAL,
        "ads_status": "paused",
        "auto_reply_enabled": False,
        "auto_reply_text": None,
        "night_mode_paused": False,
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
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def mask_phone(phone: str) -> str:
    """Mask a phone number for display: +91xxxxxx1234."""
    if len(phone) < 6:
        return "***"
    return phone[:3] + "x" * (len(phone) - 7) + phone[-4:]


async def add_account(
    user_id: int,
    phone: str,
    phone_masked: str,
    encrypted_session: str,
) -> dict:
    """Add a hosted account for a user."""
    db = get_db()
    now = datetime.utcnow()

    doc = {
        "user_id": user_id,
        "phone_masked": phone_masked,
        "encrypted_session": encrypted_session,
        "status": "active",
        "created_at": now,
    }

    await db.accounts.update_one(
        {"user_id": user_id, "phone_masked": phone_masked},
        {"$set": doc},
        upsert=True,
    )

    return doc


async def get_user_accounts(user_id: int) -> list[dict]:
    """Get all accounts for a user."""
    db = get_db()
    cursor = db.accounts.find({"user_id": user_id})
    return await cursor.to_list(length=100)


async def get_account(user_id: int, phone_masked: str) -> Optional[dict]:
    """Get a specific account."""
    db = get_db()
    return await db.accounts.find_one(
        {"user_id": user_id, "phone_masked": phone_masked}
    )


async def delete_account(user_id: int, phone_masked: str) -> bool:
    """Delete an account. Returns True if deleted."""
    db = get_db()
    result = await db.accounts.delete_one(
        {"user_id": user_id, "phone_masked": phone_masked}
    )
    return result.deleted_count > 0


async def update_account_status(
    user_id: int, phone_masked: str, status: str
) -> None:
    """Update account status (active/paused/error)."""
    db = get_db()
    await db.accounts.update_one(
        {"user_id": user_id, "phone_masked": phone_masked},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}},
    )


async def get_account_count(user_id: int) -> int:
    """Get count of hosted accounts for a user."""
    db = get_db()
    return await db.accounts.count_documents({"user_id": user_id})


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS — Broadcast target management
# ═══════════════════════════════════════════════════════════════════════════════

def parse_telegram_link(link: str) -> dict | None:
    """
    Parse a Telegram link and extract entity info.
    Supports:
      - https://t.me/username
      - https://t.me/+inviteHash
      - https://t.me/joinchat/inviteHash
      - https://t.me/addlist/folderSlug  (folder links)
      - @username
    Returns dict with type and identifier, or None if invalid.
    """
    link = link.strip()

    # @username format
    if link.startswith("@"):
        return {"type": "username", "identifier": link[1:], "raw": link}

    # Folder link: t.me/addlist/xxx
    m = re.match(r"https?://t\.me/addlist/(.+)", link)
    if m:
        return {"type": "folder", "identifier": m.group(1), "raw": link}

    # Invite link: t.me/+xxx or t.me/joinchat/xxx
    m = re.match(r"https?://t\.me/\+(.+)", link)
    if m:
        return {"type": "invite", "identifier": m.group(1), "raw": link}
    m = re.match(r"https?://t\.me/joinchat/(.+)", link)
    if m:
        return {"type": "invite", "identifier": m.group(1), "raw": link}

    # Public username: t.me/username
    m = re.match(r"https?://t\.me/([a-zA-Z0-9_]+)$", link)
    if m:
        return {"type": "username", "identifier": m.group(1), "raw": link}

    return None


async def add_group(user_id: int, link: str) -> dict | None:
    """
    Add a group/channel link as a broadcast target.
    Returns the parsed group doc or None if invalid link.
    """
    parsed = parse_telegram_link(link)
    if not parsed:
        return None

    db = get_db()
    now = datetime.utcnow()

    doc = {
        "user_id": user_id,
        "link": parsed["raw"],
        "link_type": parsed["type"],
        "identifier": parsed["identifier"],
        "status": "active",
        "last_sent_at": None,
        "send_count": 0,
        "fail_count": 0,
        "created_at": now,
    }

    await db.groups.update_one(
        {"user_id": user_id, "identifier": parsed["identifier"]},
        {"$set": doc},
        upsert=True,
    )

    return doc


async def add_groups_bulk(user_id: int, links: list[str]) -> dict:
    """
    Add multiple group links at once.
    Returns dict with added count and failed count.
    """
    added = 0
    failed = 0
    for link in links:
        result = await add_group(user_id, link)
        if result:
            added += 1
        else:
            failed += 1
    return {"added": added, "failed": failed}


async def get_user_groups(user_id: int) -> list[dict]:
    """Get all broadcast target groups for a user."""
    db = get_db()
    cursor = db.groups.find({"user_id": user_id})
    return await cursor.to_list(length=10000)


async def get_active_groups(user_id: int) -> list[dict]:
    """Get only active groups for broadcasting."""
    db = get_db()
    cursor = db.groups.find({"user_id": user_id, "status": "active"})
    return await cursor.to_list(length=10000)


async def get_group_count(user_id: int) -> int:
    """Get total group count for a user."""
    db = get_db()
    return await db.groups.count_documents({"user_id": user_id})


async def delete_group(user_id: int, identifier: str) -> bool:
    """Delete a group by identifier."""
    db = get_db()
    result = await db.groups.delete_one(
        {"user_id": user_id, "identifier": identifier}
    )
    return result.deleted_count > 0


async def delete_all_groups(user_id: int) -> int:
    """Delete all groups for a user. Returns count deleted."""
    db = get_db()
    result = await db.groups.delete_many({"user_id": user_id})
    return result.deleted_count


async def update_group_sent(user_id: int, identifier: str) -> None:
    """Update group after successful send."""
    db = get_db()
    await db.groups.update_one(
        {"user_id": user_id, "identifier": identifier},
        {
            "$set": {"last_sent_at": datetime.utcnow()},
            "$inc": {"send_count": 1},
        },
    )


async def update_group_failed(user_id: int, identifier: str) -> None:
    """Update group after failed send."""
    db = get_db()
    await db.groups.update_one(
        {"user_id": user_id, "identifier": identifier},
        {"$inc": {"fail_count": 1}},
    )


async def disable_group(user_id: int, identifier: str, reason: str = "") -> None:
    """Disable a group (forbidden, banned, etc)."""
    db = get_db()
    await db.groups.update_one(
        {"user_id": user_id, "identifier": identifier},
        {"$set": {"status": "disabled", "disabled_reason": reason}},
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_analytics(user_id: int) -> dict:
    """Get analytics for a user, creating default if not exists."""
    db = get_db()
    doc = await db.analytics.find_one({"user_id": user_id})

    if not doc:
        doc = {
            "user_id": user_id,
            "total_sent": 0,
            "failed_count": 0,
            "last_broadcast_at": None,
        }
        await db.analytics.insert_one(doc)

    return doc


async def increment_sent(user_id: int) -> None:
    """Increment total sent counter."""
    db = get_db()
    await db.analytics.update_one(
        {"user_id": user_id},
        {
            "$inc": {"total_sent": 1},
            "$set": {"last_broadcast_at": datetime.utcnow()},
        },
        upsert=True,
    )


async def increment_failed(user_id: int) -> None:
    """Increment failed send counter."""
    db = get_db()
    await db.analytics.update_one(
        {"user_id": user_id},
        {"$inc": {"failed_count": 1}},
        upsert=True,
    )


async def reset_analytics(user_id: int) -> None:
    """Reset analytics counters."""
    db = get_db()
    await db.analytics.update_one(
        {"user_id": user_id},
        {"$set": {"total_sent": 0, "failed_count": 0, "last_broadcast_at": None}},
        upsert=True,
    )
