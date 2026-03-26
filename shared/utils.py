"""
Shared utility functions for Group Message Scheduler.
"""

import re

def escape_markdown(text: str) -> str:
    """
    Escape markdown characters for Telegram's legacy Markdown parser.
    Escapes: _, *, [, ]
    """
    if not text:
        return ""
    return re.sub(r'([_*\[\]])', r'\\\1', str(text))

def build_connection_success_text(phone: str, plan: dict) -> str:
    """
    Build standardized success message after account connection.
    Used by both OTP and 2FA flows.
    """
    from datetime import datetime

    plan_type = plan.get("plan_type", "free") if plan else "free"
    
    if plan and plan.get("plan_type") == "premium" and plan.get("expires_at"):
        expires_at = plan["expires_at"]
        days_left = (expires_at - datetime.utcnow()).days
        hours_left = (expires_at - datetime.utcnow()).seconds // 3600
        time_left = f"{days_left}d {hours_left}h" if days_left > 0 else f"{hours_left}h"
        return f"""
✅ *Account Connected Successfully!*

📱 `{phone}` is now linked.

💎 *Plan:* PREMIUM
⏳ *Remaining:* {time_left}

🚀 Open the dashboard to configure groups and start sending.
"""
    else:
        # Free plan
        return f"""
✅ *Account Connected to KURUP ADS!*

📱 `{phone}` is now linked to your account.

🆓 *Plan:* Free (No Expiry)
✅ Start forwarding right away!

👇 Open the dashboard to add your groups and begin.
"""
