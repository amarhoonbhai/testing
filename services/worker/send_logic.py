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
        # Normalize and try to get input entity from cache/ID
        # Handle 10-digit IDs (positive or negative) which are likely supergroups missing -100
        s_id = str(group_id)
        is_potential_supergroup = (
            (len(s_id) >= 10 and not s_id.startswith("-")) or
            (s_id.startswith("-") and not s_id.startswith("-100") and len(s_id) >= 10)
        )

        if is_potential_supergroup:
            potential_id = int(f"-100{abs(group_id)}")
            try:
                target_entity = await client.get_input_entity(potential_id)
                group_id = potential_id
            except:
                # If -100 failed, try raw as fallback
                target_entity = await client.get_input_entity(group_id)
        else:
            target_entity = await client.get_input_entity(group_id)
            
    except (ValueError, PeerIdInvalidError, ChannelInvalidError):
        # Entity not in cache. Attempting "Brute-Force Resolution".
        try:
            if handle:
                lgr.info(f"Resolving by handle: @{handle}")
                target_entity = await client.get_entity(handle)
            else:
                lgr.info(f"Deep resolving numeric ID: {group_id}")
                # Try getting entity directly. Telethon will choose appropriate request.
                target_entity = await client.get_entity(group_id)
                
                # Double-check if we got a 'Chat' but it should be a 'Channel'
                if isinstance(target_entity, types.Chat):
                    lgr.warning(f"ID {group_id} resolved to a legacy Chat. Checking for Supergroup version...")
                    potential_id = int(f"-100{abs(group_id)}")
                    try:
                        target_entity = await client.get_entity(potential_id)
                        group_id = potential_id
                    except: pass # Stick with legacy chat if -100 fails
            
            if " [Private] +" in title and not target_entity:
                from telethon.tl.functions.messages import ImportChatInviteRequest
                invite_hash = title.split(" [Private] +")[1]
                await client(ImportChatInviteRequest(invite_hash))
                target_entity = await client.get_entity(group_id)
        except Exception as e:
            lgr.error(f"Resolution FAILED for {group_id}: {e}")
            return "failed", 0

    if not target_entity:
        lgr.warning(f"Target entity {group_id} is NULL after resolution. Skipping.")
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
