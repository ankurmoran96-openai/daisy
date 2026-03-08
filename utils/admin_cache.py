import json
import os

ADMIN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'admins.json')

def load_admins():
    if not os.path.exists(ADMIN_FILE):
        return {}
    with open(ADMIN_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_admins(data):
    with open(ADMIN_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def is_admin(chat_id, user_id):
    data = load_admins()
    chat_id = str(chat_id)
    user_id = int(user_id)
    if chat_id in data:
        return user_id in [int(x) for x in data[chat_id]]
    return False

def add_admin(chat_id, user_id):
    data = load_admins()
    chat_id = str(chat_id)
    user_id = int(user_id)
    if chat_id not in data:
        data[chat_id] = []
    if user_id not in [int(x) for x in data[chat_id]]:
        data[chat_id].append(user_id)
    save_admins(data)

def remove_admin(chat_id, user_id):
    data = load_admins()
    chat_id = str(chat_id)
    user_id = int(user_id)
    if chat_id in data:
        data[chat_id] = [x for x in data[chat_id] if int(x) != user_id]
        save_admins(data)

async def check_admin(update, context):
    """Check if the user is an admin via Cache or Telegram."""
    chat = update.effective_chat
    user_id = update.effective_user.id
    
    # Allow in private chats
    if chat.type == "private":
        return True
    
    # Check JSON cache
    if is_admin(chat.id, user_id):
        return True
        
    # Check via Telegram and update cache
    try:
        member = await chat.get_member(user_id)
        if member.status in ['creator', 'administrator']:
            add_admin(chat.id, user_id)
            return True
    except Exception as e:
        print(f"check_admin error: {e}")
        pass
        
    return False
