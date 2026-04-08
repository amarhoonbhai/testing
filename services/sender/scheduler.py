"""
Unified Scheduler Service — the brain of the Kurup Ads pipeline.
Hardened version to prevent cycle spamming and respect strict intervals.
"""

import asyncio
import logging
import datetime
import random
from typing import List

from core.base_service import BaseService
from core.database import get_database
from models.user import get_all_users, get_user_config, update_user_config
from models.session import get_all_user_sessions
from models.group import get_user_groups
from models.job import create_job

logger = logging.getLogger(__name__)

class UnifiedScheduler(BaseService):
    def __init__(self):
        super().__init__("Scheduler")
        self.poll_interval = 60  # Check every minute
        self._processing_users = set()  # Generation lock

    async def on_start(self):
        """Startup logic for the Scheduler service."""
        asyncio.create_task(self._scheduling_loop())
        asyncio.create_task(self._cleanup_loop())

    async def on_stop(self):
        """Cleanup logic for the Scheduler service."""
        pass

    async def _cleanup_loop(self):
        """Background task that automatically removes dead groups after 24h."""
        db = get_database()
        while self.running:
            try:
                cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
                res = await db.groups.delete_many({"first_fail_at": {"$lt": cutoff}})
                if res.deleted_count > 0:
                    logger.info(f"🧹 Auto-Cleanup: Removed {res.deleted_count} groups inactive for >24h")
            except Exception as e: pass
            await asyncio.sleep(3600)

    async def _scheduling_loop(self):
        """Main loop that scans users and generates jobs."""
        while self.running:
            try:
                user_ids = await get_all_users()
                # Randomized shuffle to prevent all users from hitting same second
                random.shuffle(user_ids)
                for user_id in user_ids:
                    if user_id in self._processing_users: continue
                    await self._process_user_scheduling(user_id)
            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}", exc_info=True)
            await asyncio.sleep(self.poll_interval)

    async def _process_user_scheduling(self, user_id: int):
        """Check if it's time to generate jobs for a specific user."""
        db = get_database()
        config = await get_user_config(user_id)
        if not config.get("is_active", True): return

        interval_min = config.get("interval_min", 20)
        now = datetime.datetime.utcnow()

        # 1. ENFORCE STRICT INTERVAL FROM LAST START
        # Prioritize config.last_job_gen_at to prevent "Fail -> Spam" loop
        last_start = config.get("last_job_gen_at")
        if last_start:
            # If gen_at was more than 1 week ago, it might be stale/reset
            if (now - last_start).total_seconds() < (interval_min * 60):
                # TOO SOON!
                return

        # 2. Check for ANY active jobs (prevent overlapping cycles)
        active_count = await db.scheduled_jobs.count_documents({
            "user_id": user_id,
            "status": {"$in": ["pending", "queued", "processing", "retry"]}
        })
        if active_count > 0:
            # Cycle still in progress, even if it started a while ago
            return

        # ── START NEW CYCLE ───────────────────────────────────────────────────
        self._processing_users.add(user_id)
        try:
            sessions = await get_all_user_sessions(user_id)
            connected = [s for s in sessions if s.get("connected") and s.get("is_active", True)]
            if not connected:
                # Still update gen_at to avoid checking every minute
                await update_user_config(user_id, last_job_gen_at=now)
                return

            groups = await get_user_groups(user_id, enabled_only=True)
            if not groups:
                await update_user_config(user_id, last_job_gen_at=now)
                return

            # Sort for stability
            groups.sort(key=lambda x: x.get("chat_id", 0))
            connected.sort(key=lambda x: x.get("phone", ""))
            
            num_sessions = len(connected)
            logger.info(f"🔄 [User {user_id}] Starting cycle | Accounts: {num_sessions} | Groups: {len(groups)}")
            
            # ATOMIC UPDATE: Mark START of cycle IMMEDIATELY to prevent spam if creation takes long
            await update_user_config(user_id, last_job_gen_at=now)
            
            total_jobs = 0
            for i, group in enumerate(groups):
                # Round-Robin Dispatch
                session = connected[i % num_sessions]
                await create_job(
                    user_id=user_id, phone=session["phone"],
                    message_id=config.get("message_id", -1), 
                    group_id=group["chat_id"], run_at=now,
                    copy_mode=config.get("copy_mode", False)
                )
                total_jobs += 1

            logger.info(f"✅ [User {user_id}] Cycle Generation Complete: {total_jobs} jobs.")
        finally:
            self._processing_users.remove(user_id)

if __name__ == "__main__":
    asyncio.run(UnifiedScheduler().run_forever())
