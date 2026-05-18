"""
Admin Command Center — Global Fleet Telemetry, Remote User Controls, Global Announcements.
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from app.database.models import (
    get_user, get_all_users, get_global_stats, update_user_premium,
    clear_session, update_user
)
from app.config import OWNER_ID
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu
from app.services import engine
from app.services.encryption_service import decrypt_session
from app.services.telethon_service import (
    get_client_from_session, enforce_or_remove_branding, check_account_health
)

logger = logging.getLogger(__name__)

WAITING_USER_ID = 0
WAITING_GLOBAL_MSG = 1


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /admin access check."""
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("🔴 Unauthorized. Admin access only.")
        return

    stats = await get_global_stats()
    text = messages.admin_panel_text(stats)
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=keyboards.admin_keyboard()
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for admin command center."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        return

    stats = await get_global_stats()
    text = messages.admin_panel_text(stats)
    await _send_menu(update, context, text, keyboards.admin_keyboard())


async def admin_view_all_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View global user fleet telemetry."""
    query = update.callback_query
    await query.answer()
    if query.from_user.id != OWNER_ID:
        return

    users = await get_all_users()
    text = messages.admin_all_users_stats_text(users)
    await _send_menu(update, context, text, keyboards.admin_all_users_keyboard())


async def admin_manage_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for User ID to manage."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        return

    await _send_menu(
        update, context,
        messages.admin_manage_user_prompt_text(),
        keyboards.cancel_keyboard()
    )
    return WAITING_USER_ID


async def receive_manage_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive User ID and show Admin User Dashboard."""
    text = update.message.text.strip()
    try:
        target_id = int(text)
    except ValueError:
        await update.message.reply_text("🔴 Invalid User ID format. Enter a valid integer.")
        return WAITING_USER_ID

    target_user = await get_user(target_id)
    if not target_user:
        await update.message.reply_text("🔴 User record not found in database.")
        return WAITING_USER_ID

    is_broadcasting = target_user.get("is_broadcasting", False)
    is_premium = target_user.get("is_premium", False)

    msg_text = messages.admin_user_dashboard_text(target_user, is_broadcasting)
    markup = keyboards.admin_user_dashboard_keyboard(target_id, is_premium, is_broadcasting)

    await update.message.reply_text(msg_text, parse_mode="HTML", reply_markup=markup)
    return ConversationHandler.END


async def admin_toggle_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant or revoke premium status and instantly restore/enforce branding."""
    query = update.callback_query
    await query.answer("Updating premium status...")
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        return

    data = query.data
    parts = data.split("_")
    action = parts[0]
    target_id = int(parts[2])

    is_premium = (action == "grant")
    await update_user_premium(target_id, is_premium)

    target_user = await get_user(target_id)
    if target_user and target_user.get("session_encrypted"):
        client = None
        try:
            session = decrypt_session(target_user["session_encrypted"])
            client = await get_client_from_session(session)
            await enforce_or_remove_branding(client, is_premium, target_id)
        except Exception as e:
            logger.warning(f"Failed instant branding restore for {target_id}: {e}")
        finally:
            if client:
                try:
                    await client.disconnect()
                except Exception:
                    pass

    is_broadcasting = target_user.get("is_broadcasting", False)
    msg_text = messages.admin_user_dashboard_text(target_user, is_broadcasting)
    markup = keyboards.admin_user_dashboard_keyboard(target_id, is_premium, is_broadcasting)
    await _send_menu(update, context, msg_text, markup)


async def admin_remote_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remotely start broadcast engine for a user."""
    query = update.callback_query
    await query.answer("Starting broadcast engine...")
    target_id = int(query.data.split("_")[2])

    res = await engine.start(target_id)
    target_user = await get_user(target_id)
    is_broadcasting = target_user.get("is_broadcasting", False)
    is_premium = target_user.get("is_premium", False)

    msg_text = messages.admin_user_dashboard_text(target_user, is_broadcasting)
    if not res["success"]:
        msg_text += f"\n\n⚠️ <b>Engine Start Failed:</b> {res['error']}"

    markup = keyboards.admin_user_dashboard_keyboard(target_id, is_premium, is_broadcasting)
    await _send_menu(update, context, msg_text, markup)


async def admin_remote_stop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remotely stop broadcast engine for a user."""
    query = update.callback_query
    await query.answer("Stopping broadcast engine...")
    target_id = int(query.data.split("_")[2])

    await engine.stop(target_id)
    target_user = await get_user(target_id)
    is_broadcasting = target_user.get("is_broadcasting", False)
    is_premium = target_user.get("is_premium", False)

    msg_text = messages.admin_user_dashboard_text(target_user, is_broadcasting)
    markup = keyboards.admin_user_dashboard_keyboard(target_id, is_premium, is_broadcasting)
    await _send_menu(update, context, msg_text, markup)


async def admin_remote_health_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remotely evaluate account health for a user."""
    query = update.callback_query
    await query.answer("Evaluating remote account health...")
    target_id = int(query.data.split("_")[2])

    target_user = await get_user(target_id)
    if not target_user or not target_user.get("session_encrypted"):
        await query.edit_message_text(
            messages.error_text("Target user has no active Telegram session."),
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("admin")
        )
        return

    client = None
    try:
        session = decrypt_session(target_user["session_encrypted"])
        client = await get_client_from_session(session)
        report = await check_account_health(target_id, client)
        text = messages.health_monitor_text(report["score"], report["status"], report["details"])
        await _send_menu(update, context, text, keyboards.back_keyboard("admin"))
    except Exception as e:
        await _send_menu(
            update, context,
            messages.error_text(f"Remote health check failed: {type(e).__name__}"),
            keyboards.back_keyboard("admin")
        )
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass


async def admin_remote_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remotely view live stats for a user."""
    query = update.callback_query
    await query.answer()
    target_id = int(query.data.split("_")[2])

    target_user = await get_user(target_id)
    from app.config import MAX_FAIL_SKIP
    groups = target_user.get("groups", [])
    group_fails = target_user.get("group_fails", {})
    live_count = sum(1 for g in groups if group_fails.get(g.replace(".", "_DOT_").replace("$", "_DOLLAR_"), 0) < MAX_FAIL_SKIP)
    paused_count = len(groups) - live_count

    text = messages.live_stats_text(target_user, live_count, paused_count)
    await _send_menu(update, context, text, keyboards.back_keyboard("admin"))


async def admin_remote_wipe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remotely wipe corrupted session for a user."""
    query = update.callback_query
    await query.answer("Wiping remote session...")
    target_id = int(query.data.split("_")[2])

    await engine.stop(target_id)
    await clear_session(target_id)

    target_user = await get_user(target_id)
    is_broadcasting = False
    is_premium = target_user.get("is_premium", False)

    msg_text = messages.admin_user_dashboard_text(target_user, is_broadcasting)
    msg_text += "\n\n✨ <b>Success:</b> Remote session wiped cleanly."
    markup = keyboards.admin_user_dashboard_keyboard(target_id, is_premium, is_broadcasting)
    await _send_menu(update, context, msg_text, markup)


async def admin_global_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for global fleet announcement message."""
    query = update.callback_query
    await query.answer()
    if query.from_user.id != OWNER_ID:
        return

    await _send_menu(
        update, context,
        messages.admin_global_broadcast_prompt_text(),
        keyboards.cancel_keyboard()
    )
    return WAITING_GLOBAL_MSG


async def receive_global_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and transmit global fleet announcement."""
    msg = update.message
    users = await get_all_users()

    sent = 0
    failed = 0

    for u in users:
        chat_id = u.get("telegram_user_id")
        try:
            if msg.photo:
                await context.bot.send_photo(chat_id=chat_id, photo=msg.photo[-1].file_id, caption=msg.caption or "", parse_mode="HTML")
            elif msg.video:
                await context.bot.send_video(chat_id=chat_id, video=msg.video.file_id, caption=msg.caption or "", parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=chat_id, text=msg.text or "", parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        messages.admin_global_broadcast_success_text(sent, failed),
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("admin")
    )
    return ConversationHandler.END


async def _cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel admin conversation."""
    query = update.callback_query
    if query:
        await query.answer()
    await admin_callback(update, context)
    return ConversationHandler.END


def build_admin_premium_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_manage_user_callback, pattern="^admin_manage_user$"),
            CallbackQueryHandler(admin_global_broadcast_callback, pattern="^admin_global_broadcast$"),
        ],
        states={
            WAITING_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_manage_user_id)],
            WAITING_GLOBAL_MSG: [MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO, receive_global_broadcast)],
        },
        fallbacks=[
            CallbackQueryHandler(_cancel_admin, pattern="^cancel_conv$"),
            CallbackQueryHandler(_cancel_admin, pattern="^admin$"),
            CallbackQueryHandler(_cancel_admin, pattern="^dashboard$"),
        ],
        per_user=True, per_chat=True,
    )
