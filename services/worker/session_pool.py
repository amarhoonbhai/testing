"""
Session Pool for handling multiple TelegramClient instances.
Ensures clients are connected, authorized, and cached for reuse.
"""

import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    AuthKeyUnregisteredError,
    UserDeactivatedBanError,
    UserDeactivatedError
)
from core.database import get_database

logger = logging.getLogger(__name__)

class SessionManager:
    """
    V5 Elite Session Manager.
    Handles TelegramClient lifecycle, proactive health checks, and auto-recovery.
    """
    def __init__(self):
        self._clients = {} # (user_id, phone) -> TelegramClient
        self._lock = asyncio.Lock()
        self._health_task = None

    async def start(self):
        """Initialize the manager and start background health monitoring."""
        logger.info("🛡️ SessionManager: Initializing Elite Pool...")
        self._health_task = asyncio.create_task(self._health_check_loop())

    async def stop(self):
        """Gracefully disconnect all active clients."""
        if self._health_task:
            self._health_task.cancel()
            
        async with self._lock:
            for key, client in self._clients.items():
                try:
                    await client.disconnect()
                    logger.info(f"[{key[1]}] Disconnected from pool")
                except: pass
            self._clients.clear()
        logger.info("🛡️ SessionManager: Pool shut down.")

    async def acquire(self, user_id: int, phone: str) -> TelegramClient:
        """Get a connected and authorized TelegramClient."""
        key = (user_id, phone)
        
        async with self._lock:
            if key in self._clients:
                client = self._clients[key]
                if client.is_connected() and await client.is_user_authorized():
                    return client
                # Stale client — cleaning up
                try: await client.disconnect()
                except: pass
                del self._clients[key]

            # Re-fetch session from DB
            db = get_database()
            doc = await db.sessions.find_one({"user_id": user_id, "phone": phone, "connected": True})
            if not doc:
                raise ValueError(f"Account {phone} not found or disconnected in DB")

            client = TelegramClient(
                StringSession(doc["session_string"]),
                doc["api_id"],
                doc["api_hash"],
                device_model="KURUP V5 ELITE",
                system_version="Windows 10",
                app_version="5.0",
            )

            try:
                await client.connect()
                if not await client.is_user_authorized():
                    await self._mark_unauthorized(user_id, phone, "Session Revoked")
                    raise ValueError(f"Account {phone} unauthorized")
                
                # Attach metadata
                client.user_id = user_id
                client.phone = phone
                client._last_check = asyncio.get_event_loop().time()
                
                # Start the background update receiver loop
                await client.start()
                
                self._clients[key] = client
                return client
                
            except (AuthKeyUnregisteredError, UserDeactivatedBanError, UserDeactivatedError) as e:
                await self._mark_unauthorized(user_id, phone, str(e))
                raise
            except Exception as e:
                logger.error(f"[{phone}] Error during connection: {e}")
                raise

    async def _health_check_loop(self):
        """Background loop to periodically verify session health."""
        while True:
            await asyncio.sleep(300) # Every 5 minutes
            async with self._lock:
                to_check = list(self._clients.items())
            
            for key, client in to_check:
                try:
                    # Ping Telegram to keep connection alive
                    await client.get_me()
                    client._last_check = asyncio.get_event_loop().time()
                except Exception as e:
                    logger.warning(f"[{key[1]}] Health check failed: {e}. Dropping from pool.")
                    async with self._lock:
                        if key in self._clients:
                            try: await self._clients[key].disconnect()
                            except: pass
                            del self._clients[key]

    async def _mark_unauthorized(self, user_id: int, phone: str, reason: str):
        db = get_database()
        await db.sessions.update_one(
            {"user_id": user_id, "phone": phone},
            {"$set": {"connected": False, "disabled_reason": reason}}
        )
        logger.error(f"[{phone}] Marked as DISCONNECTED: {reason}")

# Backwards compatibility alias
SessionPool = SessionManager
