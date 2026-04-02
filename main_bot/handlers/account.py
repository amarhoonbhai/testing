"""
Account management handler for Main Bot.
"""

from core.config import MAIN_BOT_USERNAME
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from models.session import get_all_user_sessions, get_session, disconnect_session, toggle_session_ads
from models.stats import get_account_stats
from models.group import get_user_groups, add_group, remove_group, get_group_by_id, toggle_group
from main_bot.utils.keyboards import (
    get_account_selection_keyboard,
    get_manage_account_keyboard, 
    get_confirm_disconnect_keyboard,
    get_back_home_keyboard,
    get_manage_groups_acc_keyboard,
    get_confirm_clear_groups_acc_keyboard
)
from shared.utils import escape_markdown, parse_group_entry

# Shared conversation states
WAITING_GROUP_URL_ACC = 110

def format_date(dt: datetime) -> str:
    if not dt:
        return "Unknown"
    return dt.strftime("%d %b %Y, %H:%M UTC")

async def accounts_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of connected accounts."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    sessions = await get_all_user_sessions(user_id)
    
    if not sessions:
        text = """
⚙️ *ACCOUNT MANAGER*

🔴 *STATUS:* No accounts connected

🚀 *GET STARTED NOW!*
1️⃣ Go back to home
2️⃣ Tap "➕ Add Account"
3️⃣ Link your account securely

*Your API credentials are safe and encrypted.*
"""
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_back_home_keyboard(),
        )
        return
    
    text = """
⚙️ *ACCOUNT MANAGER*

Select a connected account below to view its live stats or to disconnect it:
"""
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_account_selection_keyboard(sessions),
    )


async def manage_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show specific account details."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    phone = query.data.split(":")[1]
    
    session = await get_session(user_id, phone)
    
    if not session:
        await query.answer("❌ Account not found", show_alert=True)
        return
    
    # Build account details
    connected = session.get("connected", False)
    connected_at = session.get("connected_at")
    
    status_icon = "🟢" if connected else "🔴"
    status_text = "CONNECTED" if connected else "DISCONNECTED"
    
    connected_date = format_date(connected_at)
    
    stats = await get_account_stats(user_id, phone)
    total_sent = stats.get("total_sent", 0)
    success_rate = stats.get("success_rate", 0)
    last_active = format_date(stats.get("last_active"))
    
    escaped_phone = escape_markdown(phone)
    text = f"""
📱 *ACCOUNT PROFILE*

{status_icon} *STATUS:* {status_text}

👤 *DETAILS*
📞 *Phone:* `{escaped_phone}`
🔗 *Linked On:* {connected_date}

📊 *LIFETIME STATS*
📤 *Messages Sent:* {total_sent}
🎯 *Success Rate:* {success_rate}%
⏱️ *Last Active:* {last_active}

⚠️ *DANGER ZONE* ⚠️
Disconnecting removes your session forever and immediately stops all forwarding.
"""
    
    is_active = session.get("is_active", True)
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_manage_account_keyboard(phone, is_active=is_active),
    )


async def toggle_account_ads_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle ads for a specific account."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    data = query.data.split(":")
    action = data[0] # start_acc_ads or stop_acc_ads
    phone = data[1]
    
    new_status = (action == "start_acc_ads")
    await toggle_session_ads(user_id, phone, new_status)
    
    verb = "STARTED" if new_status else "STOPPED"
    await query.answer(f"✅ Ads {verb} for {phone}", show_alert=True)
    
    # Refresh the view
    await manage_account_callback(update, context)


async def start_all_accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start ads for all connected accounts of this user."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    from core.database import get_database
    db = get_database()
    await db.sessions.update_many({"user_id": user_id, "connected": True}, {"$set": {"is_active": True}})
    
    await query.answer("▶️ All Accounts STARTED", show_alert=True)
    await accounts_list_callback(update, context)


async def stop_all_accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop ads for all connected accounts of this user."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    from core.database import get_database
    db = get_database()
    await db.sessions.update_many({"user_id": user_id, "connected": True}, {"$set": {"is_active": False}})
    
    await query.answer("⏸ All Accounts STOPPED", show_alert=True)
    await accounts_list_callback(update, context)


async def manage_groups_acc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show group manager for a specific account."""
    query = update.callback_query
    user_id = update.effective_user.id
    phone = query.data.split(":")[1]
    page = int(query.data.split(":")[2]) if len(query.data.split(":")) > 2 else 0
    
    await query.answer()
    
    groups = await get_user_groups(user_id, phone=phone)
    text = f"""
👥 *GROUP MANAGER — {phone}*
══════════════════════════════

Showing *{len(groups)}* groups linked to this account.
Tap a group to toggle it ON/OFF.
"""
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_manage_groups_acc_keyboard(groups, phone, page)
    )

async def add_groups_acc_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for group URLs for a specific account."""
    query = update.callback_query
    phone = query.data.split(":")[1]
    context.user_data['active_phone'] = phone # Store for conversation handler
    
    await query.answer()
    await query.edit_message_text(
        f"""
➕ *ADD GROUPS — {phone}*

Send group links or usernames (one per line).
The bot will use this account to join and send ads.

*Supported:*
• `t.me/groupname`
• `t.me/+InviteHash`
• `@username`
• `-1001234567890`
""",
        parse_mode="Markdown"
    )
    return WAITING_GROUP_URL_ACC

async def receive_group_url_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming group links for the active account."""
    user_id = update.effective_user.id
    phone = context.user_data.get('active_phone')
    raw_text = update.message.text.strip()
    
    if not phone:
        await update.message.reply_text("❌ Session expired. Please try again from Manage Accounts.")
        return ConversationHandler.END

    lines = [l.strip() for l in raw_text.replace(",", "\n").splitlines() if l.strip()]
    added, errors = [], []

    for entry in lines:
        try:
            chat_id, chat_username, title = parse_group_entry(entry)
            await add_group(user_id, chat_id, title, account_phone=phone, chat_username=chat_username)
            added.append(title)
        except Exception as e:
            errors.append(f"❌ `{entry[:30]}`: {e}")

    res = f"✅ *Success:* Added {len(added)} groups to `{phone}`."
    if errors:
        res += "\n\n" + "\n".join(errors)
        
    await update.message.reply_text(res, parse_mode="Markdown", reply_markup=get_manage_account_keyboard(phone))
    return ConversationHandler.END

async def grp_tgl_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    # grp_tgl:{chat_id}:{phone}:{page}
    parts = query.data.split(":")
    chat_id, phone, page = int(parts[1]), parts[2], int(parts[3])
    
    group = await get_group_by_id(user_id, chat_id, phone=phone)
    if group:
        new_val = not group.get("enabled", True)
        await toggle_group(user_id, chat_id, new_val, phone=phone)
        await query.answer(f"{'✅ Enabled' if new_val else '⛔ Disabled'}")
    
    await manage_groups_acc_callback(update, context)

async def grp_del_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    # grp_del:{chat_id}:{phone}:{page}
    parts = query.data.split(":")
    chat_id, phone, page = int(parts[1]), parts[2], int(parts[3])
    
    await remove_group(user_id, chat_id, phone=phone)
    await query.answer("🗑 Group Removed")
    
    await manage_groups_acc_callback(update, context)

async def grp_pg_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # grp_pg:{phone}:{page}
    await manage_groups_acc_callback(update, context)

async def grp_clr_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    phone = query.data.split(":")[1]
    await query.answer()
    await query.edit_message_text(
        f"⚠️ *REMOVE ALL GROUPS — {phone}*?\n\nThis will delete all groups linked to this account.",
        parse_mode="Markdown",
        reply_markup=get_confirm_clear_groups_acc_keyboard(phone)
    )

async def grp_clr_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    phone = query.data.split(":")[1]
    
    from core.database import get_database
    db = get_database()
    await db.groups.delete_many({"user_id": user_id, "account_phone": phone})
    
    await query.answer("🗑 All groups cleared")
    await manage_groups_acc_callback(update, context)


async def disconnect_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show disconnect confirmation screen."""
    query = update.callback_query
    await query.answer()
    
    phone = query.data.split(":")[1]
    
    escaped_phone = escape_markdown(phone)
    text = f"""
⚠️ *CRITICAL ACTION*

📱 *Target:* `{escaped_phone}`

❗ *Are you absolutely sure you want to disconnect?*

*This will immediately:*
❌ Stop all message forwarding
🗑️ Delete your stored sessions
🔴 Require re-login via OTP to reconnect

👇 *Please confirm your choice below*
"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_confirm_disconnect_keyboard(phone),
    )


async def confirm_disconnect_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Actually disconnect the account."""
    query = update.callback_query
    await query.answer("🔄 Disconnecting...")
    
    user_id = update.effective_user.id
    phone = query.data.split(":")[1]
    
    # Disconnect session in database for specific phone
    await disconnect_session(user_id, phone)
    
    escaped_phone = escape_markdown(phone)
    text = f"""
✅ *SUCCESSFULLY DISCONNECTED*

📱 *Account:* `{escaped_phone}`

Your session has been securely wiped and forwarding has immediately halted.

You can reconnect anytime via the **Add Account** button.
"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_back_home_keyboard(),
    )
