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
import pytz
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
    ApiIdInvalidError,
)
from telethon.tl.types import InputPeerChat, InputPeerChannel, InputPeerUser

from app.config import MAX_FAIL_SKIP, MIN_INTERVAL, SEND_DELAY_MIN, SEND_DELAY_MAX, TIMEZONE
from app.database.models import (
    get_user, update_user, set_broadcasting, increment_sent,
    increment_failed, increment_group_fail, reset_group_fail,
    get_broadcasting_users, clear_progress_message, clear_session,
    get_cached_entity, set_cached_entity, set_group_reason,
    add_activity_log, set_responder_persistent_cooldown,
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

_tz = pytz.timezone(TIMEZONE)

# Track active asyncio tasks: {user_id: Task}
active_tasks = {}

# Track last activity timestamp (heartbeat) for active tasks: {user_id: float_timestamp}
active_heartbeats = {}

# Track the current active run ID for each user to prevent duplicate tasks
active_run_ids = {}

# Concurrency Semaphore to limit simultaneous active broadcasters
_worker_semaphore = asyncio.Semaphore(10)

_watchdog_task = None


async def start_watchdog():
    """Start the worker health monitor watchdog."""
    global _watchdog_task
    if _watchdog_task is None:
        _watchdog_task = asyncio.create_task(_worker_watchdog_loop())
        logger.info("Worker Health Watchdog initialized.")


async def _worker_watchdog_loop():
    """Watchdog loop to monitor and heal dead or stalled broadcast tasks."""
    import time
    from app.services.channel_logger import get_bot
    await asyncio.sleep(10)  # Wait for startup to settle
    while True:
        try:
            bot = get_bot()
            from app.database.models import get_broadcasting_users
            users = await get_broadcasting_users()
            
            for u in users:
                user_id = u["telegram_user_id"]
                # Verify that the user still has session credentials and groups
                if not u.get("session_encrypted") or not u.get("groups"):
                    logger.warning(f"Watchdog detected broadcasting user {user_id} lacks prerequisites. Turning off database broadcast flag.")
                    await set_broadcasting(user_id, False)
                    continue

                task = active_tasks.get(user_id)
                stalled = False
                now = time.time()
                
                # Check if task is running but stalled (no heartbeat update)
                if task and not task.done():
                    last_heartbeat = active_heartbeats.get(user_id, now)
                    interval = u.get("interval_seconds", 1200)
                    # Safe threshold: at least 10 minutes (600s), or 2x the user's interval
                    threshold = max(interval * 2, 600)
                    if now - last_heartbeat > threshold:
                        stalled = True
                        logger.warning(f"Watchdog detected STALLED broadcast loop for user {user_id} (No heartbeat for {now - last_heartbeat:.0f}s, threshold {threshold}s). Cancelling task...")
                        task.cancel()
                        try:
                            await asyncio.wait_for(task, timeout=5.0)
                        except Exception:
                            pass

                # If user is marked as broadcasting, but no active task is running (or it's done or stalled)
                if not task or task.done() or stalled:
                    logger.warning(f"Watchdog detected stalled/missing broadcast loop for user {user_id}. Restoring...")
                    if user_id in active_tasks:
                        del active_tasks[user_id]
                    
                    run_id = time.time()
                    active_run_ids[user_id] = run_id
                    active_heartbeats[user_id] = now
                    
                    task = asyncio.create_task(_broadcast_loop(user_id, run_id))
                    active_tasks[user_id] = task
                    
                    if bot:
                        try:
                            await bot.send_message(
                                chat_id=user_id,
                                text="🔧 <b>System Auto-Recovery</b>\n\nYour broadcast worker encountered a minor interruption. The watchdog has successfully restored your session.",
                                parse_mode="HTML"
                            )
                        except Exception as restore_err:
                            logger.warning(f"Failed to send recovery message to {user_id}: {restore_err}")
        except Exception as watchdog_err:
            logger.error(f"Error in Worker Health Watchdog loop: {watchdog_err}")
        
        await asyncio.sleep(60)



# Track auto-responder cool-downs: {(user_id, peer_id): last_reply_time}
_responder_cooldowns = {}


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

            # Avoid responding to other bots (prevents loop replies)
            sender = await event.get_sender()
            if sender and getattr(sender, 'bot', False):
                return

            rules = user.get("auto_responder_rules", {})
            
            # Rule 1: Only during broadcast
            if rules.get("only_during_broadcast", True) and not user.get("is_broadcasting"):
                return

            # Rule 2: Exclude contacts
            if rules.get("exclude_contacts", True):
                if sender and getattr(sender, 'contact', False):
                    return

            # Rule 3: Persistent Anti-Spam Cooldown
            peer_id = str(event.chat_id)
            cooldown_seconds = user.get("auto_responder_cooldown_seconds", 21600)
            
            persistent_cooldowns = user.get("auto_responder_persistent_cooldowns", {})
            last_reply = persistent_cooldowns.get(peer_id, 0.0)
            
            now = time.time()
            if now - last_reply < cooldown_seconds:
                return

            # Rule 4: Keyword Matching Rules
            keywords = user.get("auto_responder_keywords", {})
            incoming_text = (event.message.message or "").strip().lower()
            
            matched_reply = None
            for kw, rep in keywords.items():
                if kw in incoming_text:
                    matched_reply = rep
                    break

            reply_msg = matched_reply if matched_reply else user.get("auto_responder_message")
            if reply_msg:
                # Set cooldown immediately to block concurrent triggers
                await set_responder_persistent_cooldown(user_id, int(peer_id), now)
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
    if group_link.startswith("https://t.me/+") or "joinchat/" in group_link:
        if "+" in group_link:
            invite_hash = group_link.split("+")[-1].strip()
        else:
            invite_hash = group_link.split("joinchat/")[-1].strip()
        invite_hash = invite_hash.split("/")[0].split("?")[0]

        from telethon.tl.functions.messages import CheckChatInviteRequest
        from telethon.tl.types import ChatInviteAlready
        try:
            invite = await client(CheckChatInviteRequest(invite_hash))
            if isinstance(invite, ChatInviteAlready):
                entity = invite.chat
            else:
                entity = await client.get_entity(group_link)
        except Exception:
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


async def _execute_cycle(user_id: int, client: TelegramClient, bot=None, run_id: float = None) -> dict:
    """Execute one complete broadcast cycle across all valid groups."""
    user = await get_user(user_id)
    if not user:
        return {"sent": 0, "failed": 0, "skipped": 0, "total": 0}

    # Run auto-pruning before starting the cycle
    from app.database.models import auto_prune_dead_groups
    pruned_count = await auto_prune_dead_groups(user_id)
    if pruned_count > 0:
        logger.info(f"Auto-pruned {pruned_count} dead groups for user {user_id}")
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

    # Cache user doc locally to optimize database I/O performance
    cached_user = user
    last_fetch_time = 0.0

    # Pre-fetch Saved Messages to optimize database & network operations
    pre_fetched_grouped = None
    try:
        msgs = await client.get_messages("me", limit=100)
        pre_fetched_grouped = []
        if msgs:
            valid_msgs = [m for m in msgs if m.message or m.media]
            if valid_msgs:
                msgs_to_forward = list(reversed(valid_msgs))
                current_group = []
                current_group_id = None
                for m in msgs_to_forward:
                    if m.grouped_id:
                        if m.grouped_id == current_group_id:
                            current_group.append(m)
                        else:
                            if current_group:
                                pre_fetched_grouped.append(current_group)
                            current_group = [m]
                            current_group_id = m.grouped_id
                    else:
                        if current_group:
                            pre_fetched_grouped.append(current_group)
                            current_group = []
                            current_group_id = None
                        pre_fetched_grouped.append([m])
                if current_group:
                    pre_fetched_grouped.append(current_group)
    except Exception as e:
        logger.error(f"Failed to pre-fetch Saved Messages for user {user_id}: {e}")
        pre_fetched_grouped = None

    for i, group_link in enumerate(groups):
        if run_id is not None and active_run_ids.get(user_id) != run_id:
            logger.info(f"Broadcast cycle for user {user_id} interrupted: superseded by new Run ID.")
            break

        active_heartbeats[user_id] = time.time()
        now_time = time.time()
        if now_time - last_fetch_time > 10.0:
            curr_user = await get_user(user_id)
            if curr_user:
                cached_user = curr_user
                last_fetch_time = now_time
            else:
                curr_user = cached_user
        else:
            curr_user = cached_user

        if not curr_user or not curr_user.get("session_encrypted") or not curr_user.get("groups"):
            logger.info(f"Broadcast stopped mid-cycle for user {user_id} (prerequisites missing)")
            await set_broadcasting(user_id, False)
            break
        if not curr_user.get("is_broadcasting"):
            logger.info(f"Broadcast stopped mid-cycle for user {user_id} (admin override)")
            break

        # Check Auto Night Mode mid-cycle
        now = datetime.now(_tz)
        sleep_cycle = _get_current_sleep_cycle(now.hour, curr_user)
        if sleep_cycle:
            start_h, end_h = sleep_cycle
            logger.info(f"Auto Night Mode triggered mid-cycle for {user_id}.")
            if bot and curr_user.get("progress_chat_id") and curr_user.get("progress_message_id"):
                try:
                    await bot.edit_message_text(
                        chat_id=curr_user["progress_chat_id"],
                        message_id=curr_user["progress_message_id"],
                        text=messages.sleep_mode_progress_text(start_h, end_h),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    if "exactly the same" not in str(e).lower():
                        logger.warning(f"Failed to update night mode progress mid-cycle: {e}")
            break

        clean_link = group_link.replace(".", "_DOT_").replace("$", "_DOLLAR_")
        fails = group_fails.get(clean_link, 0)
        if fails >= MAX_FAIL_SKIP:
            skipped += 1
            await _update_progress(user_id, sent, failed, skipped, total_groups, start_time, bot)
            continue

        # Proactive SlowMode Skip Check
        group_slowmodes = curr_user.get("group_slowmodes", {})
        group_last_posts = curr_user.get("group_last_posts", {})
        
        if clean_link in group_slowmodes:
            slowmode_seconds = group_slowmodes[clean_link]
            last_posted = group_last_posts.get(clean_link, 0.0)
            elapsed = time.time() - last_posted
            if elapsed < slowmode_seconds:
                remaining_wait = int(slowmode_seconds - elapsed)
                logger.info(f"Skipping {group_link} due to active SlowMode ({remaining_wait}s remaining)")
                await set_group_reason(user_id, group_link, f"SlowMode Active (Wait {remaining_wait}s)")
                await add_activity_log(user_id, "skipped", group_link, f"Slowmode Active ({remaining_wait}s remaining)")
                skipped += 1
                await _update_progress(user_id, sent, failed, skipped, total_groups, start_time, bot)
                continue

        try:
            entity = await _resolve_group(client, group_link, user_id)
            
            # Group Audit Check: Verify default rights
            is_restricted = False
            restriction_reason = ""
            if hasattr(entity, 'default_banned_rights') and entity.default_banned_rights:
                rights = entity.default_banned_rights
                if rights.send_messages:
                    is_restricted = True
                    restriction_reason = "Send Messages Banned"
                elif rights.embed_links:
                    is_restricted = True
                    restriction_reason = "Embed Links Banned"
                elif rights.send_media:
                    is_restricted = True
                    restriction_reason = "Send Media Banned"

            if is_restricted:
                logger.warning(f"Group {group_link} audit failed: {restriction_reason}")
                await set_group_reason(user_id, group_link, f"Restricted ({restriction_reason})")
                await add_activity_log(user_id, "skipped", group_link, f"Restricted ({restriction_reason})")
                skipped += 1
                await _update_progress(user_id, sent, failed, skipped, total_groups, start_time, bot)
                continue
            
            # Anti-Detection: Simulate human typing indicator
            try:
                async with client.action(entity, 'typing'):
                    await asyncio.sleep(random.uniform(1.5, 3.0))
            except Exception:
                await asyncio.sleep(random.uniform(1.5, 3.0))

            # Forward saved messages
            await forward_saved_messages_to_entity(client, entity, grouped_messages=pre_fetched_grouped)
            
            sent += 1
            await increment_sent(user_id)
            await reset_group_fail(user_id, group_link)
            await add_activity_log(user_id, "sent", group_link, "Successfully posted")

            # Update last posted timestamp
            group_last_posts = curr_user.get("group_last_posts", {})
            group_last_posts[clean_link] = time.time()
            await update_user(user_id, group_last_posts=group_last_posts)

            # Config-based delay with jitter
            delay = random.uniform(SEND_DELAY_MIN, SEND_DELAY_MAX)
            logger.info(f"Sleeping for {delay:.2f}s post-send (Jitter).")
            active = await _interruptible_sleep(delay, user_id, run_id)
            if not active:
                break

        except FloodWaitError as e:
            failed += 1
            await increment_failed(user_id)
            await increment_group_fail(user_id, group_link)
            await set_group_reason(user_id, group_link, f"FloodWait ({e.seconds}s)")
            await add_activity_log(user_id, "failed", group_link, f"FloodWait error ({e.seconds}s)")
            logger.warning(f"FloodWait in broadcast for {user_id}: sleeping {e.seconds}s")
            active = await _interruptible_sleep(e.seconds + random.uniform(1.0, 3.0), user_id, run_id)
            if not active:
                break

        except SlowModeWaitError as e:
            failed += 1
            await increment_failed(user_id)
            await increment_group_fail(user_id, group_link)
            await set_group_reason(user_id, group_link, f"SlowMode ({e.seconds}s)")
            await add_activity_log(user_id, "failed", group_link, f"Slowmode Hit ({e.seconds}s)")
            logger.warning(f"SlowMode in broadcast for {user_id}: sleeping {e.seconds}s")
            
            # Save the slowmode constraint
            group_slowmodes = curr_user.get("group_slowmodes", {})
            group_slowmodes[clean_link] = e.seconds
            group_last_posts = curr_user.get("group_last_posts", {})
            group_last_posts[clean_link] = time.time()
            
            await update_user(user_id, group_slowmodes=group_slowmodes, group_last_posts=group_last_posts)
            active = await _interruptible_sleep(e.seconds + random.uniform(1.0, 2.0), user_id, run_id)
            if not active:
                break

        except (ChatWriteForbiddenError, ChatAdminRequiredError, UserBannedInChannelError) as e:
            failed += 1
            await increment_failed(user_id)
            await increment_group_fail(user_id, group_link)
            await set_group_reason(user_id, group_link, f"Forbidden / Banned ({type(e).__name__})")
            await add_activity_log(user_id, "failed", group_link, f"Forbidden/Banned: {type(e).__name__}")
            logger.warning(f"Write forbidden in {group_link} for {user_id}: {e}")
            await asyncio.sleep(1.0)

        except (AuthKeyUnregisteredError, UserDeactivatedError, SessionRevokedError, UnauthorizedError) as e:
            logger.error(f"Session revoked/deactivated during broadcast for {user_id}: {e}")
            await set_broadcasting(user_id, False)
            await clear_session(user_id)
            await log_account_invalid(user_id, str(e))
            await add_activity_log(user_id, "failed", group_link, f"Session terminated: {type(e).__name__}")
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
            await add_activity_log(user_id, "failed", group_link, f"Error: {type(e).__name__}")
            logger.error(f"Error broadcasting to {group_link} for {user_id}: {e}")
            await asyncio.sleep(1.0)

        await _update_progress(user_id, sent, failed, skipped, total_groups, start_time, bot)

    return {"sent": sent, "failed": failed, "skipped": skipped, "total": total_groups}


async def _interruptible_sleep(seconds: float, user_id: int, run_id: float = None) -> bool:
    """Sleep in 1-second increments, checking if broadcasting is still active. Returns False if interrupted."""
    for _ in range(int(seconds)):
        if run_id is not None and active_run_ids.get(user_id) != run_id:
            return False
        active_heartbeats[user_id] = time.time()
        curr = await get_user(user_id)
        if not curr or not curr.get("is_broadcasting"):
            return False
        await asyncio.sleep(1.0)
    fraction = seconds - int(seconds)
    if fraction > 0:
        await asyncio.sleep(fraction)
        if run_id is not None and active_run_ids.get(user_id) != run_id:
            return False
        active_heartbeats[user_id] = time.time()
        curr = await get_user(user_id)
        if not curr or not curr.get("is_broadcasting"):
            return False
    return True


def _get_current_sleep_cycle(hour: int, user: dict) -> tuple[int, int] | None:
    """Return (start_hour, end_hour) if the given hour falls inside the user's sleep cycle."""
    if not user or not user.get("sleep_mode_enabled", True):
        return None
    start_h = user.get("sleep_mode_start_hour", 0)
    end_h = user.get("sleep_mode_end_hour", 5)
    
    # Handle wrap-around (e.g. 22:00 to 05:00)
    if start_h <= end_h:
        if start_h <= hour < end_h:
            return (start_h, end_h)
    else:  # Wrap around midnight
        if hour >= start_h or hour < end_h:
            return (start_h, end_h)
    return None


def _format_hour(h: int) -> str:
    """Format hour h in 12-hour format with AM/PM."""
    if h == 0:
        return "12:00 AM"
    elif h == 12:
        return "12:00 PM"
    elif h < 12:
        return f"{h}:00 AM"
    else:
        return f"{h-12}:00 PM"


async def _broadcast_loop(user_id: int, run_id: float):
    """Main background loop managing broadcast cycles and resting intervals."""
    logger.info(f"Starting broadcast loop for user {user_id} (Run ID: {run_id})")
    
    # Initialize heartbeat immediately
    active_heartbeats[user_id] = time.time()
    
    from app.services.channel_logger import get_bot
    bot = get_bot()

    if _worker_semaphore.locked():
        logger.info(f"User {user_id} queued due to worker concurrency limits.")
        if bot:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text="⏳ <b>Server Load High</b>\n\nYour broadcast is queued and will start automatically as soon as a slot becomes available.",
                    parse_mode="HTML"
                )
            except Exception:
                pass

    async with _worker_semaphore:
        user = await get_user(user_id)
        if not user or not user.get("session_encrypted"):
            await set_broadcasting(user_id, False)
            return

        client = None
        try:
            session = decrypt_session(user["session_encrypted"])
            client = await get_client_from_session(session, user_id)

            _setup_auto_responder(client, user_id)

            await log_broadcast_started(user_id, len(user.get("groups", [])), user.get("interval_seconds", MIN_INTERVAL))

            was_sleeping = False

            while True:
                # Fencing token check
                if active_run_ids.get(user_id) != run_id:
                    logger.info(f"Broadcast loop for user {user_id} with old Run ID {run_id} superseded. Exiting loop.")
                    break

                curr = await get_user(user_id)
                if not curr or not curr.get("session_encrypted") or not curr.get("groups"):
                    logger.info(f"Broadcast prerequisites missing for {user_id}. Halting autonomous loop.")
                    await set_broadcasting(user_id, False)
                    break

                if not curr.get("is_broadcasting"):
                    logger.info(f"Broadcast stopped by admin override for {user_id}.")
                    break

                # Check Auto Sleep Cycles
                now = datetime.now(_tz)
                sleep_cycle = _get_current_sleep_cycle(now.hour, curr)
                if sleep_cycle:
                    start_h, end_h = sleep_cycle
                    
                    # Notify the user once upon entering the sleep cycle
                    if not was_sleeping:
                        was_sleeping = True
                        logger.info(f"Auto Sleep Cycle ({start_h}:00-{end_h}:00) activated for {user_id}. Notifying user.")
                        if bot:
                            try:
                                await bot.send_message(
                                    chat_id=user_id,
                                    text=(
                                        f"💤 <b>Sleep Cycle Activated</b>\n\n"
                                        f"The broadcaster is now going to sleep from <b>{_format_hour(start_h)}</b> to <b>{_format_hour(end_h)}</b>.\n"
                                        f"Status: <b>Sleeping</b>. It will automatically resume after the sleep cycle ends."
                                    ),
                                    parse_mode="HTML"
                                )
                            except Exception as e:
                                logger.warning(f"Failed to notify user about sleep cycle: {e}")

                    if bot and curr.get("progress_chat_id") and curr.get("progress_message_id"):
                        try:
                            await bot.edit_message_text(
                                chat_id=curr["progress_chat_id"],
                                message_id=curr["progress_message_id"],
                                text=messages.sleep_mode_progress_text(start_h, end_h),
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            if "exactly the same" not in str(e).lower():
                                logger.warning(f"Failed to update sleep cycle progress: {e}")
                    
                    # Sleep for 60 seconds, then check again
                    for _ in range(60):
                        if active_run_ids.get(user_id) != run_id:
                            break
                        curr = await get_user(user_id)
                        if not curr or not curr.get("session_encrypted") or not curr.get("groups"):
                            break
                        if not curr.get("is_broadcasting"):
                            break
                        await asyncio.sleep(1)
                    continue
                else:
                    # Outside sleep hours, reset notification flag
                    was_sleeping = False

                if active_run_ids.get(user_id) != run_id:
                    break

                cycle_res = await _execute_cycle(user_id, client, bot, run_id)
                
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
                active = await _interruptible_sleep(interval, user_id, run_id)
                if not active:
                    break

        except ApiIdInvalidError as e:
            logger.error(f"Fatal API credentials error in loop for {user_id}: {e}")
            await set_broadcasting(user_id, False)
            await log_broadcast_error(user_id, "API credentials invalid")
            if bot:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=(
                            "⚠️ <b>Fatal Broadcast Error</b>\n\n"
                            "Your Telegram API credentials are invalid. "
                            "If you configured custom credentials, please verify or clear them in the account menu."
                        ),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
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
            # Only clean up if this loop execution is still the active one
            if active_run_ids.get(user_id) == run_id:
                if user_id in active_tasks:
                    del active_tasks[user_id]
                active_heartbeats.pop(user_id, None)
                active_run_ids.pop(user_id, None)
            logger.info(f"Broadcast loop terminated for user {user_id} (Run ID: {run_id})")


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

    run_id = time.time()
    active_run_ids[user_id] = run_id

    if user_id in active_tasks:
        old_task = active_tasks[user_id]
        if not old_task.done():
            old_task.cancel()
            logger.info(f"Cancelled old broadcast task for user {user_id} during start().")

    await set_broadcasting(user_id, True)

    task = asyncio.create_task(_broadcast_loop(user_id, run_id))
    active_tasks[user_id] = task

    return {"success": True, "total_groups": len(groups)}


async def stop(user_id: int) -> dict:
    """Stop the broadcast engine for a user."""
    await set_broadcasting(user_id, False)
    await clear_progress_message(user_id)

    # Wipe the run ID to prevent any ongoing sends immediately
    active_run_ids.pop(user_id, None)

    if user_id in active_tasks:
        task = active_tasks[user_id]
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=5.0)
        except Exception:
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
            run_id = time.time()
            active_run_ids[user_id] = run_id
            task = asyncio.create_task(_broadcast_loop(user_id, run_id))
            active_tasks[user_id] = task
            logger.info(f"Started autonomous broadcast for user {user_id}")
            # Stagger connections to prevent Telegram flood flags
            await asyncio.sleep(0.5)
        else:
            await set_broadcasting(user_id, False)

    await start_watchdog()
