"""
Auto-Branding Service — ‣ Kᴜʀᴜᴘ Aᴅs

Enforced branding: runs every 30 seconds and ALWAYS sets first_name + bio
on every connected session — no equality check, always overwrites.

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
    UserDeactivatedError,
    FloodWaitError,
)

from core.logger import setup_service_logging
from core.database import init_database, close_connection, get_database
from core.config import BRANDING_NAME, BRANDING_BIO

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 30  # seconds between full passes


async def get_all_enabled_sessions() -> list:
    """Fetch all enabled sessions from MongoDB."""
    db = get_database()
    cursor = db.sessions.find({"connected": True})
    return await cursor.to_list(length=10000)


async def enforce_branding(session_doc: dict) -> str:
    """
    Always force-update first_name and bio to KURUP ADS branding.
    Returns: 'updated' | 'flood' | 'banned' | 'error'
    """
    phone = session_doc.get("phone", "unknown")
    user_id = session_doc.get("user_id")
    session_string = session_doc.get("session_string", "")
    api_id = session_doc.get("api_id")
    api_hash = session_doc.get("api_hash")

    if not session_string or not api_id or not api_hash:
        logger.warning(f"[{phone}] Missing session data — skipping")
        return "error"

    client = TelegramClient(
        StringSession(session_string),
        api_id,
        api_hash,
        device_model="‣ Kᴜʀᴜᴘ Aᴅs",
        system_version="1.0",
        app_version="1.0",
    )

    try:
        await client.connect()

        if not await client.is_user_authorized():
            logger.warning(f"[{phone}] Session unauthorized — marking disabled")
            db = get_database()
            await db.sessions.update_one(
                {"user_id": user_id, "phone": phone},
                {"$set": {"connected": False, "disabled_reason": "unauthorized"}}
            )
            return "banned"

        # ─── ALWAYS force-set name + bio (no equality check) ───
        await client(UpdateProfileRequest(
            first_name=BRANDING_NAME,
            about=BRANDING_BIO,
        ))
        logger.info(f"[{phone}] ✅ Branding enforced")
        return "updated"

    except FloodWaitError as e:
        logger.warning(f"[{phone}] FloodWait {e.seconds}s — will retry next pass")
        return "flood"

    except (AuthKeyUnregisteredError, UserDeactivatedBanError, UserDeactivatedError) as e:
        logger.warning(f"[{phone}] Account banned/deactivated: {e}")
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
    """Main enforced-branding loop — runs every 30 seconds."""
    logger.info("=" * 50)
    logger.info("‣ Kᴜʀᴜᴘ Aᴅs  Auto-Branding Service (ENFORCED)")
    logger.info(f"Brand Name : {BRANDING_NAME}")
    logger.info(f"Brand Bio  : {BRANDING_BIO}")
    logger.info(f"Interval   : {CHECK_INTERVAL}s  |  Mode: ALWAYS UPDATE")
    logger.info("=" * 50)

    while True:
        try:
            sessions = await get_all_enabled_sessions()
            total = len(sessions)

            if total == 0:
                logger.info("No connected sessions — waiting...")
            else:
                logger.info(f"Enforcing branding on {total} session(s)...")
                counts = {"updated": 0, "flood": 0, "banned": 0, "error": 0}

                for session_doc in sessions:
                    result = await enforce_branding(session_doc)
                    counts[result] = counts.get(result, 0) + 1
                    await asyncio.sleep(2)  # spacing to avoid floods

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

    if platform.system() != "Windows":
        task = asyncio.create_task(branding_loop())
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, task.cancel)
            except NotImplementedError:
                pass
    else:
        task = asyncio.create_task(branding_loop())

    try:
        await task
    except asyncio.CancelledError:
        logger.info("Branding service shutting down...")
    finally:
        await close_connection()


if __name__ == "__main__":
    asyncio.run(main())
