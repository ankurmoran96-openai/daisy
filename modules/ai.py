import aiohttp
import json
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from config import AI_API_KEY, AI_API_BASE, BOT_USERNAME, AI_MODEL_NAME_CHAT
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

async def google_search(query: str):
    """Searches the web using DuckDuckGo HTML."""
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    results = []
                    for a in soup.find_all('a', class_='result__snippet'):
                        results.append(a.text)
                    if not results:
                        return "No results found."
                    return "\n".join(results[:5])
                return "Failed to fetch search results."
    except Exception as e:
        return f"Search error: {e}"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current real-time date and time."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_math",
            "description": "Calculate a mathematical expression.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Search the web to find up-to-date information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'latest python version')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_game",
            "description": "When a user asks to play a game, you MUST call this tool. Available games: rps, tictactoe, wordguess, dice, slots, darts, mcq. For MCQ, available subjects are BIO, CHEM, PHYSICS, AI/ML CODING, PYTHON, C++, C. If the user doesn't specify a mode, ask them or choose 'ai' by default.",
            "parameters": {
                "type": "object",
                "properties": {
                    "game_name": {
                        "type": "string",
                        "description": "The name of the game (rps, tictactoe, wordguess, dice, slots, darts, mcq)"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["ai", "multi"],
                        "description": "Mode: ai (play with AI) or multi (multiplayer team/join)"
                    },
                    "subject": {
                        "type": "string",
                        "description": "ONLY FOR MCQ: The subject (BIO, CHEM, PHYSICS, AI/ML CODING, PYTHON, C++, C)."
                    }
                },
                "required": ["game_name", "mode"]
            }
        }
    }
]

async def generate_ai_response(prompt: str, user_memory: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
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
        "You have access to tools. ALWAYS use tools if you need to calculate math, fetch dynamic web info via google_search, or trigger games. "
        "You host interactive games: RPS, Tic-Tac-Toe, Word Guess, Dice, Slots, Darts, and MCQ. "
        "For games, you use Gemini 3 Flash in the backend via the trigger_game tool. If a user asks to play a game, use the `trigger_game` tool to launch it for them with the specified prompt instructions."
    )
    
    if user_memory:
        system_prompt += f"\n\nContext about this user:\n{user_memory}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    payload = {
        "model": AI_MODEL_NAME_CHAT,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.7
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{AI_API_BASE}/chat/completions", headers=headers, json=payload) as response:
                if response.status != 200:
                    return f"⚠️ <i>Error connecting to AI API: HTTP {response.status}</i>"
                
                data = await response.json()
                message = data['choices'][0]['message']

                if message.get("tool_calls"):
                    messages.append(message)
                    
                    for tool_call in message["tool_calls"]:
                        func_name = tool_call["function"]["name"]
                        func_args = json.loads(tool_call["function"]["arguments"])
                        
                        if func_name == "get_current_time":
                            result = get_current_time()
                        elif func_name == "calculate_math":
                            result = calculate_math(func_args.get("expression", ""))
                        elif func_name == "google_search":
                            result = await google_search(func_args.get("query", ""))
                        elif func_name == "trigger_game":
                            game = func_args.get("game_name", "").lower()
                            mode = func_args.get("mode", "ai")
                            subj = func_args.get("subject", "PYTHON")
                            from modules.games import start_game_from_ai
                            await start_game_from_ai(update, context, game, mode, subj)
                            result = f"Successfully launched {game} in {mode} mode for the user."
                        else:
                            result = "Error: Unknown tool."
                            
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": func_name,
                            "content": result
                        })

                    payload["messages"] = messages
                    async with session.post(f"{AI_API_BASE}/chat/completions", headers=headers, json=payload) as second_response:
                        if second_response.status == 200:
                            second_data = await second_response.json()
                            return second_data['choices'][0]['message']['content']
                        else:
                            return f"⚠️ <i>Error on second AI pass: HTTP {second_response.status}</i>"
                else:
                    return message.get('content', '')

    except Exception as e:
        return f"⚠️ <i>An exception occurred: {str(e)}</i>"

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered when the bot is mentioned or replied to."""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    bot_username = BOT_USERNAME or context.bot.username
    
    is_private = update.message.chat.type == "private"
    is_reply_to_bot = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    is_mentioned = bot_username and f"@{bot_username}" in text

    if not (is_private or is_reply_to_bot or is_mentioned):
        return

    prompt = text.replace(f"@{bot_username}", "").strip() if bot_username else text.strip()
    
    if not prompt:
        await update.message.reply_text("<b>Yes? How can I help you today?</b>", parse_mode=ParseMode.HTML)
        return

    user = update.effective_user
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    user_memory = await get_user_memory(user.id)
    
    response_text = await generate_ai_response(prompt, user_memory, update, context)
    
    memory_update = f"User: {prompt}\nDaisy: {response_text}"
    await update_user_memory(user.id, user.username or user.first_name, memory_update)

    if response_text:
        await update.message.reply_text(response_text, parse_mode=ParseMode.HTML)

ai_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ai_message)
