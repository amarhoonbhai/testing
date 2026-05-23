"""
Elite SaaS Keyboard Builders — Group Broadcaster.
Clean, executive inline button layouts optimized for mobile responsiveness.
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
            InlineKeyboardButton("📖 Guide", callback_data="how_to_use"),
            InlineKeyboardButton("📜 Terms", callback_data="disclaimer"),
        ],
        [
            InlineKeyboardButton("📢 Channel", url=f"https://t.me/{CHANNEL_USERNAME}"),
            InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_USERNAME}"),
        ]
    ])


def dashboard_keyboard(is_broadcasting: bool = False, has_account: bool = False,
                       is_owner: bool = False) -> InlineKeyboardMarkup:
    # Account button
    if has_account:
        account_btn = InlineKeyboardButton("🔗 My Account", callback_data="view_account")
    else:
        account_btn = InlineKeyboardButton("🔴 Connect", callback_data="connect_account")

    buttons = [
        [InlineKeyboardButton("👥 Manage Target Groups", callback_data="manage_groups")],
        [
            account_btn,
            InlineKeyboardButton("⏱ Set Delay", callback_data="set_interval"),
        ],
        [
            InlineKeyboardButton("📊 Live Stats", callback_data="live_stats"),
            InlineKeyboardButton("💎 Premium", callback_data="premium_info"),
        ],
        [
            InlineKeyboardButton("🤖 Auto Reply", callback_data="auto_responder"),
            InlineKeyboardButton("🌙 Quiet Hours", callback_data="quiet_hours_menu"),
        ],
        [
            InlineKeyboardButton("❤️ Health Check", callback_data="health_monitor"),
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
        label = "Groups"
    elif callback_data == "admin":
        label = "Admin Panel"
    elif callback_data == "auto_responder":
        label = "Auto Responder"
    elif callback_data == "quiet_hours_menu":
        label = "Quiet Hours"
    elif callback_data == "live_stats":
        label = "Live Stats"
    elif callback_data == "view_account":
        label = "Account Overview"
        
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"← Back to {label}", callback_data=callback_data)]])



def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("✖ Cancel Operation", callback_data="cancel_conv")]])


# ── Account ──────────────────────────────────────────────────────────────────

def account_info_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔌 Terminate Session", callback_data="disconnect_account")],
        [InlineKeyboardButton("⚙️ Custom API Settings", callback_data="setup_custom_api")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def no_account_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Connect Telegram Account", callback_data="connect_account")],
        [InlineKeyboardButton("⚙️ Custom API Settings", callback_data="setup_custom_api")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def custom_api_keyboard(has_custom_keys: bool) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("📝 Configure Custom Keys", callback_data="change_custom_api")]
    ]
    if has_custom_keys:
        buttons.append([InlineKeyboardButton("🧹 Clear Custom Keys", callback_data="clear_custom_api")])
    buttons.append([InlineKeyboardButton("← Back to Account Overview", callback_data="view_account")])
    return InlineKeyboardMarkup(buttons)



def confirm_disconnect_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Terminate Session", callback_data="confirm_disconnect")],
        [InlineKeyboardButton("← Back to Account Overview", callback_data="view_account")],
    ])


# ── Groups & Diagnostics ─────────────────────────────────────────────────────

def groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Import Groups", callback_data="add_groups")],
        [
            InlineKeyboardButton("🟢 Active", callback_data="live_groups"),
            InlineKeyboardButton("⏸ Paused", callback_data="paused_groups"),
        ],
        [
            InlineKeyboardButton("🛠️ Diagnostics", callback_data="group_diagnostics"),
            InlineKeyboardButton("🧹 Prune Dead", callback_data="prune_dead_groups"),
        ],
        [InlineKeyboardButton("📋 View Roster", callback_data="view_groups")],
        [InlineKeyboardButton("🗑 Purge Roster", callback_data="clear_groups")],
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
        [InlineKeyboardButton("← Back to Groups", callback_data="manage_groups")],
    ])


def confirm_clear_groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Purge Entire Roster", callback_data="confirm_clear_groups")],
        [InlineKeyboardButton("← Back to Groups", callback_data="manage_groups")],
    ])


def paused_groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Reset All Paused Groups", callback_data="reset_paused_groups")],
        [InlineKeyboardButton("← Back to Groups", callback_data="manage_groups")],
    ])


# ── Guide / Disclaimer ──────────────────────────────────────────────────────

def guide_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_USERNAME}")],
        [InlineKeyboardButton("← Back to Main Menu", callback_data="home")],
    ])


def disclaimer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Info & Credits", callback_data="powered_by")],
        [InlineKeyboardButton("← Back to Main Menu", callback_data="home")],
    ])


# ── Advanced & Premium ───────────────────────────────────────────────────────

def health_monitor_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Re-check Health", callback_data="health_monitor")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def auto_responder_keyboard(enabled: bool, rules: dict) -> InlineKeyboardMarkup:
    toggle_text = "🔴 Disable Auto Reply" if enabled else "🟢 Enable Auto Reply"
    only_bcast = "🔴 Always Reply" if not rules.get("only_during_broadcast", True) else "🟢 Bcast Only"
    excl_contacts = "🔴 Reply Contacts" if not rules.get("exclude_contacts", True) else "🟢 Skip Contacts"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data="toggle_auto_responder")],
        [InlineKeyboardButton("📝 Set Reply Message", callback_data="set_auto_responder_message")],
        [
            InlineKeyboardButton(only_bcast, callback_data="toggle_rule_broadcast"),
            InlineKeyboardButton(excl_contacts, callback_data="toggle_rule_contacts"),
        ],
        [
            InlineKeyboardButton("⏱ Set Cooldown", callback_data="set_responder_cooldown_menu"),
            InlineKeyboardButton("🔍 Keyword Rules", callback_data="manage_keywords"),
        ],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def live_stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 View Activity Logs", callback_data="view_activity_logs")],
        [InlineKeyboardButton("🔄 Refresh Stats", callback_data="live_stats")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def premium_info_keyboard(is_premium: bool) -> InlineKeyboardMarkup:
    buttons = []
    if not is_premium:
        buttons.append([InlineKeyboardButton("💬 Upgrade Account", url="https://t.me/spinify")])
    buttons.append([InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")])
    return InlineKeyboardMarkup(buttons)


# ── Elite Admin Command Center ───────────────────────────────────────────────

def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Fleet Telemetry", callback_data="admin_view_all_users")],
        [InlineKeyboardButton("👤 User Portal", callback_data="admin_manage_user")],
        [InlineKeyboardButton("📢 Global Broadcast", callback_data="admin_global_broadcast")],
        [InlineKeyboardButton("🔄 Refresh Panel", callback_data="admin")],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def admin_all_users_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_view_all_users")],
        [InlineKeyboardButton("← Back to Admin Panel", callback_data="admin")],
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
            InlineKeyboardButton("❤️ Remote Health", callback_data=f"remote_health_{user_id}"),
            InlineKeyboardButton("📊 User Stats", callback_data=f"remote_stats_{user_id}"),
        ],
        [InlineKeyboardButton("🧹 Force Session Wipe", callback_data=f"remote_wipe_{user_id}")],
        [InlineKeyboardButton("← Back to User Portal", callback_data="admin_manage_user")],
        [InlineKeyboardButton("← Back to Admin Panel", callback_data="admin")],
    ])


# ── Advanced Enhancements ───────────────────────────────────────────────────

def quiet_hours_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    toggle_text = "🔴 Disable Sleep Mode" if enabled else "🟢 Enable Sleep Mode"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data="toggle_sleep_mode")],
        [
            InlineKeyboardButton("🌅 Set Start Hour", callback_data="set_sleep_start"),
            InlineKeyboardButton("🌄 Set End Hour", callback_data="set_sleep_end"),
        ],
        [InlineKeyboardButton("← Back to Dashboard", callback_data="dashboard")],
    ])


def cooldown_settings_keyboard(current_cooldown: int) -> InlineKeyboardMarkup:
    presets = [
        ("Disabled", 0),
        ("30 Mins", 1800),
        ("1 Hour", 3600),
        ("6 Hours", 21600),
        ("12 Hours", 43200),
        ("24 Hours", 86400),
    ]
    buttons = []
    for label, val in presets:
        prefix = "🟢 " if val == current_cooldown else ""
        buttons.append(InlineKeyboardButton(f"{prefix}{label}", callback_data=f"save_cooldown_{val}"))
    
    grid = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    grid.append([InlineKeyboardButton("← Back to Auto Responder", callback_data="auto_responder")])
    return InlineKeyboardMarkup(grid)


def keyword_rules_keyboard(keywords: dict) -> InlineKeyboardMarkup:
    buttons = []
    for kw in keywords.keys():
        buttons.append([
            InlineKeyboardButton(f"🗑 {kw}", callback_data=f"del_keyword_{kw}")
        ])
    buttons.append([InlineKeyboardButton("➕ Add Keyword Rule", callback_data="add_keyword_rule")])
    buttons.append([InlineKeyboardButton("← Back to Auto Responder", callback_data="auto_responder")])
    return InlineKeyboardMarkup(buttons)
