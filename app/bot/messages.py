"""
Professional Message Templates — Group Broadcaster.
Clean, minimal, business-grade aesthetic.
"""

from app.config import BOT_USERNAME, SUPPORT_USERNAME, CHANNEL_USERNAME


# ━━━━━━━━━━━━━━━━━━━━
#  UI DESIGN SYSTEM
# ━━━━━━━━━━━━━━━━━━━━

def _header(title: str) -> str:
    return (
        f"<b>{title.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
    )

def _footer() -> str:
    return (
        f"\n━━━━━━━━━━━━━━━━━━\n"
        f"<b>GROUP BROADCASTER</b>"
    )

def _stat(label: str, value) -> str:
    return f"🔹 {label:<12} → <code>{value}</code>\n"


# ━━━━━━━━━━━━━━━━━━━━
#  WELCOME & NAVIGATION
# ━━━━━━━━━━━━━━━━━━━━

def welcome_text(first_name: str, last_name: str = "", user_id: int = 0, username: str = "") -> str:
    full_name = f"{first_name} {last_name}".strip()
    return (
        f"{_header('Welcome')}"
        f"Hello <b>{full_name}</b>,\n\n"
        f"{_stat('User ID', user_id)}"
        f"{_stat('Access', '@' + username if username else 'Global')}"
        f"\n"
        f"▸ Send messages to multiple groups\n"
        f"▸ Smart delay & batch algorithm\n"
        f"▸ Fully automated broadcasting\n\n"
        f"↳ <i>Tap Dashboard to get started.</i>"
        f"{_footer()}"
    )


def force_join_text() -> str:
    return (
        f"{_header('Access Required')}"
        f"Please join our channels to\n"
        f"use the Group Broadcaster.\n\n"
        f"↳ <i>Verify membership to unlock.</i>"
        f"{_footer()}"
    )


def how_to_use_text() -> str:
    return (
        f"{_header('How to Use')}"
        f"<b>Step 1:</b> Connect Account\n"
        f"┊ Link your Telegram account.\n\n"
        f"<b>Step 2:</b> Set Message\n"
        f"┊ Send text, photo, or video.\n\n"
        f"<b>Step 3:</b> Add Groups\n"
        f"┊ Paste group links (one per line).\n\n"
        f"<b>Step 4:</b> Start Broadcasting\n"
        f"┊ The bot sends automatically!\n\n"
        f"↳ <i>The bot uses smart delays to\n"
        f"   keep your account safe.</i>"
        f"{_footer()}"
    )


def disclaimer_text() -> str:
    return (
        f"{_header('Disclaimer')}"
        f"This bot automates message sending.\n"
        f"Use responsibly within Telegram TOS.\n\n"
        f"↳ <i>User assumes all responsibility.</i>"
        f"{_footer()}"
    )


def powered_by_text() -> str:
    return (
        f"{_header('Credits')}"
        f"Developed by Kurup Teams\n"
        f"© 2026 Group Broadcaster"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━
#  DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━

def dashboard_text(
    has_account: bool,
    has_message: bool,
    group_count: int,
    total_sent: int,
    total_failed: int,
    is_broadcasting: bool,
    interval: int,
    phone_masked: str = None,
) -> str:
    status = "🟢 Broadcasting" if is_broadcasting else "⏸ Idle"
    account_status = f"{phone_masked}" if has_account else "Not Connected"
    message_status = "Ready" if has_message else "Not Set"

    total = total_sent + total_failed
    rate = f"{(total_sent / total * 100):.1f}%" if total > 0 else "N/A"

    return (
        f"📊 <b>DASHBOARD</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{_stat('Status', status)}"
        f"{_stat('Account', account_status)}"
        f"{_stat('Message', message_status)}"
        f"{_stat('Groups', f'{group_count}')}"
        f"{_stat('Interval', f'{interval // 60} min')}"
        f"\n"
        f"📊 <b>Statistics</b>\n"
        f"{_stat('Sent', f'{total_sent:,}')}"
        f"{_stat('Failed', f'{total_failed:,}')}"
        f"{_stat('Success', rate)}"
        f"\n"
        f"{'↳ <i>Broadcasting is active!</i>' if is_broadcasting else '↳ <i>Set up and start broadcasting.</i>'}"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━
#  ACCOUNT
# ━━━━━━━━━━━━━━━━━━━━

def connect_account_text() -> str:
    return (
        f"{_header('Connect Account')}"
        f"Send your phone number with\n"
        f"country code to connect.\n\n"
        f"▸ Format: <code>+1234567890</code>\n"
        f"↳ <i>Your session is encrypted.</i>"
        f"{_footer()}"
    )


def otp_prompt_text() -> str:
    return (
        f"{_header('Verification')}"
        f"Enter the Telegram login code.\n\n"
        f"┊ <i>Waiting for input...</i>"
        f"{_footer()}"
    )


def password_2fa_text() -> str:
    return (
        f"{_header('2FA Password')}"
        f"Your account has 2FA enabled.\n"
        f"Please enter your password:\n\n"
        f"↳ <i>Secure session</i>"
        f"{_footer()}"
    )


def account_connected_text(phone: str) -> str:
    return (
        f"{_header('Account Connected')}"
        f"Account <code>{phone}</code> linked.\n\n"
        f"┊ Status → Active\n"
        f"↳ <i>Ready for broadcasting.</i>"
        f"{_footer()}"
    )


def account_disconnected_text(phone: str) -> str:
    return (
        f"{_header('Account Removed')}"
        f"Account <code>{phone}</code> disconnected."
        f"{_footer()}"
    )


def account_info_text(phone: str) -> str:
    return (
        f"{_header('Connected Account')}"
        f"{_stat('Phone', phone)}"
        f"{_stat('Status', 'Active')}"
        f"\n"
        f"↳ <i>This account is used for\n"
        f"   sending messages to groups.</i>"
        f"{_footer()}"
    )


def no_account_text() -> str:
    return (
        f"{_header('No Account')}"
        f"No account connected.\n"
        f"Please connect your Telegram\n"
        f"account to start broadcasting."
        f"{_footer()}"
    )


def confirm_disconnect_text(phone: str) -> str:
    return (
        f"{_header('Confirm Disconnect')}"
        f"Remove account <code>{phone}</code>?\n\n"
        f"↳ <i>Broadcasting will stop.</i>"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━
#  MESSAGE
# ━━━━━━━━━━━━━━━━━━━━

def set_message_prompt_text() -> str:
    return (
        f"{_header('Set Message')}"
        f"Send the message you want to\n"
        f"broadcast to all groups.\n\n"
        f"▸ Text message\n"
        f"▸ Photo with caption\n"
        f"▸ Video with caption\n\n"
        f"↳ <i>Send your content now...</i>"
        f"{_footer()}"
    )


def message_saved_text() -> str:
    return (
        f"{_header('Message Saved')}"
        f"Your broadcast message has been\n"
        f"saved and is ready to send.\n\n"
        f"↳ <i>Start broadcasting anytime.</i>"
        f"{_footer()}"
    )


def message_cleared_text() -> str:
    return (
        f"{_header('Message Cleared')}"
        f"Broadcast message has been removed."
        f"{_footer()}"
    )


def message_preview_text(msg: dict) -> str:
    text = msg.get("text") or ""
    media = msg.get("media_type") or "None"
    preview = text[:100] + "..." if len(text) > 100 else text

    return (
        f"{_header('Message Preview')}"
        f"{_stat('Media', media.title() if media != 'None' else 'Text Only')}"
        f"\n"
        f"<b>Content:</b>\n"
        f"{preview or '<i>No text</i>'}"
        f"{_footer()}"
    )


def no_message_text() -> str:
    return (
        f"{_header('No Message')}"
        f"No broadcast message set.\n"
        f"Please set a message first."
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━
#  GROUPS
# ━━━━━━━━━━━━━━━━━━━━

def groups_text(count: int) -> str:
    return (
        f"{_header('My Groups')}"
        f"{_stat('Total Groups', count)}"
        f"\n"
        f"↳ <i>Manage your broadcast targets.</i>"
        f"{_footer()}"
    )


def add_groups_prompt_text() -> str:
    return (
        f"{_header('Add Groups')}"
        f"Send group links or usernames.\n\n"
        f"▸ One link per line\n"
        f"▸ Supports @username format\n"
        f"▸ Supports t.me/... links\n"
        f"▸ Supports invite links\n\n"
        f"↳ <i>Paste your links now...</i>"
        f"{_footer()}"
    )


def groups_added_text(added: int, total: int) -> str:
    return (
        f"{_header('Groups Imported')}"
        f"{_stat('Added', added)}"
        f"{_stat('Total', total)}"
        f"{_footer()}"
    )


def no_groups_text() -> str:
    return (
        f"{_header('No Groups')}"
        f"No groups added yet.\n"
        f"Add groups to start broadcasting."
        f"{_footer()}"
    )


def groups_list_text(groups: list[str]) -> str:
    text = f"{_header('Group List')}"
    for i, g in enumerate(groups[:30], 1):
        # Shorten long links
        display = g if len(g) <= 35 else g[:32] + "..."
        text += f"{i}. <code>{display}</code>\n"
    if len(groups) > 30:
        text += f"\n↳ <i>+ {len(groups) - 30} more groups.</i>\n"
    text += f"\n{_stat('Total', len(groups))}"
    text += _footer()
    return text


def groups_cleared_text(count: int) -> str:
    return (
        f"{_header('Groups Cleared')}"
        f"Removed <b>{count}</b> groups."
        f"{_footer()}"
    )


def confirm_clear_groups_text() -> str:
    return (
        f"{_header('Confirm Clear')}"
        f"This will remove ALL your groups.\n"
        f"Are you sure?"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━
#  BROADCAST
# ━━━━━━━━━━━━━━━━━━━━

def broadcast_started_text() -> str:
    return (
        f"{_header('Broadcasting Started')}"
        f"Messages are being sent to your\n"
        f"groups automatically.\n\n"
        f"┊ Algorithm → Smart Batching\n"
        f"┊ Delays → Randomized\n"
        f"┊ Protection → Active\n\n"
        f"↳ <i>Check dashboard for live stats.</i>"
        f"{_footer()}"
    )


def broadcast_stopped_text() -> str:
    return (
        f"{_header('Broadcasting Stopped')}"
        f"Broadcast has been paused."
        f"{_footer()}"
    )


def broadcast_progress_text(sent: int, failed: int, skipped: int, total: int) -> str:
    remaining = total - (sent + failed + skipped)
    return (
        f"📡 <b>BROADCAST RUNNING</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"⏭ Skipped: {skipped}\n"
        f"🎯 Total: {total}\n"
        f"⏳ Remaining: {remaining}\n"
    )


def set_interval_prompt_text(min_interval: int) -> str:
    return (
        f"{_header('Set Interval')}"
        f"Enter the delay between broadcast\n"
        f"cycles in seconds.\n\n"
        f"┊ Minimum: {min_interval}s ({min_interval // 60} min)\n\n"
        f"↳ <i>Waiting for input...</i>"
        f"{_footer()}"
    )


def interval_saved_text(seconds: int) -> str:
    return (
        f"{_header('Interval Saved')}"
        f"Cycle delay updated to:\n"
        f"<b>{seconds // 60} minutes</b> ({seconds}s)"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━
#  GENERIC
# ━━━━━━━━━━━━━━━━━━━━

def error_text(msg: str) -> str:
    return (
        f"❌ <b>ERROR</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ {msg}\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )


def success_text(msg: str) -> str:
    return (
        f"✅ <b>SUCCESS</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ {msg}\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )


# ━━━━━━━━━━━━━━━━━━━━
#  ADMIN
# ━━━━━━━━━━━━━━━━━━━━

def admin_panel_text(stats: dict) -> str:
    return (
        f"{_header('Admin Panel')}"
        f"<b>Users</b>\n"
        f"┊ Total        → {stats['total_users']}\n"
        f"┊ Broadcasting → {stats['broadcasting']}\n\n"
        f"<b>Global Stats</b>\n"
        f"┊ Sent     → {stats['total_sent']:,}\n"
        f"┊ Failed   → {stats['total_failed']:,}\n"
        f"┊ Success  → {stats['success_rate']}\n"
        f"{_footer()}"
    )


# ━━━━━━━━━━━━━━━━━━━━
#  ADVANCED & PREMIUM
# ━━━━━━━━━━━━━━━━━━━━

def saved_messages_success_text() -> str:
    return (
        f"{_header('Saved Messages')}"
        f"Your broadcast message was successfully\n"
        f"sent to your Telegram Saved Messages!\n\n"
        f"↳ <i>Check your Saved Messages chat to verify.</i>"
        f"{_footer()}"
    )


def saved_messages_error_text(err: str) -> str:
    return (
        f"{_header('Saved Messages Error')}"
        f"Failed to send message to Saved Messages:\n"
        f"<code>{err}</code>\n\n"
        f"↳ <i>Please check your account connection.</i>"
        f"{_footer()}"
    )


def health_monitor_text(score: int, status: str, details: str) -> str:
    return (
        f"{_header('Health Monitor')}"
        f"{_stat('Health Score', f'{score}%')}"
        f"{_stat('Status', status)}"
        f"\n"
        f"<b>Diagnostic Details:</b>\n"
        f"{details}\n\n"
        f"↳ <i>Real-time account health evaluation.</i>"
        f"{_footer()}"
    )


def auto_responder_text(enabled: bool, message: str) -> str:
    status = "🟢 Enabled" if enabled else "🔴 Disabled"
    preview = message[:100] + "..." if len(message) > 100 else message
    return (
        f"{_header('Auto Responder')}"
        f"{_stat('Status', status)}"
        f"\n"
        f"<b>Current Reply Message:</b>\n"
        f"<code>{preview}</code>\n\n"
        f"↳ <i>Automatically replies to incoming private\n"
        f"   messages while broadcasting is active.</i>"
        f"{_footer()}"
    )


def auto_responder_prompt_text() -> str:
    return (
        f"{_header('Set Auto Responder')}"
        f"Send the text message you want the bot\n"
        f"to reply with when someone PMs you.\n\n"
        f"↳ <i>Waiting for your message input...</i>"
        f"{_footer()}"
    )


def auto_responder_saved_text() -> str:
    return (
        f"{_header('Auto Responder Saved')}"
        f"Your auto-responder message has been saved."
        f"{_footer()}"
    )


def live_stats_text(user: dict, live_count: int, paused_count: int) -> str:
    total_sent = user.get("total_sent", 0)
    total_failed = user.get("total_failed", 0)
    total = total_sent + total_failed
    rate = f"{(total_sent / total * 100):.1f}%" if total > 0 else "N/A"
    health = user.get("health_status", "Not Checked")
    premium = "💎 Premium" if user.get("is_premium") else "🆓 Free Plan"

    return (
        f"📊 <b>LIVE ACCOUNT STATS</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{_stat('Account Tier', premium)}"
        f"{_stat('Health Status', health)}"
        f"{_stat('Live Groups', live_count)}"
        f"{_stat('Paused Groups', paused_count)}"
        f"\n"
        f"📈 <b>Performance Metrics</b>\n"
        f"{_stat('Total Sent', f'{total_sent:,}')}"
        f"{_stat('Total Failed', f'{total_failed:,}')}"
        f"{_stat('Success Rate', rate)}"
        f"\n"
        f"↳ <i>Real-time individual user telemetry.</i>"
        f"{_footer()}"
    )


def premium_info_text(is_premium: bool) -> str:
    status = "💎 Active (Premium)" if is_premium else "🆓 Free Plan"
    return (
        f"{_header('Premium Membership')}"
        f"{_stat('Plan Status', status)}"
        f"{_stat('Monthly Price', '499/- INR')}"
        f"\n"
        f"✨ <b>Premium Benefits:</b>\n"
        f"• Remove enforced profile bio\n"
        f"• Remove enforced last name suffix\n"
        f"• Priority broadcasting protection\n\n"
        f"{'↳ <i>You are a Premium Member! Enjoy full branding freedom.</i>' if is_premium else '↳ <i>To upgrade to Premium, please contact the Owner/Admin with your User ID.</i>'}"
        f"{_footer()}"
    )


def live_groups_text(groups: list[str]) -> str:
    text = f"{_header('Live Groups')}"
    for i, g in enumerate(groups[:30], 1):
        display = g if len(g) <= 35 else g[:32] + "..."
        text += f"{i}. <code>{display}</code>\n"
    if len(groups) > 30:
        text += f"\n↳ <i>+ {len(groups) - 30} more live groups.</i>\n"
    if not groups:
        text += "<i>No live groups found.</i>\n"
    text += f"\n{_stat('Total Live', len(groups))}"
    text += _footer()
    return text


def paused_groups_text(groups: list[str]) -> str:
    text = f"{_header('Paused Groups')}"
    for i, g in enumerate(groups[:30], 1):
        display = g if len(g) <= 35 else g[:32] + "..."
        text += f"{i}. <code>{display}</code>\n"
    if len(groups) > 30:
        text += f"\n↳ <i>+ {len(groups) - 30} more paused groups.</i>\n"
    if not groups:
        text += "<i>No paused groups found.</i>\n"
    text += f"\n{_stat('Total Paused', len(groups))}"
    text += _footer()
    return text


def admin_premium_prompt_text() -> str:
    return (
        f"{_header('Manage Premium')}"
        f"Enter the Telegram User ID of the user\n"
        f"you want to upgrade or downgrade.\n\n"
        f"↳ <i>Waiting for User ID input...</i>"
        f"{_footer()}"
    )


def admin_premium_user_text(user: dict) -> str:
    user_id = user.get("telegram_user_id")
    username = user.get("username", "None")
    is_premium = user.get("is_premium", False)
    status = "💎 Premium" if is_premium else "🆓 Free Plan"
    return (
        f"{_header('User Premium Status')}"
        f"{_stat('User ID', user_id)}"
        f"{_stat('Username', f'@{username}')}"
        f"{_stat('Current Tier', status)}"
        f"\n"
        f"↳ <i>Select an action below:</i>"
        f"{_footer()}"
    )


def admin_all_users_stats_text(users: list[dict]) -> str:
    text = f"{_header('All Users Telemetry')}"
    for u in users[:20]:
        uid = u.get("telegram_user_id")
        phone = u.get("phone_masked") or u.get("username") or "Unlinked"
        sent = u.get("total_sent", 0)
        failed = u.get("total_failed", 0)
        health = u.get("health_status", "N/A").split(" ")[0]
        prem = "💎" if u.get("is_premium") else "🆓"
        text += f"• <code>{uid}</code> ({phone}) | {prem} | {health} | S:{sent} F:{failed}\n"
    
    if len(users) > 20:
        text += f"\n↳ <i>+ {len(users) - 20} more users.</i>\n"
    text += f"\n{_stat('Total Users', len(users))}"
    text += _footer()
    return text
