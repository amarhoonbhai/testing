"""
‣ Kᴜʀᴜᴘ Aᴅs — Auto-Branding Service

Every 30 seconds, for every connected session:
  - Keeps the account's original first name
  - Sets last_name  = "‣ Kᴜʀᴜᴘ Aᴅs"
  - Sets bio        = BRANDING_BIO

Always force-updates (no equality skip) to ensure enforcement.

Run:
    python -m services.branding.branding
"""

import asyncio
import logging
import signal
import platform

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.errors import (
    AuthKeyUnregisteredError,
    UserDeactivatedBanError,
    UserDeactivatedError,
    FloodWaitError,
    PeerIdInvalidError,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import JoinChannelRequest

from core.logger import setup_service_logging
from core.database import init_database, close_connection, get_database
from core.config import BRANDING_NAME, BRANDING_BIO
from models.session import update_session_original_name

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 30  # seconds


async def get_all_enabled_sessions() -> list:
    db = get_database()
    return await db.sessions.find({"connected": True}).to_list(length=10000)


async def enforce_branding(session_doc: dict) -> str:
    """
    Enforce branding on one account:
      - Preserve original first_name
      - Set last_name = BRANDING_NAME  (e.g. "‣ Kᴜʀᴜᴘ Aᴅs")
      - Set bio       = BRANDING_BIO
    Returns: 'updated' | 'flood' | 'banned' | 'error'
    """
    phone = session_doc.get("phone", "unknown")
    user_id = session_doc.get("user_id")
    session_string = session_doc.get("session_string", "")
    api_id = session_doc.get("api_id")
    api_hash = session_doc.get("api_hash")

    if not session_string or not api_id or not api_hash:
        logger.warning(f"[{phone}] Missing credentials — skipping")
        return "error"

    client = TelegramClient(
        StringSession(session_string), api_id, api_hash,
        device_model=BRANDING_NAME,
        system_version="1.0", app_version="1.0",
    )

    try:
        await client.connect()

        if not await client.is_user_authorized():
            logger.warning(f"[{phone}] Unauthorized — disabling")
            db = get_database()
            await db.sessions.update_one(
                {"user_id": user_id, "phone": phone},
                {"$set": {"connected": False, "disabled_reason": "unauthorized"}}
            )
            return "banned"

        # Get current info
        me = await client.get_me()
        
        # Check if we have original name stored in doc
        orig_first = session_doc.get("original_first_name")
        orig_last = session_doc.get("original_last_name", "")
        
        if not orig_first:
            # First time seeing this account — store its current name as original
            orig_first = me.first_name or "User"
            orig_last = me.last_name or ""
            await update_session_original_name(user_id, phone, orig_first, orig_last)
            logger.info(f"[{phone}] Stored original name: {orig_first} {orig_last}")

        # Enforce name: prefix + original name
        # Target: "‣ Kᴜʀᴜᴘ Aᴅs John Doe"
        target_first = f"{BRANDING_NAME} {orig_first}".strip()
        target_last = orig_last if orig_last else ""
        
        current_first = me.first_name or ""
        current_last = me.last_name or ""
        
        # Get bio separately
        full = await client(GetFullUserRequest('me'))
        current_about = full.full_user.about or ""

        needs_update = False
        if current_first != target_first or current_last != target_last or current_about != BRANDING_BIO:
            needs_update = True

        if needs_update:
            await client(UpdateProfileRequest(
                first_name=target_first,
                last_name=target_last,
                about=BRANDING_BIO,
            ))
            logger.info(f"[{phone}] ✅ Name/Bio Updated -> {target_first} {target_last}")

        # Enforce Join @adinify
        try:
            await client(JoinChannelRequest('adinify'))
            # logger.info(f"[{phone}] Joined @adinify (Enforced)")
        except Exception as je:
            if "FloodWait" in str(je):
                pass # Skip for now
            else:
                logger.warning(f"[{phone}] Join @adinify failed: {je}")

        return "updated"

    except FloodWaitError as e:
        logger.warning(f"[{phone}] FloodWait {e.seconds}s")
        return "flood"

    except (AuthKeyUnregisteredError, UserDeactivatedBanError, UserDeactivatedError) as e:
        logger.warning(f"[{phone}] Account banned: {e}")
        db = get_database()
        await db.sessions.update_one(
            {"user_id": user_id, "phone": phone},
            {"$set": {"connected": False, "disabled_reason": str(e)}}
        )
        return "banned"

    except Exception as e:
        logger.error(f"[{phone}] Branding error: {e}")
        return "error"

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def branding_loop():
    logger.info("=" * 50)
    logger.info("‣ Kᴜʀᴜᴘ Aᴅs  Auto-Branding (ENFORCED)")
    logger.info(f"Last Name : {BRANDING_NAME}")
    logger.info(f"Bio       : {BRANDING_BIO}")
    logger.info(f"Interval  : {CHECK_INTERVAL}s  |  Mode: ALWAYS UPDATE")
    logger.info("=" * 50)

    while True:
        try:
            sessions = await get_all_enabled_sessions()
            total = len(sessions)

            if not sessions:
                logger.info("No connected sessions — waiting...")
            else:
                logger.info(f"Enforcing branding on {total} session(s)...")
                counts = {"updated": 0, "flood": 0, "banned": 0, "error": 0}

                for s in sessions:
                    result = await enforce_branding(s)
                    counts[result] = counts.get(result, 0) + 1
                    await asyncio.sleep(2)

                logger.info(
                    f"Pass done — updated:{counts['updated']} "
                    f"flood:{counts['flood']} banned:{counts['banned']} "
                    f"error:{counts['error']}"
                )

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Branding loop error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


async def main():
    setup_service_logging("branding")
    await init_database()

    loop = asyncio.get_running_loop()
    task = asyncio.create_task(branding_loop())

    if platform.system() != "Windows":
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, task.cancel)
            except NotImplementedError:
                pass

    try:
        await task
    except asyncio.CancelledError:
        logger.info("Branding service shutting down...")
    finally:
        await close_connection()


if __name__ == "__main__":
    asyncio.run(main())
