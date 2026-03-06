# 🌸 Daisy - Telegram Group Management Bot

<p align="center">
  <img src="banner.jpg" alt="Daisy Banner" width="600">
</p>

Daisy is a highly advanced, witty, and deeply intelligent Telegram group management bot powered by **GPT-4o**. She acts as a professional virtual assistant and a sassy, playful companion. She comes fully equipped with a vast array of administrative commands, interactive mini-games, and intelligent conversational abilities.

## ✨ Features

### 🤖 Advanced AI (Powered by GPT-4o)
*   **Context-Aware Chat:** Remembers user details and past conversations for continuous engagement.
*   **Group Mode:** Triggers only when mentioned (`@daisyslaysbot`) or replied to, keeping the chat clean.
*   **DM Mode:** Speak freely with Daisy in Direct Messages without any constraints.
*   **Smart Assistance:** Can intelligently explain her own commands and guide users on how to interact with her.

### 👮‍♂️ Group Moderation (16 Commands)
*   `/ban` - Ban a user
*   `/unban` - Unban a user
*   `/kick` - Kick a user
*   `/mute` - Mute a user
*   `/unmute` - Unmute a user
*   `/pin` - Pin a message
*   `/unpin` - Unpin message(s)
*   `/del` - Delete a message
*   `/purge [count]` - Mass delete up to 50 messages at once
*   `/lock` - Disable group texting
*   `/unlock` - Enable group texting
*   `/setgtitle` - Change group title
*   `/setgdesc` - Change group description
*   `/exportlink` - Generate invite link
*   `/setadmin [tag]` - Promote a user to Admin with a custom tag
*   `/deladmin` - Demote a Bot Admin

### 🎮 Interactive Mini-Games
*   `/rps` - Interactive Rock-Paper-Scissors with inline buttons
*   `/wordguess` - Unscramble tech-related words
*   `/dice` - Roll the dice 🎲
*   `/slots` - Casino slot machine 🎰
*   `/darts` - Play darts 🎯
*   `/tictactoe` - Full Multiplayer Tic-Tac-Toe ❌⭕️

---

## 🚀 Installation & Setup

Follow these steps to deploy your own instance of Daisy.

### 1. Clone the Repository
```bash
git clone https://github.com/ankurmoran96-openai/daisy.git
cd daisy
```

### 2. Install Requirements
Ensure you have Python 3.8+ installed. Install the necessary dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration
1. Rename `config.example.py` to `config.py`.
2. Open `config.py` and replace the placeholder values with your actual credentials:
   - `BOT_TOKEN`: Your Telegram Bot Token from [@BotFather](https://t.me/BotFather)
   - `AI_API_KEY`: Your 3rd-party AI API key
   - `AI_API_BASE`: The Base URL for the AI API
   - `BOT_USERNAME`: Your bot's username (without the @)

*Note: Your `config.py` is ignored by `.gitignore` to keep your credentials secure.*

### 4. Run the Bot
Start Daisy with the following command:
```bash
python main.py
```

---

## 🛠 Tech Stack
*   **[python-telegram-bot](https://python-telegram-bot.org/)**: For interacting with the Telegram API.
*   **[aiohttp](https://docs.aiohttp.org/)**: For asynchronous HTTP requests to the AI API.
*   **[aiosqlite](https://github.com/omnilib/aiosqlite)**: For local, asynchronous database management (storing user context and game stats).
*   **Python `dotenv`**: For secure environment variable management.

## 👨‍💻 Developer & Support
*   **Developer:** [@Ankxrrrr](https://t.me/Ankxrrrr)
*   **Support Channel:** [@brahmosai](https://t.me/brahmosai)
