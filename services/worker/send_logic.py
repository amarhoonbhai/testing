"""
Core message-sending logic for the stronger worker.
Hardened for Megagroup (Supergroup) support and robust entity resolution.
"""

import asyncio
import logging
import random
import datetime
from telethon import TelegramClient, types, functions
from telethon.errors import (
    FloodWaitError, PeerFloodError, ChatWriteForbiddenError,
    UserPrivacyRestrictedError, InviteHashExpiredError, InviteHashInvalidError,
    ChannelsTooMuchError, UserBannedInChannelError, PeerIdInvalidError,
    ChannelInvalidError, UsernameNotOccupiedError, UsernameInvalidError
)
from core.database import get_database
from models.group import toggle_group, mark_group_failing, clear_group_fail, remove_group
from core.adaptive import AdaptiveDelayController, UserLogAdapter

logger = logging.getLogger(__name__)

async def send_message_to_group(
    client: TelegramClient,
    job_id: str,
    user_id: int,
    phone: str,
    message_id: int,
    group_id: int,
    copy_mode: bool = False,
    adaptive_controller: AdaptiveDelayController = None,
    msg_obj = None,
) -> tuple[str, int]:
    """
    Robust message sender with fix for 'Invalid object ID' (Megagroup/Channel).
    """
    db = get_database()
    lgr = UserLogAdapter(logger, {'user_id': user_id, 'phone': phone})
    
    group_doc = await db.groups.find_one({"user_id": user_id, "chat_id": group_id})
    if not group_doc: return "skip", 0

    handle = group_doc.get("chat_username")
    title = group_doc.get("chat_title", "Unknown")
    target_entity = None
    
    # ── STEP 1: ROBUST ENTITY RESOLUTION ─────────────────────────────────
    try:
        # Pre-emptive check for supergroup IDs missing the -100 prefix
        if str(group_id).startswith("-") and not str(group_id).startswith("-100"):
            # This is likely a supergroup stored incorrectly. Telethon needs -100...
            # We try to resolve via username if available, or just try appending -100
            if handle:
                target_entity = await client.get_input_entity(handle)
            else:
                # Fallback to appending -100 prefix for 10-digit IDs
                potential_id = int(f"-100{abs(group_id)}")
                target_entity = await client.get_input_entity(potential_id)
        else:
            target_entity = await client.get_input_entity(group_id)
    except (ValueError, PeerIdInvalidError, ChannelInvalidError):
        # Entity not in cache or ID is ambiguous. Attempting "Deep Resolution".
        try:
            if handle:
                target_entity = await client.get_entity(handle)
            elif " [Private] +" in title:
                from telethon.tl.functions.messages import ImportChatInviteRequest
                invite_hash = title.split(" [Private] +")[1]
                await client(ImportChatInviteRequest(invite_hash))
                # Now that we've joined, get entity again
                target_entity = await client.get_entity(group_id)
            else:
                # Last resort — if we have the ID but no peer, we might be banned or kicked
                lgr.warning(f"Could not resolve entity for {group_id}. Skipping.")
                return "failed", 0
        except Exception as e:
            lgr.error(f"Resolution FAILED for {group_id}: {e}")
            return "failed", 0

    # ── STEP 2: STEALTH BEHAVIORS ─────────────────────────────────────────
    try:
        if random.random() > 0.1:
            async with client.action(target_entity, 'typing'):
                await asyncio.sleep(random.uniform(2, 4))
    except: pass

    # ── STEP 3: EXECUTION ────────────────────────────────────────────────
    try:
        if not msg_obj:
            if message_id == -1:
                latest = await client.get_messages('me', limit=1); msg_obj = latest[0] if latest else None
            else:
                msg_obj = await client.get_messages('me', ids=message_id)

        if not msg_obj: return "failed", 0
        if not msg_obj.text and not msg_obj.media: return "skip", 0

        # USE HIGH-LEVEL FORWARDING (Handles Channel/Chat type internally)
        if copy_mode:
            await client.send_message(target_entity, msg_obj)
        else:
            # Telethon's forward_messages is smarter than manually designing requests
            await client.forward_messages(target_entity, [msg_obj], from_peer='me')
        
        if adaptive_controller: adaptive_controller.on_success()
        await clear_group_fail(user_id, group_id)
        return "sent", 0

    except FloodWaitError as e:
        if adaptive_controller: adaptive_controller.on_flood(e.seconds)
        return "flood", e.seconds
    except PeerFloodError:
        pause_until = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        await db.sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"paused_until": pause_until}})
        return "failed", 0
    except (InviteHashExpiredError, InviteHashInvalidError, UserBannedInChannelError):
        await remove_group(user_id, group_id, phone=phone)
        return "failed", 0
    except Exception as e:
        lgr.error(f"Send Error: {e}")
        return "failed", 0
