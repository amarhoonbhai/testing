"""
Unified Sender Service — the heartbeat of the simplified pipeline.
Integrated with Adaptive Delay, Multi-Ad Campaigns, and Staggered Startups.
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
from core.adaptive import AdaptiveDelayController, UserLogAdapter
from core.config import (
    SCHEDULER_POLL_INTERVAL, GROUP_GAP_SECONDS, 
    SEND_DELAY_MIN, SEND_DELAY_MAX, TIMEZONE, NIGHT_MODE_END_HOUR
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
        self._account_locks = {} # phone -> asyncio.Lock
        self._adaptive_controllers = {} # phone -> AdaptiveDelayController
        self._first_run_done = set() # phone

    async def on_start(self):
        """Startup logic for the Sender service."""
        await self.pool.start()
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._main_processing_loop())

    async def on_stop(self):
        """Cleanup logic for the Sender service."""
        await self.pool.stop()

    def _get_adaptive_controller(self, phone: str) -> AdaptiveDelayController:
        if phone not in self._adaptive_controllers:
            self._adaptive_controllers[phone] = AdaptiveDelayController(GROUP_GAP_SECONDS)
        return self._adaptive_controllers[phone]

    async def _heartbeat_loop(self):
        while self.running:
            try: await upsert_worker_heartbeat(self.worker_id)
            except: pass
            await asyncio.sleep(30)

    async def _main_processing_loop(self):
        """Main batch polling loop."""
        while self.running:
            try:
                # 1. Killswitch & Night Mode Check
                settings = await get_global_settings()
                if not settings.get("all_bots_active", True):
                    await asyncio.sleep(10); continue

                # 2. Get Jobs
                jobs = await get_pending_jobs(limit=10)
                if not jobs:
                    await asyncio.sleep(SCHEDULER_POLL_INTERVAL); continue

                # 3. Parallel Dispatch (Jobs for DIFFERENT accounts run in parallel)
                await asyncio.gather(*[self._process_job(j) for j in jobs])
            except Exception as e:
                logger.error(f"Error in sender loop: {e}")
                await asyncio.sleep(5)

    def _get_account_lock(self, phone: str) -> asyncio.Lock:
        if phone not in self._account_locks:
            self._account_locks[phone] = asyncio.Lock()
        return self._account_locks[phone]

    async def _process_job(self, job):
        job_id, user_id, phone = job["job_id"], job["user_id"], job["phone"]
        group_id, message_id = job["group_id"], job["message_id"]
        lgr = UserLogAdapter(logger, {'user_id': user_id, 'phone': phone})

        async with self._get_account_lock(phone):
            if not await claim_job(job_id, self.worker_id): return

            try:
                # 1. Initial Account Stagger (Anti-Burst)
                if phone not in self._first_run_done:
                    stagger = random.randint(5, 30)
                    lgr.info(f"Account warming up... waiting {stagger}s stagger.")
                    await asyncio.sleep(stagger)
                    self._first_run_done.add(phone)

                # 2. Status & Session Verification
                session = await get_session(user_id, phone)
                if not session or await is_session_paused(user_id, phone):
                    await fail_job(job_id, "Session paused/revoked")
                    return

                # 3. Adaptive Delay Injection
                controller = self._get_adaptive_controller(phone)
                
                # 4. Multi-Ad Campaign Execution (Option A: Ad-by-Ad)
                client = await self.pool.acquire(user_id, phone)
                config = await get_user_config(user_id)
                
                # We fetch and loop through messages if it's a global campaign
                campaign_messages = []
                if message_id == -1:
                    msgs = await client.get_messages('me', limit=10)
                    campaign_messages = [m for m in msgs if not (m.text and m.text.startswith("."))]
                    campaign_messages.reverse() # Send oldest first
                else:
                    msg = await client.get_messages('me', ids=message_id)
                    if msg: campaign_messages = [msg]

                if not campaign_messages:
                    lgr.warning("No campaign messages found in Saved Messages. Skipping job.")
                    await complete_job(job_id, groups_sent=0)
                    return

                lgr.info(f"Campaign Cycle: {len(campaign_messages)} ad(s) targeting Group {group_id}")
                
                for idx, ad in enumerate(campaign_messages):
                    if not self.running: break
                    
                    # Inter-message delay if multiple ads
                    if idx > 0:
                        msg_delay = random.randint(60, 120)
                        lgr.info(f"Applying inter-ad delay: {msg_delay}s")
                        await asyncio.sleep(msg_delay)

                    status, flood_sec = await send_message_to_group(
                        client, job_id, user_id, phone, ad.id, group_id,
                        copy_mode=config.get("copy_mode", False),
                        adaptive_controller=controller,
                        msg_obj=ad
                    )

                    await log_job_event(job_id, user_id, phone, group_id, ad.id, status, None if status == "sent" else f"Status: {status}")

                    if status == "sent":
                        lgr.info(f"Ad {idx+1}/{len(campaign_messages)} SENT to group {group_id}.")
                    elif status == "flood":
                        await self._handle_flood(user_id, phone, flood_sec, job_id)
                        return # Stop campaign for this account immediately
                    else:
                        lgr.error(f"Ad {idx+1} failed with status: {status}")

                # 5. Finalize Cycle
                await complete_job(job_id, groups_sent=1)
                
                # Application of Adaptive Group Gap (Waiting before next job/group)
                base_gap = controller.get_gap()
                final_gap = random.randint(max(10, base_gap - 15), base_gap + 15)
                lgr.info(f"Group cycle complete. Applying adaptive gap wait: {final_gap}s.")
                await asyncio.sleep(final_gap)

            except Exception as e:
                lgr.error(f"Critical execution error: {e}", exc_info=True)
                await fail_job(job_id, str(e))

    async def _handle_flood(self, user_id, phone, sec, job_id):
        db = get_database()
        pause_until = datetime.datetime.utcnow() + datetime.timedelta(seconds=sec)
        await db.sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"paused_until": pause_until, "pause_reason": f"FloodWait: {sec}s"}})
        await fail_job(job_id, f"FloodWait {sec}s")

if __name__ == "__main__":
    asyncio.run(UnifiedSender().run_forever())
