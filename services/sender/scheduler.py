"""
Unified Scheduler Service — the brain of the Kurup Ads pipeline.
Generates jobs in the scheduled_jobs collection based on user intervals.
"""

import asyncio
import logging
import datetime
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
                # Find groups that have been failing for more than 24 hours
                res = await db.groups.delete_many({
                    "first_fail_at": {"$lt": cutoff}
                })
                if res.deleted_count > 0:
                    logger.info(f"🧹 Auto-Cleanup: Removed {res.deleted_count} groups inactive for >24h")
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
            
            # Run cleanup every hour
            await asyncio.sleep(3600)

    async def _scheduling_loop(self):
        """Main loop that scans users and generates jobs."""
        while self.running:
            try:
                user_ids = await get_all_users()
                for user_id in user_ids:
                    await self._process_user_scheduling(user_id)
            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}", exc_info=True)
            
            await asyncio.sleep(self.poll_interval)

    async def _process_user_scheduling(self, user_id: int):
        """Check if it's time to generate jobs for a specific user."""
        db = get_database()
        config = await get_user_config(user_id)
        if not config.get("is_active", True):
            return

        interval_min = config.get("interval_min", 20)
        now = datetime.datetime.utcnow()

        # 1. Check for ANY active jobs (pending, queued, processing) for this user
        active_count = await db.scheduled_jobs.count_documents({
            "user_id": user_id,
            "status": {"$in": ["pending", "queued", "processing"]}
        })
        
        if active_count > 0:
            # Current cycle is still running, skip generation
            logger.debug(f"User {user_id} still has {active_count} active jobs. Waiting...")
            return

        # 2. Find time when the LAST job of the previous cycle finished
        last_job = await db.scheduled_jobs.find_one(
            {"user_id": user_id},
            sort=[("completed_at", -1)]
        )
        
        last_finish = last_job.get("completed_at") if last_job else None
        
        # 3. Only start NEW cycle if interval has passed since LAST finish (or never finished)
        if not last_finish or (now - last_finish).total_seconds() >= (interval_min * 60):
            logger.info(f"🔄 Starting new cycle for user {user_id} (Interval: {interval_min}m)")
            
            # Get all connected accounts for this user
            sessions = await get_all_user_sessions(user_id)
            connected_sessions = [s for s in sessions if s.get("connected") and s.get("is_active", True)]
            
            if not connected_sessions:
                return

            total_jobs = 0
            for session in connected_sessions:
                phone = session["phone"]
                groups = await get_user_groups(user_id, phone=phone)
                enabled_groups = [g for g in groups if g.get("enabled", True)]
                
                for group in enabled_groups:
                    await create_job(
                        user_id=user_id,
                        phone=phone,
                        message_id=config.get("message_id", -1), 
                        group_id=group["chat_id"],
                        run_at=now,
                        copy_mode=config.get("copy_mode", False)
                    )
                    total_jobs += 1

            # Update state
            await update_user_config(user_id, last_job_gen_at=now)
            if total_jobs > 0:
                logger.info(f"Successfully queued {total_jobs} jobs for user {user_id}")

if __name__ == "__main__":
    asyncio.run(UnifiedScheduler().run_forever())
