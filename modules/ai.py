import aiohttp
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from config import AI_API_KEY, AI_API_BASE, AI_MODEL_NAME, BOT_USERNAME
from database.db import get_user_memory, update_user_memory

# --- AGENT TOOLS ---
def get_current_time():
    """Returns the current date and time."""
    return datetime.now().strftime("%A, %Y-%m-%d %I:%M %p")

def calculate_math(expression: str):
    """Safely evaluates basic math expressions."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Error: Only numbers and basic operators (+, -, *, /) are allowed."
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current real-time date and time. Call this if the user asks for the time or date."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_math",
            "description": "Calculate a mathematical expression. Call this whenever you need to do math.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The math expression (e.g., '10 * 5 + 2')"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

async def generate_ai_response(prompt: str, user_memory: str) -> str:
    """Helper function to call 3rd party AI API with Agentic Tool Use."""
    if not AI_API_KEY or not AI_API_BASE:
        return "⚠️ <i>AI Configuration is missing. Please contact the administrator.</i>"

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    current_time = get_current_time()
    system_prompt = (
        f"You are Daisy, a highly advanced, witty, and deeply intelligent Telegram group management bot powered by GPT-4o. "
        f"Current Real-Time Date & Time: {current_time}. "
        "Your personality is a mix of a professional virtual assistant and a sassy, playful companion. "
        "Your developer is @Ankxrrrr and your support channel is @brahmosai. "
        "You have complete mastery over group moderation commands and interactive mini-games. "
        "Always respond intelligently. Use HTML formatting strictly (e.g., <b>bold</b>, <i>italic</i>, <code>code</code>). "
        "You have access to tools. ALWAYS use tools if you need to calculate math or fetch dynamic info. "
        "Crucial Behavior: Always be aware of the current time provided to you. If a user messages you late at night (e.g., between 12 AM / Midnight and 5 AM), playfully or caringly ask them why they are still awake so late, incorporating the current time into your response. "
    )
    
    if user_memory:
        system_prompt += f"\n\nContext about this user:\n{user_memory}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    payload = {
        "model": AI_MODEL_NAME,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.7
    }

    try:
        async with aiohttp.ClientSession() as session:
            # First API Call
            async with session.post(f"{AI_API_BASE}/chat/completions", headers=headers, json=payload) as response:
                if response.status != 200:
                    return f"⚠️ <i>Error connecting to AI API: HTTP {response.status}</i>"
                
                data = await response.json()
                message = data['choices'][0]['message']

                # Check if the AI decided to use a tool
                if message.get("tool_calls"):
                    messages.append(message) # Add the assistant's tool call request to history
                    
                    for tool_call in message["tool_calls"]:
                        func_name = tool_call["function"]["name"]
                        func_args = json.loads(tool_call["function"]["arguments"])
                        
                        # Execute local tools
                        if func_name == "get_current_time":
                            result = get_current_time()
                        elif func_name == "calculate_math":
                            result = calculate_math(func_args.get("expression", ""))
                        else:
                            result = "Error: Unknown tool."
                            
                        # Feed the tool result back to the AI
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": func_name,
                            "content": result
                        })

                    # Second API Call (with tool results included)
                    payload["messages"] = messages
                    async with session.post(f"{AI_API_BASE}/chat/completions", headers=headers, json=payload) as second_response:
                        if second_response.status == 200:
                            second_data = await second_response.json()
                            return second_data['choices'][0]['message']['content']
                        else:
                            return f"⚠️ <i>Error on second AI pass: HTTP {second_response.status}</i>"
                else:
                    # Normal text response
                    return message.get('content', '')

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
    memory_update = f"User: {prompt}\nDaisy: {response_text}"
    await update_user_memory(user.id, user.username or user.first_name, memory_update)

    # Reply using HTML parse mode
    await update.message.reply_text(response_text, parse_mode=ParseMode.HTML)

# Setup handler
ai_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ai_message)
