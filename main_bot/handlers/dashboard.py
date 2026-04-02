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
from models.group import get_user_groups, add_group, remove_group, get_group_count, get_group_by_id, toggle_group
from models.session import get_all_user_sessions
from models.stats import get_account_stats
from core.database import get_database
from main_bot.utils.keyboards import (
    get_dashboard_keyboard, get_add_account_keyboard,
    get_manage_groups_keyboard, get_manage_settings_keyboard
)
from core.config import (
    MIN_INTERVAL_MINUTES, MAX_GROUPS_PER_USER,
    BRANDING_NAME, BRANDING_BIO, OWNER_ID
)
from shared.utils import escape_markdown, parse_group_entry

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
            plan_type = plan.get("plan_type", "free")
            expires_at = plan.get("expires_at")

            if plan_type == "premium" and expires_at:
                days_left = (expires_at - datetime.datetime.utcnow()).days
                hours_left = ((expires_at - datetime.datetime.utcnow()).seconds // 3600)
                expiry_date = format_expiry_date(expires_at)
                plan_badge = "💎 PREMIUM"
                if days_left > 0:
                    plan_status = f"{plan_badge} ▪ {days_left}d {hours_left}h left"
                else:
                    plan_status = f"{plan_badge} ▪ {hours_left}h left"
                plan_line2 = f"     └─ 📅 Expires: {expiry_date}"
            else:
                plan_status = "🆓 FREE PLAN"
                plan_line2 = "     └─ ✅ Active — No Expiry"
        else:
            plan_status = "🆓 FREE PLAN"
            plan_line2 = "     └─ ✅ Active — No Expiry"
    else:
        plan_status = "🆓 FREE PLAN"
        plan_line2 = "     └─ ✅ Active — No Expiry"
    
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
    
    try:
        data = await get_user_profile_data(user_id)
        sessions = data.get('sessions', [])
        user_doc = data.get('user') or {}
        config_doc = data.get('config') or {}
        created_at = user_doc.get('created_at')
        member_since = created_at.strftime('%Y-%m-%d') if created_at else 'N/A'
        interval = config_doc.get('interval_min', 'N/A')

        text = f"""
📊 *MY STATISTICS — KURUP ADS*
══════════════════════════════

📨 *Total Sent:* {data.get('total_sent', 0)}
✅ *Successful:* {data.get('total_success', 0)}
📈 *Success Rate:* {data.get('success_rate', 0)}%

👥 *Groups Tracked:* {data.get('total_groups', 0)}
📱 *Active Accounts:* {len(sessions)}
⏱️ *Interval:* {interval} min
📅 *Member Since:* {member_since}
"""
    except Exception as e:
        text = f"❌ Could not load stats: {e}"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_dashboard_keyboard()
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command for both users and admin."""
    user_id = update.effective_user.id
    
    if user_id == OWNER_ID:
        from main_bot.handlers.admin import get_stats_text
        text = await get_stats_text()
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_dashboard_keyboard())
    else:
        try:
            data = await get_user_profile_data(user_id)
            sessions = data.get('sessions', [])
            user_data = data.get('user') or {}
            config_data = data.get('config') or {}
            created_at = user_data.get('created_at')
            member_since = created_at.strftime('%Y-%m-%d') if created_at else 'N/A'
            interval = config_data.get('interval_min', 'N/A')
            text = f"""
📊 *YOUR STATS — KURUP ADS*

📨 *Total Sent:* {data.get('total_sent', 0)}
✅ *Successful:* {data.get('total_success', 0)}
📈 *Success Rate:* {data.get('success_rate', 0)}%

👥 *Groups:* {data.get('total_groups', 0)}
📱 *Accounts:* {len(sessions)}
⏱️ *Interval:* {interval} min
📅 *Member Since:* {member_since}
"""
        except Exception as e:
            text = f"❌ Could not load stats: {e}"
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
    try:
        await query.edit_message_text(
            """
➕ *ADD GROUPS*

Send one or multiple group links, one per line.

*Supported formats:*
• `https://t.me/groupname` — public group
• `https://t.me/+AbcXyzPrivateHash` — private group
• `@groupname` — username
• `-1001234567890` — numeric Chat ID
• `https://t.me/addlist/FolderHash` — folder link

*Example (bulk add):*
```
https://t.me/group1
https://t.me/+AbcPrivate
@anothergroup
```
⚠️ For private groups, the bot will join them automatically using your connected account.
""",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    return WAITING_GROUP_URL


async def receive_group_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bulk group input — all link types supported."""
    user_id = update.effective_user.id
    raw_text = update.message.text.strip()

    # Split input by newlines and commas
    lines = [line.strip() for line in raw_text.replace(",", "\n").splitlines() if line.strip()]

    added, skipped, errors = [], [], []

    for entry in lines:
        try:
            chat_id, chat_username, title = parse_group_entry(entry)
            result = await add_group(user_id, chat_id, title, chat_username=chat_username)
            if result is not None:
                added.append(title)
            else:
                skipped.append(entry)
        except Exception as e:
            errors.append(f"`{entry[:40]}` — {str(e)}")

    # Build result message
    lines_out = []
    if added:
        lines_out.append(f"✅ *Added* ({len(added)}): " + ", ".join(f"`{t}`" for t in added))
    if skipped:
        lines_out.append(f"⚠️ *Already exists / skipped* ({len(skipped)})")
    if errors:
        lines_out.append(f"❌ *Errors* ({len(errors)}):")
        lines_out.extend(errors)
    if not lines_out:
        lines_out = ["❌ No valid groups found in your input."]

    await update.message.reply_text(
        "\n".join(lines_out),
        parse_mode="Markdown",
        reply_markup=get_dashboard_keyboard()
    )
    return ConversationHandler.END




async def remove_group_ui_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    parts = query.data.split(":")
    chat_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    await remove_group(user_id, chat_id)
    await query.answer("✅ Group removed")

    groups = await get_user_groups(user_id)
    from main_bot.utils.keyboards import get_manage_groups_keyboard, GROUPS_PER_PAGE
    total_pages = max(1, (len(groups) + GROUPS_PER_PAGE - 1) // GROUPS_PER_PAGE)
    page = min(page, total_pages - 1)
    await query.edit_message_text(
        f"👥 *GROUP MANAGER* — {len(groups)} groups\n\n"
        "Tap a group to toggle it on/off. Tap 🗑 to remove.",
        parse_mode="Markdown",
        reply_markup=get_manage_groups_keyboard(groups, page)
    )


async def groups_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pagination — switch to requested page."""
    query = update.callback_query
    user_id = update.effective_user.id
    page = int(query.data.split(":")[1])
    await query.answer()

    groups = await get_user_groups(user_id)
    from main_bot.utils.keyboards import get_manage_groups_keyboard
    await query.edit_message_text(
        f"👥 *GROUP MANAGER* — {len(groups)} groups\n\n"
        "Tap a group to toggle it on/off. Tap 🗑 to remove.",
        parse_mode="Markdown",
        reply_markup=get_manage_groups_keyboard(groups, page)
    )


async def group_toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle a group enabled/disabled."""
    query = update.callback_query
    user_id = update.effective_user.id
    parts = query.data.split(":")
    chat_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0

    # Toggle
    db_group = await get_group_by_id(user_id, chat_id)
    if db_group:
        new_val = not db_group.get("enabled", True)
        await toggle_group(user_id, chat_id, new_val)
        status = "✅ Enabled" if new_val else "⛔ Disabled"
    else:
        status = "⚠️ Group not found"

    await query.answer(status)

    groups = await get_user_groups(user_id)
    from main_bot.utils.keyboards import get_manage_groups_keyboard
    await query.edit_message_text(
        f"👥 *GROUP MANAGER* — {len(groups)} groups\n\n"
        "Tap a group to toggle it on/off. Tap 🗑 to remove.",
        parse_mode="Markdown",
        reply_markup=get_manage_groups_keyboard(groups, page)
    )


async def confirm_clear_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show clear all confirmation."""
    query = update.callback_query
    await query.answer()
    from main_bot.utils.keyboards import get_confirm_clear_groups_keyboard
    await query.edit_message_text(
        "⚠️ *REMOVE ALL GROUPS?*\n\nThis will delete all your groups. This cannot be undone.",
        parse_mode="Markdown",
        reply_markup=get_confirm_clear_groups_keyboard()
    )


async def clear_groups_confirmed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete all groups."""
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer("🗑 All groups cleared")

    from core.database import get_database
    db = get_database()
    await db.groups.delete_many({"user_id": user_id})

    from main_bot.utils.keyboards import get_manage_groups_keyboard
    await query.edit_message_text(
        "✅ All groups removed.\n\nTap ➕ Add Groups to add new ones.",
        parse_mode="Markdown",
        reply_markup=get_manage_groups_keyboard([], 0)
    )


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """No-operation callback for display-only buttons."""
    await update.callback_query.answer()


async def set_interval_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.edit_message_text(
            f"⏱️ *SET INTERVAL*\n\nPlease send the interval in minutes (Min: {MIN_INTERVAL_MINUTES}).",
            parse_mode="Markdown"
        )
    except Exception:
        pass
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
    try:
        await query.edit_message_text(
            "🤖 *SET RESPONDER TEXT*\n\nPlease send the message you want the bot to reply with.",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    return WAITING_RESPONDER_TEXT


async def receive_responder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    await update_user_config(user_id, auto_reply_text=text)
    await update.message.reply_text("✅ Responder text updated.", reply_markup=get_dashboard_keyboard())
    return ConversationHandler.END
