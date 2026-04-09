"""
Admin/Owner panel handler for Main Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest

from models.stats import get_admin_stats
from models.user import get_all_users_for_broadcast
from models.settings import get_global_settings, update_global_settings
from main_bot.utils.keyboards import (
    get_admin_keyboard, get_broadcast_keyboard, get_back_home_keyboard,
    get_night_mode_settings_keyboard, get_stats_keyboard,
    get_admin_group_stats_keyboard
)
from core.config import OWNER_ID, MAIN_BOT_TOKEN
from core.utils import escape_markdown
from models.session import get_all_connected_sessions
from models.group import get_all_failing_groups, clear_group_fail


# Conversation states
WAITING_BROADCAST_MESSAGE = 1
WAITING_UPGRADE_USER_ID = 2


def is_owner(user_id: int) -> bool:
    """Check if user is the owner."""
    return user_id == OWNER_ID


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    await query.answer()
    
    text = """
👑 *ADMINISTRATOR TERMINAL*

Welcome to the command center.
Manage users, track live statistics, and broadcast announcements directly below.
"""
    
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard(),
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command."""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("⛔ Access denied")
        return
    
    text = """
👑 *ADMINISTRATOR TERMINAL*
══════════════════════════════

Welcome to the command center.
Manage users, track live statistics, and 
broadcast announcements directly below.
"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard(),
    )


async def get_stats_text():
    from core.database import get_database
    from datetime import datetime

    stats = await get_admin_stats()

    total = stats.get('sends_24h', 0)
    success = stats.get('success_24h', 0)
    success_rate = round((success / total * 100) if total > 0 else 0, 1)

    # ─── Live Session Monitor ───
    db = get_database()
    sessions = await db.sessions.find({"connected": True}).to_list(length=200)
    disabled = await db.sessions.count_documents({"connected": False})

    # Group by user
    user_sessions: dict = {}
    for s in sessions:
        uid = s.get("user_id", "?")
        phone = s.get("phone", "?")
        user_sessions.setdefault(uid, []).append(phone)

    session_lines = []
    for uid, phones in list(user_sessions.items())[:15]:  # show max 15 users
        phones_str = ", ".join(f"`{p}`" for p in phones)
        session_lines.append(f"  ├ `{uid}` → {phones_str}")
    if len(user_sessions) > 15:
        session_lines.append(f"  └ ... and {len(user_sessions) - 15} more users")

    session_block = "\n".join(session_lines) if session_lines else "  No active sessions"

    return f"""
‣ Kᴜʀᴜᴘ Aᴅs │ *ADMIN PANEL*
══════════════════════════════

👥 *USER METRICS*
├ Total Users: {stats.get('total_users', 0)}
├ Active Sessions: {len(sessions)}
└ Disabled Sessions: {disabled}

📨 *PERFORMANCE (LAST 24H)*
├ Messages Attempted: {total}
├ Messages Delivered: {success}
├ Success Rate: {success_rate}%
└ Failures: {stats.get('failed_24h', 0)}

📁 *GROUP HEALTH*
├ Total Groups: {stats.get('total_groups', 'N/A')}
├ Currently Failing: {stats.get('groups_failing', 0)} ⚠️
└ Removed (24h): {stats.get('groups_removed_24h', 0)}

📱 *LIVE SESSION MONITOR* ({len(sessions)} active | {disabled} disabled)
{session_block}

🛡️ *SYSTEM:* 🟢 Operational
_Live data as of {datetime.utcnow().strftime('%H:%M')} UTC_
"""

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("⛔ Access denied")
        return
    
    text = await get_stats_text()
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_stats_keyboard(),
    )


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command."""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("⛔ Access denied")
        return
    
    text = """
📢 *GLOBAL BROADCAST SYSTEM*
══════════════════════════════

Select your target audience below to 
initiate the broadcast sequence:
"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_broadcast_keyboard(),
    )


async def admin_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    await query.answer()
    
    text = await get_stats_text()
    
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_stats_keyboard(),
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise

async def admin_health_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show session health and live worker monitor."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    await query.answer()
    
    from models.session import get_all_connected_sessions
    from models.stats import get_active_workers
    from datetime import datetime
    
    sessions = await get_all_connected_sessions()
    workers = await get_active_workers()
    
    text = "🩺 *SYSTEM HEALTH MONITOR*\n\n"
    
    # ─── Worker Monitor ───
    text += "👷 *LIVE WORKERS*\n"
    if workers:
        for w in workers:
            wid = w.get("worker_id", "???")
            last = w.get("last_seen")
            ago = int((datetime.utcnow() - last).total_seconds()) if last else "?"
            text += f"  ├ ID: `{wid}` ▪ Status: {ago}s ago\n"
        text += f"  └ Total Active: {len(workers)}\n\n"
    else:
        text += "  └ ⚠️ No active workers detected!\n\n"
    
    # ─── Session Health ───
    text += "📱 *SESSIONS*\n"
    active_sessions_count = 0
    if sessions:
        for s in sessions:
            uid = s.get("user_id")
            if not uid: continue
            
            active_sessions_count += 1
            phone = s.get("phone", "Unknown")
            status = s.get("worker_status", "Off")
            streak = s.get("error_streak", 0)
            
            icon = "🟢"
            if streak > 5: icon = "🔴"
            elif streak > 0: icon = "🟡"
            
            text += f"  {icon} `{phone}` | {status} | Err: {streak}\n"
            
    if active_sessions_count == 0:
        text += "  _No active sessions found._"
    
    text += "\n\n*Status Legend:*\n🟢 Healthy | 🟡 Unstable | 🔴 Critical"
    
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_stats_keyboard(),
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise



async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show broadcast options."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    await query.answer()
    
    text = """
📢 *GLOBAL BROADCAST SYSTEM*
══════════════════════════════

Select your target audience below to 
initiate the broadcast sequence:
"""
    
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_broadcast_keyboard(),
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def broadcast_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast target selection."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    target = query.data.split(":")[1]
    context.user_data["broadcast_target"] = target
    
    await query.answer()
    
    text = f"""
📢 *BROADCAST TARGET: {target.upper()}*

Awaiting transmission payload...
Send me the exact message you want to blast.

*Supports:* Text, Photos, Videos, Documents
*Abort:* Type `/cancel` anytime to stop.
"""
    
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_back_home_keyboard(),
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise
    
    context.user_data["waiting_for"] = "broadcast_message"
    return WAITING_BROADCAST_MESSAGE


async def receive_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process and send broadcast message."""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        return ConversationHandler.END
        
    if update.message.text == "/cancel":
        await update.message.reply_text("Broadcast cancelled.", reply_markup=get_back_home_keyboard())
        context.user_data.pop("waiting_for", None)
        context.user_data.pop("broadcast_target", None)
        return ConversationHandler.END
    
    target = context.user_data.get("broadcast_target", "all")
    message = update.message
    
    # Get target users
    user_ids = await get_all_users_for_broadcast(target)
    
    success = 0
    failed = 0
    
    status_msg = await message.reply_text(f"📤 *Initiating broadcast to {len(user_ids)} users...*", parse_mode="Markdown")
    
    for uid in user_ids:
        try:
            if message.text:
                # Try without parse_mode first (safer for plain text with special chars)
                try:
                    await context.bot.send_message(
                        uid, 
                        message.text, 
                        parse_mode="Markdown",
                        disable_web_page_preview=False
                    )
                except Exception:
                    # Fallback: send without Markdown if it fails
                    await context.bot.send_message(
                        uid, 
                        message.text,
                        disable_web_page_preview=False
                    )
            elif message.photo:
                await context.bot.send_photo(
                    uid,
                    message.photo[-1].file_id,
                    caption=message.caption
                )
            elif message.video:
                await context.bot.send_video(
                    uid,
                    message.video.file_id,
                    caption=message.caption
                )
            elif message.animation:
                await context.bot.send_animation(
                    uid,
                    message.animation.file_id,
                    caption=message.caption
                )
            elif message.sticker:
                await context.bot.send_sticker(uid, message.sticker.file_id)
            elif message.voice:
                await context.bot.send_voice(
                    uid,
                    message.voice.file_id,
                    caption=message.caption
                )
            elif message.audio:
                await context.bot.send_audio(
                    uid,
                    message.audio.file_id,
                    caption=message.caption
                )
            elif message.video_note:
                await context.bot.send_video_note(uid, message.video_note.file_id)
            elif message.document:
                await context.bot.send_document(
                    uid,
                    message.document.file_id,
                    caption=message.caption
                )
            else:
                # Fallback: copy the message directly for any other type
                await context.bot.copy_message(
                    chat_id=uid,
                    from_chat_id=message.chat_id,
                    message_id=message.message_id
                )
            success += 1
        except Exception as e:
            failed += 1
            # Log first few failures for debugging
            if failed <= 3:
                import logging
                logging.warning(f"Broadcast failed for {uid}: {e}")
    
    await status_msg.edit_text(
        f"✅ *BROADCAST COMPLETE*\n\n"
        f"🎯 *Delivered:* {success}\n"
        f"❌ *Failed:* {failed}",
        parse_mode="Markdown",
        reply_markup=get_back_home_keyboard()
    )
    
    context.user_data.pop("waiting_for", None)
    context.user_data.pop("broadcast_target", None)
    return ConversationHandler.END


async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show users overview."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    await query.answer()
    
    stats = await get_admin_stats()
    
    text = f"""
👥 *GLOBAL USER DATABASE*

📊 *Total Registered Users:* {stats['total_users']}

*SEGMENTATION ANALYSIS:*
├ 🔗 Active API Sessions: {stats['connected_sessions']}
└ 🛡️ Status: 🟢 All services operating normally
"""
    
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_stats_keyboard(),
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def admin_nightmode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show global night mode settings."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    await query.answer()
    
    settings = await get_global_settings()
    current = settings.get("night_mode_force", "auto").upper()
    
    text = f"""
🌙 *GLOBAL NIGHT MODE CONTROL*
══════════════════════════════

*Current State:* `{current}`

Select a mode button below to override the system-wide night mode behavior:

🔴 *FORCE ON:* Pauses all bots immediately.
🟢 *FORCE OFF:* Disables night mode pause entirely.
⏳ *AUTO (Schedule):* Resumes 00:00-06:00 IST logic.

_This change affects all accounts globally._
"""
    
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_night_mode_settings_keyboard(),
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def set_nightmode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update global night mode setting via callback."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    mode = query.data.split(":")[1]
    await update_global_settings(night_mode_force=mode)
    
    await query.answer(f"✅ Night Mode updated to {mode.upper()}", show_alert=True)
    await admin_nightmode_callback(update, context)


async def nightmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /nightmode command from owner."""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("⛔ Access denied")
        return
    
    settings = await get_global_settings()
    current = settings.get("night_mode_force", "auto").upper()
    
    text = f"""
🌙 *GLOBAL NIGHT MODE CONTROL*
══════════════════════════════

*Current State:* `{current}`

Select a mode button below to override the system-wide night mode behavior.
"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_night_mode_settings_keyboard(),
    )


async def admin_group_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed group failure statistics."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    await query.answer()
    
    failing = await get_all_failing_groups()
    
    text = "📁 *GROUP HEALTH MONITOR*\n"
    text += "══════════════════════════════\n\n"
    
    if not failing:
        text += "✅ *All groups are healthy!*\nNo failures detected in the last 24h."
    else:
        text += f"⚠️ *Detected {len(failing)} failing groups:*\n\n"
        # Group by reason
        reasons: dict = {}
        for g in failing:
            r = g.get("fail_reason", "Unknown")
            reasons.setdefault(r, []).append(g)
            
        for reason, groups in reasons.items():
            text += f"📍 *{reason}* ({len(groups)})\n"
            for g in groups[:5]: # Show max 5 per reason
                title = g.get("chat_title", "Unknown")
                uid = g.get("user_id", "?")
                text += f"  ├ `{title[:20]}` (User: `{uid}`)\n"
            if len(groups) > 5:
                text += f"  └ ... and {len(groups) - 5} more\n"
            text += "\n"
            
    text += "\n_Failing groups are automatically paused. Click 'Retry All' to attempt recovery._"
    
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_group_stats_keyboard(),
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise

async def admin_retry_failing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all group failures to trigger retries."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    failing = await get_all_failing_groups()
    if not failing:
        await query.answer("✅ No failing groups to retry", show_alert=True)
        return
        
    await query.answer(f"🔄 Retrying {len(failing)} groups...", show_alert=True)
    
    for g in failing:
        await clear_group_fail(g["user_id"], g["chat_id"])
        
    # Refresh view
    await admin_group_stats_callback(update, context)

async def admin_stop_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop all bots globally."""
    query = update.callback_query
    if not is_owner(update.effective_user.id): return
    
    from models.settings import update_global_settings
    await update_global_settings(all_bots_active=False)
    await query.answer("🛑 ALL BOTS STOPPED GLOBALLY", show_alert=True)
    await admin_callback(update, context)

async def admin_start_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start all bots globally."""
    query = update.callback_query
    if not is_owner(update.effective_user.id): return
    
    from models.settings import update_global_settings
    await update_global_settings(all_bots_active=True)
    await query.answer("▶️ ALL BOTS STARTED GLOBALLY", show_alert=True)
    await admin_callback(update, context)
