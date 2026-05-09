import asyncio
import logging
import os
import socket
import uuid
from datetime import datetime, timedelta

from telethon.errors import (
    FloodWaitError, ChatWriteForbiddenError, UserBannedInChannelError,
    ChannelPrivateError, ChatIdInvalidError, PeerIdInvalidError,
    AuthKeyUnregisteredError, UserDeactivatedBanError
)

from app.config import (
    WORKER_CONCURRENCY, JOB_LEASE_SECONDS, MAX_JOB_RETRIES,
    ACCOUNT_HEALTH_ACTIVE, ACCOUNT_HEALTH_LIMITED, ACCOUNT_HEALTH_FAILED
)
from app.database.models import (
    get_user, get_account, get_user_groups, claim_job, release_job,
    complete_job, fail_job, lock_account, unlock_account,
    update_account_status, update_account_health, update_group_sent,
    update_group_failed, disable_group, delete_group, increment_sent, increment_failed
)
from app.services.encryption_service import decrypt_session
from app.services.telethon_service import get_client_from_session
from app.services.channel_logger import log_message_sent, log_error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Worker")

# Unique ID for this worker instance
WORKER_ID = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"

async def process_job(job: dict):
    job_id = job["_id"]
    user_id = job["user_id"]
    phone = job["account_phone"]
    group_id = job["group_id"]
    ad_id = job["ad_id"]

    logger.info(f"Processing job {job_id} for user {user_id}")

    # 1. Lock account
    if not await lock_account(phone, WORKER_ID):
        logger.info(f"Account {phone} is locked, releasing job.")
        await release_job(job_id)
        return

    client = None
    try:
        # 2. Get User, Account, Group, Ad
        user = await get_user(user_id)
        account = await get_account(user_id, phone)
        
        if not user or not account:
            await fail_job(job_id, "User or account not found", MAX_JOB_RETRIES)
            return

        # Find the specific ad
        ad = next((a for a in user.get("ads", []) if a["id"] == ad_id), None)
        if not ad:
            await fail_job(job_id, "Ad creative not found", MAX_JOB_RETRIES)
            return

        # Find the group
        groups = await get_user_groups(user_id)
        group = next((g for g in groups if g["identifier"] == group_id), None)
        if not group:
            await fail_job(job_id, "Target group not found", MAX_JOB_RETRIES)
            return

        # 3. Connect Telethon
        try:
            session = decrypt_session(account["encrypted_session"])
            client = await get_client_from_session(session)
        except (AuthKeyUnregisteredError, UserDeactivatedBanError, ConnectionError) as e:
            await update_account_status(user_id, phone, ACCOUNT_HEALTH_FAILED, str(e))
            await fail_job(job_id, f"Session failure: {type(e).__name__}", MAX_JOB_RETRIES)
            return

        # 4. Resolve and Send
        try:
            entity = await _resolve_entity(client, group)
            if not entity:
                await fail_job(job_id, "Could not resolve entity", MAX_JOB_RETRIES)
                return

            await _safe_send_ad(client, user_id, group, ad, entity, phone)
            await complete_job(job_id)

        except FloodWaitError as e:
            logger.warning(f"FloodWait on {phone}: {e.seconds}s")
            limited_until = datetime.utcnow() + timedelta(seconds=e.seconds + 60)
            await update_account_status(user_id, phone, ACCOUNT_HEALTH_LIMITED, f"FloodWait {e.seconds}s", limited_until=limited_until)
            await fail_job(job_id, f"FloodWait {e.seconds}s", MAX_JOB_RETRIES)
        
        except Exception as e:
            logger.error(f"Error in job processing: {e}")
            await fail_job(job_id, str(e), MAX_JOB_RETRIES)

    except Exception as e:
        logger.error(f"Job processing exception: {e}", exc_info=True)
        await fail_job(job_id, str(e), MAX_JOB_RETRIES)
    finally:
        if client:
            try: await client.disconnect()
            except: pass
        await unlock_account(phone, WORKER_ID)


async def _resolve_entity(client, group):
    """Try to resolve group entity using cached numeric ID or link."""
    # Try multiple ways to resolve, as Telethon might need a join or link resolution first
    identifier = group.get("identifier")
    numeric_id = group.get("numeric_id")
    link = group.get("link")

    try:
        if numeric_id:
            # Note: numeric_id might fail if the account hasn't "seen" the group
            return await client.get_entity(numeric_id)
    except Exception:
        pass

    try:
        # Resolve by username or link
        return await client.get_entity(identifier or link)
    except Exception:
        try:
            # Final attempt with the full link
            return await client.get_entity(link)
        except Exception as e:
            logger.error(f"Resolution failed for {identifier}: {e}")
            return None


async def _safe_send_ad(client, user_id, group, ad, entity, phone):
    """Core sending logic with granular error handling."""
    from telethon.errors import (
        SlowModeWaitError, ChatWriteForbiddenError, UserBannedInChannelError,
        ChatAdminRequiredError, ChannelPrivateError, PeerFloodError, RPCError
    )
    from app.database.models import update_group_health, update_group_sent

    media_path = ad.get("ad_media_file_path")
    ad_message = ad.get("ad_message") or "Kurup Ads"
    topic_id = group.get("topic_id")
    identifier = group["identifier"]
    numeric_id = group.get("numeric_id")
    
    send_kwargs = {}
    if topic_id:
        send_kwargs["reply_to"] = topic_id

    try:
        if ad.get("ad_media_type") in ("photo", "video") and media_path:
            if os.path.exists(media_path):
                await client.send_file(entity, media_path, caption=ad_message, **send_kwargs)
            else:
                await client.send_message(entity, ad_message, **send_kwargs)
        else:
            await client.send_message(entity, ad_message, **send_kwargs)

        # Success updates
        await update_group_health(user_id, identifier, numeric_id=numeric_id)
        await update_group_sent(user_id, identifier, numeric_id=numeric_id)
        await update_account_health(user_id, phone, 1)
        await increment_sent(user_id)
        await log_message_sent(user_id, identifier, phone, True)

    except SlowModeWaitError as e:
        logger.warning(f"SlowMode on {identifier}: {e.seconds}s")
        next_allowed = datetime.utcnow() + timedelta(seconds=e.seconds)
        await update_group_health(user_id, identifier, next_allowed_at=next_allowed, numeric_id=numeric_id)
        raise # Still raise to fail/retry the job later

    except (ChatWriteForbiddenError, UserBannedInChannelError, ChatAdminRequiredError):
        logger.warning(f"Permission denied for {identifier}")
        await update_group_health(user_id, identifier, can_send=False, status="restricted", numeric_id=numeric_id)
        await log_message_sent(user_id, identifier, phone, False, "Permission Denied")

    except ChannelPrivateError:
        logger.warning(f"Channel private or left: {identifier}")
        await update_group_health(user_id, identifier, can_send=False, status="left_or_private", numeric_id=numeric_id)

    except PeerFloodError:
        logger.warning(f"PeerFlood on account {phone}")
        limited_until = datetime.utcnow() + timedelta(hours=24)
        await update_account_status(user_id, phone, ACCOUNT_HEALTH_LIMITED, "PeerFlood", limited_until=limited_until)
        raise

    except RPCError as e:
        logger.error(f"RPCError sending to {identifier}: {e}")
        await update_group_health(user_id, identifier, error=str(e), numeric_id=numeric_id)
        await update_account_health(user_id, phone, -1)
        raise

async def worker_task(queue: asyncio.Queue):
    while True:
        job = await queue.get()
        try:
            await process_job(job)
        except Exception as e:
            logger.error(f"Worker task error: {e}")
        finally:
            queue.task_done()

async def main():
    logger.info(f"Worker {WORKER_ID} starting with concurrency {WORKER_CONCURRENCY}")
    
    queue = asyncio.Queue(maxsize=WORKER_CONCURRENCY * 2)
    
    # Start worker tasks
    tasks = []
    for _ in range(WORKER_CONCURRENCY):
        tasks.append(asyncio.create_task(worker_task(queue)))
    
    while True:
        try:
            # Only pull a new job if queue has space
            if not queue.full():
                job = await claim_job(WORKER_ID, JOB_LEASE_SECONDS)
                if job:
                    await queue.put(job)
                else:
                    await asyncio.sleep(5)
            else:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
