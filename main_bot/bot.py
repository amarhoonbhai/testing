"""
Main Bot entry point for Group Message Scheduler.
"""

import logging
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from core.config import MAIN_BOT_TOKEN
from shared.bot_init import setup_logging, create_base_application, run_bot_gracefully

# Import handlers
from main_bot.handlers.start import start_handler, home_callback, check_join_callback
from main_bot.handlers.dashboard import (
    dashboard_callback,
    add_account_callback,
    toggle_send_mode_callback,
    manage_groups_callback,
    manage_settings_callback,
    user_stats_callback,
    stats_command,
    toggle_shuffle_ui_callback,
    toggle_copy_ui_callback,
    toggle_responder_ui_callback,
    add_group_prompt,
    receive_group_url,
    remove_group_ui_callback,
    set_interval_prompt,
    receive_interval,
    set_responder_text_prompt,
    receive_responder_text,
    WAITING_GROUP_URL,
    WAITING_INTERVAL,
    WAITING_RESPONDER_TEXT,
)
from main_bot.handlers.plans import my_plan_callback, buy_plan_callback
from main_bot.handlers.referral import referral_callback
from main_bot.handlers.redeem import (
    redeem_code_callback,
    receive_redeem_code,
    redeem_command,
    WAITING_CODE,
)
from main_bot.handlers.admin import (
    admin_callback,
    admin_command,
    # stats_command,  # Now handled in dashboard.py for both
    broadcast_command,
    admin_stats_callback,
    admin_broadcast_callback,
    broadcast_target_callback,
    receive_broadcast_message,
    gen_code_callback,
    generate_command,
    admin_users_callback,
    admin_nightmode_callback,
    set_nightmode_callback,
    nightmode_command,
    admin_health_callback,
    WAITING_BROADCAST_MESSAGE,
    admin_upgrade_init_callback,
    receive_upgrade_user_id,
    admin_upgrade_perform_callback,
    upgrade_command,
    WAITING_UPGRADE_USER_ID,
)
from main_bot.handlers.help import help_callback, help_command, guide_callback
from main_bot.handlers.account import (
    accounts_list_callback,
    manage_account_callback,
    disconnect_account_callback,
    confirm_disconnect_callback,
)
from main_bot.handlers.profile import profile_callback

# Configure logging
logger = setup_logging()

def create_application() -> Application:
    """Create and configure the bot application."""
    application = create_base_application(MAIN_BOT_TOKEN)

    # ============== Command Handlers ==============
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("redeem", redeem_command))
    application.add_handler(CommandHandler("my_plan", my_plan_callback))
    application.add_handler(CommandHandler("referral", referral_callback))
    application.add_handler(CommandHandler("profile", profile_callback))
    application.add_handler(CommandHandler("accounts", accounts_list_callback))
    application.add_handler(CommandHandler("dashboard", dashboard_callback))
    application.add_handler(CommandHandler("generate", generate_command))
    application.add_handler(CommandHandler("nightmode", nightmode_command))
    application.add_handler(CommandHandler("upgrade", upgrade_command))

    # ============== Conversation Handlers ==============
    redeem_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(redeem_code_callback, pattern="^redeem_code$")],
        states={
            WAITING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_redeem_code)],
        },
        fallbacks=[
            CallbackQueryHandler(home_callback, pattern="^home$"),
            CallbackQueryHandler(dashboard_callback, pattern="^dashboard$"),
        ],
        per_user=True,
        per_chat=True,
    )
    application.add_handler(redeem_conv)

    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_target_callback, pattern="^broadcast:")],
        states={
            WAITING_BROADCAST_MESSAGE: [
                MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, receive_broadcast_message)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(home_callback, pattern="^home$"),
            CallbackQueryHandler(admin_callback, pattern="^admin$"),
        ],
        per_user=True,
        per_chat=True,
    )
    application.add_handler(broadcast_conv)

    upgrade_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_upgrade_init_callback, pattern="^admin_upgrade_init$")],
        states={
            WAITING_UPGRADE_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_upgrade_user_id)],
        },
        fallbacks=[
            CallbackQueryHandler(home_callback, pattern="^home$"),
            CallbackQueryHandler(admin_callback, pattern="^admin$"),
        ],
        per_user=True,
        per_chat=True,
    )
    application.add_handler(upgrade_conv)

    # Dashboard sub-conversations
    add_group_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_group_prompt, pattern="^add_group_prompt$")],
        states={
            WAITING_GROUP_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_group_url)],
        },
        fallbacks=[CallbackQueryHandler(manage_groups_callback, pattern="^manage_groups$")],
        per_user=True, per_chat=True,
    )
    application.add_handler(add_group_conv)

    set_interval_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_interval_prompt, pattern="^set_interval_prompt$")],
        states={
            WAITING_INTERVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_interval)],
        },
        fallbacks=[CallbackQueryHandler(manage_settings_callback, pattern="^manage_settings$")],
        per_user=True, per_chat=True,
    )
    application.add_handler(set_interval_conv)

    set_responder_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_responder_text_prompt, pattern="^set_responder_text_prompt$")],
        states={
            WAITING_RESPONDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_responder_text)],
        },
        fallbacks=[CallbackQueryHandler(manage_settings_callback, pattern="^manage_settings$")],
        per_user=True, per_chat=True,
    )
    application.add_handler(set_responder_conv)

    # ============== Callback Query Handlers ==============
    patterns = [
        ("^home$", home_callback),
        ("^check_join$", check_join_callback),
        ("^dashboard$", dashboard_callback),
        ("^toggle_send_mode$", toggle_send_mode_callback),
        ("^add_account$", add_account_callback),
        ("^help$", help_callback),
        ("^guide$", guide_callback),
        ("^my_plan$", my_plan_callback),
        ("^referral$", referral_callback),
        ("^profile$", profile_callback),
        ("^manage_groups$", manage_groups_callback),
        ("^manage_settings$", manage_settings_callback),
        ("^user_stats$", user_stats_callback),
        ("^toggle_shuffle_ui$", toggle_shuffle_ui_callback),
        ("^toggle_copy_ui$", toggle_copy_ui_callback),
        ("^toggle_responder_ui$", toggle_responder_ui_callback),
        ("^remove_group_ui:", remove_group_ui_callback),
        ("^admin$", admin_callback),
        ("^admin_stats$", admin_stats_callback),
        ("^admin_broadcast$", admin_broadcast_callback),
        ("^gen_code:", gen_code_callback),
        ("^admin_users$", admin_users_callback),
        ("^accounts_list$", accounts_list_callback),
        ("^manage_account:", manage_account_callback),
        ("^disconnect_account:", disconnect_account_callback),
        ("^confirm_disconnect:", confirm_disconnect_callback),
        ("^admin_nightmode$", admin_nightmode_callback),
        ("^set_nightmode:", set_nightmode_callback),
        ("^admin_health$", admin_health_callback),
        ("^adm_upgr:", admin_upgrade_perform_callback),
        ("^buy_plan:", buy_plan_callback),
    ]
    
    for pattern, callback in patterns:
        application.add_handler(CallbackQueryHandler(callback, pattern=pattern))

    return application

async def main():
    """Start the bot."""
    print("=" * 50)
    print("Group Message Scheduler - Main Bot V3.3")
    print("=" * 50)

    application = create_application()
    await run_bot_gracefully(application, "Main Bot")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
