"""
Message templates — Kurup Ads Bot.

Clean, professional copy with readable text.
Consistent ─── ✦ ─── header style.
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
    name = first_name
    if last_name:
        name += f" {last_name}"

    return (
        f"        ─── ✦ ───\n"
        f"   <b>‣ Kurup Ads  Engine</b>\n"
        f"        ─── ✦ ───\n"
        f"\n"
        f"   Hello, <b>{name}</b> 👋\n"
        f"\n"
        f"   ┊ ID       <code>{user_id}</code>\n"
        f"   ┊ Handle   @{username or '—'}\n"
        f"\n"
        f"   ━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"   Your complete broadcast\n"
        f"   automation platform.\n"
        f"\n"
        f"   ┊ Encrypted sessions\n"
        f"   ┊ Smart scheduling\n"
        f"   ┊ Multi-account support\n"
        f"   ┊ Night-safe mode\n"
        f"\n"
        f"   ━━━━━━━━━━━━━━━━━━━━━\n"
        f"   @{SUPPORT_USERNAME}  ·  @{CHANNEL_USERNAME}"
    )


def force_join_text() -> str:
    return (
        f"        ─── 🔒 ───\n"
        f"    <b>Channel Membership Required</b>\n"
        f"        ─── 🔒 ───\n"
        f"\n"
        f"   You must join all our channels\n"
        f"   to use this bot.\n"
        f"\n"
        f"   ┊ @philobots\n"
        f"   ┊ @sellinghub0\n"
        f"\n"
        f"   Join all channels, then\n"
        f"   tap <b>Verify</b> to continue."
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
    ad_flag = "Ready" if ad_set else "Not set"

    if night_paused:
        state = "🌙 Night Standby"
    elif ads_status == "running":
        state = "● Live"
    else:
        state = "○ Idle"

    return (
        f"        ─── ⚡ ───\n"
        f"    <b>Command Center</b>\n"
        f"        ─── ⚡ ───\n"
        f"\n"
        f"   ┊ Accounts    {account_count} / {max_accounts}\n"
        f"   ┊ Targets     {group_count} groups\n"
        f"   ┊ Ad Copy     {ad_flag}\n"
        f"   ┊ Cycle       {interval // 60} min\n"
        f"   ┊ Status      {state}\n"
        f"\n"
        f"   ━━━━━━━━━━━━━━━━━━━━━\n"
        f"   <i>Select an option below.</i>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def add_account_text() -> str:
    return (
        f"        ─── 📱 ───\n"
        f"    <b>Link New Account</b>\n"
        f"        ─── 📱 ───\n"
        f"\n"
        f"   Enter your phone number\n"
        f"   with country code:\n"
        f"\n"
        f"   <code>+919876543210</code>\n"
        f"\n"
        f"   🔐 <i>Your data is encrypted</i>"
    )


def otp_prompt_text() -> str:
    return (
        f"        ─── 🔑 ───\n"
        f"    <b>Enter Verification Code</b>\n"
        f"        ─── 🔑 ───\n"
        f"\n"
        f"   A login code was sent to\n"
        f"   your Telegram app.\n"
        f"\n"
        f"   Type it below:\n"
        f"\n"
        f"   ⚠ <i>Never share this code</i>"
    )


def password_2fa_text() -> str:
    return (
        f"        ─── 🔐 ───\n"
        f"    <b>Two-Factor Password</b>\n"
        f"        ─── 🔐 ───\n"
        f"\n"
        f"   This account has 2FA.\n"
        f"   Enter your cloud password:\n"
        f"\n"
        f"   🔒 <i>Discarded after use</i>"
    )


def account_added_text(phone_masked: str) -> str:
    return (
        f"        ─── ✓ ───\n"
        f"    <b>Account Activated</b>\n"
        f"        ─── ✓ ───\n"
        f"\n"
        f"   ┊ Number    <code>{phone_masked}</code>\n"
        f"   ┊ Status    Online ✅\n"
        f"   ┊ Session   Encrypted 🔐\n"
        f"   ┊ Profile   ‣ Kurup Ads\n"
        f"\n"
        f"   <i>Ready for broadcasting.</i>"
    )


def no_accounts_text() -> str:
    return (
        f"        ─── 📱 ───\n"
        f"    <b>No Accounts Found</b>\n"
        f"        ─── 📱 ───\n"
        f"\n"
        f"   Link an account to get started."
    )


def accounts_list_text(accounts: list[dict]) -> str:
    lines = [
        f"        ─── 📱 ───",
        f"    <b>Linked Accounts</b>",
        f"        ─── 📱 ───",
        f"",
    ]
    for i, acc in enumerate(accounts, 1):
        if acc.get("status") == "active":
            dot = "●"
        elif acc.get("status") == "error":
            dot = "✕"
        else:
            dot = "○"
        lines.append(f"   {dot}  {i}. <code>{acc['phone_masked']}</code>")
    return "\n".join(lines)


def delete_confirm_text(phone_masked: str) -> str:
    return (
        f"        ─── ⚠ ───\n"
        f"    <b>Confirm Removal</b>\n"
        f"        ─── ⚠ ───\n"
        f"\n"
        f"   Disconnect <code>{phone_masked}</code>?\n"
        f"\n"
        f"   Session data will be erased.\n"
        f"   <i>This cannot be undone.</i>"
    )


def account_deleted_text(phone_masked: str) -> str:
    return (
        f"        ─── ✓ ───\n"
        f"    <b>Account Removed</b>\n"
        f"        ─── ✓ ───\n"
        f"\n"
        f"   <code>{phone_masked}</code>\n"
        f"   Session securely destroyed."
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def groups_text(total: int, active: int, disabled: int) -> str:
    return (
        f"        ─── 📂 ───\n"
        f"    <b>Broadcast Targets</b>\n"
        f"        ─── 📂 ───\n"
        f"\n"
        f"   ┊ Total      {total}\n"
        f"   ┊ Active     {active}\n"
        f"   ┊ Disabled   {disabled}\n"
        f"\n"
        f"   <i>Manage your target groups.</i>"
    )


def add_groups_text() -> str:
    return (
        f"        ─── ➕ ───\n"
        f"    <b>Add Targets</b>\n"
        f"        ─── ➕ ───\n"
        f"\n"
        f"   Paste group or channel links,\n"
        f"   <b>one per line</b>.\n"
        f"\n"
        f"   Supported formats:\n"
        f"   ┊ <code>t.me/channel</code>\n"
        f"   ┊ <code>t.me/+inviteHash</code>\n"
        f"   ┊ <code>t.me/addlist/folder</code>\n"
        f"   ┊ <code>@username</code>\n"
        f"\n"
        f"   <i>You can paste many at once.</i>"
    )


def groups_added_text(added: int, failed: int) -> str:
    lines = [
        f"        ─── ✓ ───",
        f"    <b>Targets Updated</b>",
        f"        ─── ✓ ───",
        f"",
        f"   ┊ Added     {added}",
    ]
    if failed:
        lines.append(f"   ┊ Invalid   {failed}")
    return "\n".join(lines)


def no_groups_text() -> str:
    return (
        f"        ─── 📂 ───\n"
        f"    <b>No Targets Added</b>\n"
        f"        ─── 📂 ───\n"
        f"\n"
        f"   Add group links to start\n"
        f"   broadcasting."
    )


def groups_list_text(groups: list[dict]) -> str:
    lines = [
        f"        ─── 📋 ───",
        f"    <b>Target List</b>",
        f"        ─── 📋 ───",
        f"",
    ]
    for i, g in enumerate(groups[:50], 1):
        dot = "●" if g.get("status") == "active" else "✕"
        ident = g.get("identifier", "?")
        sent = g.get("send_count", 0)
        lines.append(f"   {dot}  {i}. <code>{ident}</code>  ·  {sent} sent")
    if len(groups) > 50:
        lines.append(f"\n   <i>+ {len(groups) - 50} more</i>")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  ADS
# ═══════════════════════════════════════════════════════════════════════════════

def set_ad_text() -> str:
    return (
        f"        ─── 📝 ───\n"
        f"    <b>Set Ad Message</b>\n"
        f"        ─── 📝 ───\n"
        f"\n"
        f"   Send your broadcast content.\n"
        f"\n"
        f"   Accepted formats:\n"
        f"   ┊ Text message\n"
        f"   ┊ Photo with caption\n"
        f"   ┊ Video with caption\n"
        f"\n"
        f"   <i>Formatting is preserved.</i>"
    )


def ad_saved_text() -> str:
    return (
        f"        ─── ✓ ───\n"
        f"    <b>Ad Saved</b>\n"
        f"        ─── ✓ ───\n"
        f"\n"
        f"   Your ad is ready for the\n"
        f"   next broadcast cycle."
    )


def set_interval_text() -> str:
    m = MIN_INTERVAL // 60
    return (
        f"        ─── ⏱ ───\n"
        f"    <b>Set Broadcast Interval</b>\n"
        f"        ─── ⏱ ───\n"
        f"\n"
        f"   Enter cycle time in seconds.\n"
        f"   Minimum: <b>{MIN_INTERVAL}s</b> ({m} min)\n"
        f"\n"
        f"   ┊ <code>{MIN_INTERVAL}</code>   →  {m} min\n"
        f"   ┊ <code>1800</code>  →  30 min\n"
        f"   ┊ <code>3600</code>  →  1 hour\n"
        f"   ┊ <code>7200</code>  →  2 hours"
    )


def interval_saved_text(seconds: int) -> str:
    return (
        f"        ─── ✓ ───\n"
        f"    <b>Interval Updated</b>\n"
        f"        ─── ✓ ───\n"
        f"\n"
        f"   Broadcast every <b>{seconds}s</b>\n"
        f"   ({seconds // 60} minutes per cycle)"
    )


def ads_started_text() -> str:
    return (
        f"        ─── ▶ ───\n"
        f"    <b>Broadcasting Started</b>\n"
        f"        ─── ▶ ───\n"
        f"\n"
        f"   Your ads are now being sent.\n"
        f"\n"
        f"   ┊ 🌙  Night guard   12–5 AM\n"
        f"   ┊ 🛡  Flood shield  Active\n"
        f"   ┊ ⏱   Smart pacing  300s+\n"
        f"\n"
        f"   <i>Make sure your content follows\n"
        f"   Telegram's guidelines.</i>"
    )


def ads_stopped_text() -> str:
    return (
        f"        ─── ⏸ ───\n"
        f"    <b>Broadcasting Stopped</b>\n"
        f"        ─── ⏸ ───\n"
        f"\n"
        f"   All sending has been paused.\n"
        f"   No messages will be sent\n"
        f"   until you resume."
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
        state = "● Live"
    elif current_status == "night_paused":
        state = "🌙 Night Standby"
    else:
        state = "○ Idle"

    total = total_sent + failed_count
    rate = f"{(total_sent / total * 100):.1f}%" if total else "—"

    return (
        f"        ─── 📊 ───\n"
        f"    <b>Performance Report</b>\n"
        f"        ─── 📊 ───\n"
        f"\n"
        f"   ┊ Delivered    {total_sent}\n"
        f"   ┊ Failed       {failed_count}\n"
        f"   ┊ Success      {rate}\n"
        f"   ┊ Accounts     {active_accounts}\n"
        f"   ┊ Targets      {group_count}\n"
        f"   ┊ Last Cycle   {last_broadcast}\n"
        f"   ┊ Status       {state}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO REPLY
# ═══════════════════════════════════════════════════════════════════════════════

def auto_reply_text(enabled: bool, reply_text: str | None) -> str:
    flag = "● Enabled" if enabled else "○ Disabled"
    current = reply_text if reply_text else "<i>Not set</i>"
    return (
        f"        ─── 💬 ───\n"
        f"    <b>Auto Reply Settings</b>\n"
        f"        ─── 💬 ───\n"
        f"\n"
        f"   ┊ Status    {flag}\n"
        f"   ┊ Message   {current}"
    )


def set_auto_reply_prompt_text() -> str:
    return (
        f"        ─── ✏ ───\n"
        f"    <b>Set Reply Message</b>\n"
        f"        ─── ✏ ───\n"
        f"\n"
        f"   Send the message you want\n"
        f"   to auto-reply with when\n"
        f"   someone DMs your account."
    )


def auto_reply_saved_text() -> str:
    return (
        f"        ─── ✓ ───\n"
        f"    <b>Reply Saved</b>\n"
        f"        ─── ✓ ───\n"
        f"\n"
        f"   Auto-reply message updated."
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GUIDE & DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

def how_to_use_text() -> str:
    return (
        f"        ─── 📖 ───\n"
        f"    <b>How To Use</b>\n"
        f"        ─── 📖 ───\n"
        f"\n"
        f"   <b>Step 1 — Link Account</b>\n"
        f"   Enter phone → Verify OTP\n"
        f"   → Profile auto-branded\n"
        f"\n"
        f"   <b>Step 2 — Add Targets</b>\n"
        f"   Manage Groups → Paste links\n"
        f"\n"
        f"   <b>Step 3 — Set Your Ad</b>\n"
        f"   Set Ad → Send text or media\n"
        f"\n"
        f"   <b>Step 4 — Set Interval</b>\n"
        f"   Minimum {MIN_INTERVAL}s ({MIN_INTERVAL // 60} min)\n"
        f"\n"
        f"   <b>Step 5 — Go Live</b>\n"
        f"   Start Ads → Broadcasting begins\n"
        f"\n"
        f"   ━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"   <b>Safety Features</b>\n"
        f"   ┊ Night guard   12–5 AM IST\n"
        f"   ┊ Smart delays  300s+\n"
        f"   ┊ Flood shield  Automatic\n"
        f"   ┊ Encryption    Fernet AES\n"
        f"   ┊ Branding      ‣ Kurup Ads"
    )


def disclaimer_text() -> str:
    return (
        f"        ─── ⚖ ───\n"
        f"    <b>Terms of Use</b>\n"
        f"        ─── ⚖ ───\n"
        f"\n"
        f"   This bot is designed for\n"
        f"   <b>legitimate, permission-based\n"
        f"   marketing</b> only.\n"
        f"\n"
        f"   By using this bot you agree:\n"
        f"\n"
        f"   ┊ Only broadcast to groups\n"
        f"     you own or have rights to.\n"
        f"\n"
        f"   ┊ Follow Telegram's Terms\n"
        f"     of Service at all times.\n"
        f"\n"
        f"   ┊ You are responsible for\n"
        f"     everything you broadcast.\n"
        f"\n"
        f"   ┊ Spamming and scraping\n"
        f"     are strictly forbidden.\n"
        f"\n"
        f"   ┊ Developers are not liable\n"
        f"     for any misuse.\n"
        f"\n"
        f"   <b>Breaking these rules may get\n"
        f"   your Telegram account restricted.</b>"
    )


def powered_by_text() -> str:
    return (
        f"        ─── ⚡ ───\n"
        f"    <b>‣ Kurup Ads  Network</b>\n"
        f"        ─── ⚡ ───\n"
        f"\n"
        f"   @{BOT_USERNAME}\n"
        f"   <i>Professional broadcast\n"
        f"   automation for Telegram.</i>\n"
        f"\n"
        f"   ┊ Support   @{SUPPORT_USERNAME}\n"
        f"   ┊ Updates   @{CHANNEL_USERNAME}\n"
        f"\n"
        f"   <i>Built for performance.</i>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ERRORS
# ═══════════════════════════════════════════════════════════════════════════════

def error_text(message: str) -> str:
    return (
        f"        ─── ✕ ───\n"
        f"    <b>Something Went Wrong</b>\n"
        f"        ─── ✕ ───\n"
        f"\n"
        f"   {message}"
    )


def max_accounts_text(max_count: int) -> str:
    return (
        f"        ─── ⚠ ───\n"
        f"    <b>Account Limit Reached</b>\n"
        f"        ─── ⚠ ───\n"
        f"\n"
        f"   Maximum of <b>{max_count}</b> accounts.\n"
        f"   Remove one to add another."
    )
