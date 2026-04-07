"""
LOGIN BOT - Kurup Ads Elite V5.
Unified service for account connection and session management.
"""

import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from core.config import LOGIN_BOT_TOKEN
from core.base_service import BaseService

# Import handlers
from login_bot.handlers.start import start_handler
from login_bot.handlers.phone import (
    add_account_callback, receive_phone_number, receive_api_id,
    receive_api_hash, edit_phone_callback, cancel_callback,
)
from login_bot.handlers.otp import (
    send_otp_callback, resend_otp_callback, otp_keypad_callback,
)
from login_bot.handlers.twofa import receive_2fa_password
from login_bot.handlers.manage import (
    manage_accounts_callback, manage_acc_details_callback, disconnect_acc_callback,
    confirm_disconnect_acc_callback, login_home_callback
)
from login_bot.handlers.login import login_conversation_handler

logger = logging.getLogger(__name__)

class LoginBotService(BaseService):
    def __init__(self):
        super().__init__("LoginBot")
        self.application = None

    def create_application(self):
        """Standard handler registration."""
        app = ApplicationBuilder().token(LOGIN_BOT_TOKEN).build()
        
        # Commands
        app.add_handler(CommandHandler("start", start_handler))
        
        # Login Conversation (Highly important)
        app.add_handler(login_conversation_handler)
        
        # Callback patterns
        patterns = [
            ("^add_account$", add_account_callback), ("^edit_phone$", edit_phone_callback),
            ("^cancel$", cancel_callback), ("^send_otp$", send_otp_callback),
            ("^resend_otp$", resend_otp_callback), ("^otp:", otp_keypad_callback),
            ("^manage_accounts$", manage_accounts_callback), ("^manage_acc:", manage_acc_details_callback),
            ("^disconnect_acc:", disconnect_acc_callback), ("^confirm_disc_acc:", confirm_disconnect_acc_callback),
            ("^login_home$", login_home_callback),
        ]
        for p, cb in patterns:
            app.add_handler(CallbackQueryHandler(cb, pattern=p))
            
        return app

    async def on_start(self):
        """Startup logic for the Login Bot."""
        self.application = self.create_application()
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        logger.info("Login Bot Elite V5 started.")

    async def on_stop(self):
        """Cleanup logic for the Login Bot."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

if __name__ == "__main__":
    asyncio.run(LoginBotService().run_forever())
