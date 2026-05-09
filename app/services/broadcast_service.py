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
    # Immediate scan on startup
    await asyncio.sleep(5)
    
    while True:
        try:
            from app.database.mongo import get_db
            db = get_db()
            async for user_doc in db.users.find({}):
                user_id = user_doc["telegram_user_id"]
                
                # Check criteria for auto-start
                accounts = await get_user_accounts(user_id)
                active_accounts = [a for a in accounts if a.get("status") == ACCOUNT_HEALTH_ACTIVE]
                groups_count = await get_group_count(user_id)
                ads = user_doc.get("ads", [])
                
                should_run = (
                    len(active_accounts) > 0 and 
                    groups_count > 0 and 
                    len(ads) > 0
                )
                
                is_running = is_broadcasting(user_id)
                
                if should_run and not is_running:
                    logger.info(f"Orchestrator: Auto-activating engine for {user_id} (Requirements met)")
                    await start_broadcast(user_id)
                elif not should_run and is_running:
                    logger.info(f"Orchestrator: Auto-halting engine for {user_id} (Requirements lost)")
                    await stop_broadcast(user_id)
                    
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            # New: Report orchestrator errors to channel
            await log_error(0, "Orchestrator Failure", str(e))
            
        await asyncio.sleep(30) # Scan every 30 seconds


async def start_broadcast(user_id: int) -> dict:
    """Start the parallel broadcast loop for a user."""
    user = await get_user(user_id)
    if not user: return {"success": False, "error": "User not found."}
    
    accounts = await get_user_accounts(user_id)
    active_accounts = [a for a in accounts if a.get("status") == ACCOUNT_HEALTH_ACTIVE]
    if not active_accounts:
        return {"success": False, "error": "No active accounts linked."}
        
    if await get_group_count(user_id) == 0:
        return {"success": False, "error": "No target groups added."}
        
    if not user.get("ads"):
        return {"success": False, "error": "No ads configured."}

    interval = max(user.get("interval_seconds", MIN_INTERVAL), MIN_INTERVAL)
    await stop_broadcast(user_id)

    # Update status BEFORE starting task to avoid race condition
    await update_user(user_id, ads_status="running")
    
    task = asyncio.create_task(_broadcast_loop(user_id, interval))
    _active_tasks[user_id] = task
    
    logger.info(f"Broadcast engine started for {user_id}")
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


async def _interruptible_sleep(seconds: float, user_id: int) -> bool:
    """
    Sleep for N seconds while periodically checking if the broadcast was stopped.
    Returns True if sleep completed, False if broadcast was stopped/paused.
    """
    for _ in range(0, int(seconds), 2):
        try:
            user = await get_user(user_id)
            if not user:
                # If user doc is missing temporarily, don't kill the engine
                await asyncio.sleep(2)
                continue
                
            if user.get("ads_status") != "running":
                return False
        except Exception as e:
            logger.warning(f"DB check failed in sleep for {user_id}: {e}")
            
        await asyncio.sleep(2)
    return True


# ═══════════════════════════════════════════════════════════════════════════════
#  CORE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

async def _broadcast_loop(user_id: int, interval: int):
    """Orchestrator for parallel broadcast cycles."""
    try:
        while True:
            logger.info(f"Starting new broadcast cycle for user {user_id}")
            
            # Auto-check requirements instead of just status
            accounts = await get_user_accounts(user_id)
            active_accounts = [a for a in accounts if a.get("status") == ACCOUNT_HEALTH_ACTIVE]
            groups_count = await get_group_count(user_id)
            user = await get_user(user_id)
            ads = user.get("ads", []) if user else []

            if not active_accounts or groups_count == 0 or not ads:
                logger.info(f"Broadcast loop for {user_id} terminating: Requirements no longer met")
                await update_user(user_id, ads_status="paused")
                break

            # ── Night Mode check ──
            if _is_night_time():
                wait = _seconds_until_night_ends()
                await update_user(user_id, night_mode_paused=True)
                await log_night_mode(user_id, "start")
                await asyncio.sleep(wait + 60)
                await update_user(user_id, night_mode_paused=False)
                await log_night_mode(user_id, "end")
                continue

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
        # New: Report critical loop failures
        await log_error(user_id, "Critical Engine Error", str(e))
    finally:
        _active_tasks.pop(user_id, None)
        await update_user(user_id, ads_status="paused", night_mode_paused=False)


async def _run_account_task(user_id: int, account: dict, shard: List[dict], user: dict) -> tuple[int, int]:
    """Manages a single account's work within a cycle."""
    phone = account["phone_masked"]
    sent, failed = 0, 0
    client = None
    
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
                    
                    # New: Update group state on failure if not already handled
                    await update_group_failed(user_id, group.get("identifier"), numeric_id=group.get("numeric_id"))
                    
                    if "FloodWait" in (error_msg or ""):
                        # Adaptive Backoff: If account is flooding, take a longer pause
                        wait_time = int(error_msg.split("(")[1].split("s")[0]) if "(" in (error_msg or "") else 60
                        logger.warning(f"Adaptive Backoff for {phone}: Sleeping {wait_time}s")
                        # Adaptive backoff is also interruptible
                        if not await _interruptible_sleep(min(wait_time + 10, 300), user_id):
                            return sent, failed
                    
                    if "Unauthorized" in (error_msg or "") or "Deactivated" in (error_msg or ""):
                        await update_account_status(user_id, phone, ACCOUNT_HEALTH_FAILED, error_msg)
                        return sent, failed

                # Smart delay between targets (Interruptible)
                if not await _interruptible_sleep(_get_send_delay(), user_id):
                    logger.info(f"Account task {phone} detected STOP signal during delay. Aborting.")
                    return sent, failed
                
        finally:
            if client:
                await client.disconnect()
            
    except (AuthKeyUnregisteredError, UserDeactivatedBanError, ConnectionError) as e:
        logger.warning(f"Account {phone} failed: {type(e).__name__}")
        await update_account_status(user_id, phone, ACCOUNT_HEALTH_FAILED, str(e))
        # New: Report account loss to channel
        await log_error(user_id, "Account Failure", f"Phone: {phone}\nReason: {type(e).__name__}")
    except Exception as e:
        logger.error(f"Unexpected task error for {phone}: {e}")
        await log_error(user_id, "Task Exception", f"Phone: {phone}\nError: {str(e)}")
        
    return sent, failed


async def _send_to_target(client, user_id: int, group: dict, user: dict, phone: str, is_retry: bool = False) -> tuple[bool, Optional[str]]:
    """Handles sending to a specific target with retry/recovery logic."""
    identifier = group.get("identifier", "")
    numeric_id = group.get("numeric_id")
    ads = user.get("ads", [])
    if not ads: return False, "No ads"
    
    # Handle multiple messages with gaps
    results = []
    for i, ad in enumerate(ads):
        try:
            # If multiple ads, add a gap between them for the same group
            if i > 0:
                # Synchronize inner gap with the requested 7-min message gap
                inner_gap = SEND_GAP_SECONDS + random.uniform(SEND_JITTER_MIN, SEND_JITTER_MAX)
                if not await _interruptible_sleep(inner_gap, user_id):
                    return False, "Stopped"
            
            entity = await _resolve_entity_with_retry(client, group)
            if not entity:
                logger.warning(f"Could not resolve target {identifier}")
                # New: Report resolution failure to channel
                await log_message_sent(user_id, identifier, phone, False, "Resolution Failed")
                results.append(False)
                continue

            # Core Sending
            ad_mode = ad.get("ad_mode", "direct")
            topic_id = group.get("topic_id")
            
            send_kwargs = {}
            if topic_id:
                send_kwargs["reply_to"] = topic_id

            if ad_mode == "forward" and ad.get("ad_forward_mid"):
                from app.config import BOT_USERNAME
                try:
                    await client.forward_messages(entity, ad.get("ad_forward_mid"), BOT_USERNAME, **send_kwargs)
                except Exception:
                    # Fallback: try forwarding from the entity directly if it was a user message
                    await client.forward_messages(entity, ad.get("ad_forward_mid"), user_id, **send_kwargs)
            elif ad.get("ad_media_type") in ("photo", "video") and ad.get("ad_media_file_id"):
                await client.send_file(entity, ad.get("ad_media_file_id"), caption=ad.get("ad_message") or "", **send_kwargs)
            else:
                await client.send_message(entity, ad.get("ad_message") or "Kurup Ads", **send_kwargs)

            results.append(True)
            await update_group_sent(user_id, identifier, numeric_id=numeric_id)
            await log_message_sent(user_id, identifier, phone, True)

        except FloodWaitError as e:
            logger.warning(f"FloodWait on {phone}: {e.seconds}s")
            await update_account_status(user_id, phone, ACCOUNT_HEALTH_LIMITED, f"FloodWait {e.seconds}s")
            return False, f"FloodWait ({e.seconds}s)"

        except SlowModeWaitError as e:
            logger.warning(f"SlowMode on {identifier}: {e.seconds}s")
            await asyncio.sleep(e.seconds)
            # Retry immediately for this specific ad
            return await _send_to_target(client, user_id, group, user, phone, is_retry=True)

        except (ChatWriteForbiddenError, UserBannedInChannelError):
            # Check if we are actually in the group
            try:
                from telethon.tl.functions.channels import GetParticipantRequest
                from telethon.tl.types import ChannelParticipantSelf
                me = await client(GetParticipantRequest(entity, 'me'))
                is_member = isinstance(me.participant, ChannelParticipantSelf)
            except Exception:
                is_member = False

            if is_member:
                # We are in, but forbidden -> Muted or Restricted
                await disable_group(user_id, identifier, "Muted/No-Post-Perm", numeric_id=numeric_id)
                await log_message_sent(user_id, identifier, phone, False, "Muted (In Group)")
                return False, "Muted"

            if is_retry:
                # Already tried joining/retrying, still forbidden
                await disable_group(user_id, identifier, "Forbidden (Permanently)", numeric_id=numeric_id)
                await log_message_sent(user_id, identifier, phone, False, "Forbidden")
                return False, "Forbidden"
                
            try:
                from telethon.tl.functions.channels import JoinChannelRequest
                # Try joining by entity instead of link to be more robust
                await client(JoinChannelRequest(entity))
                # Retry once after joining
                return await _send_to_target(client, user_id, group, user, phone, is_retry=True)
            except Exception as e:
                logger.warning(f"Join failed for {identifier}: {e}")
                await disable_group(user_id, identifier, f"Join Failed ({type(e).__name__})", numeric_id=numeric_id)
                await log_message_sent(user_id, identifier, phone, False, "Join Failed")
                return False, "Join Failed"

        except (ChannelPrivateError, ChatIdInvalidError, PeerIdInvalidError):
            await delete_group(user_id, identifier)
            return False, "Invalid Peer"

        except Exception as e:
            logger.error(f"Error sending ad to {identifier}: {e}")
            results.append(False)
            await update_group_failed(user_id, identifier, numeric_id=numeric_id)

    success = any(results)
    return success, None if success else "All ads failed"


async def _resolve_entity_with_retry(client, group: dict, retry: bool = True):
    """Robust entity resolution with join-on-demand logic."""
    identifier = group.get("identifier", "")
    link = group.get("link", "")
    link_type = group.get("link_type", "")
    
    try:
        # Try direct resolution
        if link_type in ("username", "topic"):
            return await client.get_entity(f"@{identifier}")
        if link_type in ("private_chat", "private_topic"):
            # Try to resolve numeric ID (must be int)
            try:
                # Private IDs often need -100 prefix for get_entity
                return await client.get_entity(int(f"-100{identifier}"))
            except Exception:
                return await client.get_entity(int(identifier))
        
        # New: Use numeric_id if available as it's the most reliable
        if group.get("numeric_id"):
            try:
                return await client.get_entity(group.get("numeric_id"))
            except Exception:
                pass

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
            elif link_type != "folder": # Don't try to "join" a folder link directly
                await client(JoinChannelRequest(link))
            
            # Recursive call with retry=False to avoid infinite loops
            return await _resolve_entity_with_retry(client, group, retry=False)
        except Exception:
            return None
