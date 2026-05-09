"""
Premium Message templates — Kurup Ads Bot.

Redesigned for a senior, professional, and minimalist aesthetic.
Using structured headers, clean dividers, and high-quality unicode symbols.
"""

from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME, MIN_INTERVAL

# ═══════════════════════════════════════════════════════════════════════════════
#  UI CORE DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

def _header(title: str) -> str:
    return (
        f"<b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

def _footer() -> str:
    return (
        f"\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>KURUP ADS</b>  ·  SYSTEM CLOUD"
    )

def _stat_line(label: str, value: any, icon: str = "•") -> str:
    return f"{icon}  {label:<12} <code>{value}</code>\n"


# ═══════════════════════════════════════════════════════════════════════════════
#  TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

def welcome_text(first_name: str, last_name: str = "", user_id: int = 0, username: str = "") -> str:
    full_name = f"{first_name} {last_name}".strip()
    return (
        f"{_header('K U R U P  A D S  E N G I N E')}"
        f"Welcome, <b>{full_name}</b>\n\n"
        f"{_stat_line('Operator', user_id, '🆔')}"
        f"{_stat_line('Network', '@' + username if username else 'Global', '🌐')}"
        f"\n"
        f"Your professional broadcast automation\n"
        f"suite is active and ready.\n\n"
        f"➜ Encrypted Asset Hosting\n"
        f"➜ Parallel Sharding Engine\n"
        f"➜ Intelligent Error Recovery"
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
) -> str:
    status_icon = "🟢" if ads_status == "running" else "🔴"
    if night_paused:
        status_icon = "🌙"
        status_text = "NIGHT STANDBY"
    else:
        status_text = "OPERATIONAL" if ads_status == "running" else "IDLE"

    return (
        f"{_header('C O M M A N D  C E N T E R')}"
        f"<b>SYSTEM PERFORMANCE</b>\n"
        f"{_stat_line('Assets', f'{account_count} / {max_accounts}', '📱')}"
        f"{_stat_line('Targets', f'{group_count} Groups', '📂')}"
        f"{_stat_line('Creatives', 'Ready' if ad_set else 'Missing', '🎨')}"
        f"{_stat_line('Cycle', f'{interval // 60}m', '⏱')}"
        f"\n"
        f"<b>LIVE STATUS</b>\n"
        f"┊ Status    {status_icon} <b>{status_text}</b>\n"
        f"┊ Progress  <code>{active_in_cycle} active tasks</code>"
        f"{_footer()}"
    )


def accounts_list_text(accounts: list[dict]) -> str:
    text = f"{_header('A S S E T  M A N I F E S T')}"
    if not accounts:
        text += "<i>No hosted accounts linked.</i>\n"
    else:
        for i, acc in enumerate(accounts, 1):
            status = acc.get("status", "active")
            icon = "✅" if status == "active" else "⚠️" if status == "limited" else "❌"
            health = acc.get("health", 100)
            text += f" {icon}  {i}. <code>{acc['phone_masked']}</code>  ({health}%)\n"
            if acc.get("status_reason"):
                text += f"    └ <i>{acc['status_reason']}</i>\n"
    
    text += _footer()
    return text


def groups_text(total: int, active: int, disabled: int) -> str:
    return (
        f"{_header('T A R G E T  P O O L')}"
        f"{_stat_line('Total', total, '📊')}"
        f"{_stat_line('Active', active, '🟢')}"
        f"{_stat_line('Excluded', disabled, '🔴')}"
        f"\n"
        f"<i>Automated pruning and recovery logic\n"
        f"is active for all targets.</i>"
        f"{_footer()}"
    )


def analytics_text(total_sent: int, failed_count: int, last_sent: str = "Never") -> str:
    total = total_sent + failed_count
    rate = (total_sent / total * 100) if total > 0 else 0
    
    return (
        f"{_header('B R O A D C A S T  I N T E L')}"
        f"{_stat_line('Delivered', total_sent, '✅')}"
        f"{_stat_line('Failed', failed_count, '❌')}"
        f"{_stat_line('Success', f'{rate:.1f}%', '📈')}"
        f"{_stat_line('Last Send', last_sent, '⏰')}"
        f"{_footer()}"
    )


def error_text(msg: str) -> str:
    return (
        f"<b>SYSTEM EXCEPTION</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ <code>{msg}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )

def success_text(msg: str) -> str:
    return (
        f"<b>OPERATION SUCCESS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ {msg}\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )

def add_account_text() -> str:
    return (
        f"{_header('LINK ASSET')}"
        f"Provide the phone number for the\n"
        f"account you wish to host.\n\n"
        f"➜ Format: <code>+1234567890</code>\n"
        f"➜ Privacy: AES-256 Encrypted"
        f"{_footer()}"
    )

def otp_prompt_text() -> str:
    return (
        f"{_header('VERIFICATION')}"
        f"A login code has been issued to\n"
        f"your Telegram account.\n\n"
        f"Please input the code below.\n"
        f"┊ <i>Waiting for input...</i>"
        f"{_footer()}"
    )

def password_2fa_text() -> str:
    return (
        f"{_header('CLOUD PASSWORD')}"
        f"This account is 2FA protected.\n"
        f"Please input your password:\n\n"
        f"┊ 🔒 Session Encrypted"
        f"{_footer()}"
    )

def account_added_text(phone: str) -> str:
    return (
        f"{_header('SYNC COMPLETE')}"
        f"Asset <code>{phone}</code> linked.\n\n"
        f"┊ Status: <b>OPERATIONAL</b>\n"
        f"┊ Branding: <b>ENFORCED</b>"
        f"{_footer()}"
    )

def account_deleted_text(phone: str) -> str:
    return (
        f"{_header('ASSET PURGED')}"
        f"Account <code>{phone}</code> has been\n"
        f"disconnected from the system."
        f"{_footer()}"
    )

def delete_confirm_text(phone: str) -> str:
    return (
        f"{_header('CONFIRM REMOVAL')}"
        f"Are you sure you want to disconnect\n"
        f"account: <code>{phone}</code>?\n\n"
        f"⚠️ <b>This cannot be undone.</b>"
        f"{_footer()}"
    )

def max_accounts_text(limit: int) -> str:
    return (
        f"{_header('LIMIT REACHED')}"
        f"Your plan allows up to {limit} accounts.\n"
        f"Remove an existing asset to add more."
        f"{_footer()}"
    )

def add_groups_text() -> str:
    return (
        f"{_header('IMPORT TARGETS')}"
        f"Send group links or usernames.\n\n"
        f"➜ One link per line\n"
        f"➜ Folder links supported"
        f"{_footer()}"
    )

def groups_added_text(added: int, failed: int) -> str:
    return (
        f"{_header('IMPORT COMPLETE')}"
        f"┊ Added     <b>{added}</b>\n"
        f"┊ Failed    <b>{failed}</b>"
        f"{_footer()}"
    )

def no_groups_text() -> str:
    return (
        f"{_header('NO TARGETS')}"
        f"Target list is empty. Please\n"
        f"import groups to begin."
        f"{_footer()}"
    )

def groups_list_text(groups: list[dict]) -> str:
    text = f"{_header('TARGET MANIFEST')}"
    for i, g in enumerate(groups[:20], 1):
        status = "●" if g.get("status") == "active" else "○"
        text += f" {i}. {status} <code>{g['identifier']}</code>\n"
    if len(groups) > 20:
        text += f"\n<i>... and {len(groups)-20} more.</i>\n"
    text += _footer()
    return text

def no_accounts_text() -> str:
    return (
        f"{_header('NO ASSETS')}"
        f"No accounts linked. Please link\n"
        f"at least one account to start."
        f"{_footer()}"
    )

def account_detail_text(acc: dict) -> str:
    status = acc.get("status", "active").upper()
    health = acc.get("health", 100)
    success = acc.get("success_count", 0)
    failure = acc.get("failure_count", 0)
    
    return (
        f"{_header('ASSET ANALYTICS')}"
        f"{_stat_line('Account', acc['phone_masked'], '📱')}"
        f"{_stat_line('Status', status, '⚡️')}"
        f"{_stat_line('Health', f'{health}%', '🏥')}"
        f"\n"
        f"<b>PERFORMANCE</b>\n"
        f"┊ Delivered   {success}\n"
        f"┊ Exceptions  {failure}\n"
        f"\n"
        f"<i>Reason: {acc.get('status_reason', 'None')}</i>"
        f"{_footer()}"
    )

def set_auto_reply_prompt_text() -> str:
    return (
        f"{_header('AUTO RESPONDER')}"
        f"Send the message you want the\n"
        f"bot to send automatically when\n"
        f"someone messages your accounts."
        f"{_footer()}"
    )

def auto_reply_saved_text() -> str:
    return (
        f"{_header('RESPONSE SAVED')}"
        f"Your auto-reply message has been\n"
        f"successfully updated."
        f"{_footer()}"
    )

def auto_reply_text(enabled: bool, reply_text: str = "") -> str:
    status = "ENABLED" if enabled else "DISABLED"
    return (
        f"{_header('AUTO RESPONDER')}"
        f"┊ Status    <b>{status}</b>\n\n"
        f"<b>Current Response:</b>\n"
        f"<i>{reply_text or 'Not configured'}</i>"
        f"{_footer()}"
    )

def ads_started_text() -> str:
    return (
        f"{_header('ENGINE ACTIVATED')}"
        f"Broadcast cycle is now live.\n\n"
        f"┊ Status: <b>RUNNING</b>\n"
        f"┊ Sharding: <b>ENABLED</b>"
        f"{_footer()}"
    )

def ads_stopped_text() -> str:
    return (
        f"{_header('ENGINE HALTED')}"
        f"Broadcast cycle has been\n"
        f"successfully terminated."
        f"{_footer()}"
    )

def ads_console_text(count: int) -> str:
    return (
        f"{_header('CREATIVE CONSOLE')}"
        f"┊ Active    <b>{count} / 3</b>\n"
        f"┊ Rotation  <b>Random Shard</b>\n\n"
        f"Manage your broadcast creatives below:"
        f"{_footer()}"
    )

def set_interval_text() -> str:
    return (
        f"{_header('CYCLE SCHEDULE')}"
        f"Enter the delay between cycles\n"
        f"in seconds (Minimum: {MIN_INTERVAL}s).\n\n"
        f"┊ <i>Waiting for input...</i>"
        f"{_footer()}"
    )

def interval_saved_text(seconds: int) -> str:
    return (
        f"{_header('SCHEDULE SAVED')}"
        f"Broadcast interval updated to:\n"
        f"<b>{seconds // 60} minutes</b> ({seconds}s)"
        f"{_footer()}"
    )

def force_join_text() -> str:
    return (
        f"{_header('ACCESS RESTRICTED')}"
        f"To utilize the Kurup Ads Engine,\n"
        f"you must be a member of our\n"
        f"official network channels.\n\n"
        f"┊ <i>Verify membership to unlock.</i>"
        f"{_footer()}"
    )

def how_to_use_text() -> str:
    return (
        f"{_header('SYSTEM GUIDE')}"
        f"<b>1. Link Asset</b>\n"
        f"Connect your Telegram account(s)\n"
        f"via the Command Center.\n\n"
        f"<b>2. Define Targets</b>\n"
        f"Import group/channel links where\n"
        f"your ads will be delivered.\n\n"
        f"<b>3. Set Creative</b>\n"
        f"Configure your ad text or media.\n\n"
        f"<b>4. Go Live</b>\n"
        f"Start the broadcast engine."
        f"{_footer()}"
    )

def disclaimer_text() -> str:
    return (
        f"{_header('TERMS OF SERVICE')}"
        f"This system is for automated\n"
        f"marketing purposes. Use it\n"
        f"responsibly within Telegram's\n"
        f"Terms of Service.\n\n"
        f"⚠️ <b>We are not responsible for\n"
        f"account bans or restrictions.</b>"
        f"{_footer()}"
    )

def powered_by_text() -> str:
    return (
        f"{_header('ENGINE CREDITS')}"
        f"Developed by <b>Kurup Teams</b>\n"
        f"Architecture: <i>Senior Backend</i>\n\n"
        f"© 2026 Kurup Ads Elite"
        f"{_footer()}"
    )

def admin_panel_text(stats: dict) -> str:
    return (
        f"{_header('ADMINISTRATOR CONSOLE')}"
        f"<b>USER METRICS</b>\n"
        f"{_stat_line('Total Users', stats['total_users'], '👥')}"
        f"{_stat_line('Running', stats['running_users'], '🟢')}"
        f"\n"
        f"<b>ASSET METRICS</b>\n"
        f"{_stat_line('Total Accs', stats['total_accounts'], '📱')}"
        f"{_stat_line('Healthy', stats['active_accounts'], '✅')}"
        f"{_stat_line('Errors', stats['error_accounts'], '❌')}"
        f"\n"
        f"<b>TARGET METRICS</b>\n"
        f"{_stat_line('Groups Pool', stats['total_groups'], '📂')}"
        f"\n"
        f"<b>PERFORMANCE</b>\n"
        f"{_stat_line('Global Sent', stats['global_sent'], '📤')}"
        f"{_stat_line('Success Rate', stats['success_rate'], '📈')}"
        f"{_footer()}"
    )
