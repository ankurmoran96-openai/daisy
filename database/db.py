import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'daisy.db')

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # User Memory Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_memory (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                interaction_count INTEGER DEFAULT 0,
                memory_context TEXT
            )
        ''')
        
        # Group Settings Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS group_settings (
                chat_id INTEGER PRIMARY KEY,
                ai_enabled BOOLEAN DEFAULT 1,
                lang TEXT DEFAULT 'en'
            )
        ''')
        
        # Game Stats Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS game_stats (
                user_id INTEGER PRIMARY KEY,
                rps_wins INTEGER DEFAULT 0,
                rps_losses INTEGER DEFAULT 0,
                word_guess_wins INTEGER DEFAULT 0
            )
        ''')
        await db.commit()

async def get_user_memory(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT memory_context FROM user_memory WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""

async def update_user_memory(user_id, username, new_context):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT memory_context FROM user_memory WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            
        if row:
            # Keep a larger history context (approx 8000 chars)
            updated_context = (row[0] + "\n" + new_context)[-8000:]
            await db.execute("UPDATE user_memory SET memory_context = ?, interaction_count = interaction_count + 1 WHERE user_id = ?", (updated_context, user_id))
        else:
            await db.execute("INSERT INTO user_memory (user_id, username, interaction_count, memory_context) VALUES (?, ?, 1, ?)", (user_id, username, new_context))
        await db.commit()

async def update_game_stat(user_id, game, result):
     async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO game_stats (user_id) VALUES (?)", (user_id,))
        if game == 'rps':
            if result == 'win':
                await db.execute("UPDATE game_stats SET rps_wins = rps_wins + 1 WHERE user_id = ?", (user_id,))
            elif result == 'loss':
                await db.execute("UPDATE game_stats SET rps_losses = rps_losses + 1 WHERE user_id = ?", (user_id,))
        elif game == 'word':
            if result == 'win':
                await db.execute("UPDATE game_stats SET word_guess_wins = word_guess_wins + 1 WHERE user_id = ?", (user_id,))
        await db.commit()
