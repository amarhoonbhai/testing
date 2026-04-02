"""
Inline keyboard builders for Main Bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from core.config import MAIN_BOT_USERNAME, CHANNEL_USERNAME, WEBAPP_URL


def get_welcome_keyboard() -> InlineKeyboardMarkup:
    """Build welcome screen keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🚀 OPEN KURUP ADS BOT", web_app=WebAppInfo(url=WEBAPP_URL)),
        ],
        [
            InlineKeyboardButton("📌 Join Community", url=f"https://t.me/{CHANNEL_USERNAME}"),
            InlineKeyboardButton("📊 Stats", callback_data="user_stats"),
        ],
        [
            InlineKeyboardButton("📘 Help & Docs", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Build dashboard keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🚀 OPEN KURUP ADS BOT", web_app=WebAppInfo(url=WEBAPP_URL)),
        ],
        [
            InlineKeyboardButton("🎁 My Plan", callback_data="my_plan"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_account_selection_keyboard(sessions: list) -> InlineKeyboardMarkup:
    """Build keyboard with list of accounts for selection."""
    keyboard = []
    
    for s in sessions:
        phone = s.get("phone", "Unknown")
        status = "🟢" if s.get("connected") else "🔴"
        keyboard.append([InlineKeyboardButton(f"{status} {phone}", callback_data=f"manage_account:{phone}")])
    
    keyboard.append([InlineKeyboardButton("➕ Add Another Account", callback_data="add_account")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Dashboard", callback_data="dashboard")])
    
    return InlineKeyboardMarkup(keyboard)


def get_plan_keyboard() -> InlineKeyboardMarkup:
    """Build plan display keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("💎 Upgrade to WEEKLY (₹99)", callback_data="buy_plan:week"),
        ],
        [
            InlineKeyboardButton("🏆 Upgrade to MONTHLY (₹299)", callback_data="buy_plan:month"),
        ],
        [
            InlineKeyboardButton("🧾 Redeem Promo Code", callback_data="redeem_code"),
        ],
        [
            InlineKeyboardButton("👨‍💻 Contact Support", url="https://t.me/spinify"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="dashboard"),
            InlineKeyboardButton("🏠 Home", callback_data="home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_upgrade_keyboard(target_user_id: int) -> InlineKeyboardMarkup:
    """Build admin upgrade selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("💎 Grant 1 Week", callback_data=f"adm_upgr:{target_user_id}:week"),
            InlineKeyboardButton("🏆 Grant 1 Month", callback_data=f"adm_upgr:{target_user_id}:month"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Admin", callback_data="admin"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_referral_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    """Build referral screen keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📤 Share Link with Friends", switch_inline_query=referral_link),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="dashboard"),
            InlineKeyboardButton("🏠 Home", callback_data="home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_home_keyboard() -> InlineKeyboardMarkup:
    """Simple back and home keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔙 Go Back", callback_data="dashboard"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_home_keyboard() -> InlineKeyboardMarkup:
    """Just home button."""
    keyboard = [
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Build admin panel keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🩺 Health Monitor", callback_data="admin_health"),
            InlineKeyboardButton("📊 Live Stats", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("📁 Group Stats", callback_data="admin_group_stats"),
            InlineKeyboardButton("📢 Global Blast", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton("🎟 Give 1 Week", callback_data="gen_code:week"),
            InlineKeyboardButton("🎟 Give 1 Month", callback_data="gen_code:month"),
        ],
        [
            InlineKeyboardButton("⚡ Quick Upgrade User", callback_data="admin_upgrade_init"),
        ],
        [
            InlineKeyboardButton("👥 User Database", callback_data="admin_users"),
            InlineKeyboardButton("🌙 Night Mode", callback_data="admin_nightmode"),
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_stats_keyboard() -> InlineKeyboardMarkup:
    """Stats screen keyboard — includes a refresh button."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="home"),
        ],
        [
            InlineKeyboardButton("🔙 Admin Panel", callback_data="admin"),
        ],
    ])


def get_admin_group_stats_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for group stats view."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Retry All Failing", callback_data="admin_retry_failing"),
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_group_stats"),
            InlineKeyboardButton("🔙 Admin Panel", callback_data="admin"),
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="home"),
        ],
    ])



def get_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Build broadcast target selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📢 All Users", callback_data="broadcast:all"),
            InlineKeyboardButton("🔗 Active APIs", callback_data="broadcast:connected"),
        ],
        [
            InlineKeyboardButton("🎁 Trial Group", callback_data="broadcast:trial"),
            InlineKeyboardButton("💎 Premium Base", callback_data="broadcast:paid"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Tools", callback_data="admin"),
            InlineKeyboardButton("🏠 Home", callback_data="home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_manage_account_keyboard(phone: str) -> InlineKeyboardMarkup:
    """Build manage account keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔌 Disconnect Session", callback_data=f"disconnect_account:{phone}"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="accounts_list"),
            InlineKeyboardButton("🏠 Home", callback_data="home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_disconnect_keyboard(phone: str) -> InlineKeyboardMarkup:
    """Build disconnect confirmation keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ CONFIRM: WIPE IT", callback_data=f"confirm_disconnect:{phone}"),
        ],
        [
            InlineKeyboardButton("❌ CANCEL", callback_data=f"manage_account:{phone}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Build profile screen keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("⚙️ Manage Accounts", callback_data="accounts_list"),
        ],
        [
            InlineKeyboardButton("🎁 My Plan", callback_data="my_plan"),
            InlineKeyboardButton("🤝 Referrals", callback_data="referral"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Dashboard", callback_data="dashboard"),
            InlineKeyboardButton("🏠 Home", callback_data="home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_night_mode_settings_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for global night mode settings."""
    keyboard = [
        [
            InlineKeyboardButton("🔴 FORCE ON", callback_data="set_nightmode:on"),
            InlineKeyboardButton("🟢 FORCE OFF", callback_data="set_nightmode:off"),
        ],
        [
            InlineKeyboardButton("⏳ AUTO (Schedule)", callback_data="set_nightmode:auto"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_stats"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


GROUPS_PER_PAGE = 8


def get_manage_groups_keyboard(groups: list, page: int = 0) -> InlineKeyboardMarkup:
    """
    Paginated group manager keyboard.
    Shows GROUPS_PER_PAGE groups per page with:
      - ✅/⛔ toggle (enable/disable)
      - ❌ remove
    Plus: prev/next page navigation and Add Group button.
    """
    keyboard = []
    total = len(groups)
    total_pages = max(1, (total + GROUPS_PER_PAGE - 1) // GROUPS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start = page * GROUPS_PER_PAGE
    page_groups = groups[start: start + GROUPS_PER_PAGE]

    # ── Group rows ──────────────────────────────────────────────────────────
    for g in page_groups:
        title = g.get("chat_title", "Unknown")
        chat_id = g.get("chat_id")
        enabled = g.get("enabled", True)
        display = title[:22] + "…" if len(title) > 22 else title
        toggle_icon = "✅" if enabled else "⛔"

        keyboard.append([
            InlineKeyboardButton(
                f"{toggle_icon} {display}",
                callback_data=f"group_toggle:{chat_id}:{page}"
            ),
            InlineKeyboardButton(
                "🗑", callback_data=f"remove_group_ui:{chat_id}:{page}"
            ),
        ])

    # ── Pagination row ──────────────────────────────────────────────────────
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"groups_page:{page-1}"))
    nav_row.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"groups_page:{page+1}"))
    if nav_row:
        keyboard.append(nav_row)

    # ── Action row ──────────────────────────────────────────────────────────
    keyboard.append([
        InlineKeyboardButton("➕ Add Groups", callback_data="add_group_prompt"),
        InlineKeyboardButton("🗑 Clear All", callback_data="confirm_clear_groups"),
    ])
    keyboard.append([
        InlineKeyboardButton(f"📊 {total} groups total", callback_data="noop"),
    ])
    keyboard.append([
        InlineKeyboardButton("🔙 Dashboard", callback_data="dashboard"),
    ])

    return InlineKeyboardMarkup(keyboard)


def get_confirm_clear_groups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚠️ YES, Remove All", callback_data="clear_groups_confirmed")],
        [InlineKeyboardButton("❌ Cancel", callback_data="manage_groups:0")],
    ])


def get_manage_settings_keyboard(config: dict, is_branded: bool = True) -> InlineKeyboardMarkup:
    """Build keyboard for user settings management."""
    shuffle_status = "🟢 ON" if config.get("shuffle_mode") else "⚫ OFF"
    copy_status = "🟢 ON" if config.get("copy_mode") else "⚫ OFF"
    responder_status = "🟢 ON" if config.get("auto_reply_enabled") else "⚫ OFF"
    
    # Add lock icons if not branded
    s_lock = "" if is_branded else " 🔒"
    c_lock = "" if is_branded else " 🔒"
    r_lock = "" if is_branded else " 🔒"
    m_lock = "" if is_branded else " 🔒"
    
    keyboard = [
        [
            InlineKeyboardButton(f"🔁 Shuffle: {shuffle_status}{s_lock}", callback_data="toggle_shuffle_ui"),
            InlineKeyboardButton(f"📝 Copy Mode: {copy_status}{c_lock}", callback_data="toggle_copy_ui"),
        ],
        [
            InlineKeyboardButton(f"🔄 Toggle Send Mode{m_lock}", callback_data="toggle_send_mode"),
        ],
        [
            InlineKeyboardButton("⏱️ Set Interval", callback_data="set_interval_prompt"),
            InlineKeyboardButton(f"🤖 Responder: {responder_status}{r_lock}", callback_data="toggle_responder_ui"),
        ],
        [
            InlineKeyboardButton(f"✍️ Set Responder Text{r_lock}", callback_data="set_responder_text_prompt"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Dashboard", callback_data="dashboard"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_guide_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for the main help screen — includes button to open the full guide."""
    keyboard = [
        [
            InlineKeyboardButton("📖 Beginner's Guide", callback_data="guide"),
        ],
        [
            InlineKeyboardButton("🏠 Back to Home", callback_data="home"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
