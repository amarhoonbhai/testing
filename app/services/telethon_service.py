"""
Telethon service — manages Telegram user account connections and messaging.

Handles:
- Sending login codes
- OTP verification
- 2FA password authentication
- Creating session strings
- Building clients from stored sessions
- Saved Messages Auto-Forwarding (Albums & Media Groups)
- Profile Branding Enforcement & Instant Restoration
- Deep Account Health Diagnostics

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


async def create_client(session_string: str = "", user_id: int | None = None) -> TelegramClient:
    """Create a Telethon client with the given session string."""
    api_id = API_ID
    api_hash = API_HASH
    device_model = "Group Broadcaster SaaS"
    system_version = "1.0"
    app_version = "3.0"

    if user_id is not None:
        from app.database.models import get_user, update_user, generate_random_device
        user = await get_user(user_id)
        if user:
            # Custom API credentials
            custom_id = user.get("custom_api_id")
            custom_hash = user.get("custom_api_hash")
            if custom_id and custom_hash:
                try:
                    api_id = int(custom_id)
                    api_hash = str(custom_hash).strip()
                except ValueError:
                    logger.warning(f"Invalid custom API ID format for user {user_id}: {custom_id}")

            # Rotated/persistent device configuration
            u_device = user.get("device_model")
            u_system = user.get("system_version")
            u_app = user.get("app_version")
            if not u_device or not u_system or not u_app:
                # Generate, persist, and use
                dev = generate_random_device()
                device_model = dev["device_model"]
                system_version = dev["system_version"]
                app_version = dev["app_version"]
                await update_user(
                    user_id,
                    device_model=device_model,
                    system_version=system_version,
                    app_version=app_version
                )
            else:
                device_model = u_device
                system_version = u_system
                app_version = u_app

    client = TelegramClient(
        StringSession(session_string),
        api_id,
        api_hash,
        device_model=device_model,
        system_version=system_version,
        app_version=app_version,
    )
    return client



async def send_login_code(phone: str, user_id: int) -> dict:
    """
    Send a Telegram login code to the given phone number.

    Returns dict with:
        - client: TelegramClient (connected, keep for sign_in)
        - phone_code_hash: str
        - success: bool
        - error: str (if failed)
    """
    client = await create_client(user_id=user_id)


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
        from app.database.models import get_user
        user = await get_user(user_id) if user_id else None
        if user and user.get("custom_api_id") and user.get("custom_api_hash"):
            err_msg = "Your custom API credentials (API ID / API Hash) are invalid. Please check them under Custom API Settings or clear them to use defaults."
        else:
            err_msg = "API credentials are invalid. Contact support."
        return {
            "client": None,
            "phone_code_hash": None,
            "success": False,
            "error": err_msg,
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


async def get_client_from_session(session_string: str, user_id: int | None = None) -> TelegramClient:
    """
    Create and connect a Telethon client from an existing session string.
    Caller is responsible for disconnecting when done.
    """
    client = await create_client(session_string, user_id=user_id)

    await client.connect()

    if not await client.is_user_authorized():
        await client.disconnect()
        raise ConnectionError("Session is no longer authorized")

    return client


async def forward_saved_messages_to_entity(client: TelegramClient, entity) -> dict:
    """
    Fetch all messages from user's Saved Messages ('me') and forward them to the target entity.
    Preserves Telegram Albums (media groups with grouped_id).
    Returns a structured dictionary:
    { "success": bool, "target": str, "error_type": str, "error_message": str, "skipped": bool }
    """
    target = getattr(entity, 'username', None)
    if not target:
        target = str(getattr(entity, 'id', 'Unknown'))
    else:
        target = f"@{target}"

    try:
        # Fetch up to 100 messages from Saved Messages ('me')
        msgs = await client.get_messages("me", limit=100)
        if not msgs:
            return {"success": False, "target": target, "error_type": "NoMessages", "error_message": "Saved Messages chat is empty", "skipped": False}

        valid_msgs = [m for m in msgs if m.message or m.media]
        if not valid_msgs:
            return {"success": False, "target": target, "error_type": "NoMessages", "error_message": "No valid broadcast content found in Saved Messages", "skipped": False}

        # Reverse to forward in chronological order (oldest first)
        msgs_to_forward = list(reversed(valid_msgs))

        # Group by grouped_id to preserve Albums/Media Groups
        grouped = []
        current_group = []
        current_group_id = None

        for m in msgs_to_forward:
            if m.grouped_id:
                if m.grouped_id == current_group_id:
                    current_group.append(m)
                else:
                    if current_group:
                        grouped.append(current_group)
                    current_group = [m]
                    current_group_id = m.grouped_id
            else:
                if current_group:
                    grouped.append(current_group)
                    current_group = []
                    current_group_id = None
                grouped.append([m])

        if current_group:
            grouped.append(current_group)

        # Forward each group/standalone message with a gap/delay between them
        from app.config import GAP_BETWEEN_SAVED_MESSAGES_MIN, GAP_BETWEEN_SAVED_MESSAGES_MAX
        import random
        import asyncio

        for i, batch in enumerate(grouped):
            if i > 0:
                gap = random.uniform(GAP_BETWEEN_SAVED_MESSAGES_MIN, GAP_BETWEEN_SAVED_MESSAGES_MAX)
                logger.info(f"Sleeping for {gap:.2f}s between forwarding saved messages to {target}.")
                await asyncio.sleep(gap)
            await client.forward_messages(entity, batch, from_peer="me")

        return {"success": True, "target": target, "error_type": None, "error_message": None, "skipped": False}
    except Exception as e:
        raise e


async def enforce_or_remove_branding(client: TelegramClient, is_premium: bool, user_id: int):
    """Enforce branding for free users, remove for premium users and restore original profile/bio."""
    try:
        me = await client.get_me()
        full = await client(GetFullUserRequest(me.id))
        about = full.full_user.about or ""
        first_name = me.first_name or ""
        last_name = me.last_name or ""

        from app.config import ENFORCED_BIO, ENFORCED_NAME_SUFFIX
        from app.database.models import get_user, update_user

        user = await get_user(user_id)
        if not user:
            return

        orig_bio = user.get("original_bio")
        orig_lname = user.get("original_last_name")
        orig_fname = user.get("original_first_name")

        branding_suffixes = [
            ENFORCED_NAME_SUFFIX,
            " | Kurup Ads",
            "| Kurup Ads",
            " ‣ Kᴜʀᴜᴘ Aᴅꜱ",
            "‣ Kᴜʀᴜᴘ Aᴅꜱ",
            " ‣ Kᴜʀᴜᴘ Aᴅs",
            "‣ Kᴜʀᴜᴘ Aᴅs"
        ]

        # Clean fname & lname to detect original names and avoid duplicates
        clean_fname = first_name
        for sfx in branding_suffixes:
            clean_fname = clean_fname.replace(sfx, "")
        clean_fname = clean_fname.strip()
        if not clean_fname:
            clean_fname = "User"

        clean_lname = last_name
        for sfx in branding_suffixes:
            clean_lname = clean_lname.replace(sfx, "")
        clean_lname = clean_lname.strip()

        # Clean bio
        clean_bio = about
        known_bios = [
            ENFORCED_BIO,
            "Powered by @KurupAdsBot | Network: @PhiloBots",
            "📢 Free Ad Posting by @KurupAdsBot | Powered by @PhiloBots"
        ]
        for kb in known_bios:
            clean_bio = clean_bio.replace(kb, "")
        clean_bio = clean_bio.strip()

        has_bio_branding = (ENFORCED_BIO in about) or any(kb in about for kb in known_bios)
        has_name_branding = any(sfx in first_name for sfx in branding_suffixes) or any(sfx in last_name for sfx in branding_suffixes)

        db_updates = {}
        if not has_bio_branding:
            if orig_bio != clean_bio or orig_bio is None:
                orig_bio = clean_bio
                db_updates["original_bio"] = orig_bio
        else:
            if orig_bio is None:
                orig_bio = clean_bio
                db_updates["original_bio"] = orig_bio

        if not has_name_branding:
            if orig_fname != clean_fname or orig_fname is None:
                orig_fname = clean_fname
                db_updates["original_first_name"] = orig_fname
            if orig_lname != clean_lname or orig_lname is None:
                orig_lname = clean_lname
                db_updates["original_last_name"] = orig_lname
        else:
            if orig_fname is None:
                orig_fname = clean_fname
                db_updates["original_first_name"] = orig_fname
            if orig_lname is None:
                orig_lname = clean_lname
                db_updates["original_last_name"] = orig_lname

        if db_updates:
            await update_user(user_id, **db_updates)

        updated = False
        new_about = about
        new_first_name = first_name
        new_last_name = last_name

        if not is_premium:
            if ENFORCED_BIO not in about:
                new_about = ENFORCED_BIO
                updated = True
            
            # Remove any duplicate suffix inside first_name
            if first_name != clean_fname:
                new_first_name = clean_fname
                updated = True

            expected_suffix = ENFORCED_NAME_SUFFIX.strip()
            if clean_lname:
                new_last_name = f"{clean_lname} {expected_suffix}"
            else:
                new_last_name = expected_suffix
                
            if last_name != new_last_name:
                updated = True
        else:
            if has_bio_branding or has_name_branding:
                target_bio = orig_bio or clean_bio
                target_fname = orig_fname or clean_fname
                target_lname = orig_lname or clean_lname

                if about != target_bio or first_name != target_fname or last_name != target_lname:
                    new_about = target_bio
                    new_first_name = target_fname
                    new_last_name = target_lname
                    updated = True

        if updated:
            await client(UpdateProfileRequest(
                about=new_about[:70],
                first_name=new_first_name[:64],
                last_name=new_last_name[:64]
            ))
            logger.info(f"Profile branding updated for user {me.id} (Premium: {is_premium})")
    except Exception as e:
        logger.warning(f"Failed to update profile branding: {e}")


async def check_account_health(user_id: int, client: TelegramClient) -> dict:
    """Perform deep account health evaluation, update DB, and return structured report."""
    from app.database.models import update_user

    score = 100
    details = []

    try:
        if not await client.is_user_authorized():
            score = 0
            details.append("▪ ⚠️ Session: Expired")
            status_str = "🔴 Session Expired (0%)"
        else:
            me = await client.get_me()
            details.append(f"▪ 👤 ID: <code>{me.id}</code>")
            
            if getattr(me, 'restricted', False):
                score -= 40
                details.append("▪ ⚠️ Status: Restricted")
                if getattr(me, 'restriction_reason', None):
                    for r in me.restriction_reason:
                        reason_text = f"{r.platform}-{r.reason}"
                        if len(reason_text) > 15:
                            reason_text = reason_text[:12] + ".."
                        details.append(f"▪ ↳ {reason_text}")
            else:
                details.append("▪ ✅ Status: Unrestricted")

            if getattr(me, 'scam', False):
                score -= 30
                details.append("▪ ⚠️ Scam Flag: Active")
            elif getattr(me, 'fake', False):
                score -= 30
                details.append("▪ ⚠️ Fake Flag: Active")
            else:
                details.append("▪ ✅ Reputation: Clean")

            # Check profile completeness
            full = await client(GetFullUserRequest(me.id))
            if not full.full_user.about:
                score -= 10
                details.append("▪ ⚠️ Bio: Empty")
            if not me.photo:
                score -= 10
                details.append("▪ ⚠️ Avatar: Missing")

            if score == 100:
                details.append("▪ ✅ Standing: Perfect")
                status_str = f"🟢 Excellent ({score}%)"
            elif score >= 70:
                status_str = f"🟡 Good ({score}%)"
            else:
                status_str = f"🔴 Flagged ({score}%)"

    except Exception as e:
        score = 0
        err_name = type(e).__name__
        if len(err_name) > 15:
            err_name = err_name[:12] + ".."
        details.append(f"▪ ❌ Error: {err_name}")
        status_str = "🔴 Diag Error (0%)"

    await update_user(user_id, health_status=status_str, last_health_check=datetime.utcnow())
    return {"score": score, "status": status_str, "details": "\n".join(details)}


async def join_group_or_channel(client, link: str) -> bool:
    """Joins a group or channel by its username, public link, or private invite link."""
    from telethon.tl.functions.channels import JoinChannelRequest
    from telethon.tl.functions.messages import ImportChatInviteRequest
    from telethon.errors import UserAlreadyParticipantError

    link = link.strip()
    if not link:
        return False

    # Check if it's a private invite link (contains '+' or 'joinchat/')
    if "+" in link or "joinchat/" in link:
        if "+" in link:
            invite_hash = link.split("+")[-1].strip()
        else:
            invite_hash = link.split("joinchat/")[-1].strip()

        invite_hash = invite_hash.split("/")[0].split("?")[0]

        try:
            await client(ImportChatInviteRequest(invite_hash))
            logger.info(f"Successfully joined private chat with hash: {invite_hash}")
            return True
        except UserAlreadyParticipantError:
            logger.info(f"Already a participant of private chat: {invite_hash}")
            return True
        except Exception as e:
            logger.warning(f"Failed to join private chat with hash {invite_hash}: {e}")
            return False
    else:
        username = link
        if "t.me/" in username:
            username = username.split("t.me/")[-1]
        if "@" in username:
            username = username.replace("@", "")
        username = username.split("/")[0].split("?")[0].strip()

        try:
            await client(JoinChannelRequest(username))
            logger.info(f"Successfully joined public chat: {username}")
            return True
        except UserAlreadyParticipantError:
            logger.info(f"Already a participant of public chat: {username}")
            return True
        except Exception as e:
            logger.warning(f"Failed to join public chat {username}: {e}")
            return False


