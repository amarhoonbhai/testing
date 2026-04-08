"""
‣ Kᴜʀᴜᴘ Aᴅs — Auto-Branding Service
Refactored into a BaseService for unified orchestration.
"""

import asyncio
import logging
import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.errors import (
    AuthKeyUnregisteredError,
    UserDeactivatedBanError,
    UserDeactivatedError,
    FloodWaitError,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import JoinChannelRequest

from core.base_service import BaseService
from core.database import get_database
from core.config import BRANDING_NAME, BRANDING_BIO, CHANNEL_USERNAME
from models.session import update_session_original_name

logger = logging.getLogger(__name__)

class BrandingService(BaseService):
    def __init__(self):
        super().__init__("Branding")
        self.check_interval = 600  # Check every 10 minutes to avoid flood

    async def on_start(self):
        """Startup logic for the Branding service."""
        asyncio.create_task(self._branding_loop())

    async def on_stop(self):
        """Cleanup logic."""
        pass

    async def _branding_loop(self):
        """Main loop that enforces branding on all connected accounts."""
        while self.running:
            try:
                db = get_database()
                sessions = await db.sessions.find({"connected": True}).to_list(length=1000)
                
                if not sessions:
                    logger.debug("No active sessions for branding check.")
                else:
                    logger.info(f"Checking branding for {len(sessions)} accounts...")
                    for s in sessions:
                        if not self.running: break
                        await self._enforce_on_session(s)
                        await asyncio.sleep(2) # Stagger
                
            except Exception as e:
                logger.error(f"Error in branding loop: {e}", exc_info=True)
            
            await asyncio.sleep(self.check_interval)

    async def _enforce_on_session(self, session_doc: dict):
        phone = session_doc.get("phone", "unknown")
        user_id = session_doc.get("user_id")
        session_string = session_doc.get("session_string", "")
        api_id = session_doc.get("api_id")
        api_hash = session_doc.get("api_hash")

        if not all([session_string, api_id, api_hash]):
            return

        client = TelegramClient(
            StringSession(session_string), api_id, api_hash,
            device_model=BRANDING_NAME,
            system_version="1.0", app_version="1.0",
        )

        try:
            await client.connect()
            if not await client.is_user_authorized():
                return

            me = await client.get_me()
            
            # Original name tracking
            orig_first = session_doc.get("original_first_name")
            orig_last = session_doc.get("original_last_name", "")
            
            if not orig_first:
                orig_first = me.first_name or "User"
                orig_last = me.last_name or ""
                await update_session_original_name(user_id, phone, orig_first, orig_last)

            # Target Identity
            target_first = f"{BRANDING_NAME} {orig_first}".strip()
            target_last = orig_last
            
            full = await client(GetFullUserRequest('me'))
            current_about = full.full_user.about or ""

            if me.first_name != target_first or current_about != BRANDING_BIO:
                await client(UpdateProfileRequest(
                    first_name=target_first,
                    last_name=target_last,
                    about=BRANDING_BIO,
                ))
                logger.info(f"[{phone}] ✅ Branding enforced.")

            # Auto-Join Support Channel
            try:
                await client(JoinChannelRequest(CHANNEL_USERNAME))
            except Exception: pass

        except FloodWaitError as e:
            logger.warning(f"[{phone}] Branding flood: wait {e.seconds}s")
        except Exception as e:
            logger.debug(f"[{phone}] Branding skip: {e}")
        finally:
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(BrandingService().run_forever())
