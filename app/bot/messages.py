"""
Message templates for all bot screens.

Premium glassmorphic UI using unicode aesthetics.
Every screen has a unique visual identity.
"""

from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME, MIN_INTERVAL

# ── Premium UI Glyphs ────────────────────────────────────────────────────────
_H = "══════════════════════════"  # header bar
_S = "──────────────────────────"  # separator


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
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ⌞ <b>@{BOT_USERNAME}</b> ⌝\n"
        f"     <i>Premium Ads Engine</i>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  ✦ Welcome, <b>{name}</b>!\n"
        f"\n"
        f"  ╭─ <b>Your Profile</b>\n"
        f"  │ 🆔  <code>{user_id}</code>\n"
        f"  │ 👤  @{username or '—'}\n"
        f"  ╰{_S}\n"
        f"\n"
        f"  ╭─ <b>Features</b>\n"
        f"  │ ▸ Smart Ad Broadcasting\n"
        f"  │ ▸ Night Mode 🌙 (12–5 AM)\n"
        f"  │ ▸ Multi-Account Engine\n"
        f"  │ ▸ Anti-Freeze Shield 🛡️\n"
        f"  ╰{_S}\n"
        f"\n"
        f"  💬 @{SUPPORT_USERNAME}  •  📢 @{CHANNEL_USERNAME}"
    )


def force_join_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     🔒 <b>VERIFICATION</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Join these channels to proceed:\n"
        f"\n"
        f"  ▸ @philobots\n"
        f"  ▸ @sellinghub0\n"
        f"\n"
        f"  Tap <b>Verify</b> when done ✓"
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
    ad_icon = "✅" if ad_set else "⨯"

    if night_paused:
        status = "🌙 SLEEPING"
    elif ads_status == "running":
        status = "🟢 LIVE"
    else:
        status = "⏸ PAUSED"

    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ⚡ <b>COMMAND CENTER</b>\n"
        f"     @{BOT_USERNAME}\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  ╭─ <b>Live Stats</b>\n"
        f"  │ 📱  Accounts   <b>{account_count}/{max_accounts}</b>\n"
        f"  │ 📂  Groups     <b>{group_count}</b>\n"
        f"  │ 📝  Ad         <b>{ad_icon}</b>\n"
        f"  │ ⏱  Interval   <b>{interval // 60}m</b>\n"
        f"  │ 📡  Status     <b>{status}</b>\n"
        f"  ╰{_S}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def add_account_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     📱 <b>HOST ACCOUNT</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Enter phone with country code:\n"
        f"\n"
        f"  <code>+1234567890</code>\n"
        f"\n"
        f"  🔐 <i>End-to-end encrypted</i>"
    )


def otp_prompt_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     🔑 <b>ENTER OTP</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Code sent to your Telegram.\n"
        f"  Enter it below:\n"
        f"\n"
        f"  ⚠️ <i>Never share this code</i>"
    )


def password_2fa_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     🔐 <b>2FA PASSWORD</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Account has 2FA enabled.\n"
        f"  Enter your cloud password:\n"
        f"\n"
        f"  🔒 <i>Password is never stored</i>"
    )


def account_added_text(phone_masked: str) -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ✅ <b>ACCOUNT LIVE</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  ╭─ Details\n"
        f"  │ 📱  <code>{phone_masked}</code>\n"
        f"  │ 📡  Active\n"
        f"  │ 🔐  Encrypted\n"
        f"  │ 🏷  ‣ Kᴜʀᴜᴘ Aᴅs branded\n"
        f"  ╰{_S}\n"
        f"\n"
        f"  <i>Ready for broadcasting</i>"
    )


def no_accounts_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     📱 <b>NO ACCOUNTS</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Add an account to begin!"
    )


def accounts_list_text(accounts: list[dict]) -> str:
    lines = [
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈",
        f"     📱 <b>MY ACCOUNTS</b>",
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈",
        f"",
    ]
    for i, acc in enumerate(accounts, 1):
        if acc.get("status") == "active":
            s = "🟢"
        elif acc.get("status") == "error":
            s = "🔴"
        else:
            s = "🟡"
        lines.append(f"  {s}  {i}. <code>{acc['phone_masked']}</code>")
    return "\n".join(lines)


def delete_confirm_text(phone_masked: str) -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ⚠️ <b>CONFIRM DELETE</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Remove <code>{phone_masked}</code> ?\n"
        f"\n"
        f"  <i>This cannot be undone.</i>"
    )


def account_deleted_text(phone_masked: str) -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     🗑 <b>ACCOUNT REMOVED</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  <code>{phone_masked}</code> deleted.\n"
        f"  Session securely destroyed."
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def groups_text(total: int, active: int, disabled: int) -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     📂 <b>GROUPS</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  ╭─ Overview\n"
        f"  │ 📊  Total    <b>{total}</b>\n"
        f"  │ 🟢  Active   <b>{active}</b>\n"
        f"  │ 🔴  Disabled <b>{disabled}</b>\n"
        f"  ╰{_S}"
    )


def add_groups_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ➕ <b>ADD GROUPS</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Send links — <b>one per line</b>:\n"
        f"\n"
        f"  ▸ <code>https://t.me/group</code>\n"
        f"  ▸ <code>https://t.me/+invite</code>\n"
        f"  ▸ <code>https://t.me/addlist/folder</code>\n"
        f"  ▸ <code>@username</code>\n"
        f"\n"
        f"  💡 <i>Paste multiple at once</i>"
    )


def groups_added_text(added: int, failed: int) -> str:
    lines = [
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈",
        f"     ✅ <b>GROUPS UPDATED</b>",
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈",
        f"",
        f"  ▸ Added: <b>{added}</b>",
    ]
    if failed:
        lines.append(f"  ▸ Invalid: <b>{failed}</b>")
    return "\n".join(lines)


def no_groups_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     📂 <b>NO GROUPS</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Add groups to start!"
    )


def groups_list_text(groups: list[dict]) -> str:
    lines = [
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈",
        f"     📋 <b>GROUP LIST</b>",
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈",
        f"",
    ]
    for i, g in enumerate(groups[:50], 1):
        s = "🟢" if g.get("status") == "active" else "🔴"
        ident = g.get("identifier", "?")
        sent = g.get("send_count", 0)
        lines.append(f"  {s}  {i}. <code>{ident}</code>  ×{sent}")
    if len(groups) > 50:
        lines.append(f"\n  <i>+ {len(groups) - 50} more</i>")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  ADS
# ═══════════════════════════════════════════════════════════════════════════════

def set_ad_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     📝 <b>SET AD</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Send your ad content:\n"
        f"\n"
        f"  ▸ Text message\n"
        f"  ▸ Photo + caption\n"
        f"  ▸ Video + caption\n"
        f"\n"
        f"  💡 <i>Include links for best CTR</i>"
    )


def ad_saved_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ✅ <b>AD SAVED</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Ready for next broadcast cycle."
    )


def set_interval_text() -> str:
    m = MIN_INTERVAL // 60
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ⏱ <b>SET INTERVAL</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Enter delay in seconds.\n"
        f"  Min: <b>{MIN_INTERVAL}s</b> ({m} min)\n"
        f"\n"
        f"  ╭─ Presets\n"
        f"  │ <code>{MIN_INTERVAL}</code>  →  {m} min\n"
        f"  │ <code>1800</code>  →  30 min\n"
        f"  │ <code>3600</code>  →  1 hour\n"
        f"  │ <code>7200</code>  →  2 hours\n"
        f"  ╰{_S}"
    )


def interval_saved_text(seconds: int) -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ✅ <b>INTERVAL SET</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  ⏱ <b>{seconds}s</b>  ({seconds // 60} min)"
    )


def ads_started_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ▶️ <b>ADS LIVE</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Broadcasting is <b>active</b>.\n"
        f"\n"
        f"  ╭─ Shields\n"
        f"  │ 🌙  Night pause  12–5 AM\n"
        f"  │ 🛡  Anti-freeze  ON\n"
        f"  │ ⏱  Smart delays  ON\n"
        f"  ╰{_S}\n"
        f"\n"
        f"  ⚠️ <i>Respect Telegram ToS</i>"
    )


def ads_stopped_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ⏸ <b>ADS PAUSED</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Broadcasting stopped.\n"
        f"  No messages until resumed."
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
        s = "🟢 LIVE"
    elif current_status == "night_paused":
        s = "🌙 SLEEPING"
    else:
        s = "⏸ PAUSED"

    total = total_sent + failed_count
    rate = f"{(total_sent / total * 100):.0f}%" if total else "—"

    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     📊 <b>ANALYTICS</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  ╭─ Performance\n"
        f"  │ 📤  Sent       <b>{total_sent}</b>\n"
        f"  │ ❌  Failed     <b>{failed_count}</b>\n"
        f"  │ 📈  Rate       <b>{rate}</b>\n"
        f"  │ 📱  Accounts   <b>{active_accounts}</b>\n"
        f"  │ 📂  Groups     <b>{group_count}</b>\n"
        f"  │ 🕐  Last       <b>{last_broadcast}</b>\n"
        f"  │ 📡  Status     <b>{s}</b>\n"
        f"  ╰{_S}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO REPLY
# ═══════════════════════════════════════════════════════════════════════════════

def auto_reply_text(enabled: bool, reply_text: str | None) -> str:
    status = "🟢 ON" if enabled else "🔴 OFF"
    current = reply_text if reply_text else "<i>Not set</i>"
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     💬 <b>AUTO REPLY</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  ╭─ Config\n"
        f"  │ Status: <b>{status}</b>\n"
        f"  │ Text: {current}\n"
        f"  ╰{_S}"
    )


def set_auto_reply_prompt_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ✏️ <b>SET REPLY TEXT</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Send the auto-reply message.\n"
        f"  <i>Sent when someone DMs\n"
        f"  your hosted account.</i>"
    )


def auto_reply_saved_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ✅ <b>REPLY SAVED</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Auto-reply updated."
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GUIDE & DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

def how_to_use_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     📖 <b>USER GUIDE</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  <b>① Add Account</b>\n"
        f"     Dashboard → Add → Phone → OTP\n"
        f"\n"
        f"  <b>② Add Groups</b>\n"
        f"     Dashboard → Groups → Paste links\n"
        f"\n"
        f"  <b>③ Set Ad Message</b>\n"
        f"     Dashboard → Set Ad → Send content\n"
        f"\n"
        f"  <b>④ Set Interval</b>\n"
        f"     Min {MIN_INTERVAL}s ({MIN_INTERVAL // 60} min)\n"
        f"\n"
        f"  <b>⑤ Start Broadcasting</b>\n"
        f"     Dashboard → Start Ads ▶️\n"
        f"\n"
        f"  ╭─ 🛡 <b>Safety</b>\n"
        f"  │ ▸ Night mode 12–5 AM IST\n"
        f"  │ ▸ 300s smart delays\n"
        f"  │ ▸ FloodWait protection\n"
        f"  │ ▸ Encrypted sessions\n"
        f"  │ ▸ ‣ Kᴜʀᴜᴘ Aᴅs branding\n"
        f"  ╰{_S}"
    )


def disclaimer_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ⚖️ <b>DISCLAIMER</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  This bot is for <b>legitimate\n"
        f"  opt-in marketing</b> only.\n"
        f"\n"
        f"  By using this bot you agree:\n"
        f"\n"
        f"  ① Only broadcast to groups\n"
        f"     you own or have permission.\n"
        f"\n"
        f"  ② Comply with Telegram ToS.\n"
        f"\n"
        f"  ③ You are responsible for\n"
        f"     all content you broadcast.\n"
        f"\n"
        f"  ④ Spamming & scraping are\n"
        f"     strictly prohibited.\n"
        f"\n"
        f"  ⑤ Developers hold no liability\n"
        f"     for misuse of this tool.\n"
        f"\n"
        f"  ⚠️ <b>Violations may cause\n"
        f"  Telegram account restrictions.</b>"
    )


def powered_by_text() -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ⚡ <b>POWERED BY</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  @{BOT_USERNAME}\n"
        f"  <i>Premium Telegram Automation</i>\n"
        f"\n"
        f"  💬  @{SUPPORT_USERNAME}\n"
        f"  📢  @{CHANNEL_USERNAME}\n"
        f"\n"
        f"  <i>Built with ❤️ by ‣ Kᴜʀᴜᴘ Aᴅs</i>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ERRORS
# ═══════════════════════════════════════════════════════════════════════════════

def error_text(message: str) -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ❌ <b>ERROR</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  {message}"
    )


def max_accounts_text(max_count: int) -> str:
    return (
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"     ⚠️ <b>LIMIT REACHED</b>\n"
        f"  ◈━━━━━━━━━━━━━━━━━━━━━━━◈\n"
        f"\n"
        f"  Max <b>{max_count}</b> accounts.\n"
        f"  Delete one to add new."
    )
