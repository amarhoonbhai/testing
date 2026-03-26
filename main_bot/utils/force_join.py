"""
Utility for checking mandatory channel joins.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from core.config import REQUIRED_CHANNELS

async def is_joined(user_id: int, bot: Bot) -> bool:
    """Check if user has joined all required channels."""
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
            if member.status in ["left", "kicked", "restricted"]:
                return False
        except BadRequest:
            # If bot is not admin in channel, we can't check
            continue
        except Exception:
            return False
    return True

def get_join_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard with join links and 'Check Again' button."""
    keyboard = []
    for channel in REQUIRED_CHANNELS:
        keyboard.append([InlineKeyboardButton(f"📢 Join @{channel}", url=f"https://t.me/{channel}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Check Again", callback_data="check_join")])
    return InlineKeyboardMarkup(keyboard)

async def force_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Middleware-like check for force join.
    Returns True if joined, False if not (and sends joining message).
    """
    user_id = update.effective_user.id
    bot = context.bot
    
    if await is_joined(user_id, bot):
        return True
    
    text = (
        "⚠️ **MANDATORY CHANNEL JOIN** ⚠️\n\n"
        "To use this bot, you must join our official channels first.\n"
        "This helps us keep the bot free for everyone!"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=get_join_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=get_join_keyboard(),
            parse_mode="Markdown"
        )
    return False
