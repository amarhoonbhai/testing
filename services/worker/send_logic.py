"""
Core message-sending logic for the stronger worker.
Handles dynamic joining, handle resolution, and multi-ad campaigns.
"""

import asyncio
import logging
import random
import datetime
from telethon import TelegramClient, types
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
    msg_obj = None, # Optional: pass pre-fetched message object for multi-ad
) -> tuple[str, int]:
    """
    Send a message to a group with Multi-Ad support and Stealth features.
    """
    db = get_database()
    lgr = UserLogAdapter(logger, {'user_id': user_id, 'phone': phone})
    
    group_doc = await db.groups.find_one({"user_id": user_id, "chat_id": group_id})
    if not group_doc: return "skip", 0

    handle = group_doc.get("chat_username")
    title = group_doc.get("chat_title", "Unknown")
    target_entity = None
    
    # ── STEP 1: Entity Resolution & Auto-Join ─────────────────────────────
    try:
        target_entity = await client.get_input_entity(group_id)
    except (ValueError, PeerIdInvalidError, ChannelInvalidError):
        try:
            if handle:
                from telethon.tl.functions.channels import JoinChannelRequest
                await client(JoinChannelRequest(handle))
                target_entity = await client.get_input_entity(handle)
            elif " [Private] +" in title:
                from telethon.tl.functions.messages import ImportChatInviteRequest
                invite_hash = title.split(" [Private] +")[1]
                await client(ImportChatInviteRequest(invite_hash))
                target_entity = await client.get_input_entity(group_id)
            else:
                lgr.warning(f"No handle/invite for auto-join to {group_id}")
                return "failed", 0
        except Exception as e:
            lgr.error(f"Auto-Join FAILED for {group_id}: {e}")
            await mark_group_failing(user_id, group_id, f"Auto-Join Failed: {str(e)}")
            return "failed", 0

    # ── STEP 2: Stealth Behaviors ─────────────────────────────────────────
    try:
        if random.random() > 0.1:
            async with client.action(target_entity, 'typing'):
                await asyncio.sleep(random.uniform(2, 4))
    except: pass
    await asyncio.sleep(random.uniform(0.2, 0.8))

    # ── STEP 3: Content Fetching with Empty-Skip ──────────────────────────
    try:
        if not msg_obj:
            if message_id == -1:
                latest = await client.get_messages('me', limit=1)
                if latest: msg_obj = latest[0]
            else:
                msg_obj = await client.get_messages('me', ids=message_id)

        if not msg_obj:
            lgr.error(f"Could not fetch ad message {message_id}")
            return "failed", 0
        
        # EMPTY MESSAGE SKIP Logic
        if not msg_obj.text and not msg_obj.media:
            lgr.warning(f"Skipping Message ID {msg_obj.id} — no text or media found.")
            return "skip", 0
            
        # SERVICE MESSAGE SKIP Logic
        if hasattr(msg_obj, 'action') and msg_obj.action is not None:
            lgr.warning(f"Skipping Message ID {msg_obj.id} — service message.")
            return "skip", 0

        # ── STEP 4: Send ──────────────────────────────────────────────────
        if copy_mode:
            await client.send_message(target_entity, msg_obj)
        else:
            await client.forward_messages(target_entity, msg_obj)
        
        if adaptive_controller: adaptive_controller.on_success()
        await clear_group_fail(user_id, group_id)
        return "sent", 0

    except FloodWaitError as e:
        if adaptive_controller: adaptive_controller.on_flood(e.seconds)
        return "flood", e.seconds

    except PeerFloodError:
        lgr.critical(f"🚨 PEER_FLOOD: Account restricted. Cooling down 2h.")
        pause_until = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        await db.sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"paused_until": pause_until, "pause_reason": "PeerFlood (2h cooldown)"}})
        return "failed", 0

    except ChatWriteForbiddenError:
        await mark_group_failing(user_id, group_id, "No permission to post")
        return "failed", 0

    except (InviteHashExpiredError, InviteHashInvalidError, UserBannedInChannelError):
        lgr.warning(f"Removing group {group_id} (Banned or Link Expired)")
        await remove_group(user_id, group_id, phone=phone)
        return "failed", 0

    except Exception as e:
        lgr.error(f"Send Error to {group_id}: {e}")
        return "failed", 0
