import random
import asyncio
import json
import aiohttp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Poll
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from database.db import update_game_stat
from config import AI_API_KEY, AI_API_BASE, AI_MODEL_NAME_GAME

def get_play_again_keyboard(game: str, extra: str = ""):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Play Again (AI)", callback_data=f"gmode_{game}_ai_{extra}")],
        [InlineKeyboardButton("👥 Play Again (Multi)", callback_data=f"gmode_{game}_multi_{extra}")]
    ])

# --- AI Helper for MCQ ---
async def fetch_mcq_from_ai(subject: str) -> dict:
    prompt = (
        f"Generate a multiple choice question about {subject}. "
        "Return ONLY a valid JSON object with EXACTLY these keys: "
        "'question' (string), 'options' (list of exactly 4 string options), "
        "'answer' (integer 0-3 representing the index of the correct option). "
        "Do not use markdown formatting blocks, just raw JSON."
    )
    headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": AI_MODEL_NAME_GAME,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    default_q = {
        "question": f"Default {subject} Question: What is 2 + 2?",
        "options": ["1", "2", "3", "4"],
        "answer": 3
    }

    if not AI_API_KEY or not AI_API_BASE:
        return default_q

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{AI_API_BASE}/chat/completions", headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data['choices'][0]['message']['content'].strip()
                    if content.startswith("```json"):
                        content = content[7:-3].strip()
                    elif content.startswith("```"):
                        content = content[3:-3].strip()
                    parsed = json.loads(content)
                    if "question" in parsed and "options" in parsed and "answer" in parsed:
                        return parsed
    except Exception as e:
        print(f"Error fetching MCQ: {e}")
    return default_q

# --- Command Entry Points ---
async def cmd_rps(update: Update, context: ContextTypes.DEFAULT_TYPE): await prompt_mode(update, context, 'rps')
async def cmd_tictactoe(update: Update, context: ContextTypes.DEFAULT_TYPE): await route_game(update, context, 'tictactoe', 'multi', '')
async def cmd_wordguess(update: Update, context: ContextTypes.DEFAULT_TYPE): await prompt_mode(update, context, 'wordguess')
async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE): await prompt_mode(update, context, 'dice')
async def cmd_slots(update: Update, context: ContextTypes.DEFAULT_TYPE): await prompt_mode(update, context, 'slots')
async def cmd_darts(update: Update, context: ContextTypes.DEFAULT_TYPE): await prompt_mode(update, context, 'darts')

async def cmd_mcq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await route_game(update, context, 'mcq', 'ai', '')

async def prompt_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, game: str, extra: str = "", is_query: bool = False):
    kb = [
        [InlineKeyboardButton("🤖 Play with AI", callback_data=f"gmode_{game}_ai_{extra}")],
        [InlineKeyboardButton("👥 Multiplayer", callback_data=f"gmode_{game}_multi_{extra}")]
    ]
    text = f"<blockquote><b>🎮 {game.upper()}</b>\nChoose your game mode:</blockquote>"
    if is_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# --- AI Trigger ---
async def start_game_from_ai(update: Update, context: ContextTypes.DEFAULT_TYPE, game: str, mode: str, subject: str = ""):
    extra = subject if game == 'mcq' else ""
    await route_game(update, context, game, mode, extra, is_ai_trigger=True)

# --- Router & Lobbies ---
async def gmode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split('_')
    game = parts[1]
    mode = parts[2]
    extra = parts[3] if len(parts) > 3 else ""
    await query.answer()
    await route_game(update, context, game, mode, extra, query=query)

async def route_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game: str, mode: str, extra: str, query=None, is_ai_trigger=False):
    chat_id = query.message.chat_id if query else update.effective_chat.id
    user = query.from_user if query else update.effective_user

    if game == 'tictactoe':
        mode = 'multi'

    if mode == 'ai':
        if game == 'rps': await start_rps_ai(user, chat_id, context, query)
        elif game == 'wordguess': await start_wordguess(user, chat_id, context, query, ai_mode=True)
        elif game in ['dice', 'slots', 'darts']: await start_casino_ai(user, chat_id, context, game, query)
        elif game == 'mcq': await start_mcq(user, chat_id, context, extra, query)
    elif mode == 'multi':
        msg_id = str(query.message.message_id) if query else str(update.message.message_id)
        game_id = f"{chat_id}_{msg_id}"
        
        context.bot_data.setdefault('lobbies', {})[game_id] = {
            'game': game, 'extra': extra, 'p1': user.id, 'p1_name': user.first_name, 'p2': None, 'p2_name': None
        }
        kb = [[InlineKeyboardButton("🎮 Join Game (P2)", callback_data=f"joinlobby_{game_id}")]]
        text = f"<blockquote><b>👥 {game.upper()} Multiplayer Lobby</b>\n\nPlayer 1: {user.first_name}\nPlayer 2: Waiting...</blockquote>"
        if query: await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        else: await context.bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def joinlobby_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split('_')
    game_id = "_".join(parts[1:])
    lobby = context.bot_data.get('lobbies', {}).get(game_id)

    if not lobby: return await query.answer("Lobby expired!", show_alert=True)
    if query.from_user.id == lobby['p1']: return await query.answer("You are already P1!", show_alert=True)

    lobby['p2'] = query.from_user.id
    lobby['p2_name'] = query.from_user.first_name
    await query.answer("Joined!")

    game = lobby['game']
    extra = lobby['extra']

    if game == 'rps': await launch_rps_multi(query, context, lobby, game_id)
    elif game == 'tictactoe': await launch_ttt_multi(query, context, lobby, game_id)
    elif game in ['dice', 'slots', 'darts']: await launch_casino_multi(query, context, lobby, game, game_id)
    elif game == 'wordguess': await start_wordguess(query.from_user, query.message.chat_id, context, query, ai_mode=False)
    elif game == 'mcq': await start_mcq(query.from_user, query.message.chat_id, context, extra, query)

# --- RPS Logic ---
async def start_rps_ai(user, chat_id, context, query=None):
    kb = [[
        InlineKeyboardButton("🪨 Rock", callback_data=f"rpsai_rock_{user.id}"),
        InlineKeyboardButton("📄 Paper", callback_data=f"rpsai_paper_{user.id}"),
        InlineKeyboardButton("✂️ Scissors", callback_data=f"rpsai_scissors_{user.id}")
    ]]
    text = "<blockquote><b>🎮 RPS (vs AI)</b>\nChoose your weapon:</blockquote>"
    if query: await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    else: await context.bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def rpsai_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split('_')
    user_choice = parts[1]
    uid = int(parts[2])
    if query.from_user.id != uid: return await query.answer("Not your game!")
    
    bot_choice = random.choice(['rock', 'paper', 'scissors'])
    emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
    
    if user_choice == bot_choice: result = "It's a draw! 🤝"
    elif (user_choice == 'rock' and bot_choice == 'scissors') or \
         (user_choice == 'paper' and bot_choice == 'rock') or \
         (user_choice == 'scissors' and bot_choice == 'paper'):
        result = "You win! 🎉"
        await update_game_stat(uid, 'rps', 'win')
    else:
        result = "I win! 😈"
        await update_game_stat(uid, 'rps', 'loss')
        
    await query.edit_message_text(
        f"<blockquote><b>🎮 RPS vs AI</b>\n\n<b>You:</b> {emojis[user_choice]}\n<b>AI:</b> {emojis[bot_choice]}\n\n<b>{result}</b></blockquote>",
        reply_markup=get_play_again_keyboard('rps'),
        parse_mode=ParseMode.HTML
    )

async def launch_rps_multi(query, context, lobby, game_id):
    context.bot_data.setdefault('rps_multi', {})[game_id] = {'p1': lobby['p1'], 'p2': lobby['p2'], 'p1_choice': None, 'p2_choice': None, 'p1_name': lobby['p1_name'], 'p2_name': lobby['p2_name']}
    kb = [[
        InlineKeyboardButton("🪨 Rock", callback_data=f"rpsm_rock_{game_id}"),
        InlineKeyboardButton("📄 Paper", callback_data=f"rpsm_paper_{game_id}"),
        InlineKeyboardButton("✂️ Scissors", callback_data=f"rpsm_scissors_{game_id}")
    ]]
    text = f"<blockquote><b>🎮 RPS Multiplayer</b>\n{lobby['p1_name']} vs {lobby['p2_name']}\nBoth players, select your choice!</blockquote>"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def rpsm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split('_')
    choice = parts[1]
    game_id = "_".join(parts[2:])
    game = context.bot_data.get('rps_multi', {}).get(game_id)
    if not game: return await query.answer("Game expired!")

    uid = query.from_user.id
    if uid == game['p1']:
        game['p1_choice'] = choice
        await query.answer("Choice registered!")
    elif uid == game['p2']:
        game['p2_choice'] = choice
        await query.answer("Choice registered!")
    else:
        return await query.answer("Not your game!")

    if game['p1_choice'] and game['p2_choice']:
        c1, c2 = game['p1_choice'], game['p2_choice']
        emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
        if c1 == c2: res = "It's a draw! 🤝"
        elif (c1=='rock' and c2=='scissors') or (c1=='paper' and c2=='rock') or (c1=='scissors' and c2=='paper'): res = f"{game['p1_name']} Wins! 🎉"
        else: res = f"{game['p2_name']} Wins! 🎉"

        await query.edit_message_text(
            f"<blockquote><b>🎮 RPS Result</b>\n{game['p1_name']}: {emojis[c1]}\n{game['p2_name']}: {emojis[c2]}\n\n<b>{res}</b></blockquote>", 
            reply_markup=get_play_again_keyboard('rps'),
            parse_mode=ParseMode.HTML
        )
        del context.bot_data['rps_multi'][game_id]

# --- Tic-Tac-Toe Logic ---
def get_ttt_keyboard(board, game_id):
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            val = board[i*3 + j]
            text = " " if val == "-" else val
            row.append(InlineKeyboardButton(text, callback_data=f"tttc_{i*3+j}_{game_id}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def check_ttt_winner(board):
    win_cond = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in win_cond:
        if board[a] != "-" and board[a] == board[b] == board[c]: return board[a]
    if "-" not in board: return "Draw"
    return None

async def start_ttt_ai(user, chat_id, context, query=None):
    game_id = f"ai_{chat_id}_{user.id}_{random.randint(1000,9999)}"
    context.bot_data.setdefault('ttt_games', {})[game_id] = {
        'board': ["-"] * 9, 'player_x': user.id, 'player_x_name': user.first_name,
        'player_o': 'AI', 'player_o_name': 'Daisy AI', 'turn': '❌', 'mode': 'ai'
    }
    text = f"<blockquote><b>❌ Tic-Tac-Toe vs AI ⭕️</b>\nTurn: ❌ {user.first_name}</blockquote>"
    kb = get_ttt_keyboard(["-"]*9, game_id)
    if query: await query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else: await context.bot.send_message(chat_id, text, reply_markup=kb, parse_mode=ParseMode.HTML)

async def launch_ttt_multi(query, context, lobby, game_id):
    context.bot_data.setdefault('ttt_games', {})[game_id] = {
        'board': ["-"] * 9, 'player_x': lobby['p1'], 'player_x_name': lobby['p1_name'],
        'player_o': lobby['p2'], 'player_o_name': lobby['p2_name'], 'turn': '❌', 'mode': 'multi'
    }
    text = f"<blockquote><b>❌ Tic-Tac-Toe Multiplayer ⭕️</b>\n❌ {lobby['p1_name']} vs ⭕️ {lobby['p2_name']}\nTurn: ❌ {lobby['p1_name']}</blockquote>"
    await query.edit_message_text(text, reply_markup=get_ttt_keyboard(["-"]*9, game_id), parse_mode=ParseMode.HTML)

async def ttt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split('_')
    pos = int(parts[1])
    game_id = "_".join(parts[2:])
    
    game = context.bot_data.get('ttt_games', {}).get(game_id)
    if not game: return await query.answer("Game expired!")

    uid = query.from_user.id
    if game['turn'] == '❌' and uid != game['player_x']: return await query.answer("Not your turn!")
    if game['mode'] == 'multi' and game['turn'] == '⭕️' and uid != game['player_o']: return await query.answer("Not your turn!")

    if game['board'][pos] != "-": return await query.answer("Spot taken!")

    game['board'][pos] = game['turn']
    winner = check_ttt_winner(game['board'])

    if winner:
        await finish_ttt(query, game, game_id, winner)
        return

    game['turn'] = '⭕️' if game['turn'] == '❌' else '❌'

    if game['mode'] == 'ai' and game['turn'] == '⭕️':
        empty_spots = [i for i, v in enumerate(game['board']) if v == "-"]
        if empty_spots:
            ai_pos = random.choice(empty_spots)
            game['board'][ai_pos] = '⭕️'
            winner = check_ttt_winner(game['board'])
            if winner:
                await finish_ttt(query, game, game_id, winner)
                return
            game['turn'] = '❌'

    turn_name = game['player_x_name'] if game['turn'] == '❌' else game['player_o_name']
    await query.edit_message_text(
        f"<blockquote><b>❌ Tic-Tac-Toe ⭕️</b>\nTurn: {game['turn']} {turn_name}</blockquote>",
        reply_markup=get_ttt_keyboard(game['board'], game_id), parse_mode=ParseMode.HTML
    )

async def finish_ttt(query, game, game_id, winner):
    if winner == "Draw": text = "It's a Draw! 🤝"
    else:
        w_name = game['player_x_name'] if winner == '❌' else game['player_o_name']
        text = f"🎉 {w_name} ({winner}) Wins!"
        
    kb_list = get_ttt_keyboard(game['board'], game_id).inline_keyboard
    kb_list.append([InlineKeyboardButton("👥 Play Again (Multi)", callback_data=f"gmode_tictactoe_multi_")])
    
    await query.edit_message_text(
        f"<blockquote><b>❌ Tic-Tac-Toe ⭕️</b>\n\n{text}</blockquote>",
        reply_markup=InlineKeyboardMarkup(kb_list), parse_mode=ParseMode.HTML
    )
    del context.bot_data['ttt_games'][game_id]

# --- Casino Games ---
async def start_casino_ai(user, chat_id, context, game, query=None):
    if query: await query.edit_message_text(f"Rolling {game}...", parse_mode=ParseMode.HTML)
    emojis = {'dice': '🎲', 'slots': '🎰', 'darts': '🎯'}
    msg = await context.bot.send_dice(chat_id=chat_id, emoji=emojis[game])
    await asyncio.sleep(4)
    val = msg.dice.value
    
    if game == 'slots':
        res = "🎰 JACKPOT! 🎉" if val in [1, 22, 43, 64] else "🎰 Better luck next time!"
    elif game == 'darts':
        res = "🎯 Bullseye! 🏆" if val == 6 else ("🎯 Good shot!" if val >= 4 else "🎯 Missed center.")
    else:
        res = f"🎲 You rolled {val}!"
        
    await context.bot.send_message(chat_id, f"<blockquote><b>{res}</b></blockquote>", reply_to_message_id=msg.message_id, reply_markup=get_play_again_keyboard(game), parse_mode=ParseMode.HTML)

async def launch_casino_multi(query, context, lobby, game, game_id):
    chat_id = query.message.chat_id
    await query.edit_message_text(f"<blockquote><b>{game.upper()} Multiplayer</b>\n{lobby['p1_name']} vs {lobby['p2_name']}! Rolling...</blockquote>", parse_mode=ParseMode.HTML)
    emojis = {'dice': '🎲', 'slots': '🎰', 'darts': '🎯'}
    emoji = emojis[game]

    msg1 = await context.bot.send_dice(chat_id=chat_id, emoji=emoji)
    await asyncio.sleep(1)
    msg2 = await context.bot.send_dice(chat_id=chat_id, emoji=emoji)

    await asyncio.sleep(4)
    v1, v2 = msg1.dice.value, msg2.dice.value
    if v1 > v2: res = f"🎉 {lobby['p1_name']} wins!"
    elif v2 > v1: res = f"🎉 {lobby['p2_name']} wins!"
    else: res = "It's a draw! 🤝"

    await context.bot.send_message(chat_id, f"<blockquote>{lobby['p1_name']} rolled: {v1}\n{lobby['p2_name']} rolled: {v2}\n\n<b>{res}</b></blockquote>", reply_markup=get_play_again_keyboard(game), parse_mode=ParseMode.HTML)

# --- Wordguess ---
async def start_wordguess(user, chat_id, context, query=None, ai_mode=True):
    word = random.choice(['telegram', 'python', 'daisy', 'artificial', 'intelligence', 'openai', 'developer'])
    scrambled = "".join(random.sample(word, len(word)))
    context.chat_data['word'] = word
    mode_text = "(Solo/AI Mode)" if ai_mode else "(Multiplayer - First to guess wins!)"
    text = f"<blockquote><b>🧠 Word Guess {mode_text}</b>\nUnscramble: <code>{scrambled.upper()}</code>\nReply with <code>/guess [answer]</code></blockquote>"
    if query: await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    else: await context.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)

async def guess_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'word' not in context.chat_data: return await update.message.reply_text("No game active.")
    if not context.args: return await update.message.reply_text("Usage: /guess [word]")
    guess = context.args[0].lower()
    if guess == context.chat_data['word']:
        await update.message.reply_text(f"🎉 Correct, {update.effective_user.first_name}!", reply_markup=get_play_again_keyboard('wordguess'))
        del context.chat_data['word']
    else:
        await update.message.reply_text("❌ Incorrect!")

# --- MCQ Game ---
async def start_mcq(user, chat_id, context, subject, query=None):
    if not subject:
        subject = random.choice(["Coding", "C++", "Python", "C", "Chemistry", "Physics", "Biology", "General Knowledge"])

    if query: await query.edit_message_text(f"Generating {subject} Question via AI...", parse_mode=ParseMode.HTML)
    else: await context.bot.send_message(chat_id, f"Generating {subject} Question via AI...", parse_mode=ParseMode.HTML)

    q_data = await fetch_mcq_from_ai(subject)
    
    try:
        await context.bot.send_poll(
            chat_id=chat_id,
            question=f"[{subject}] {q_data['question']}",
            options=q_data['options'],
            type=Poll.QUIZ,
            correct_option_id=q_data['answer'],
            is_anonymous=False
        )
    except Exception as e:
        await context.bot.send_message(chat_id, "⚠️ Error sending MCQ Poll. Try again.")

# --- Handlers List ---
handlers = [
    CommandHandler('rps', cmd_rps),
    CommandHandler('tictactoe', cmd_tictactoe),
    CommandHandler('wordguess', cmd_wordguess),
    CommandHandler('dice', cmd_dice),
    CommandHandler('slots', cmd_slots),
    CommandHandler('darts', cmd_darts),
    CommandHandler('mcq', cmd_mcq),
    CommandHandler('guess', guess_word),
    CallbackQueryHandler(gmode_callback, pattern='^gmode_'),
    CallbackQueryHandler(joinlobby_callback, pattern='^joinlobby_'),
    CallbackQueryHandler(rpsai_callback, pattern='^rpsai_'),
    CallbackQueryHandler(rpsm_callback, pattern='^rpsm_'),
    CallbackQueryHandler(ttt_callback, pattern='^tttc_')
]
