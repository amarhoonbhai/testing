"""
Message templates for all bot screens.

Uses glass UI styling with unicode box drawing for premium look.
Pulls branding from config.
"""

from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME, MIN_INTERVAL

# ── Glass UI helpers ─────────────────────────────────────────────────────────
_TOP = "┌─────────────────────────────┐"
_BOT = "└─────────────────────────────┘"
_SEP = "├─────────────────────────────┤"


# ═══════════════════════════════════════════════════════════════════════════════
#  WELCOME / START
# ═══════════════════════════════════════════════════════════════════════════════

def welcome_text(
    first_name: str = "",
    last_name: str = "",
    user_id: int = 0,
    username: str = "",
) -> str:
    name = first_name
    if last_name:
        name += f" {last_name}"

    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>@{BOT_USERNAME}</b>\n"
        f"│  <i>The Future of Telegram Automation</i>\n"
        f"{_SEP}\n"
        f"│  👋 Welcome, <b>{name}</b>!\n"
        f"│\n"
        f"│  🆔 ID: <code>{user_id}</code>\n"
        f"│  👤 Username: @{username or '—'}\n"
        f"{_SEP}\n"
        f"│  • Premium Ad Broadcasting\n"
        f"│  • Smart Delays & Night Mode 🌙\n"
        f"│  • Multi-Account & Multi-Group\n"
        f"│  • Anti-Freeze Protection 🛡️\n"
        f"{_SEP}\n"
        f"│  💬 Support: @{SUPPORT_USERNAME}\n"
        f"│  📢 Updates: @{CHANNEL_USERNAME}\n"
        f"{_BOT}"
    )


def force_join_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>CHANNEL VERIFICATION</b>\n"
        f"{_SEP}\n"
        f"│  You must join our channels\n"
        f"│  before using this bot:\n"
        f"│\n"
        f"│  • @philobots\n"
        f"│  • @sellinghub0\n"
        f"│\n"
        f"│  Join all and click <b>Verify</b> ✅\n"
        f"{_BOT}"
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
    ad_status_icon = "✅ Set" if ad_set else "🔴 Not Set"

    if night_paused:
        ads_icon = "🌙 Night Mode"
    elif ads_status == "running":
        ads_icon = "▶️ Running"
    else:
        ads_icon = "⏸️ Paused"

    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>DASHBOARD</b>\n"
        f"│  @{BOT_USERNAME}\n"
        f"{_SEP}\n"
        f"│  📱 Accounts: <b>{account_count}/{max_accounts}</b>\n"
        f"│  📂 Groups: <b>{group_count}</b>\n"
        f"│  📝 Ad Message: <b>{ad_status_icon}</b>\n"
        f"│  ⏱️ Interval: <b>{interval}s</b> ({interval // 60} min)\n"
        f"│  📡 Status: <b>{ads_icon}</b>\n"
        f"{_SEP}\n"
        f"│  <i>Choose an action below</i>\n"
        f"{_BOT}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def add_account_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>HOST NEW ACCOUNT</b>\n"
        f"{_SEP}\n"
        f"│  🔒 Secure Account Hosting\n"
        f"│\n"
        f"│  Enter your phone number\n"
        f"│  with country code:\n"
        f"│\n"
        f"│  <code>Example: +1234567890</code>\n"
        f"│\n"
        f"│  <i>🔐 Your data is encrypted</i>\n"
        f"{_BOT}"
    )


def otp_prompt_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>VERIFICATION CODE</b>\n"
        f"{_SEP}\n"
        f"│  A login code has been sent\n"
        f"│  to your Telegram app.\n"
        f"│\n"
        f"│  Enter the <b>OTP code</b> below:\n"
        f"│\n"
        f"│  <i>⚠️ Never share this code</i>\n"
        f"{_BOT}"
    )


def password_2fa_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>TWO-FACTOR AUTH</b>\n"
        f"{_SEP}\n"
        f"│  Your account has 2FA enabled.\n"
        f"│\n"
        f"│  Enter your <b>cloud password</b>:\n"
        f"│\n"
        f"│  <i>🔒 Password is never stored</i>\n"
        f"{_BOT}"
    )


def account_added_text(phone_masked: str) -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>ACCOUNT HOSTED</b> ✅\n"
        f"{_SEP}\n"
        f"│  📱 Account: <code>{phone_masked}</code>\n"
        f"│  📡 Status: Active ✅\n"
        f"│  🔐 Session: Encrypted\n"
        f"│  🏷️ Branding: Applied\n"
        f"{_SEP}\n"
        f"│  <i>Ready for broadcasting</i>\n"
        f"{_BOT}"
    )


def no_accounts_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>NO ACCOUNTS HOSTED</b>\n"
        f"{_SEP}\n"
        f"│  Add an account to start!\n"
        f"{_BOT}"
    )


def accounts_list_text(accounts: list[dict]) -> str:
    lines = [f"{_TOP}", f"│  ⌞_⌝ <b>MY ACCOUNTS</b>", _SEP]
    for i, acc in enumerate(accounts, 1):
        status = "✅" if acc.get("status") == "active" else "⏸️"
        if acc.get("status") == "error":
            status = "❌"
        lines.append(f"│  {i}. {status} <code>{acc['phone_masked']}</code>")
    lines.append(_BOT)
    return "\n".join(lines)


def delete_confirm_text(phone_masked: str) -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>CONFIRM DELETION</b>\n"
        f"{_SEP}\n"
        f"│  Delete: <code>{phone_masked}</code>\n"
        f"│\n"
        f"│  ⚠️ Cannot be undone\n"
        f"{_BOT}"
    )


def account_deleted_text(phone_masked: str) -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>ACCOUNT DELETED</b> 🗑️\n"
        f"{_SEP}\n"
        f"│  <code>{phone_masked}</code> removed.\n"
        f"│  Session securely destroyed.\n"
        f"{_BOT}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def groups_text(total: int, active: int, disabled: int) -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>MANAGE GROUPS</b>\n"
        f"{_SEP}\n"
        f"│  📂 Total: <b>{total}</b>\n"
        f"│  ✅ Active: <b>{active}</b>\n"
        f"│  🔴 Disabled: <b>{disabled}</b>\n"
        f"{_SEP}\n"
        f"│  <i>Add groups, folders, or channels</i>\n"
        f"{_BOT}"
    )


def add_groups_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>ADD GROUPS</b>\n"
        f"{_SEP}\n"
        f"│  Send links — <b>one per line</b>:\n"
        f"│\n"
        f"│  • <code>https://t.me/group</code>\n"
        f"│  • <code>https://t.me/+invite</code>\n"
        f"│  • <code>https://t.me/addlist/folder</code>\n"
        f"│  • <code>@username</code>\n"
        f"│\n"
        f"│  💡 <i>Paste multiple at once</i>\n"
        f"{_BOT}"
    )


def groups_added_text(added: int, failed: int) -> str:
    lines = [_TOP, f"│  ⌞_⌝ <b>GROUPS UPDATED</b>", _SEP]
    lines.append(f"│  ✅ Added: <b>{added}</b>")
    if failed:
        lines.append(f"│  ❌ Invalid: <b>{failed}</b>")
    lines.append(_BOT)
    return "\n".join(lines)


def no_groups_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>NO GROUPS ADDED</b>\n"
        f"{_SEP}\n"
        f"│  Add groups to start broadcasting!\n"
        f"{_BOT}"
    )


def groups_list_text(groups: list[dict]) -> str:
    lines = [_TOP, f"│  ⌞_⌝ <b>YOUR GROUPS</b>", _SEP]
    for i, g in enumerate(groups[:50], 1):
        status = "✅" if g.get("status") == "active" else "🔴"
        ident = g.get("identifier", "?")
        sent = g.get("send_count", 0)
        lines.append(f"│  {i}. {status} <code>{ident}</code> — sent: {sent}")
    total = len(groups)
    if total > 50:
        lines.append(f"│  <i>... and {total - 50} more</i>")
    lines.append(_BOT)
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  ADS
# ═══════════════════════════════════════════════════════════════════════════════

def set_ad_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>SET AD MESSAGE</b>\n"
        f"{_SEP}\n"
        f"│  Send your ad content now:\n"
        f"│\n"
        f"│  • Text message\n"
        f"│  • Photo with caption\n"
        f"│  • Video with caption\n"
        f"│\n"
        f"│  <i>💡 Include links for best results</i>\n"
        f"{_BOT}"
    )


def ad_saved_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>AD MESSAGE SAVED</b> ✅\n"
        f"{_SEP}\n"
        f"│  Your ad has been saved.\n"
        f"│  Used in the next broadcast cycle.\n"
        f"{_BOT}"
    )


def set_interval_text() -> str:
    min_minutes = MIN_INTERVAL // 60
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>SET TIME INTERVAL</b>\n"
        f"{_SEP}\n"
        f"│  Enter delay in seconds.\n"
        f"│  ⏱️ Min: <b>{MIN_INTERVAL}s</b> ({min_minutes} min)\n"
        f"│\n"
        f"│  • <code>{MIN_INTERVAL}</code> = {min_minutes} min\n"
        f"│  • <code>1800</code> = 30 min\n"
        f"│  • <code>3600</code> = 1 hour\n"
        f"│  • <code>7200</code> = 2 hours\n"
        f"{_BOT}"
    )


def interval_saved_text(seconds: int) -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>INTERVAL UPDATED</b> ✅\n"
        f"{_SEP}\n"
        f"│  Set to <b>{seconds}s</b> ({seconds // 60} min)\n"
        f"{_BOT}"
    )


def ads_started_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>ADVERTISING STARTED</b> ▶️\n"
        f"{_SEP}\n"
        f"│  Broadcasting is now active.\n"
        f"│\n"
        f"│  🌙 Night mode: 12 AM – 5 AM\n"
        f"│  🛡️ Anti-freeze: ON\n"
        f"│  ⏱️ Smart delays: ON\n"
        f"{_SEP}\n"
        f"│  <i>⚠️ Comply with Telegram ToS</i>\n"
        f"{_BOT}"
    )


def ads_stopped_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>ADVERTISING PAUSED</b> ⏸️\n"
        f"{_SEP}\n"
        f"│  Broadcasting paused.\n"
        f"│  No messages until resumed.\n"
        f"{_BOT}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

def analytics_text(
    total_sent: int,
    failed_count: int,
    active_accounts: int,
    last_broadcast: str,
    current_status: str,
    group_count: int = 0,
) -> str:
    if current_status == "running":
        status_icon = "▶️ Running"
    elif current_status == "night_paused":
        status_icon = "🌙 Night Mode"
    else:
        status_icon = "⏸️ Paused"

    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>ADS ANALYTICS</b>\n"
        f"{_SEP}\n"
        f"│  📤 Sent: <b>{total_sent}</b>\n"
        f"│  ❌ Failed: <b>{failed_count}</b>\n"
        f"│  📱 Accounts: <b>{active_accounts}</b>\n"
        f"│  📂 Groups: <b>{group_count}</b>\n"
        f"│  🕐 Last: <b>{last_broadcast}</b>\n"
        f"│  📡 Status: <b>{status_icon}</b>\n"
        f"{_BOT}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO REPLY
# ═══════════════════════════════════════════════════════════════════════════════

def auto_reply_text(enabled: bool, reply_text: str | None) -> str:
    status = "✅ Enabled" if enabled else "🔴 Disabled"
    current = reply_text if reply_text else "Not Set"
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>AUTO REPLY</b>\n"
        f"{_SEP}\n"
        f"│  Status: <b>{status}</b>\n"
        f"│  Text: <i>{current}</i>\n"
        f"{_BOT}"
    )


def set_auto_reply_prompt_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>SET AUTO REPLY</b>\n"
        f"{_SEP}\n"
        f"│  Send the reply text.\n"
        f"│  <i>Auto-sent when someone</i>\n"
        f"│  <i>messages your account.</i>\n"
        f"{_BOT}"
    )


def auto_reply_saved_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>AUTO REPLY SAVED</b> ✅\n"
        f"{_SEP}\n"
        f"│  Message updated.\n"
        f"{_BOT}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  HOW TO USE (GUIDE)
# ═══════════════════════════════════════════════════════════════════════════════

def how_to_use_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>USER GUIDE</b>\n"
        f"│  @{BOT_USERNAME}\n"
        f"{_SEP}\n"
        f"│\n"
        f"│  <b>Step 1: Add Account</b>\n"
        f"│  Dashboard → Add Accounts\n"
        f"│  → Phone → OTP → Done\n"
        f"│\n"
        f"│  <b>Step 2: Add Groups</b>\n"
        f"│  Dashboard → Manage Groups\n"
        f"│  → Add Groups → Paste links\n"
        f"│\n"
        f"│  <b>Step 3: Set Ad</b>\n"
        f"│  Dashboard → Set Ad Message\n"
        f"│  → Send text/photo/video\n"
        f"│\n"
        f"│  <b>Step 4: Set Interval</b>\n"
        f"│  Dashboard → Set Interval\n"
        f"│  → Min {MIN_INTERVAL}s ({MIN_INTERVAL // 60} min)\n"
        f"│\n"
        f"│  <b>Step 5: Start Ads</b>\n"
        f"│  Dashboard → Start Ads ▶️\n"
        f"{_SEP}\n"
        f"│  🛡️ <b>Safety Features</b>\n"
        f"│  • 🌙 Night mode 12–5 AM IST\n"
        f"│  • ⏱️ 300s smart delays\n"
        f"│  • 🔄 Auto-restart after night\n"
        f"│  • 🛡️ FloodWait protection\n"
        f"│  • 🔒 Encrypted sessions\n"
        f"{_BOT}"
    )


def disclaimer_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>DISCLAIMER</b> ⚖️\n"
        f"{_SEP}\n"
        f"│\n"
        f"│  This bot is designed for\n"
        f"│  <b>legitimate opt-in marketing</b>\n"
        f"│  purposes only.\n"
        f"│\n"
        f"│  By using this bot you agree:\n"
        f"│\n"
        f"│  1. You will only broadcast to\n"
        f"│     groups/channels you own or\n"
        f"│     have permission to post in.\n"
        f"│\n"
        f"│  2. You will comply with\n"
        f"│     Telegram's Terms of Service.\n"
        f"│\n"
        f"│  3. You are solely responsible\n"
        f"│     for content you broadcast.\n"
        f"│\n"
        f"│  4. Spamming, scraping, or mass\n"
        f"│     unsolicited messaging is\n"
        f"│     strictly prohibited.\n"
        f"│\n"
        f"│  5. The developers are not liable\n"
        f"│     for any misuse of this tool.\n"
        f"│\n"
        f"│  ⚠️ <b>Violation may result in\n"
        f"│  account restrictions by Telegram.</b>\n"
        f"{_BOT}"
    )


def powered_by_text() -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>POWERED BY</b>\n"
        f"{_SEP}\n"
        f"│  @{BOT_USERNAME}\n"
        f"│  Premium Telegram Automation\n"
        f"│\n"
        f"│  💬 Support: @{SUPPORT_USERNAME}\n"
        f"│  📢 Updates: @{CHANNEL_USERNAME}\n"
        f"│\n"
        f"│  <i>Built with ❤️</i>\n"
        f"{_BOT}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ERRORS
# ═══════════════════════════════════════════════════════════════════════════════

def error_text(message: str) -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>ERROR</b> ❌\n"
        f"{_SEP}\n"
        f"│  {message}\n"
        f"{_BOT}"
    )


def max_accounts_text(max_count: int) -> str:
    return (
        f"{_TOP}\n"
        f"│  ⌞_⌝ <b>LIMIT REACHED</b>\n"
        f"{_SEP}\n"
        f"│  Max <b>{max_count}</b> accounts.\n"
        f"│  Delete one to add new.\n"
        f"{_BOT}"
    )
