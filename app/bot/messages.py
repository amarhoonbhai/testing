"""
Elite SaaS Message Templates — Group Broadcaster.
Clean, minimal, executive text symbol architecture.
Emojis are strictly reserved for primary status definitions.
"""

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
        f"{_sub('Account Identification')}"
        f"{_stat('Telegram User ID', user_id)}"
        f"{_stat('Access Tier', '@' + username if username else 'Global')}"
        f"{_end_sub()}"
        f"{_sub('System Capabilities')}"
        f"{_item('Autonomous Multi-Group Broadcasting')}"
        f"{_item('Smart Saved Messages Auto-Forwarding')}"
        f"{_item('Telegram Album & Media Group Preservation')}"
        f"{_item('Adaptive Rate Limiting & Backoff Protection')}"
        f"{_end_sub()}"
        f"↳ <i>Select an option below to access your executive dashboard.</i>"
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
        f"{_header('Executive Operating Guide')}"
        f"{_sub('Step 1 : Connect Telegram Account')}"
        f"{_item('Link your account via secure encrypted session.')}"
        f"{_end_sub()}"
        f"{_sub('Step 2 : Add Target Groups')}"
        f"{_item('Import group links, invite links, or @usernames.')}"
        f"{_end_sub()}"
        f"{_sub('Step 3 : Prepare Saved Messages')}"
        f"{_item('Send text, photos, videos, or albums directly')}"
        f"{_item('into your own Telegram Saved Messages chat.')}"
        f"{_end_sub()}"
        f"{_sub('Step 4 : Start Autonomous Broadcast')}"
        f"{_item('The bot automatically fetches and forwards your')}"
        f"{_item('Saved Messages content with smart human delays.')}"
        f"{_end_sub()}"
        f"↳ <i>Built with adaptive rate-limiting for account safety.</i>"
        f"{_footer()}"
    )


def disclaimer_text() -> str:
    return (
        f"{_header('Legal & Compliance Disclaimer')}"
        f"This enterprise software automates message transmission.\n"
        f"Operators must comply with Telegram Terms of Service.\n\n"
        f"↳ <i>The user assumes full operational responsibility.</i>"
        f"{_footer()}"
    )


def powered_by_text() -> str:
    return (
        f"{_header('Architecture & Credits')}"
        f"Engineered by Kurup Teams\n"
        f"Enterprise SaaS Automation Suite\n"
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
    status = "🟢 Active (Autonomous)" if is_broadcasting else "🟡 Standby (Awaiting Account/Groups)"
    account_status = f"{phone_masked}" if has_account else "🔴 Not Connected"
    tier = "💎 Premium Tier" if is_premium else "🆓 Free Plan"

    total = total_sent + total_failed
    rate = f"{(total_sent / total * 100):.1f}%" if total > 0 else "N/A"

    return (
        f"{_header('Executive Dashboard')}"
        f"{_sub('System Status')}"
        f"{_stat('Engine State', status)}"
        f"{_stat('Connected Account', account_status)}"
        f"{_stat('Account Tier', tier)}"
        f"{_stat('Health Standing', health_status)}"
        f"{_end_sub()}"
        f"{_sub('Broadcast Configuration')}"
        f"{_stat('Broadcast Source', 'Saved Messages (Auto)')}"
        f"{_stat('Target Groups', f'{group_count}')}"
        f"{_stat('Cycle Interval', f'{interval // 60} minutes')}"
        f"{_end_sub()}"
        f"{_sub('Lifetime Telemetry')}"
        f"{_stat('Total Messages Sent', f'{total_sent:,}')}"
        f"{_stat('Total Failed Attempts', f'{total_failed:,}')}"
        f"{_stat('Overall Success Rate', rate)}"
        f"{_end_sub()}"
        f"{'↳ <i>Autonomous broadcasting engine is live in the background!</i>' if is_broadcasting else '↳ <i>Connect account and add groups to activate autonomous broadcasting.</i>'}"
        f"{_footer()}"
    )



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACCOUNT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def connect_account_text() -> str:
    return (
        f"{_header('Connect Telegram Account')}"
        f"Please submit your phone number in international\n"
        f"format to establish a secure encrypted session.\n\n"
        f"▸ Example : <code>+1234567890</code>\n\n"
        f"↳ <i>Military-grade session encryption active.</i>"
        f"{_footer()}"
    )


def otp_prompt_text() -> str:
    return (
        f"{_header('Authentication Verification')}"
        f"Please enter the 5-digit Telegram login code\n"
        f"sent to your Telegram app.\n\n"
        f"┊ <i>Awaiting security code...</i>"
        f"{_footer()}"
    )


def password_2fa_text() -> str:
    return (
        f"{_header('Two-Factor Authentication')}"
        f"Your account is protected with 2FA.\n"
        f"Please enter your cloud password:\n\n"
        f"↳ <i>Credentials are processed in-memory only.</i>"
        f"{_footer()}"
    )


def account_connected_text(phone: str) -> str:
    return (
        f"{_header('Session Established')}"
        f"Account <code>{phone}</code> successfully linked.\n\n"
        f"┊ Connection State → Active & Verified\n"
        f"↳ <i>Ready for autonomous broadcasting.</i>"
        f"{_footer()}"
    )


def account_disconnected_text(phone: str) -> str:
    return (
        f"{_header('Session Terminated')}"
        f"Account <code>{phone}</code> has been securely disconnected.\n"
        f"All stored session keys have been wiped."
        f"{_footer()}"
    )


def account_info_text(phone: str, is_premium: bool = False, health: str = "Not Checked") -> str:
    tier = "💎 Premium" if is_premium else "🆓 Free"
    return (
        f"{_header('Account Overview')}"
        f"{_sub('Session Details')}"
        f"{_stat('Phone Number', phone)}"
        f"{_stat('Connection State', 'Active & Encrypted')}"
        f"{_stat('Service Tier', tier)}"
        f"{_stat('Health Score', health)}"
        f"{_end_sub()}"
        f"↳ <i>This account acts as the broadcasting worker.</i>"
        f"{_footer()}"
    )


def no_account_text() -> str:
    return (
        f"{_header('No Account Connected')}"
        f"🔴 No Telegram account is currently linked.\n\n"
        f"Please connect your account to enable the\n"
        f"autonomous broadcasting engine."
        f"{_footer()}"
    )


def confirm_disconnect_text(phone: str) -> str:
    return (
        f"{_header('Confirm Disconnect')}"
        f"Are you sure you want to remove account <code>{phone}</code>?\n\n"
        f"⚠️ <b>Warning:</b> All active broadcasts will be terminated."
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GROUPS & DIAGNOSTICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def groups_text(count: int) -> str:
    return (
        f"{_header('Target Groups Management')}"
        f"{_stat('Total Configured Groups', count)}"
        f"\n"
        f"↳ <i>Manage your broadcast destinations.</i>"
        f"{_footer()}"
    )


def add_groups_prompt_text() -> str:
    return (
        f"{_header('Import Target Groups')}"
        f"Submit your group links or usernames (one per line).\n\n"
        f"{_sub('Supported Formats')}"
        f"{_item('@username')}"
        f"{_item('https://t.me/username')}"
        f"{_item('https://t.me/+inviteHash')}"
        f"{_item('https://t.me/c/123456789/1')}"
        f"{_end_sub()}"
        f"↳ <i>Paste your target list now...</i>"
        f"{_footer()}"
    )


def groups_added_text(added: int, total: int) -> str:
    return (
        f"{_header('Import Summary')}"
        f"{_sub('Ingestion Results')}"
        f"{_stat('Newly Added Groups', added)}"
        f"{_stat('Total Active Groups', total)}"
        f"{_end_sub()}"
        f"{_footer()}"
    )


def no_groups_text() -> str:
    return (
        f"{_header('No Groups Configured')}"
        f"🔴 Your broadcast target list is empty.\n\n"
        f"Please import target groups to begin broadcasting."
        f"{_footer()}"
    )


def groups_list_text(groups: list[str]) -> str:
    text = f"{_header('Configured Group Roster')}"
    for i, g in enumerate(groups[:30], 1):
        display = g if len(g) <= 35 else g[:32] + "..."
        text += f"▪ {i:02d}. <code>{display}</code>\n"
    if len(groups) > 30:
        text += f"▪ ↳ <i>+ {len(groups) - 30} additional groups...</i>\n"
    text += f"\n{_stat('Total Group Count', len(groups))}"
    text += _footer()
    return text


def groups_cleared_text(count: int) -> str:
    return (
        f"{_header('Roster Purged')}"
        f"Successfully removed <b>{count}</b> groups from your account."
        f"{_footer()}"
    )


def confirm_clear_groups_text() -> str:
    return (
        f"{_header('Confirm Roster Purge')}"
        f"⚠️ This action will permanently delete ALL configured groups.\n"
        f"Are you sure you wish to proceed?"
        f"{_footer()}"
    )


def live_groups_text(groups: list[str]) -> str:
    text = f"{_header('Active Live Groups')}"
    for i, g in enumerate(groups[:30], 1):
        display = g if len(g) <= 35 else g[:32] + "..."
        text += f"▪ {i:02d}. <code>{display}</code>\n"
    if len(groups) > 30:
        text += f"▪ ↳ <i>+ {len(groups) - 30} additional live groups...</i>\n"
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
        text += f"▪ ↳ <i>+ {len(groups) - 30} additional paused groups...</i>\n"
    if not groups:
        text += "▪ <i>No paused groups found.</i>\n"
    text += f"\n{_stat('Total Paused Groups', len(groups))}"
    text += _footer()
    return text


def group_diagnostics_text(group_reasons: dict, paused_groups: list[str]) -> str:
    text = f"{_header('Group Failure Diagnostics')}"
    if not paused_groups:
        text += "▪ ✅ <i>All configured groups are fully operational.</i>\n"
    else:
        text += "<b>Failure Root Cause Analysis</b>\n"
        for i, g in enumerate(paused_groups[:20], 1):
            display = g if len(g) <= 25 else g[:22] + "..."
            safe_key = g.replace(".", "_DOT_").replace("$", "_DOLLAR_")
            reason = group_reasons.get(safe_key, "Consecutive Failures / Unknown")
            text += f"▪ {i:02d}. <code>{display}</code> : <b>{reason}</b>\n"
        if len(paused_groups) > 20:
            text += f"▪ ↳ <i>+ {len(paused_groups) - 20} more failing groups...</i>\n"
        text += f"\n↳ <i>Tap 'Prune Dead Groups' to automatically remove invalid targets.</i>\n"
    
    text += f"\n{_stat('Total Failing Groups', len(paused_groups))}"
    text += _footer()
    return text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BROADCAST & TELEMETRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def broadcast_started_text() -> str:
    return (
        f"{_header('Engine Initialized')}"
        f"Autonomous broadcasting engine is now active.\n\n"
        f"{_sub('Runtime Architecture')}"
        f"{_stat('Source Channel', 'Saved Messages (me)')}"
        f"{_stat('Batching Mode', 'Smart Batch Gaps')}"
        f"{_stat('Delay Logic', 'Randomized Human Jitter')}"
        f"{_stat('Flood Protection', 'Adaptive Backoff Active')}"
        f"{_end_sub()}"
        f"↳ <i>Monitor live progress via the executive dashboard.</i>"
        f"{_footer()}"
    )


def broadcast_stopped_text() -> str:
    return (
        f"{_header('Engine Paused')}"
        f"⏸ Autonomous broadcasting engine has been paused.\n"
        f"All active worker threads have been cleanly halted."
        f"{_footer()}"
    )


def broadcast_progress_text(sent: int, failed: int, skipped: int, total: int, speed: float = 0.0, eta_seconds: int = 0) -> str:
    remaining = total - (sent + failed + skipped)
    rate = f"{(sent / (sent + failed) * 100):.1f}%" if (sent + failed) > 0 else "100%"
    
    eta_str = f"{eta_seconds // 60}m {eta_seconds % 60}s" if eta_seconds > 0 else "Calculating..."
    if remaining <= 0:
        eta_str = "Cycle Complete"

    return (
        f"{_header('Live Broadcast Telemetry')}"
        f"<b>Execution Metrics</b>\n"
        f"▪ ✅ Successful Forwards : <code>{sent}</code>\n"
        f"▪ ❌ Failed Attempts     : <code>{failed}</code>\n"
        f"▪ ⏭ Skipped Targets     : <code>{skipped}</code>\n"
        f"▪ 🎯 Total Target Groups : <code>{total}</code>\n"
        f"▪ ⏳ Remaining Targets   : <code>{remaining}</code>\n\n"
        f"<b>Performance & Vitals</b>\n"
        f"▪ ⚡ Transmission Speed  : <code>{speed:.1f} msg/min</code>\n"
        f"▪ 📈 Current Success Rate: <code>{rate}</code>\n"
        f"▪ ⏱ Estimated Completion : <code>{eta_str}</code>"
        f"{_footer()}"
    )



def set_interval_prompt_text(min_interval: int) -> str:
    return (
        f"{_header('Configure Cycle Interval')}"
        f"Specify the resting delay between complete broadcast\n"
        f"cycles in seconds.\n\n"
        f"▸ Minimum Allowed : <code>{min_interval}s</code> ({min_interval // 60} minutes)\n\n"
        f"↳ <i>Awaiting interval value...</i>"
        f"{_footer()}"
    )


def interval_saved_text(seconds: int) -> str:
    return (
        f"{_header('Interval Configured')}"
        f"Broadcast cycle resting delay updated to:\n"
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
        f"{_header('Account Health Diagnostic')}"
        f"{_sub('Vitals Overview')}"
        f"{_stat('Health Score', f'{score}%')}"
        f"{_stat('Account Standing', status)}"
        f"{_end_sub()}"
        f"<b>Diagnostic Report</b>\n"
        f"{clean_details}\n\n"
        f"↳ <i>Real-time automated account standing evaluation.</i>"
        f"{_footer()}"
    )


def auto_responder_text(enabled: bool, message: str, rules: dict) -> str:
    status = "🟢 Active (Enabled)" if enabled else "🔴 Inactive (Disabled)"
    preview = message[:100] + "..." if len(message) > 100 else message
    
    only_broadcast = "🟢 Yes" if rules.get("only_during_broadcast", True) else "🔴 No (Always)"
    exclude_contacts = "🟢 Yes" if rules.get("exclude_contacts", True) else "🔴 No (Everyone)"

    return (
        f"{_header('Smart Auto Responder')}"
        f"{_stat('Operating State', status)}"
        f"\n"
        f"{_sub('Configured Reply Message')}\n"
        f"<code>{preview}</code>\n"
        f"{_end_sub()}"
        f"{_sub('Smart Execution Rules')}"
        f"{_stat('Only During Broadcast', only_broadcast)}"
        f"{_stat('Exclude Known Contacts', exclude_contacts)}"
        f"{_end_sub()}"
        f"↳ <i>Autonomous private message response engine.</i>"
        f"{_footer()}"
    )


def auto_responder_prompt_text() -> str:
    return (
        f"{_header('Configure Reply Message')}"
        f"Submit the text message you wish the bot to automatically\n"
        f"reply with when incoming private messages are received.\n\n"
        f"↳ <i>Awaiting reply message input...</i>"
        f"{_footer()}"
    )


def auto_responder_saved_text() -> str:
    return (
        f"{_header('Configuration Saved')}"
        f"Auto-responder reply message successfully updated."
        f"{_footer()}"
    )


def live_stats_text(user: dict, live_count: int, paused_count: int) -> str:
    total_sent = user.get("total_sent", 0)
    total_failed = user.get("total_failed", 0)
    total = total_sent + total_failed
    rate = f"{(total_sent / total * 100):.1f}%" if total > 0 else "N/A"
    health = user.get("health_status", "Not Checked")
    premium = "💎 Premium Tier" if user.get("is_premium") else "🆓 Free Plan"

    return (
        f"{_header('Real-Time User Telemetry')}"
        f"{_sub('Account Standing')}"
        f"{_stat('Service Tier', premium)}"
        f"{_stat('Health Standing', health)}"
        f"{_stat('Live Targets', live_count)}"
        f"{_stat('Paused Targets', paused_count)}"
        f"{_end_sub()}"
        f"{_sub('Lifetime Performance Metrics')}"
        f"{_stat('Total Messages Sent', f'{total_sent:,}')}"
        f"{_stat('Total Failed Attempts', f'{total_failed:,}')}"
        f"{_stat('Overall Success Rate', rate)}"
        f"{_end_sub()}"
        f"↳ <i>Granular individual account observability.</i>"
        f"{_footer()}"
    )


def premium_info_text(is_premium: bool) -> str:
    status = "💎 Active (Premium Tier)" if is_premium else "🆓 Free Plan"
    return (
        f"{_header('Premium Membership')}"
        f"{_sub('Subscription Details')}"
        f"{_stat('Plan Status', status)}"
        f"{_stat('Plan Duration', '45 Days')}"
        f"{_stat('Pricing', '499/- INR')}"
        f"{_end_sub()}"
        f"{_sub('Premium Executive Benefits')}"
        f"{_item('Complete removal of enforced profile bio')}"
        f"{_item('Complete removal of enforced last name suffix')}"
        f"{_item('Instant background bio/profile restoration')}"
        f"{_item('Priority broadcast engine execution')}"
        f"{_end_sub()}"
        f"{'↳ <i>You are an elite Premium Member! Enjoy complete branding freedom.</i>' if is_premium else '↳ <i>To upgrade to Premium, DM @spinify with your User ID (499/- for 45 days).</i>'}"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ELITE ADMIN COMMAND CENTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def admin_panel_text(stats: dict) -> str:
    sent_str = f"{stats['total_sent']:,}"
    failed_str = f"{stats['total_failed']:,}"
    return (
        f"{_header('Elite Admin Command Center')}"
        f"{_sub('Global Fleet Telemetry')}"
        f"{_stat('Total Registered Users', stats['total_users'])}"
        f"{_stat('Active Broadcasting', stats['broadcasting'])}"
        f"{_end_sub()}"
        f"{_sub('Global Lifetime Performance')}"
        f"{_stat('Total Messages Sent', sent_str)}"
        f"{_stat('Total Failed Attempts', failed_str)}"
        f"{_stat('Global Success Rate', stats['success_rate'])}"
        f"{_end_sub()}"
        f"↳ <i>Select a management capability below.</i>"
        f"{_footer()}"
    )



def admin_manage_user_prompt_text() -> str:
    return (
        f"{_header('User Management Portal')}"
        f"Enter the Telegram User ID of the target user to access\n"
        f"their remote management dashboard.\n\n"
        f"↳ <i>Awaiting User ID input...</i>"
        f"{_footer()}"
    )


def admin_user_dashboard_text(user: dict, is_broadcasting: bool) -> str:
    user_id = user.get("telegram_user_id")
    username = user.get("username", "None")
    phone = user.get("phone_masked", "🔴 Unlinked")
    is_premium = user.get("is_premium", False)
    status = "💎 Premium Tier" if is_premium else "🆓 Free Plan"
    engine_state = "🟢 Active (Broadcasting)" if is_broadcasting else "⏸ Idle (Paused)"
    health = user.get("health_status", "Not Checked")
    sent = user.get("total_sent", 0)
    failed = user.get("total_failed", 0)
    total = sent + failed
    rate = f"{(sent / total * 100):.1f}%" if total > 0 else "N/A"

    return (
        f"{_header(f'Remote User Dashboard : {user_id}')}"
        f"{_sub('User Identity & Vitals')}"
        f"{_stat('Telegram User ID', user_id)}"
        f"{_stat('Username', f'@{username}')}"
        f"{_stat('Connected Account', phone)}"
        f"{_stat('Account Tier', status)}"
        f"{_stat('Health Standing', health)}"
        f"{_stat('Engine State', engine_state)}"
        f"{_end_sub()}"
        f"{_sub('User Telemetry')}"
        f"{_stat('Total Sent', f'{sent:,}')}"
        f"{_stat('Total Failed', f'{failed:,}')}"
        f"{_stat('Success Rate', rate)}"
        f"{_end_sub()}"
        f"↳ <i>Execute remote administrative commands below:</i>"
        f"{_footer()}"
    )


def admin_all_users_stats_text(users: list[dict]) -> str:
    text = f"{_header('Global User Fleet Telemetry')}"
    for u in users[:20]:
        uid = u.get("telegram_user_id")
        phone = u.get("phone_masked") or u.get("username") or "Unlinked"
        sent = u.get("total_sent", 0)
        failed = u.get("total_failed", 0)
        health = u.get("health_status", "N/A").split(" ")[0]
        prem = "💎" if u.get("is_premium") else "🆓"
        text += f"▪ <code>{uid}</code> ({phone}) | {prem} | {health} | S:{sent} F:{failed}\n"
    
    if len(users) > 20:
        text += f"▪ ↳ <i>+ {len(users) - 20} additional users...</i>\n"
    text += f"\n{_stat('Total Fleet Users', len(users))}"
    text += _footer()
    return text


def admin_global_broadcast_prompt_text() -> str:
    return (
        f"{_header('Global Fleet Announcement')}"
        f"Submit the announcement message (text, photo, or video)\n"
        f"you wish to broadcast to all registered bot users.\n\n"
        f"↳ <i>Awaiting announcement message...</i>"
        f"{_footer()}"
    )


def admin_global_broadcast_success_text(sent: int, failed: int) -> str:
    return (
        f"{_header('Global Announcement Complete')}"
        f"Announcement broadcast successfully executed across the fleet.\n\n"
        f"{_sub('Execution Results')}"
        f"{_stat('Successfully Delivered', sent)}"
        f"{_stat('Failed / Bot Blocked', failed)}"
        f"{_end_sub()}"
        f"{_footer()}"
    )

