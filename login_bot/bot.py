"""
Login Bot entry point for Group Message Scheduler.
"""

import logging
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from core.config import LOGIN_BOT_TOKEN
from shared.bot_init import setup_logging, create_base_application, run_bot_gracefully

# Import handlers
from login_bot.handlers.start import start_handler
from login_bot.handlers.phone import (
    add_account_callback,
    receive_phone_number,
    receive_api_id,
    receive_api_hash,
    edit_phone_callback,
    cancel_callback,
)
from login_bot.handlers.otp import (
    send_otp_callback,
    resend_otp_callback,
    otp_keypad_callback,
)
from login_bot.handlers.twofa import receive_2fa_password
from login_bot.handlers.manage import (
    manage_accounts_callback,
    manage_acc_details_callback,
    disconnect_acc_callback,
    confirm_disconnect_acc_callback,
    login_home_callback
)

# Configure logging
logger = setup_logging()

def create_application() -> Application:
    """Create and configure the bot application."""
    application = create_base_application(LOGIN_BOT_TOKEN)

    # ============== Command Handlers ==============
    application.add_handler(CommandHandler("start", start_handler))

    # ============== Callback Query Handlers ==============
    patterns = [
        ("^add_account$", add_account_callback),
        ("^edit_phone$", edit_phone_callback),
        ("^cancel$", cancel_callback),
        ("^send_otp$", send_otp_callback),
        ("^resend_otp$", resend_otp_callback),
        ("^otp:", otp_keypad_callback),
        ("^manage_accounts$", manage_accounts_callback),
        ("^manage_acc:", manage_acc_details_callback),
        ("^disconnect_acc:", disconnect_acc_callback),
        ("^confirm_disc_acc:", confirm_disconnect_acc_callback),
        ("^login_home$", login_home_callback),
    ]
    
    for pattern, callback in patterns:
        application.add_handler(CallbackQueryHandler(callback, pattern=pattern))

from login_bot.handlers.login import login_conversation_handler

logger = logging.getLogger(__name__)

class LoginBotService(BaseService):
    def __init__(self):
        super().__init__("LoginBot")
        self.application = None

    async def on_start(self):
        """Startup logic for the Login Bot."""
        self.application = ApplicationBuilder().token(LOGIN_BOT_TOKEN).build()
        self.application.add_handler(start_handler)
        self.application.add_handler(login_conversation_handler)
        
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Login Bot V5 Elite started polling.")

    async def on_stop(self):
        """Cleanup logic for the Login Bot."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

if __name__ == "__main__":
    asyncio.run(LoginBotService().run_forever())
