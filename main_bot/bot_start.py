import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from core.config import MAIN_BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command – send a welcome message."""
    welcome_text = (
        "🚀 *Welcome to Kurup Ads Bot!*\n\n"
        "The bot is currently being updated to the classic version.\n"
        "Please wait a moment while we restore the full interface."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def main() -> None:
    app = ApplicationBuilder().token(MAIN_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    logger.info("Bot started – listening for /start")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
