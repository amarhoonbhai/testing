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

class SessionPool:
    def __init__(self):
        self._clients = {} # (user_id, phone) -> TelegramClient
        self._lock = asyncio.Lock()

    async def start(self):
        """Startup cleanup or pre-loading if needed."""
        logger.info("Session Pool initialized")

    async def stop(self):
        """Disconnect all active clients."""
        async with self._lock:
            for client in self._clients.values():
                try:
                    await client.disconnect()
                except Exception:
                    pass
            self._clients.clear()
            logger.info("Session Pool stopped")

    async def acquire(self, user_id: int, phone: str) -> TelegramClient:
        """Get a connected and authorized TelegramClient for the given account."""
        key = (user_id, phone)
        
        async with self._lock:
            if key in self._clients:
                client = self._clients[key]
                if client.is_connected() and await client.is_user_authorized():
                    return client
                # Client disconnected or unauthorized — try reconnecting/recreating
                try:
                    await client.disconnect()
                except Exception:
                    pass
                del self._clients[key]

            # Create new client
            db = get_database()
            session_doc = await db.sessions.find_one({"user_id": user_id, "phone": phone, "connected": True})
            if not session_doc:
                raise ValueError(f"No connected session found for {phone}")

            session_string = session_doc.get("session_string")
            api_id = session_doc.get("api_id")
            api_hash = session_doc.get("api_hash")

            if not session_string or not api_id or not api_hash:
                raise ValueError(f"Missing API credentials for {phone}")

            client = TelegramClient(
                StringSession(session_string),
                api_id,
                api_hash,
                device_model="K\u0280\u1d1c\u1d18 A\u1d05s",
                system_version="1.0",
                app_version="3.3",
            )

            try:
                await client.connect()
                if not await client.is_user_authorized():
                    # Account likely banned or session revoked
                    await db.sessions.update_one(
                        {"user_id": user_id, "phone": phone},
                        {"$set": {"connected": False, "disabled_reason": "session_revoked"}}
                    )
                    raise ValueError(f"Account {phone} is unauthorized")
                
                client.user_id = user_id
                client.phone = phone
                
                self._clients[key] = client
                return client

            except (AuthKeyUnregisteredError, UserDeactivatedBanError, UserDeactivatedError) as e:
                logger.error(f"Account {phone} is deactivated or banned: {e}")
                await db.sessions.update_one(
                    {"user_id": user_id, "phone": phone},
                    {"$set": {"connected": False, "disabled_reason": str(e)}}
                )
                raise

            except Exception as e:
                logger.error(f"Error acquiring client for {phone}: {e}")
                raise

    def release(self, user_id: int, phone: str):
        """Keep the client connected in the pool (no-op unless we want to disconnect)."""
        pass
