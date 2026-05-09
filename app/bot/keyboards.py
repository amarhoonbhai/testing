"""
Professional SaaS Keyboard Builders — Kurup Ads.
Text-only buttons for a minimalist, business-grade interface.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.config import CHANNEL_USERNAME, SUPPORT_USERNAME, REQUIRED_CHANNELS


def force_join_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for ch in REQUIRED_CHANNELS:
        buttons.append([InlineKeyboardButton(f"Join @{ch}", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton("Verify Membership", callback_data="check_join")])
    return InlineKeyboardMarkup(buttons)


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Dashboard", callback_data="dashboard")],
        [
            InlineKeyboardButton("Guide", callback_data="how_to_use"),
            InlineKeyboardButton("Terms", callback_data="disclaimer"),
        ],
        [
            InlineKeyboardButton("Network", url=f"https://t.me/{CHANNEL_USERNAME}"),
            InlineKeyboardButton("Support", url=f"https://t.me/{SUPPORT_USERNAME}"),
        ]
    ])


def dashboard_keyboard(ads_status: str = "paused", is_owner: bool = False) -> InlineKeyboardMarkup:
    # Campaign toggle
    if ads_status == "running":
        campaign_btn = InlineKeyboardButton("Stop Campaign", callback_data="stop_ads")
    else:
        campaign_btn = InlineKeyboardButton("Start Campaign", callback_data="start_ads")
        
    buttons = [
        [campaign_btn],
        [
            InlineKeyboardButton("Accounts", callback_data="my_accounts"),
            InlineKeyboardButton("Groups", callback_data="manage_groups"),
        ],
        [
            InlineKeyboardButton("Ads", callback_data="manage_ads"),
            InlineKeyboardButton("Delay", callback_data="set_interval"),
        ],
        [
            InlineKeyboardButton("Report", callback_data="analytics"),
            InlineKeyboardButton("Fix Issues", callback_data="admin_health" if is_owner else "home"),
        ],
        [
            InlineKeyboardButton("Responder", callback_data="auto_reply"),
            InlineKeyboardButton("Guide", callback_data="how_to_use"),
        ],
    ]
    if is_owner:
        buttons.append([InlineKeyboardButton("Admin Panel", callback_data="admin")])
    
    buttons.append([InlineKeyboardButton("Back", callback_data="home")])
    return InlineKeyboardMarkup(buttons)


def back_keyboard(callback_data: str = "dashboard") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=callback_data)]])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="cancel_conv")]])


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Users", callback_data="admin_users"),
            InlineKeyboardButton("Health", callback_data="admin_health"),
        ],
        [InlineKeyboardButton("Report", callback_data="admin_bstats")],
        [InlineKeyboardButton("Refresh", callback_data="admin")],
        [InlineKeyboardButton("Back", callback_data="dashboard")],
    ])


def ads_list_keyboard(ads: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for ad in ads:
        label = ad.get("ad_message", "Ad")[:20]
        buttons.append([
            InlineKeyboardButton(label, callback_data=f"view_ad:{ad['id']}"),
            InlineKeyboardButton("Remove", callback_data=f"del_ad:{ad['id']}"),
        ])
    if len(ads) < 3:
        buttons.append([InlineKeyboardButton("Add Ad", callback_data="add_ad")])
    buttons.append([InlineKeyboardButton("Back", callback_data="dashboard")])
    return InlineKeyboardMarkup(buttons)


def confirm_delete_ad_keyboard(ad_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Confirm Removal", callback_data=f"confirm_del_ad:{ad_id}")],
        [InlineKeyboardButton("Back", callback_data="manage_ads")],
    ])


def confirm_delete_keyboard(phone: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Confirm Removal", callback_data=f"confirm_del:{phone}")],
        [InlineKeyboardButton("Back", callback_data="delete_accounts")],
    ])


def delete_accounts_keyboard(accounts: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for acc in accounts:
        phone = acc["phone_masked"]
        buttons.append([InlineKeyboardButton(f"Remove {phone}", callback_data=f"del_acc:{phone}")])
    buttons.append([InlineKeyboardButton("Back", callback_data="dashboard")])
    return InlineKeyboardMarkup(buttons)


def no_accounts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Add Account", callback_data="add_account")],
        [InlineKeyboardButton("Back", callback_data="dashboard")],
    ])


def confirm_clear_groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Confirm Purge", callback_data="confirm_clear_groups")],
        [InlineKeyboardButton("Back", callback_data="manage_groups")],
    ])


def groups_after_add_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("View Groups", callback_data="view_groups")],
        [InlineKeyboardButton("Back", callback_data="dashboard")],
    ])


def groups_list_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Purge All", callback_data="clear_groups")],
        [InlineKeyboardButton("Back", callback_data="manage_groups")],
    ])


def groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Import Groups", callback_data="add_groups")],
        [InlineKeyboardButton("View Groups", callback_data="view_groups")],
        [InlineKeyboardButton("Clean Bad Groups", callback_data="clear_groups")], # Renamed as requested
        [InlineKeyboardButton("Back", callback_data="dashboard")],
    ])


def guide_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Support", url=f"https://t.me/{SUPPORT_USERNAME}")],
        [InlineKeyboardButton("Back", callback_data="home")],
    ])


def disclaimer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Credits", callback_data="powered_by")],
        [InlineKeyboardButton("Back", callback_data="home")],
    ])


def analytics_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Refresh", callback_data="analytics")],
        [InlineKeyboardButton("Back", callback_data="dashboard")],
    ])


def auto_reply_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    toggle_btn = (
        InlineKeyboardButton("Disable", callback_data="ar_disable")
        if enabled else
        InlineKeyboardButton("Enable", callback_data="ar_enable")
    )
    return InlineKeyboardMarkup([
        [toggle_btn],
        [InlineKeyboardButton("Edit Response", callback_data="ar_set_text")],
        [InlineKeyboardButton("Back", callback_data="dashboard")],
    ])


def accounts_list_keyboard(accounts: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for acc in accounts:
        phone = acc["phone_masked"]
        buttons.append([InlineKeyboardButton(f"{phone}", callback_data=f"acc_detail:{phone}")])
    buttons.append([
        InlineKeyboardButton("Refresh", callback_data="my_accounts"),
        InlineKeyboardButton("Remove Account", callback_data="delete_accounts"),
    ])
    buttons.append([
        InlineKeyboardButton("Add Account", callback_data="add_account"),
        InlineKeyboardButton("Back", callback_data="dashboard"),
    ])
    return InlineKeyboardMarkup(buttons)
