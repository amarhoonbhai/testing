"""
Code model — redeem codes for plan activation.
"""

import secrets
from datetime import datetime
from typing import Optional, Dict, Any

from core.database import get_database

async def generate_redeem_code(plan_type: str, created_by: int) -> str:
    """Generate a unique redeem code for a specific plan."""
    db = get_database()
    code = f"ADS-{secrets.token_hex(4).upper()}"
    
    await db.codes.insert_one({
        "code": code,
        "plan_type": plan_type,
        "created_by": created_by,
        "created_at": datetime.utcnow(),
        "used_by": None,
        "used_at": None,
        "status": "active"
    })
    
    return code

async def redeem_code(user_id: int, code_str: str) -> Optional[str]:
    """Redeem a code and activate the corresponding plan. Returns plan_type or None."""
    db = get_database()
    code_str = code_str.strip().upper()
    
    code = await db.codes.find_one({"code": code_str, "status": "active"})
    if not code:
        return None
        
    await db.codes.update_one(
        {"code": code_str},
        {
            "$set": {
                "status": "used",
                "used_by": user_id,
                "used_at": datetime.utcnow()
            }
        }
    )
    
    plan_type = code["plan_type"]
    from models.plan import activate_plan
    await activate_plan(user_id, plan_type)
    
    return plan_type
