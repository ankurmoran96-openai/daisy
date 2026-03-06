import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_API_BASE = os.getenv("AI_API_BASE")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "gpt-4o")
BOT_USERNAME = os.getenv("BOT_USERNAME")

if not BOT_TOKEN:
    print("WARNING: BOT_TOKEN is not set in .env")
