from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from database.db import update_game_stat
import random
import asyncio

# --- Rock Paper Scissors (Interactive) ---
async def play_rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🪨 Rock", callback_data="rps_rock"),
            InlineKeyboardButton("📄 Paper", callback_data="rps_paper"),
            InlineKeyboardButton("✂️ Scissors", callback_data="rps_scissors")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "<b>🎮 Rock, Paper, Scissors!</b>\nChoose your weapon:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def rps_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_choice = query.data.split('_')[1]
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
        f"<b>🎮 Rock, Paper, Scissors!</b>\n\n"
        f"<b>You:</b> {emojis[user_choice]} {user_choice.title()}\n"
        f"<b>Daisy:</b> {emojis[bot_choice]} {bot_choice.title()}\n\n"
        f"<b>Result:</b> {result}",
        parse_mode=ParseMode.HTML
    )

# --- Word Guess (Interactive UI) ---
WORDS = ['telegram', 'python', 'daisy', 'artificial', 'intelligence', 'openai', 'developer']

async def play_wordguess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word = random.choice(WORDS)
    scrambled = "".join(random.sample(word, len(word)))
    context.chat_data['word'] = word
    
    text = (
        "<b>🧠 Word Guess Challenge!</b>\n\n"
        f"Unscramble this word: <code>{scrambled.upper()}</code>\n\n"
        "<i>Reply with <code>/guess [your_answer]</code> to win!</i>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def guess_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'word' not in context.chat_data:
        await update.message.reply_text("<b>No game active. Start one with /wordguess</b>", parse_mode=ParseMode.HTML)
        return
        
    if not context.args:
         await update.message.reply_text("<b>Usage:</b> <code>/guess [your_answer]</code>", parse_mode=ParseMode.HTML)
         return
         
    guess = context.args[0].lower()
    correct_word = context.chat_data['word']
    
    if guess == correct_word:
        await update.message.reply_text(f"<b>🎉 Correct!</b> The word was <code>{correct_word.upper()}</code>.", parse_mode=ParseMode.HTML)
        await update_game_stat(update.effective_user.id, 'word', 'win')
        del context.chat_data['word']
    else:
        await update.message.reply_text("<b>❌ Incorrect! Try again.</b>", parse_mode=ParseMode.HTML)

# --- Dice Roll (Animated) ---
async def play_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎲')
    await asyncio.sleep(4)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<b>🎲 You rolled a {msg.dice.value}!</b>",
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
        text = "<b>🎰 JACKPOT! You won! 🎉</b>"
    else:
        text = "<b>🎰 Better luck next time!</b>"
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
        text = "<b>🎯 Bullseye! Perfect shot! 🏆</b>"
    elif val >= 4:
        text = "<b>🎯 Good shot!</b>"
    else:
        text = "<b>🎯 Missed the center. Try again!</b>"
        
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
        f"<b>❌ Tic-Tac-Toe ⭕️</b>\n\n"
        f"<b>Player X:</b> {update.effective_user.first_name}\n"
        f"<b>Player O:</b> Waiting for opponent...\n\n"
        f"<i>Click the button below to join!</i>",
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
            f"<b>❌ Tic-Tac-Toe ⭕️</b>\n\n"
            f"<b>Player X:</b> {game['player_x_name']}\n"
            f"<b>Player O:</b> {game['player_o_name']}\n\n"
            f"<b>Turn:</b> ❌ {game['player_x_name']}'s turn!",
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
                text = f"<b>❌ Tic-Tac-Toe ⭕️</b>\n\nIt's a Draw! 🤝"
            else:
                winner_name = game['player_x_name'] if winner == '❌' else game['player_o_name']
                text = f"<b>❌ Tic-Tac-Toe ⭕️</b>\n\n<b>🎉 {winner_name} ({winner}) Wins!</b>"
                
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
                f"<b>❌ Tic-Tac-Toe ⭕️</b>\n\n"
                f"<b>Player X:</b> {game['player_x_name']}\n"
                f"<b>Player O:</b> {game['player_o_name']}\n\n"
                f"<b>Turn:</b> {game['turn']} {turn_name}'s turn!",
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