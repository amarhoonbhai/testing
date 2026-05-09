"""
Database models — CRUD operations for users, accounts, analytics, and groups.

All functions operate on the shared Motor database instance.
"""

from datetime import datetime, timedelta
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
        "ads": [],                  # Array of ad objects
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


async def add_user_ad(telegram_user_id: int, ad_data: dict) -> bool:
    """Add an ad to the user's list (max 3)."""
    db = get_db()
    user = await get_user(telegram_user_id)
    if not user or len(user.get("ads", [])) >= 3:
        return False
    
    import uuid
    ad_data["id"] = str(uuid.uuid4())[:8]
    ad_data["created_at"] = datetime.utcnow()
    
    await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$push": {"ads": ad_data}}
    )
    return True


async def delete_user_ad(telegram_user_id: int, ad_id: str) -> bool:
    """Remove a specific ad by ID."""
    db = get_db()
    result = await db.users.update_one(
        {"telegram_user_id": telegram_user_id},
        {"$pull": {"ads": {"id": ad_id}}}
    )
    return result.modified_count > 0


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
        "health": 100,              # 0-100 health score
        "success_count": 0,
        "failure_count": 0,
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
    user_id: int, phone_masked: str, status: str, reason: str = "", limited_until: datetime = None
) -> None:
    """Update account status (active/limited/failed/forbidden/error)."""
    db = get_db()
    fields = {
        "status": status, 
        "status_reason": reason,
        "updated_at": datetime.utcnow()
    }
    if limited_until:
        fields["limited_until"] = limited_until
    
    await db.accounts.update_one(
        {"user_id": user_id, "phone_masked": phone_masked},
        {"$set": fields},
    )


async def lock_account(phone_masked: str, worker_id: str) -> bool:
    """Try to lock an account for a worker."""
    db = get_db()
    now = datetime.utcnow()
    expiry = now + timedelta(minutes=10)

    result = await db.accounts.update_one(
        {
            "phone_masked": phone_masked,
            "$or": [
                {"worker_lock": None},
                {"worker_lock_until": {"$lte": now}}
            ]
        },
        {
            "$set": {
                "worker_lock": worker_id,
                "worker_lock_until": expiry
            }
        }
    )
    return result.modified_count > 0


async def unlock_account(phone_masked: str, worker_id: str) -> None:
    """Release an account lock."""
    db = get_db()
    await db.accounts.update_one(
        {"phone_masked": phone_masked, "worker_lock": worker_id},
        {"$set": {"worker_lock": None, "worker_lock_until": None}}
    )


async def update_account_health(user_id: int, phone_masked: str, delta: int) -> int:
    """Increment/decrement account health score (0-100)."""
    db = get_db()
    acc = await db.accounts.find_one({"user_id": user_id, "phone_masked": phone_masked})
    if not acc:
        return 100
    
    new_health = max(0, min(100, acc.get("health", 100) + delta))
    
    update_data = {"health": new_health, "updated_at": datetime.utcnow()}
    if delta > 0:
        update_data["success_count"] = acc.get("success_count", 0) + 1
    elif delta < 0:
        update_data["failure_count"] = acc.get("failure_count", 0) + 1
        
    await db.accounts.update_one(
        {"user_id": user_id, "phone_masked": phone_masked},
        {"$set": update_data}
    )
    return new_health


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
      - https://t.me/username/123 (Forum Topic)
      - https://t.me/c/12345/678 (Private Forum Topic)
      - https://t.me/c/12345 (Private Channel)
      - https://t.me/+inviteHash
      - https://t.me/joinchat/inviteHash
      - https://t.me/addlist/folderSlug
      - @username
    """
    link = link.strip().rstrip("/")

    # @username format
    if link.startswith("@"):
        return {"type": "username", "identifier": link[1:], "raw": link}

    # Forum Topic: t.me/username/123
    m = re.match(r"https?://t\.me/([a-zA-Z0-9_]+)/(\d+)$", link)
    if m:
        return {"type": "topic", "identifier": m.group(1), "topic_id": int(m.group(2)), "raw": link}

    # Private Topic: t.me/c/(\d+)/(\d+)
    m = re.match(r"https?://t\.me/c/(\d+)/(\d+)$", link)
    if m:
        return {"type": "private_topic", "identifier": int(m.group(1)), "topic_id": int(m.group(2)), "raw": link}

    # Private Channel: t.me/c/(\d+)$
    m = re.match(r"https?://t\.me/c/(\d+)$", link)
    if m:
        return {"type": "private_chat", "identifier": int(m.group(1)), "raw": link}

    # Folder link
    m = re.match(r"https?://t\.me/addlist/(.+)", link)
    if m:
        return {"type": "folder", "identifier": m.group(1), "raw": link}

    # Invite link
    m = re.match(r"https?://t\.me/\+(.+)", link)
    if m:
        return {"type": "invite", "identifier": m.group(1), "raw": link}
    m = re.match(r"https?://t\.me/joinchat/(.+)", link)
    if m:
        return {"type": "invite", "identifier": m.group(1), "raw": link}

    # Public username
    m = re.match(r"https?://t\.me/([a-zA-Z0-9_]+)$", link)
    if m:
        return {"type": "username", "identifier": m.group(1), "raw": link}

    return None


async def add_group(user_id: int, link: str, numeric_id: int = None) -> dict | None:
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
        "numeric_id": numeric_id,
        "topic_id": parsed.get("topic_id"),
        "status": "active",
        "can_send": True,           # Hardened permission flag
        "next_allowed_at": None,    # For SlowModeWait cooldowns
        "last_sent_at": None,
        "send_count": 0,
        "fail_count": 0,
        "failure_count": 0,         # Consecutive failures
        "last_error": None,
        "created_at": now,
    }

    # Match by numeric_id if available, otherwise by identifier + topic
    query = {"user_id": user_id}
    if numeric_id:
        query["numeric_id"] = numeric_id
    else:
        query["identifier"] = parsed["identifier"]
        query["topic_id"] = parsed.get("topic_id")

    await db.groups.update_one(query, {"$set": doc}, upsert=True)

    return doc


async def add_groups_bulk(user_id: int, entries: list[str | dict]) -> dict:
    """
    Add multiple group links/data at once.
    'entries' can be a list of strings (links) or dicts ({"link": str, "id": int}).
    Returns dict with added count and failed count.
    """
    added = 0
    failed = 0
    for entry in entries:
        if isinstance(entry, dict):
            result = await add_group(user_id, entry["link"], entry.get("id"))
        else:
            result = await add_group(user_id, entry)
            
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


async def update_group_health(
    user_id: int, identifier: str, status: str = None, can_send: bool = None, 
    next_allowed_at: datetime = None, error: str = None, numeric_id: int = None
) -> None:
    """Update granular group health info after a send attempt."""
    db = get_db()
    query = {"user_id": user_id}
    if numeric_id: query["numeric_id"] = numeric_id
    else: query["identifier"] = identifier

    fields = {"updated_at": datetime.utcnow()}
    if status: fields["status"] = status
    if can_send is not None: fields["can_send"] = can_send
    if next_allowed_at: fields["next_allowed_at"] = next_allowed_at
    if error: 
        fields["last_error"] = error
        # Increment failure count on error
        await db.groups.update_one(query, {"$inc": {"failure_count": 1}})
    else:
        # Reset failure count on success
        fields["failure_count"] = 0
        fields["can_send"] = True

    await db.groups.update_one(query, {"$set": fields})


async def get_active_groups(user_id: int) -> list[dict]:
    """Get only active groups that are safe to broadcast to."""
    db = get_db()
    now = datetime.utcnow()
    query = {
        "user_id": user_id, 
        "status": "active",
        "can_send": True,
        "failure_count": {"$lt": 10}, # Don't try permanently broken groups
        "$or": [
            {"next_allowed_at": None},
            {"next_allowed_at": {"$lte": now}}
        ]
    }
    cursor = db.groups.find(query).sort("last_sent_at", 1)
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


async def update_group_sent(user_id: int, identifier: str, numeric_id: int = None) -> None:
    """Update group after successful send."""
    db = get_db()
    query = {"user_id": user_id}
    if numeric_id:
        query["numeric_id"] = numeric_id
    else:
        query["identifier"] = identifier

    await db.groups.update_one(
        query,
        {
            "$set": {"last_sent_at": datetime.utcnow()},
            "$inc": {"send_count": 1},
        },
    )


async def update_group_failed(user_id: int, identifier: str, numeric_id: int = None) -> None:
    """Update group after failed send."""
    db = get_db()
    query = {"user_id": user_id}
    if numeric_id:
        query["numeric_id"] = numeric_id
    else:
        query["identifier"] = identifier

    await db.groups.update_one(
        query,
        {"$inc": {"fail_count": 1}},
    )


async def disable_group(user_id: int, identifier: str, reason: str = "", numeric_id: int = None) -> None:
    """Disable a group (forbidden, banned, etc)."""
    db = get_db()
    query = {"user_id": user_id}
    if numeric_id:
        query["numeric_id"] = numeric_id
    else:
        query["identifier"] = identifier

    await db.groups.update_one(
        query,
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


# ═══════════════════════════════════════════════════════════════════════════════
#  BROADCAST JOBS — Distributed worker management
# ═══════════════════════════════════════════════════════════════════════════════

async def create_broadcast_job(job_data: dict) -> bool:
    """
    Create a new broadcast job. 
    Uses a unique key (user_id + group_id + status:pending) to avoid duplicates.
    """
    db = get_db()
    now = datetime.utcnow()
    
    # Ensure mandatory fields
    job_data.update({
        "status": "pending",
        "attempts": 0,
        "created_at": now,
        "updated_at": now,
        "locked_until": None,
        "locked_by": None,
    })
    
    # Unique key for this specific pending broadcast
    job_data["unique_key"] = f"{job_data['user_id']}_{job_data['group_id']}_pending"

    try:
        await db.broadcast_jobs.insert_one(job_data)
        return True
    except Exception: # Duplicate key error or other
        return False


async def claim_job(worker_id: str, lease_seconds: int) -> Optional[dict]:
    """
    Find a pending job and lock it for a worker.
    Respects run_after and locked_until.
    """
    db = get_db()
    now = datetime.utcnow()
    locked_until = now + timedelta(seconds=lease_seconds)

    # Find job that is:
    # 1. Status 'pending'
    # 2. run_after <= now
    # 3. NOT locked, OR lock expired
    query = {
        "status": "pending",
        "run_after": {"$lte": now},
        "$or": [
            {"locked_until": None},
            {"locked_until": {"$lte": now}}
        ]
    }
    
    update = {
        "$set": {
            "locked_until": locked_until,
            "locked_by": worker_id,
            "updated_at": now
        }
    }
    
    return await db.broadcast_jobs.find_one_and_update(
        query, update, return_document=True
    )


async def release_job(job_id) -> None:
    """Release a job back to pending (e.g. if account is locked)."""
    db = get_db()
    await db.broadcast_jobs.update_one(
        {"_id": job_id},
        {
            "$set": {
                "locked_until": None,
                "locked_by": None,
                "updated_at": datetime.utcnow()
            }
        }
    )


async def complete_job(job_id) -> None:
    """Mark job as done and remove unique constraint."""
    db = get_db()
    await db.broadcast_jobs.update_one(
        {"_id": job_id},
        {
            "$set": {
                "status": "done",
                "unique_key": f"done_{job_id}", # Free up the pending unique key
                "updated_at": datetime.utcnow()
            }
        }
    )


async def fail_job(job_id, error: str, max_retries: int) -> None:
    """Increment attempts and potentially move to failed state."""
    db = get_db()
    job = await db.broadcast_jobs.find_one({"_id": job_id})
    if not job: return

    attempts = job.get("attempts", 0) + 1
    status = "pending"
    unique_key = job.get("unique_key")

    if attempts >= max_retries:
        status = "failed"
        unique_key = f"failed_{job_id}" # Free up the unique key

    await db.broadcast_jobs.update_one(
        {"_id": job_id},
        {
            "$set": {
                "status": status,
                "attempts": attempts,
                "last_error": error,
                "unique_key": unique_key,
                "locked_until": None, # Release lock
                "locked_by": None,
                "updated_at": datetime.utcnow(),
                "run_after": datetime.utcnow() # Retry immediately or add backoff
            }
        }
    )


async def cancel_user_jobs(user_id: int) -> int:
    """Delete all pending jobs for a user when ads are paused."""
    db = get_db()
    result = await db.broadcast_jobs.delete_many({
        "user_id": user_id,
        "status": "pending"
    })
    return result.deleted_count


async def init_db_indexes():
    """Initialize MongoDB indexes for scaling and uniqueness."""
    db = get_db()
    from pymongo import IndexModel, ASCENDING, DESCENDING

    # USERS
    await db.users.create_index([("telegram_user_id", ASCENDING)], unique=True)
    await db.users.create_index([("ads_status", ASCENDING)])

    # ACCOUNTS
    await db.accounts.create_index([("user_id", ASCENDING), ("status", ASCENDING)])
    await db.accounts.create_index([("limited_until", ASCENDING)])

    # GROUPS
    await db.groups.create_index([("user_id", ASCENDING), ("status", ASCENDING), ("last_sent_at", ASCENDING)])

    # BROADCAST JOBS
    await db.broadcast_jobs.create_index([("status", ASCENDING), ("run_after", ASCENDING)])
    await db.broadcast_jobs.create_index([("locked_until", ASCENDING)])
    await db.broadcast_jobs.create_index([("unique_key", ASCENDING)], unique=True)
    
    print("Database indexes initialized successfully.")
