"""
Inline keyboard builders for all bot screens.

Professional, clean button labels matching the UI redesign.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME, REQUIRED_CHANNELS


# ═══════════════════════════════════════════════════════════════════════════════
#  FORCE JOIN
# ═══════════════════════════════════════════════════════════════════════════════

def force_join_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for ch in REQUIRED_CHANNELS:
        buttons.append(
            [InlineKeyboardButton(f"Join @{ch}", url=f"https://t.me/{ch}")]
        )
    buttons.append(
        [InlineKeyboardButton("✓  Verify Membership", callback_data="check_join")]
    )
    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════════════════════════
#  START
# ═══════════════════════════════════════════════════════════════════════════════

def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡  Command Center", callback_data="dashboard")],
        [
            InlineKeyboardButton("📖  Guide", callback_data="how_to_use"),
            InlineKeyboardButton("⚖  Terms", callback_data="disclaimer"),
        ],
        [
            InlineKeyboardButton("📢  Network", url=f"https://t.me/{CHANNEL_USERNAME}"),
            InlineKeyboardButton("💬  Support", url=f"https://t.me/{SUPPORT_USERNAME}"),
        ],
        [InlineKeyboardButton("⚡  Powered by ‣ Kᴜʀᴜᴘ Aᴅs", callback_data="powered_by")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def dashboard_keyboard(is_owner: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("➕  Link Account", callback_data="add_account"),
            InlineKeyboardButton("📱  Accounts", callback_data="my_accounts"),
        ],
        [
            InlineKeyboardButton("👁  View Ad", callback_data="view_ad"),
            InlineKeyboardButton("📝  Set Ad", callback_data="set_ad"),
        ],
        [
            InlineKeyboardButton("⏱  Timing", callback_data="set_interval"),
            InlineKeyboardButton("📂  Targets", callback_data="manage_groups"),
        ],
        [
            InlineKeyboardButton("📊  Report", callback_data="analytics"),
            InlineKeyboardButton("💬  Responder", callback_data="auto_reply"),
        ],
        [
            InlineKeyboardButton("▶  Go Live", callback_data="start_ads"),
            InlineKeyboardButton("⏸  Halt", callback_data="stop_ads"),
        ],
        [InlineKeyboardButton("🗑  Remove Accounts", callback_data="delete_accounts")],
    ]
    
    if is_owner:
        buttons.append([InlineKeyboardButton("⚙  Admin Console", callback_data="admin")])
    
    buttons.append([InlineKeyboardButton("↩  Home", callback_data="home")])
    
    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def no_accounts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕  Link Account", callback_data="add_account")],
        [InlineKeyboardButton("↩  Back", callback_data="dashboard")],
    ])


def accounts_list_keyboard(accounts: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for acc in accounts:
        phone = acc["phone_masked"]
        dot = "●" if acc.get("status") == "active" else "○"
        buttons.append(
            [InlineKeyboardButton(
                f"{dot}  {phone}",
                callback_data=f"acc_detail:{phone}",
            )]
        )
    buttons.append([
        InlineKeyboardButton("↻  Refresh", callback_data="my_accounts"),
        InlineKeyboardButton("🗑  Remove", callback_data="delete_accounts"),
    ])
    buttons.append(
        [InlineKeyboardButton("↩  Back", callback_data="dashboard")]
    )
    return InlineKeyboardMarkup(buttons)


def delete_accounts_keyboard(accounts: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for acc in accounts:
        phone = acc["phone_masked"]
        buttons.append(
            [InlineKeyboardButton(
                f"✕  {phone}",
                callback_data=f"del_acc:{phone}",
            )]
        )
    buttons.append(
        [InlineKeyboardButton("↩  Back", callback_data="dashboard")]
    )
    return InlineKeyboardMarkup(buttons)


def confirm_delete_keyboard(phone_masked: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✓  Confirm", callback_data=f"confirm_del:{phone_masked}"),
            InlineKeyboardButton("✕  Abort", callback_data="delete_accounts"),
        ],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕  Import Targets", callback_data="add_groups")],
        [InlineKeyboardButton("📋  View Manifest", callback_data="view_groups")],
        [InlineKeyboardButton("🗑  Purge All", callback_data="clear_groups")],
        [InlineKeyboardButton("↩  Back", callback_data="dashboard")],
    ])


def groups_list_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↻  Refresh", callback_data="view_groups")],
        [InlineKeyboardButton("➕  Import More", callback_data="add_groups")],
        [InlineKeyboardButton("↩  Back", callback_data="manage_groups")],
    ])


def confirm_clear_groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✓  Purge All", callback_data="confirm_clear_groups"),
            InlineKeyboardButton("✕  Abort", callback_data="manage_groups"),
        ],
    ])


def groups_after_add_keyboard() -> InlineKeyboardMarkup:
    """Shown after successfully adding groups — lets user add more or go back."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕  Add More Groups", callback_data="add_groups")],
        [InlineKeyboardButton("📋  View All Targets", callback_data="view_groups")],
        [InlineKeyboardButton("↩  Back to Groups", callback_data="manage_groups")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO REPLY
# ═══════════════════════════════════════════════════════════════════════════════

def auto_reply_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    toggle_text = "○  Disable" if enabled else "●  Enable"
    toggle_data = "ar_disable" if enabled else "ar_enable"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data=toggle_data)],
        [InlineKeyboardButton("✏  Compose Reply", callback_data="ar_set_text")],
        [InlineKeyboardButton("↩  Back", callback_data="dashboard")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

def analytics_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↻  Refresh", callback_data="analytics")],
        [InlineKeyboardButton("↩  Back", callback_data="dashboard")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  GENERIC
# ═══════════════════════════════════════════════════════════════════════════════

def back_keyboard(callback_data: str = "dashboard") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩  Back", callback_data=callback_data)],
    ])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✕  Cancel", callback_data="cancel_conv")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥  Users", callback_data="admin_users"),
            InlineKeyboardButton("🏥  Health", callback_data="admin_health"),
        ],
        [
            InlineKeyboardButton("📊  Broadcast Intel", callback_data="admin_bstats"),
        ],
        [InlineKeyboardButton("↻  Refresh", callback_data="admin")],
        [InlineKeyboardButton("↩  Back", callback_data="dashboard")],
    ])


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩  Admin Panel", callback_data="admin")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  GUIDE & DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

def guide_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚖  Terms of Use", callback_data="disclaimer")],
        [InlineKeyboardButton("↩  Home", callback_data="home")],
    ])


def disclaimer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖  Operations Guide", callback_data="how_to_use")],
        [InlineKeyboardButton("↩  Home", callback_data="home")],
    ])
