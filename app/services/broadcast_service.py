"""
Broadcast service — Decoupled bridge for distributed workers.
"""

import logging
from app.database.models import update_user, cancel_user_jobs, get_user, get_user_accounts, get_group_count

logger = logging.getLogger(__name__)

async def start_broadcast(user_id: int) -> dict:
    """Start the broadcast (sets status for scheduler)."""
    user = await get_user(user_id)
    if not user: return {"success": False, "error": "User not found."}
    
    accounts = await get_user_accounts(user_id)
    active_accounts = [a for a in accounts if a.get("status") == "active"]
    if not active_accounts:
        return {"success": False, "error": "No active accounts linked."}
        
    if await get_group_count(user_id) == 0:
        return {"success": False, "error": "No target groups added."}
        
    if not user.get("ads"):
        return {"success": False, "error": "No ads configured."}

    # Update status to running. Scheduler will pick this up.
    await update_user(user_id, ads_status="running")
    logger.info(f"Broadcast status set to RUNNING for {user_id}")
    return {"success": True}


async def stop_broadcast(user_id: int) -> dict:
    """Stop the broadcast (sets status and clears pending jobs)."""
    await update_user(user_id, ads_status="paused")
    # Cancel any pending jobs in the queue
    deleted = await cancel_user_jobs(user_id)
    logger.info(f"Broadcast status set to PAUSED for {user_id}. {deleted} jobs cancelled.")
    return {"success": True}


def is_broadcasting(user_id: int) -> bool:
    """Check if a user is in running state (simplified)."""
    # This is used by some UI elements, but we can't easily check 'active' tasks anymore.
    # We return False and let the UI use the user['ads_status'] instead.
    return False

def get_active_broadcast_count() -> int:
    """Not applicable in distributed mode."""
    return 0

async def start_orchestrator():
    """No longer used in this process."""
    logger.info("Local Orchestrator: DISABLED (Using distributed scheduler/workers)")
    pass
