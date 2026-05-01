"""
Premium Message templates — Kurup Ads Bot.

Modern, professional, and minimalist aesthetic.
Using clean dividers and clear structural hierarchy.
"""

from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME, MIN_INTERVAL


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _header(title: str) -> str:
    return (
        f"─── ✦ ───\n"
        f"<b>{title}</b>\n"
        f"─── ✦ ───\n\n"
    )

def _footer() -> str:
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"@{BOT_USERNAME}  ·  @philobots"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  WELCOME
# ═══════════════════════════════════════════════════════════════════════════════

def welcome_text(
    first_name: str = "",
    last_name: str = "",
    user_id: int = 0,
    username: str = "",
) -> str:
    name = f"{first_name} {last_name}".strip()
    return (
        f"{_header('Kᴜʀᴜᴘ Aᴅs Eɴɢɪɴᴇ')}"
        f"Hello, <b>{name}</b> 👋\n\n"
        f"┊ ID       <code>{user_id}</code>\n"
        f"┊ Handle   @{username or 'None'}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Your complete broadcast\n"
        f"automation platform.\n\n"
        f"┊ Encrypted sessions\n"
        f"┊ Smart scheduling\n"
        f"┊ Multi-account support\n"
        f"┊ Night-safe mode"
        f"{_footer()}"
    )


def force_join_text() -> str:
    return (
        f"{_header('Aᴄᴄᴇss Rᴇsᴛʀɪᴄᴛᴇᴅ')}"
        f"To activate your session, please\n"
        f"join our official network:\n\n"
        f"‣ @philobots\n"
        f"‣ @sellinghub0\n\n"
        f"Tap <b>Verify</b> once joined."
        f"{_footer()}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def dashboard_text(
    account_count: int,
    max_accounts: int,
    ad_set: bool,
    interval: int,
    ads_status: str,
    group_count: int = 0,
    night_paused: bool = False,
) -> str:
    status_icon = "🟢" if ads_status == "running" else "🔴"
    if night_paused:
        status_icon = "🌙"
        status_text = "NIGHT STANDBY"
    else:
        status_text = "LIVE" if ads_status == "running" else "IDLE"

    return (
        f"{_header('Cᴏᴍᴍᴀɴᴅ Cᴇɴᴛᴇʀ')}"
        f"<b>Sʏsᴛᴇᴍ Sᴛᴀᴛs</b>\n"
        f"┊ Accounts   {account_count} / {max_accounts}\n"
        f"┊ Targets    {group_count} groups\n"
        f"┊ Ad Copy    {'Ready' if ad_set else 'Missing'}\n"
        f"┊ Interval   {interval // 60} min\n\n"
        f"<b>Oᴘᴇʀᴀᴛɪᴏɴᴀʟ Sᴛᴀᴛᴜs</b>\n"
        f"┊ Status     {status_icon} <b>{status_text}</b>"
        f"{_footer()}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def add_account_text() -> str:
    return (
        f"{_header('Lɪɴᴋ Aᴄᴄᴏᴜɴᴛ')}"
        f"Please provide the phone number\n"
        f"for the account you wish to host.\n\n"
        f"‣ Format: <code>+1234567890</code>\n"
        f"‣ Status: Encrypted"
        f"{_footer()}"
    )


def otp_prompt_text() -> str:
    return (
        f"{_header('Vᴇʀɪғɪᴄᴀᴛɪᴏɴ')}"
        f"A login code has been issued to\n"
        f"your Telegram account.\n\n"
        f"Please input the code below.\n"
        f"┊ <i>Waiting for input...</i>"
        f"{_footer()}"
    )


def password_2fa_text() -> str:
    return (
        f"{_header('Cʟᴏᴜᴅ Pᴀssᴡᴏʀᴅ')}"
        f"Your account is protected by 2FA.\n"
        f"Please input your password:\n\n"
        f"┊ 🔒 AES-256 Encrypted"
        f"{_footer()}"
    )


def account_added_text(phone_masked: str) -> str:
    return (
        f"{_header('Sʏɴᴄ Cᴏᴍᴘʟᴇᴛᴇ')}"
        f"Account <code>{phone_masked}</code> has\n"
        f"been successfully synchronized.\n\n"
        f"┊ Branding: Applied\n"
        f"┊ Status: <b>ACTIVE</b>"
        f"{_footer()}"
    )


def no_accounts_text() -> str:
    return (
        f"{_header('Nᴏ Aᴄᴄᴏᴜɴᴛs')}"
        f"No active accounts found.\n"
        f"Please link an account to begin."
        f"{_footer()}"
    )


def accounts_list_text(accounts: list[dict]) -> str:
    text = f"{_header('Hᴏsᴛᴇᴅ Aᴄᴄᴏᴜɴᴛs')}"
    for i, acc in enumerate(accounts, 1):
        status = "✅" if acc.get("status") == "active" else "❌"
        health = acc.get("health", 100)
        text += f"   {i}. {status} <code>{acc['phone_masked']}</code> ({health}%)\n"
    
    if not accounts:
        text += "   <i>No accounts linked yet.</i>\n"
        
    text += _footer()
    return text


def delete_confirm_text(phone_masked: str) -> str:
    return (
        f"{_header('Cᴏɴғɪʀᴍ Pᴜʀɢᴇ')}"
        f"Are you sure you want to remove\n"
        f"account: <code>{phone_masked}</code>?\n\n"
        f"⚠️ <b>This action is irreversible.</b>"
        f"{_footer()}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def groups_text(total: int, active: int, disabled: int) -> str:
    return (
        f"{_header('Tᴀʀɢᴇᴛ Mᴀɴᴀɢᴇᴍᴇɴᴛ')}"
        f"┊ Total Targets   {total}\n"
        f"┊ Active Pools    {active}\n"
        f"┊ Excluded        {disabled}\n\n"
        f"────────────────────────\n"
        f"<i>Pruning dead links automatically...</i>"
        f"{_footer()}"
    )


def add_groups_text() -> str:
    return (
        f"{_header('Iᴍᴘᴏʀᴛ Tᴀʀɢᴇᴛs')}"
        f"Please send the links or usernames\n"
        f"of your target groups/channels.\n\n"
        f"‣ Format: One per line\n"
        f"‣ Supports: Folder Links (addlist)"
        f"{_footer()}"
    )


def groups_added_text(added: int, failed: int) -> str:
    return (
        f"{_header('Iᴍᴘᴏʀᴛ Cᴏᴍᴘʟᴇᴛᴇ')}"
        f"┊ Successfully Added   {added}\n"
        f"┊ Failed/Duplicate      {failed}"
        f"{_footer()}"
    )


def no_groups_text() -> str:
    return (
        f"{_header('Nᴏ Tᴀʀɢᴇᴛs')}"
        f"The broadcast list is empty.\n"
        f"Please import target groups."
        f"{_footer()}"
    )


def groups_list_text(groups: list[dict]) -> str:
    text = f"{_header('Tᴀʀɢᴇᴛ Mᴀɴɪғᴇsᴛ')}"
    for i, g in enumerate(groups[:25], 1):
        status = "●" if g.get("status") == "active" else "○"
        text += f"   {i}. {status} {g['identifier']}\n"
    
    if len(groups) > 25:
        text += f"\n   <i>...and {len(groups) - 25} more.</i>\n"
    
    text += _footer()
    return text


# ═══════════════════════════════════════════════════════════════════════════════
#  TIMING & INTERVAL
# ═══════════════════════════════════════════════════════════════════════════════

def set_interval_text() -> str:
    return (
        f"{_header('Sᴄʜᴇᴅᴜʟᴇ Tɪᴍɪɴɢ')}"
        f"Input the delay between cycles\n"
        f"in seconds.\n\n"
        f"‣ Minimum: {MIN_INTERVAL}s\n"
        f"‣ Default: 1200s (20 min)"
        f"{_footer()}"
    )


def interval_saved_text(seconds: int) -> str:
    return (
        f"{_header('Sᴄʜᴇᴅᴜʟᴇ Sᴀᴠᴇᴅ')}"
        f"Global broadcast interval set to:\n"
        f"┊ <b>{seconds // 60} minutes</b>\n\n"
        f"<i>Safe-mode active.</i>"
        f"{_footer()}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ADS / BROADCAST
# ═══════════════════════════════════════════════════════════════════════════════

def ads_started_text() -> str:
    return (
        f"{_header('Eɴɢɪɴᴇ Lɪᴠᴇ')}"
        f"Broadcast automation has been\n"
        f"successfully initiated.\n\n"
        f"┊ Monitoring: Logs Channel\n"
        f"┊ Mode: Global Pool"
        f"{_footer()}"
    )


def ads_stopped_text() -> str:
    return (
        f"{_header('Eɴɢɪɴᴇ Hᴀʟᴛᴇᴅ')}"
        f"The broadcast engine has been\n"
        f"stopped by the operator."
        f"{_footer()}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

def analytics_text(total_sent: int, failed_count: int, last_sent: str = "Never") -> str:
    success_rate = 0
    if (total_sent + failed_count) > 0:
        success_rate = (total_sent / (total_sent + failed_count)) * 100

    return (
        f"{_header('Pᴇʀғᴏʀᴍᴀɴᴄᴇ Rᴇᴘᴏʀᴛ')}"
        f"┊ Total Sent      {total_sent}\n"
        f"┊ Total Failed    {failed_count}\n"
        f"┊ Success Rate    {success_rate:.1f}%\n"
        f"┊ Last Active     {last_sent}"
        f"{_footer()}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO REPLY
# ═══════════════════════════════════════════════════════════════════════════════

def auto_reply_text(enabled: bool, reply_text: str = "") -> str:
    status = "ENABLED" if enabled else "DISABLED"
    return (
        f"{_header('Aᴜᴛᴏ Rᴇsᴘᴏɴᴅᴇʀ')}"
        f"┊ Status: <b>{status}</b>\n\n"
        f"<b>Current Response:</b>\n"
        f"<i>{reply_text or 'Not set'}</i>"
        f"{_footer()}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ERROR / GENERIC
# ═══════════════════════════════════════════════════════════════════════════════

def error_text(msg: str) -> str:
    return (
        f"─── ⚠️ ───\n"
        f"<b>Sʏsᴛᴇᴍ Eʀʀᴏʀ</b>\n"
        f"─── ⚠️ ───\n\n"
        f"{msg}\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )


def how_to_use_text() -> str:
    return (
        f"{_header('Oᴘᴇʀᴀᴛɪᴏɴs Gᴜɪᴅᴇ')}"
        f"1. <b>Link Account</b>: Sync your Telegram.\n"
        f"2. <b>Set Ad</b>: Compose your creative.\n"
        f"3. <b>Targets</b>: Import group links.\n"
        f"4. <b>Go Live</b>: Start broadcasting."
        f"{_footer()}"
    )


def disclaimer_text() -> str:
    return (
        f"{_header('Lᴇɢᴀʟ Tᴇʀᴍs')}"
        f"By using this bot, you agree to:\n\n"
        f"‣ Not broadcast illegal content\n"
        f"‣ Accept all account risks\n"
        f"‣ Comply with Telegram TOS"
        f"{_footer()}"
    )
