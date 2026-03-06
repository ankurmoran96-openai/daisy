from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
import logging

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context):
    print(f"Received start command from: {update.effective_user.first_name}")
    await update.message.reply_text("Bot is working now!")

app = ApplicationBuilder().token("8633495334:AAH_ytIQiHfpgtThafybSP8kMtIGGAgcQwI").build()
app.add_handler(CommandHandler('start', start))
app.run_polling(drop_pending_updates=True)
