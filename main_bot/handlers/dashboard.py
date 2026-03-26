"""
Dashboard handler for Main Bot.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from models.user import (
    get_user_config, update_user_config, is_user_branded, 
    get_user_profile_data, get_all_users
)
from models.plan import get_plan
from models.group import get_user_groups, add_group, remove_group, get_group_count
from models.session import get_all_user_sessions
from models.stats import get_account_stats
from core.database import get_database
from main_bot.utils.keyboards import (
    get_dashboard_keyboard, get_add_account_keyboard,
    get_manage_groups_keyboard, get_manage_settings_keyboard
)
from core.config import (
    MIN_INTERVAL_MINUTES, MAX_GROUPS_PER_USER,
    BRANDING_NAME, BRANDING_BIO
)
from shared.utils import escape_markdown

# Conversation states
WAITING_GROUP_URL = 10
WAITING_INTERVAL = 11
WAITING_RESPONDER_TEXT = 12
import datetime
# Group stats moved to models.group


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
    plan = await get_plan(user_id)
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
    if plan:
        if plan.get("status") == "active":
            plan_type = plan.get("plan_type", "trial").title()
            days_left = (plan["expires_at"] - datetime.datetime.utcnow()).days
            hours_left = ((plan["expires_at"] - datetime.datetime.utcnow()).seconds // 3600)
            expiry_date = format_expiry_date(plan["expires_at"])
            
            if plan_type.lower() == "trial":
                plan_badge = "🏅 TRIAL"
            else:
                plan_badge = "💎 PREMIUM"
            
            if days_left > 0:
                plan_status = f"{plan_badge} ▪ {days_left}d {hours_left}h left"
            else:
                plan_status = f"{plan_badge} ▪ {hours_left}h left"
            
            plan_line2 = f"     └─ 📅 Expires: {expiry_date}"
        else:
            plan_status = "🔴 EXPIRED"
            plan_line2 = "     └─ Redeem a code to reactivate!"
    else:
        plan_status = "⚪ NO PLAN"
        plan_line2 = "     └─ Connect an account for *7 days FREE!*"
    
    # ═══ Forwarding status ═══
    has_connected = any(s.get("connected") for s in sessions) if sessions else False
    if has_connected and group_count > 0 and plan and plan.get("status") == "active":
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
    
    if is_branded:
        copy_icon = "🟢" if config.get("copy_mode") else "⚫"
        shuffle_icon = "🟢" if config.get("shuffle_mode") else "⚫"
        responder_icon = "🟢" if config.get("auto_reply_enabled") else "⚫"
    else:
        copy_icon = "🔒"
        shuffle_icon = "🔒"
        responder_icon = "🔒"
        
    send_mode = config.get("send_mode", "sequential").title()
    reply_text = config.get("auto_reply_text", "")
    reply_preview = escape_markdown(reply_text[:25] + "..." if len(reply_text) > 25 else reply_text)
    if not is_branded:
        reply_preview = "Locked"
    
    dashboard_text = f"""
📊 *DASHBOARD* — {user_name}

📱 *ACCOUNTS* ({len(sessions) if sessions else 0})
{account_section}

🏷️ *SUBSCRIPTION*
  ➤ {plan_status}
{plan_line2}

📤 *FORWARDING:* {fwd_status}
  ➤ Groups: {group_count} ▪ Total Sent: {total_sends}
  ➤ Status: {await get_group_status_summary(user_id)}
  ➤ Interval: {interval} min ▪ Night: 12-6 AM

⚙️ *SETTINGS*
  {copy_icon} Copy Mode ▪ {shuffle_icon} Shuffle
  🔄 Send Mode: {send_mode}
  {responder_icon} Responder: _{reply_preview}_

💡 *TIP:* Send `.addgroup <url>` in Saved Messages!
"""
    
    # Determine how to respond
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            dashboard_text,
            parse_mode="Markdown",
            reply_markup=get_dashboard_keyboard(),
        )
    else:
        await update.message.reply_text(
            dashboard_text,
            parse_mode="Markdown",
            reply_markup=get_dashboard_keyboard(),
        )


async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dashboard callback."""
    await show_dashboard(update, context)


async def add_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show add account screen."""
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
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_add_account_keyboard(),
    )


async def toggle_send_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle between send modes (sequential -> rotate -> random -> sequential)."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check branding status
    if not await is_user_branded(user_id):
        await query.answer("❌ This feature is locked for free users.\nAdd branding to your profile to unlock!", show_alert=True)
        return
    
    config = await get_user_config(user_id)
    current_mode = config.get("send_mode", "sequential")
    
    modes = ["sequential", "rotate", "random"]
    next_mode = modes[(modes.index(current_mode) + 1) % len(modes)]
    
    await update_user_config(user_id, send_mode=next_mode)
    await query.answer(f"✅ Send mode updated to {next_mode.title()}")
    
    # Refresh settings view if we are in that menu, otherwise refresh dashboard
    if query.message.text and "SETTINGS" in query.message.text:
        await manage_settings_callback(update, context)
    else:
        await dashboard_callback(update, context)


# ==================== Management Handlers ====================

async def manage_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show group management menu."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    await query.answer()
    
    groups = await get_user_groups(user_id)
    text = f"""
👥 *GROUP MANAGEMENT*
══════════════════════════════

You have *{len(groups)}* groups registered.
Below are the first 10 groups. Click "Remove" to delete one.

_Note: You can add more groups by clicking "Add Group" below._
"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_manage_groups_keyboard(groups)
    )


async def manage_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user settings menu."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    await query.answer()
    
    config = await get_user_config(user_id)
    interval = config.get("interval_min", MIN_INTERVAL_MINUTES)
    send_mode = config.get("send_mode", "sequential").title()
    
    text = f"""
🛠️ *USER SETTINGS*
══════════════════════════════

⏱️ *Interval:* {interval} minutes
🔄 *Send Mode:* {send_mode}
🤖 *Auto-Responder:* {"Enabled ✅" if config.get("auto_reply_enabled") else "Disabled ⚫"}

_Toggle or update your preferences below._
"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_manage_settings_keyboard(config, is_branded=await is_user_branded(user_id))
    )


async def user_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user personal statistics."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    await query.answer()
    
    data = await get_user_profile_data(user_id)
    
    text = f"""
📊 *MY STATISTICS*
══════════════════════════════

📨 *Total Messages Sent:* {data['total_sent']}
✅ *Successful Deliveries:* {data['total_success']}
📈 *Success Rate:* {data['success_rate']}%

👥 *Groups Tracked:* {data['total_groups']}
📱 *Active Accounts:* {len(data['sessions'])}

⏱️ *Current Interval:* {data['config'].get('interval_min')} min
📅 *Member Since:* {data['user']['created_at'].strftime('%Y-%m-%d')}
"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_dashboard_keyboard()
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command for both users and admin."""
    user_id = update.effective_user.id
    
    if user_id == OWNER_ID:
        from main_bot.handlers.admin import get_stats_text, get_admin_keyboard
        text = await get_stats_text()
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_admin_keyboard())
    else:
        data = await get_user_profile_data(user_id)
        text = f"📊 *PERSONAL STATS*\n\nTotal Sent: {data['total_sent']}\nGroups: {data['total_groups']}\nSuccess: {data['success_rate']}%"
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_dashboard_keyboard())


# ==================== Toggle Handlers ====================

async def toggle_shuffle_ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not await is_user_branded(user_id):
        await query.answer("🔒 Feature locked. Add branding to unlock!", show_alert=True)
        return
        
    config = await get_user_config(user_id)
    new_val = not config.get("shuffle_mode", False)
    await update_user_config(user_id, shuffle_mode=new_val)
    await query.answer(f"Shuffle {'Enabled' if new_val else 'Disabled'}")
    await manage_settings_callback(update, context)


async def toggle_copy_ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not await is_user_branded(user_id):
        await query.answer("🔒 Feature locked. Add branding to unlock!", show_alert=True)
        return
        
    config = await get_user_config(user_id)
    new_val = not config.get("copy_mode", False)
    await update_user_config(user_id, copy_mode=new_val)
    await query.answer(f"Copy Mode {'Enabled' if new_val else 'Disabled'}")
    await manage_settings_callback(update, context)


async def toggle_responder_ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not await is_user_branded(user_id):
        await query.answer("🔒 Feature locked. Add branding to unlock!", show_alert=True)
        return
        
    config = await get_user_config(user_id)
    new_val = not config.get("auto_reply_enabled", False)
    await update_user_config(user_id, auto_reply_enabled=new_val)
    await query.answer(f"Responder {'Enabled' if new_val else 'Disabled'}")
    await manage_settings_callback(update, context)


# ==================== Input Prompts (Conversation) ====================

async def add_group_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ *ADD NEW GROUP*\n\nPlease send the Group URL or Username.\nExample: `https://t.me/group_link` or `@group_username`",
        parse_mode="Markdown"
    )
    return WAITING_GROUP_URL


async def receive_group_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()
    
    # Extremely simplified logic to simulate adding a group
    # In a real bot, we'd need a session to join and get title
    # For now, we'll try to extract a pseudo-ID/Title
    chat_id = hash(url) % 1000000000 
    title = url.split("/")[-1] if "/" in url else url
    
    success = await add_group(user_id, chat_id, title)
    
    if success:
        await update.message.reply_text(f"✅ Group added: *{title}*", parse_mode="Markdown", reply_markup=get_dashboard_keyboard())
    else:
        await update.message.reply_text("❌ Failed to add group. Check limit.")
        
    return ConversationHandler.END


async def remove_group_ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    chat_id = int(query.data.split(":")[1])
    
    await remove_group(user_id, chat_id)
    await query.answer("✅ Group removed")
    await manage_groups_callback(update, context)


async def set_interval_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"⏱️ *SET INTERVAL*\n\nPlease send the interval in minutes (Min: {MIN_INTERVAL_MINUTES}).",
        parse_mode="Markdown"
    )
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
    
    if not await is_user_branded(user_id):
        await query.answer("🔒 Feature locked. Add branding to unlock!", show_alert=True)
        return
        
    await query.answer()
    await query.edit_message_text(
        "🤖 *SET RESPONDER TEXT*\n\nPlease send the message you want the bot to reply with.",
        parse_mode="Markdown"
    )
    return WAITING_RESPONDER_TEXT


async def receive_responder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    await update_user_config(user_id, auto_reply_text=text)
    await update.message.reply_text("✅ Responder text updated.", reply_markup=get_dashboard_keyboard())
    return ConversationHandler.END
