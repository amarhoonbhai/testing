"""
Group Broadcaster Bot — Main application entry point.
Registers all handlers and starts the bot.
"""

import asyncio
import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
)

from app.config import BOT_TOKEN, validate_config
from app.database.mongo import init_db, close_db
from app.utils.logger import setup_logging
from app.services.channel_logger import set_bot
from app.services import engine

# Import handlers
from app.bot.handlers.start import (
    start_handler, home_callback, check_join_callback,
    how_to_use_callback, disclaimer_callback, powered_by_callback,
    ping_handler, help_handler,
)
from app.bot.handlers.dashboard import (
    dashboard_callback, health_monitor_callback, live_stats_callback,
    premium_info_callback, auto_responder_callback, toggle_auto_responder_callback,
    build_auto_responder_conversation, toggle_rule_broadcast_callback,
    toggle_rule_contacts_callback, stats_handler,
)
from app.bot.handlers.account import (
    build_account_conversation,
    view_account_callback, disconnect_account_callback,
    confirm_disconnect_callback,
)
from app.bot.handlers.groups import (
    manage_groups_callback, view_groups_callback,
    clear_groups_callback, confirm_clear_groups_callback,
    build_add_groups_conversation, live_groups_callback,
    paused_groups_callback, reset_paused_groups_callback,
    group_diagnostics_callback, prune_dead_groups_callback,
)
from app.bot.handlers.broadcast import build_interval_conversation
from app.bot.handlers.admin import (
    admin_command, admin_callback, admin_view_all_users_callback,
    admin_toggle_premium_callback, build_admin_premium_conversation,
    admin_remote_start_callback, admin_remote_stop_callback,
    admin_remote_health_callback, admin_remote_stats_callback,
    admin_remote_wipe_callback,
)

logger = logging.getLogger(__name__)


def create_application():
    """Build and configure the bot application with all handlers."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ── Commands ─────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("dashboard", dashboard_callback))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("ping", ping_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("stats", stats_handler))

    # ── Conversation Handlers (must be registered BEFORE callbacks) ──
    app.add_handler(build_account_conversation())
    app.add_handler(build_add_groups_conversation())
    app.add_handler(build_interval_conversation())
    app.add_handler(build_auto_responder_conversation())
    app.add_handler(build_admin_premium_conversation())

    # ── Callback Query Handlers ──────────────────────────────
    callbacks = [
        ("^home$", home_callback),
        ("^check_join$", check_join_callback),
        ("^dashboard$", dashboard_callback),
        ("^how_to_use$", how_to_use_callback),
        ("^disclaimer$", disclaimer_callback),
        ("^powered_by$", powered_by_callback),
        # Account
        ("^view_account$", view_account_callback),
        ("^disconnect_account$", disconnect_account_callback),
        ("^confirm_disconnect$", confirm_disconnect_callback),
        # Groups
        ("^manage_groups$", manage_groups_callback),
        ("^view_groups$", view_groups_callback),
        ("^clear_groups$", clear_groups_callback),
        ("^confirm_clear_groups$", confirm_clear_groups_callback),
        ("^live_groups$", live_groups_callback),
        ("^paused_groups$", paused_groups_callback),
        ("^reset_paused_groups$", reset_paused_groups_callback),
        ("^group_diagnostics$", group_diagnostics_callback),
        ("^prune_dead_groups$", prune_dead_groups_callback),
        # Advanced & Premium
        ("^health_monitor$", health_monitor_callback),
        ("^live_stats$", live_stats_callback),
        ("^premium_info$", premium_info_callback),
        ("^auto_responder$", auto_responder_callback),
        ("^toggle_auto_responder$", toggle_auto_responder_callback),
        ("^toggle_rule_broadcast$", toggle_rule_broadcast_callback),
        ("^toggle_rule_contacts$", toggle_rule_contacts_callback),
        # Admin
        ("^admin$", admin_callback),
        ("^admin_view_all_users$", admin_view_all_users_callback),
        ("^grant_prem_.*$", admin_toggle_premium_callback),
        ("^revoke_prem_.*$", admin_toggle_premium_callback),
        ("^remote_start_.*$", admin_remote_start_callback),
        ("^remote_stop_.*$", admin_remote_stop_callback),
        ("^remote_health_.*$", admin_remote_health_callback),
        ("^remote_stats_.*$", admin_remote_stats_callback),
        ("^remote_wipe_.*$", admin_remote_wipe_callback),
    ]
    for pattern, handler in callbacks:
        app.add_handler(CallbackQueryHandler(handler, pattern=pattern))

    return app


async def main():
    """Initialize and run the bot."""
    setup_logging("group_broadcaster")
    validate_config()

    logger.info("=" * 50)
    logger.info("  GROUP BROADCASTER — Starting Up")
    logger.info("  Smart Batched Sending Algorithm")
    logger.info("=" * 50)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Build and start bot
    app = create_application()
    await app.initialize()

    # Set bot instance for channel logger
    set_bot(app.bot)

    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    # Auto-resume active broadcasts
    await engine.auto_resume()

    logger.info("Bot is running! Press Ctrl+C to stop.")

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        logger.info("Shutting down...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        await close_db()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
