"""
Professional SaaS Message Templates — Kurup Ads.
Redesigned for a minimalist, business-grade aesthetic.
"""

from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME, MIN_INTERVAL

# ━━━━━━━━━━━━━━━━━━━━
#  UI CORE DESIGN
# ━━━━━━━━━━━━━━━━━━━━

def _header(title: str) -> str:
    return (
        f"<b>{title.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )

def _footer() -> str:
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>KURUP ADS ELITE</b>"
    )

def _stat_line(label: str, value: any, icon: str = "") -> str:
    # Saas style: Label → Value
    icon_str = f"{icon}  " if icon else ""
    return f"{icon_str}{label:<12} → <code>{value}</code>\n"


# ━━━━━━━━━━━━━━━━━━━━
#  TEMPLATES
# ━━━━━━━━━━━━━━━━━━━━

def welcome_text(first_name: str, last_name: str = "", user_id: int = 0, username: str = "") -> str:
    full_name = f"{first_name} {last_name}".strip()
    return (
        f"{_header('Welcome')}"
        f"Hello <b>{full_name}</b>,\n\n"
        f"{_stat_line('User ID', user_id)}"
        f"{_stat_line('Access', '@' + username if username else 'Global')}"
        f"\n"
        f"▸ Professional Campaign Automation\n"
        f"▸ Encrypted Account Hosting\n"
        f"↳ <i>Your system is active and ready.</i>"
        f"{_footer()}"
    )


def dashboard_text(
    account_count: int,
    max_accounts: int,
    ad_set: bool,
    interval: int,
    ads_status: str,
    group_count: int = 0,
    night_paused: bool = False,
    active_in_cycle: int = 0,
    health_stats: dict = None,
    analytics: dict = None
) -> str:
    status_text = "Running" if ads_status == "running" else "Idle"
    if night_paused: status_text = "Night Mode"

    health = health_stats or {}
    stats = analytics or {}
    
    total_sent = stats.get("total_sent", 0)
    failed_count = stats.get("failed_count", 0)
    total = total_sent + failed_count
    rate = (total_sent / total * 100) if total > 0 else 0

    return (
        f"<b>KURUP ADS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Campaign Dashboard\n\n"
        f"{_stat_line('Status', status_text)}"
        f"{_stat_line('Accounts', f'{account_count} Active')}"
        f"{_stat_line('Groups', f'{group_count} Active')}"
        f"{_stat_line('Ads', '2 Ready' if ad_set else 'Missing')}"
        f"{_stat_line('Delay', f'{interval // 60} Minutes')}"
        f"\n"
        f"Today’s Report\n"
        f"{_stat_line('Sent', f'{total_sent:,}')}"
        f"{_stat_line('Failed', f'{failed_count:,}')}"
        f"{_stat_line('Success Rate', f'{rate:.1f}%')}"
        f"\n"
        f"Next Step\n"
        f"↳ {'Your campaign is running safely.' if ads_status == 'running' else 'Complete setup to start campaign.'}"
        f"{_footer()}"
    )


def accounts_list_text(accounts: list[dict]) -> str:
    text = f"{_header('Accounts')}"
    if not accounts:
        text += "↳ <i>No accounts linked.</i>\n"
    else:
        for i, acc in enumerate(accounts, 1):
            status = acc.get("status", "active")
            health = acc.get("health", 100)
            text += f"{i}. <code>{acc['phone_masked']}</code> ({health}%)\n"
            text += f"┃ Status → {status.title()}\n"
    
    text += _footer()
    return text


def groups_text(total: int, active: int, disabled: int) -> str:
    return (
        f"{_header('Groups')}"
        f"{_stat_line('Total', total)}"
        f"{_stat_line('Active', active)}"
        f"{_stat_line('Restricted', disabled)}"
        f"\n"
        f"↳ <i>Automated group cleanup is active.</i>"
        f"{_footer()}"
    )


def analytics_text(total_sent: int, failed_count: int, last_sent: str = "Never") -> str:
    total = total_sent + failed_count
    rate = (total_sent / total * 100) if total > 0 else 0
    
    return (
        f"{_header('Report')}"
        f"{_stat_line('Delivered', total_sent)}"
        f"{_stat_line('Failed', failed_count)}"
        f"{_stat_line('Success', f'{rate:.1f}%')}"
        f"{_stat_line('Last Activity', last_sent)}"
        f"{_footer()}"
    )


def error_text(msg: str) -> str:
    return (
        f"<b>ERROR</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"┃ {msg}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

def success_text(msg: str) -> str:
    return (
        f"<b>SUCCESS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"┃ {msg}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

def add_account_text() -> str:
    return (
        f"{_header('Add Account')}"
        f"Please provide the phone number:\n\n"
        f"▸ Format: <code>+1234567890</code>\n"
        f"↳ <i>Encryption is active.</i>"
        f"{_footer()}"
    )

def otp_prompt_text() -> str:
    return (
        f"{_header('Verification')}"
        f"Enter the Telegram login code below.\n\n"
        f"┃ <i>Waiting for input...</i>"
        f"{_footer()}"
    )

def password_2fa_text() -> str:
    return (
        f"{_header('Cloud Password')}"
        f"Account is 2FA protected.\n"
        f"Please enter your password:\n\n"
        f"↳ <i>Secure Session</i>"
        f"{_footer()}"
    )

def account_added_text(phone: str) -> str:
    return (
        f"{_header('Sync Complete')}"
        f"Account <code>{phone}</code> linked.\n\n"
        f"┃ Status → Operational\n"
        f"┃ Branding → Active"
        f"{_footer()}"
    )

def account_deleted_text(phone: str) -> str:
    return (
        f"{_header('Account Purged')}"
        f"Account <code>{phone}</code> disconnected."
        f"{_footer()}"
    )

def delete_confirm_text(phone: str) -> str:
    return (
        f"{_header('Confirm Removal')}"
        f"Are you sure you want to remove\n"
        f"account <code>{phone}</code>?\n\n"
        f"↳ <i>This cannot be undone.</i>"
        f"{_footer()}"
    )

def max_accounts_text(limit: int) -> str:
    return (
        f"{_header('Limit Reached')}"
        f"Your plan allows up to {limit} accounts."
        f"{_footer()}"
    )

def add_groups_text() -> str:
    return (
        f"{_header('Import Groups')}"
        f"Send group links or usernames.\n\n"
        f"▸ One link per line\n"
        f"▸ Folder links supported"
        f"{_footer()}"
    )

def groups_added_text(added: int, failed: int) -> str:
    return (
        f"{_header('Import Complete')}"
        f"{_stat_line('Added', added)}"
        f"{_stat_line('Failed', failed)}"
        f"{_footer()}"
    )

def no_groups_text() -> str:
    return (
        f"{_header('No Groups')}"
        f"Group list is empty. Please import\n"
        f"groups to start campaign."
        f"{_footer()}"
    )

def groups_list_text(groups: list[dict]) -> str:
    text = f"{_header('Group Manifest')}"
    for i, g in enumerate(groups[:20], 1):
        text += f"{i}. <code>{g['identifier']}</code>\n"
    if len(groups) > 20:
        text += f"\n↳ <i>+ {len(groups)-20} more groups.</i>\n"
    text += _footer()
    return text

def no_accounts_text() -> str:
    return (
        f"{_header('No Accounts')}"
        f"No accounts linked. Please link\n"
        f"at least one account."
        f"{_footer()}"
    )

def account_detail_text(acc: dict) -> str:
    status = acc.get("status", "active").upper()
    health = acc.get("health", 100)
    success = acc.get("success_count", 0)
    failure = acc.get("failure_count", 0)
    
    return (
        f"{_header('Account Detail')}"
        f"{_stat_line('Phone', acc['phone_masked'])}"
        f"{_stat_line('Status', status)}"
        f"{_stat_line('Health', f'{health}%')}"
        f"\n"
        f"Performance\n"
        f"┃ Sent → {success}\n"
        f"┃ Errors → {failure}\n"
        f"\n"
        f"↳ <i>{acc.get('status_reason', 'Normal')}</i>"
        f"{_footer()}"
    )

def set_auto_reply_prompt_text() -> str:
    return (
        f"{_header('Auto Responder')}"
        f"Provide the message for automated\n"
        f"responses to direct messages."
        f"{_footer()}"
    )

def auto_reply_saved_text() -> str:
    return (
        f"{_header('Response Saved')}"
        f"Auto-reply message updated."
        f"{_footer()}"
    )

def auto_reply_text(enabled: bool, reply_text: str = "") -> str:
    status = "Enabled" if enabled else "Disabled"
    return (
        f"{_header('Auto Responder')}"
        f"┃ Status → {status}\n\n"
        f"Current Response:\n"
        f"<i>{reply_text or 'Not configured'}</i>"
        f"{_footer()}"
    )

def ads_started_text() -> str:
    return (
        f"{_header('Campaign Started')}"
        f"Broadcast campaign is now running.\n\n"
        f"┃ Status → Active\n"
        f"┃ Sharding → Enabled"
        f"{_footer()}"
    )

def ads_stopped_text() -> str:
    return (
        f"{_header('Campaign Halted')}"
        f"Broadcast campaign has been paused."
        f"{_footer()}"
    )

def ads_console_text(count: int) -> str:
    return (
        f"{_header('Ad Console')}"
        f"┃ Active → {count} / 3\n"
        f"┃ Logic → Random Rotation\n\n"
        f"Manage your ad creatives below:"
        f"{_footer()}"
    )

def set_interval_text() -> str:
    return (
        f"{_header('Campaign Delay')}"
        f"Enter the delay between cycles\n"
        f"in seconds (Min: {MIN_INTERVAL}s).\n\n"
        f"┃ <i>Waiting for input...</i>"
        f"{_footer()}"
    )

def interval_saved_text(seconds: int) -> str:
    return (
        f"{_header('Schedule Saved')}"
        f"Campaign delay updated to:\n"
        f"<b>{seconds // 60} minutes</b> ({seconds}s)"
        f"{_footer()}"
    )

def force_join_text() -> str:
    return (
        f"{_header('Access Denied')}"
        f"Membership is required to use\n"
        f"the Kurup Ads Campaign suite.\n\n"
        f"↳ <i>Verify membership to unlock.</i>"
        f"{_footer()}"
    )

def how_to_use_text() -> str:
    return (
        f"{_header('System Guide')}"
        f"1. Accounts\n"
        f"┃ Connect Telegram accounts.\n\n"
        f"2. Groups\n"
        f"┃ Import target links.\n\n"
        f"3. Ads\n"
        f"┃ Configure ad creatives.\n\n"
        f"4. Campaign\n"
        f"┃ Start the engine."
        f"{_footer()}"
    )

def disclaimer_text() -> str:
    return (
        f"{_header('Terms')}"
        f"This system is for automated marketing.\n"
        f"Use responsibly within Telegram TOS.\n\n"
        f"↳ <i>User assumes all risk for accounts.</i>"
        f"{_footer()}"
    )

def powered_by_text() -> str:
    return (
        f"{_header('Credits')}"
        f"Developed by Kurup Teams\n"
        f"© 2026 Kurup Ads Elite"
        f"{_footer()}"
    )

def admin_panel_text(stats: dict) -> str:
    return (
        f"{_header('Admin Panel')}"
        f"User Metrics\n"
        f"┃ Total → {stats['total_users']}\n"
        f"┃ Running → {stats['running_users']}\n\n"
        f"Account Metrics\n"
        f"┃ Total → {stats['total_accounts']}\n"
        f"┃ Healthy → {stats['active_accounts']}\n\n"
        f"Global Performance\n"
        f"┃ Sent → {stats['global_sent']}\n"
        f"┃ Success → {stats['success_rate']}"
        f"{_footer()}"
    )
