"""
Start handler — /start command, welcome, guide, disclaimer.

Force-join verification runs on EVERY interaction. If a user leaves
any required channel, the bot blocks them until they rejoin.
"""

import os
import logging
import functools
from telegram import Update
from telegram.ext import ContextTypes

from app.config import REQUIRED_CHANNELS, BOT_USERNAME, BANNER_PATH
from app.database.models import upsert_user
from app.bot import messages, keyboards
from app.services.channel_logger import log_user_start

logger = logging.getLogger(__name__)

# Resolve banner path relative to project root
_BANNER_ABS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    BANNER_PATH,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  FORCE-JOIN GATE — checks on EVERY action
# ═══════════════════════════════════════════════════════════════════════════════

async def _check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user has joined ALL required channels."""
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(f"@{channel}", user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            logger.warning(f"Cannot verify membership for @{channel}")
            return False
    return True


def require_join(handler_func):
    """
    Decorator: Enforces channel membership on EVERY button press.
    If user has left any channel, blocks them with rejoin screen.
    """
    @functools.wraps(handler_func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id

        joined = await _check_membership(user_id, context)
        if not joined:
            await _send_menu(
                update, context,
                messages.force_join_text(),
                keyboards.force_join_keyboard(),
            )
            return

        return await handler_func(update, context, *args, **kwargs)
    return wrapper


# ═══════════════════════════════════════════════════════════════════════════════
#  MENU HELPER
# ═══════════════════════════════════════════════════════════════════════════════

async def _send_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup,
    *,
    with_banner: bool = False,
):
    """
    Reusable function to send or edit a menu message.
    Edits the existing message if triggered by a callback, otherwise sends new.
    """
    query = update.callback_query

    if query:
        try:
            await query.answer()
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            return
        except Exception:
            pass  # Fallback to sending new message

    # Send new message (with optional banner)
    chat_id = update.effective_chat.id

    if with_banner and os.path.exists(_BANNER_ABS):
        try:
            with open(_BANNER_ABS, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                )
                return
        except Exception:
            logger.warning("Failed to send banner image, falling back to text")

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    await upsert_user(user.id, user.username or "")

    # Log to channel
    await log_user_start(user.id, user.username or "", user.first_name or "")

    # Check force-join
    joined = await _check_membership(user.id, context)
    if not joined:
        await _send_menu(
            update, context,
            messages.force_join_text(),
            keyboards.force_join_keyboard(),
        )
        return

    await _send_menu(
        update, context,
        messages.welcome_text(
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            user_id=user.id,
            username=user.username or "",
        ),
        keyboards.start_keyboard(),
        with_banner=True,
    )


async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Verify' button click for force-join."""
    query = update.callback_query
    user = query.from_user

    joined = await _check_membership(user.id, context)
    if not joined:
        await query.answer(
            "❌ You haven't joined all channels yet. Please join and try again.",
            show_alert=True,
        )
        return

    await query.answer("✅ Verified successfully!")
    await _send_menu(
        update, context,
        messages.welcome_text(
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            user_id=user.id,
            username=user.username or "",
        ),
        keyboards.start_keyboard(),
    )


@require_join
async def home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Back' to home/start screen."""
    user = update.effective_user
    await _send_menu(
        update, context,
        messages.welcome_text(
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            user_id=user.id,
            username=user.username or "",
        ),
        keyboards.start_keyboard(),
    )


@require_join
async def how_to_use_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Guide' button."""
    await _send_menu(
        update, context,
        messages.how_to_use_text(),
        keyboards.guide_keyboard(),
    )


@require_join
async def disclaimer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Disclaimer' button."""
    await _send_menu(
        update, context,
        messages.disclaimer_text(),
        keyboards.disclaimer_keyboard(),
    )


@require_join
async def powered_by_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Powered by' button."""
    await _send_menu(
        update, context,
        messages.powered_by_text(),
        keyboards.back_keyboard("home"),
    )
