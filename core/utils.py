"""
V5 Elite Core Utilities.
Hardened Universal Link Parser with Supergroup ID Normalization.
"""

import re
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_group_entry(entry: str):
    """
    Bulletproof Universal Parser for Telegram links.
    Returns: (target, slug, display_title, link_type)
    """
    entry = entry.strip()

    # 1. Raw numeric ID (e.g. -1001234567890)
    if re.match(r'^-?\d+$', entry):
        chat_id = int(entry)
        # Normalize: if it's a 10-digit negative ID, it's likely a supergroup missing -100
        if chat_id < 0 and -9999999999 < chat_id < -100000000:
            chat_id = int(f"-100{abs(chat_id)}")
        return chat_id, None, f"ID: {chat_id}", "id"

    # 2. Chatlist (addlist) Folder Links
    if "/addlist/" in entry:
        match = re.search(r'(?:t\.me|telegram\.me|telegram\.dog)/addlist/([A-Za-z0-9_-]+)', entry)
        if match:
            slug = match.group(1)
            return slug, slug, f"Chatlist: {slug}", "addlist"

    # 3. Private Invite Links (t.me/+Hash or t.me/joinchat/Hash)
    # MUST CAPTURE FULL HASH
    private_match = re.search(r'(?:t\.me|telegram\.me|telegram\.dog|tg://join\?invite=)(?:\/|\+?|joinchat\/)([A-Za-z0-9_\-]+)', entry)
    if private_match:
        # Extra check to ensure it's not a public slug
        if "/+" in entry or "joinchat/" in entry or "invite=" in entry:
            invite_hash = private_match.group(1)
            # Use a deterministic ID for storage, but return the FULL hash for joining
            chat_id = abs(hash(f"invite:{invite_hash}")) % 10**12 * -1
            return invite_hash, None, f"[Private] +{invite_hash[:8]}...", "private"

    # 4. Message/Channel Links with Numeric IDs (https://t.me/c/12345/1)
    cid_match = re.search(r'(?:t\.me|telegram\.me|telegram\.dog)/c/(\d+)', entry)
    if cid_match:
        chat_id = int(f"-100{cid_match.group(1)}")
        return chat_id, None, f"ID: {chat_id}", "id"

    # 5. Public Links (@username, t.me/username, telegram.dog/username)
    clean = re.sub(r'https?://(t\.me|telegram\.me|telegram\.dog)/', '', entry)
    clean = re.sub(r'tg://resolve\?domain=', '', clean)
    slug = clean.lstrip('@').split('?')[0].split('/')[0].strip()

    if re.match(r'^[A-Za-z][\w_]{3,}$', slug):
        chat_id = slug_to_id(slug)
        return slug, slug, f"@{slug}", "public"

    raise ValueError(f"Unrecognized link format: {entry}")

def slug_to_id(slug: str) -> int:
    """Deterministic hash for placeholder IDs before Telegram resolution."""
    h = int(hashlib.md5(slug.lower().encode()).hexdigest(), 16) % 10**9
    return -int(h)

def escape_markdown(text: str) -> str:
    """Legacy Markdown escaping."""
    if not text: return ""
    return re.sub(r'([_*\[\]])', r'\\\1', str(text))

def escape_markdown_v2(text: str) -> str:
    """
    Escape characters for Telegram's MarkdownV2 parser.
    Escapes: \ _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    if not text: return ""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

def build_connection_success_text(phone: str, branding_active: bool = True) -> str:
    """Standardized success message after account connection."""
    branding_tag = "🟢 ACTIVE" if branding_active else "🔴 MISSING"
    
    return f"""
✅ <b>Account Connected Successfully!</b>

📱 <code>{phone}</code> is now linked.

🚀 <b>KURUP ADS — FREE EDITION</b>
📢 <b>Branding:</b> {branding_tag}

Open the dashboard to configure groups and start sending.
"""
