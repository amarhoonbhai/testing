"""
Stats model — collection handling for user and admin statistics.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List

from core.database import get_database

async def get_admin_stats() -> Dict[str, Any]:
    """Get global system statistics for admins."""
    db = get_database()
    now = datetime.utcnow()
    cutoff_24h = now - timedelta(days=1)
    
    total_users = await db.users.count_documents({})
    connected_sessions = await db.sessions.count_documents({"connected": True})
    
    # Plans segmentation
    paid_active = await db.plans.count_documents({"status": "active", "plan_type": "premium"})
    trial_active = await db.plans.count_documents({"status": "active", "plan_type": "trial"})
    expired = await db.plans.count_documents({"status": "expired"})
    
    # Message stats (last 24h)
    sends_24h = await db.job_logs.count_documents({"timestamp": {"$gt": cutoff_24h}})
    success_24h = await db.job_logs.count_documents({"timestamp": {"$gt": cutoff_24h}, "status": "sent"})
    failed_24h = sends_24h - success_24h
    
    # Group health
    total_groups = await db.groups.count_documents({})
    groups_failing = await db.groups.count_documents({"first_fail_at": {"$exists": True}})
    groups_removed_24h = await db.job_logs.count_documents({
        "timestamp": {"$gt": cutoff_24h}, 
        "status": "removed"
    })
    
    success_rate = round((success_24h / sends_24h * 100) if sends_24h > 0 else 0, 1)
    
    return {
        "total_users": total_users,
        "connected_sessions": connected_sessions,
        "paid_active": paid_active,
        "trial_active": trial_active,
        "expired": expired,
        "sends_24h": sends_24h,
        "success_24h": success_24h,
        "failed_24h": failed_24h,
        "avg_success_rate": success_rate,
        "total_groups": total_groups,
        "groups_failing": groups_failing,
        "groups_removed_24h": groups_removed_24h
    }

async def get_send_stats(user_id: int) -> Dict[str, Any]:
    """Get message sending statistics for a specific user."""
    db = get_database()
    cutoff_24h = datetime.utcnow() - timedelta(days=1)
    
    sent_24h = await db.job_logs.count_documents({
        "user_id": user_id,
        "status": "sent",
        "timestamp": {"$gt": cutoff_24h}
    })
    
    total_sent = await db.job_logs.count_documents({
        "user_id": user_id,
        "status": "sent"
    })
    
    return {
        "sent_24h": sent_24h,
        "total_sent": total_sent
    }

async def get_account_stats(user_id: int, phone: str) -> Dict[str, Any]:
    """Get statistics for a specific Telegram account."""
    db = get_database()
    
    # Last active from session itself
    session = await db.sessions.find_one({"user_id": user_id, "phone": phone})
    last_active = session.get("last_active") if session else None
    
    # Success rate from job_logs (last 100 attempts)
    cursor = db.job_logs.find({"user_id": user_id, "phone": phone}).sort("timestamp", -1).limit(100)
    history = await cursor.to_list(length=100)
    
    total = len(history)
    sent = len([h for h in history if h.get("status") == "sent"])
    
    rate = int((sent / total * 100)) if total > 0 else 100
    
    # Total sent ever on this phone
    total_sent = await db.job_logs.count_documents({"user_id": user_id, "phone": phone, "status": "sent"})
    
    return {
        "last_active": last_active,
        "success_rate": rate,
        "total_sent": total_sent
    }
