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


def parse_group_entry(entry: str):
    """
    Parse any supported group link format and return (chat_id, chat_username, title).
    """
    import hashlib
    entry = entry.strip()

    # Raw numeric ID (e.g. -1001234567890)
    if re.match(r'^-?\d+$', entry):
        chat_id = int(entry)
        return chat_id, None, str(chat_id)

    # @username
    if entry.startswith("@"):
        slug = entry[1:].split('?')[0].strip()
        chat_id = slug_to_id(slug)
        return chat_id, slug, slug

    # tg://resolve?domain=name
    tg_match = re.match(r'tg://resolve\?domain=([\w_]+)', entry)
    if tg_match:
        slug = tg_match.group(1)
        return slug_to_id(slug), slug, slug

    # https://t.me/addlist/... (folder links)
    if 't.me/addlist/' in entry:
        slug = entry.split('addlist/')[-1].split('?')[0].strip('/')
        # Store folder links with a recognisable fake numeric ID
        chat_id = abs(hash(f"folder:{slug}")) % 10**12 * -1
        return chat_id, None, f"[Folder] {slug}"

    # https://t.me/+Hash (private invite)
    plus_match = re.search(r't\.me/\+([A-Za-z0-9_\-]+)', entry)
    if plus_match:
        invite_hash = plus_match.group(1)
        chat_id = abs(hash(f"invite:{invite_hash}")) % 10**12 * -1
        return chat_id, None, f"[Private] +{invite_hash[:12]}"

    # https://t.me/username (public)
    public_match = re.search(r't\.me/([A-Za-z][\w_]{3,})', entry)
    if public_match:
        slug = public_match.group(1)
        return slug_to_id(slug), slug, slug

    raise ValueError("Unrecognized link format")


def slug_to_id(slug: str) -> int:
    """Convert a public username/slug to a stable numeric ID."""
    import hashlib
    h = int(hashlib.md5(slug.lower().encode()).hexdigest(), 16) % 10**9
    return -int(h)  # negative = group namespace
