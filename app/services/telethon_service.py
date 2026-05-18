"""
Telethon service — manages Telegram user account connections and messaging.

Handles:
- Sending login codes
- OTP verification
- 2FA password authentication
- Creating session strings
- Building clients from stored sessions
- Sending messages to groups/channels

SECURITY: Never logs phone numbers, OTPs, passwords, or session strings.
"""

import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    FloodWaitError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    PhoneNumberBannedError,
    PhoneNumberInvalidError,
    ApiIdInvalidError,
)
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest
from datetime import datetime

from app.config import API_ID, API_HASH

logger = logging.getLogger(__name__)


async def create_client(session_string: str = "") -> TelegramClient:
    """Create a Telethon client with the given session string."""
    client = TelegramClient(
        StringSession(session_string),
        API_ID,
        API_HASH,
        device_model="Group Broadcaster",
        system_version="1.0",
        app_version="2.0",
    )
    return client


async def send_login_code(phone: str) -> dict:
    """
    Send a Telegram login code to the given phone number.

    Returns dict with:
        - client: TelegramClient (connected, keep for sign_in)
        - phone_code_hash: str
        - success: bool
        - error: str (if failed)
    """
    client = await create_client()

    try:
        await client.connect()
        result = await client.send_code_request(phone)
        logger.info("Login code sent successfully")

        return {
            "client": client,
            "phone_code_hash": result.phone_code_hash,
            "success": True,
            "error": None,
        }

    except PhoneNumberInvalidError:
        await client.disconnect()
        return {
            "client": None,
            "phone_code_hash": None,
            "success": False,
            "error": "Invalid phone number format. Please check and try again.",
        }
    except PhoneNumberBannedError:
        await client.disconnect()
        return {
            "client": None,
            "phone_code_hash": None,
            "success": False,
            "error": "This phone number is banned by Telegram.",
        }
    except FloodWaitError as e:
        await client.disconnect()
        return {
            "client": None,
            "phone_code_hash": None,
            "success": False,
            "error": f"Too many attempts. Please wait {e.seconds} seconds.",
        }
    except ApiIdInvalidError:
        await client.disconnect()
        return {
            "client": None,
            "phone_code_hash": None,
            "success": False,
            "error": "API credentials are invalid. Contact support.",
        }
    except Exception as e:
        await client.disconnect()
        logger.error(f"Failed to send login code: {type(e).__name__}")
        return {
            "client": None,
            "phone_code_hash": None,
            "success": False,
            "error": f"An error occurred: {type(e).__name__}",
        }


async def verify_code(
    client: TelegramClient,
    phone: str,
    code: str,
    phone_code_hash: str,
) -> dict:
    """
    Verify the OTP code.

    Returns dict with:
        - session_string: str (if success)
        - needs_2fa: bool
        - success: bool
        - error: str (if failed)
    """
    try:
        await client.sign_in(
            phone=phone,
            code=code,
            phone_code_hash=phone_code_hash,
        )

        session_string = client.session.save()
        logger.info("Account authenticated successfully")

        return {
            "session_string": session_string,
            "needs_2fa": False,
            "success": True,
            "error": None,
        }

    except SessionPasswordNeededError:
        logger.info("2FA password required")
        return {
            "session_string": None,
            "needs_2fa": True,
            "success": False,
            "error": None,
        }
    except PhoneCodeInvalidError:
        return {
            "session_string": None,
            "needs_2fa": False,
            "success": False,
            "error": "Invalid OTP code. Please try again.",
        }
    except PhoneCodeExpiredError:
        return {
            "session_string": None,
            "needs_2fa": False,
            "success": False,
            "error": "OTP code has expired. Please start over.",
        }
    except FloodWaitError as e:
        return {
            "session_string": None,
            "needs_2fa": False,
            "success": False,
            "error": f"Too many attempts. Wait {e.seconds} seconds.",
        }
    except Exception as e:
        logger.error(f"OTP verification failed: {type(e).__name__}")
        return {
            "session_string": None,
            "needs_2fa": False,
            "success": False,
            "error": f"Verification failed: {type(e).__name__}",
        }


async def verify_2fa(client: TelegramClient, password: str) -> dict:
    """
    Verify 2FA password.

    Returns dict with:
        - session_string: str (if success)
        - success: bool
        - error: str (if failed)
    """
    try:
        await client.sign_in(password=password)

        session_string = client.session.save()
        logger.info("2FA authentication successful")

        return {
            "session_string": session_string,
            "success": True,
            "error": None,
        }

    except Exception as e:
        logger.error(f"2FA verification failed: {type(e).__name__}")
        return {
            "session_string": None,
            "success": False,
            "error": "Incorrect 2FA password. Please try again.",
        }


async def get_client_from_session(session_string: str) -> TelegramClient:
    """
    Create and connect a Telethon client from an existing session string.
    Caller is responsible for disconnecting when done.
    """
    client = await create_client(session_string)
    await client.connect()

    if not await client.is_user_authorized():
        await client.disconnect()
        raise ConnectionError("Session is no longer authorized")

    return client


async def send_message_to_entity(
    client: TelegramClient,
    entity,
    text: str = None,
    media_type: str = None,
    media_path: str = None,
) -> dict:
    """
    Send a message (text/photo/video) to a resolved entity.
    Returns a structured dictionary:
    { "success": bool, "target": str, "error_type": str, "error_message": str, "skipped": bool }
    """
    target = getattr(entity, 'username', None)
    if not target:
        target = str(getattr(entity, 'id', 'Unknown'))
    else:
        target = f"@{target}"

    try:
        if media_type == "photo" and media_path:
            await client.send_file(entity, media_path, caption=text or "")
        elif media_type == "video" and media_path:
            await client.send_file(entity, media_path, caption=text or "")
        elif text:
            await client.send_message(entity, text)
        else:
            return {"success": False, "target": target, "error_type": "ValueError", "error_message": "No message content to send", "skipped": False}

        return {"success": True, "target": target, "error_type": None, "error_message": None, "skipped": False}
    except Exception as e:
        # Re-raise so the engine can catch specific FloodWait or permissions
        # But we format the error safely
        raise e


async def enforce_or_remove_branding(client: TelegramClient, is_premium: bool):
    """Enforce branding for free users, remove for premium users."""
    try:
        me = await client.get_me()
        full = await client(GetFullUserRequest(me.id))
        about = full.full_user.about or ""
        first_name = me.first_name or ""
        last_name = me.last_name or ""

        from app.config import ENFORCED_BIO, ENFORCED_NAME_SUFFIX

        updated = False
        new_about = about
        new_last_name = last_name

        if not is_premium:
            if ENFORCED_BIO not in about:
                new_about = ENFORCED_BIO
                updated = True
            if ENFORCED_NAME_SUFFIX not in last_name:
                new_last_name = f"{last_name.replace(ENFORCED_NAME_SUFFIX, '').strip()} {ENFORCED_NAME_SUFFIX}".strip()
                updated = True
        else:
            if ENFORCED_BIO in about:
                new_about = about.replace(ENFORCED_BIO, "").strip()
                updated = True
            if ENFORCED_NAME_SUFFIX in last_name:
                new_last_name = last_name.replace(ENFORCED_NAME_SUFFIX, "").strip()
                updated = True

        if updated:
            await client(UpdateProfileRequest(
                about=new_about[:70],
                first_name=first_name,
                last_name=new_last_name[:64]
            ))
            logger.info(f"Profile branding updated for user {me.id} (Premium: {is_premium})")
    except Exception as e:
        logger.warning(f"Failed to update profile branding: {e}")


async def check_account_health(user_id: int, client: TelegramClient) -> dict:
    """Check account health, update DB, and return report."""
    from app.database.models import update_user

    score = 100
    details = []

    try:
        if not await client.is_user_authorized():
            score = 0
            details.append("⚠️ Session is unauthorized or expired.")
            status_str = "Session Expired (0%)"
        else:
            me = await client.get_me()
            if getattr(me, 'restricted', False):
                score -= 50
                details.append("⚠️ Account is restricted by Telegram.")
            if getattr(me, 'scam', False) or getattr(me, 'fake', False):
                score -= 30
                details.append("⚠️ Account is flagged as scam/fake.")
            if score == 100:
                details.append("✅ Account is fully active and unrestricted.")
                status_str = f"Excellent ({score}%)"
            else:
                status_str = f"Restricted ({score}%)"

    except Exception as e:
        score = 0
        details.append(f"❌ Error checking health: {type(e).__name__}")
        status_str = "Error (0%)"

    await update_user(user_id, health_status=status_str, last_health_check=datetime.utcnow())
    return {"score": score, "status": status_str, "details": "\n".join(details)}


async def send_message_to_saved_messages(client: TelegramClient, message: dict) -> dict:
    """Send broadcast message to user's Saved Messages ('me')."""
    try:
        # Resolve 'me' entity
        me = await client.get_entity("me")
        return await send_message_to_entity(
            client, me,
            text=message.get("text"),
            media_type=message.get("media_type"),
            media_path=message.get("media_path")
        )
    except Exception as e:
        logger.error(f"Failed to send to Saved Messages: {e}")
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e)}
