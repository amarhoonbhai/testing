"""
Broadcast Engine — Smart batched sending algorithm.

In-process async engine that sends messages to groups with:
- Random delays between sends (mimics human behavior)
- Batch processing with gaps (prevents spam detection)
- Cycle intervals (configurable repeat period)
- FloodWait auto-backoff
- Auto-skip for repeatedly failing groups
- Auto-resume on bot restart
"""

import asyncio
import logging
import random
from datetime import datetime

from telethon.errors import (
    FloodWaitError,
    ChatWriteForbiddenError,
    UserBannedInChannelError,
    ChannelPrivateError,
    ChatIdInvalidError,
    PeerIdInvalidError,
    AuthKeyUnregisteredError,
    UserDeactivatedBanError,
    ChatAdminRequiredError,
    PeerFloodError,
    SlowModeWaitError,
    RPCError,
)

from app.config import (
    SEND_DELAY_MIN, SEND_DELAY_MAX,
    BATCH_SIZE, BATCH_GAP_MIN, BATCH_GAP_MAX,
    MAX_FAIL_SKIP,
)
from app.database.models import (
    get_user, set_broadcasting,
    increment_sent, increment_failed,
    increment_group_fail, reset_group_fail,
)
from app.services.encryption_service import decrypt_session
from app.services.telethon_service import get_client_from_session, send_message_to_entity
from app.services.channel_logger import (
    log_broadcast_started, log_broadcast_stopped,
    log_broadcast_cycle, log_error,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  BROADCAST ENGINE SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_active_tasks: dict[int, asyncio.Task] = {}  # user_id -> broadcast Task


def is_running(user_id: int) -> bool:
    """Check if a broadcast is currently running for a user."""
    task = _active_tasks.get(user_id)
    return task is not None and not task.done()


async def start(user_id: int) -> dict:
    """
    Start broadcasting for a user.
    Validates prerequisites and launches the async broadcast loop.
    """
    if is_running(user_id):
        return {"success": False, "error": "Broadcast is already running."}

    user = await get_user(user_id)
    if not user:
        return {"success": False, "error": "User not found."}

    if not user.get("session_encrypted"):
        return {"success": False, "error": "No account connected. Please connect your Telegram account first."}

    if not user.get("message"):
        return {"success": False, "error": "No message set. Please set your broadcast message first."}

    groups = user.get("groups", [])
    if not groups:
        return {"success": False, "error": "No groups added. Please add target groups first."}

    # Mark as broadcasting in DB
    await set_broadcasting(user_id, True)

    # Launch async task
    task = asyncio.create_task(_broadcast_loop(user_id))
    _active_tasks[user_id] = task

    # Log
    interval = user.get("interval_seconds", 1200)
    await log_broadcast_started(user_id, len(groups), interval)

    logger.info(f"Broadcast started for user {user_id} — {len(groups)} groups, {interval}s interval")
    return {"success": True, "total_groups": len(groups)}


async def stop(user_id: int) -> dict:
    """Stop broadcasting for a user."""
    # Cancel task if running
    task = _active_tasks.pop(user_id, None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # Update DB
    await set_broadcasting(user_id, False)
    await log_broadcast_stopped(user_id)

    logger.info(f"Broadcast stopped for user {user_id}")
    return {"success": True}


async def auto_resume():
    """
    Called on bot startup.
    Resumes broadcasting for all users who were active before shutdown.
    """
    from app.database.models import get_broadcasting_users

    users = await get_broadcasting_users()
    if not users:
        logger.info("Auto-resume: No active broadcasts to resume.")
        return

    logger.info(f"Auto-resume: Resuming {len(users)} active broadcast(s)...")

    for user in users:
        user_id = user["telegram_user_id"]
        try:
            # Validate the user still has everything needed
            if not user.get("session_encrypted") or not user.get("message") or not user.get("groups"):
                await set_broadcasting(user_id, False)
                logger.warning(f"Auto-resume skipped for {user_id}: missing prerequisites")
                continue

            task = asyncio.create_task(_broadcast_loop(user_id))
            _active_tasks[user_id] = task
            logger.info(f"Auto-resumed broadcast for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to auto-resume for {user_id}: {e}")
            await set_broadcasting(user_id, False)


# ═══════════════════════════════════════════════════════════════════════════════
#  CORE BROADCAST LOOP
# ═══════════════════════════════════════════════════════════════════════════════

async def _broadcast_loop(user_id: int):
    """
    Main broadcast loop with smart batched sending.

    Algorithm:
    1. Shuffle groups (randomize order each cycle)
    2. Split into batches of BATCH_SIZE
    3. Send to each group in batch with random SEND_DELAY
    4. After each batch, pause for BATCH_GAP
    5. After all groups, wait for INTERVAL before next cycle
    6. Handle FloodWait/errors gracefully
    7. Auto-skip groups that fail MAX_FAIL_SKIP times
    """
    logger.info(f"[{user_id}] Broadcast loop started")

    try:
        while True:
            # Re-fetch user data each cycle (message/groups/interval may change)
            user = await get_user(user_id)
            if not user or not user.get("is_broadcasting"):
                logger.info(f"[{user_id}] Broadcast stopped (user state changed)")
                break

            session_encrypted = user.get("session_encrypted")
            message = user.get("message")
            groups = list(user.get("groups", []))
            group_fails = user.get("group_fails", {})
            interval = user.get("interval_seconds", 1200)

            if not session_encrypted or not message or not groups:
                logger.warning(f"[{user_id}] Missing prerequisites, stopping broadcast")
                break

            # ── Connect Telethon client for this cycle ──
            client = None
            try:
                session = decrypt_session(session_encrypted)
                client = await get_client_from_session(session)
            except (AuthKeyUnregisteredError, UserDeactivatedBanError, ConnectionError) as e:
                logger.error(f"[{user_id}] Session failure: {type(e).__name__}")
                await log_error(user_id, "Session Failure", str(e))
                break
            except Exception as e:
                logger.error(f"[{user_id}] Connection error: {e}")
                await log_error(user_id, "Connection Error", str(e))
                # Wait and retry instead of breaking
                await asyncio.sleep(60)
                continue

            try:
                # ── Execute one broadcast cycle ──
                progress_chat_id = user.get("progress_chat_id")
                progress_message_id = user.get("progress_message_id")
                
                sent, failed, skipped = await _execute_cycle(
                    client, user_id, message, groups, group_fails,
                    progress_chat_id=progress_chat_id,
                    progress_message_id=progress_message_id
                )

                # Log cycle results
                await log_broadcast_cycle(user_id, sent, failed, skipped)
                logger.info(
                    f"[{user_id}] Cycle complete: {sent} sent, {failed} failed, {skipped} skipped"
                )

            except asyncio.CancelledError:
                raise  # Propagate cancellation
            except Exception as e:
                logger.error(f"[{user_id}] Cycle error: {e}", exc_info=True)
            finally:
                # Always disconnect after cycle
                if client:
                    try:
                        await client.disconnect()
                    except Exception:
                        pass

            # ── Wait for interval before next cycle ──
            logger.info(f"[{user_id}] Waiting {interval}s before next cycle...")
            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        logger.info(f"[{user_id}] Broadcast loop cancelled")
    except Exception as e:
        logger.error(f"[{user_id}] Broadcast loop crashed: {e}", exc_info=True)
    finally:
        # Cleanup
        await set_broadcasting(user_id, False)
        _active_tasks.pop(user_id, None)
        logger.info(f"[{user_id}] Broadcast loop ended")


async def _execute_cycle(
    client, user_id: int, message: dict, groups: list[str], group_fails: dict,
    progress_chat_id: int = None, progress_message_id: int = None
) -> tuple[int, int, int]:
    """
    Execute one broadcast cycle across all groups.
    Updates the live progress message.
    """
    import time
    from app.bot import messages
    from app.services.channel_logger import _bot as telegram_bot

    sent = 0
    failed = 0
    skipped = 0
    total = len(groups)
    start_time = time.time()
    last_update_time = start_time
    last_update_count = 0

    # Step 1: Shuffle groups for randomization
    random.shuffle(groups)

    # Step 2: Filter out groups that have failed too many times
    active_groups = []
    for group in groups:
        safe_key = group.replace(".", "_DOT_").replace("$", "_DOLLAR_")
        fail_count = group_fails.get(safe_key, 0)
        if fail_count >= MAX_FAIL_SKIP:
            skipped += 1
        else:
            active_groups.append(group)

    if not active_groups:
        logger.warning(f"[{user_id}] All groups skipped (too many failures)")
        return sent, failed, skipped

    # Step 3: Split into batches
    batches = [
        active_groups[i:i + BATCH_SIZE]
        for i in range(0, len(active_groups), BATCH_SIZE)
    ]

    async def _update_progress():
        if telegram_bot and progress_chat_id and progress_message_id:
            try:
                await telegram_bot.edit_message_text(
                    chat_id=progress_chat_id,
                    message_id=progress_message_id,
                    text=messages.broadcast_progress_text(sent, failed, skipped, total),
                    parse_mode="HTML"
                )
            except Exception:
                pass

    for batch_idx, batch in enumerate(batches):
        for group_link in batch:
            result = {"success": False, "target": group_link, "error_type": None, "error_message": None, "skipped": False}
            try:
                # Resolve entity
                entity = await _resolve_group(client, group_link)
                if not entity:
                    result["error_type"] = "ResolveError"
                    result["error_message"] = "Could not resolve entity"
                    failed += 1
                    await increment_failed(user_id)
                    await increment_group_fail(user_id, group_link)
                else:
                    # Send message
                    res = await send_message_to_entity(
                        client, entity,
                        text=message.get("text"),
                        media_type=message.get("media_type"),
                        media_path=message.get("media_path"),
                    )
                    sent += 1
                    await increment_sent(user_id)
                    await reset_group_fail(user_id, group_link)
                    result = res

            except FloodWaitError as e:
                logger.warning(f"[{user_id}] FloodWait: {e.seconds}s — sleeping...")
                await asyncio.sleep(e.seconds + 30)
                # Retry this group after wait
                try:
                    entity = await _resolve_group(client, group_link)
                    if entity:
                        res = await send_message_to_entity(
                            client, entity,
                            text=message.get("text"),
                            media_type=message.get("media_type"),
                            media_path=message.get("media_path"),
                        )
                        sent += 1
                        await increment_sent(user_id)
                        await reset_group_fail(user_id, group_link)
                        result = res
                    else:
                        failed += 1
                        await increment_failed(user_id)
                        result["error_type"] = "ResolveError"
                except Exception as ex:
                    failed += 1
                    await increment_failed(user_id)
                    await increment_group_fail(user_id, group_link)
                    result["error_type"] = type(ex).__name__
                    result["error_message"] = str(ex)

            except SlowModeWaitError as e:
                logger.info(f"[{user_id}] SlowMode on {group_link}: {e.seconds}s — skipping")
                skipped += 1
                result["skipped"] = True
                result["error_type"] = "SlowMode"
                result["error_message"] = f"Wait {e.seconds}s"

            except (ChatWriteForbiddenError, UserBannedInChannelError,
                    ChatAdminRequiredError) as e:
                logger.info(f"[{user_id}] Permission denied: {group_link}")
                failed += 1
                await increment_failed(user_id)
                await increment_group_fail(user_id, group_link)
                result["error_type"] = "PermissionError"
                result["error_message"] = type(e).__name__

            except (ChannelPrivateError, ChatIdInvalidError, PeerIdInvalidError) as e:
                logger.info(f"[{user_id}] Invalid/private group: {group_link}")
                failed += 1
                await increment_failed(user_id)
                await increment_group_fail(user_id, group_link)
                result["error_type"] = "InvalidGroup"
                result["error_message"] = type(e).__name__

            except PeerFloodError:
                logger.warning(f"[{user_id}] PeerFlood — pausing 5 minutes")
                await asyncio.sleep(300)
                failed += 1
                await increment_failed(user_id)
                result["error_type"] = "PeerFloodError"

            except RPCError as e:
                logger.warning(f"[{user_id}] RPC error on {group_link}: {e}")
                failed += 1
                await increment_failed(user_id)
                await increment_group_fail(user_id, group_link)
                result["error_type"] = "RPCError"
                result["error_message"] = str(e)

            except Exception as e:
                logger.error(f"[{user_id}] Unexpected error on {group_link}: {e}")
                failed += 1
                await increment_failed(user_id)
                await increment_group_fail(user_id, group_link)
                result["error_type"] = type(e).__name__
                result["error_message"] = str(e)
                
            # Log failure if any
            if not result.get("success") and not result.get("skipped"):
                from app.services.channel_logger import log_send_failed
                await log_send_failed(user_id, group_link, result.get("error_type", "Error"), result.get("error_message", ""))

            # ── Check if we should update progress ──
            current = sent + failed + skipped
            current_time = time.time()
            if (current - last_update_count >= 10) or (current_time - last_update_time >= 30):
                await _update_progress()
                last_update_count = current
                last_update_time = current_time

            # ── Send delay between individual messages ──
            delay = random.uniform(SEND_DELAY_MIN, SEND_DELAY_MAX)
            await asyncio.sleep(delay)

        # ── Batch gap after each batch ──
        if batch_idx < len(batches) - 1:  # Don't gap after last batch
            gap = random.uniform(BATCH_GAP_MIN, BATCH_GAP_MAX)
            logger.info(f"[{user_id}] Batch {batch_idx + 1}/{len(batches)} done — gap {gap:.0f}s")
            await asyncio.sleep(gap)
            
    # Final progress update
    await _update_progress()

    return sent, failed, skipped


async def _resolve_group(client, group_link: str):
    """
    Resolve a group link to a Telethon entity.

    Supports:
    - @username
    - https://t.me/username
    - https://t.me/+inviteHash
    - https://t.me/c/chatid
    """
    import re

    try:
        # Direct @username
        if group_link.startswith("@"):
            return await client.get_entity(group_link)

        # t.me/c/12345 (private by numeric ID)
        m = re.match(r"https?://t\.me/c/(\d+)$", group_link)
        if m:
            numeric_id = int(f"-100{m.group(1)}")
            return await client.get_entity(numeric_id)

        # t.me/username or t.me/+hash or any other link
        return await client.get_entity(group_link)

    except Exception as e:
        logger.debug(f"Failed to resolve {group_link}: {type(e).__name__}")
        return None
