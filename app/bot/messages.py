"""
Message templates — Kurup Ads Premium UI.

Distinctive, minimal design language with professional copy.
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
        f"   <b>‣ Kᴜʀᴜᴘ Aᴅs  Eɴɢɪɴᴇ</b>\n"
        f"        ─── ✦ ───\n"
        f"\n"
        f"   Greetings, <b>{name}</b>\n"
        f"\n"
        f"   ┊ ɪᴅ     <code>{user_id}</code>\n"
        f"   ┊ ᴛᴀɢ    @{username or '—'}\n"
        f"\n"
        f"   ━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"   Your all-in-one broadcast\n"
        f"   automation suite.\n"
        f"\n"
        f"   ┊ Encrypted sessions\n"
        f"   ┊ Intelligent scheduling\n"
        f"   ┊ Multi-account relay\n"
        f"   ┊ Night-safe operations\n"
        f"\n"
        f"   ━━━━━━━━━━━━━━━━━━━━━\n"
        f"   @{SUPPORT_USERNAME}  ·  @{CHANNEL_USERNAME}"
    )


def force_join_text() -> str:
    return (
        f"        ─── 🔒 ───\n"
        f"    <b>Mᴇᴍʙᴇʀsʜɪᴘ Rᴇǫᴜɪʀᴇᴅ</b>\n"
        f"        ─── 🔒 ───\n"
        f"\n"
        f"   To activate your dashboard,\n"
        f"   join the following networks:\n"
        f"\n"
        f"   ┊ @philobots\n"
        f"   ┊ @sellinghub0\n"
        f"\n"
        f"   Tap <b>Verify</b> once completed."
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
    ad_flag = "Configured" if ad_set else "Pending"

    if night_paused:
        state = "🌙 Night Standby"
    elif ads_status == "running":
        state = "● Broadcasting"
    else:
        state = "○ Idle"

    return (
        f"        ─── ⚡ ───\n"
        f"    <b>Cᴏᴍᴍᴀɴᴅ Cᴇɴᴛᴇʀ</b>\n"
        f"        ─── ⚡ ───\n"
        f"\n"
        f"   ┊ ᴀᴄᴄᴏᴜɴᴛs   {account_count} / {max_accounts}\n"
        f"   ┊ ᴛᴀʀɢᴇᴛs    {group_count} groups\n"
        f"   ┊ ᴀᴅ ᴄᴏᴘʏ    {ad_flag}\n"
        f"   ┊ ᴄʏᴄʟᴇ      {interval // 60} min\n"
        f"   ┊ sᴛᴀᴛᴜs     {state}\n"
        f"\n"
        f"   ━━━━━━━━━━━━━━━━━━━━━\n"
        f"   <i>Select an operation below.</i>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def add_account_text() -> str:
    return (
        f"        ─── 📱 ───\n"
        f"    <b>Lɪɴᴋ Nᴇᴡ Aᴄᴄᴏᴜɴᴛ</b>\n"
        f"        ─── 📱 ───\n"
        f"\n"
        f"   Provide your number with\n"
        f"   international prefix:\n"
        f"\n"
        f"   <code>+919876543210</code>\n"
        f"\n"
        f"   🔐 <i>AES-256 encrypted vault</i>"
    )


def otp_prompt_text() -> str:
    return (
        f"        ─── 🔑 ───\n"
        f"    <b>Aᴜᴛʜᴇɴᴛɪᴄᴀᴛɪᴏɴ</b>\n"
        f"        ─── 🔑 ───\n"
        f"\n"
        f"   A verification code was\n"
        f"   dispatched to your Telegram.\n"
        f"\n"
        f"   Enter it below.\n"
        f"\n"
        f"   ⚠ <i>Do not share this code</i>"
    )


def password_2fa_text() -> str:
    return (
        f"        ─── 🔐 ───\n"
        f"    <b>Tᴡᴏ-Fᴀᴄᴛᴏʀ Aᴜᴛʜ</b>\n"
        f"        ─── 🔐 ───\n"
        f"\n"
        f"   This account requires\n"
        f"   a cloud password.\n"
        f"\n"
        f"   Enter it now.\n"
        f"\n"
        f"   🔒 <i>Discarded after use</i>"
    )


def account_added_text(phone_masked: str) -> str:
    return (
        f"        ─── ✓ ───\n"
        f"    <b>Aᴄᴄᴏᴜɴᴛ Aᴄᴛɪᴠᴀᴛᴇᴅ</b>\n"
        f"        ─── ✓ ───\n"
        f"\n"
        f"   ┊ ɴᴜᴍʙᴇʀ   <code>{phone_masked}</code>\n"
        f"   ┊ sᴛᴀᴛᴜs   Online\n"
        f"   ┊ sᴇssɪᴏɴ  Encrypted\n"
        f"   ┊ ᴘʀᴏꜰɪʟᴇ  ‣ Kᴜʀᴜᴘ Aᴅs\n"
        f"\n"
        f"   <i>Account is deployment-ready.</i>"
    )


def no_accounts_text() -> str:
    return (
        f"        ─── 📱 ───\n"
        f"    <b>Nᴏ Aᴄᴄᴏᴜɴᴛs Fᴏᴜɴᴅ</b>\n"
        f"        ─── 📱 ───\n"
        f"\n"
        f"   Link an account to begin\n"
        f"   your first broadcast."
    )


def accounts_list_text(accounts: list[dict]) -> str:
    lines = [
        f"        ─── 📱 ───",
        f"    <b>Lɪɴᴋᴇᴅ Aᴄᴄᴏᴜɴᴛs</b>",
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
        f"    <b>Cᴏɴꜰɪʀᴍ Rᴇᴍᴏᴠᴀʟ</b>\n"
        f"        ─── ⚠ ───\n"
        f"\n"
        f"   Disconnect <code>{phone_masked}</code>?\n"
        f"\n"
        f"   Session data will be purged.\n"
        f"   <i>This is irreversible.</i>"
    )


def account_deleted_text(phone_masked: str) -> str:
    return (
        f"        ─── ✓ ───\n"
        f"    <b>Aᴄᴄᴏᴜɴᴛ Pᴜʀɢᴇᴅ</b>\n"
        f"        ─── ✓ ───\n"
        f"\n"
        f"   <code>{phone_masked}</code>\n"
        f"   Session destroyed securely."
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def groups_text(total: int, active: int, disabled: int) -> str:
    return (
        f"        ─── 📂 ───\n"
        f"    <b>Bʀᴏᴀᴅᴄᴀsᴛ Tᴀʀɢᴇᴛs</b>\n"
        f"        ─── 📂 ───\n"
        f"\n"
        f"   ┊ ᴛᴏᴛᴀʟ       {total}\n"
        f"   ┊ ᴀᴄᴛɪᴠᴇ      {active}\n"
        f"   ┊ ᴅɪsᴀʙʟᴇᴅ    {disabled}\n"
        f"\n"
        f"   <i>Manage your delivery endpoints.</i>"
    )


def add_groups_text() -> str:
    return (
        f"        ─── ➕ ───\n"
        f"    <b>Aᴅᴅ Tᴀʀɢᴇᴛs</b>\n"
        f"        ─── ➕ ───\n"
        f"\n"
        f"   Paste invite or public links,\n"
        f"   <b>one per line</b>.\n"
        f"\n"
        f"   Accepted formats:\n"
        f"   ┊ <code>t.me/channel</code>\n"
        f"   ┊ <code>t.me/+inviteHash</code>\n"
        f"   ┊ <code>t.me/addlist/folder</code>\n"
        f"   ┊ <code>@username</code>\n"
        f"\n"
        f"   <i>Batch import supported.</i>"
    )


def groups_added_text(added: int, failed: int) -> str:
    lines = [
        f"        ─── ✓ ───",
        f"    <b>Tᴀʀɢᴇᴛs Uᴘᴅᴀᴛᴇᴅ</b>",
        f"        ─── ✓ ───",
        f"",
        f"   ┊ Imported   {added}",
    ]
    if failed:
        lines.append(f"   ┊ Rejected   {failed}")
    return "\n".join(lines)


def no_groups_text() -> str:
    return (
        f"        ─── 📂 ───\n"
        f"    <b>Nᴏ Tᴀʀɢᴇᴛs Sᴇᴛ</b>\n"
        f"        ─── 📂 ───\n"
        f"\n"
        f"   Import group links to\n"
        f"   configure delivery endpoints."
    )


def groups_list_text(groups: list[dict]) -> str:
    lines = [
        f"        ─── 📋 ───",
        f"    <b>Tᴀʀɢᴇᴛ Mᴀɴɪꜰᴇsᴛ</b>",
        f"        ─── 📋 ───",
        f"",
    ]
    for i, g in enumerate(groups[:50], 1):
        dot = "●" if g.get("status") == "active" else "✕"
        ident = g.get("identifier", "?")
        sent = g.get("send_count", 0)
        lines.append(f"   {dot}  {i}. <code>{ident}</code>  ·  {sent} sent")
    if len(groups) > 50:
        lines.append(f"\n   <i>+ {len(groups) - 50} more targets</i>")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  ADS
# ═══════════════════════════════════════════════════════════════════════════════

def set_ad_text() -> str:
    return (
        f"        ─── 📝 ───\n"
        f"    <b>Cᴏᴍᴘᴏsᴇ Aᴅ Cᴏᴘʏ</b>\n"
        f"        ─── 📝 ───\n"
        f"\n"
        f"   Forward or compose your\n"
        f"   broadcast creative now.\n"
        f"\n"
        f"   Accepted media:\n"
        f"   ┊ Text\n"
        f"   ┊ Photo + caption\n"
        f"   ┊ Video + caption\n"
        f"\n"
        f"   <i>Rich formatting preserved.</i>"
    )


def ad_saved_text() -> str:
    return (
        f"        ─── ✓ ───\n"
        f"    <b>Cʀᴇᴀᴛɪᴠᴇ Sᴀᴠᴇᴅ</b>\n"
        f"        ─── ✓ ───\n"
        f"\n"
        f"   Your ad copy is queued\n"
        f"   for the next cycle."
    )


def set_interval_text() -> str:
    m = MIN_INTERVAL // 60
    return (
        f"        ─── ⏱ ───\n"
        f"    <b>Cʏᴄʟᴇ Tɪᴍɪɴɢ</b>\n"
        f"        ─── ⏱ ───\n"
        f"\n"
        f"   Set broadcast cycle duration\n"
        f"   in seconds.\n"
        f"\n"
        f"   Minimum: <b>{MIN_INTERVAL}s</b> ({m} min)\n"
        f"\n"
        f"   ┊ <code>{MIN_INTERVAL}</code>   {m} min\n"
        f"   ┊ <code>1800</code>  30 min\n"
        f"   ┊ <code>3600</code>  1 hour\n"
        f"   ┊ <code>7200</code>  2 hours"
    )


def interval_saved_text(seconds: int) -> str:
    return (
        f"        ─── ✓ ───\n"
        f"    <b>Tɪᴍɪɴɢ Cᴏɴꜰɪɢᴜʀᴇᴅ</b>\n"
        f"        ─── ✓ ───\n"
        f"\n"
        f"   Cycle interval: <b>{seconds}s</b>\n"
        f"   ({seconds // 60} minutes per rotation)"
    )


def ads_started_text() -> str:
    return (
        f"        ─── ▶ ───\n"
        f"    <b>Bʀᴏᴀᴅᴄᴀsᴛ Lɪᴠᴇ</b>\n"
        f"        ─── ▶ ───\n"
        f"\n"
        f"   Delivery pipeline activated.\n"
        f"\n"
        f"   ┊ 🌙  Night guard   12–5 AM\n"
        f"   ┊ 🛡  Flood shield  Active\n"
        f"   ┊ ⏱   Smart pacing  300s+\n"
        f"\n"
        f"   <i>Ensure your content complies\n"
        f"   with Telegram guidelines.</i>"
    )


def ads_stopped_text() -> str:
    return (
        f"        ─── ⏸ ───\n"
        f"    <b>Bʀᴏᴀᴅᴄᴀsᴛ Hᴀʟᴛᴇᴅ</b>\n"
        f"        ─── ⏸ ───\n"
        f"\n"
        f"   Delivery pipeline paused.\n"
        f"   No further dispatches until\n"
        f"   you resume operations."
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
        state = "● Broadcasting"
    elif current_status == "night_paused":
        state = "🌙 Night Standby"
    else:
        state = "○ Idle"

    total = total_sent + failed_count
    rate = f"{(total_sent / total * 100):.1f}%" if total else "—"

    return (
        f"        ─── 📊 ───\n"
        f"    <b>Pᴇʀꜰᴏʀᴍᴀɴᴄᴇ Rᴇᴘᴏʀᴛ</b>\n"
        f"        ─── 📊 ───\n"
        f"\n"
        f"   ┊ ᴅᴇʟɪᴠᴇʀᴇᴅ   {total_sent}\n"
        f"   ┊ ꜰᴀɪʟᴇᴅ      {failed_count}\n"
        f"   ┊ sᴜᴄᴄᴇss     {rate}\n"
        f"   ┊ ᴀᴄᴄᴏᴜɴᴛs    {active_accounts}\n"
        f"   ┊ ᴛᴀʀɢᴇᴛs     {group_count}\n"
        f"   ┊ ʟᴀsᴛ ᴄʏᴄʟᴇ  {last_broadcast}\n"
        f"   ┊ sᴛᴀᴛᴜs      {state}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO REPLY
# ═══════════════════════════════════════════════════════════════════════════════

def auto_reply_text(enabled: bool, reply_text: str | None) -> str:
    flag = "● Enabled" if enabled else "○ Disabled"
    current = reply_text if reply_text else "<i>Not configured</i>"
    return (
        f"        ─── 💬 ───\n"
        f"    <b>Aᴜᴛᴏ-Rᴇsᴘᴏɴᴅᴇʀ</b>\n"
        f"        ─── 💬 ───\n"
        f"\n"
        f"   ┊ sᴛᴀᴛᴇ    {flag}\n"
        f"   ┊ ᴍᴇssᴀɢᴇ  {current}"
    )


def set_auto_reply_prompt_text() -> str:
    return (
        f"        ─── ✏ ───\n"
        f"    <b>Cᴏᴍᴘᴏsᴇ Rᴇᴘʟʏ</b>\n"
        f"        ─── ✏ ───\n"
        f"\n"
        f"   Compose the auto-response\n"
        f"   for incoming DMs on your\n"
        f"   linked accounts."
    )


def auto_reply_saved_text() -> str:
    return (
        f"        ─── ✓ ───\n"
        f"    <b>Rᴇsᴘᴏɴᴅᴇʀ Uᴘᴅᴀᴛᴇᴅ</b>\n"
        f"        ─── ✓ ───\n"
        f"\n"
        f"   Auto-response configured."
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GUIDE & DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

def how_to_use_text() -> str:
    return (
        f"        ─── 📖 ───\n"
        f"    <b>Oᴘᴇʀᴀᴛɪᴏɴs Gᴜɪᴅᴇ</b>\n"
        f"        ─── 📖 ───\n"
        f"\n"
        f"   <b>Phase 1 — Link Account</b>\n"
        f"   Provide phone → Verify OTP\n"
        f"   → Profile auto-branded\n"
        f"\n"
        f"   <b>Phase 2 — Import Targets</b>\n"
        f"   Manage Groups → Paste links\n"
        f"   → Batch import confirmed\n"
        f"\n"
        f"   <b>Phase 3 — Compose Creative</b>\n"
        f"   Set Ad → Send text/media\n"
        f"   → Queued for delivery\n"
        f"\n"
        f"   <b>Phase 4 — Configure Timing</b>\n"
        f"   Set Interval → Min {MIN_INTERVAL}s\n"
        f"   → Pacing auto-applied\n"
        f"\n"
        f"   <b>Phase 5 — Go Live</b>\n"
        f"   Start Ads → Pipeline active\n"
        f"\n"
        f"   ━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"   <b>Built-in Safeguards</b>\n"
        f"   ┊ Night standby  12–5 AM\n"
        f"   ┊ Intelligent pacing  300s+\n"
        f"   ┊ Flood protection  Auto\n"
        f"   ┊ Session encryption  Fernet\n"
        f"   ┊ Profile branding  ‣ Kᴜʀᴜᴘ Aᴅs"
    )


def disclaimer_text() -> str:
    return (
        f"        ─── ⚖ ───\n"
        f"    <b>Tᴇʀᴍs ᴏꜰ Usᴇ</b>\n"
        f"        ─── ⚖ ───\n"
        f"\n"
        f"   This platform is engineered\n"
        f"   exclusively for <b>permission-\n"
        f"   based marketing</b>.\n"
        f"\n"
        f"   By proceeding, you acknowledge:\n"
        f"\n"
        f"   ┊ Broadcast only to groups where\n"
        f"     you hold posting rights.\n"
        f"\n"
        f"   ┊ Full compliance with Telegram's\n"
        f"     Terms of Service is mandatory.\n"
        f"\n"
        f"   ┊ You bear sole responsibility\n"
        f"     for distributed content.\n"
        f"\n"
        f"   ┊ Unsolicited messaging and\n"
        f"     scraping are prohibited.\n"
        f"\n"
        f"   ┊ The development team disclaims\n"
        f"     liability for policy violations.\n"
        f"\n"
        f"   <b>Non-compliance may trigger\n"
        f"   platform-level restrictions.</b>"
    )


def powered_by_text() -> str:
    return (
        f"        ─── ⚡ ───\n"
        f"    <b>‣ Kᴜʀᴜᴘ Aᴅs  Nᴇᴛᴡᴏʀᴋ</b>\n"
        f"        ─── ⚡ ───\n"
        f"\n"
        f"   @{BOT_USERNAME}\n"
        f"   <i>Enterprise-grade broadcast\n"
        f"   automation for Telegram.</i>\n"
        f"\n"
        f"   ┊ Support   @{SUPPORT_USERNAME}\n"
        f"   ┊ Updates   @{CHANNEL_USERNAME}\n"
        f"\n"
        f"   <i>Engineered for performance.</i>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ERRORS
# ═══════════════════════════════════════════════════════════════════════════════

def error_text(message: str) -> str:
    return (
        f"        ─── ✕ ───\n"
        f"    <b>Oᴘᴇʀᴀᴛɪᴏɴ Fᴀɪʟᴇᴅ</b>\n"
        f"        ─── ✕ ───\n"
        f"\n"
        f"   {message}"
    )


def max_accounts_text(max_count: int) -> str:
    return (
        f"        ─── ⚠ ───\n"
        f"    <b>Cᴀᴘᴀᴄɪᴛʏ Rᴇᴀᴄʜᴇᴅ</b>\n"
        f"        ─── ⚠ ───\n"
        f"\n"
        f"   Maximum of <b>{max_count}</b> accounts.\n"
        f"   Remove one to link another."
    )
