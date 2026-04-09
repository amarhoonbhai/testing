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

async def get_user_profile_data(user_id: int) -> Dict[str, Any]:
    """Aggregate all user data for the dashboard with extended metrics."""
    db = get_database()
    cutoff_24h = datetime.utcnow() - timedelta(days=1)
    
    # Basic counts
    total_groups = await db.groups.count_documents({"user_id": user_id})
    active_groups = await db.groups.count_documents({"user_id": user_id, "enabled": True})
    
    # Sends in last 24h
    sent_24h = await db.job_logs.count_documents({
        "user_id": user_id, "status": "sent", "timestamp": {"$gt": cutoff_24h}
    })
    
    # Success rate in last 24h
    total_24h = await db.job_logs.count_documents({
        "user_id": user_id, "timestamp": {"$gt": cutoff_24h}
    })
    success_rate_24h = int((sent_24h / total_24h * 100)) if total_24h > 0 else 100
    
    # Total sent ever
    total_sent = await db.sessions.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$stats_total", 0]}}}}
    ]).to_list(length=1)
    total_sum = total_sent[0]["total"] if total_sent else 0

    sessions = await db.sessions.find({"user_id": user_id}).to_list(length=100)
    user = await db.users.find_one({"user_id": user_id})
    # Use 'config' collection as per new architecture
    config = await db.config.find_one({"user_id": user_id})
    
    return {
        "user_id": user_id,
        "user": user,
        "config": config,
        "sessions": sessions,
        "total_groups": total_groups,
        "active_groups": active_groups,
        "sent_24h": sent_24h,
        "success_rate": success_rate_24h,
        "total_sent": total_sum,
        "success_rate_24h": success_rate_24h
    }


async def log_send(
    user_id: int,
    chat_id: int,
    saved_msg_id: int,
    status: str = "success",
    error: str = None,
    phone: str = None
):
    """Log a message send attempt and update account stats."""
    db = get_database()
    
    now = datetime.utcnow()
    log_doc = {
        "user_id": user_id,
        "phone": phone,
        "chat_id": chat_id,
        "saved_msg_id": saved_msg_id,
        "sent_at": now,
        "status": status,
        "error": error,
    }
    
    # Use send_logs for detailed history (matching source logic)
    await db.send_logs.insert_one(log_doc)
    
    # Legacy compatibility: also log to job_logs for dashboard stats
    legacy_status = "sent" if status == "success" else status
    await db.job_logs.insert_one({
        "user_id": user_id,
        "phone": phone,
        "group_id": chat_id,
        "message_id": saved_msg_id,
        "status": legacy_status,
        "error": error,
        "timestamp": now
    })
    
    # Update session activity and success rate
    if phone:
        update_data = {"last_active_at": now}
        
        # Increment total/success counters in session for fast dashboard access
        inc_data = {"stats_total": 1}
        if status == "success":
            inc_data["stats_success"] = 1
            
        await db.sessions.update_one(
            {"user_id": user_id, "phone": phone},
            {"$set": update_data, "$inc": inc_data}
        )

async def get_active_workers() -> List[Dict[str, Any]]:
    """Get list of active workers that reported heartbeat in the last 2 minutes."""
    db = get_database()
    cutoff = datetime.utcnow() - timedelta(minutes=2)
    cursor = db.worker_status.find({"last_seen": {"$gt": cutoff}})
    return await cursor.to_list(length=100)
