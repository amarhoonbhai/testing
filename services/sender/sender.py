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
import signal
import os
import platform
import datetime
import random

from core.logger import setup_service_logging
from core.database import init_database, close_connection, get_database
from models.user import get_user_config
from core.config import SCHEDULER_POLL_INTERVAL, SEND_DELAY_MIN, SEND_DELAY_MAX
from models.job import (
    get_pending_jobs, claim_job, complete_job, fail_job, 
    upsert_worker_heartbeat
)
from models.session import is_session_paused, get_session
from models.settings import get_global_settings
from services.worker.session_pool import SessionPool
from services.worker.send_logic import send_message_to_group

logger = logging.getLogger(__name__)

class UnifiedSender:
    def __init__(self):
        self.running = False
        self.worker_id = f"worker_{platform.node()}_{os.getpid()}"
        self.pool = SessionPool()
        self._batch_counts = {} # phone -> count

    async def start(self):
        self.running = True
        await self.pool.start()
        logger.info(f"🚀 Unified Sender started (ID: {self.worker_id})")
        
        # Start heartbeat task
        asyncio.create_async_task(self._heartbeat_loop())
        
        while self.running:
            try:
                # 1. Check Global Killswitch
                global_settings = await get_global_settings()
                if not global_settings.get("is_active", True):
                    await asyncio.sleep(10)
                    continue

                # 2. Poll for jobs
                jobs = await get_pending_jobs(limit=10)
                if not jobs:
                    await asyncio.sleep(SCHEDULER_POLL_INTERVAL)
                    continue

                # 3. Process jobs concurrently
                tasks = [self._process_job(job) for job in jobs]
                await asyncio.gather(*tasks)

            except Exception as e:
                logger.error(f"Error in main sender loop: {e}")
                await asyncio.sleep(5)

    async def _heartbeat_loop(self):
        while self.running:
            try:
                await upsert_worker_heartbeat(self.worker_id)
            except Exception:
                pass
            await asyncio.sleep(30)

    async def _process_job(self, job):
        job_id = job["_id"]
        user_id = job["user_id"]
        phone = job["phone"] # In V4, jobs are strictly per-account phone
        group_id = job["group_id"]
        message_id = job["message_id"]

        # 1. Claim the job
        if not await claim_job(job_id, self.worker_id):
            return

        try:
            # 2. Check individual account status
            session = await get_session(user_id, phone)
            if not session or not session.get("is_active", True):
                await fail_job(job_id, "Account ads are paused/inactive")
                return

            if await is_session_paused(user_id, phone):
                await fail_job(job_id, "Session in cooldown/paused")
                return

            # 3. Apply Anti-Freeze batch logic
            count = self._batch_counts.get(phone, 0)
            if count >= 5:
                # Every 5 messages, take a longer break (5-10 mins)
                break_sec = random.randint(300, 600)
                logger.info(f"[{phone}] Batch break (5 messages done) — pausing for {break_sec}s")
                self._batch_counts[phone] = 0
                await fail_job(job_id, f"Batch break active ({break_sec}s)")
                return

            # 4. Acquire client and send
            client = await self.pool.acquire(user_id, phone)
            config = await get_user_config(user_id)
            
            status, flood_sec = await send_message_to_group(
                client, job_id, user_id, phone, message_id, group_id,
                copy_mode=config.get("copy_mode", False)
            )

            if status == "sent":
                await complete_job(job_id)
                self._batch_counts[phone] = count + 1
                # Inter-message delay (60-120s)
                delay = random.randint(60, 120)
                logger.info(f"[{phone}] Message sent to {group_id}. Waiting {delay}s...")
                await asyncio.sleep(delay)
            elif status == "flood":
                await fail_job(job_id, f"FloodWait for {flood_sec}s")
            else:
                await fail_job(job_id, f"Send failed: {status}")

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            await fail_job(job_id, str(e))

    async def stop(self):
        self.running = False
        await self.pool.stop()
        logger.info("Unified Sender shut down.")

# To support 'asyncio.create_async_task' or similar
if not hasattr(asyncio, "create_async_task"):
    asyncio.create_async_task = asyncio.create_task

async def main():
    setup_service_logging("sender")
    await init_database()
    sender = UnifiedSender()
    
    # Handle signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(sender.stop()))
        except NotImplementedError:
            pass # Windows

    try:
        await sender.start()
    finally:
        await close_connection()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
