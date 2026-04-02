"""
Settings model — global system configuration.
"""

from datetime import datetime
from typing import Dict, Any

from core.database import get_database

async def get_global_settings() -> Dict[str, Any]:
    """Get global system settings, creating default if not exists."""
    db = get_database()
    settings = await db.settings.find_one({"key": "global"})
    
    if not settings:
        settings = {
            "key": "global",
            "all_bots_active": True,
            "night_mode_force": "auto",  # auto, on, off
            "updated_at": datetime.utcnow()
        }
        await db.settings.insert_one(settings)
    
    return settings

async def update_global_settings(**kwargs):
    """Update global system settings."""
    db = get_database()
    kwargs["updated_at"] = datetime.utcnow()
    await db.settings.update_one(
        {"key": "global"},
        {"$set": kwargs},
        upsert=True
    )
