"""
Premium Message templates — Kurup Ads Bot.

Modern, professional, and minimalist aesthetic.
Using clean dividers and clear structural hierarchy.
"""

from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME, MIN_INTERVAL


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
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>OPERATOR PROFILE</b>\n"
        f"\n"
        f"  👤 Name: {name}\n"
        f"  🆔 User ID: <code>{user_id}</code>\n"
        f"  🔗 Handle: @{username or 'None'}\n"
        f"\n"
        f"<b>SYSTEM STATUS</b>\n"
        f"  🛡 Security: Encrypted (AES-256)\n"
        f"  ⚡ Engine: v2.0 Production\n"
        f"\n"
        f"────────────────────────\n"
        f"<i>Securely managing your Telegram automation.</i>"
    )


def force_join_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>ACCESS RESTRICTED</b>\n"
        f"\n"
        f"To activate your session, please\n"
        f"join our official network:\n"
        f"\n"
        f"  📡 @philobots\n"
        f"  🛍 @sellinghub0\n"
        f"\n"
        f"Tap 'Verify' once joined.\n"
        f"────────────────────────"
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
        status_text = "Night Standby"
    else:
        status_text = "Live" if ads_status == "running" else "Idle"

    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>COMMAND CENTER</b>\n"
        f"\n"
        f"  📱 Accounts: {account_count} / {max_accounts}\n"
        f"  📂 Targets: {group_count} groups\n"
        f"  📝 Ad Copy: {'Ready' if ad_set else 'Missing'}\n"
        f"  ⏱ Interval: {interval // 60} minutes\n"
        f"\n"
        f"  STATUS: {status_icon} <b>{status_text}</b>\n"
        f"────────────────────────\n"
        f"<i>Select a module to manage:</i>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def add_account_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>LINK ACCOUNT</b>\n"
        f"\n"
        f"Please provide the phone number\n"
        f"for the account you wish to host.\n"
        f"\n"
        f"Format: <code>+1234567890</code>\n"
        f"────────────────────────"
    )


def otp_prompt_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>VERIFICATION</b>\n"
        f"\n"
        f"A login code has been issued to\n"
        f"your Telegram account.\n"
        f"\n"
        f"Please input the code below.\n"
        f"────────────────────────"
    )


def password_2fa_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>CLOUD PASSWORD</b>\n"
        f"\n"
        f"Your account is protected by 2FA.\n"
        f"Please input your password:\n"
        f"────────────────────────"
    )


def account_added_text(phone_masked: str) -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>SUCCESS</b>\n"
        f"\n"
        f"Account <code>{phone_masked}</code> has\n"
        f"been successfully synchronized.\n"
        f"\n"
        f"Branding applied: ‣ Kurup Ads\n"
        f"────────────────────────"
    )


def no_accounts_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>NO ACCOUNTS</b>\n"
        f"\n"
        f"No active accounts found.\n"
        f"Please link an account to begin.\n"
        f"────────────────────────"
    )


def accounts_list_text(accounts: list[dict]) -> str:
    text = "<b>K U R U P  A D S</b>\n────────────────────────\n<b>HOSTED ACCOUNTS</b>\n\n"
    for i, acc in enumerate(accounts, 1):
        status = "✅" if acc.get("status") == "active" else "❌"
        text += f"{i}. {status} <code>{acc['phone_masked']}</code>\n"
    text += "\n────────────────────────"
    return text


def delete_confirm_text(phone_masked: str) -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>CONFIRM DELETION</b>\n"
        f"\n"
        f"Are you sure you want to remove\n"
        f"account: <code>{phone_masked}</code>?\n"
        f"\n"
        f"<i>This action is irreversible.</i>\n"
        f"────────────────────────"
    )


def account_deleted_text(phone_masked: str) -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>DELETED</b>\n"
        f"\n"
        f"Account <code>{phone_masked}</code> has\n"
        f"been removed from the system.\n"
        f"────────────────────────"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def groups_text(total: int, active: int, disabled: int) -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>TARGET MANAGEMENT</b>\n"
        f"\n"
        f"  Total Targets: {total}\n"
        f"  Active Pools: {active}\n"
        f"  Excluded: {disabled}\n"
        f"\n"
        f"────────────────────────"
    )


def add_groups_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>IMPORT TARGETS</b>\n"
        f"\n"
        f"Please send the links or usernames\n"
        f"of the target groups/channels.\n"
        f"\n"
        f"Format: One per line.\n"
        f"────────────────────────"
    )


def groups_added_text(added: int, failed: int) -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>IMPORT COMPLETE</b>\n"
        f"\n"
        f"  Successfully Added: {added}\n"
        f"  Failed/Duplicate: {failed}\n"
        f"\n"
        f"────────────────────────"
    )


def no_groups_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>NO TARGETS</b>\n"
        f"\n"
        f"The broadcast list is empty.\n"
        f"Please import target groups.\n"
        f"────────────────────────"
    )


def groups_list_text(groups: list[dict]) -> str:
    text = "<b>K U R U P  A D S</b>\n────────────────────────\n<b>BROADCAST POOL</b>\n\n"
    for i, g in enumerate(groups[:20], 1):
        status = "✅" if g.get("status") == "active" else "❌"
        text += f"{i}. {status} <code>{g.get('identifier')}</code>\n"
    if len(groups) > 20:
        text += f"\n<i>... and {len(groups)-20} more</i>"
    text += "\n────────────────────────"
    return text


# ═══════════════════════════════════════════════════════════════════════════════
#  ADS
# ═══════════════════════════════════════════════════════════════════════════════

def set_ad_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>CONTENT COMPOSER</b>\n"
        f"\n"
        f"Send the message, image, or video\n"
        f"that you want to broadcast.\n"
        f"\n"
        f"<i>HTML formatting is supported.</i>\n"
        f"────────────────────────"
    )


def ad_saved_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>CONTENT SAVED</b>\n"
        f"\n"
        f"Your broadcast creative has been\n"
        f"successfully stored and ready.\n"
        f"────────────────────────"
    )


def set_interval_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>TIMING PARAMETERS</b>\n"
        f"\n"
        f"Specify the delay between each\n"
        f"broadcast cycle in seconds.\n"
        f"\n"
        f"  Min: {MIN_INTERVAL}s\n"
        f"  Default: 1200s (20m)\n"
        f"────────────────────────"
    )


def interval_saved_text(seconds: int) -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>TIMING UPDATED</b>\n"
        f"\n"
        f"System interval set to: {seconds}s\n"
        f"────────────────────────"
    )


def ads_started_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>SYSTEM ACTIVATED</b>\n"
        f"\n"
        f"The broadcast engine is now LIVE.\n"
        f"Live updates in the logs channel.\n"
        f"\n"
        f"  ⚡ Night Mode: Active (12-5 AM)\n"
        f"  🛡 Anti-Flood: Enabled\n"
        f"────────────────────────"
    )


def ads_stopped_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>SYSTEM DEACTIVATED</b>\n"
        f"\n"
        f"The broadcast engine has been\n"
        f"returned to standby mode.\n"
        f"────────────────────────"
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
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>PERFORMANCE REPORT</b>\n"
        f"\n"
        f"  ✅ Successful: {total_sent}\n"
        f"  ❌ Errors/Fails: {failed_count}\n"
        f"  📱 Accounts: {active_accounts}\n"
        f"  📂 Targets: {group_count}\n"
        f"\n"
        f"  Last Run: {last_broadcast}\n"
        f"────────────────────────"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO REPLY
# ═══════════════════════════════════════════════════════════════════════════════

def auto_reply_text(enabled: bool, reply_text: str | None) -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>AUTO-RESPONDER</b>\n"
        f"\n"
        f"  Status: {'🟢 Enabled' if enabled else '🔴 Disabled'}\n"
        f"  Message: {reply_text or 'Not Set'}\n"
        f"\n"
        f"────────────────────────"
    )


def set_auto_reply_prompt_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>RESPONDER CONTENT</b>\n"
        f"\n"
        f"Send the text you want the bot\n"
        f"to send as an automatic reply.\n"
        f"────────────────────────"
    )


def auto_reply_saved_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>RESPONDER UPDATED</b>\n"
        f"\n"
        f"Your auto-reply message has been\n"
        f"successfully configured.\n"
        f"────────────────────────"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GUIDE & DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

def how_to_use_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>OPERATIONS GUIDE</b>\n"
        f"\n"
        f"1. <b>Link Account</b>: Securely connect your Telegram user account.\n"
        f"2. <b>Set Targets</b>: Provide usernames or links of groups.\n"
        f"3. <b>Configure Ad</b>: Upload your marketing creative.\n"
        f"4. <b>Timing</b>: Set the interval between broadcasts.\n"
        f"5. <b>Start</b>: Activate the engine.\n"
        f"\n"
        f"────────────────────────"
    )


def disclaimer_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>LEGAL NOTICE</b>\n"
        f"\n"
        f"This system is for legitimate\n"
        f"marketing purposes only.\n"
        f"\n"
        f"User assumes all responsibility\n"
        f"for content and compliance with\n"
        f"Telegram Terms of Service.\n"
        f"────────────────────────"
    )


def powered_by_text() -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>CREDITS</b>\n"
        f"\n"
        f"  Powered by: ‣ Kurup Ads\n"
        f"  Support: @kurupads\n"
        f"\n"
        f"────────────────────────"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ERRORS
# ═══════════════════════════════════════════════════════════════════════════════

def error_text(message: str) -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>SYSTEM ERROR</b>\n"
        f"\n"
        f"  {message}\n"
        f"────────────────────────"
    )


def max_accounts_text(max_count: int) -> str:
    return (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>LIMIT REACHED</b>\n"
        f"\n"
        f"You have reached the maximum of\n"
        f"{max_count} hosted accounts.\n"
        f"────────────────────────"
    )
