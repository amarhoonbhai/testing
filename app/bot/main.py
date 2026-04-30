"""
Kurup Ads Bot — Main application entry point.
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

# Import handlers
from app.bot.handlers.start import (
    start_handler, home_callback, check_join_callback,
    how_to_use_callback, disclaimer_callback, powered_by_callback,
)
from app.bot.handlers.dashboard import dashboard_callback
from app.bot.handlers.accounts import (
    build_add_account_conversation,
    my_accounts_callback, delete_accounts_callback,
    del_acc_callback, confirm_del_callback,
)
from app.bot.handlers.ads import (
    build_set_ad_conversation, build_set_interval_conversation,
    start_ads_callback, stop_ads_callback,
)
from app.bot.handlers.analytics import analytics_callback
from app.bot.handlers.auto_reply import (
    auto_reply_callback, ar_enable_callback,
    ar_disable_callback, build_auto_reply_conversation,
)
from app.bot.handlers.groups import (
    manage_groups_callback, view_groups_callback,
    clear_groups_callback, confirm_clear_groups_callback,
    build_add_groups_conversation,
)
from app.bot.handlers.admin import (
    admin_command, admin_callback,
    admin_users_callback, admin_health_callback,
    admin_broadcast_stats_callback,
)

logger = logging.getLogger(__name__)


def create_application():
    """Build and configure the bot application with all handlers."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ── Commands ─────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("dashboard", dashboard_callback))
    app.add_handler(CommandHandler("admin", admin_command))

    # ── Conversation Handlers (must be registered BEFORE callbacks) ──
    app.add_handler(build_add_account_conversation())
    app.add_handler(build_set_ad_conversation())
    app.add_handler(build_set_interval_conversation())
    app.add_handler(build_auto_reply_conversation())
    app.add_handler(build_add_groups_conversation())

    # ── Callback Query Handlers ──────────────────────────────
    callbacks = [
        ("^home$", home_callback),
        ("^check_join$", check_join_callback),
        ("^dashboard$", dashboard_callback),
        ("^how_to_use$", how_to_use_callback),
        ("^disclaimer$", disclaimer_callback),
        ("^powered_by$", powered_by_callback),
        ("^my_accounts$", my_accounts_callback),
        ("^delete_accounts$", delete_accounts_callback),
        ("^start_ads$", start_ads_callback),
        ("^stop_ads$", stop_ads_callback),
        ("^analytics$", analytics_callback),
        ("^auto_reply$", auto_reply_callback),
        ("^ar_enable$", ar_enable_callback),
        ("^ar_disable$", ar_disable_callback),
        # Groups
        ("^manage_groups$", manage_groups_callback),
        ("^view_groups$", view_groups_callback),
        ("^clear_groups$", clear_groups_callback),
        ("^confirm_clear_groups$", confirm_clear_groups_callback),
        # Admin (owner-only)
        ("^admin$", admin_callback),
        ("^admin_users$", admin_users_callback),
        ("^admin_health$", admin_health_callback),
        ("^admin_bstats$", admin_broadcast_stats_callback),
    ]
    for pattern, handler in callbacks:
        app.add_handler(CallbackQueryHandler(handler, pattern=pattern))

    # Dynamic callbacks with parameters
    app.add_handler(CallbackQueryHandler(del_acc_callback, pattern=r"^del_acc:"))
    app.add_handler(CallbackQueryHandler(confirm_del_callback, pattern=r"^confirm_del:"))

    return app


async def main():
    """Initialize and run the bot."""
    setup_logging("kurup_ads")
    validate_config()

    logger.info("=" * 50)
    logger.info("  KURUP ADS BOT — Starting Up")
    logger.info("  Night Mode: 12:00 AM – 5:00 AM IST")
    logger.info("  Min Interval: 1200s | Send Gap: 300s")
    logger.info("  Logs Channel: ACTIVE")
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

    logger.info("Bot is running! Press Ctrl+C to stop.")

    # Keep running until interrupted
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
