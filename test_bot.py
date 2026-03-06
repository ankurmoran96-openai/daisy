from telegram.ext import ApplicationBuilder, CommandHandler
import logging

logging.basicConfig(level=logging.INFO)

async def start(update, context):
    await update.message.reply_text("Bot is finally responding to /start!")

app = ApplicationBuilder().token("8633495334:AAH_ytIQiHfpgtThafybSP8kMtIGGAgcQwI").build()
app.add_handler(CommandHandler('start', start))
app.run_polling(drop_pending_updates=True)
