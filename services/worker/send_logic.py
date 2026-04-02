"""
Core send logic — extracted from the existing worker/sender.py.

Contains the actual Telegram message-sending logic that workers execute:
  - Entity pre-validation
  - Human-like typing simulation
  - FloodWait / PeerFlood / permission error handling
  - Group auto-pause / auto-remove
"""

import asyncio
import random
import logging
from typing import Tuple

from telethon import TelegramClient


from telethon.errors import (
    FloodWaitError,
    PeerFloodError,
    ChatWriteForbiddenError,
    ChannelPrivateError,
    ChatAdminRequiredError,
    UserBannedInChannelError,
    InputUserDeactivatedError,
    RPCError,
    ChannelInvalidError,
    UsernameNotOccupiedError,
    UsernameInvalidError,
    InviteHashExpiredError,
)

from models.group import remove_group, toggle_group, mark_group_failing, clear_group_fail
from models.job import log_job_event
from models.session import pause_session
from shared.spintax import parse_spintax

logger = logging.getLogger(__name__)

def make_unique(text: str) -> str:
    """Appends a random number of zero-width spaces to make message hash unique."""
    return text + ("\u200b" * random.randint(1, 4))


async def send_message_to_group(
    client: TelegramClient,
    job_id: str,
    user_id: int,
    phone: str,
    message_id: int,
    group_id: int,
    copy_mode: bool = False,
) -> Tuple[str, int]:
    """
    Send a single message to a single group.

    Returns:
        (status, flood_wait_seconds)
        status is one of: "sent", "failed", "flood", "removed", "paused", "deactivated"
        flood_wait_seconds > 0 if a FloodWaitError was encountered.
    """
    try:        # ── 1. Pre-validate / resolve entity ─────────────────────
        entity = None
        try:
            entity = await client.get_entity(group_id)

        except (ChannelInvalidError, UsernameNotOccupiedError,
                UsernameInvalidError, InviteHashExpiredError) as e:
            logger.warning(f"❌ Group {group_id} invalid ({type(e).__name__}). Removing.")
            asyncio.create_task(remove_group(user_id, group_id))
            await log_job_event(job_id, user_id, phone, group_id, message_id,
                                "removed", f"Pre-check: {type(e).__name__}")
            return ("removed", 0)

        except (ChatWriteForbiddenError, ChannelPrivateError,
                ChatAdminRequiredError, UserBannedInChannelError) as e:
            logger.warning(f"⚠️ Group {group_id} restricted ({type(e).__name__}). Marking failing.")
            asyncio.create_task(mark_group_failing(user_id, group_id, f"Pre-check: {type(e).__name__}"))
            await log_job_event(job_id, user_id, phone, group_id, message_id,
                                "failing", f"Pre-check: {type(e).__name__}")
            return ("failing", 0)

        except (ValueError, Exception) as e:
            # Entity not in cache — try full dialog scan
            logger.info(f"Entity not cached for {group_id} — scanning dialogs...")
            try:
                # Optimized dialog scan: only if it looks like a real ID
                if group_id < -1000000000: # Typical real group ID range
                    async for dialog in client.iter_dialogs():
                        if dialog.id == group_id:
                            entity = dialog.entity
                            break
            except Exception:
                pass

            # Still not found — try to look up from DB (stored username or invite hash)
            if not entity:
                try:
                    from core.database import get_database
                    db = get_database()
                    group_doc = await db.groups.find_one({"user_id": user_id, "chat_id": group_id})
                    if not group_doc:
                        return ("failed", 0)
                        
                    title = group_doc.get("chat_title", "")
                    username = group_doc.get("chat_username")

                    # 1. Try public username resolution
                    if not username and title and re.match(r'^[a-zA-Z0-9_]{4,32}$', title):
                        # Fallback for old groups: title might be the slug
                        username = title

                    if username:
                        logger.info(f"Attempting to resolve public group: @{username}")
                        try:
                            entity = await client.get_entity(username)
                            if entity:
                                # Update stored chat_id with real ID for future
                                await db.groups.update_one(
                                    {"user_id": user_id, "chat_id": group_id},
                                    {"$set": {"chat_id": entity.id}}
                                )
                                logger.info(f"Successfully resolved @{username} to {entity.id}")
                        except Exception as res_e:
                            logger.warning(f"Failed to resolve @{username}: {res_e}")

                    # 2. Try private invite join
                    if not entity and "[Private]" in title:
                        import re
                        m = re.search(r'\+([A-Za-z0-9_\-]+)', title)
                        if m:
                            invite_hash = m.group(1)
                            logger.info(f"Trying to join private group via hash +{invite_hash}")
                            try:
                                from telethon.tl.functions.messages import ImportChatInviteRequest
                                result = await client(ImportChatInviteRequest(invite_hash))
                                if hasattr(result, 'chats') and result.chats:
                                    entity = result.chats[0]
                                    await db.groups.update_one(
                                        {"user_id": user_id, "chat_id": group_id},
                                        {"$set": {"chat_id": entity.id}}
                                    )
                                    logger.info(f"Joined private group {entity.id} via invite")
                            except Exception as join_e:
                                if "USER_ALREADY_PARTICLE" in str(join_e).upper():
                                    # Already in, get entity by hash? Telethon doesn't easily support this.
                                    # Fallback: maybe it's in dialogs now?
                                    pass
                                logger.warning(f"Failed to join via invite hash: {join_e}")
                except Exception:
                    pass

            if not entity:
                logger.warning(f"Cannot resolve entity for group_id={group_id} — skipping")
                asyncio.create_task(mark_group_failing(user_id, group_id, "Entity Not Found"))
                await log_job_event(job_id, user_id, phone, group_id, message_id,
                                    "failing", "Entity Not Found")
                return ("failing", 0)

        # ── 2. Human-like interactions ──────────────────────────────────
        # 2a. Mark as read (looks like a person opened the chat)
        try:
            await client.send_read_acknowledge(entity)
            await asyncio.sleep(random.uniform(1.0, 3.0))
        except Exception:
            pass

        # 2b. Human-like typing
        if random.random() > 0.1:  # 90% chance
            try:
                async with client.action(entity, "typing"):
                    await asyncio.sleep(random.uniform(2.5, 6.0))
            except Exception:
                pass

        # ── 3. Micro-delay (Human thinking time) ────────────────────────
        await asyncio.sleep(random.uniform(0.5, 2.0))

        # ── 4. Send the message ─────────────────────────────────────────
        if copy_mode:
            # Copy mode: sends without "Forwarded from" tag
            saved_msg = await client.get_messages("me", ids=message_id)
            if not saved_msg:
                await log_job_event(job_id, user_id, phone, group_id, message_id,
                                    "failed", "Message not found in Saved Messages")
                return ("failed", 0)
            if not saved_msg.text and not saved_msg.media:
                await log_job_event(job_id, user_id, phone, group_id, message_id,
                                    "skipped", "Empty message")
                return ("failed", 0)
            msg_text = parse_spintax(saved_msg.text or "")
            msg_text = make_unique(msg_text)
            
            await client.send_message(
                entity=entity,
                message=msg_text,
                file=saved_msg.media or None,
                formatting_entities=saved_msg.entities if saved_msg.text else None,
                link_preview=False,
            )
        else:
            # Forward mode — NOTE: from_peer must be "me", NOT InputPeerSelf()
            await client.forward_messages(
                entity=entity,
                messages=[message_id],
                from_peer="me",
            )

        await log_job_event(job_id, user_id, phone, group_id, message_id, "sent")
        # Clear any previous failing status on success
        asyncio.create_task(clear_group_fail(user_id, group_id))
        return ("sent", 0)

    except FloodWaitError as e:
        logger.warning(f"FloodWait: {e.seconds}s on group {group_id}")
        await log_job_event(job_id, user_id, phone, group_id, message_id,
                            "flood", f"FloodWait {e.seconds}s")
        return ("flood", e.seconds)

    except PeerFloodError:
        logger.error(f"🚨 PeerFlood on group {group_id} — account restricted! Pausing for 24h.")
        asyncio.create_task(pause_session(user_id, phone, duration_hours=24))
        await log_job_event(job_id, user_id, phone, group_id, message_id,
                            "flood", "PeerFlood (Auto-Paused 24h)")
        return ("flood", 7200)  # 2-hour cooldown for this specific worker loop

    except (ChannelInvalidError, UsernameNotOccupiedError,
            UsernameInvalidError, InviteHashExpiredError) as e:
        logger.warning(f"❌ Removing group {group_id}: {type(e).__name__}")
        asyncio.create_task(remove_group(user_id, group_id))
        await log_job_event(job_id, user_id, phone, group_id, message_id,
                            "removed", f"{type(e).__name__}")
        return ("removed", 0)

    except (ChatWriteForbiddenError, ChannelPrivateError,
            ChatAdminRequiredError, UserBannedInChannelError) as e:
        reason = type(e).__name__
        logger.warning(f"⚠️ Group {group_id} failing: {reason}")
        asyncio.create_task(mark_group_failing(user_id, group_id, reason))
        await log_job_event(job_id, user_id, phone, group_id, message_id,
                            "failing", f"Failing: {reason}")
        return ("failing", 0)

    except InputUserDeactivatedError:
        logger.error(f"🛑 Account {phone} is deactivated!")
        from models.session import mark_session_disabled
        asyncio.create_task(
            mark_session_disabled(user_id, phone, reason="UserDeactivated")
        )
        await log_job_event(job_id, user_id, phone, group_id, message_id,
                            "failed", "UserDeactivated")
        return ("deactivated", 0)


    except RPCError as e:
        error_msg = str(e).upper()
        
        # 1. MESSAGE_ID_INVALID: The ad message was deleted from Saved Messages
        if "MESSAGE_ID_INVALID" in error_msg or "OPERATION ON SUCH MESSAGE" in error_msg:
            logger.warning(f"Message ID invalid or deleted (msg {message_id})")
            await log_job_event(job_id, user_id, phone, group_id, message_id,
                                "skipped", "Message deleted/invalid")
            # Don't pause the group, just skip this message
            return ("failed", 0)

        # 2. TOPIC_CLOSED or Join Required: Mark as failing (delayed removal)
        elif any(x in error_msg for x in ["CHAT_ADMIN_REQUIRED", "CHAT_WRITE_FORBIDDEN",
                                          "USER_BANNED_IN_CHANNEL", "TOPIC_CLOSED", "JOIN THE DISCUSSION GROUP",
                                          "SEND_MESSAGES_FORBIDDEN"]):
            asyncio.create_task(mark_group_failing(user_id, group_id, f"Restricted: {error_msg[:40]}"))
            await log_job_event(job_id, user_id, phone, group_id, message_id,
                                "failing", f"Restricted: {error_msg[:40]}")
            return ("failing", 0)
            
        # 3. CHANNEL_INVALID or Not Occupied: Remove the group
        elif any(x in error_msg for x in ["CHANNEL_INVALID", "USERNAME_NOT_OCCUPIED",
                                            "USERNAME_INVALID", "INVITE_HASH_EXPIRED"]):
            asyncio.create_task(remove_group(user_id, group_id))
            await log_job_event(job_id, user_id, phone, group_id, message_id,
                                "removed", f"Invalid: {error_msg[:20]}")
            return ("removed", 0)
            
        # 4. Message Empty: User tried to copy a totally empty URL preview or similar unsupported media
        elif "MESSAGE CANNOT BE EMPTY" in error_msg:
            logger.warning(f"Empty message content for copying (msg {message_id})")
            await log_job_event(job_id, user_id, phone, group_id, message_id,
                                "skipped", "Empty message or unsupported media")
            return ("failed", 0)
            
        else:
            logger.error(f"RPCError on group {group_id}: {e}")
            await log_job_event(job_id, user_id, phone, group_id, message_id,
                                "failed", error_msg[:50])
            return ("failed", 0)

    except Exception as e:
        logger.error(f"Unexpected error on group {group_id}: {e}")
        await log_job_event(job_id, user_id, phone, group_id, message_id,
                            "failed", str(e)[:50])
        return ("failed", 0)
