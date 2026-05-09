import asyncio
import logging
import random
from datetime import datetime, timedelta
import pytz

from app.config import (
    TIMEZONE, NIGHT_MODE_ENABLED, NIGHT_MODE_START_HOUR, NIGHT_MODE_END_HOUR,
    ACCOUNT_HEALTH_ACTIVE, MIN_INTERVAL
)
from app.database.mongo import get_db
from app.database.models import (
    get_user_accounts, get_active_groups, create_broadcast_job, init_db_indexes
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Scheduler")

_tz = pytz.timezone(TIMEZONE)

def is_night_time() -> bool:
    if not NIGHT_MODE_ENABLED:
        return False
    now = datetime.now(_tz)
    return NIGHT_MODE_START_HOUR <= now.hour < NIGHT_MODE_END_HOUR

async def scheduler_loop():
    logger.info("Scheduler started.")
    await init_db_indexes()
    db = get_db()
    
    while True:
        try:
            if is_night_time():
                logger.info("Night mode active, skipping scheduling...")
                await asyncio.sleep(300)
                continue

            # 1. Find users with running ads
            async for user in db.users.find({"ads_status": "running"}):
                user_id = user["telegram_user_id"]
                interval = max(user.get("interval_seconds", MIN_INTERVAL), MIN_INTERVAL)
                ads = user.get("ads", [])
                
                if not ads:
                    continue

                # 2. Get active accounts for this user
                accounts = await get_user_accounts(user_id)
                # Filter active and NOT currently limited
                now = datetime.utcnow()
                active_accounts = [
                    a for a in accounts 
                    if a.get("status") == ACCOUNT_HEALTH_ACTIVE and 
                    (a.get("limited_until") is None or a.get("limited_until") <= now)
                ]
                
                if not active_accounts:
                    continue

                # 3. Get groups that need a message
                # Logic: last_sent_at is None OR (now - last_sent_at) >= interval
                # AND next_allowed_at is None OR next_allowed_at <= now
                # AND can_send is True AND failure_count < 10
                threshold = now - timedelta(seconds=interval)
                query = {
                    "user_id": user_id,
                    "status": "active",
                    "can_send": True,
                    "failure_count": {"$lt": 10},
                    "$or": [
                        {"last_sent_at": None},
                        {"last_sent_at": {"$lte": threshold}}
                    ],
                    "$and": [
                        {"$or": [
                            {"next_allowed_at": None},
                            {"next_allowed_at": {"$lte": now}}
                        ]}
                    ]
                }
                
                # We also check if there is ALREADY a pending job for this group
                # (although create_broadcast_job has a unique key, we can optimize here)
                groups_cursor = db.groups.find(query)
                groups_to_schedule = await groups_cursor.to_list(length=1000)
                
                if not groups_to_schedule:
                    continue

                logger.info(f"Scheduling {len(groups_to_schedule)} jobs for user {user_id}")

                # 4. Distribute groups among accounts (Round Robin)
                for i, group in enumerate(groups_to_schedule):
                    account = active_accounts[i % len(active_accounts)]
                    
                    # Pick a random ad from user's ads list for rotation
                    ad = random.choice(ads)
                    
                    job_data = {
                        "user_id": user_id,
                        "account_phone": account["phone_masked"], # using phone_masked as account identifier
                        "group_id": group["identifier"],
                        "ad_id": ad["id"],
                        "run_after": now + timedelta(seconds=random.randint(0, 60)), # small jitter
                    }
                    
                    await create_broadcast_job(job_data)

        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            
        await asyncio.sleep(60) # Run every minute

if __name__ == "__main__":
    asyncio.run(scheduler_loop())
