"""
Broadcast service — Production-grade parallel sharding engine.

Features:
- Group Sharding: Distributes groups across active accounts to avoid duplicates.
- Parallel Execution: Runs all accounts simultaneously for maximum speed.
- Auto-Join Recovery: Attempts to join groups on 'Forbidden' errors.
- Account Health Tracking: Distinguishes between flood, auth, and permission errors.
- Structured Reporting: Sends detailed cycle summaries to the logs channel.
"""

import asyncio
import logging
import random
from datetime import datetime
from typing import Optional, List, Dict

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
    ACCOUNT_HEALTH_ACTIVE, ACCOUNT_HEALTH_LIMITED,
    ACCOUNT_HEALTH_FAILED, ACCOUNT_HEALTH_FORBIDDEN,
)
from app.database.models import (
    get_user, get_user_accounts, get_active_groups,
    increment_sent, increment_failed, update_user,
    update_account_status, update_group_sent,
    update_group_failed, disable_group, get_group_count,
    update_account_health, delete_group,
)
from app.services.encryption_service import decrypt_session
from app.services.telethon_service import get_client_from_session
from app.services.channel_logger import (
    log_broadcast_cycle, log_night_mode, log_error, log_message_sent
)
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


# ── ORCHESTRATOR ──

async def start_orchestrator():
    """Background task to auto-start/stop broadcasts based on user settings."""
    logger.info("System Orchestrator: ACTIVATED")
    while True:
        try:
            from app.database.mongo import get_db
            db = get_db()
            async for user_doc in db.users.find({}):
                user_id = user_doc["user_id"]
                
                # Check criteria for auto-start
                accounts = await get_user_accounts(user_id)
                active_accounts = [a for a in accounts if a.get("status") == ACCOUNT_HEALTH_ACTIVE]
                groups_count = await get_group_count(user_id)
                ads = user_doc.get("ads", [])
                
                should_run = len(active_accounts) > 0 and groups_count > 0 and len(ads) > 0
                
                if should_run and not is_broadcasting(user_id):
                    await start_broadcast(user_id)
                elif not should_run and is_broadcasting(user_id):
                    await stop_broadcast(user_id)
                    
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            
        await asyncio.sleep(60) # Scan every minute


async def start_broadcast(user_id: int) -> dict:
    """Start the parallel broadcast loop for a user."""
    user = await get_user(user_id)
    if not user: return {"success": False}
    
    interval = max(user.get("interval_seconds", MIN_INTERVAL), MIN_INTERVAL)
    await stop_broadcast(user_id)

    task = asyncio.create_task(_broadcast_loop(user_id, interval))
    _active_tasks[user_id] = task
    await update_user(user_id, ads_status="running")
    return {"success": True}


async def stop_broadcast(user_id: int) -> dict:
    """Stop the broadcast loop for a user."""
    task = _active_tasks.pop(user_id, None)
    if task and not task.done():
        task.cancel()
        try: await task
        except asyncio.CancelledError: pass
    await update_user(user_id, ads_status="paused")
    return {"success": True}


def get_active_broadcast_count() -> int:
    """Get count of currently active broadcasts."""
    return sum(1 for t in _active_tasks.values() if not t.done())


# ═══════════════════════════════════════════════════════════════════════════════
#  NIGHT MODE & UTILS
# ═══════════════════════════════════════════════════════════════════════════════

def _is_night_time() -> bool:
    if not NIGHT_MODE_ENABLED:
        return False
    now = datetime.now(_tz)
    return NIGHT_MODE_START_HOUR <= now.hour < NIGHT_MODE_END_HOUR


def _seconds_until_night_ends() -> int:
    now = datetime.now(_tz)
    end_today = now.replace(hour=NIGHT_MODE_END_HOUR, minute=0, second=0, microsecond=0)
    if now < end_today:
        return int((end_today - now).total_seconds())
    from datetime import timedelta
    end_tomorrow = end_today + timedelta(days=1)
    return int((end_tomorrow - now).total_seconds())


def _get_send_delay() -> float:
    jitter = random.uniform(SEND_JITTER_MIN, SEND_JITTER_MAX)
    return SEND_GAP_SECONDS + jitter


def _shard_groups(groups: List[Dict], n: int) -> List[List[Dict]]:
    """Split a list of groups into N shards for parallel processing."""
    if n <= 0: return []
    random.shuffle(groups)
    return [groups[i::n] for i in range(n)]


# ═══════════════════════════════════════════════════════════════════════════════
#  CORE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

async def _broadcast_loop(user_id: int, interval: int):
    """Orchestrator for parallel broadcast cycles."""
    try:
        while True:
            # ── Night Mode check ──
            if _is_night_time():
                wait = _seconds_until_night_ends()
                await update_user(user_id, night_mode_paused=True)
                await log_night_mode(user_id, "start")
                await asyncio.sleep(wait + 60)
                await update_user(user_id, night_mode_paused=False)
                await log_night_mode(user_id, "end")
                continue

            # ── State check ──
            user = await get_user(user_id)
            if not user or user.get("ads_status") != "running":
                break

            accounts = await get_user_accounts(user_id)
            active_accounts = [a for a in accounts if a.get("status") == ACCOUNT_HEALTH_ACTIVE]
            if not active_accounts:
                logger.warning(f"Engine halt for {user_id}: No active accounts left")
                await log_error(user_id, "Engine Halt", "No active accounts remaining.")
                break

            groups = await get_active_groups(user_id)
            if not groups:
                logger.warning(f"Engine halt for {user_id}: Target pool empty")
                break

            # ── Sharding & Parallel Tasks ──
            shards = _shard_groups(groups, len(active_accounts))
            tasks = []
            for i, account in enumerate(active_accounts):
                if i < len(shards) and shards[i]:
                    tasks.append(_run_account_task(user_id, account, shards[i], user))

            logger.info(f"Cycle started: {len(tasks)} parallel tasks for {user_id}")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate results
            cycle_sent = 0
            cycle_failed = 0
            for res in results:
                if isinstance(res, tuple):
                    s, f = res
                    cycle_sent += s
                    cycle_failed += f
                elif isinstance(res, Exception):
                    logger.error(f"Account task error: {res}")

            # Cycle complete report
            await log_broadcast_cycle(user_id, cycle_sent, cycle_failed)
            
            total_sleep = interval + random.uniform(60, 180)
            logger.info(f"Cycle complete for {user_id}: {cycle_sent} sent, {cycle_failed} failed. Next in {total_sleep:.0f}s")
            await asyncio.sleep(total_sleep)

    except asyncio.CancelledError:
        logger.info(f"Broadcast loop cancelled for {user_id}")
    except Exception as e:
        logger.error(f"Critical loop error for {user_id}: {e}", exc_info=True)
    finally:
        _active_tasks.pop(user_id, None)
        await update_user(user_id, ads_status="paused", night_mode_paused=False)


async def _run_account_task(user_id: int, account: dict, shard: List[dict], user: dict) -> tuple[int, int]:
    """Manages a single account's work within a cycle."""
    phone = account["phone_masked"]
    sent, failed = 0, 0
    
    try:
        session = decrypt_session(account["encrypted_session"])
        client = await get_client_from_session(session)
        
        try:
            await enforce_branding(client)
            
            for group in shard:
                if _is_night_time(): break
                
                success, error_msg = await _send_to_target(client, user_id, group, user, phone)
                if success:
                    sent += 1
                    await increment_sent(user_id)
                    await update_account_health(user_id, phone, 1)
                else:
                    failed += 1
                    await increment_failed(user_id)
                    await update_account_health(user_id, phone, -2)
                    
                    if "FloodWait" in (error_msg or ""):
                        # Adaptive Backoff: If account is flooding, take a longer pause
                        wait_time = int(error_msg.split("(")[1].split("s")[0]) if "(" in (error_msg or "") else 60
                        logger.warning(f"Adaptive Backoff for {phone}: Sleeping {wait_time}s")
                        await asyncio.sleep(min(wait_time + 10, 300)) # Max 5 min pause for account task
                    
                    if "Unauthorized" in (error_msg or "") or "Deactivated" in (error_msg or ""):
                        await update_account_status(user_id, phone, ACCOUNT_HEALTH_FAILED, error_msg)
                        return sent, failed

                # Smart delay between targets
                await asyncio.sleep(_get_send_delay())
                
        finally:
            await client.disconnect()
            
    except (AuthKeyUnregisteredError, UserDeactivatedBanError, ConnectionError) as e:
        logger.warning(f"Account {phone} failed: {type(e).__name__}")
        await update_account_status(user_id, phone, ACCOUNT_HEALTH_FAILED, str(e))
    except Exception as e:
        logger.error(f"Unexpected task error for {phone}: {e}")
        
    return sent, failed


async def _send_to_target(client, user_id: int, group: dict, user: dict, phone: str) -> tuple[bool, Optional[str]]:
    """Handles sending to a specific target with retry/recovery logic."""
    identifier = group.get("identifier", "")
    ads = user.get("ads", [])
    if not ads: return False, "No ads"
    
    # Handle multiple messages with gaps
    results = []
    for i, ad in enumerate(ads):
        try:
            # If multiple ads, add a gap between them for the same group
            if i > 0:
                inner_gap = random.uniform(30, 60)
                await asyncio.sleep(inner_gap)
            
            entity = await _resolve_entity_with_retry(client, group)
            if not entity:
                results.append(False)
                continue

            # Core Sending
            ad_mode = ad.get("ad_mode", "direct")
            if ad_mode == "forward" and ad.get("ad_forward_mid"):
                from app.config import BOT_USERNAME
                await client.forward_messages(entity, ad.get("ad_forward_mid"), BOT_USERNAME)
            elif ad.get("ad_media_type") in ("photo", "video") and ad.get("ad_media_file_id"):
                await client.send_file(entity, ad.get("ad_media_file_id"), caption=ad.get("ad_message") or "")
            else:
                await client.send_message(entity, ad.get("ad_message") or "Kurup Ads")

            results.append(True)
            await update_group_sent(user_id, identifier)
            await log_message_sent(user_id, identifier, phone, True)

        except FloodWaitError as e:
            logger.warning(f"FloodWait on {phone}: {e.seconds}s")
            await update_account_status(user_id, phone, ACCOUNT_HEALTH_LIMITED, f"FloodWait {e.seconds}s")
            return False, f"FloodWait ({e.seconds}s)"

        except (ChatWriteForbiddenError, UserBannedInChannelError):
            try:
                from telethon.tl.functions.channels import JoinChannelRequest
                await client(JoinChannelRequest(identifier))
                # Skip the inner gap for retry
                return await _send_to_target(client, user_id, group, user, phone)
            except Exception:
                await disable_group(user_id, identifier, "Forbidden (Auto-Cleaned)")
                await log_message_sent(user_id, identifier, phone, False, "Forbidden")
                return False, "Forbidden"

        except (ChannelPrivateError, ChatIdInvalidError, PeerIdInvalidError):
            await delete_group(user_id, identifier)
            return False, "Invalid Peer"

        except Exception as e:
            logger.error(f"Error sending ad to {identifier}: {e}")
            results.append(False)

    success = any(results)
    return success, None if success else "All ads failed"


async def _resolve_entity_with_retry(client, group: dict, retry: bool = True):
    """Robust entity resolution with join-on-demand logic."""
    identifier = group.get("identifier", "")
    link = group.get("link", "")
    link_type = group.get("link_type", "")
    
    try:
        # Try direct resolution
        if link_type == "username":
            return await client.get_entity(f"@{identifier}")
        return await client.get_entity(link)
    except Exception:
        if not retry: return None
        
        # Try joining
        try:
            from telethon.tl.functions.messages import ImportChatInviteRequest
            from telethon.tl.functions.channels import JoinChannelRequest
            
            if link_type == "invite":
                hash_val = identifier.split("+")[-1] if "+" in identifier else identifier
                if "joinchat/" in hash_val: hash_val = hash_val.split("/")[-1]
                await client(ImportChatInviteRequest(hash_val))
            else:
                await client(JoinChannelRequest(link))
            
            # Recursive call with retry=False to avoid infinite loops
            return await _resolve_entity_with_retry(client, group, retry=False)
        except Exception:
            return None
