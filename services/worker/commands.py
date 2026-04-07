"""
Userbot command handlers for logged-in accounts.
Allows users to run commands from their own accounts like .ping or .stats.
"""

import time
import asyncio
import logging
from telethon import events, TelegramClient, types
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, GetDialogFiltersRequest
from core.database import get_database
from models.stats import get_account_stats
from models.group import add_group, remove_group, get_user_groups
from shared.utils import escape_markdown, parse_group_entry
from core.config import OWNER_ID

logger = logging.getLogger(__name__)

def register_userbot_handlers(client: TelegramClient):
    """Register all userbot command handlers to the client once."""
    if hasattr(client, '_userbot_handlers_registered'):
        return
    client._userbot_handlers_registered = True

    async def async_delete(event, response, delay=30):
        """Helper to delete command and response after delay."""
        await asyncio.sleep(delay)
        try:
            await event.delete()
            await response.delete()
        except:
            pass

    @client.on(events.NewMessage(pattern=r'\.ping', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def ping_handler(event):
        start = time.time()
        msg = await event.edit("🏓 **PONG**")
        end = time.time()
        ms = (end - start) * 1000
        await msg.edit(f"🏓 **PONG**\n⏱ `{ms:.2f}ms`")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.stats', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def stats_handler(event):
        # Extract metadata from client
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        
        if not user_id or not phone:
            await event.edit("❌ **Error:** Metadata missing for this session.")
            return
            
        await event.edit("⏳ **Fetching Stats...**")
        stats = await get_account_stats(user_id, phone)
        
        total_sent = stats.get("total_sent", 0)
        success_rate = stats.get("success_rate", 0)
        
        text = f"""
📊 **ACCOUNT STATS**
📞 **Phone:** `{phone}`
📤 **Total Sent:** `{total_sent}`
🎯 **Success Rate:** `{success_rate}%`
🚀 **Status:** `ACTIVE`
"""
        await event.edit(text)

    @client.on(events.NewMessage(pattern=r'\.add(\s(?s).+)?', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def bulk_add_handler(event):
        links_raw = event.pattern_match.group(1)
        if not links_raw:
            await event.edit("❌ **Usage:** `.add <link1> <link2> ...` (Supports newlines/commas)")
            return
            
        import re
        # Split by space, comma, or newline and clean
        link_list = [l.strip() for l in re.split(r'[,\s\n]+', links_raw) if l.strip()]
        total = len(link_list)
        await event.edit(f"⏳ **Processing {total} groups...**")
        
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        
        success_names = []
        failed = 0
        for i, link in enumerate(link_list):
            try:
                # Periodic progress update for large batches
                if i > 0 and i % 5 == 0:
                    await event.edit(f"⏳ **Processing...** [`{i}/{total} Done`]")

                chat_id, chat_username, title = parse_group_entry(link)
                
                # Try joining
                if "+ " in title or "@" in title:
                    if "+ " in title:
                        invite_hash = title.split("+")[1]
                        await client(ImportChatInviteRequest(invite_hash))
                    elif chat_username:
                        await client(JoinChannelRequest(chat_username))
                
                # Get actual chat title
                try:
                    chat = await client.get_entity(chat_id if chat_id else chat_username)
                    title = chat.title
                except: pass
                
                await add_group(user_id, chat_id, title, phone, chat_username=chat_username)
                success_names.append(title)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Failed to add {link}: {e}")
                failed += 1
                
        # Build "Group Added" feedback
        if success_names:
            summary = "\n".join([f"✅ **Group Added:** {name}" for name in success_names])
            if failed > 0:
                summary += f"\n❌ **Failed:** `{failed}` groups"
            msg = await event.edit(summary)
        else:
            msg = await event.edit(f"❌ **Failed to add groups.** (`{failed}` errors)")
            
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.rem_failed', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def rem_failed_handler(event):
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        
        db = get_database()
        res = await db.groups.delete_many({
            "user_id": user_id, 
            "account_phone": phone, 
            "$or": [{"enabled": False}, {"first_fail_at": {"$exists": True}}]
        })
        msg = await event.edit(f"🗑 **Cleaned!** Removed `{res.deleted_count}` failed groups.")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.info', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def info_handler(event):
        if not event.is_group:
            await event.edit("ℹ️ This command only works in groups.")
            return
            
        chat = await event.get_chat()
        perms = await client.get_permissions(chat)
        
        is_forum = getattr(chat, 'forum', False)
        can_send = perms.send_messages
        text = f"""
ℹ️ **GROUP INFO**
👤 **Title:** `{chat.title}`
🆔 **ID:** `{chat.id}`
📂 **Type:** `{'Forum' if is_forum else 'Supergroup' if event.is_channel else 'Group'}`
💬 **Can Post:** `{'✅ YES' if can_send else '❌ NO'}`
"""
        msg = await event.edit(text)
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.sync', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def sync_handler(event):
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        
        await event.edit("⏳ **Syncing all current groups & forums...**")
        count = 0
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                try:
                    # Check if we can post before syncing
                    perms = await client.get_permissions(dialog.entity)
                    if not perms.send_messages:
                        continue

                    chat_username = getattr(dialog.entity, 'username', None)
                    await add_group(user_id, dialog.id, dialog.name, phone, chat_username=chat_username)
                    count += 1
                except: pass
        
        msg = await event.edit(f"✅ **Synced!** Registered `{count}` groups (where you can post) to your account.")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.sync_folder(\s.+)?', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def sync_folder_handler(event):
        folder_name = event.pattern_match.group(1)
        if not folder_name:
            await event.edit("❌ **Usage:** `.sync_folder <name>`")
            return
            
        folder_name = folder_name.strip().lower()
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        
        await event.edit(f"⏳ **Fetching folder '{folder_name}'...**")
        
        try:
            filters = await client(GetDialogFiltersRequest())
            target_filter = None
            for f in filters:
                if hasattr(f, 'title') and f.title.lower() == folder_name:
                    target_filter = f
                    break
            
            if not target_filter:
                msg = await event.edit(f"❌ **Error:** Folder '{folder_name}' not found.")
                asyncio.create_task(async_delete(event, msg))
                return
                
            count = 0
            await event.edit(f"⏳ **Importing groups from '{target_filter.title}'...**")
            
            for peer in target_filter.include_peers:
                try:
                    entity = await client.get_entity(peer)
                    # Only add groups/channels
                    if isinstance(entity, (types.Chat, types.Channel)):
                        # Check permissions
                        perms = await client.get_permissions(entity)
                        if not perms.send_messages: continue
                        
                        chat_username = getattr(entity, 'username', None)
                        await add_group(user_id, entity.id, entity.title, phone, chat_username=chat_username)
                        count += 1
                except: continue
                
            msg = await event.edit(f"✅ **Done!** Added `{count}` groups from folder `{target_filter.title}`.")
            asyncio.create_task(async_delete(event, msg))
            
        except Exception as e:
            logger.error(f"Folder sync error: {e}")
            msg = await event.edit(f"❌ **Error:** {str(e)}")
            asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.alive', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def alive_handler(event):
        msg = await event.edit("🚀 **Kurup Userbot is active and running!**")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.id', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def id_handler(event):
        user_id = getattr(client, 'user_id', 'Unknown')
        chat_id = event.chat_id
        text = f"🆔 **User ID:** `{user_id}`\n🏘 **Chat ID:** `{chat_id}`"
        msg = await event.edit(text)
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.me', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def me_handler(event):
        me = await client.get_me()
        user_id = getattr(client, 'user_id', 'Unknown')
        phone = getattr(client, 'phone', 'Unknown')
        text = f"""
👤 **ACCOUNT INFO**
📞 **Phone:** `{phone}`
🆔 **ID:** `{user_id}`
📝 **Name:** {me.first_name} {me.last_name or ''}
🌟 **Username:** @{me.username or 'None'}
"""
        msg = await event.edit(text)
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.leave', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def leave_handler(event):
        if not event.is_group:
            msg = await event.edit("❌ You can only use `.leave` in groups.")
            asyncio.create_task(async_delete(event, msg))
            return
            
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        chat_id = event.chat_id
        
        await event.edit("👋 **Leaving group and removing from database...**")
        try:
            await remove_group(user_id, chat_id, phone=phone)
            await client.delete_dialog(chat_id)
        except Exception as e:
            logger.error(f"Error leaving group: {e}")
            
    @client.on(events.NewMessage(pattern=r'\.reply(\s.+)?', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def manual_reply_handler(event):
        reply_msg = await event.get_reply_message()
        text = event.pattern_match.group(1)
        
        if not reply_msg or not text:
            msg = await event.edit("❌ **Usage:** Reply to a message with `.reply <text>`")
            asyncio.create_task(async_delete(event, msg))
            return
            
        await event.delete() # Remove command
        await reply_msg.reply(text.strip())

    @client.on(events.NewMessage(pattern=r'\.set_reply(\s.+)?', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def set_reply_handler(event):
        text = event.pattern_match.group(1)
        if not text:
            msg = await event.edit("❌ **Usage:** `.set_reply <message>`")
            asyncio.create_task(async_delete(event, msg))
            return
            
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        
        db = get_database()
        await db.sessions.update_one(
            {"user_id": user_id, "phone": phone},
            {"$set": {"auto_reply_text": text.strip()}}
        )
        msg = await event.edit("✅ **Auto-reply message updated!**")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.on_reply', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def on_reply_handler(event):
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        
        db = get_database()
        await db.sessions.update_one(
            {"user_id": user_id, "phone": phone},
            {"$set": {"auto_reply_enabled": True}}
        )
        msg = await event.edit("✅ **Auto-responder ENABLED!**")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.off_reply', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def off_reply_handler(event):
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        
        db = get_database()
        await db.sessions.update_one(
            {"user_id": user_id, "phone": phone},
            {"$set": {"auto_reply_enabled": False}}
        )
        msg = await event.edit("❌ **Auto-responder DISABLED!**")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.help', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def help_handler(event):
        help_text = """
🛠 **USERBOT COMMANDS**
`.ping` - Check latency
`.stats` - View lifetime stats
`.alive` - Check if bot is active
`.me` - Show account info
`.id` - Get chat/user ID
`.add <links>` - Bulk add groups
`.sync` - Register all current groups
`.info` - Check group permissions
`.leave` - Leave group & remove from DB
`.reply <text>` - Reply to a message
`.set_reply <text>` - Set auto-reply msg
`.on_reply` - Enable auto-responder
`.off_reply` - Disable auto-responder
`.rem_failed` - Clean failing groups
`.help` - Show this menu

_All responses delete after 30 seconds._
"""
        msg = await event.edit(help_text)
        asyncio.create_task(async_delete(event, msg))

    logger.info(f"[{getattr(client, 'phone', 'unknown')}] Userbot commands registered")

# Auto-responder cooldown cache: (phone, sender_id) -> last_reply_time
_responder_cooldowns = {}

def register_auto_responder(client: TelegramClient):
    """Register auto-responder for incoming private messages once."""
    if hasattr(client, '_auto_responder_registered'):
        return
    client._auto_responder_registered = True
    
    @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
    async def responder_handler(event):
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        sender_id = event.sender_id
        
        if not user_id or not phone or not sender_id:
            return

        # Check cooldown (5 minutes)
        now = time.time()
        cache_key = (phone, sender_id)
        if cache_key in _responder_cooldowns:
            if now - _responder_cooldowns[cache_key] < 300:
                return

        db = get_database()
        session = await db.sessions.find_one({"user_id": user_id, "phone": phone})
        
        if session and session.get("auto_reply_enabled") and session.get("auto_reply_text"):
            _responder_cooldowns[cache_key] = now
            await event.reply(session["auto_reply_text"])
            logger.info(f"[{phone}] Auto-replied to {sender_id}")
