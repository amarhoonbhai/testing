"""
Inline keyboard builders for all bot screens.

Reusable keyboard functions with consistent layout.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME, REQUIRED_CHANNELS


# ═══════════════════════════════════════════════════════════════════════════════
#  FORCE JOIN
# ═══════════════════════════════════════════════════════════════════════════════

def force_join_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for force-join verification."""
    buttons = []
    for ch in REQUIRED_CHANNELS:
        buttons.append(
            [InlineKeyboardButton(f"Join @{ch}", url=f"https://t.me/{ch}")]
        )
    buttons.append(
        [InlineKeyboardButton("✅ Verify", callback_data="check_join")]
    )
    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════════════════════════
#  START / WELCOME
# ═══════════════════════════════════════════════════════════════════════════════

def start_keyboard() -> InlineKeyboardMarkup:
    """Main start screen keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")],
        [
            InlineKeyboardButton("📖 Guide", callback_data="how_to_use"),
            InlineKeyboardButton("📜 Disclaimer", callback_data="disclaimer"),
        ],
        [
            InlineKeyboardButton("📢 Updates", url=f"https://t.me/{CHANNEL_USERNAME}"),
            InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_USERNAME}"),
        ],
        [InlineKeyboardButton("⚡ Powered by", callback_data="powered_by")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def dashboard_keyboard() -> InlineKeyboardMarkup:
    """Dashboard 2-column layout."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Accounts", callback_data="add_account"),
            InlineKeyboardButton("📱 My Accounts", callback_data="my_accounts"),
        ],
        [
            InlineKeyboardButton("📝 Set Ad Message", callback_data="set_ad"),
            InlineKeyboardButton("⏱️ Set Interval", callback_data="set_interval"),
        ],
        [
            InlineKeyboardButton("📂 Manage Groups", callback_data="manage_groups"),
            InlineKeyboardButton("📈 Analytics", callback_data="analytics"),
        ],
        [
            InlineKeyboardButton("▶️ Start Ads", callback_data="start_ads"),
            InlineKeyboardButton("⏸️ Stop Ads", callback_data="stop_ads"),
        ],
        [
            InlineKeyboardButton("🗑️ Delete Accounts", callback_data="delete_accounts"),
            InlineKeyboardButton("💬 Auto Reply", callback_data="auto_reply"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="home")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def no_accounts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Add Account", callback_data="add_account")],
        [InlineKeyboardButton("🔙 Back", callback_data="dashboard")],
    ])


def accounts_list_keyboard(accounts: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for acc in accounts:
        phone = acc["phone_masked"]
        status_icon = "✅" if acc.get("status") == "active" else "⏸️"
        buttons.append(
            [InlineKeyboardButton(
                f"{status_icon} {phone}",
                callback_data=f"acc_detail:{phone}",
            )]
        )
    buttons.append([
        InlineKeyboardButton("🔄 Refresh", callback_data="my_accounts"),
        InlineKeyboardButton("🗑️ Remove", callback_data="delete_accounts"),
    ])
    buttons.append(
        [InlineKeyboardButton("🔙 Back", callback_data="dashboard")]
    )
    return InlineKeyboardMarkup(buttons)


def delete_accounts_keyboard(accounts: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for acc in accounts:
        phone = acc["phone_masked"]
        buttons.append(
            [InlineKeyboardButton(
                f"🗑️ {phone}",
                callback_data=f"del_acc:{phone}",
            )]
        )
    buttons.append(
        [InlineKeyboardButton("🔙 Back", callback_data="dashboard")]
    )
    return InlineKeyboardMarkup(buttons)


def confirm_delete_keyboard(phone_masked: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_del:{phone_masked}"),
            InlineKeyboardButton("❌ Cancel", callback_data="delete_accounts"),
        ],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def groups_keyboard() -> InlineKeyboardMarkup:
    """Groups management main keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Groups", callback_data="add_groups")],
        [InlineKeyboardButton("📋 View Groups", callback_data="view_groups")],
        [InlineKeyboardButton("🗑️ Clear All Groups", callback_data="clear_groups")],
        [InlineKeyboardButton("🔙 Back", callback_data="dashboard")],
    ])


def groups_list_keyboard() -> InlineKeyboardMarkup:
    """Groups list view keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="view_groups")],
        [InlineKeyboardButton("➕ Add More", callback_data="add_groups")],
        [InlineKeyboardButton("🔙 Back", callback_data="manage_groups")],
    ])


def confirm_clear_groups_keyboard() -> InlineKeyboardMarkup:
    """Confirmation for clearing all groups."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Clear All", callback_data="confirm_clear_groups"),
            InlineKeyboardButton("❌ Cancel", callback_data="manage_groups"),
        ],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO REPLY
# ═══════════════════════════════════════════════════════════════════════════════

def auto_reply_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    toggle_text = "🔴 Disable" if enabled else "✅ Enable"
    toggle_data = "ar_disable" if enabled else "ar_enable"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data=toggle_data)],
        [InlineKeyboardButton("📝 Set Reply Text", callback_data="ar_set_text")],
        [InlineKeyboardButton("🔙 Back", callback_data="dashboard")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

def analytics_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="analytics")],
        [InlineKeyboardButton("🔙 Back", callback_data="dashboard")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  GENERIC
# ═══════════════════════════════════════════════════════════════════════════════

def back_keyboard(callback_data: str = "dashboard") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=callback_data)],
    ])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_conv")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def admin_keyboard() -> InlineKeyboardMarkup:
    """Admin panel main keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            InlineKeyboardButton("🏥 Health", callback_data="admin_health"),
        ],
        [
            InlineKeyboardButton("📊 Broadcast Stats", callback_data="admin_bstats"),
        ],
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin")],
        [InlineKeyboardButton("🔙 Back", callback_data="dashboard")],
    ])


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  GUIDE & DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

def guide_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Disclaimer", callback_data="disclaimer")],
        [InlineKeyboardButton("🔙 Back", callback_data="home")],
    ])


def disclaimer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Guide", callback_data="how_to_use")],
        [InlineKeyboardButton("🔙 Back", callback_data="home")],
    ])

