"""
Unified Sender Service — the heartbeat of the simplified pipeline.
Replaces both the old Scheduler and ARQ Worker. 
Runs a loop that:
  1. Polls scheduled_jobs for pending work.
  2. Claims jobs atomically.
  3. Executes message sends directly using the SessionPool and SendLogic.
"""

import asyncio
import logging
import os
import platform
import datetime
import random

from core.base_service import BaseService
from core.database import get_database
from models.user import get_user_config
from core.config import (
    SCHEDULER_POLL_INTERVAL, GROUP_GAP_SECONDS, 
    SEND_DELAY_MIN, SEND_DELAY_MAX
)
from models.job import (
    get_pending_jobs, claim_job, complete_job, fail_job, 
    upsert_worker_heartbeat, log_job_event
)
from models.session import is_session_paused, get_session
from models.settings import get_global_settings
from services.worker.session_pool import SessionManager
from services.worker.send_logic import send_message_to_group

logger = logging.getLogger(__name__)

class UnifiedSender(BaseService):
    def __init__(self):
        super().__init__("Sender")
        self.worker_id = f"worker_{platform.node()}_{os.getpid()}"
        self.pool = SessionManager()
        self._batch_counts = {} # phone -> count
        self._account_locks = {} # phone -> asyncio.Lock

    async def on_start(self):
        """Startup logic for the Sender service."""
        await self.pool.start()
        # Start heartbeat and main processing loop as background tasks
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._main_processing_loop())

    async def on_stop(self):
        """Cleanup logic for the Sender service."""
        await self.pool.stop()

    async def _heartbeat_loop(self):
        while self.running:
            try:
                await upsert_worker_heartbeat(self.worker_id)
            except Exception as e:
                logger.warning(f"Heartbeat failed: {e}")
            await asyncio.sleep(30)

    async def _main_processing_loop(self):
        """Standardized processing loop."""
        while self.running:
            try:
                # 1. Killswitch
                settings = await get_global_settings()
                if not settings.get("all_bots_active", True):
                    await asyncio.sleep(10)
                    continue

                # 2. Get Jobs
                jobs = await get_pending_jobs(limit=10)
                if not jobs:
                    await asyncio.sleep(SCHEDULER_POLL_INTERVAL)
                    continue

                # 3. Process
                # We still gather, but _process_job will use per-account locks
                await asyncio.gather(*[self._process_job(j) for j in jobs])
                
            except Exception as e:
                logger.error(f"Error in sender loop: {e}")
                await asyncio.sleep(5)

    def _get_account_lock(self, phone: str) -> asyncio.Lock:
        if phone not in self._account_locks:
            self._account_locks[phone] = asyncio.Lock()
        return self._account_locks[phone]

    async def _process_job(self, job):
        job_id = job["job_id"] # Use job_id (UUID)
        user_id = job["user_id"]
        phone = job["phone"]
        group_id = job["group_id"]
        message_id = job["message_id"]

        # Ensure we only process ONE job per account at a time
        async with self._get_account_lock(phone):
            if not await claim_job(job_id, self.worker_id):
                return

            try:
                session = await get_session(user_id, phone)
                if not session or await is_session_paused(user_id, phone):
                    await fail_job(job_id, "Session unavailable/paused")
                    return

                # 1. Natural Send Delay (Jitter)
                delay = random.randint(SEND_DELAY_MIN, SEND_DELAY_MAX)
                logger.info(f"[{phone}] Applying send jitter: {delay}s")
                await asyncio.sleep(delay)

                client = await self.pool.acquire(user_id, phone)
                config = await get_user_config(user_id)
                
                status, flood_sec = await send_message_to_group(
                    client, job_id, user_id, phone, message_id, group_id,
                    copy_mode=config.get("copy_mode", False)
                )

                # LOG THE EVENT (This is crucial for stats!)
                await log_job_event(
                    job_id=job_id, user_id=user_id, phone=phone,
                    group_id=group_id, message_id=message_id,
                    status=status, error=None if status == "sent" else f"Status: {status}"
                )

                if status == "sent":
                    await complete_job(job_id, groups_sent=1)
                    # 2. RANDOMIZED Group Gap (Delay before next group for this same account)
                    # We target 210s (3.5m) but add +/- 15s of jitter for safety
                    base_gap = config.get("group_gap", GROUP_GAP_SECONDS)
                    jitter_gap = random.randint(max(10, base_gap - 15), base_gap + 15)
                    
                    logger.info(f"[{phone}] Message SENT to {group_id}. Applying randomized gap: {jitter_gap}s")
                    await asyncio.sleep(jitter_gap)
                elif status == "flood":
                    await self._handle_flood(user_id, phone, flood_sec, job_id)
                else:
                    await fail_job(job_id, f"Send failed: {status}")

            except Exception as e:
                logger.error(f"Job {job_id} error: {e}")
                await fail_job(job_id, str(e))
                await log_job_event(
                    job_id=job_id, user_id=user_id, phone=phone,
                    group_id=group_id, message_id=message_id,
                    status="failed", error=str(e)
                )

    async def _handle_flood(self, user_id, phone, sec, job_id):
        db = get_database()
        pause_until = datetime.datetime.utcnow() + datetime.timedelta(seconds=sec)
        await db.sessions.update_one(
            {"user_id": user_id, "phone": phone},
            {"$set": {"paused_until": pause_until, "pause_reason": f"FloodWait: {sec}s"}}
        )
        await fail_job(job_id, f"FloodWait {sec}s")

if __name__ == "__main__":
    asyncio.run(UnifiedSender().run_forever())
