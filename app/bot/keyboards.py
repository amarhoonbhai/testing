"""
Elite SaaS Keyboard Builders — Group Broadcaster.
Clean, executive inline button layouts.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.config import CHANNEL_USERNAME, SUPPORT_USERNAME, REQUIRED_CHANNELS


def force_join_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for ch in REQUIRED_CHANNELS:
        buttons.append([InlineKeyboardButton(f"Join @{ch}", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton("✅ Verify Membership", callback_data="check_join")])
    return InlineKeyboardMarkup(buttons)


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Executive Dashboard", callback_data="dashboard")],
        [
            InlineKeyboardButton("📖 Operating Guide", callback_data="how_to_use"),
            InlineKeyboardButton("📜 Legal & Terms", callback_data="disclaimer"),
        ],
        [
            InlineKeyboardButton("📢 Official Channel", url=f"https://t.me/{CHANNEL_USERNAME}"),
            InlineKeyboardButton("💬 Enterprise Support", url=f"https://t.me/{SUPPORT_USERNAME}"),
        ]
    ])


def dashboard_keyboard(is_broadcasting: bool = False, has_account: bool = False,
                       is_owner: bool = False) -> InlineKeyboardMarkup:
    # Broadcast toggle
    if is_broadcasting:
        broadcast_btn = InlineKeyboardButton("⏹ Pause Broadcasting Engine", callback_data="stop_broadcast")
    else:
        broadcast_btn = InlineKeyboardButton("▶️ Initialize Broadcasting Engine", callback_data="start_broadcast")

    # Account button
    if has_account:
        account_btn = InlineKeyboardButton("🔗 Connected Account", callback_data="view_account")
    else:
        account_btn = InlineKeyboardButton("🔴 Connect Account", callback_data="connect_account")

    buttons = [
        [broadcast_btn],
        [InlineKeyboardButton("👥 Manage Target Groups", callback_data="manage_groups")],
        [
            account_btn,
            InlineKeyboardButton("⏱ Cycle Interval", callback_data="set_interval"),
        ],
        [
            InlineKeyboardButton("📊 Live User Telemetry", callback_data="live_stats"),
            InlineKeyboardButton("💎 Premium Tier", callback_data="premium_info"),
        ],
        [
            InlineKeyboardButton("🤖 Smart Auto Responder", callback_data="auto_responder"),
            InlineKeyboardButton("❤️ Account Health Monitor", callback_data="health_monitor"),
        ],
    ]

    if is_owner:
        buttons.append([InlineKeyboardButton("🔧 Elite Admin Command Center", callback_data="admin")])

    buttons.append([InlineKeyboardButton("← Back to Main Menu", callback_data="home")])
    return InlineKeyboardMarkup(buttons)


def back_keyboard(callback_data: str = "dashboard") -> InlineKeyboardMarkup:
    # Friendly mapping for label
    label = "Dashboard" if callback_data == "dashboard" else "Previous Menu"
    if callback_data == "home":
        label = "Main Menu"
    elif callback_data == "manage_groups":
        label = "Groups Management"
    elif callback_data == "admin":
        label = "Admin Command Center"
    elif callback_data == "auto_responder":
        label = "Auto Responder"
        
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"← Back to {label}", callback_data=callback_data)]])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("✖ Cancel Operation", callback_data="cancel_conv")]])


# ── Account ──────────────────────────────────────────────────────────────────

def account_info_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔌 Terminate Session", callback_data="disconnect_account")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def no_account_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Connect Telegram Account", callback_data="connect_account")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def confirm_disconnect_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Terminate Session", callback_data="confirm_disconnect")],
        [InlineKeyboardButton("← Back to Account Overview", callback_data="view_account")],
    ])


# ── Groups & Diagnostics ─────────────────────────────────────────────────────

def groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Import Target Groups", callback_data="add_groups")],
        [
            InlineKeyboardButton("🟢 Active Live Groups", callback_data="live_groups"),
            InlineKeyboardButton("⏸ Paused / Skipped Groups", callback_data="paused_groups"),
        ],
        [
            InlineKeyboardButton("🛠️ Group Diagnostics", callback_data="group_diagnostics"),
            InlineKeyboardButton("🧹 Prune Dead Groups", callback_data="prune_dead_groups"),
        ],
        [InlineKeyboardButton("📋 View Configured Roster", callback_data="view_groups")],
        [InlineKeyboardButton("🗑 Purge Entire Roster", callback_data="clear_groups")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def groups_after_add_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 View Configured Roster", callback_data="view_groups")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def groups_list_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Purge Entire Roster", callback_data="clear_groups")],
        [InlineKeyboardButton("← Back to Groups Management", callback_data="manage_groups")],
    ])


def confirm_clear_groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Purge Entire Roster", callback_data="confirm_clear_groups")],
        [InlineKeyboardButton("← Back to Groups Management", callback_data="manage_groups")],
    ])


def paused_groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Reset All Paused Groups", callback_data="reset_paused_groups")],
        [InlineKeyboardButton("← Back to Groups Management", callback_data="manage_groups")],
    ])


# ── Guide / Disclaimer ──────────────────────────────────────────────────────

def guide_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Enterprise Support", url=f"https://t.me/{SUPPORT_USERNAME}")],
        [InlineKeyboardButton("← Back to Main Menu", callback_data="home")],
    ])


def disclaimer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Architecture & Credits", callback_data="powered_by")],
        [InlineKeyboardButton("← Back to Main Menu", callback_data="home")],
    ])


# ── Advanced & Premium ───────────────────────────────────────────────────────

def health_monitor_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Re-evaluate Health Standing", callback_data="health_monitor")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def auto_responder_keyboard(enabled: bool, rules: dict) -> InlineKeyboardMarkup:
    toggle_text = "🔴 Disable Auto Responder" if enabled else "🟢 Enable Auto Responder"
    only_bcast = "🔴 Respond Always" if not rules.get("only_during_broadcast", True) else "🟢 Only During Broadcast"
    excl_contacts = "🔴 Include Contacts" if not rules.get("exclude_contacts", True) else "🟢 Exclude Contacts"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data="toggle_auto_responder")],
        [InlineKeyboardButton("📝 Configure Reply Message", callback_data="set_auto_responder_message")],
        [
            InlineKeyboardButton(only_bcast, callback_data="toggle_rule_broadcast"),
            InlineKeyboardButton(excl_contacts, callback_data="toggle_rule_contacts"),
        ],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def live_stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh Telemetry", callback_data="live_stats")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def premium_info_keyboard(is_premium: bool) -> InlineKeyboardMarkup:
    buttons = []
    if not is_premium:
        buttons.append([InlineKeyboardButton("💬 DM @spinify to Upgrade", url="https://t.me/spinify")])
    buttons.append([InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")])
    return InlineKeyboardMarkup(buttons)


# ── Elite Admin Command Center ───────────────────────────────────────────────

def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Global Fleet Telemetry", callback_data="admin_view_all_users")],
        [InlineKeyboardButton("👤 User Management Portal", callback_data="admin_manage_user")],
        [InlineKeyboardButton("📢 Global Fleet Announcement", callback_data="admin_global_broadcast")],
        [InlineKeyboardButton("🔄 Refresh Command Center", callback_data="admin")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def admin_all_users_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh Fleet Telemetry", callback_data="admin_view_all_users")],
        [InlineKeyboardButton("← Back to Command Center", callback_data="admin")],
    ])


def admin_user_dashboard_keyboard(user_id: int, is_premium: bool, is_broadcasting: bool) -> InlineKeyboardMarkup:
    if is_premium:
        prem_btn = InlineKeyboardButton("❌ Revoke Premium Tier", callback_data=f"revoke_prem_{user_id}")
    else:
        prem_btn = InlineKeyboardButton("✅ Grant Premium Tier", callback_data=f"grant_prem_{user_id}")

    if is_broadcasting:
        bcast_btn = InlineKeyboardButton("⏹ Remote Stop Engine", callback_data=f"remote_stop_{user_id}")
    else:
        bcast_btn = InlineKeyboardButton("▶️ Remote Start Engine", callback_data=f"remote_start_{user_id}")

    return InlineKeyboardMarkup([
        [prem_btn],
        [bcast_btn],
        [
            InlineKeyboardButton("❤️ Remote Health Check", callback_data=f"remote_health_{user_id}"),
            InlineKeyboardButton("📊 User Telemetry", callback_data=f"remote_stats_{user_id}"),
        ],
        [InlineKeyboardButton("🧹 Force Session Wipe", callback_data=f"remote_wipe_{user_id}")],
        [InlineKeyboardButton("← Back to User Portal", callback_data="admin_manage_user")],
        [InlineKeyboardButton("← Back to Command Center", callback_data="admin")],
    ])
