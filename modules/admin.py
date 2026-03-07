from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode
from utils.admin_cache import check_admin, add_admin, remove_admin
import asyncio

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("<b>Reply to a user's message to ban them.</b>", parse_mode=ParseMode.HTML)
        return
    try:
        await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=reply.from_user.id)
        await update.message.reply_text(f"<b>🔨 Banned <a href='tg://user?id={reply.from_user.id}'>{reply.from_user.first_name}</a>.</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
         await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return
    
    target_user = await resolve_target(update, context)
    if not target_user:
        await update.message.reply_text("<b>Reply to a user's message, mention them, or provide their ID to unban.</b>", parse_mode=ParseMode.HTML)
        return

    try:
        await context.bot.unban_chat_member(chat_id=update.effective_chat.id, user_id=target_user.id, only_if_banned=True)
        await update.message.reply_text(f"<b>✅ Unbanned <a href='tg://user?id={target_user.id}'>{target_user.first_name}</a>.</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
         await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
         await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
         return

    target_user = await resolve_target(update, context)
    if not target_user:
        await update.message.reply_text("<b>Reply to a user's message, mention them, or provide their ID to unmute.</b>", parse_mode=ParseMode.HTML)
        return

    permissions = ChatPermissions(
        can_send_messages=True, can_send_audios=True, can_send_documents=True,
        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
        can_add_web_page_previews=True, can_change_info=True, can_invite_users=True, can_pin_messages=True
    )
    try:
        await context.bot.restrict_chat_member(chat_id=update.effective_chat.id, user_id=target_user.id, permissions=permissions)
        await update.message.reply_text(f"<b>🔊 Unmuted <a href='tg://user?id={target_user.id}'>{target_user.first_name}</a>.</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
         await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("<b>Reply to a user's message to kick them.</b>", parse_mode=ParseMode.HTML)
        return
    try:
        await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=reply.from_user.id)
        await context.bot.unban_chat_member(chat_id=update.effective_chat.id, user_id=reply.from_user.id)
        await update.message.reply_text(f"<b>👢 Kicked <a href='tg://user?id={reply.from_user.id}'>{reply.from_user.first_name}</a>.</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
         await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def pin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("<b>Reply to a message to pin it.</b>", parse_mode=ParseMode.HTML)
        return
    try:
        await context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=reply.message_id)
        await update.message.reply_text("<b>📌 Message Pinned!</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
         await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def unpin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return
    try:
        reply = update.message.reply_to_message
        if reply:
            await context.bot.unpin_chat_message(chat_id=update.effective_chat.id, message_id=reply.message_id)
        else:
            await context.bot.unpin_all_chat_messages(chat_id=update.effective_chat.id)
        await update.message.reply_text("<b>📌 Message(s) Unpinned!</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
         await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def del_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("<b>Reply to a message to delete it.</b>", parse_mode=ParseMode.HTML)
        return
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=reply.message_id)
        await update.message.delete()
    except Exception as e:
         await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def lock_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        return
    try:
        permissions = ChatPermissions(can_send_messages=False)
        await context.bot.set_chat_permissions(chat_id=update.effective_chat.id, permissions=permissions)
        await update.message.reply_text("<b>🔒 Chat locked. Users cannot send messages.</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
         await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def unlock_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        return
    try:
        permissions = ChatPermissions(
            can_send_messages=True, can_send_audios=True, can_send_documents=True,
            can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
            can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
            can_add_web_page_previews=True, can_change_info=True, can_invite_users=True, can_pin_messages=True
        )
        await context.bot.set_chat_permissions(chat_id=update.effective_chat.id, permissions=permissions)
        await update.message.reply_text("<b>🔓 Chat unlocked. Users can send messages now.</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
         await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    chat = update.effective_chat
    user_id = update.effective_user.id
    try:
        member = await chat.get_member(user_id)
        if member.status != 'creator':
            await update.message.reply_text("<b>🚫 Only the group creator can promote bot admins!</b>", parse_mode=ParseMode.HTML)
            return
    except Exception:
        return
    
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("<b>Reply to a user with <code>/setadmin [nickname]</code> to promote them.</b>", parse_mode=ParseMode.HTML)
        return
        
    custom_title = " ".join(context.args) if context.args else "Admin"
    target_id = reply.from_user.id
    
    try:
        # Promote in Telegram Group
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target_id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_restrict_members=True,
            can_promote_members=False,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        # Set custom title
        await context.bot.set_chat_administrator_custom_title(
            chat_id=chat.id,
            user_id=target_id,
            custom_title=custom_title[:16]
        )
    except Exception as e:
        await update.message.reply_text(f"<b>⚠️ Error promoting in Telegram:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)
        
    add_admin(chat.id, target_id)
    await update.message.reply_text(f"<b>🌟 Promoted <a href='tg://user?id={target_id}'>{reply.from_user.first_name}</a> with tag <code>{custom_title[:16]}</code>!</b>", parse_mode=ParseMode.HTML)

async def del_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    chat = update.effective_chat
    user_id = update.effective_user.id
    try:
        member = await chat.get_member(user_id)
        if member.status != 'creator':
            await update.message.reply_text("<b>🚫 Only the group creator can demote bot admins!</b>", parse_mode=ParseMode.HTML)
            return
    except:
        return
    
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("<b>Reply to a user to remove them from Bot Admins.</b>", parse_mode=ParseMode.HTML)
        return
        
    remove_admin(chat.id, reply.from_user.id)
    await update.message.reply_text(f"<b>📉 Removed <a href='tg://user?id={reply.from_user.id}'>{reply.from_user.first_name}</a> from Bot Admins.</b>", parse_mode=ParseMode.HTML)


async def set_gtitle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return
    if not context.args:
        await update.message.reply_text("<b>Usage:</b> <code>/setgtitle [new title]</code>", parse_mode=ParseMode.HTML)
        return
    title = " ".join(context.args)
    try:
        await context.bot.set_chat_title(chat_id=update.effective_chat.id, title=title)
        await update.message.reply_text(f"<b>✅ Group title changed to:</b> <code>{title}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def set_gdesc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return
    desc = " ".join(context.args) if context.args else ""
    try:
        await context.bot.set_chat_description(chat_id=update.effective_chat.id, description=desc)
        await update.message.reply_text("<b>✅ Group description updated!</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def export_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return
    try:
        link = await context.bot.export_chat_invite_link(chat_id=update.effective_chat.id)
        await update.message.reply_text(f"<b>🔗 Invite Link:</b> {link}", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def purge_msgs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Purge a specified number of messages (up to 50 for safety)."""
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return
        
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("<b>Reply to a message and say <code>/purge [count]</code> to delete up to 50 messages.</b>", parse_mode=ParseMode.HTML)
        return
        
    count = 10 # Default
    if context.args and context.args[0].isdigit():
        count = int(context.args[0])
        
    count = min(count, 50) # Cap to avoid abuse/rate limits
    
    start_id = reply.message_id
    chat_id = update.effective_chat.id
    
    deleted = 0
    # Add a typing action so it feels responsive
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')
    
    # Try deleting the current command message too
    try:
        await update.message.delete()
    except: pass
    
    for i in range(count):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=start_id + i)
            deleted += 1
            await asyncio.sleep(0.1) # Small delay to avoid severe rate-limits
        except Exception:
            pass # Message might not exist or be deleted
            
    success_msg = await context.bot.send_message(chat_id=chat_id, text=f"<b>🧹 Purged {deleted} messages!</b>", parse_mode=ParseMode.HTML)
    await asyncio.sleep(3)
    try:
        await success_msg.delete()
    except: pass





import time
from datetime import timedelta

def parse_time(time_str):
    if not time_str: return None
    match = re.match(r"(\d+)([mhd|w])", time_str)
    if not match: return None
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == 'm': return timedelta(minutes=amount)
    if unit == 'h': return timedelta(hours=amount)
    if unit == 'd': return timedelta(days=amount)
    if unit == 'w': return timedelta(weeks=amount)
    return None

async def resolve_target(update, context):
    reply = update.message.reply_to_message
    if reply: return reply.from_user
    if context.args:
        # Check entities
        for ent in update.message.entities:
            if ent.type == "text_mention": return ent.user
        
        target_str = context.args[0]
        if target_str.isdigit():
            try:
                member = await context.bot.get_chat_member(update.effective_chat.id, int(target_str))
                return member.user
            except:
                return None
    return None

async def advanced_action(update, context, action_type, silent=False, delete_reply=False, is_temp=False):
    if update.effective_chat.type == "private":
        await update.message.reply_text("<b>⚠️ These commands are intended to be used in groups!</b>", parse_mode=ParseMode.HTML)
        return
    if not await check_admin(update, context):
        await update.message.reply_text("<b>🚫 You lack admin privileges!</b>", parse_mode=ParseMode.HTML)
        return

    target_user = await resolve_target(update, context)
    if not target_user:
        await update.message.reply_text("<b>Please reply to a user, provide their ID, or mention them.</b>", parse_mode=ParseMode.HTML)
        return

    until_date = None
    time_str = None
    if is_temp:
        args = context.args
        for arg in args:
            t = parse_time(arg)
            if t:
                until_date = int(time.time() + t.total_seconds())
                time_str = arg
                break
        if not until_date:
            await update.message.reply_text("<b>Please specify a valid time (e.g. 4m, 3h, 6d).</b>", parse_mode=ParseMode.HTML)
            return

    try:
        if action_type == 'ban':
            await context.bot.ban_chat_member(update.effective_chat.id, target_user.id, until_date=until_date)
            action_text = f"Banned" if not is_temp else f"Banned for {time_str}"
        elif action_type == 'mute':
            permissions = ChatPermissions(can_send_messages=False)
            await context.bot.restrict_chat_member(update.effective_chat.id, target_user.id, permissions=permissions, until_date=until_date)
            action_text = f"Muted" if not is_temp else f"Muted for {time_str}"
        elif action_type == 'kick':
            await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
            await context.bot.unban_chat_member(update.effective_chat.id, target_user.id)
            action_text = "Kicked"
            
        if delete_reply and update.message.reply_to_message:
            await update.message.reply_to_message.delete()
        if silent:
            await update.message.delete()
        else:
            await update.message.reply_text(f"<b>🔨 {action_text} <a href='tg://user?id={target_user.id}'>{target_user.first_name}</a>.</b>", parse_mode=ParseMode.HTML)

    except Exception as e:
        await update.message.reply_text(f"<b>⚠️ Error:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def cmd_ban(update, context): await advanced_action(update, context, 'ban')
async def cmd_dban(update, context): await advanced_action(update, context, 'ban', delete_reply=True)
async def cmd_sban(update, context): await advanced_action(update, context, 'ban', silent=True)
async def cmd_tban(update, context): await advanced_action(update, context, 'ban', is_temp=True)

async def cmd_mute(update, context): await advanced_action(update, context, 'mute')
async def cmd_dmute(update, context): await advanced_action(update, context, 'mute', delete_reply=True)
async def cmd_smute(update, context): await advanced_action(update, context, 'mute', silent=True)
async def cmd_tmute(update, context): await advanced_action(update, context, 'mute', is_temp=True)

async def cmd_kick(update, context): await advanced_action(update, context, 'kick')
async def cmd_dkick(update, context): await advanced_action(update, context, 'kick', delete_reply=True)
async def cmd_skick(update, context): await advanced_action(update, context, 'kick', silent=True)

async def cmd_kickme(update, context):
    if update.effective_chat.type == "private": return
    try:
        user = update.effective_user
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"<b>👢 <a href='tg://user?id={user.id}'>{user.first_name}</a> kicked themselves!</b>", parse_mode=ParseMode.HTML)
    except: pass


# Handlers List
handlers = [
    CommandHandler('ban', cmd_ban), CommandHandler('dban', cmd_dban), CommandHandler('sban', cmd_sban), CommandHandler('tban', cmd_tban), CommandHandler('unban', unban_user),
    CommandHandler('mute', cmd_mute), CommandHandler('dmute', cmd_dmute), CommandHandler('smute', cmd_smute), CommandHandler('tmute', cmd_tmute), CommandHandler('unmute', unmute_user),
    CommandHandler('kick', cmd_kick), CommandHandler('dkick', cmd_dkick), CommandHandler('skick', cmd_skick), CommandHandler('kickme', cmd_kickme), CommandHandler('pin', pin_msg),
    CommandHandler('unpin', unpin_msg), CommandHandler('del', del_msg),
    CommandHandler('lock', lock_chat), CommandHandler('unlock', unlock_chat),
    CommandHandler('setadmin', set_admin), CommandHandler('deladmin', del_admin),
    CommandHandler('setgtitle', set_gtitle), CommandHandler('setgdesc', set_gdesc),
    CommandHandler('exportlink', export_link), CommandHandler('purge', purge_msgs)
]