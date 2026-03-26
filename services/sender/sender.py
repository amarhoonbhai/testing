"""
Unified Sender Service — the heartbeat of the simplified pipeline.

Replaces both the old Scheduler and ARQ Worker. 
Runs a loop that:
  1. Polls scheduled_jobs for pending work.
  2. Claims jobs atomically.
  3. Executes message sends directly using the SessionPool.
"""

import asyncio
import logging
import signal
import os
import platform

from core.logger import setup_service_logging
from core.database import init_database, close_connection
from core.config import SCHEDULER_POLL_INTERVAL, SEND_DELAY_MIN, SEND_DELAY_MAX
from models.job import (
    get_pending_jobs, claim_job, complete_job, fail_job, 
    upsert_worker_heartbeat
)
from services.worker.session_pool import SessionPool
from services.worker.send_logic import send_message_to_group

logger = logging.getLogger(__name__)

WORKER_ID = f"sender-{platform.node()}-{os.getpid()}"

class UnifiedSender:
    def __init__(self):
        self.running = False
        self._shutdown_event = asyncio.Event()
        self._session_pool: SessionPool | None = None
        self._active_jobs = 0
        self._total_processed = 0

    async def start(self):
        setup_service_logging("sender")
        logger.info("=" * 50)
        logger.info(f"Unified Sender Service Starting ({WORKER_ID})")
        logger.info("=" * 50)

        self.running = True
        await init_database()

        self._session_pool = SessionPool()
        await self._session_pool.start()

        # Signal handlers (Unix only)
        if platform.system() != "Windows":
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, lambda: self.stop())
                except NotImplementedError:
                    pass

        # Heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        try:
            while self.running:
                # 1. Poll pending jobs
                jobs = await get_pending_jobs(limit=10) # Process in small batches
                
                if jobs:
                    for job_data in jobs:
                        if not self.running:
                            break
                        
                        job_id = job_data["job_id"]
                        
                        # 2. Claim job
                        job = await claim_job(job_id, WORKER_ID)
                        if not job:
                            continue
                        
                        # 3. Execute job
                        self._active_jobs += 1
                        asyncio.create_task(self._process_job(job))

                # 4. Sleep
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=SCHEDULER_POLL_INTERVAL
                    )
                    break
                except asyncio.TimeoutError:
                    continue

        except Exception as e:
            logger.error(f"Main loop error: {e}")
        finally:
            self.running = False
            heartbeat_task.cancel()
            await self.cleanup()

    async def _process_job(self, job):
        job_id = job["job_id"]
        user_id = job["user_id"]
        phone = job["phone"]
        message_id = job["message_id"]
        groups = job.get("groups", [])
        copy_mode = job.get("copy_mode", False)

        logger.info(f"📤 Processing job {job_id} for {phone} ({len(groups)} groups)")

        try:
            client = await self._session_pool.acquire(user_id, phone)
            
            sent_count = 0
            for group_id in groups:
                if not self.running:
                    break
                
                success = await send_message_to_group(client, group_id, message_id, copy_mode)
                if success:
                    sent_count += 1
                
                import random
                delay = random.randint(SEND_DELAY_MIN, SEND_DELAY_MAX)
                await asyncio.sleep(delay)

            await complete_job(job_id, sent_count)
            logger.info(f"✅ Job {job_id} completed: {sent_count} sent")
            
        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {e}")
            await fail_job(job_id, str(e))
        finally:
            self._active_jobs -= 1
            self._total_processed += 1

    async def _heartbeat_loop(self):
        while self.running:
            try:
                await upsert_worker_heartbeat(WORKER_ID, self._active_jobs, self._total_processed)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            await asyncio.sleep(30)

    def stop(self):
        if not self.running:
            return
        logger.info("Shutdown signal received")
        self.running = False
        self._shutdown_event.set()

    async def cleanup(self):
        logger.info("Cleaning up...")
        if self._session_pool:
            await self._session_pool.stop()
        await close_connection()
        logger.info("Sender stopped")

async def main():
    sender = UnifiedSender()
    await sender.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
