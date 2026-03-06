import aiohttp
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from config import AI_API_KEY, AI_API_BASE, AI_MODEL_NAME, BOT_USERNAME
from database.db import get_user_memory, update_user_memory

async def generate_ai_response(prompt: str, user_memory: str) -> str:
    """Helper function to call 3rd party AI API."""
    if not AI_API_KEY or not AI_API_BASE:
        return "⚠️ <i>AI Configuration is missing. Please contact the administrator.</i>"

    # Example payload, adjust depending on the exact 3rd party API (assuming OpenAI compatible for now)
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "You are Daisy, a highly advanced, witty, and deeply intelligent Telegram group management bot powered by GPT-4o. "
        "Your personality is a mix of a professional virtual assistant and a sassy, playful companion. You don't tolerate spam, but you love engaging with users. "
        "Your developer is @Ankxrrrr and your support channel is @brahmosai. "
        "You have complete mastery over group moderation. You can execute: /ban, /unban, /kick, /mute, /unmute, /pin, /unpin, /del, /purge, /lock, /unlock, /setadmin, /deladmin, /setgtitle, /setgdesc, and /exportlink. "
        "You also host interactive mini-games: /rps, /wordguess, /dice, /slots, /darts, and multiplayer /tictactoe. "
        "In Direct Messages (DMs), users can talk to you freely without constraints. "
        "In Groups, users MUST mention you (@daisyslaysbot) or reply to your messages to trigger a response. "
        "Always respond intelligently. If users ask how to do something, provide exact command usage. Use HTML formatting strictly (e.g., <b>bold</b>, <i>italic</i>, <code>code</code>). "
        "Remember user details and past conversation context if provided below. Keep your responses engaging, slightly sarcastic but extremely helpful!"
    )
    
    if user_memory:
        system_prompt += f"\n\nContext about this user:\n{user_memory}"

    payload = {
        "model": AI_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{AI_API_BASE}/chat/completions", headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    return f"⚠️ <i>Error connecting to AI API: HTTP {response.status}</i>"
    except Exception as e:
        return f"⚠️ <i>An exception occurred: {str(e)}</i>"


async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered when the bot is mentioned or replied to."""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    bot_username = BOT_USERNAME or context.bot.username
    
    # Check if bot is mentioned or if it's a direct message
    is_private = update.message.chat.type == "private"
    is_reply_to_bot = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    is_mentioned = bot_username and f"@{bot_username}" in text

    if not (is_private or is_reply_to_bot or is_mentioned):
        return # Do not respond if not triggered

    # Clean the prompt
    prompt = text.replace(f"@{bot_username}", "").strip() if bot_username else text.strip()
    
    if not prompt:
        await update.message.reply_text("<b>Yes? How can I help you today?</b>", parse_mode=ParseMode.HTML)
        return

    user = update.effective_user
    
    # Send typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    # Retrieve memory
    user_memory = await get_user_memory(user.id)
    
    # Generate response
    response_text = await generate_ai_response(prompt, user_memory)
    
    # Save to memory (simple summarization/saving for now)
    memory_update = f"User: {prompt}\nDaisy: {response_text[:50]}..."
    await update_user_memory(user.id, user.username or user.first_name, memory_update)

    # Reply using HTML parse mode
    await update.message.reply_text(response_text, parse_mode=ParseMode.HTML)

# Setup handler
ai_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ai_message)
