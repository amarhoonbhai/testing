"""
V5 Elite Core Utilities.
Centralized helpers for text processing, group parsing, and UI building.
"""

import re
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

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
    plan_type = plan.get("plan_type", "free") if plan else "free"
    
    if plan and plan.get("plan_type") == "premium" and plan.get("expires_at"):
        expires_at = plan["expires_at"]
        now = datetime.utcnow()
        diff = expires_at - now
        days_left = diff.days
        hours_left = diff.seconds // 3600
        time_left = f"{days_left}d {hours_left}h" if days_left > 0 else f"{hours_left}h"
        
        return f"""
✅ *Account Connected Successfully!*

📱 `{phone}` is now linked.

💎 *Plan:* PREMIUM
⏳ *Remaining:* {time_left}

🚀 Open the dashboard to configure groups and start sending.
"""
    else:
        return f"""
✅ *Account Connected to KURUP ADS!*

📱 `{phone}` is now linked to your account.

🆓 *Plan:* Free (No Expiry)
✅ Start forwarding right away!

👇 Open the dashboard to add your groups and begin.
"""

def parse_group_entry(entry: str):
    """
    Parse any supported group link format and return (chat_id, chat_username, title).
    Handles public usernames, private invite hashes, and numeric IDs.
    """
    entry = entry.strip()

    # 1. Raw numeric ID (e.g. -1001234567890)
    if re.match(r'^-?\d+$', entry):
        chat_id = int(entry)
        return chat_id, None, f"Group {chat_id}"

    # 2. Private Invite Links (t.me/+Hash or t.me/joinchat/Hash)
    private_match = re.search(r'(t\.me/|tg://join\?invite=)(\+?|joinchat/)([A-Za-z0-9_\-]+)', entry)
    if private_match:
        invite_hash = private_match.group(3)
        # Deterministic fake ID for tracking before join
        chat_id = abs(hash(f"invite:{invite_hash}")) % 10**12 * -1
        return chat_id, None, f"[Private] +{invite_hash[:10]}"

    # 3. Private Link with ID (https://t.me/c/123456789/1)
    cid_match = re.search(r't\.me/c/(\d+)', entry)
    if cid_match:
        chat_id = -int(f"100{cid_match.group(1)}")
        return chat_id, None, f"Group {chat_id}"

    # 4. Public @username or t.me/username
    slug = entry
    if 't.me/' in slug:
        slug = slug.split('t.me/')[-1]
    if 'tg://resolve?domain=' in slug:
        slug = slug.split('domain=')[-1]
    slug = slug.lstrip('@').split('?')[0].split('/')[0].strip()

    if re.match(r'^[A-Za-z][\w_]{3,}$', slug):
        chat_id = slug_to_id(slug)
        return chat_id, slug, f"@{slug}"

    raise ValueError(f"Unrecognized link format: {entry}")

def slug_to_id(slug: str) -> int:
    """Convert a public username/slug to a stable numeric ID."""
    h = int(hashlib.md5(slug.lower().encode()).hexdigest(), 16) % 10**9
    return -int(h)
