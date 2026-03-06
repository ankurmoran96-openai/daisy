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

def get_start_caption(username):
    return (
        f"<b>Heyy {username} 👋🏻, Daisy here!!!</b>\n"
        f"<b>Your ultimate group assistant and yapper 🫶🏻</b>\n\n"
        f"<b>What I can do?</b>\n"
        f"I am a highly advanced Group Assistant and AI Chatbot designed to seamlessly manage and elevate your Telegram communities. \n\n"
        f"<b>✨ Advanced Moderation</b>\n"
        f"Say goodbye to manual spam control! I offer an extensive suite of administrative tools—from muting and banning to mass-purging messages and managing local bot admins. Your group's security is my top priority.\n\n"
        f"<b>🧠 Intelligent AI (GPT-4o)</b>\n"
        f"I'm not just a static script. Powered by state-of-the-art AI, I can hold dynamic conversations, remember our past chats, and provide intelligent answers to your members' questions. Just mention me in the chat!\n\n"
        f"<b>🎮 Engaging Mini-Games</b>\n"
        f"Keep your community active and entertained! I host a variety of interactive games including Rock-Paper-Scissors, Word Scrambles, Casino Slots, Darts, and even Multiplayer Tic-Tac-Toe. \n\n"
        f"<b>🛠 Seamless Integration</b>\n"
        f"Adding me to your group takes seconds. Once I have admin rights, I silently work in the background, keeping things orderly and fun without being intrusive.\n\n"
        f"Use the <b>HELP</b> button below to see my full command list and discover all the ways I can help your community thrive.\n\n"
        f"<i>🎊 Enjoy your time, Hope your day is spent well. You can chat with me here in DMs too, just like how you text your bestie!</i>"
    )

HELP_CAPTION = (
    "<b>🌸 Daisy's Command Center 🌸</b>\n"
    "<i>Here is everything I can do for you!</i>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>👮‍♂️ Admin Commands (16)</b>\n"
    "<code>/ban</code> - Remove a user permanently\n"
    "<code>/unban</code> - Forgive and unban a user\n"
    "<code>/kick</code> - Remove a user (can rejoin)\n"
    "<code>/mute</code> - Restrict texting rights\n"
    "<code>/unmute</code> - Restore texting rights\n"
    "<code>/pin</code> - Highlight a message\n"
    "<code>/unpin</code> - Remove highlighted messages\n"
    "<code>/del</code> - Delete a specific message\n"
    "<code>/purge [count]</code> - Mass sweep messages\n"
    "<code>/lock</code> - Lockdown the entire chat\n"
    "<code>/unlock</code> - Lift the lockdown\n"
    "<code>/setgtitle</code> - Update group name\n"
    "<code>/setgdesc</code> - Update group bio\n"
    "<code>/exportlink</code> - Generate a fresh invite\n"
    "<code>/setadmin [tag]</code> - Assign a Bot Admin\n"
    "<code>/deladmin</code> - Revoke Bot Admin\n\n"
    "<b>🎮 Mini Games (6)</b>\n"
    "<code>/rps</code> - Interactive Rock-Paper-Scissors\n"
    "<code>/wordguess</code> - Unscramble the word\n"
    "<code>/dice</code> - Roll the lucky dice 🎲\n"
    "<code>/slots</code> - Hit the Casino jackpot 🎰\n"
    "<code>/darts</code> - Aim for the bullseye 🎯\n"
    "<code>/tictactoe</code> - Multiplayer Showdown ❌⭕️\n\n"
    "<b>🤖 AI Chat Engine</b>\n"
    "Mention me <code>@daisyslaysbot</code> in a group, or just reply to me to start chatting!"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    user_name = update.effective_user.first_name
    caption = get_start_caption(user_name)
    
    if os.path.exists(BANNER_PATH):
        with open(BANNER_PATH, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=get_start_keyboard()
            )
    else:
        await update.message.reply_text(
            text=caption,
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
        user_name = query.from_user.first_name
        caption = get_start_caption(user_name)
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=get_start_keyboard()
            )
        except Exception:
             await query.edit_message_text(
                text=caption,
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
