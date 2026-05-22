"""
Dashboard handler — Executive Overview, Health Monitor, Auto Responder, Telemetry, Premium.
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from app.database.models import get_user, update_user
from app.config import OWNER_ID, DEFAULT_INTERVAL
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join, end_conversation_callback
from app.services.encryption_service import decrypt_session
from app.services.telethon_service import get_client_from_session, check_account_health

logger = logging.getLogger(__name__)

WAITING_AR_MESSAGE = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the main executive dashboard."""
    user_id = update.effective_user.id
    user = await get_user(user_id)

    has_account = bool(user.get("session_encrypted")) if user else False
    group_count = len(user.get("groups", [])) if user else 0
    total_sent = user.get("total_sent", 0) if user else 0
    total_failed = user.get("total_failed", 0) if user else 0
    is_broadcasting = user.get("is_broadcasting", False) if user else False
    interval = user.get("interval_seconds", DEFAULT_INTERVAL) if user else DEFAULT_INTERVAL
    phone_masked = user.get("phone_masked") if user else None
    is_premium = user.get("is_premium", False) if user else False
    health_status = user.get("health_status", "Not Checked") if user else "Not Checked"

    is_owner = (user_id == OWNER_ID)

    text = messages.dashboard_text(
        has_account=has_account,
        group_count=group_count,
        total_sent=total_sent,
        total_failed=total_failed,
        is_broadcasting=is_broadcasting,
        interval=interval,
        phone_masked=phone_masked,
        is_premium=is_premium,
        health_status=health_status,
    )

    markup = keyboards.dashboard_keyboard(
        is_broadcasting=is_broadcasting,
        has_account=has_account,
        is_owner=is_owner,
    )

    await _send_menu(update, context, text, markup)


# ═══════════════════════════════════════════════════════════════════════════════
#  HEALTH MONITOR
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def health_monitor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perform deep account health evaluation and display report."""
    query = update.callback_query
    await query.answer("Evaluating account health...")
    user_id = query.from_user.id

    user = await get_user(user_id)
    if not user or not user.get("session_encrypted"):
        await _send_menu(
            update, context,
            messages.error_text("You must connect your Telegram account first to evaluate health standing."),
            keyboards.back_keyboard("dashboard")
        )
        return

    client = None
    try:
        session = decrypt_session(user["session_encrypted"])
        client = await get_client_from_session(session)
        
        report = await check_account_health(user_id, client)
        
        text = messages.health_monitor_text(
            score=report["score"],
            status=report["status"],
            details=report["details"],
        )
        await _send_menu(update, context, text, keyboards.health_monitor_keyboard())

    except Exception as e:
        logger.error(f"Health monitor failed: {e}")
        await _send_menu(
            update, context,
            messages.error_text(f"Health evaluation failed: {type(e).__name__}"),
            keyboards.back_keyboard("dashboard")
        )
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
#  SMART AUTO RESPONDER
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def auto_responder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View auto-responder settings."""
    user_id = update.effective_user.id
    user = await get_user(user_id)

    enabled = user.get("auto_responder_enabled", False) if user else False
    msg = user.get("auto_responder_message", "Hello! I am currently busy.") if user else "Hello! I am currently busy."
    rules = user.get("auto_responder_rules", {}) if user else {}

    text = messages.auto_responder_text(enabled, msg, rules)
    await _send_menu(update, context, text, keyboards.auto_responder_keyboard(enabled, rules))


@require_join
async def toggle_auto_responder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle auto responder on/off."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user = await get_user(user_id)
    enabled = not user.get("auto_responder_enabled", False) if user else True
    await update_user(user_id, auto_responder_enabled=enabled)

    await auto_responder_callback(update, context)


@require_join
async def toggle_rule_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle rule: respond only during broadcast."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user = await get_user(user_id)
    rules = user.get("auto_responder_rules", {}) if user else {}
    rules["only_during_broadcast"] = not rules.get("only_during_broadcast", True)
    await update_user(user_id, auto_responder_rules=rules)

    await auto_responder_callback(update, context)


@require_join
async def toggle_rule_contacts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle rule: exclude known contacts."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user = await get_user(user_id)
    rules = user.get("auto_responder_rules", {}) if user else {}
    rules["exclude_contacts"] = not rules.get("exclude_contacts", True)
    await update_user(user_id, auto_responder_rules=rules)

    await auto_responder_callback(update, context)


@require_join
async def set_auto_responder_prompt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for new auto-responder reply message."""
    query = update.callback_query
    await query.answer()
    await _send_menu(
        update, context,
        messages.auto_responder_prompt_text(),
        keyboards.cancel_keyboard()
    )
    return WAITING_AR_MESSAGE


async def receive_auto_responder_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save auto-responder message."""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    await update_user(user_id, auto_responder_message=text)

    await update.message.reply_text(
        messages.auto_responder_saved_text(),
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("auto_responder"),
    )
    return ConversationHandler.END


def build_auto_responder_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(set_auto_responder_prompt_callback, pattern="^set_auto_responder_message$"),
        ],
        states={
            WAITING_AR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_auto_responder_message),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(end_conversation_callback, pattern="^cancel_conv$"),
            CallbackQueryHandler(end_conversation_callback, pattern="^dashboard$"),
        ],
        per_user=True, per_chat=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  LIVE STATS & PREMIUM
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def live_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View real-time user telemetry."""
    query = update.callback_query
    if query:
        await query.answer()
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        return

    from app.config import MAX_FAIL_SKIP
    groups = user.get("groups", [])
    group_fails = user.get("group_fails", {})
    live_count = sum(1 for g in groups if group_fails.get(g.replace(".", "_DOT_").replace("$", "_DOLLAR_"), 0) < MAX_FAIL_SKIP)
    paused_count = len(groups) - live_count

    text = messages.live_stats_text(user, live_count, paused_count)
    await _send_menu(update, context, text, keyboards.live_stats_keyboard())


@require_join
async def premium_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View premium membership info."""
    query = update.callback_query
    if query:
        await query.answer()
    user_id = update.effective_user.id
    user = await get_user(user_id)

    is_premium = user.get("is_premium", False) if user else False
    text = messages.premium_info_text(is_premium)
    await _send_menu(update, context, text, keyboards.premium_info_keyboard(is_premium))


@require_join
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command by displaying live stats."""
    await live_stats_callback(update, context)

