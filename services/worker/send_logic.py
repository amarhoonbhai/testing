"""
Core message-sending logic for the stronger worker.
Handles dynamic joining, handle resolution, and robust error management.
"""

import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import (
    FloodWaitError,
    PeerIdInvalidError,
    ChatWriteForbiddenError,
    UserPrivacyRestrictedError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    ChannelsTooMuchError,
    UserBannedInChannelError,
)
from core.database import get_database
from models.group import toggle_group, mark_group_failing, clear_group_fail, remove_group

logger = logging.getLogger(__name__)

async def send_message_to_group(
    client: TelegramClient,
    job_id: str,
    user_id: int,
    phone: str,
    message_id: int,
    group_id: int, # This is the numeric ID we stored or a fake hash ID
    copy_mode: bool = False,
) -> tuple[str, int]:
    """
    Send (forward) a message to a group with auto-join support.
    Returns: (status, flood_seconds)
    Status: 'sent', 'flood', 'deactivated', 'failed', 'skip'
    """
    db = get_database()
    
    # 1. Fetch group document to get handle/invite
    group_doc = await db.groups.find_one({"user_id": user_id, "chat_id": group_id})
    if not group_doc:
        logger.warning(f"[{phone}] Group {group_id} not found in database — skipping")
        return "skip", 0

    handle = group_doc.get("chat_username")
    title = group_doc.get("chat_title", "Unknown")
    
    target_entity = None
    
    # 2. Resolve target entity
    try:
        if handle:
            # Public username
            target_entity = await client.get_entity(handle)
        else:
            # Private hash or numeric ID
            # If it's a numeric ID (original ID preserved)
            if group_id < 0:
                target_entity = await client.get_entity(group_id)
            else:
                # This could be a private invite hash (we stored as "Invite:hash" in title or similar)
                # For simplicity, if we don't have an entity, we try to join first
                raise ValueError("No handle for invite")

    except (ValueError, PeerIdInvalidError):
        # We need to join or resolve
        # Check if the title contains an invite hash we stored
        # Format: "[Private] +hash"
        if " [Private] +" in title:
            invite_hash = title.split(" [Private] +")[1]
            try:
                await client(ImportChatInviteRequest(invite_hash))
                target_entity = await client.get_entity(group_id) # Try numeric lookup again
            except InviteHashExpiredError:
                await remove_group(user_id, group_id, phone=phone)
                logger.info(f"[{phone}] 🗑 Auto-Removed {group_id} (Invite link expired)")
                return "failed", 0
            except InviteHashInvalidError:
                await remove_group(user_id, group_id, phone=phone)
                logger.info(f"[{phone}] 🗑 Auto-Removed {group_id} (Invalid invite hash)")
                return "failed", 0
            except Exception as join_err:
                logger.error(f"[{phone}] Failed to join {group_id}: {join_err}")
                return "failed", 0
        elif handle:
            # Maybe it's a public join
            try:
                await client(JoinChannelRequest(handle))
                target_entity = await client.get_entity(handle)
            except Exception as join_err:
                logger.error(f"[{phone}] Failed to join {handle}: {join_err}")
                return "failed", 0
        else:
            await mark_group_failing(user_id, group_id, "Cannot resolve group entity")
            return "failed", 0

    # 3. Perform Forwarding
    try:
        await client(ForwardMessagesRequest(
            from_peer='me',
            id=[message_id],
            to_peer=target_entity,
            drop_author=not copy_mode, # True = 'Standard' (no author), False = 'Copy' (with author)
        ))
        
        # 4. Update Success Stats
        await clear_group_fail(user_id, group_id)
        await db.sessions.update_one(
            {"user_id": user_id, "phone": phone},
            {"$inc": {"total_sent": 1}, "$set": {"last_active": __import__('datetime').datetime.utcnow()}}
        )
        return "sent", 0

    except FloodWaitError as e:
        logger.warning(f"[{phone}] FloodWait observed: {e.seconds}s")
        return "flood", e.seconds

    except ChatWriteForbiddenError:
        await mark_group_failing(user_id, group_id, "ChatWriteForbidden: No permission to post here")
        logger.info(f"[{phone}] ⏸ Paused {group_id} (No permission to post)")
        return "failed", 0

    except UserPrivacyRestrictedError:
        await mark_group_failing(user_id, group_id, "UserPrivacyRestricted: Cannot forward due to privacy")
        return "failed", 0
    
    except UserBannedInChannelError:
        await remove_group(user_id, group_id, phone=phone)
        logger.info(f"[{phone}] 🗑 Auto-Removed {group_id} (Banned from group)")
        return "failed", 0

    except PeerIdInvalidError:
        await remove_group(user_id, group_id, phone=phone)
        logger.info(f"[{phone}] 🗑 Auto-Removed {group_id} (Group inaccessible/deleted)")
        return "failed", 0

    except Exception as e:
        err_name = type(e).__name__
        logger.error(f"[{phone}] {err_name} sending to {group_id}: {e}")
        await mark_group_failing(user_id, group_id, f"{err_name}: {str(e)}")
        return "failed", 0
