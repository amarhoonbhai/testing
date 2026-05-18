"""
Elite SaaS Message Templates — Group Broadcaster.
Clean, minimal, executive text symbol architecture.
Emojis are strictly reserved for primary status definitions.
"""

from datetime import datetime
from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  EXECUTIVE TEXT SYMBOL DESIGN SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _header(title: str) -> str:
    return (
        f"<b>{title.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

def _footer() -> str:
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"▪ <b>GROUP BROADCASTER</b> ▪"
    )

def _stat(label: str, value) -> str:
    return f"▪ <b>{label}:</b> <code>{value}</code>\n"

def _sub(title: str) -> str:
    return f"<b>{title}</b>\n"

def _end_sub() -> str:
    return f"\n"

def _item(text: str) -> str:
    return f"▸ {text}\n"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WELCOME & NAVIGATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def welcome_text(first_name: str, last_name: str = "", user_id: int = 0, username: str = "") -> str:
    full_name = f"{first_name} {last_name}".strip()
    return (
        f"{_header('Welcome to Group Broadcaster')}"
        f"Hello <b>{full_name}</b>,\n\n"
        f"{_sub('Account Details')}"
        f"{_stat('Telegram User ID', user_id)}"
        f"{_stat('Access Plan', '@' + username if username else 'Global')}"
        f"{_end_sub()}"
        f"{_sub('Bot Features')}"
        f"{_item('Automated Group Broadcasting')}"
        f"{_item('Auto-Forward from Saved Messages')}"
        f"{_item('Preserves Albums & Media Groups')}"
        f"{_item('Smart Flood & Spam Protection')}"
        f"{_end_sub()}"
        f"↳ <i>Select an option below to manage your bot.</i>"
        f"{_footer()}"
    )


def force_join_text() -> str:
    return (
        f"{_header('Security & Access Gate')}"
        f"Please verify your membership in our official\n"
        f"channels to unlock the Group Broadcaster suite.\n\n"
        f"↳ <i>Tap 'Verify Membership' once joined.</i>"
        f"{_footer()}"
    )


def how_to_use_text() -> str:
    return (
        f"{_header('How to Use the Bot')}"
        f"{_sub('Step 1: Connect Account')}"
        f"{_item('Link your Telegram account securely.')}"
        f"{_end_sub()}"
        f"{_sub('Step 2: Add Target Groups')}"
        f"{_item('Add group links, invite links, or @usernames.')}"
        f"{_end_sub()}"
        f"{_sub('Step 3: Prepare Messages')}"
        f"{_item('Send text, photos, videos, or albums directly')}"
        f"{_item('into your Telegram Saved Messages chat.')}"
        f"{_end_sub()}"
        f"{_sub('Step 4: Start Broadcasting')}"
        f"{_item('The bot automatically forwards your messages')}"
        f"{_item('to your groups with safe time delays.')}"
        f"{_end_sub()}"
        f"↳ <i>Built with smart protection to keep your account safe.</i>"
        f"{_footer()}"
    )


def disclaimer_text() -> str:
    return (
        f"{_header('Terms & Disclaimer')}"
        f"This software automates sending messages.\n"
        f"Please follow Telegram's Terms of Service.\n\n"
        f"↳ <i>You are responsible for how you use this bot.</i>"
        f"{_footer()}"
    )


def powered_by_text() -> str:
    return (
        f"{_header('About & Credits')}"
        f"Developed by Kurup Teams\n"
        f"Professional Automation Bot\n"
        f"© 2026 Group Broadcaster"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
) -> str:
    status = "🟢 Active (Broadcasting)" if is_broadcasting else "🟡 Standby (Waiting for Account/Groups)"
    now = datetime.now()
    if is_broadcasting and (now.hour >= 0 and now.hour < 5):
        status = "🌙 Night Mode (Sleeping 12 AM - 5 AM)"

    account_status = f"{phone_masked}" if has_account else "🔴 Not Connected"
    tier = "💎 Premium Plan" if is_premium else "🆓 Free Plan"

    total = total_sent + total_failed
    rate = f"{(total_sent / total * 100):.1f}%" if total > 0 else "N/A"

    footer_note = (
        "↳ <i>🌙 Auto Night Mode active. Sleeping until 5:00 AM.</i>"
        if is_broadcasting and (now.hour >= 0 and now.hour < 5)
        else ("↳ <i>The bot is broadcasting automatically in the background!</i>" if is_broadcasting else "↳ <i>Connect your account and add groups to start broadcasting.</i>")
    )

    return (
        f"{_header('Main Dashboard')}"
        f"{_sub('System Status')}"
        f"{_stat('Bot State', status)}"
        f"{_stat('Connected Account', account_status)}"
        f"{_stat('Account Plan', tier)}"
        f"{_stat('Account Health', health_status)}"
        f"{_end_sub()}"
        f"{_sub('Broadcast Settings')}"
        f"{_stat('Message Source', 'Saved Messages (Auto)')}"
        f"{_stat('Target Groups', f'{group_count}')}"
        f"{_stat('Time Delay', f'{interval // 60} minutes')}"
        f"{_end_sub()}"
        f"{_sub('Total Statistics')}"
        f"{_stat('Messages Sent', f'{total_sent:,}')}"
        f"{_stat('Failed Attempts', f'{total_failed:,}')}"
        f"{_stat('Success Rate', rate)}"
        f"{_end_sub()}"
        f"{footer_note}"
        f"{_footer()}"
    )




# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACCOUNT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def connect_account_text() -> str:
    return (
        f"{_header('Connect Telegram Account')}"
        f"Please enter your phone number with the country code\n"
        f"to link your account securely.\n\n"
        f"▸ Example: <code>+1234567890</code>\n\n"
        f"↳ <i>Your connection is fully encrypted and safe.</i>"
        f"{_footer()}"
    )


def otp_prompt_text() -> str:
    return (
        f"{_header('Enter Login Code')}"
        f"Please enter the 5-digit login code sent to your\n"
        f"Telegram app.\n\n"
        f"▪ <i>Waiting for code...</i>"
        f"{_footer()}"
    )


def password_2fa_text() -> str:
    return (
        f"{_header('Two-Factor Password')}"
        f"Your account has Two-Factor Authentication.\n"
        f"Please enter your cloud password:\n\n"
        f"↳ <i>Your password is used once and never saved.</i>"
        f"{_footer()}"
    )


def account_connected_text(phone: str) -> str:
    return (
        f"{_header('Account Connected')}"
        f"Account <code>{phone}</code> is successfully connected.\n\n"
        f"▪ Connection Status: Active & Secure\n"
        f"↳ <i>Ready for automated broadcasting.</i>"
        f"{_footer()}"
    )


def account_disconnected_text(phone: str) -> str:
    return (
        f"{_header('Account Disconnected')}"
        f"Account <code>{phone}</code> has been securely removed.\n"
        f"All stored data has been deleted."
        f"{_footer()}"
    )


def account_info_text(phone: str, is_premium: bool = False, health: str = "Not Checked") -> str:
    tier = "💎 Premium" if is_premium else "🆓 Free"
    return (
        f"{_header('Account Overview')}"
        f"{_sub('Account Details')}"
        f"{_stat('Phone Number', phone)}"
        f"{_stat('Connection', 'Active & Secure')}"
        f"{_stat('Account Plan', tier)}"
        f"{_stat('Health Score', health)}"
        f"{_end_sub()}"
        f"↳ <i>This account is used to send broadcast messages.</i>"
        f"{_footer()}"
    )


def no_account_text() -> str:
    return (
        f"{_header('No Account Connected')}"
        f"🔴 No Telegram account is currently linked.\n\n"
        f"Please connect your account to enable the\n"
        f"automated broadcasting bot."
        f"{_footer()}"
    )


def confirm_disconnect_text(phone: str) -> str:
    return (
        f"{_header('Confirm Disconnect')}"
        f"Are you sure you want to remove account <code>{phone}</code>?\n\n"
        f"⚠️ <b>Warning:</b> All active broadcasts will be stopped."
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GROUPS & DIAGNOSTICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def groups_text(count: int) -> str:
    return (
        f"{_header('Manage Groups')}"
        f"{_stat('Configured Groups', count)}"
        f"\n"
        f"↳ <i>Manage where your messages are sent.</i>"
        f"{_footer()}"
    )


def add_groups_prompt_text() -> str:
    return (
        f"{_header('Add Target Groups')}"
        f"Send your group links or usernames (one per line).\n\n"
        f"{_sub('Supported Formats')}"
        f"{_item('@username')}"
        f"{_item('https://t.me/username')}"
        f"{_item('https://t.me/+inviteHash')}"
        f"{_item('https://t.me/c/123456789/1')}"
        f"{_end_sub()}"
        f"↳ <i>Paste your group list now...</i>"
        f"{_footer()}"
    )


def groups_added_text(added: int, total: int) -> str:
    return (
        f"{_header('Groups Added')}"
        f"{_sub('Summary')}"
        f"{_stat('New Groups Added', added)}"
        f"{_stat('Total Groups', total)}"
        f"{_end_sub()}"
        f"{_footer()}"
    )


def no_groups_text() -> str:
    return (
        f"{_header('No Groups Configured')}"
        f"🔴 Your broadcast target list is empty.\n\n"
        f"Please add target groups to begin broadcasting."
        f"{_footer()}"
    )


def groups_list_text(groups: list[str]) -> str:
    text = f"{_header('Configured Groups')}"
    for i, g in enumerate(groups[:30], 1):
        display = g if len(g) <= 35 else g[:32] + "..."
        text += f"▪ {i:02d}. <code>{display}</code>\n"
    if len(groups) > 30:
        text += f"▪ ↳ <i>+ {len(groups) - 30} more groups...</i>\n"
    text += f"\n{_stat('Total Groups', len(groups))}"
    text += _footer()
    return text


def groups_cleared_text(count: int) -> str:
    return (
        f"{_header('Groups Cleared')}"
        f"Successfully removed <b>{count}</b> groups from your account."
        f"{_footer()}"
    )


def confirm_clear_groups_text() -> str:
    return (
        f"{_header('Confirm Clear Groups')}"
        f"⚠️ This will delete ALL your configured groups.\n"
        f"Are you sure you want to proceed?"
        f"{_footer()}"
    )


def live_groups_text(groups: list[str]) -> str:
    text = f"{_header('Active Live Groups')}"
    for i, g in enumerate(groups[:30], 1):
        display = g if len(g) <= 35 else g[:32] + "..."
        text += f"▪ {i:02d}. <code>{display}</code>\n"
    if len(groups) > 30:
        text += f"▪ ↳ <i>+ {len(groups) - 30} more live groups...</i>\n"
    if not groups:
        text += "▪ <i>No active live groups found.</i>\n"
    text += f"\n{_stat('Total Live Groups', len(groups))}"
    text += _footer()
    return text


def paused_groups_text(groups: list[str]) -> str:
    text = f"{_header('Paused / Skipped Groups')}"
    for i, g in enumerate(groups[:30], 1):
        display = g if len(g) <= 35 else g[:32] + "..."
        text += f"▪ {i:02d}. <code>{display}</code>\n"
    if len(groups) > 30:
        text += f"▪ ↳ <i>+ {len(groups) - 30} more paused groups...</i>\n"
    if not groups:
        text += "▪ <i>No paused groups found.</i>\n"
    text += f"\n{_stat('Total Paused Groups', len(groups))}"
    text += _footer()
    return text


def group_diagnostics_text(group_reasons: dict, paused_groups: list[str]) -> str:
    text = f"{_header('Group Error Check')}"
    if not paused_groups:
        text += "▪ ✅ <i>All groups are working perfectly.</i>\n"
    else:
        text += "<b>Error Summary</b>\n"
        for i, g in enumerate(paused_groups[:20], 1):
            display = g if len(g) <= 25 else g[:22] + "..."
            safe_key = g.replace(".", "_DOT_").replace("$", "_DOLLAR_")
            reason = group_reasons.get(safe_key, "Consecutive Failures / Unknown")
            text += f"▪ {i:02d}. <code>{display}</code> : <b>{reason}</b>\n"
        if len(paused_groups) > 20:
            text += f"▪ ↳ <i>+ {len(paused_groups) - 20} more failing groups...</i>\n"
        text += f"\n↳ <i>Tap 'Remove Dead Groups' to delete broken links.</i>\n"
    
    text += f"\n{_stat('Failing Groups', len(paused_groups))}"
    text += _footer()
    return text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BROADCAST & TELEMETRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def broadcast_started_text() -> str:
    return (
        f"{_header('Broadcast Started')}"
        f"The bot is now broadcasting automatically.\n\n"
        f"{_sub('Broadcast Settings')}"
        f"{_stat('Message Source', 'Saved Messages (me)')}"
        f"{_stat('Batching', 'Smart Time Gaps')}"
        f"{_stat('Time Delay', 'Random Human Delays')}"
        f"{_stat('Spam Protection', 'Active Protection')}"
        f"{_end_sub()}"
        f"↳ <i>Check your live progress on the main dashboard.</i>"
        f"{_footer()}"
    )


def broadcast_stopped_text() -> str:
    return (
        f"{_header('Broadcast Paused')}"
        f"⏸ The broadcast has been paused.\n"
        f"All sending tasks have been cleanly stopped."
        f"{_footer()}"
    )


def broadcast_progress_text(sent: int, failed: int, skipped: int, total: int, speed: float = 0.0, eta_seconds: int = 0) -> str:
    remaining = total - (sent + failed + skipped)
    rate = f"{(sent / (sent + failed) * 100):.1f}%" if (sent + failed) > 0 else "100%"
    
    eta_str = f"{eta_seconds // 60}m {eta_seconds % 60}s" if eta_seconds > 0 else "Calculating..."
    if remaining <= 0:
        eta_str = "Cycle Complete"

    return (
        f"{_header('Live Broadcast Stats')}"
        f"<b>Sending Progress</b>\n"
        f"▪ ✅ Successfully Sent: <code>{sent}</code>\n"
        f"▪ ❌ Failed Attempts  : <code>{failed}</code>\n"
        f"▪ ⏭ Skipped Groups  : <code>{skipped}</code>\n"
        f"▪ 🎯 Total Groups     : <code>{total}</code>\n"
        f"▪ ⏳ Remaining Groups : <code>{remaining}</code>\n\n"
        f"<b>Speed & Performance</b>\n"
        f"▪ ⚡ Sending Speed    : <code>{speed:.1f} msg/min</code>\n"
        f"▪ 📈 Success Rate     : <code>{rate}</code>\n"
        f"▪ ⏱ Time Remaining   : <code>{eta_str}</code>"
        f"{_footer()}"
    )


def night_mode_progress_text() -> str:
    return (
        f"{_header('🌙 Auto Night Mode')}"
        f"<b>Resting Period Active</b>\n"
        f"▪ Status: Sleeping (12:00 AM to 5:00 AM)\n"
        f"▪ Reason: Quiet hours / Spam protection\n\n"
        f"↳ <i>Broadcasting will automatically resume at 5:00 AM.</i>"
        f"{_footer()}"
    )



def set_interval_prompt_text(min_interval: int) -> str:
    return (
        f"{_header('Set Time Delay')}"
        f"Set the waiting delay between broadcast cycles\n"
        f"in seconds.\n\n"
        f"▸ Minimum Allowed: <code>{min_interval}s</code> ({min_interval // 60} minutes)\n\n"
        f"↳ <i>Send the number of seconds now...</i>"
        f"{_footer()}"
    )


def interval_saved_text(seconds: int) -> str:
    return (
        f"{_header('Time Delay Saved')}"
        f"Broadcast waiting delay updated to:\n"
        f"<b>{seconds // 60} minutes</b> ({seconds} seconds)."
        f"{_footer()}"
    )



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GENERIC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def error_text(msg: str) -> str:
    return (
        f"❌ <b>SYSTEM ERROR</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ {msg}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )


def success_text(msg: str) -> str:
    return (
        f"✅ <b>OPERATION SUCCESSFUL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ {msg}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ADVANCED & PREMIUM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def health_monitor_text(score: int, status: str, details: str) -> str:
    clean_details = details.replace("├ ▪ ", "▪ ").replace("└───────────────────────────────────", "").strip()
    return (
        f"{_header('Account Health Check')}"
        f"{_sub('Health Overview')}"
        f"{_stat('Health Score', f'{score}%')}"
        f"{_stat('Account Status', status)}"
        f"{_end_sub()}"
        f"<b>Health Report</b>\n"
        f"{clean_details}\n\n"
        f"↳ <i>Automatic check of your Telegram account status.</i>"
        f"{_footer()}"
    )


def auto_responder_text(enabled: bool, message: str, rules: dict) -> str:
    status = "🟢 Active (Enabled)" if enabled else "🔴 Inactive (Disabled)"
    preview = message[:100] + "..." if len(message) > 100 else message
    
    only_broadcast = "🟢 Yes" if rules.get("only_during_broadcast", True) else "🔴 No (Always)"
    exclude_contacts = "🟢 Yes" if rules.get("exclude_contacts", True) else "🔴 No (Everyone)"

    return (
        f"{_header('Auto Responder')}"
        f"{_stat('Status', status)}"
        f"\n"
        f"{_sub('Reply Message')}\n"
        f"<code>{preview}</code>\n"
        f"{_end_sub()}"
        f"{_sub('Settings')}"
        f"{_stat('Only While Broadcasting', only_broadcast)}"
        f"{_stat('Ignore Known Contacts', exclude_contacts)}"
        f"{_end_sub()}"
        f"↳ <i>Automatically replies to incoming private messages.</i>"
        f"{_footer()}"
    )


def auto_responder_prompt_text() -> str:
    return (
        f"{_header('Set Reply Message')}"
        f"Send the text message you want the bot to reply with\n"
        f"when people send you private messages.\n\n"
        f"↳ <i>Send your reply message now...</i>"
        f"{_footer()}"
    )


def auto_responder_saved_text() -> str:
    return (
        f"{_header('Reply Message Saved')}"
        f"Auto-responder message successfully updated."
        f"{_footer()}"
    )


def live_stats_text(user: dict, live_count: int, paused_count: int) -> str:
    total_sent = user.get("total_sent", 0)
    total_failed = user.get("total_failed", 0)
    total = total_sent + total_failed
    rate = f"{(total_sent / total * 100):.1f}%" if total > 0 else "N/A"
    health = user.get("health_status", "Not Checked")
    premium = "💎 Premium Plan" if user.get("is_premium") else "🆓 Free Plan"

    return (
        f"{_header('User Live Stats')}"
        f"{_sub('Account Status')}"
        f"{_stat('Account Plan', premium)}"
        f"{_stat('Health Status', health)}"
        f"{_stat('Active Groups', live_count)}"
        f"{_stat('Paused Groups', paused_count)}"
        f"{_end_sub()}"
        f"{_sub('Total Performance')}"
        f"{_stat('Messages Sent', f'{total_sent:,}')}"
        f"{_stat('Failed Attempts', f'{total_failed:,}')}"
        f"{_stat('Success Rate', rate)}"
        f"{_end_sub()}"
        f"↳ <i>Detailed live statistics for your account.</i>"
        f"{_footer()}"
    )


def premium_info_text(is_premium: bool) -> str:
    status = "💎 Active (Premium)" if is_premium else "🆓 Free Plan"
    return (
        f"{_header('Premium Plan')}"
        f"{_sub('Plan Details')}"
        f"{_stat('Status', status)}"
        f"{_stat('Duration', '45 Days')}"
        f"{_stat('Price', '499/- INR')}"
        f"{_end_sub()}"
        f"{_sub('Premium Benefits')}"
        f"{_item('Remove bot branding from your bio')}"
        f"{_item('Remove bot branding from your name')}"
        f"{_item('Instant profile restoration')}"
        f"{_item('Priority message sending')}"
        f"{_end_sub()}"
        f"{'↳ <i>You are a Premium Member! Enjoy complete branding freedom.</i>' if is_premium else '↳ <i>To upgrade to Premium, DM @spinify with your User ID (499/- for 45 days).</i>'}"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ELITE ADMIN COMMAND CENTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def admin_panel_text(stats: dict) -> str:
    sent_str = f"{stats['total_sent']:,}"
    failed_str = f"{stats['total_failed']:,}"
    return (
        f"{_header('Admin Control Panel')}"
        f"{_sub('Global User Stats')}"
        f"{_stat('Total Users', stats['total_users'])}"
        f"{_stat('Active Broadcasting', stats['broadcasting'])}"
        f"{_end_sub()}"
        f"{_sub('Global Performance')}"
        f"{_stat('Total Messages Sent', sent_str)}"
        f"{_stat('Total Failed', failed_str)}"
        f"{_stat('Success Rate', stats['success_rate'])}"
        f"{_end_sub()}"
        f"↳ <i>Select an admin option below.</i>"
        f"{_footer()}"
    )



def admin_manage_user_prompt_text() -> str:
    return (
        f"{_header('Manage User')}"
        f"Enter the Telegram User ID of the user to access\n"
        f"their bot dashboard.\n\n"
        f"↳ <i>Waiting for User ID...</i>"
        f"{_footer()}"
    )


def admin_user_dashboard_text(user: dict, is_broadcasting: bool) -> str:
    user_id = user.get("telegram_user_id")
    username = user.get("username", "None")
    phone = user.get("phone_masked", "🔴 Unlinked")
    is_premium = user.get("is_premium", False)
    status = "💎 Premium Plan" if is_premium else "🆓 Free Plan"
    engine_state = "🟢 Active (Broadcasting)" if is_broadcasting else "⏸ Paused (Idle)"
    health = user.get("health_status", "Not Checked")
    sent = user.get("total_sent", 0)
    failed = user.get("total_failed", 0)
    total = sent + failed
    rate = f"{(sent / total * 100):.1f}%" if total > 0 else "N/A"

    return (
        f"{_header(f'User Dashboard: {user_id}')}"
        f"{_sub('User Details')}"
        f"{_stat('User ID', user_id)}"
        f"{_stat('Username', f'@{username}')}"
        f"{_stat('Phone Number', phone)}"
        f"{_stat('Account Plan', status)}"
        f"{_stat('Health Status', health)}"
        f"{_stat('Bot State', engine_state)}"
        f"{_end_sub()}"
        f"{_sub('User Stats')}"
        f"{_stat('Messages Sent', f'{sent:,}')}"
        f"{_stat('Failed Attempts', f'{failed:,}')}"
        f"{_stat('Success Rate', rate)}"
        f"{_end_sub()}"
        f"↳ <i>Manage this user below:</i>"
        f"{_footer()}"
    )


def admin_all_users_stats_text(users: list[dict]) -> str:
    text = f"{_header('All Users List')}"
    for u in users[:20]:
        uid = u.get("telegram_user_id")
        phone = u.get("phone_masked") or u.get("username") or "Unlinked"
        sent = u.get("total_sent", 0)
        failed = u.get("total_failed", 0)
        health = u.get("health_status", "N/A").split(" ")[0]
        prem = "💎" if u.get("is_premium") else "🆓"
        text += f"▪ <code>{uid}</code> ({phone}) | {prem} | {health} | S:{sent} F:{failed}\n"
    
    if len(users) > 20:
        text += f"▪ ↳ <i>+ {len(users) - 20} more users...</i>\n"
    text += f"\n{_stat('Total Users', len(users))}"
    text += _footer()
    return text


def admin_global_broadcast_prompt_text() -> str:
    return (
        f"{_header('Global Announcement')}"
        f"Send the message (text, photo, or video) you want\n"
        f"to broadcast to all bot users.\n\n"
        f"↳ <i>Waiting for announcement message...</i>"
        f"{_footer()}"
    )


def admin_global_broadcast_success_text(sent: int, failed: int) -> str:
    return (
        f"{_header('Announcement Sent')}"
        f"Your announcement was successfully sent to all users.\n\n"
        f"{_sub('Results')}"
        f"{_stat('Successfully Sent', sent)}"
        f"{_stat('Failed / Blocked', failed)}"
        f"{_end_sub()}"
        f"{_footer()}"
    )


