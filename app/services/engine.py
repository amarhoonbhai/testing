"""
Broadcasting Engine — Manages asynchronous broadcast worker loops.

Features:
- Saved Messages Auto-Forwarding (Albums & Media Groups)
- Adaptive Exponential Backoff with Jitter (FloodWait / SlowMode)
- Memory & Database Entity Caching (InputPeer optimization)
- Real-time Telemetry (ETA, Speed in msg/min, Live Progress Dashboard)
- Session Revocation Protection & Self-Healing
- Smart Auto-Responder Rules (Only during broadcast, Exclude contacts)
"""

import asyncio
import logging
import random
import time
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError,
    SlowModeWaitError,
    ChatWriteForbiddenError,
    ChatAdminRequiredError,
    UserBannedInChannelError,
    AuthKeyUnregisteredError,
    UserDeactivatedError,
    SessionRevokedError,
    UnauthorizedError,
)
from telethon.tl.types import InputPeerChat, InputPeerChannel, InputPeerUser

from app.config import MAX_FAIL_SKIP, MIN_INTERVAL
from app.database.models import (
    get_user, update_user, set_broadcasting, increment_sent,
    increment_failed, increment_group_fail, reset_group_fail,
    get_broadcasting_users, clear_progress_message, clear_session,
    get_cached_entity, set_cached_entity, set_group_reason,
)
from app.services.encryption_service import decrypt_session
from app.services.telethon_service import (
    get_client_from_session, forward_saved_messages_to_entity,
    enforce_or_remove_branding,
)
from app.services.channel_logger import (
    log_broadcast_started, log_broadcast_stopped, log_broadcast_cycle_complete,
    log_broadcast_error, log_account_invalid,
)
from app.bot import messages, keyboards

logger = logging.getLogger(__name__)

# Track active asyncio tasks: {user_id: Task}
active_tasks = {}


def _setup_auto_responder(client: TelegramClient, user_id: int):
    """Register Telethon event listener for smart auto-responder."""
    @client.on(events.NewMessage(incoming=True))
    async def auto_responder_handler(event):
        try:
            if not event.is_private:
                return

            user = await get_user(user_id)
            if not user or not user.get("auto_responder_enabled"):
                return

            rules = user.get("auto_responder_rules", {})
            
            # Rule 1: Only during broadcast
            if rules.get("only_during_broadcast", True) and not user.get("is_broadcasting"):
                return

            # Rule 2: Exclude contacts
            if rules.get("exclude_contacts", True):
                sender = await event.get_sender()
                if getattr(sender, 'contact', False):
                    return

            reply_msg = user.get("auto_responder_message")
            if reply_msg:
                # Human delay before replying
                await asyncio.sleep(random.uniform(1.5, 4.0))
                await event.reply(reply_msg)
                logger.info(f"Auto-responder replied to {event.chat_id} for user {user_id}")
        except Exception as e:
            logger.warning(f"Auto-responder error for {user_id}: {e}")


async def _resolve_group(client: TelegramClient, group_link: str, user_id: int):
    """
    Resolve a group link to a Telethon entity.
    Uses database entity caching to eliminate redundant get_entity RPC calls.
    """
    cached = await get_cached_entity(user_id, group_link)
    if cached:
        try:
            peer_type = cached.get("_type")
            peer_id = cached.get("id")
            access_hash = cached.get("access_hash", 0)

            if peer_type == "InputPeerChannel":
                return InputPeerChannel(peer_id, access_hash)
            elif peer_type == "InputPeerChat":
                return InputPeerChat(peer_id)
            elif peer_type == "InputPeerUser":
                return InputPeerUser(peer_id, access_hash)
        except Exception as e:
            logger.warning(f"Cached entity invalid for {group_link}: {e}")

    # Not cached or invalid, fetch via API
    if group_link.startswith("https://t.me/+"):
        entity = await client.get_entity(group_link)
    elif group_link.startswith("https://t.me/c/"):
        parts = group_link.split("/")
        channel_id = int(parts[4])
        peer_id = int(f"-100{channel_id}") if not str(channel_id).startswith("-100") else channel_id
        entity = await client.get_entity(peer_id)
    else:
        clean = group_link.replace("https://t.me/", "").replace("@", "").strip()
        entity = await client.get_entity(clean)

    # Cache the resolved input peer
    input_peer = await client.get_input_entity(entity)
    cache_dict = {
        "id": getattr(input_peer, 'channel_id', getattr(input_peer, 'chat_id', getattr(input_peer, 'user_id', 0))),
        "access_hash": getattr(input_peer, 'access_hash', 0),
        "_type": type(input_peer).__name__,
    }
    await set_cached_entity(user_id, group_link, cache_dict)
    return entity


async def _update_progress(user_id: int, sent: int, failed: int, skipped: int, total: int, start_time: float, bot=None):
    """Update the live broadcast progress message with ETA and speed calculations."""
    user = await get_user(user_id)
    if not user or not user.get("progress_chat_id") or not user.get("progress_message_id"):
        return

    chat_id = user["progress_chat_id"]
    msg_id = user["progress_message_id"]

    elapsed = time.time() - start_time
    total_processed = sent + failed + skipped
    remaining = total - total_processed

    speed = (sent / elapsed * 60) if elapsed > 0 else 0.0
    eta_seconds = int((remaining / speed * 60)) if speed > 0 else 0

    text = messages.broadcast_progress_text(
        sent=sent, failed=failed, skipped=skipped, total=total,
        speed=speed, eta_seconds=eta_seconds
    )

    if bot:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                parse_mode="HTML"
            )
        except Exception as e:
            if "exactly the same" not in str(e).lower():
                logger.warning(f"Failed to update progress message: {e}")


async def _execute_cycle(user_id: int, client: TelegramClient, bot=None) -> dict:
    """Execute one complete broadcast cycle across all valid groups."""
    user = await get_user(user_id)
    if not user:
        return {"sent": 0, "failed": 0, "skipped": 0, "total": 0}

    groups = user.get("groups", [])
    group_fails = user.get("group_fails", {})
    total_groups = len(groups)

    sent = 0
    failed = 0
    skipped = 0
    start_time = time.time()

    # Apply/Remove branding at start of cycle
    await enforce_or_remove_branding(client, user.get("is_premium", False), user_id)

    for i, group_link in enumerate(groups):
        curr_user = await get_user(user_id)
        if not curr_user or not curr_user.get("session_encrypted") or not curr_user.get("groups"):
            logger.info(f"Broadcast stopped mid-cycle for user {user_id} (prerequisites missing)")
            await set_broadcasting(user_id, False)
            break
        if not curr_user.get("is_broadcasting"):
            logger.info(f"Broadcast stopped mid-cycle for user {user_id} (admin override)")
            break

        fails = group_fails.get(group_link.replace(".", "_DOT_").replace("$", "_DOLLAR_"), 0)
        if fails >= MAX_FAIL_SKIP:
            skipped += 1
            await _update_progress(user_id, sent, failed, skipped, total_groups, start_time, bot)
            continue

        try:
            entity = await _resolve_group(client, group_link, user_id)
            
            # Forward saved messages
            await forward_saved_messages_to_entity(client, entity)
            
            sent += 1
            await increment_sent(user_id)
            await reset_group_fail(user_id, group_link)

            delay = random.uniform(2.0, 5.0)
            await asyncio.sleep(delay)

        except FloodWaitError as e:
            failed += 1
            await increment_failed(user_id)
            await increment_group_fail(user_id, group_link)
            await set_group_reason(user_id, group_link, f"FloodWait ({e.seconds}s)")
            logger.warning(f"FloodWait in broadcast for {user_id}: sleeping {e.seconds}s")
            await asyncio.sleep(e.seconds + random.uniform(1.0, 3.0))

        except SlowModeWaitError as e:
            failed += 1
            await increment_failed(user_id)
            await increment_group_fail(user_id, group_link)
            await set_group_reason(user_id, group_link, f"SlowMode ({e.seconds}s)")
            logger.warning(f"SlowMode in broadcast for {user_id}: sleeping {e.seconds}s")
            await asyncio.sleep(e.seconds + random.uniform(1.0, 2.0))

        except (ChatWriteForbiddenError, ChatAdminRequiredError, UserBannedInChannelError) as e:
            failed += 1
            await increment_failed(user_id)
            await increment_group_fail(user_id, group_link)
            await set_group_reason(user_id, group_link, f"Forbidden / Banned ({type(e).__name__})")
            logger.warning(f"Write forbidden in {group_link} for {user_id}: {e}")
            await asyncio.sleep(1.0)

        except (AuthKeyUnregisteredError, UserDeactivatedError, SessionRevokedError, UnauthorizedError) as e:
            logger.error(f"Session revoked/deactivated during broadcast for {user_id}: {e}")
            await set_broadcasting(user_id, False)
            await clear_session(user_id)
            await log_account_invalid(user_id, str(e))
            if bot and curr_user.get("progress_chat_id"):
                try:
                    await bot.send_message(
                        chat_id=curr_user["progress_chat_id"],
                        text=messages.error_text(f"Your Telegram session was terminated ({type(e).__name__}). Broadcasting stopped."),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
            break

        except Exception as e:
            failed += 1
            await increment_failed(user_id)
            await increment_group_fail(user_id, group_link)
            await set_group_reason(user_id, group_link, f"Error ({type(e).__name__})")
            logger.error(f"Error broadcasting to {group_link} for {user_id}: {e}")
            await asyncio.sleep(1.0)

        await _update_progress(user_id, sent, failed, skipped, total_groups, start_time, bot)

    return {"sent": sent, "failed": failed, "skipped": skipped, "total": total_groups}


async def _broadcast_loop(user_id: int):
    """Main background loop managing broadcast cycles and resting intervals."""
    logger.info(f"Starting broadcast loop for user {user_id}")
    from app.services.channel_logger import get_bot
    bot = get_bot()

    user = await get_user(user_id)
    if not user or not user.get("session_encrypted"):
        await set_broadcasting(user_id, False)
        return

    client = None
    try:
        session = decrypt_session(user["session_encrypted"])
        client = await get_client_from_session(session)

        _setup_auto_responder(client, user_id)

        await log_broadcast_started(user_id, len(user.get("groups", [])), user.get("interval_seconds", MIN_INTERVAL))

        while True:
            curr = await get_user(user_id)
            if not curr or not curr.get("session_encrypted") or not curr.get("groups"):
                logger.info(f"Broadcast prerequisites missing for {user_id}. Halting autonomous loop.")
                await set_broadcasting(user_id, False)
                break

            if not curr.get("is_broadcasting"):
                logger.info(f"Broadcast stopped by admin override for {user_id}.")
                break

            cycle_res = await _execute_cycle(user_id, client, bot)
            
            curr = await get_user(user_id)
            if not curr or not curr.get("session_encrypted") or not curr.get("groups"):
                logger.info(f"Broadcast prerequisites missing for {user_id} after cycle. Halting autonomous loop.")
                await set_broadcasting(user_id, False)
                break

            if not curr.get("is_broadcasting"):
                logger.info(f"Broadcast stopped by admin override for {user_id} after cycle.")
                break

            await log_broadcast_cycle_complete(
                user_id, cycle_res["sent"], cycle_res["failed"], cycle_res["skipped"]
            )

            interval = curr.get("interval_seconds", MIN_INTERVAL)
            logger.info(f"Cycle complete for {user_id}. Resting for {interval}s.")
            
            for _ in range(interval):
                curr = await get_user(user_id)
                if not curr or not curr.get("session_encrypted") or not curr.get("groups"):
                    break
                if not curr.get("is_broadcasting"):
                    break
                await asyncio.sleep(1)

    except (AuthKeyUnregisteredError, UserDeactivatedError, SessionRevokedError, UnauthorizedError) as e:
        logger.error(f"Fatal session error in loop for {user_id}: {e}")
        await set_broadcasting(user_id, False)
        await clear_session(user_id)
        await log_account_invalid(user_id, str(e))
    except Exception as e:
        logger.error(f"Fatal error in broadcast loop for {user_id}: {e}")
        await set_broadcasting(user_id, False)
        await log_broadcast_error(user_id, str(e))
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
        if user_id in active_tasks:
            del active_tasks[user_id]
        logger.info(f"Broadcast loop terminated for user {user_id}")


async def start(user_id: int) -> dict:
    """Start the broadcast engine for a user autonomously."""
    user = await get_user(user_id)
    if not user:
        return {"success": False, "error": "User record not found."}

    if not user.get("session_encrypted"):
        return {"success": False, "error": "You must connect your Telegram account first."}

    groups = user.get("groups", [])
    if not groups:
        return {"success": False, "error": "You must add at least one target group."}

    if user_id in active_tasks:
        if not user.get("is_broadcasting"):
            await set_broadcasting(user_id, True)
        return {"success": True, "total_groups": len(groups)}

    await set_broadcasting(user_id, True)

    task = asyncio.create_task(_broadcast_loop(user_id))
    active_tasks[user_id] = task

    return {"success": True, "total_groups": len(groups)}


async def stop(user_id: int) -> dict:
    """Stop the broadcast engine for a user."""
    await set_broadcasting(user_id, False)
    await clear_progress_message(user_id)

    if user_id in active_tasks:
        task = active_tasks[user_id]
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        if user_id in active_tasks:
            del active_tasks[user_id]

    from app.services.channel_logger import log_broadcast_stopped
    await log_broadcast_stopped(user_id)

    return {"success": True}


async def auto_resume():
    """Resume active broadcasts on bot startup autonomously."""
    from app.database.models import get_active_users
    users = await get_active_users()
    logger.info(f"Auto-resuming autonomous broadcasts for {len(users)} active users...")

    for u in users:
        user_id = u["telegram_user_id"]
        if u.get("session_encrypted") and u.get("groups"):
            await set_broadcasting(user_id, True)
            task = asyncio.create_task(_broadcast_loop(user_id))
            active_tasks[user_id] = task
            logger.info(f"Started autonomous broadcast for user {user_id}")
        else:
            await set_broadcasting(user_id, False)
