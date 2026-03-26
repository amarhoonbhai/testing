"""
‣ Kᴜʀᴜᴘ Aᴅs — Scheduler Service

Monitors every connected session's Saved Messages for new messages.
When a user sends a message to their Saved Messages, this service:
  1. Detects the new message via Telethon
  2. Resolves all the user's groups (including folder groups)
  3. Creates a job in scheduled_jobs for the sender to process

Respects the user's interval setting — won't create a job if one was
created less than interval_min minutes ago for the same account.

Run as a standalone process:
    python -m services.scheduler.scheduler
"""

import asyncio
import logging
import signal
import platform
from datetime import datetime, timedelta
from typing import Optional

from telethon import TelegramClient, events
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

POLL_INTERVAL = 15  # seconds between checking for new sessions to add


# ─── Helpers ────────────────────────────────────────────────────────────────

async def get_all_connected_sessions() -> list:
    db = get_database()
    cursor = db.sessions.find({"connected": True})
    return await cursor.to_list(length=10000)


async def get_user_config(user_id: int) -> dict:
    db = get_database()
    return await db.user_configs.find_one({"user_id": user_id}) or {}


async def get_user_groups(user_id: int) -> list:
    db = get_database()
    cursor = db.groups.find({"user_id": user_id, "enabled": True})
    return await cursor.to_list(length=10000)


async def get_last_job_time(user_id: int, phone: str) -> Optional[datetime]:
    db = get_database()
    doc = await db.scheduled_jobs.find_one(
        {"user_id": user_id, "phone": phone},
        sort=[("created_at", -1)]
    )
    return doc.get("created_at") if doc else None


async def create_job(user_id: int, phone: str, message_id: int, groups: list, copy_mode: bool):
    from models.job import create_job as _create_job
    await _create_job(
        user_id=user_id,
        phone=phone,
        message_id=message_id,
        groups=groups,
        copy_mode=copy_mode,
    )


async def resolve_folder_groups(client: TelegramClient, title: str) -> list:
    """
    Resolve a folder link stored as '[Folder] <hash>' to actual chat IDs
    by downloading all dialogs that belong to that folder filter.
    """
    try:
        result = await client(GetDialogFiltersRequest())
        folder_peers = []

        for f in result.filters:
            if not hasattr(f, 'include_peers'):
                continue
            for peer in f.include_peers:
                try:
                    entity = await client.get_entity(peer)
                    folder_peers.append(entity.id)
                except Exception:
                    pass

        if folder_peers:
            logger.info(f"Resolved folder to {len(folder_peers)} groups")
            return folder_peers

    except Exception as e:
        logger.warning(f"Folder resolution error: {e}")

    # Fallback: collect all group dialogs
    try:
        peers = []
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                peers.append(dialog.id)
        return peers
    except Exception as e:
        logger.warning(f"Dialog fallback error: {e}")
        return []


async def resolve_groups_for_client(client: TelegramClient, raw_groups: list) -> list:
    """
    Given the list of group docs from DB, return actual chat IDs.
    Handles:
      - Negative hash IDs (slug-based): try to resolve from dialogs
      - [Folder] groups: expand to all folder peers
      - Raw numeric IDs: use directly
    """
    resolved = []
    needs_dialog_map = []

    for g in raw_groups:
        chat_id = g.get("chat_id")
        title = g.get("chat_title", "")

        if title.startswith("[Folder]"):
            peers = await resolve_folder_groups(client, title)
            resolved.extend(peers)
        elif title.startswith("[Private]"):
            # Private invite link — stored with hash-based ID
            # Try to use the stored chat_id directly (may work if bot joined)
            if chat_id:
                resolved.append(chat_id)
        else:
            # Public group or raw numeric ID
            if chat_id and abs(chat_id) > 1_000_000_000:
                # Likely a real Telegram ID
                resolved.append(chat_id)
            else:
                # Slug-based hash — need to look up from dialogs
                needs_dialog_map.append(g)

    # For slug-based hash IDs, try matching against dialogs
    if needs_dialog_map:
        try:
            dialog_map = {}
            async for dialog in client.iter_dialogs():
                dialog_map[dialog.id] = dialog
                if dialog.name:
                    dialog_map[dialog.name.lower()] = dialog

            for g in needs_dialog_map:
                slug = g.get("chat_title", "")
                chat_id = g.get("chat_id")
                # Try matching by username
                dlg = dialog_map.get(slug.lower())
                if dlg:
                    resolved.append(dlg.id)
                    # Update DB with real chat_id
                    db = get_database()
                    await db.groups.update_one(
                        {"user_id": g["user_id"], "chat_id": chat_id},
                        {"$set": {"chat_id": dlg.id}}
                    )
                elif chat_id:
                    resolved.append(chat_id)  # use stored hash as fallback
        except Exception as e:
            logger.warning(f"Dialog resolution error: {e}")
            for g in needs_dialog_map:
                if g.get("chat_id"):
                    resolved.append(g["chat_id"])

    return list(set(resolved))  # deduplicate


# ─── Per-Session Listener ────────────────────────────────────────────────────

class SessionListener:
    """Manages a single Telethon client that listens for Saved Messages."""

    def __init__(self, session_doc: dict):
        self.user_id = session_doc["user_id"]
        self.phone = session_doc["phone"]
        self.session_string = session_doc["session_string"]
        self.api_id = session_doc["api_id"]
        self.api_hash = session_doc["api_hash"]
        self.client: Optional[TelegramClient] = None
        self.running = False

    async def start(self):
        self.client = TelegramClient(
            StringSession(self.session_string),
            self.api_id,
            self.api_hash,
            device_model="‣ Kᴜʀᴜᴘ Aᴅs Listener",
            system_version="1.0",
            app_version="1.0",
        )

        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                logger.warning(f"[{self.phone}] Unauthorized — skipping listener")
                await self.client.disconnect()
                return False
        except Exception as e:
            logger.error(f"[{self.phone}] Connect error: {e}")
            return False

        @self.client.on(events.NewMessage(from_users="me", pattern=None))
        async def _on_saved_message(event):
            """Triggered when user sends a message to their own Saved Messages."""
            try:
                # Only respond to messages in self-chat (Saved Messages)
                if event.chat_id != event.sender_id:
                    return

                msg_id = event.id
                logger.info(f"[{self.phone}] 📩 New Saved Message #{msg_id} — scheduling send")

                # Check interval
                config = await get_user_config(self.user_id)
                interval = max(
                    config.get("interval_min", DEFAULT_INTERVAL_MINUTES),
                    MIN_INTERVAL_MINUTES
                )
                copy_mode = config.get("copy_mode", False)

                last_job = await get_last_job_time(self.user_id, self.phone)
                if last_job:
                    elapsed = (datetime.utcnow() - last_job).total_seconds() / 60
                    if elapsed < interval:
                        wait_mins = round(interval - elapsed, 1)
                        logger.info(f"[{self.phone}] Interval not reached, {wait_mins}m remaining — skipping")
                        return

                # Get and resolve groups
                raw_groups = await get_user_groups(self.user_id)
                if not raw_groups:
                    logger.info(f"[{self.phone}] No groups configured — nothing to send")
                    return

                group_ids = await resolve_groups_for_client(self.client, raw_groups)
                if not group_ids:
                    logger.warning(f"[{self.phone}] All groups resolved to empty — skipping")
                    return

                # Create job
                await create_job(
                    user_id=self.user_id,
                    phone=self.phone,
                    message_id=msg_id,
                    groups=group_ids,
                    copy_mode=copy_mode,
                )
                logger.info(f"[{self.phone}] ✅ Job created for {len(group_ids)} groups (msg #{msg_id})")

            except Exception as e:
                logger.error(f"[{self.phone}] Event handler error: {e}")

        self.running = True
        logger.info(f"[{self.phone}] 🎧 Listener active — watching Saved Messages")
        return True

    async def run_until_disconnected(self):
        if self.client:
            await self.client.run_until_disconnected()

    async def stop(self):
        self.running = False
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass


# ─── Scheduler Manager ───────────────────────────────────────────────────────

class SchedulerManager:
    """Maintains listeners for all connected sessions."""

    def __init__(self):
        self._listeners: dict[str, SessionListener] = {}  # key: "user_id:phone"
        self._running = False

    async def start(self):
        setup_service_logging("scheduler")
        await init_database()
        self._running = True

        logger.info("=" * 50)
        logger.info("‣ Kᴜʀᴜᴘ Aᴅs  Scheduler Service Started")
        logger.info("=" * 50)

        # Initial load
        await self._sync_sessions()

        # Periodic sync to pick up new sessions
        while self._running:
            await asyncio.sleep(POLL_INTERVAL)
            await self._sync_sessions()

    async def _sync_sessions(self):
        """Add listeners for new sessions, remove for disconnected ones."""
        sessions = await get_all_connected_sessions()
        active_keys = set()

        for s in sessions:
            user_id = s.get("user_id")
            phone = s.get("phone")
            api_id = s.get("api_id")
            api_hash = s.get("api_hash")
            session_string = s.get("session_string", "")

            if not all([user_id, phone, api_id, api_hash, session_string]):
                continue

            key = f"{user_id}:{phone}"
            active_keys.add(key)

            if key not in self._listeners:
                listener = SessionListener(s)
                ok = await listener.start()
                if ok:
                    self._listeners[key] = listener
                    asyncio.create_task(listener.run_until_disconnected())

        # Remove stale listeners
        for key in list(self._listeners.keys()):
            if key not in active_keys:
                await self._listeners[key].stop()
                del self._listeners[key]
                logger.info(f"Removed listener for {key}")

        logger.debug(f"Active listeners: {len(self._listeners)}")

    async def stop(self):
        self._running = False
        for listener in self._listeners.values():
            await listener.stop()
        await close_connection()
        logger.info("Scheduler stopped")


# ─── Entry Point ─────────────────────────────────────────────────────────────

async def main():
    manager = SchedulerManager()

    if platform.system() != "Windows":
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(manager.stop()))
            except NotImplementedError:
                pass

    try:
        await manager.start()
    except asyncio.CancelledError:
        pass
    finally:
        await manager.stop()


if __name__ == "__main__":
    asyncio.run(main())
