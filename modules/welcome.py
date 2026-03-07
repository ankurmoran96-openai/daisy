from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text(
                "<b>🌸 Hello everyone! Daisy is here!</b>\n"
                "Thank you for adding me to this group. Make me an admin to unlock my full potential and keep this group safe and fun!\n"
                "Type /help to see my commands.",
                parse_mode=ParseMode.HTML
            )
        else:
            welcome_text = (
                f"<b>🌸 Welcome to the group, <a href='tg://user?id={member.id}'>{member.first_name}</a>! 🌸</b>\n\n"
                f"We're thrilled to have you here. Feel free to chat, play games, and make yourself at home!\n\n"
                f"<i>Enjoy your stay!</i>"
            )
            await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

welcome_handler = MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member)