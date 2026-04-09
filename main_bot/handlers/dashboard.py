"""
Dashboard handler for Main Bot.
"""

import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from models.user import (
    get_user_config, update_user_config, is_user_branded, 
    get_user_profile_data
)
from models.group import get_user_groups, get_group_count
from models.session import get_all_user_sessions
from models.stats import get_account_stats
from main_bot.utils.keyboards import (
    get_dashboard_keyboard, get_add_account_keyboard,
    get_manage_settings_keyboard
)
from core.config import (
    MIN_INTERVAL_MINUTES, BRANDING_NAME, BRANDING_BIO, OWNER_ID
)
from core.utils import escape_markdown

# Conversation states
WAITING_INTERVAL = 11
WAITING_RESPONDER_TEXT = 12


def format_last_active(dt: datetime.datetime) -> str:
    """Format datetime as relative 'N m/h/d ago'."""
    if not dt:
        return "Never"
    
    now = datetime.datetime.utcnow()
    diff = now - dt
    
    if diff.total_seconds() < 60:
        return "Just now"
    if diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() // 60)}m ago"
    if diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() // 3600)}h ago"
    
    return f"{diff.days}d ago"


async def get_group_status_summary(user_id: int) -> str:
    """Consise summary of group health: 🟢 5 Active ▪ 🔴 2 Paused"""
    groups = await get_user_groups(user_id)
    if not groups:
        return "No groups found"
    
    active = len([g for g in groups if g.get("enabled", True)])
    paused = len(groups) - active
    
    parts = []
    if active > 0:
        parts.append(f"🟢 {active} Active")
    if paused > 0:
        parts.append(f"🔴 {paused} Paused")
        
    return " ▪ ".join(parts)


def format_expiry_date(dt: datetime.datetime) -> str:
    """Format expiry date as a readable string."""
    if not dt:
        return "N/A"
    return dt.strftime("%d %b %Y, %I:%M %p")


async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the main dashboard."""
    user_id = update.effective_user.id
    user_name = escape_markdown(update.effective_user.first_name or "User")
    
    # Get user data
    sessions = await get_all_user_sessions(user_id)
    config = await get_user_config(user_id)
    group_count = await get_group_count(user_id)
    
    # ═══ Build account section ═══
    account_section = ""
    total_sends = 0
    if sessions:
        for idx, s in enumerate(sessions, 1):
            status_icon = "🟢" if s.get("connected") else "🔴"
            phone = s.get("phone", "Unknown")
            stats = await get_account_stats(user_id, phone)
            
            last_active = format_last_active(stats["last_active"])
            rate = stats["success_rate"]
            sends = stats.get("total_sent", 0)
            total_sends += sends
            
            escaped_phone = escape_markdown(phone)
            account_section += f"  {status_icon} `{escaped_phone}`\n"
            account_section += f"     ├─ 📊 Sent: {sends} ▪ Rate: {rate}%\n"
            account_section += f"     └─ ⏱️ Active: {last_active}\n"
    else:
        account_section = "  ○ No accounts connected\n  └─ Tap *Add Account* below"
    
    # ═══ Plan badge ═══
    plan_status = "🆓 FREE EDITION"
    plan_line2 = "     └─ ✅ Active — Network Branded"
    
    # ═══ Forwarding status ═══
    has_connected = any(s.get("connected") for s in sessions) if sessions else False
    if has_connected and group_count > 0:
        fwd_status = "🟢 *ACTIVE*"
    elif has_connected and group_count == 0:
        fwd_status = "🟡 *NO GROUPS*"
    elif not has_connected:
        fwd_status = "🔴 *NO ACCOUNT*"
    else:
        fwd_status = "🔴 *PAUSED*"
    
    interval = config.get("interval_min", MIN_INTERVAL_MINUTES)
    
    # ═══ Settings section ═══
    is_branded = await is_user_branded(user_id)
    branding_status = "🟢 ACTIVE" if is_branded else "🔴 MISSING"
    
    copy_icon = "🟢" if config.get("copy_mode") else "⚫"
    shuffle_icon = "🟢" if config.get("shuffle_mode") else "⚫"
    responder_icon = "🟢" if config.get("auto_reply_enabled") else "⚫"
        
    send_mode = config.get("send_mode", "sequential").title()
    reply_text = config.get("auto_reply_text", "")
    reply_preview = escape_markdown(reply_text[:25] + "..." if len(reply_text) > 25 else reply_text)
    if not is_branded:
        reply_preview = "Locked"
    
    dashboard_text = f"""
📊 *DASHBOARD* — {user_name}

📱 *ACCOUNTS* ({len(sessions) if sessions else 0})
{account_section}

📤 *FORWARDING:* {fwd_status}
  ➤ Groups: {group_count} ▪ Total Sent: {total_sends}
  ➤ Health: {await get_group_status_summary(user_id)}
  ➤ Interval: {interval}m

🏷️ *BRANDING:* {branding_status}
  └─ _Powered by @KurupAdsBot (Free Edition)_

⚙️ *SETTINGS*
  {copy_icon} Copy Mode ▪ {shuffle_icon} Shuffle
  🔄 Send Mode: {send_mode}
  {responder_icon} Responder: _{reply_preview}_


"""
    
    kb = get_dashboard_keyboard(
        is_active=config.get("is_active", True),
        include_add=(not sessions)
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(dashboard_text, parse_mode="Markdown", reply_markup=kb)
    else:
        await update.message.reply_text(dashboard_text, parse_mode="Markdown", reply_markup=kb)


async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_dashboard(update, context)


async def start_ads_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await update_user_config(user_id, is_active=True)
    await query.answer("▶️ Ad Campaign STARTED", show_alert=True)
    await show_dashboard(update, context)


async def stop_ads_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await update_user_config(user_id, is_active=False)
    await query.answer("⏸ Ad Campaign STOPPED", show_alert=True)
    await show_dashboard(update, context)


async def add_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = """
🔗 *CONNECT YOUR ACCOUNT*

Securely link your Telegram account
to start auto-forwarding messages.

✅ 256-bit encrypted session
✅ Your API credentials only
✅ Disconnect anytime

👇 *Tap below to continue to Login Bot*
"""
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_add_account_keyboard())


async def toggle_send_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    # Features are now UNLOCKED for everyone (Enforced branding)
    config = await get_user_config(user_id)
    modes = ["sequential", "rotate", "random"]
    current = config.get("send_mode", "sequential")
    next_mode = modes[(modes.index(current) + 1) % len(modes)]
    await update_user_config(user_id, send_mode=next_mode)
    await query.answer(f"✅ Send mode: {next_mode.title()}")
    await manage_settings_callback(update, context)


async def manage_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    config = await get_user_config(user_id)
    interval = config.get("interval_min", MIN_INTERVAL_MINUTES)
    send_mode = config.get("send_mode", "sequential").title()
    text = f"""
🛠️ *USER SETTINGS*
══════════════════════════════

⏱️ *Interval:* {interval} minutes (Wait after cycle)
🔄 *Group Gap:* 3.5 minutes (Pre-set)
🤖 *Auto-Responder:* {"Enabled ✅" if config.get("auto_reply_enabled") else "Disabled ⚫"}

_Toggle or update your preferences below._
"""
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_manage_settings_keyboard(config, is_branded=await is_user_branded(user_id)))


async def user_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    try:
        data = await get_user_profile_data(user_id)
        sessions = data.get('sessions', [])
        user_doc = data.get('user') or {}
        created_at = user_doc.get('created_at')
        member_since = created_at.strftime('%Y-%m-%d') if created_at else 'N/A'
        
        sent_24h = data.get('sent_24h', 0)
        rate_24h = data.get('success_rate_24h', 100)
        total_sent = data.get('total_sent', 0)
        active_groups = data.get('active_groups', 0)
        total_groups = data.get('total_groups', 0)

        text = f"""
📊 *MY STATISTICS — KURUP ADS*
══════════════════════════════

🚀 *PERFORMANCE (24H)*
📤 *Sent (24h):* {sent_24h}
🎯 *Success Rate:* {rate_24h}%

📈 *LIFETIME*
📤 *Total Sent:* {total_sent}
📅 *Member Since:* {member_since}

👥 *GROUPS*
✅ *Active:* {active_groups}
📁 *Total Joined:* {total_groups}
📱 *Linked Accounts:* {len(sessions)}
"""
    except Exception as e:
        text = f"❌ Could not load stats: {e}"
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_dashboard_keyboard())


async def toggle_shuffle_ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if not await is_user_branded(user_id):
        await query.answer("🔒 Feature locked.", show_alert=True)
        return
    config = await get_user_config(user_id)
    new_val = not config.get("shuffle_mode", False)
    await update_user_config(user_id, shuffle_mode=new_val)
    await query.answer(f"Shuffle {'Enabled' if new_val else 'Disabled'}")
    await manage_settings_callback(update, context)


async def toggle_copy_ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    # Features are now UNLOCKED
    config = await get_user_config(user_id)
    new_val = not config.get("copy_mode", False)
    await update_user_config(user_id, copy_mode=new_val)
    await query.answer(f"Copy Mode {'Enabled' if new_val else 'Disabled'}")
    await manage_settings_callback(update, context)


async def toggle_responder_ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    # Features are now UNLOCKED
    config = await get_user_config(user_id)
    new_val = not config.get("auto_reply_enabled", False)
    await update_user_config(user_id, auto_reply_enabled=new_val)
    await query.answer(f"Responder {'Enabled' if new_val else 'Disabled'}")
    await manage_settings_callback(update, context)


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


async def set_interval_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"⏱️ *SET INTERVAL*\n\nPlease send the interval in minutes (Min: {MIN_INTERVAL_MINUTES}).", parse_mode="Markdown")
    return WAITING_INTERVAL


async def receive_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        val = int(update.message.text)
        if val < MIN_INTERVAL_MINUTES:
            await update.message.reply_text(f"⚠️ Minimum interval is {MIN_INTERVAL_MINUTES} minutes.")
            return WAITING_INTERVAL
        await update_user_config(user_id, interval_min=val)
        await update.message.reply_text(f"✅ Interval set to {val} minutes.", reply_markup=get_dashboard_keyboard())
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Please send a valid number.")
        return WAITING_INTERVAL


async def set_responder_text_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    # Features are now UNLOCKED
    await query.answer()
    await query.edit_message_text("🤖 *SET RESPONDER TEXT*\n\nPlease send the message you want the bot to reply with.", parse_mode="Markdown")
    return WAITING_RESPONDER_TEXT


async def receive_responder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update_user_config(user_id, auto_reply_text=update.message.text)
    await update.message.reply_text("✅ Responder text updated.", reply_markup=get_dashboard_keyboard())
    return ConversationHandler.END
