"""
Broadcast service — Production-grade ad broadcasting engine.

Features:
- Night mode: Auto-pause 12:00 AM – 5:00 AM IST, auto-restart after
- Group-based targeting: Sends only to user-configured groups
- Smart delays: 300s gap between sends + random jitter (30-90s)
- Anti-freeze: Exponential backoff on FloodWait, max consecutive error limit
- Per-user asyncio tasks with clean lifecycle management

SAFETY:
- Min 1200s (20 min) between broadcast cycles
- 300s + jitter between individual message sends
- Auto-pause on excessive errors
- Respects Telegram FloodWait headers
"""

import asyncio
import logging
import random
from datetime import datetime
from typing import Optional

import pytz
from telethon.errors import (
    FloodWaitError,
    ChatWriteForbiddenError,
    ChannelPrivateError,
    UserBannedInChannelError,
    SlowModeWaitError,
    ChatIdInvalidError,
    PeerIdInvalidError,
    UserDeactivatedBanError,
    AuthKeyUnregisteredError,
)

from app.config import (
    SEND_GAP_SECONDS, SEND_JITTER_MIN, SEND_JITTER_MAX,
    MIN_INTERVAL, FLOOD_BACKOFF_BASE, FLOOD_BACKOFF_MAX,
    MAX_CONSECUTIVE_ERRORS, NIGHT_MODE_ENABLED,
    NIGHT_MODE_START_HOUR, NIGHT_MODE_END_HOUR, TIMEZONE,
)
from app.database.models import (
    get_user, get_user_accounts, get_active_groups,
    increment_sent, increment_failed, update_user,
    update_account_status, update_group_sent,
    update_group_failed, disable_group, get_group_count,
)
from app.services.encryption_service import decrypt_session
from app.services.telethon_service import get_client_from_session
from app.services.channel_logger import log_broadcast_cycle, log_night_mode, log_error
from app.services.branding_service import enforce_branding

logger = logging.getLogger(__name__)

# Active broadcast tasks: {user_id: asyncio.Task}
_active_tasks: dict[int, asyncio.Task] = {}

_tz = pytz.timezone(TIMEZONE)


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def is_broadcasting(user_id: int) -> bool:
    """Check if a user has an active broadcast task."""
    task = _active_tasks.get(user_id)
    return task is not None and not task.done()


async def start_broadcast(user_id: int) -> dict:
    """Start the broadcast loop for a user. Returns success/error dict."""
    user = await get_user(user_id)
    if not user:
        return {"success": False, "error": "User not found."}

    if not user.get("ad_message") and not user.get("ad_media_file_id"):
        return {"success": False, "error": "No ad message set. Set one first."}

    accounts = await get_user_accounts(user_id)
    if not accounts:
        return {"success": False, "error": "No hosted accounts. Add one first."}

    active_accounts = [a for a in accounts if a.get("status") == "active"]
    if not active_accounts:
        return {"success": False, "error": "No active accounts available."}

    group_count = await get_group_count(user_id)
    if group_count == 0:
        return {"success": False, "error": "No groups added. Add groups first."}

    interval = max(user.get("interval_seconds", MIN_INTERVAL), MIN_INTERVAL)

    # Stop existing task if any
    await stop_broadcast(user_id)

    # Create and start new task
    task = asyncio.create_task(_broadcast_loop(user_id, interval))
    _active_tasks[user_id] = task

    await update_user(user_id, ads_status="running")
    logger.info(f"Broadcast started for user {user_id} (interval={interval}s)")

    return {"success": True, "error": None}


async def stop_broadcast(user_id: int) -> dict:
    """Stop the broadcast loop for a user."""
    task = _active_tasks.pop(user_id, None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await update_user(user_id, ads_status="paused")
    logger.info(f"Broadcast stopped for user {user_id}")
    return {"success": True}


def get_active_broadcast_count() -> int:
    """Get count of currently active broadcasts."""
    return sum(1 for t in _active_tasks.values() if not t.done())


# ═══════════════════════════════════════════════════════════════════════════════
#  NIGHT MODE
# ═══════════════════════════════════════════════════════════════════════════════

def _is_night_time() -> bool:
    """Check if current time is within night mode window (IST)."""
    if not NIGHT_MODE_ENABLED:
        return False
    now = datetime.now(_tz)
    return NIGHT_MODE_START_HOUR <= now.hour < NIGHT_MODE_END_HOUR


def _seconds_until_night_ends() -> int:
    """Calculate seconds until night mode ends."""
    now = datetime.now(_tz)
    end_today = now.replace(
        hour=NIGHT_MODE_END_HOUR, minute=0, second=0, microsecond=0
    )
    if now < end_today:
        return int((end_today - now).total_seconds())
    # Already past end hour today — night ends tomorrow
    from datetime import timedelta
    end_tomorrow = end_today + timedelta(days=1)
    return int((end_tomorrow - now).total_seconds())


# ═══════════════════════════════════════════════════════════════════════════════
#  SMART DELAY
# ═══════════════════════════════════════════════════════════════════════════════

def _get_send_delay() -> float:
    """Get delay between individual sends: base gap + random jitter."""
    jitter = random.uniform(SEND_JITTER_MIN, SEND_JITTER_MAX)
    return SEND_GAP_SECONDS + jitter


def _get_backoff_delay(consecutive_errors: int) -> float:
    """Exponential backoff: base * 2^errors, capped at max."""
    delay = FLOOD_BACKOFF_BASE * (2 ** min(consecutive_errors, 6))
    return min(delay, FLOOD_BACKOFF_MAX)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN BROADCAST LOOP
# ═══════════════════════════════════════════════════════════════════════════════

async def _broadcast_loop(user_id: int, interval: int):
    """
    Main broadcast loop with night mode and safety controls.

    Flow per cycle:
    1. Check night mode → sleep until morning if active
    2. Get user's active accounts and target groups
    3. For each account, send ad to each group with smart delays
    4. Sleep for configured interval + jitter before next cycle
    """
    consecutive_errors = 0

    try:
        while True:
            try:
                # ── Night Mode Check ─────────────────────────────
                if _is_night_time():
                    wait_secs = _seconds_until_night_ends()
                    logger.info(
                        f"Night mode active for user {user_id}, "
                        f"sleeping {wait_secs}s until morning"
                    )
                    await update_user(user_id, night_mode_paused=True)
                    await log_night_mode(user_id, "start")
                    await asyncio.sleep(wait_secs + 60)  # +60s buffer
                    await update_user(user_id, night_mode_paused=False)
                    await log_night_mode(user_id, "end")
                    logger.info(f"Night mode ended for user {user_id}, resuming")
                    continue

                # ── Validate user state ──────────────────────────
                user = await get_user(user_id)
                if not user or user.get("ads_status") != "running":
                    break

                ad_message = user.get("ad_message")
                ad_media_type = user.get("ad_media_type")
                ad_media_file_id = user.get("ad_media_file_id")

                accounts = await get_user_accounts(user_id)
                active_accounts = [
                    a for a in accounts if a.get("status") == "active"
                ]
                if not active_accounts:
                    logger.warning(f"No active accounts for user {user_id}")
                    break

                groups = await get_active_groups(user_id)
                if not groups:
                    logger.warning(f"No active groups for user {user_id}")
                    break

                # ── Send to groups using accounts ────────────────
                cycle_sent = 0
                cycle_failed = 0

                for account in active_accounts:
                    try:
                        session_str = decrypt_session(
                            account["encrypted_session"]
                        )
                        client = await get_client_from_session(session_str)

                        try:
                            # Re-enforce branding each cycle
                            await enforce_branding(client)

                            sent, failed = await _send_to_groups(
                                client, user_id, groups,
                                ad_message, ad_media_type, ad_media_file_id,
                            )
                            cycle_sent += sent
                            cycle_failed += failed
                            consecutive_errors = 0  # Reset on success
                        finally:
                            await client.disconnect()

                    except (ConnectionError, UserDeactivatedBanError,
                            AuthKeyUnregisteredError):
                        logger.warning(
                            f"Session dead for {account['phone_masked']}"
                        )
                        await update_account_status(
                            user_id, account["phone_masked"], "error"
                        )
                        consecutive_errors += 1
                    except Exception:
                        logger.error(
                            f"Account error: {account['phone_masked']}",
                            exc_info=True,
                        )
                        consecutive_errors += 1

                # ── Safety: too many consecutive errors → pause ──
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.warning(
                        f"Too many errors ({consecutive_errors}) for "
                        f"user {user_id}, auto-pausing"
                    )
                    await log_error(user_id, "Auto-Pause", f"Reached {consecutive_errors} consecutive account errors.")
                    break

                # Send live update to channel
                await log_broadcast_cycle(user_id, cycle_sent, cycle_failed)

                cycle_jitter = random.uniform(60, 180)
                total_sleep = interval + cycle_jitter
                logger.info(
                    f"Cycle done for user {user_id}: "
                    f"sent={cycle_sent} failed={cycle_failed} "
                    f"sleeping {total_sleep:.0f}s"
                )
                await log_broadcast_cycle(user_id, cycle_sent, cycle_failed)
                await asyncio.sleep(total_sleep)

            except asyncio.CancelledError:
                raise
            except Exception:
                consecutive_errors += 1
                backoff = _get_backoff_delay(consecutive_errors)
                logger.error(
                    f"Loop error for user {user_id}, "
                    f"backoff {backoff:.0f}s (errors={consecutive_errors})",
                    exc_info=True,
                )
                await asyncio.sleep(backoff)

    except asyncio.CancelledError:
        logger.info(f"Broadcast cancelled for user {user_id}")
    finally:
        _active_tasks.pop(user_id, None)
        await update_user(user_id, ads_status="paused", night_mode_paused=False)


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUP-BASED SENDING
# ═══════════════════════════════════════════════════════════════════════════════

async def _send_to_groups(
    client,
    user_id: int,
    groups: list[dict],
    ad_message: Optional[str],
    ad_media_type: Optional[str],
    ad_media_file_id: Optional[str],
) -> tuple[int, int]:
    """
    Send ad to target groups with smart delays.
    Returns (sent_count, failed_count).
    """
    sent = 0
    failed = 0

    for group in groups:
        # Night mode check mid-cycle
        if _is_night_time():
            logger.info("Night mode hit mid-cycle, stopping sends")
            break

        identifier = group.get("identifier", "")
        link_type = group.get("link_type", "")

        try:
            # Resolve the entity
            entity = await _resolve_entity(client, group)
            if entity is None:
                failed += 1
                await update_group_failed(user_id, identifier)
                continue

            # Send the message
            if ad_media_type in ("photo", "video") and ad_media_file_id:
                await client.send_file(
                    entity,
                    ad_media_file_id,
                    caption=ad_message or "",
                )
            elif ad_message:
                await client.send_message(entity, ad_message)
            else:
                continue

            sent += 1
            await increment_sent(user_id)
            await update_group_sent(user_id, identifier)
            logger.info(f"Sent to {identifier}")

            # ── Smart delay between sends ────────────────────
            delay = _get_send_delay()
            await asyncio.sleep(delay)

        except FloodWaitError as e:
            wait = min(e.seconds + 30, FLOOD_BACKOFF_MAX)
            logger.warning(f"FloodWait {e.seconds}s for {identifier}")
            await asyncio.sleep(wait)
            failed += 1
        except SlowModeWaitError as e:
            logger.info(f"SlowMode {e.seconds}s in {identifier}")
            await asyncio.sleep(e.seconds + 10)
            failed += 1
        except (ChatWriteForbiddenError, UserBannedInChannelError):
            logger.info(f"Cannot post in {identifier} — disabling")
            await disable_group(user_id, identifier, "write_forbidden")
            await increment_failed(user_id)
            failed += 1
        except (ChannelPrivateError, ChatIdInvalidError, PeerIdInvalidError):
            logger.info(f"Invalid/private group {identifier} — disabling")
            await disable_group(user_id, identifier, "invalid_or_private")
            await increment_failed(user_id)
            failed += 1
        except Exception as e:
            logger.error(f"Send error for {identifier}: {type(e).__name__}")
            await update_group_failed(user_id, identifier)
            await increment_failed(user_id)
            failed += 1

    return sent, failed


async def _resolve_entity(client, group: dict):
    """Resolve a group dict to a Telethon entity."""
    link_type = group.get("link_type", "")
    identifier = group.get("identifier", "")
    link = group.get("link", "")

    try:
        if link_type == "username":
            return await client.get_entity(f"@{identifier}")
        elif link_type == "invite":
            # For invite links, try to get entity from link
            return await client.get_entity(link)
        elif link_type == "folder":
            # Folder links need special handling — join via folder
            # then iterate dialogs to find new groups
            return None  # Handled separately by folder joining
        else:
            return await client.get_entity(link)
    except Exception as e:
        logger.warning(f"Cannot resolve {identifier}: {type(e).__name__}")
        return None
