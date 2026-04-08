"""
Userbot command handlers for logged-in accounts.
Finalized Suite: .addgroup, .interval, .remfailed, .ping, .id, .me, .alive, .setreply, .onreply, .offreply, .sync.
"""

import time
import asyncio
import logging
import re
from telethon import events, TelegramClient, types, functions
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.chatlists import CheckChatlistInviteRequest, JoinChatlistInviteRequest

from core.database import get_database
from models.stats import get_account_stats
from models.group import add_group, remove_group, get_user_groups
from models.user import update_user_config, get_user_config
from core.utils import escape_markdown, parse_group_entry
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

    # 1. Identity & System
    @client.on(events.NewMessage(pattern=r'\.ping', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def ping_handler(event):
        start = time.time()
        msg = await event.edit("🏓 **PONG**")
        ms = (time.time() - start) * 1000
        await msg.edit(f"🏓 **PONG**\n⏱ `{ms:.2f}ms`")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.alive', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def alive_handler(event):
        msg = await event.edit("🚀 **Kurup Userbot is active.**")
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

    # 2. Status & Settings
    @client.on(events.NewMessage(pattern=r'\.interval', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def interval_handler(event):
        user_id = getattr(client, 'user_id', None)
        if not user_id: return
        config = await get_user_config(user_id)
        msg = await event.edit(f"⏱ **Interval Settings:**\n├ Cycle Wait: `{config.get('interval_min', 20)}m` (Post-Cycle)\n└ Status: `{'ACTIVE ✅' if config.get('is_active') else 'PAUSED ⏸'}`")
        asyncio.create_task(async_delete(event, msg))

    # 3. Group Management
    @client.on(events.NewMessage(pattern=r'\.addgroup(\s(?s).+)?', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def addgroup_handler(event):
        raw = event.pattern_match.group(1)
        if not raw:
            await event.edit("❌ **Usage:** `.addgroup <link/addlist_link>`")
            return
            
        links = [l.strip() for l in re.split(r'[,\s\n]+', raw) if l.strip()]
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        
        await event.edit(f"⏳ **Importing {len(links)} groups/folders...**")
        success = 0
        failed = 0
        
        for link in links:
            try:
                # FOLDER SUPPORT
                if "t.me/addlist/" in link or "telegram.me/addlist/" in link:
                    slug = link.split("/addlist/")[1].split("?")[0]
                    check = await client(CheckChatlistInviteRequest(slug=slug))
                    await client(JoinChatlistInviteRequest(slug=slug, peers=check.missing_peers))
                    
                    for peer in check.already_peers + check.missing_peers:
                        try:
                            entity = await client.get_entity(peer)
                            if isinstance(entity, (types.Chat, types.Channel)):
                                await add_group(user_id, entity.id, entity.title, phone, chat_username=getattr(entity, 'username', None))
                                success += 1
                        except: pass
                else:
                    # Individual Group
                    chat_id, chat_username, title = parse_group_entry(link)
                    if chat_username:
                        await client(JoinChannelRequest(chat_username))
                    elif "+ " in title:
                        await client(ImportChatInviteRequest(title.split("+")[1]))
                    
                    chat = await client.get_entity(chat_id if chat_id else chat_username)
                    await add_group(user_id, chat.id, chat.title, phone, chat_username=getattr(chat, 'username', None))
                    success += 1
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Addgroup failed for {link}: {e}")
                failed += 1

        msg = await event.edit(f"✅ **Import Complete!**\n📥 Added: `{success}` groups\n❌ Failed: `{failed}`")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.remfailed', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def remfailed_handler(event):
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        db = get_database()
        res = await db.groups.delete_many({
            "user_id": user_id, "account_phone": phone, 
            "$or": [{"enabled": False}, {"first_fail_at": {"$exists": True}}]
        })
        msg = await event.edit(f"🗑 **Cleaned!** Removed `{res.deleted_count}` failing groups.")
        asyncio.create_task(async_delete(event, msg))

    # 4. Bio & Reply
    @client.on(events.NewMessage(pattern=r'\.setreply(\s.+)?', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def setreply_handler(event):
        text = event.pattern_match.group(1)
        if not text:
            await event.edit("❌ **Usage:** `.setreply <msg>`")
            return
        user_id = getattr(client, 'user_id', None)
        phone = getattr(client, 'phone', None)
        db = get_database()
        await db.sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"auto_reply_text": text.strip()}})
        msg = await event.edit("✅ **Auto-reply updated!**")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.onreply', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def onreply_handler(event):
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        await get_database().sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"auto_reply_enabled": True}})
        msg = await event.edit("✅ **Auto-responder ON!**")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.offreply', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def offreply_handler(event):
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        await get_database().sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"auto_reply_enabled": False}})
        msg = await event.edit("❌ **Auto-responder OFF!**")
        asyncio.create_task(async_delete(event, msg))

    # 5. Help & Sync
    @client.on(events.NewMessage(pattern=r'\.help', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def help_handler(event):
        help_text = """
🛠 **USERBOT MASTER COMMANDS**

📁 **GROUPS**
`.addgroup <link>` - Link or Folder
`.interval` - View settings
`.remfailed` - Clean dead groups
`.sync` - Import all chats

⚙️ **AUTO-REPLY**
`.setreply <msg>` - Set response
`.onreply` / `.offreply` - Toggle

ℹ️ **IDENTITY**
`.ping` | `.id` | `.me` | `.alive`

_All responses delete after 30s._
"""
        msg = await event.edit(help_text)
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.sync', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def sync_handler(event):
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        await event.edit("⏳ **Syncing account groups...**")
        count = 0
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                try:
                    perms = await client.get_permissions(dialog.entity)
                    if perms.send_messages:
                        await add_group(user_id, dialog.id, dialog.name, phone, chat_username=getattr(dialog.entity, 'username', None))
                        count += 1
                except: pass
        msg = await event.edit(f"✅ **Synced!** Registered `{count}` groups.")
        asyncio.create_task(async_delete(event, msg))

    logger.info(f"[{getattr(client, 'phone', 'unknown')}] Master commands registered")

def register_auto_responder(client: TelegramClient):
    """Register auto-responder once."""
    if hasattr(client, '_auto_responder_registered'): return
    client._auto_responder_registered = True
    
    _responder_cooldowns = {}
    @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
    async def responder_handler(event):
        user_id, phone, sender_id = getattr(client, 'user_id', None), getattr(client, 'phone', None), event.sender_id
        if not all([user_id, phone, sender_id]): return
        now = time.time()
        if (phone, sender_id) in _responder_cooldowns and (now - _responder_cooldowns[(phone, sender_id)] < 300): return
        db = get_database()
        session = await db.sessions.find_one({"user_id": user_id, "phone": phone})
        if session and session.get("auto_reply_enabled") and session.get("auto_reply_text"):
            _responder_cooldowns[(phone, sender_id)] = now
            await event.reply(session["auto_reply_text"])
