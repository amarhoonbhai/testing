"""
Auto-Branding Service — KURUP ADS

Runs a background loop every 30 seconds.
For every connected/enabled session in MongoDB:
  - Connects via Telethon using the stored session string
  - Checks current first_name and bio
  - If they don't match BRANDING_NAME / BRANDING_BIO, updates them
  - Disconnects after update

Run as a standalone process:
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
    FloodWaitError,
)

from core.logger import setup_service_logging
from core.database import init_database, close_connection, get_database
from core.config import BRANDING_NAME, BRANDING_BIO

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 30  # seconds between full checks


async def get_all_enabled_sessions() -> list:
    """Fetch all enabled sessions from MongoDB."""
    db = get_database()
    cursor = db.sessions.find({"connected": True})
    return await cursor.to_list(length=10000)


async def apply_branding_to_session(session_doc: dict) -> bool:
    """
    Connect to a session and set first_name / bio to match KURUP ADS branding.
    Returns True if updated, False if already branded or failed.
    """
    phone = session_doc.get("phone", "unknown")
    user_id = session_doc.get("user_id")
    session_string = session_doc.get("session_string", "")
    api_id = session_doc.get("api_id")
    api_hash = session_doc.get("api_hash")

    if not session_string or not api_id or not api_hash:
        logger.warning(f"[{phone}] Missing session data — skipping")
        return False

    client = TelegramClient(
        StringSession(session_string),
        api_id,
        api_hash,
        device_model="KURUP ADS Branding",
        system_version="1.0",
        app_version="1.0",
    )

    try:
        await client.connect()

        if not await client.is_user_authorized():
            logger.warning(f"[{phone}] Session unauthorized — skipping")
            return False

        # Get current profile
        me = await client.get_me()
        current_name = me.first_name or ""
        current_bio = ""

        try:
            from telethon.tl.functions.users import GetFullUserRequest
            full = await client(GetFullUserRequest(me))
            current_bio = full.full_user.about or ""
        except Exception:
            pass

        # Check if already branded
        name_ok = current_name == BRANDING_NAME
        bio_ok = current_bio == BRANDING_BIO

        if name_ok and bio_ok:
            logger.debug(f"[{phone}] Already branded — no update needed")
            return False

        # Apply branding
        await client(UpdateProfileRequest(
            first_name=BRANDING_NAME,
            about=BRANDING_BIO,
        ))
        logger.info(f"[{phone}] ✅ Branding applied: name='{BRANDING_NAME}'")
        return True

    except FloodWaitError as e:
        logger.warning(f"[{phone}] FloodWait {e.seconds}s — skipping this round")
        return False
    except (AuthKeyUnregisteredError, UserDeactivatedBanError) as e:
        logger.warning(f"[{phone}] Account banned/deactivated: {e}")
        # Mark session as disconnected in DB
        db = get_database()
        await db.sessions.update_one(
            {"user_id": user_id, "phone": phone},
            {"$set": {"connected": False, "disabled_reason": str(e)}}
        )
        return False
    except Exception as e:
        logger.error(f"[{phone}] Error during branding: {e}")
        return False
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def branding_loop():
    """Main loop — runs every 30 seconds."""
    logger.info("=" * 50)
    logger.info("KURUP ADS Auto-Branding Service Started")
    logger.info(f"Brand Name : {BRANDING_NAME}")
    logger.info(f"Brand Bio  : {BRANDING_BIO}")
    logger.info(f"Interval   : {CHECK_INTERVAL}s")
    logger.info("=" * 50)

    while True:
        try:
            sessions = await get_all_enabled_sessions()
            total = len(sessions)
            updated = 0

            if total == 0:
                logger.info("No connected sessions found — waiting...")
            else:
                logger.info(f"Checking {total} session(s) for branding...")
                for session_doc in sessions:
                    result = await apply_branding_to_session(session_doc)
                    if result:
                        updated += 1
                    # Small delay between accounts to avoid flood
                    await asyncio.sleep(1)

                logger.info(f"Branding pass complete — {updated}/{total} updated")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Branding loop error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


async def main():
    setup_service_logging("branding")
    await init_database()

    loop = asyncio.get_running_loop()

    # Graceful shutdown on Unix
    if platform.system() != "Windows":
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda: task.cancel())
            except NotImplementedError:
                pass

    task = asyncio.create_task(branding_loop())

    try:
        await task
    except asyncio.CancelledError:
        logger.info("Branding service shutting down...")
    finally:
        await close_connection()


if __name__ == "__main__":
    asyncio.run(main())
