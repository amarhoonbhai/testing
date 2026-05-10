"""
Professional Keyboard Builders — Group Broadcaster.
Clean inline button layouts.
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
        [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")],
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
    # Broadcast toggle
    if is_broadcasting:
        broadcast_btn = InlineKeyboardButton("⏹ Stop Broadcasting", callback_data="stop_broadcast")
    else:
        broadcast_btn = InlineKeyboardButton("▶️ Start Broadcasting", callback_data="start_broadcast")

    # Account button
    if has_account:
        account_btn = InlineKeyboardButton("🔗 My Account", callback_data="view_account")
    else:
        account_btn = InlineKeyboardButton("🔗 Connect Account", callback_data="connect_account")

    buttons = [
        [broadcast_btn],
        [
            InlineKeyboardButton("📝 Set Message", callback_data="set_message"),
            InlineKeyboardButton("👥 Groups", callback_data="manage_groups"),
        ],
        [
            account_btn,
            InlineKeyboardButton("⏱ Interval", callback_data="set_interval"),
        ],
    ]

    if is_owner:
        buttons.append([InlineKeyboardButton("🔧 Admin Panel", callback_data="admin")])

    buttons.append([InlineKeyboardButton("← Back", callback_data="home")])
    return InlineKeyboardMarkup(buttons)


def back_keyboard(callback_data: str = "dashboard") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("← Back", callback_data=callback_data)]])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("✖ Cancel", callback_data="cancel_conv")]])


# ── Account ──────────────────────────────────────────────────────────────────

def account_info_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔌 Disconnect", callback_data="disconnect_account")],
        [InlineKeyboardButton("← Back", callback_data="dashboard")],
    ])


def no_account_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Connect Account", callback_data="connect_account")],
        [InlineKeyboardButton("← Back", callback_data="dashboard")],
    ])


def confirm_disconnect_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Disconnect", callback_data="confirm_disconnect")],
        [InlineKeyboardButton("← Back", callback_data="view_account")],
    ])


# ── Message ──────────────────────────────────────────────────────────────────

def message_keyboard(has_message: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if has_message:
        buttons.append([InlineKeyboardButton("👁 Preview", callback_data="preview_message")])
        buttons.append([InlineKeyboardButton("🗑 Clear Message", callback_data="clear_message")])
    buttons.append([InlineKeyboardButton("📝 Set New Message", callback_data="input_message")])
    buttons.append([InlineKeyboardButton("← Back", callback_data="dashboard")])
    return InlineKeyboardMarkup(buttons)


def after_message_saved_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👁 Preview", callback_data="preview_message")],
        [InlineKeyboardButton("← Back", callback_data="dashboard")],
    ])


# ── Groups ───────────────────────────────────────────────────────────────────

def groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Groups", callback_data="add_groups")],
        [InlineKeyboardButton("📋 View Groups", callback_data="view_groups")],
        [InlineKeyboardButton("🗑 Clear All Groups", callback_data="clear_groups")],
        [InlineKeyboardButton("← Back", callback_data="dashboard")],
    ])


def groups_after_add_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 View Groups", callback_data="view_groups")],
        [InlineKeyboardButton("← Back", callback_data="dashboard")],
    ])


def groups_list_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Clear All", callback_data="clear_groups")],
        [InlineKeyboardButton("← Back", callback_data="manage_groups")],
    ])


def confirm_clear_groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Clear All", callback_data="confirm_clear_groups")],
        [InlineKeyboardButton("← Back", callback_data="manage_groups")],
    ])


# ── Guide / Disclaimer ──────────────────────────────────────────────────────

def guide_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_USERNAME}")],
        [InlineKeyboardButton("← Back", callback_data="home")],
    ])


def disclaimer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Credits", callback_data="powered_by")],
        [InlineKeyboardButton("← Back", callback_data="home")],
    ])


# ── Admin ────────────────────────────────────────────────────────────────────

def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin")],
        [InlineKeyboardButton("← Back", callback_data="dashboard")],
    ])
