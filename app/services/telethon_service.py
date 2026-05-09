"""
Telethon service — manages Telegram user account connections.

Handles:
- Sending login codes
- OTP verification
- 2FA password authentication
- Creating session strings
- Building clients from stored sessions

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

from app.config import API_ID, API_HASH

logger = logging.getLogger(__name__)


async def create_client(session_string: str = "") -> TelegramClient:
    """
    Create a Telethon client with the given session string.
    If empty, creates a new session.
    """
    client = TelegramClient(
        StringSession(session_string),
        API_ID,
        API_HASH,
        device_model="Kurup Ads Bot",
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


async def get_account_dialogs(client: TelegramClient) -> list[dict]:
    """
    Get all dialogs (chats/groups/channels) for a connected client.
    Only returns groups and channels where the user can post.
    """
    dialogs = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                dialogs.append({
                    "id": dialog.id,
                    "title": dialog.title,
                    "is_group": dialog.is_group,
                    "is_channel": dialog.is_channel,
                })
    except Exception as e:
        logger.error(f"Failed to fetch dialogs: {type(e).__name__}")

    return dialogs


async def expand_folder_link(client: TelegramClient, slug: str) -> list[dict]:
    """
    Expand a Telegram folder link (t.me/addlist/slug) into a list of group data.
    Returns list of {"link": str, "id": int}
    """
    from telethon.tl.functions.chatlists import GetChatlistInviteRequest
    from telethon.tl.types import Chat, Channel
    
    results = []
    try:
        # Get the invite info
        invite = await client(GetChatlistInviteRequest(slug))
        
        # Peer entities are in invite.peers
        for peer in invite.peers:
            if isinstance(peer, (Chat, Channel)):
                data = {"id": peer.id}
                if getattr(peer, "username", None):
                    data["link"] = f"https://t.me/{peer.username}"
                else:
                    # Private group: t.me/c/id
                    data["link"] = f"https://t.me/c/{peer.id}"
                results.append(data)
                    
    except Exception as e:
        logger.error(f"Failed to expand folder {slug}: {e}")
        
    return results
