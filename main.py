import logging
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

from config import BOT_TOKEN, BOT_USERNAME
from database.db import init_db
from modules.admin import handlers as admin_handlers
from modules.ai import ai_handler
from modules.games import handlers as game_handlers

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BANNER_PATH = os.path.join(os.path.dirname(__file__), 'banner.jpg')

def get_start_keyboard():
    bot_username = BOT_USERNAME or "daisyslaysbot"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛠 Support", url="https://t.me/brahmosai"),
            InlineKeyboardButton("👨‍💻 Dev", url="https://t.me/Ankxrrrr")
        ],
        [
            InlineKeyboardButton("📚 HELP", callback_data="help_menu")
        ],
        [
            InlineKeyboardButton("➕ ADD ME TO GROUP", url=f"https://t.me/{bot_username}?startgroup=true")
        ]
    ])

def get_help_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="start_menu")]
    ])

START_CAPTION = (
    "<b>🌸 Welcome to Daisy!</b>\n\n"
    "<b>Powered by Advanced GPT-4o AI 🧠</b>\n\n"
    "<blockquote>"
    "I am a powerful, fully-featured group management bot. "
    "I can moderate your group, play interactive games with users, and hold intelligent conversations! "
    "Just mention me or reply to me to start chatting."
    "</blockquote>\n\n"
    "──────────────\n"
    "<i>Click the HELP button below to see everything I can do!</i>"
)

HELP_CAPTION = (
    "<b>🌸 Daisy's Command Center</b>\n"
    "──────────────\n"
    "<b>👮‍♂️ Admin Commands (16)</b>\n"
    "<code>/ban</code> - Ban a user\n"
    "<code>/unban</code> - Unban a user\n"
    "<code>/kick</code> - Kick a user\n"
    "<code>/mute</code> - Mute a user\n"
    "<code>/unmute</code> - Unmute a user\n"
    "<code>/pin</code> - Pin a message\n"
    "<code>/unpin</code> - Unpin message(s)\n"
    "<code>/del</code> - Delete a message\n"
    "<code>/purge [count]</code> - Mass delete messages\n"
    "<code>/lock</code> - Disable group texting\n"
    "<code>/unlock</code> - Enable group texting\n"
    "<code>/setgtitle</code> - Change group title\n"
    "<code>/setgdesc</code> - Change group description\n"
    "<code>/exportlink</code> - Generate invite link\n"
    "<code>/setadmin [tag]</code> - Promote Bot Admin\n"
    "<code>/deladmin</code> - Demote Bot Admin\n\n"
    "<b>🎮 Mini Games (6)</b>\n"
    "<code>/rps</code> - Interactive Rock-Paper-Scissors\n"
    "<code>/wordguess</code> - Unscramble words\n"
    "<code>/dice</code> - Roll the dice 🎲\n"
    "<code>/slots</code> - Casino slot machine 🎰\n"
    "<code>/darts</code> - Play darts 🎯\n"
    "<code>/tictactoe</code> - Multiplayer Tic-Tac-Toe ❌⭕️\n\n"
    "<b>🤖 AI Chat</b>\n"
    "Just mention me <code>@daisyslaysbot</code> in chat, or talk to me directly here!"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    if os.path.exists(BANNER_PATH):
        with open(BANNER_PATH, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=START_CAPTION,
                parse_mode=ParseMode.HTML,
                reply_markup=get_start_keyboard()
            )
    else:
        await update.message.reply_text(
            text=START_CAPTION,
            parse_mode=ParseMode.HTML,
            reply_markup=get_start_keyboard()
        )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the Help and Back inline buttons."""
    query = update.callback_query
    await query.answer()

    if query.data == "help_menu":
        try:
            # We must edit the caption since the original message is a photo
            await query.edit_message_caption(
                caption=HELP_CAPTION,
                parse_mode=ParseMode.HTML,
                reply_markup=get_help_keyboard()
            )
        except Exception:
            # Fallback if no photo
            await query.edit_message_text(
                text=HELP_CAPTION,
                parse_mode=ParseMode.HTML,
                reply_markup=get_help_keyboard()
            )
            
    elif query.data == "start_menu":
        try:
            await query.edit_message_caption(
                caption=START_CAPTION,
                parse_mode=ParseMode.HTML,
                reply_markup=get_start_keyboard()
            )
        except Exception:
             await query.edit_message_text(
                text=START_CAPTION,
                parse_mode=ParseMode.HTML,
                reply_markup=get_start_keyboard()
            )


def main():
    if not BOT_TOKEN:
        logging.error("No BOT_TOKEN provided! Exiting.")
        return

    # Build the application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Base Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^(help_menu|start_menu)$"))

    # Register Admin & Game Handlers
    for handler in admin_handlers:
        application.add_handler(handler)
        
    for handler in game_handlers:
        application.add_handler(handler)
    
    # AI Handler (Must be registered last to not block commands)
    application.add_handler(ai_handler)

    # Initialize database
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())

    # Start polling
    logging.info("Starting Daisy bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
