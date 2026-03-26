"""
‣ Kᴜʀᴜᴘ Aᴅs — Scheduler Service

Every interval_min minutes, for each connected session:
  1. Fetches ALL messages from the account's Saved Messages
  2. Picks the next message (rotating index via current_msg_index)
  3. Resolves all the user's groups (including folder and private links)
  4. Creates a job in scheduled_jobs for the sender to process

Run:
    python -m services.scheduler.scheduler
"""

import asyncio
import logging
import signal
import platform
from datetime import datetime
from typing import Optional

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.errors import (
    AuthKeyUnregisteredError,
    UserDeactivatedBanError,
)

from core.logger import setup_service_logging
from core.database import init_database, close_connection, get_database
from core.config import DEFAULT_INTERVAL_MINUTES, MIN_INTERVAL_MINUTES

logger = logging.getLogger(__name__)

POLL_INTERVAL = 20  # seconds between polling each session


# ── DB Helpers ────────────────────────────────────────────────────────────────

async def get_all_connected_sessions() -> list:
    db = get_database()
    return await db.sessions.find({"connected": True}).to_list(length=10000)


async def get_user_config(user_id: int) -> dict:
    db = get_database()
    return await db.user_configs.find_one({"user_id": user_id}) or {}


async def get_user_groups(user_id: int) -> list:
    db = get_database()
    return await db.groups.find({"user_id": user_id, "enabled": True}).to_list(length=10000)


async def get_last_job_time(user_id: int, phone: str) -> Optional[datetime]:
    db = get_database()
    doc = await db.scheduled_jobs.find_one(
        {"user_id": user_id, "phone": phone},
        sort=[("created_at", -1)]
    )
    return doc.get("created_at") if doc else None


async def advance_msg_index(user_id: int, phone: str, total: int) -> int:
    """Atomically increment current_msg_index and return the new value."""
    db = get_database()
    result = await db.sessions.find_one_and_update(
        {"user_id": user_id, "phone": phone},
        {"$inc": {"current_msg_index": 1}},
        return_document=True
    )
    idx = (result or {}).get("current_msg_index", 0)
    return idx % total  # wrap around


async def create_send_job(user_id: int, phone: str, message_id: int,
                          groups: list, copy_mode: bool):
    from models.job import create_job
    await create_job(
        user_id=user_id,
        phone=phone,
        message_id=message_id,
        groups=groups,
        copy_mode=copy_mode,
    )


# ── Group Resolution ─────────────────────────────────────────────────────────

async def resolve_folder_groups(client: TelegramClient) -> list:
    """Expand all folder peers across all Telegram dialog filters."""
    peers = []
    try:
        result = await client(GetDialogFiltersRequest())
        for f in result.filters:
            if not hasattr(f, 'include_peers'):
                continue
            for peer in f.include_peers:
                try:
                    entity = await client.get_entity(peer)
                    peers.append(entity.id)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Folder resolution error: {e}")

    # Fallback: all groups & channels visible in dialogs
    if not peers:
        try:
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    peers.append(dialog.id)
        except Exception as e:
            logger.warning(f"Dialog fallback error: {e}")

    return list(set(peers))


async def resolve_groups_for_client(client: TelegramClient, raw_groups: list) -> list:
    """Convert stored group records to real Telegram chat IDs."""
    resolved = []
    slug_groups = []

    for g in raw_groups:
        chat_id = g.get("chat_id")
        title = g.get("chat_title", "")

        if title.startswith("[Folder]"):
            folder_peers = await resolve_folder_groups(client)
            resolved.extend(folder_peers)

        elif title.startswith("[Private]"):
            # Was stored with hash-based ID — use directly (account may have joined)
            if chat_id:
                resolved.append(chat_id)

        elif chat_id and abs(chat_id) > 1_000_000_000:
            # Real Telegram channel/group ID
            resolved.append(chat_id)

        else:
            # Slug / username based — need dialog lookup
            slug_groups.append(g)

    # Resolve username-based groups via dialogs
    if slug_groups:
        try:
            dialog_map = {}
            async for dialog in client.iter_dialogs():
                dialog_map[dialog.id] = dialog
                if dialog.name:
                    dialog_map[dialog.name.lower()] = dialog

            for g in slug_groups:
                title = g.get("chat_title", "")
                chat_id = g.get("chat_id")
                dlg = dialog_map.get(title.lower())
                if dlg:
                    resolved.append(dlg.id)
                    # Update DB with real chat_id
                    db = get_database()
                    await db.groups.update_one(
                        {"user_id": g["user_id"], "chat_id": chat_id},
                        {"$set": {"chat_id": dlg.id}}
                    )
                elif chat_id:
                    resolved.append(chat_id)
        except Exception as e:
            logger.warning(f"Slug resolution error: {e}")
            for g in slug_groups:
                if g.get("chat_id"):
                    resolved.append(g["chat_id"])

    return list(set(resolved))


# ── Per-Session Worker ────────────────────────────────────────────────────────

async def process_session(session_doc: dict):
    """
    For one session: check interval, fetch saved messages, pick next,
    resolve groups, create send job.
    """
    user_id = session_doc["user_id"]
    phone = session_doc.get("phone", "?")
    session_string = session_doc.get("session_string", "")
    api_id = session_doc.get("api_id")
    api_hash = session_doc.get("api_hash")

    if not all([session_string, api_id, api_hash]):
        return

    # ── Interval check ────────────────────────────────────────────────────
    config = await get_user_config(user_id)
    interval = max(
        int(config.get("interval_min", DEFAULT_INTERVAL_MINUTES)),
        MIN_INTERVAL_MINUTES
    )
    copy_mode = bool(config.get("copy_mode", False))

    last_job = await get_last_job_time(user_id, phone)
    if last_job:
        elapsed_min = (datetime.utcnow() - last_job).total_seconds() / 60
        if elapsed_min < interval:
            return  # Too soon — skip silently

    # ── Connect ───────────────────────────────────────────────────────────
    client = TelegramClient(
        StringSession(session_string), api_id, api_hash,
        device_model="‣ Kᴜʀᴜᴘ Aᴅs Scheduler",
        system_version="1.0", app_version="1.0",
    )

    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning(f"[{phone}] Unauthorized — disabling session")
            db = get_database()
            await db.sessions.update_one(
                {"user_id": user_id, "phone": phone},
                {"$set": {"connected": False, "disabled_reason": "unauthorized"}}
            )
            return

        # ── Fetch ALL Saved Messages ───────────────────────────────────
        saved_msgs = []
        async for msg in client.iter_messages("me", limit=200):
            if msg.text or msg.media:
                saved_msgs.append(msg.id)

        if not saved_msgs:
            logger.info(f"[{phone}] No saved messages — skipping")
            return

        # Reverse so oldest is index 0 (cycle from first to last)
        saved_msgs.reverse()
        total = len(saved_msgs)

        # ── Pick next message (rotating) ──────────────────────────────
        idx = await advance_msg_index(user_id, phone, total)
        message_id = saved_msgs[idx]

        # ── Get & resolve groups ──────────────────────────────────────
        raw_groups = await get_user_groups(user_id)
        if not raw_groups:
            logger.info(f"[{phone}] No groups configured — skipping")
            return

        group_ids = await resolve_groups_for_client(client, raw_groups)
        if not group_ids:
            logger.warning(f"[{phone}] No resolvable groups — skipping")
            return

        # ── Create job ────────────────────────────────────────────────
        await create_send_job(user_id, phone, message_id, group_ids, copy_mode)
        logger.info(
            f"[{phone}] ✅ Job created | msg #{message_id} "
            f"({idx+1}/{total}) → {len(group_ids)} groups"
        )

    except (AuthKeyUnregisteredError, UserDeactivatedBanError) as e:
        logger.warning(f"[{phone}] Account banned: {e}")
        db = get_database()
        await db.sessions.update_one(
            {"user_id": user_id, "phone": phone},
            {"$set": {"connected": False, "disabled_reason": str(e)}}
        )
    except Exception as e:
        logger.error(f"[{phone}] process_session error: {e}")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


# ── Main Loop ─────────────────────────────────────────────────────────────────

async def scheduler_loop():
    logger.info("=" * 50)
    logger.info("‣ Kᴜʀᴜᴘ Aᴅs  Scheduler — Message Cycling Mode")
    logger.info(f"Poll interval: {POLL_INTERVAL}s")
    logger.info("=" * 50)

    while True:
        try:
            sessions = await get_all_connected_sessions()
            if not sessions:
                logger.info("No connected sessions — waiting...")
            else:
                logger.info(f"Polling {len(sessions)} session(s)...")
                # Run all sessions concurrently (each checks its own interval)
                tasks = [process_session(s) for s in sessions]
                await asyncio.gather(*tasks, return_exceptions=True)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")

        await asyncio.sleep(POLL_INTERVAL)


async def main():
    setup_service_logging("scheduler")
    await init_database()

    loop = asyncio.get_running_loop()
    task = asyncio.create_task(scheduler_loop())

    if platform.system() != "Windows":
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, task.cancel)
            except NotImplementedError:
                pass

    try:
        await task
    except asyncio.CancelledError:
        logger.info("Scheduler shutting down...")
    finally:
        await close_connection()


if __name__ == "__main__":
    asyncio.run(main())
