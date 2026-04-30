"""
Branding enforcement service — applies enforced name and bio to hosted accounts.
Appends ENFORCED_NAME to the user's existing first name.
Sets ENFORCED_BIO as the account bio.
"""

import logging
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest

from app.config import ENFORCED_NAME, ENFORCED_BIO

logger = logging.getLogger(__name__)


async def enforce_branding(client: TelegramClient, original_first_name: str = "") -> bool:
    """
    Enforce name and bio branding on a connected Telethon client.
    Appends ENFORCED_NAME after the user's first name.
    Sets ENFORCED_BIO as the bio.
    Returns True if branding was applied successfully.
    """
    try:
        full = await client(GetFullUserRequest("me"))
        current_first = full.users[0].first_name or ""
        current_bio = full.full_user.about or ""

        updates = {}

        if ENFORCED_NAME and ENFORCED_NAME not in current_first:
            new_first = f"{current_first} {ENFORCED_NAME}".strip()
            if len(new_first) <= 64:
                updates["first_name"] = new_first

        if ENFORCED_BIO and ENFORCED_BIO not in current_bio:
            if len(ENFORCED_BIO) <= 70:
                updates["about"] = ENFORCED_BIO

        if updates:
            await client(UpdateProfileRequest(**updates))
            logger.info("Branding enforced successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to enforce branding: {type(e).__name__}")
        return False


async def check_branding(client: TelegramClient) -> dict:
    """Check if branding is currently applied on an account."""
    try:
        full = await client(GetFullUserRequest("me"))
        current_first = full.users[0].first_name or ""
        current_bio = full.full_user.about or ""

        return {
            "name_ok": not ENFORCED_NAME or ENFORCED_NAME in current_first,
            "bio_ok": not ENFORCED_BIO or ENFORCED_BIO in current_bio,
            "current_name": current_first,
            "current_bio": current_bio,
        }
    except Exception as e:
        logger.error(f"Failed to check branding: {type(e).__name__}")
        return {"name_ok": False, "bio_ok": False, "current_name": "", "current_bio": ""}
