from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from database.db import update_game_stat
import random
import asyncio

# --- Rock Paper Scissors (Interactive) ---
async def play_rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [
            InlineKeyboardButton("🪨 Rock", callback_data=f"rps_rock_{user_id}"),
            InlineKeyboardButton("📄 Paper", callback_data=f"rps_paper_{user_id}"),
            InlineKeyboardButton("✂️ Scissors", callback_data=f"rps_scissors_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "<blockquote><b>🎮 Rock, Paper, Scissors!</b>\nChoose your weapon:</blockquote>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def rps_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    parts = query.data.split('_')
    user_choice = parts[1]
    original_user_id = int(parts[2])
    
    if query.from_user.id != original_user_id:
        await query.answer("This is not your game!", show_alert=True)
        return
        
    await query.answer()
    
    bot_choice = random.choice(['rock', 'paper', 'scissors'])
    
    emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
    
    if user_choice == bot_choice:
        result = "It's a draw! 🤝"
    elif (user_choice == 'rock' and bot_choice == 'scissors') or \
         (user_choice == 'paper' and bot_choice == 'rock') or \
         (user_choice == 'scissors' and bot_choice == 'paper'):
        result = "You win! 🎉"
        await update_game_stat(query.from_user.id, 'rps', 'win')
    else:
        result = "I win! 😈"
        await update_game_stat(query.from_user.id, 'rps', 'loss')
        
    await query.edit_message_text(
        f"<blockquote><b>🎮 Rock, Paper, Scissors!</b>\n\n"
        f"<b>You:</b> {emojis[user_choice]} <code>{user_choice.title()}</code>\n"
        f"<b>Daisy:</b> {emojis[bot_choice]} <code>{bot_choice.title()}</code>\n\n"
        f"<b>Result:</b> {result}</blockquote>",
        parse_mode=ParseMode.HTML
    )

# --- Word Guess (Interactive UI) ---
WORDS = ['telegram', 'python', 'daisy', 'artificial', 'intelligence', 'openai', 'developer']

async def play_wordguess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word = random.choice(WORDS)
    scrambled = "".join(random.sample(word, len(word)))
    context.chat_data['word'] = word
    
    text = (
        "<blockquote><b>🧠 Word Guess Challenge!</b>\n\n"
        f"Unscramble this word: <code>{scrambled.upper()}</code>\n\n"
        "<i>Reply with <code>/guess [your_answer]</code> to win!</i></blockquote>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def guess_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'word' not in context.chat_data:
        await update.message.reply_text("<blockquote><b>No game active. Start one with /wordguess</b></blockquote>", parse_mode=ParseMode.HTML)
        return
        
    if not context.args:
         await update.message.reply_text("<blockquote><b>Usage:</b> <code>/guess [your_answer]</code></blockquote>", parse_mode=ParseMode.HTML)
         return
         
    guess = context.args[0].lower()
    correct_word = context.chat_data['word']
    
    if guess == correct_word:
        await update.message.reply_text(f"<blockquote><b>🎉 Correct!</b> The word was <code>{correct_word.upper()}</code>.</blockquote>", parse_mode=ParseMode.HTML)
        await update_game_stat(update.effective_user.id, 'word', 'win')
        del context.chat_data['word']
    else:
        await update.message.reply_text("<blockquote><b>❌ Incorrect! Try again.</b></blockquote>", parse_mode=ParseMode.HTML)

# --- Dice Roll (Animated) ---
async def play_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎲')
    await asyncio.sleep(4)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<blockquote><b>🎲 You rolled a <code>{msg.dice.value}</code>!</b></blockquote>",
        reply_to_message_id=msg.message_id,
        parse_mode=ParseMode.HTML
    )

# --- Slot Machine (Animated) ---
async def play_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎰')
    await asyncio.sleep(4)
    val = msg.dice.value
    # Jackpot combinations in Telegram slots
    if val in [1, 22, 43, 64]:
        text = "<blockquote><b>🎰 JACKPOT! You won! 🎉</b></blockquote>"
    else:
        text = "<blockquote><b>🎰 Better luck next time!</b></blockquote>"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_to_message_id=msg.message_id,
        parse_mode=ParseMode.HTML
    )

# --- Darts (Animated) ---
async def play_darts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎯')
    await asyncio.sleep(4)
    val = msg.dice.value
    if val == 6:
        text = "<blockquote><b>🎯 Bullseye! Perfect shot! 🏆</b></blockquote>"
    elif val >= 4:
        text = "<blockquote><b>🎯 Good shot!</b></blockquote>"
    else:
        text = "<blockquote><b>🎯 Missed the center. Try again!</b></blockquote>"
        
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_to_message_id=msg.message_id,
        parse_mode=ParseMode.HTML
    )

# --- Tic Tac Toe (Multiplayer) ---
def get_ttt_keyboard(board, game_id):
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            val = board[i*3 + j]
            text = " " if val == "-" else val
            row.append(InlineKeyboardButton(text, callback_data=f"tttc_{game_id}_{i*3 + j}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def check_ttt_winner(board):
    win_cond = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in win_cond:
        if board[a] != "-" and board[a] == board[b] == board[c]:
            return board[a]
    if "-" not in board:
        return "Draw"
    return None

async def play_tictactoe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_id = str(update.effective_message.id)
    
    if 'ttt_games' not in context.bot_data:
        context.bot_data['ttt_games'] = {}
        
    context.bot_data['ttt_games'][game_id] = {
        'board': ["-"] * 9,
        'player_x': update.effective_user.id,
        'player_x_name': update.effective_user.first_name,
        'player_o': None,
        'player_o_name': None,
        'turn': '❌'
    }
    
    keyboard = [[InlineKeyboardButton("🎮 Join Game (Player O)", callback_data=f"tttjoin_{game_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"<blockquote><b>❌ Tic-Tac-Toe ⭕️</b>\n\n"
        f"<b>Player X:</b> <code>{update.effective_user.first_name}</code>\n"
        f"<b>Player O:</b> <i>Waiting for opponent...</i>\n\n"
        f"<i>Click the button below to join!</i></blockquote>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def ttt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split('_')
    action = data[0]
    game_id = data[1]
    
    if 'ttt_games' not in context.bot_data or game_id not in context.bot_data['ttt_games']:
        await query.answer("This game has expired!", show_alert=True)
        return
        
    game = context.bot_data['ttt_games'][game_id]
    user_id = query.from_user.id
    
    if action == "tttjoin":
        if game['player_x'] == user_id:
            await query.answer("You are already Player X!", show_alert=True)
            return
        if game['player_o'] is not None:
            await query.answer("Someone already joined as Player O!", show_alert=True)
            return
            
        game['player_o'] = user_id
        game['player_o_name'] = query.from_user.first_name
        
        await query.message.edit_text(
            f"<blockquote><b>❌ Tic-Tac-Toe ⭕️</b>\n\n"
            f"<b>Player X:</b> <code>{game['player_x_name']}</code>\n"
            f"<b>Player O:</b> <code>{game['player_o_name']}</code>\n\n"
            f"<b>Turn:</b> ❌ <code>{game['player_x_name']}</code>'s turn!</blockquote>",
            reply_markup=get_ttt_keyboard(game['board'], game_id),
            parse_mode=ParseMode.HTML
        )
        await query.answer("You joined as Player O!")
        return

    if action == "tttc":
        pos = int(data[2])
        
        if game['player_o'] is None:
            await query.answer("Waiting for Player O to join!", show_alert=True)
            return
            
        if (game['turn'] == '❌' and user_id != game['player_x']) or \
           (game['turn'] == '⭕️' and user_id != game['player_o']):
            await query.answer("It's not your turn!", show_alert=True)
            return
            
        if game['board'][pos] != "-":
            await query.answer("That spot is taken!", show_alert=True)
            return
            
        game['board'][pos] = game['turn']
        winner = check_ttt_winner(game['board'])
        
        if winner:
            if winner == "Draw":
                text = f"<blockquote><b>❌ Tic-Tac-Toe ⭕️</b>\n\nIt's a Draw! 🤝</blockquote>"
            else:
                winner_name = game['player_x_name'] if winner == '❌' else game['player_o_name']
                text = f"<blockquote><b>❌ Tic-Tac-Toe ⭕️</b>\n\n<b>🎉 <code>{winner_name}</code> ({winner}) Wins!</b></blockquote>"
                
            await query.message.edit_text(
                text,
                reply_markup=get_ttt_keyboard(game['board'], game_id),
                parse_mode=ParseMode.HTML
            )
            del context.bot_data['ttt_games'][game_id]
        else:
            game['turn'] = '⭕️' if game['turn'] == '❌' else '❌'
            turn_name = game['player_x_name'] if game['turn'] == '❌' else game['player_o_name']
            
            await query.message.edit_text(
                f"<blockquote><b>❌ Tic-Tac-Toe ⭕️</b>\n\n"
                f"<b>Player X:</b> <code>{game['player_x_name']}</code>\n"
                f"<b>Player O:</b> <code>{game['player_o_name']}</code>\n\n"
                f"<b>Turn:</b> {game['turn']} <code>{turn_name}</code>'s turn!</blockquote>",
                reply_markup=get_ttt_keyboard(game['board'], game_id),
                parse_mode=ParseMode.HTML
            )
        await query.answer()

# Game Handlers List
handlers = [
    CommandHandler('rps', play_rps),
    CommandHandler('wordguess', play_wordguess),
    CommandHandler('guess', guess_word),
    CommandHandler('dice', play_dice),
    CommandHandler('slots', play_slots),
    CommandHandler('darts', play_darts),
    CommandHandler('tictactoe', play_tictactoe),
    CallbackQueryHandler(rps_callback, pattern='^rps_'),
    CallbackQueryHandler(ttt_callback, pattern='^ttt')
]