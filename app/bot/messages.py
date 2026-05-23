"""
Elite SaaS Message Templates — Group Broadcaster.
Clean, minimal, executive text symbol architecture.
Emojis are strictly reserved for primary status definitions.
"""

from datetime import datetime
import pytz
from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME, TIMEZONE

_tz = pytz.timezone(TIMEZONE)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  EXECUTIVE TEXT SYMBOL DESIGN SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _header(title: str) -> str:
    return (
        f"<b>┌𓊈 ⚜️ {title.upper()} 𓊉</b>\n"
        f"<b>│</b>\n"
    )

def _footer() -> str:
    return (
        f"<b>│</b>\n"
        f"<b>└𓊈 ⚡️ Kᴜʀᴜᴘ Aᴅꜱ Aᴜᴛᴏᴍᴀᴛɪᴏɴ 𓊉</b>"
    )

def _progress_bar(percentage: float, width: int = 10) -> str:
    filled = int(round(percentage * width / 100))
    return "▰" * filled + "▱" * (width - filled)

def _stat(label: str, value) -> str:
    return f"<b>│</b> ◽ <b>{label}:</b> <code>{value}</code>\n"

def _sub(title: str) -> str:
    return f"<b>│ 📂 {title}</b>\n"

def _end_sub() -> str:
    return f"<b>│</b>\n"

def _item(text: str) -> str:
    return f"<b>│</b> ▫ {text}\n"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WELCOME & NAVIGATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def welcome_text(first_name: str, last_name: str = "", user_id: int = 0, username: str = "") -> str:
    full_name = f"{first_name} {last_name}".strip()
    return (
        f"{_header('Welcome')}"
        f"<b>│</b> Hello <b>{full_name}</b>,\n"
        f"<b>│</b>\n"
        f"{_sub('Details')}"
        f"{_stat('User ID', user_id)}"
        f"{_stat('Plan', '@' + username if username else 'Global')}"
        f"{_end_sub()}"
        f"{_sub('Features')}"
        f"{_item('Auto Group Broadcast')}"
        f"{_item('Forward Saved Msg')}"
        f"{_item('Keep Media Albums')}"
        f"{_item('Smart Anti-Spam Shield')}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Select option below:</i>"
        f"{_footer()}"
    )


def force_join_text() -> str:
    return (
        f"{_header('Access Gate')}"
        f"<b>│</b> Please join our channels\n"
        f"<b>│</b> to unlock broadcaster suite.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Tap Verify once joined.</i>"
        f"{_footer()}"
    )


def how_to_use_text() -> str:
    return (
        f"{_header('Operating Guide')}"
        f"{_sub('1. Connect Account')}"
        f"{_item('Link your account securely.')}"
        f"{_end_sub()}"
        f"{_sub('2. Add Targets')}"
        f"{_item('Add group links or @usernames.')}"
        f"{_end_sub()}"
        f"{_sub('3. Post Messages')}"
        f"{_item('Send text or media directly')}"
        f"{_item('into your Saved Messages.')}"
        f"{_end_sub()}"
        f"{_sub('4. Start Broadcaster')}"
        f"{_item('Bot automatically forwards')}"
        f"{_item('to groups with safe delays.')}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Built with smart anti-spam.</i>"
        f"{_footer()}"
    )


def disclaimer_text() -> str:
    return (
        f"{_header('Disclaimer')}"
        f"<b>│</b> This bot automates messages.\n"
        f"<b>│</b> Please follow Telegram Terms.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Use responsibly at own risk.</i>"
        f"{_footer()}"
    )


def powered_by_text() -> str:
    return (
        f"{_header('About & Credits')}"
        f"<b>│</b> Developed by Kurup Teams\n"
        f"<b>│</b> Professional Automation Bot\n"
        f"<b>│</b> © 2026 Group Broadcaster"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _is_in_sleep_cycle(hour: int, enabled: bool, start_h: int, end_h: int) -> bool:
    if not enabled:
        return False
    if start_h <= end_h:
        return start_h <= hour < end_h
    else:
        return hour >= start_h or hour < end_h


def dashboard_text(
    has_account: bool,
    group_count: int,
    total_sent: int,
    total_failed: int,
    is_broadcasting: bool,
    interval: int,
    phone_masked: str = None,
    is_premium: bool = False,
    health_status: str = "Not Checked",
    sleep_enabled: bool = True,
    sleep_start_hour: int = 0,
    sleep_end_hour: int = 5,
) -> str:
    # Format hour with AM/PM
    def format_h(h: int) -> str:
        if h == 0:
            return "12 AM"
        elif h == 12:
            return "12 PM"
        elif h < 12:
            return f"{h} AM"
        else:
            return f"{h-12} PM"

    now = datetime.now(_tz)
    in_sleep = is_broadcasting and _is_in_sleep_cycle(now.hour, sleep_enabled, sleep_start_hour, sleep_end_hour)
    status = "🌙 Sleeping (Night)" if in_sleep else ("🟢 Broadcasting" if is_broadcasting else "🟡 Standby (Idle)")

    account_status = f"{phone_masked}" if has_account else "🔴 Unlinked"
    tier = "💎 Premium" if is_premium else "🆓 Free"

    total = total_sent + total_failed
    rate = f"{(total_sent / total * 100):.1f}%" if total > 0 else "N/A"

    if in_sleep:
        footer_note = f"<b>│</b> ↳ <i>🌙 Sleeping (Night Mode) until {format_h(sleep_end_hour)}.</i>"
    elif is_broadcasting:
        footer_note = "<b>│</b> ↳ <i>Bot is broadcasting in background.</i>"
    else:
        footer_note = "<b>│</b> ↳ <i>Link account & add groups to start.</i>"

    return (
        f"{_header('Dashboard')}"
        f"{_sub('System')}"
        f"{_stat('State', status)}"
        f"{_stat('Account', account_status)}"
        f"{_stat('Plan', tier)}"
        f"{_stat('Health', health_status)}"
        f"{_end_sub()}"
        f"{_sub('Broadcast')}"
        f"{_stat('Source', 'Saved Messages')}"
        f"{_stat('Groups', f'{group_count}')}"
        f"{_stat('Delay', f'{interval // 60}m')}"
        f"{_end_sub()}"
        f"{_sub('Stats')}"
        f"{_stat('Sent', f'{total_sent:,}')}"
        f"{_stat('Failed', f'{total_failed:,}')}"
        f"{_stat('Success', rate)}"
        f"{_end_sub()}"
        f"{footer_note}\n"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACCOUNT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def connect_account_text() -> str:
    return (
        f"{_header('Connect Account')}"
        f"<b>│</b> Enter phone with country code\n"
        f"<b>│</b> to link account securely.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ◽ Example: <code>+1234567890</code>\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Connection is encrypted.</i>"
        f"{_footer()}"
    )


def otp_prompt_text() -> str:
    return (
        f"{_header('Enter Code')}"
        f"<b>│</b> Enter the 5-digit login code\n"
        f"<b>│</b> sent to your Telegram app.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ◽ <i>Waiting for code...</i>"
        f"{_footer()}"
    )


def password_2fa_text() -> str:
    return (
        f"{_header('2FA Password')}"
        f"<b>│</b> Enter your cloud 2FA password\n"
        f"<b>│</b> to complete authentication.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Password is never saved.</i>"
        f"{_footer()}"
    )


def account_connected_text(phone: str) -> str:
    return (
        f"{_header('Connected')}"
        f"<b>│</b> Account <code>{phone}</code> linked.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ◽ Status: Active & Secure\n"
        f"<b>│</b> ↳ <i>Ready for broadcasting.</i>"
        f"{_footer()}"
    )


def account_disconnected_text(phone: str) -> str:
    return (
        f"{_header('Disconnected')}"
        f"<b>│</b> Account <code>{phone}</code> removed.\n"
        f"<b>│</b> All session data deleted."
        f"{_footer()}"
    )


def account_info_text(phone: str, is_premium: bool = False, health: str = "Not Checked") -> str:
    tier = "💎 Premium" if is_premium else "🆓 Free"
    return (
        f"{_header('Account Info')}"
        f"{_sub('Details')}"
        f"{_stat('Phone', phone)}"
        f"{_stat('Status', 'Active & Secure')}"
        f"{_stat('Plan', tier)}"
        f"{_stat('Health', health)}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Used for active broadcasting.</i>"
        f"{_footer()}"
    )


def no_account_text() -> str:
    return (
        f"{_header('No Account')}"
        f"<b>│</b> 🔴 No account is linked.\n"
        f"<b>│</b>\n"
        f"<b>│</b> Link your Telegram account\n"
        f"<b>│</b> to start broadcasting."
        f"{_footer()}"
    )


def confirm_disconnect_text(phone: str) -> str:
    return (
        f"{_header('Disconnect?')}"
        f"<b>│</b> Disconnect <code>{phone}</code>?\n"
        f"<b>│</b>\n"
        f"<b>│</b> ⚠️ Active broadcasts will stop."
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GROUPS & DIAGNOSTICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def groups_text(count: int) -> str:
    return (
        f"{_header('Groups Menu')}"
        f"{_stat('Total Groups', count)}"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Manage target channels/groups.</i>"
        f"{_footer()}"
    )


def add_groups_prompt_text() -> str:
    return (
        f"{_header('Add Groups')}"
        f"<b>│</b> Send group links / @usernames\n"
        f"<b>│</b> (one group per line).\n"
        f"<b>│</b>\n"
        f"{_sub('Formats')}"
        f"{_item('@username')}"
        f"{_item('t.me/username')}"
        f"{_item('t.me/+inviteHash')}"
        f"{_item('t.me/c/12345/1')}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Paste your group list now...</i>"
        f"{_footer()}"
    )


def groups_added_text(added: int, total: int) -> str:
    return (
        f"{_header('Import Status')}"
        f"{_sub('Summary')}"
        f"{_stat('Added Now', added)}"
        f"{_stat('Total Groups', total)}"
        f"{_end_sub()}"
        f"{_footer()}"
    )


def no_groups_text() -> str:
    return (
        f"{_header('Empty Roster')}"
        f"<b>│</b> 🔴 Target list is empty.\n"
        f"<b>│</b>\n"
        f"<b>│</b> Please add target groups."
        f"{_footer()}"
    )


def groups_list_text(groups: list[str]) -> str:
    text = f"{_header('Target Roster')}"
    for i, g in enumerate(groups[:20], 1):
        display = g if len(g) <= 20 else g[:17] + "..."
        text += f"<b>│</b> ◽ {i:02d}. <code>{display}</code>\n"
    if len(groups) > 20:
        text += f"<b>│</b> ↳ <i>+ {len(groups) - 20} more groups...</i>\n"
    text += f"<b>│</b>\n"
    text += f"{_stat('Total Groups', len(groups))}"
    text += _footer()
    return text


def groups_cleared_text(count: int) -> str:
    return (
        f"{_header('Roster Cleared')}"
        f"<b>│</b> Removed <b>{count}</b> groups successfully."
        f"{_footer()}"
    )


def confirm_clear_groups_text() -> str:
    return (
        f"{_header('Purge Roster?')}"
        f"<b>│</b> ⚠️ Delete ALL groups?\n"
        f"<b>│</b> This action is permanent."
        f"{_footer()}"
    )


def live_groups_text(groups: list[str]) -> str:
    text = f"{_header('Active Groups')}"
    for i, g in enumerate(groups[:20], 1):
        display = g if len(g) <= 20 else g[:17] + "..."
        text += f"<b>│</b> ◽ {i:02d}. <code>{display}</code>\n"
    if len(groups) > 20:
        text += f"<b>│</b> ↳ <i>+ {len(groups) - 20} more active...</i>\n"
    if not groups:
        text += "<b>│</b> ◽ <i>No active groups found.</i>\n"
    text += f"<b>│</b>\n"
    text += f"{_stat('Total Active', len(groups))}"
    text += _footer()
    return text


def paused_groups_text(groups: list[str]) -> str:
    text = f"{_header('Paused Groups')}"
    for i, g in enumerate(groups[:20], 1):
        display = g if len(g) <= 20 else g[:17] + "..."
        text += f"<b>│</b> ◽ {i:02d}. <code>{display}</code>\n"
    if len(groups) > 20:
        text += f"<b>│</b> ↳ <i>+ {len(groups) - 20} more paused...</i>\n"
    if not groups:
        text += "<b>│</b> ◽ <i>No paused groups.</i>\n"
    text += f"<b>│</b>\n"
    text += f"{_stat('Total Paused', len(groups))}"
    text += _footer()
    return text


def group_diagnostics_text(group_reasons: dict, paused_groups: list[str]) -> str:
    text = f"{_header('Diagnostics')}"
    if not paused_groups:
        text += "<b>│</b> ◽ ✅ <i>All groups healthy.</i>\n"
    else:
        text += f"{_sub('Failing Groups')}"
        for i, g in enumerate(paused_groups[:15], 1):
            display = g if len(g) <= 15 else g[:12] + "..."
            safe_key = g.replace(".", "_DOT_").replace("$", "_DOLLAR_")
            reason = group_reasons.get(safe_key, "Error")
            short_reason = reason if len(reason) <= 12 else reason[:10] + ".."
            text += f"<b>│</b> ◽ {i:02d}. <code>{display}</code>: {short_reason}\n"
        if len(paused_groups) > 15:
            text += f"<b>│</b> ↳ <i>+ {len(paused_groups) - 15} more errors...</i>\n"
        text += f"<b>│</b>\n"
        text += f"<b>│</b> ↳ <i>Prune dead to delete broken links.</i>\n"
    
    text += f"<b>│</b>\n"
    text += f"{_stat('Failing', len(paused_groups))}"
    text += _footer()
    return text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BROADCAST & TELEMETRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def broadcast_started_text() -> str:
    return (
        f"{_header('Started')}"
        f"<b>│</b> Broadcast started successfully.\n"
        f"<b>│</b>\n"
        f"{_sub('Settings')}"
        f"{_stat('Source', 'Saved Messages')}"
        f"{_stat('Mode', 'Smart Gaps')}"
        f"{_stat('Delay', 'Human Simulation')}"
        f"{_stat('Protection', 'Anti-Spam Shield')}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Monitor progress on dashboard.</i>"
        f"{_footer()}"
    )


def broadcast_stopped_text() -> str:
    return (
        f"{_header('Paused')}"
        f"<b>│</b> ⏸ Broadcast has been paused.\n"
        f"<b>│</b> Active tasks safely suspended."
        f"{_footer()}"
    )


def broadcast_progress_text(sent: int, failed: int, skipped: int, total: int, speed: float = 0.0, eta_seconds: int = 0) -> str:
    total_processed = sent + failed + skipped
    pct = (total_processed / total * 100) if total > 0 else 0.0
    bar = _progress_bar(pct)
    
    remaining = total - total_processed
    rate = f"{(sent / (sent + failed) * 100):.1f}%" if (sent + failed) > 0 else "100%"
    
    eta_str = f"{eta_seconds // 60}m {eta_seconds % 60}s" if eta_seconds > 0 else "Pending"
    if remaining <= 0:
        eta_str = "Complete"

    return (
        f"{_header('Live Progress')}"
        f"<b>│ 📊 Status: [{pct:.1f}%]</b>\n"
        f"<b>│</b> <code>{bar}</code>\n"
        f"<b>│</b>\n"
        f"{_sub('Details')}"
        f"{_stat('Sent', sent)}"
        f"{_stat('Failed', failed)}"
        f"{_stat('Skipped', skipped)}"
        f"{_stat('Total', total)}"
        f"{_stat('Left', remaining)}"
        f"{_end_sub()}"
        f"{_sub('Speed')}"
        f"{_stat('Rate', f'{speed:.1f} m/m')}"
        f"{_stat('Success', rate)}"
        f"{_stat('ETA', eta_str)}"
        f"{_end_sub()}"
        f"{_footer()}"
    )


def night_mode_progress_text() -> str:
    return (
        f"{_header('Night Mode')}"
        f"<b>│ 🌙 Sleep Active</b>\n"
        f"<b>│</b> Time: <code>12:00 AM - 5:00 AM</code>\n"
        f"<b>│</b> Reason: Anti-Spam Rest\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Resumes at 5:00 AM.</i>"
        f"{_footer()}"
    )


def sleep_mode_progress_text(start_h: int, end_h: int) -> str:
    def format_hour(h: int) -> str:
        if h == 0:
            return "12 AM"
        elif h == 12:
            return "12 PM"
        elif h < 12:
            return f"{h} AM"
        else:
            return f"{h-12} PM"

    return (
        f"{_header('Sleep Mode')}"
        f"<b>│ 🌙 Sleep Active</b>\n"
        f"<b>│</b> Time: <code>{format_hour(start_h)} - {format_hour(end_h)}</code>\n"
        f"<b>│</b> Reason: Safe resting cycle\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Resumes at {format_hour(end_h)}.</i>"
        f"{_footer()}"
    )


def set_interval_prompt_text(min_interval: int) -> str:
    min_m = min_interval // 60
    return (
        f"{_header('Set Delay')}"
        f"<b>│</b> Enter cycle delay in seconds.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ◽ Min: <code>{min_interval}s</code> ({min_m}m)\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Send seconds value now...</i>"
        f"{_footer()}"
    )


def interval_saved_text(seconds: int) -> str:
    return (
        f"{_header('Delay Saved')}"
        f"<b>│</b> Delay updated to:\n"
        f"<b>│</b> <b>{seconds // 60}m</b> (<code>{seconds}s</code>)"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GENERIC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def error_text(msg: str) -> str:
    return (
        f"<b>┌𓊈 ❌ ERROR 𓊉</b>\n"
        f"<b>│</b>\n"
        f"<b>│</b> ⚠️ <code>{msg}</code>\n"
        f"<b>│</b>\n"
        f"<b>└𓊈 ⚡️ Kurup Ads Bot 𓊉</b>"
    )


def success_text(msg: str) -> str:
    return (
        f"<b>┌𓊈 ✅ SUCCESS 𓊉</b>\n"
        f"<b>│</b>\n"
        f"<b>│</b> ✨ <code>{msg}</code>\n"
        f"<b>│</b>\n"
        f"<b>└𓊈 ⚡️ Kurup Ads Bot 𓊉</b>"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ADVANCED & PREMIUM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def health_monitor_text(score: int, status: str, details: str) -> str:
    clean_details = details.replace("├ ▪ ", "▪ ").replace("└───────────────────────────────────", "").strip()
    formatted_details = "\n".join([f"<b>│</b> {line}" for line in clean_details.split("\n")])
    return (
        f"{_header('Health Check')}"
        f"{_sub('Overview')}"
        f"{_stat('Score', f'{score}%')}"
        f"{_stat('Status', status)}"
        f"{_end_sub()}"
        f"<b>│ 📋 Report</b>\n"
        f"{formatted_details}\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Automatic diagnostic.</i>"
        f"{_footer()}"
    )


def auto_responder_text(enabled: bool, message: str, rules: dict) -> str:
    status = "🟢 Active" if enabled else "🔴 Disabled"
    preview = message[:40] + "..." if len(message) > 40 else message
    
    only_broadcast = "🟢 Yes" if rules.get("only_during_broadcast", True) else "🔴 No"
    exclude_contacts = "🟢 Yes" if rules.get("exclude_contacts", True) else "🔴 No"

    return (
        f"{_header('Auto Responder')}"
        f"{_stat('Status', status)}"
        f"<b>│</b>\n"
        f"<b>│ 📂 Reply Msg Preview</b>\n"
        f"<b>│</b> <code>{preview}</code>\n"
        f"<b>│</b>\n"
        f"{_sub('Rules')}"
        f"{_stat('Only Broadcast', only_broadcast)}"
        f"{_stat('Exclude Contact', exclude_contacts)}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Replies to private chats.</i>"
        f"{_footer()}"
    )


def auto_responder_prompt_text() -> str:
    return (
        f"{_header('Set Reply Msg')}"
        f"<b>│</b> Send the auto-reply text\n"
        f"<b>│</b> for private messages.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Send reply message now...</i>"
        f"{_footer()}"
    )


def auto_responder_saved_text() -> str:
    return (
        f"{_header('Reply Saved')}"
        f"<b>│</b> Auto-responder saved."
        f"{_footer()}"
    )


def live_stats_text(user: dict, live_count: int, paused_count: int) -> str:
    total_sent = user.get("total_sent", 0)
    total_failed = user.get("total_failed", 0)
    total = total_sent + total_failed
    rate = f"{(total_sent / total * 100):.1f}%" if total > 0 else "N/A"
    health = user.get("health_status", "Not Checked")
    premium = "💎 Premium" if user.get("is_premium") else "🆓 Free"

    return (
        f"{_header('Live Stats')}"
        f"{_sub('Account')}"
        f"{_stat('Plan', premium)}"
        f"{_stat('Health', health)}"
        f"{_stat('Active', live_count)}"
        f"{_stat('Paused', paused_count)}"
        f"{_end_sub()}"
        f"{_sub('Performance')}"
        f"{_stat('Sent', f'{total_sent:,}')}"
        f"{_stat('Failed', f'{total_failed:,}')}"
        f"{_stat('Rate', rate)}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Account performance details.</i>"
        f"{_footer()}"
    )


def premium_info_text(is_premium: bool) -> str:
    status = "💎 Active" if is_premium else "🆓 Free"
    if is_premium:
        footer_text = "<b>│</b> ↳ <i>Complete branding freedom.</i>"
    else:
        footer_text = (
            "<b>│</b> Upgrade: DM @spinify with ID\n"
            "<b>│</b> Price: 499/- for 45 days"
        )
    return (
        f"{_header('Premium')}"
        f"{_sub('Plan Details')}"
        f"{_stat('Status', status)}"
        f"{_stat('Duration', '45 Days')}"
        f"{_stat('Price', '499/- INR')}"
        f"{_end_sub()}"
        f"{_sub('Benefits')}"
        f"{_item('Remove branding from bio')}"
        f"{_item('Remove branding from name')}"
        f"{_item('Instant profile restore')}"
        f"{_item('Priority message sending')}"
        f"{_end_sub()}"
        f"{footer_text}\n"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ELITE ADMIN COMMAND CENTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def admin_panel_text(stats: dict) -> str:
    sent_str = f"{stats['total_sent']:,}"
    failed_str = f"{stats['total_failed']:,}"
    return (
        f"{_header('Admin Panel')}"
        f"{_sub('Global Stats')}"
        f"{_stat('Users', stats['total_users'])}"
        f"{_stat('Active', stats['broadcasting'])}"
        f"{_end_sub()}"
        f"{_sub('Performance')}"
        f"{_stat('Sent', sent_str)}"
        f"{_stat('Failed', failed_str)}"
        f"{_stat('Rate', stats['success_rate'])}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Select admin option below.</i>"
        f"{_footer()}"
    )


def admin_manage_user_prompt_text() -> str:
    return (
        f"{_header('Manage User')}"
        f"<b>│</b> Enter the Telegram User ID\n"
        f"<b>│</b> to open dashboard.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Send User ID now...</i>"
        f"{_footer()}"
    )


def admin_user_dashboard_text(user: dict, is_broadcasting: bool) -> str:
    user_id = user.get("telegram_user_id")
    username = user.get("username")
    user_val = f"@{username}" if username else "None"
    phone = user.get("phone_masked", "🔴 Unlinked")
    is_premium = user.get("is_premium", False)
    status = "💎 Premium" if is_premium else "🆓 Free"
    engine_state = "🟢 Running" if is_broadcasting else "⏸ Idle"
    health = user.get("health_status", "Not Checked")
    sent = user.get("total_sent", 0)
    failed = user.get("total_failed", 0)
    total = sent + failed
    rate = f"{(sent / total * 100):.1f}%" if total > 0 else "N/A"

    return (
        f"{_header(f'User: {user_id}')}"
        f"{_sub('Details')}"
        f"{_stat('ID', user_id)}"
        f"{_stat('User', user_val)}"
        f"{_stat('Phone', phone)}"
        f"{_stat('Plan', status)}"
        f"{_stat('Health', health)}"
        f"{_stat('State', engine_state)}"
        f"{_end_sub()}"
        f"{_sub('Stats')}"
        f"{_stat('Sent', f'{sent:,}')}"
        f"{_stat('Failed', f'{failed:,}')}"
        f"{_stat('Success', rate)}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Manage this user below:</i>"
        f"{_footer()}"
    )


def admin_all_users_stats_text(users: list[dict]) -> str:
    text = f"{_header('All Users List')}"
    for u in users[:20]:
        uid = u.get("telegram_user_id")
        raw_phone = u.get("phone_masked") or u.get("username") or "Unlinked"
        phone = f"@{raw_phone}" if u.get("username") and not u.get("phone_masked") else raw_phone
        if len(phone) > 12:
            phone = phone[:10] + ".."
        sent = u.get("total_sent", 0)
        failed = u.get("total_failed", 0)
        
        health_status = u.get("health_status") or ""
        health_emoji = "⚪"
        for emoji in ["🟢", "🟡", "🔴"]:
            if emoji in health_status:
                health_emoji = emoji
                break
        
        prem = "💎" if u.get("is_premium") else "Free"
        text += f"<b>│</b> ◽ <code>{uid}</code> ({phone})\n"
        text += f"<b>│</b>   ↳ {prem} | {health_emoji} | S:{sent} F:{failed}\n"
    
    if len(users) > 20:
        text += f"<b>│</b> ↳ <i>+ {len(users) - 20} more users...</i>\n"
    text += f"<b>│</b>\n"
    text += f"{_stat('Total Users', len(users))}"
    text += _footer()
    return text


def admin_global_broadcast_prompt_text() -> str:
    return (
        f"{_header('Global Broadcast')}"
        f"<b>│</b> Send content to broadcast\n"
        f"<b>│</b> to all bot users.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Send broadcast now...</i>"
        f"{_footer()}"
    )


def admin_global_broadcast_success_text(sent: int, failed: int) -> str:
    return (
        f"{_header('Broadcast Sent')}"
        f"<b>│</b> Global broadcast completed.\n"
        f"<b>│</b>\n"
        f"{_sub('Results')}"
        f"{_stat('Sent', sent)}"
        f"{_stat('Failed', failed)}"
        f"{_end_sub()}"
        f"{_footer()}"
    )


# ── Advanced Enhancements ───────────────────────────────────────────────────

def quiet_hours_menu_text(enabled: bool, start_h: int, end_h: int) -> str:
    def format_h(h: int) -> str:
        if h == 0:
            return "12:00 AM"
        elif h == 12:
            return "12:00 PM"
        elif h < 12:
            return f"{h}:00 AM"
        else:
            return f"{h-12}:00 PM"
    status = "🟢 Enabled" if enabled else "🔴 Disabled"
    return (
        f"{_header('Quiet Hours')}"
        f"{_sub('Status')}"
        f"{_stat('Sleep Mode', status)}"
        f"{_stat('Start Time', format_h(start_h))}"
        f"{_stat('End Time', format_h(end_h))}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Broadcasting pauses during these hours.</i>"
        f"{_footer()}"
    )


def responder_cooldown_text(seconds: int) -> str:
    if seconds == 0:
        cd_display = "Disabled"
    elif seconds < 3600:
        cd_display = f"{seconds // 60} Minutes"
    else:
        cd_display = f"{seconds // 3600} Hour(s)"
    return (
        f"{_header('Responder Cooldown')}"
        f"<b>│</b> Current rate limit: <b>{cd_display}</b>\n"
        f"<b>│</b>\n"
        f"<b>│</b> ↳ <i>Prevents duplicate replies within this window.</i>"
        f"{_footer()}"
    )


def keyword_rules_text(keywords: dict) -> str:
    text = f"{_header('Keyword Rules')}"
    if not keywords:
        text += "<b>│</b> ◽ <i>No keyword rules defined yet.</i>\n"
    else:
        text += f"{_sub('Current Mappings')}"
        for i, (kw, rep) in enumerate(keywords.items(), 1):
            preview = rep[:25] + "..." if len(rep) > 25 else rep
            text += f"<b>│</b> {i}. <code>{kw}</code> ➜ <i>{preview}</i>\n"
        text += f"{_end_sub()}"
    text += f"<b>│</b>\n"
    text += f"<b>│</b> ↳ <i>Matches incoming message keywords.</i>"
    text += _footer()
    return text


def activity_logs_text(logs: list) -> str:
    text = f"{_header('Activity Logs')}"
    if not logs:
        text += "<b>│</b> ◽ <i>No recent broadcast activities.</i>\n"
    else:
        # Display logs from newest to oldest
        for entry in reversed(logs):
            ts = entry.get("timestamp", "")
            if ts:
                try:
                    # ts is like '2026-05-23T13:28:15.123456Z'
                    time_part = ts.split("T")[1][:5]
                except Exception:
                    time_part = "Time"
            else:
                time_part = "Time"
            
            type_ = entry.get("type", "sent")
            group = entry.get("group", "")
            details = entry.get("details", "")
            
            disp_group = group.replace("https://t.me/", "")
            if len(disp_group) > 15:
                disp_group = disp_group[:12] + ".."
            
            if type_ == "sent":
                emoji = "✅"
            elif type_ == "skipped":
                emoji = "⏭"
            else:
                emoji = "❌"
            
            text += f"<b>│</b> {emoji} <code>[{time_part}]</code> {disp_group}: {details}\n"
    text += f"<b>│</b>\n"
    text += f"<b>│</b> ↳ <i>Showing last 20 actions.</i>"
    text += _footer()
    return text


def custom_api_menu_text(has_custom: bool, api_id: int | None, api_hash: str | None) -> str:
    status = "🟢 Configured (Custom)" if has_custom else "⚪ Default Shared Keys"
    masked_hash = f"{api_hash[:4]}...{api_hash[-4:]}" if api_hash and len(api_hash) > 8 else "None"
    return (
        f"{_header('Custom API')}"
        f"{_sub('Current Configuration')}"
        f"{_stat('Status', status)}"
        f"{_stat('API ID', api_id or 'Default')}"
        f"{_stat('API Hash', masked_hash)}"
        f"{_end_sub()}"
        f"<b>│</b> ↳ <i>Configure your own API ID and API Hash from</i>\n"
        f"<b>│</b>   my.telegram.org to bypass shared rate limits\n"
        f"<b>│</b>   and enhance security.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ℹ️ <i>Device identifiers are automatically generated</i>\n"
        f"<b>│</b>   <i>and rotated to match real phone parameters.</i>"
        f"{_footer()}"
    )


def prompt_custom_api_id_text() -> str:
    return (
        f"{_header('API Config')}"
        f"<b>│</b> Please send your custom <b>API ID</b>.\n"
        f"<b>│</b>\n"
        f"<b>│</b> ℹ️ <i>You can obtain this from:</i>\n"
        f"<b>│</b>   https://my.telegram.org\n"
        f"<b>│</b>\n"
        f"<b>│</b> ⚠️ <i>Must be a valid integer.</i>"
        f"{_footer()}"
    )


def prompt_custom_api_hash_text() -> str:
    return (
        f"{_header('API Config')}"
        f"<b>│</b> 🔐 API ID accepted.\n"
        f"<b>│</b>\n"
        f"<b>│</b> Please send your custom <b>API Hash</b>."
        f"{_footer()}"
    )


def api_credentials_saved_text() -> str:
    return (
        f"{_header('Success')}"
        f"<b>│</b> ✅ Custom API credentials saved.\n"
        f"<b>│</b>\n"
        f"<b>│</b> They will be used next time you link\n"
        f"<b>│</b> or authenticate your account."
        f"{_footer()}"
    )


def api_credentials_cleared_text() -> str:
    return (
        f"{_header('Success')}"
        f"<b>│</b> 🧹 Custom API credentials cleared.\n"
        f"<b>│</b>\n"
        f"<b>│</b> The default shared API credentials\n"
        f"<b>│</b> will be used."
        f"{_footer()}"
    )

