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
            [InlineKeyboardButton(f"‣ Jᴏɪɴ @{ch}", url=f"https://t.me/{ch}")]
        )
    buttons.append(
        [InlineKeyboardButton("✓  Vᴇʀɪғʏ Mᴇᴍʙᴇʀsʜɪᴘ", callback_data="check_join")]
    )
    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════════════════════════
#  START
# ═══════════════════════════════════════════════════════════════════════════════

def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡  Cᴏᴍᴍᴀɴᴅ Cᴇɴᴛᴇʀ", callback_data="dashboard")],
        [
            InlineKeyboardButton("📖  Gᴜɪᴅᴇ", callback_data="how_to_use"),
            InlineKeyboardButton("⚖  Tᴇʀᴍs", callback_data="disclaimer"),
        ],
        [
            InlineKeyboardButton("📢  Nᴇᴛᴡᴏʀᴋ", url=f"https://t.me/{CHANNEL_USERNAME}"),
            InlineKeyboardButton("💬  Sᴜᴘᴘᴏʀᴛ", url=f"https://t.me/{SUPPORT_USERNAME}"),
        ],
        [InlineKeyboardButton("⚡  Pᴏᴡᴇʀᴇᴅ ʙʏ ‣ Kᴜʀᴜᴘ Aᴅs", callback_data="powered_by")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def dashboard_keyboard(is_owner: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("➕  Lɪɴᴋ Aᴄᴄᴏᴜɴᴛ", callback_data="add_account"),
            InlineKeyboardButton("📱  Aᴄᴄᴏᴜɴᴛs", callback_data="my_accounts"),
        ],
        [
            InlineKeyboardButton("📢  Aᴅ Cᴏɴsᴏʟᴇ", callback_data="manage_ads"),
            InlineKeyboardButton("⏱  Sᴄʜᴇᴅᴜʟᴇ", callback_data="set_interval"),
        ],
        [
            InlineKeyboardButton("📂  Tᴀʀɢᴇᴛs", callback_data="manage_groups"),
            InlineKeyboardButton("📊  Rᴇᴘᴏʀᴛ", callback_data="analytics"),
        ],
        [
            InlineKeyboardButton("▶  Gᴏ Lɪᴠᴇ", callback_data="start_ads"),
            InlineKeyboardButton("⏸  Hᴀʟᴛ", callback_data="stop_ads"),
        ],
        [
            InlineKeyboardButton("💬  Rᴇsᴘᴏɴᴅᴇʀ", callback_data="auto_reply"),
            InlineKeyboardButton("🗑  Pᴜʀɢᴇ Aᴄᴄs", callback_data="delete_accounts"),
        ],
    ]
    
    if is_owner:
        buttons.append([InlineKeyboardButton("⚙  Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin")])
    
    buttons.append([InlineKeyboardButton("↩  Hᴏᴍᴇ", callback_data="home")])
    
    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════════════════════════
#  AD MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def ads_list_keyboard(ads: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for ad in ads:
        label = ad.get("ad_message", "Media Ad")[:15] + "..."
        buttons.append([
            InlineKeyboardButton(f"👁 {label}", callback_data=f"view_ad:{ad['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"del_ad:{ad['id']}"),
        ])
    
    if len(ads) < 3:
        buttons.append([InlineKeyboardButton("➕  Aᴅᴅ Cʀᴇᴀᴛɪᴠᴇ", callback_data="add_ad")])
    
    buttons.append([InlineKeyboardButton("↩  Bᴀᴄᴋ", callback_data="dashboard")])
    return InlineKeyboardMarkup(buttons)


def confirm_delete_ad_keyboard(ad_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✓  Cᴏɴғɪʀᴍ Pᴜʀɢᴇ", callback_data=f"confirm_del_ad:{ad_id}"),
            InlineKeyboardButton("✕  Aʙᴏʀᴛ", callback_data="manage_ads"),
        ],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

def no_accounts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕  Lɪɴᴋ Aᴄᴄᴏᴜɴᴛ", callback_data="add_account")],
        [InlineKeyboardButton("↩  Bᴀᴄᴋ", callback_data="dashboard")],
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
        InlineKeyboardButton("↻  Rᴇғʀᴇsʜ", callback_data="my_accounts"),
        InlineKeyboardButton("🗑  Rᴇᴍᴏᴠᴇ", callback_data="delete_accounts"),
    ])
    buttons.append(
        [InlineKeyboardButton("↩  Bᴀᴄᴋ", callback_data="dashboard")]
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
        [InlineKeyboardButton("↩  Bᴀᴄᴋ", callback_data="dashboard")]
    )
    return InlineKeyboardMarkup(buttons)


def confirm_delete_keyboard(phone_masked: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✓  Cᴏɴғɪʀᴍ", callback_data=f"confirm_del:{phone_masked}"),
            InlineKeyboardButton("✕  Aʙᴏʀᴛ", callback_data="delete_accounts"),
        ],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕  Iᴍᴘᴏʀᴛ Tᴀʀɢᴇᴛs", callback_data="add_groups")],
        [InlineKeyboardButton("📋  Vɪᴇᴡ Mᴀɴɪғᴇsᴛ", callback_data="view_groups")],
        [InlineKeyboardButton("🗑  Pᴜʀɢᴇ Aʟʟ", callback_data="clear_groups")],
        [InlineKeyboardButton("↩  Bᴀᴄᴋ", callback_data="dashboard")],
    ])


def groups_list_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↻  Rᴇғʀᴇsʜ", callback_data="view_groups")],
        [InlineKeyboardButton("➕  Iᴍᴘᴏʀᴛ Mᴏʀᴇ", callback_data="add_groups")],
        [InlineKeyboardButton("↩  Bᴀᴄᴋ", callback_data="manage_groups")],
    ])


def confirm_clear_groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✓  Pᴜʀɢᴇ Aʟʟ", callback_data="confirm_clear_groups"),
            InlineKeyboardButton("✕  Aʙᴏʀᴛ", callback_data="manage_groups"),
        ],
    ])


def groups_after_add_keyboard() -> InlineKeyboardMarkup:
    """Shown after successfully adding groups — lets user add more or go back."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕  Aᴅᴅ Mᴏʀᴇ Tᴀʀɢᴇᴛs", callback_data="add_groups")],
        [InlineKeyboardButton("📋  Vɪᴇᴡ Aʟʟ Pᴏᴏʟs", callback_data="view_groups")],
        [InlineKeyboardButton("↩  Bᴀᴄᴋ ᴛᴏ Mᴀɴᴀɢᴇᴍᴇɴᴛ", callback_data="manage_groups")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTO REPLY
# ═══════════════════════════════════════════════════════════════════════════════

def auto_reply_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    toggle_text = "○  Dɪsᴀʙʟᴇ" if enabled else "●  Eɴᴀʙʟᴇ"
    toggle_data = "ar_disable" if enabled else "ar_enable"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data=toggle_data)],
        [InlineKeyboardButton("✏  Cᴏᴍᴘᴏsᴇ Rᴇsᴘᴏɴsᴇ", callback_data="ar_set_text")],
        [InlineKeyboardButton("↩  Bᴀᴄᴋ", callback_data="dashboard")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

def analytics_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↻  Rᴇғʀᴇsʜ Rᴇᴘᴏʀᴛ", callback_data="analytics")],
        [InlineKeyboardButton("↩  Bᴀᴄᴋ", callback_data="dashboard")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  GENERIC
# ═══════════════════════════════════════════════════════════════════════════════

def back_keyboard(callback_data: str = "dashboard") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩  Bᴀᴄᴋ", callback_data=callback_data)],
    ])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✕  Cᴀɴᴄᴇʟ", callback_data="cancel_conv")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥  Usᴇʀs", callback_data="admin_users"),
            InlineKeyboardButton("🏥  Hᴇᴀʟᴛʜ", callback_data="admin_health"),
        ],
        [
            InlineKeyboardButton("📊  Bʀᴏᴀᴅᴄᴀsᴛ Iɴᴛᴇʟ", callback_data="admin_bstats"),
        ],
        [InlineKeyboardButton("↻  Rᴇғʀᴇsʜ Sᴛᴀᴛs", callback_data="admin")],
        [InlineKeyboardButton("↩  Bᴀᴄᴋ", callback_data="dashboard")],
    ])


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩  Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin")],
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  GUIDE & DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

def guide_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚖  Tᴇʀᴍs ᴏғ Usᴇ", callback_data="disclaimer")],
        [InlineKeyboardButton("↩  Hᴏᴍᴇ", callback_data="home")],
    ])


def disclaimer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖  Oᴘᴇʀᴀᴛɪᴏɴs Gᴜɪᴅᴇ", callback_data="how_to_use")],
        [InlineKeyboardButton("↩  Hᴏᴍᴇ", callback_data="home")],
    ])
