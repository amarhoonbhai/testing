import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from core.config import MAIN_BOT_TOKEN, WEBAPP_URL

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command – send a welcome message with a Web App button."""
    welcome_text = (
        "🚀 *Welcome to Kurup Ads Bot!*\n"
        "Manage your accounts, plans, and settings via our Web App.\n"
        "Click the button below to open it."
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Open Web App",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        ]
    ])
    await update.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

async def main() -> None:
    app = ApplicationBuilder().token(MAIN_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    logger.info("Bot started – listening for /start")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
