"""
Dashboard handler — shows the main control panel with live stats.
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from app.config import OWNER_ID
from app.database.models import get_user, upsert_user
from app.services import engine
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join

logger = logging.getLogger(__name__)


@require_join
async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the dashboard with live user stats."""
    user_id = update.effective_user.id

    user = await get_user(user_id)
    if not user:
        user = await upsert_user(user_id, update.effective_user.username or "")

    has_account = bool(user.get("session_encrypted"))
    has_message = bool(user.get("message"))
    group_count = len(user.get("groups", []))
    total_sent = user.get("total_sent", 0)
    total_failed = user.get("total_failed", 0)
    interval = user.get("interval_seconds", 1200)
    phone_masked = user.get("phone_masked")

    # Check live broadcasting status (task may have crashed)
    is_broadcasting = engine.is_running(user_id)

    # Sync DB state if task died
    if user.get("is_broadcasting") and not is_broadcasting:
        from app.database.models import set_broadcasting
        await set_broadcasting(user_id, False)

    is_owner = (user_id == OWNER_ID)

    text = messages.dashboard_text(
        has_account=has_account,
        has_message=has_message,
        group_count=group_count,
        total_sent=total_sent,
        total_failed=total_failed,
        is_broadcasting=is_broadcasting,
        interval=interval,
        phone_masked=phone_masked,
    )

    reply_markup = keyboards.dashboard_keyboard(
        is_broadcasting=is_broadcasting,
        has_account=has_account,
        is_owner=is_owner,
    )

    await _send_menu(update, context, text, reply_markup)


# ── Health Monitor ───────────────────────────────────────────────────────────

@require_join
async def health_monitor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check account health live."""
    query = update.callback_query
    await query.answer("Checking account health...")
    user_id = query.from_user.id

    user = await get_user(user_id)
    if not user or not user.get("session_encrypted"):
        await _send_menu(
            update, context,
            messages.error_text("You must connect your Telegram account first."),
            keyboards.back_keyboard("dashboard")
        )
        return

    client = None
    try:
        from app.services.encryption_service import decrypt_session
        from app.services.telethon_service import get_client_from_session, check_account_health
        session = decrypt_session(user["session_encrypted"])
        client = await get_client_from_session(session)

        report = await check_account_health(user_id, client)
        text = messages.health_monitor_text(report["score"], report["status"], report["details"])
        await _send_menu(update, context, text, keyboards.health_monitor_keyboard())
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        await _send_menu(
            update, context,
            messages.error_text(f"Health check failed: {e}"),
            keyboards.health_monitor_keyboard()
        )
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass


# ── Live Stats ───────────────────────────────────────────────────────────────

@require_join
async def live_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View individual live stats."""
    query = update.callback_query
    if query:
        await query.answer()
    user_id = update.effective_user.id

    user = await get_user(user_id)
    if not user:
        return

    groups = user.get("groups", [])
    group_fails = user.get("group_fails", {})
    from app.config import MAX_FAIL_SKIP
    live_count = sum(1 for g in groups if group_fails.get(g, 0) < MAX_FAIL_SKIP)
    paused_count = sum(1 for g in groups if group_fails.get(g, 0) >= MAX_FAIL_SKIP)

    text = messages.live_stats_text(user, live_count, paused_count)
    await _send_menu(update, context, text, keyboards.live_stats_keyboard())


# ── Premium Info ─────────────────────────────────────────────────────────────

@require_join
async def premium_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View premium info."""
    query = update.callback_query
    if query:
        await query.answer()
    user_id = update.effective_user.id

    user = await get_user(user_id)
    is_premium = user.get("is_premium", False) if user else False

    text = messages.premium_info_text(is_premium)
    await _send_menu(update, context, text, keyboards.premium_info_keyboard(is_premium))


# ── Auto Responder ───────────────────────────────────────────────────────────

WAITING_AUTO_RESPONDER = 1

@require_join
async def auto_responder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View auto responder menu."""
    query = update.callback_query
    if query:
        await query.answer()
    user_id = update.effective_user.id

    user = await get_user(user_id)
    if not user:
        return

    enabled = user.get("auto_responder_enabled", False)
    msg = user.get("auto_responder_message", "Hello! I am currently busy. I will get back to you soon.")

    text = messages.auto_responder_text(enabled, msg)
    await _send_menu(update, context, text, keyboards.auto_responder_keyboard(enabled))


@require_join
async def toggle_auto_responder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle auto responder ON/OFF."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user = await get_user(user_id)
    enabled = not user.get("auto_responder_enabled", False)
    from app.database.models import update_user
    await update_user(user_id, auto_responder_enabled=enabled)

    await auto_responder_callback(update, context)


@require_join
async def set_auto_responder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for auto responder message."""
    query = update.callback_query
    await query.answer()

    await _send_menu(
        update, context,
        messages.auto_responder_prompt_text(),
        keyboards.back_keyboard("auto_responder")
    )
    return WAITING_AUTO_RESPONDER


async def receive_auto_responder_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save auto responder message."""
    user_id = update.effective_user.id
    text = update.message.text

    from app.database.models import update_user
    await update_user(user_id, auto_responder_message=text)

    await update.message.reply_text(
        messages.auto_responder_saved_text(),
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("auto_responder")
    )
    return ConversationHandler.END


async def _cancel_to_auto_responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    await auto_responder_callback(update, context)
    return ConversationHandler.END


def build_auto_responder_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(set_auto_responder_callback, pattern="^set_auto_responder_message$"),
        ],
        states={
            WAITING_AUTO_RESPONDER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_auto_responder_message),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(_cancel_to_auto_responder, pattern="^auto_responder$"),
            CallbackQueryHandler(_cancel_to_auto_responder, pattern="^dashboard$"),
            CallbackQueryHandler(_cancel_to_auto_responder, pattern="^home$"),
        ],
        per_user=True, per_chat=True,
    )
