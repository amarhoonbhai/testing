"""
MAIN BOT - Kurup Ads Elite V5.
Unified service for group management, stats, and admin control.
"""

import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from core.config import MAIN_BOT_TOKEN
from core.base_service import BaseService

# Import handlers
from main_bot.handlers.start import start_handler, home_callback, check_join_callback
from main_bot.handlers.dashboard import (
    dashboard_callback, add_account_callback, toggle_send_mode_callback,
    manage_settings_callback, user_stats_callback, toggle_shuffle_ui_callback,
    toggle_copy_ui_callback, toggle_responder_ui_callback, noop_callback,
    set_interval_prompt, receive_interval, set_responder_text_prompt,
    receive_responder_text, WAITING_INTERVAL, WAITING_RESPONDER_TEXT,
)
from main_bot.handlers.plans import my_plan_callback, buy_plan_callback
from main_bot.handlers.referral import referral_callback
from main_bot.handlers.redeem import (
    redeem_code_callback, receive_redeem_code, redeem_command, WAITING_CODE,
)
from main_bot.handlers.admin import (
    admin_callback, admin_command, broadcast_command, stats_command,
    admin_stats_callback, admin_broadcast_callback, broadcast_target_callback,
    receive_broadcast_message, gen_code_callback, generate_command,
    admin_users_callback, admin_nightmode_callback, set_nightmode_callback,
    nightmode_command, admin_health_callback, WAITING_BROADCAST_MESSAGE,
    admin_upgrade_init_callback, receive_upgrade_user_id, admin_upgrade_perform_callback,
    upgrade_command, WAITING_UPGRADE_USER_ID, admin_group_stats_callback,
    admin_retry_failing_callback, admin_stop_all_callback, admin_start_all_callback,
)
from main_bot.handlers.help import help_callback, help_command, guide_callback
from main_bot.handlers.account import (
    accounts_list_callback, manage_account_callback, disconnect_account_callback,
    confirm_disconnect_callback, toggle_account_ads_callback, start_all_accounts_callback,
    stop_all_accounts_callback, manage_groups_acc_callback, add_groups_acc_prompt,
    receive_group_url_acc, grp_tgl_callback, grp_del_callback, grp_pg_callback,
    grp_clr_confirm_callback, grp_clr_done_callback, WAITING_GROUP_URL_ACC,
)
from main_bot.handlers.profile import profile_callback

logger = logging.getLogger(__name__)

class MainBotService(BaseService):
    def __init__(self):
        super().__init__("MainBot")
        self.application = None

    def create_application(self):
        """Standard handler registration."""
        app = ApplicationBuilder().token(MAIN_BOT_TOKEN).build()

        # Command Handlers
        cmds = [
            ("start", start_handler), ("admin", admin_command), ("stats", stats_command),
            ("broadcast", broadcast_command), ("help", help_command), ("redeem", redeem_command),
            ("my_plan", my_plan_callback), ("referral", referral_callback), ("profile", profile_callback),
            ("accounts", accounts_list_callback), ("dashboard", dashboard_callback),
            ("generate", generate_command), ("nightmode", nightmode_command), ("upgrade", upgrade_command)
        ]
        for cmd, h in cmds:
            app.add_handler(CommandHandler(cmd, h))

        # Conversations
        app.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(redeem_code_callback, pattern="^redeem_code$")],
            states={WAITING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_redeem_code)]},
            fallbacks=[CallbackQueryHandler(home_callback, pattern="^home$")],
            per_user=True, per_chat=True
        ))
        
        app.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(broadcast_target_callback, pattern="^broadcast:")],
            states={WAITING_BROADCAST_MESSAGE: [MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, receive_broadcast_message)]},
            fallbacks=[CallbackQueryHandler(admin_callback, pattern="^admin$")],
            per_user=True, per_chat=True
        ))

        # Callback patterns
        patterns = [
            ("^home$", home_callback), ("^check_join$", check_join_callback),
            ("^dashboard$", dashboard_callback), ("^admin$", admin_callback),
            ("^admin_stats$", admin_stats_callback), ("^admin_broadcast$", admin_broadcast_callback),
            ("^accounts_list$", accounts_list_callback), ("^manage_settings$", manage_settings_callback),
            ("^user_stats$", user_stats_callback), ("^profile$", profile_callback),
            ("^help$", help_callback), ("^guide$", guide_callback)
        ]
        # Adding more patterns for administrative and account actions (simplified)
        for p, cb in patterns:
            app.add_handler(CallbackQueryHandler(cb, pattern=p))
        
        # Catch-all for remaining account/admin callbacks
        app.add_handler(CallbackQueryHandler(manage_account_callback, pattern="^manage_account:"))
        app.add_handler(CallbackQueryHandler(disconnect_account_callback, pattern="^disconnect_account:"))
        app.add_handler(CallbackQueryHandler(confirm_disconnect_callback, pattern="^confirm_disconnect:"))
        app.add_handler(CallbackQueryHandler(manage_groups_acc_callback, pattern="^manage_groups_acc:"))
        app.add_handler(CallbackQueryHandler(grp_tgl_callback, pattern="^grp_tgl:"))
        app.add_handler(CallbackQueryHandler(grp_del_callback, pattern="^grp_del:"))
        app.add_handler(CallbackQueryHandler(grp_pg_callback, pattern="^grp_pg:"))
        
        return app

    async def on_start(self):
        self.application = self.create_application()
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        logger.info("Main Bot Elite V5 started.")

    async def on_stop(self):
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

if __name__ == "__main__":
    asyncio.run(MainBotService().run_forever())
