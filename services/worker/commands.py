"""
Userbot command handlers with DEEP DEBUGGING.
Finalized Suite: .addgroup, .interval, .remfailed, .ping, .id, .me, .alive, .leave, .sync, .test.
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

# Use a specific logger for command debugging
debug_logger = logging.getLogger("commands.debug")
logger = logging.getLogger(__name__)

def register_userbot_handlers(client: TelegramClient):
    """Register all userbot command handlers to the client once."""
    if hasattr(client, '_userbot_handlers_registered'):
        return
    client._userbot_handlers_registered = True

    phone = getattr(client, 'phone', 'unknown')
    logger.info(f"[{phone}] STARTING HANDLER REGISTRATION...")

    async def async_delete(event, response, delay=30):
        """Helper to delete command and response after delay."""
        await asyncio.sleep(delay)
        try:
            await event.delete()
            if hasattr(response, 'delete'): await response.delete()
        except: pass

    async def safe_respond(event, text):
        """Edit if outgoing (user account), Reply if incoming (Admin/Remote)."""
        phone = getattr(client, 'phone', 'unknown')
        cmd_name = event.raw_text.split()[0] if event.raw_text else "Unknown"
        sender_label = "OWNER" if event.sender_id == OWNER_ID else "SELF"
        
        debug_logger.critical(f"[{phone}] ⚡ EXECUTION: {cmd_name} | From: {sender_label} ({event.sender_id})")
        
        try:
            if event.out: return await event.edit(text)
            else: return await event.reply(text)
        except Exception as e:
            logger.error(f"Response failed: {e}")
            return await event.respond(text)

    # --- DEBUG LISTENERS ---
    @client.on(events.NewMessage(func=lambda e: e.raw_text and e.raw_text.startswith('.')))
    async def global_debug_handler(event):
        """Logs EVERY message starting with . to identify pattern failures."""
        phone = getattr(client, 'phone', 'unknown')
        is_owner = event.sender_id == OWNER_ID
        is_self = event.out
        debug_logger.critical(f"[{phone}] 🔍 RAW INPUT DETECTED: '{event.raw_text}' | Sender: {event.sender_id} | Owner: {OWNER_ID} | Match: {is_owner or is_self}")

    @client.on(events.NewMessage(pattern=r'\.test\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def test_handler(event):
        """A simple command that responds to confirm the listener is alive."""
        msg = await safe_respond(event, "🛠 **DEBUG: Listener is ALIVE!**\nRegistration: Successful ✅\nSession: Active ✅")
        asyncio.create_task(async_delete(event, msg))

    # --- STANDARD COMMANDS ---
    @client.on(events.NewMessage(pattern=r'\.ping\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def ping_handler(event):
        start = time.time()
        msg = await safe_respond(event, "🏓 **PONG**")
        ms = (time.time() - start) * 1000
        try: await msg.edit(f"🏓 **PONG**\n⏱ `{ms:.2f}ms`")
        except: pass
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.alive\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def alive_handler(event):
        msg = await safe_respond(event, "🚀 **Kurup Userbot is active.**")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.id\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def id_handler(event):
        text = f"🆔 **User ID:** `{getattr(client, 'user_id', 'Unknown')}`\n🏘 **Chat ID:** `{event.chat_id}`"
        msg = await safe_respond(event, text)
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.me\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def me_handler(event):
        me = await client.get_me()
        text = f"👤 **ACCOUNT INFO**\n📞 **Phone:** `{getattr(client, 'phone', 'Unknown')}`\n🆔 **ID:** `{me.id}`\n📝 **Name:** {me.first_name} {me.last_name or ''}\n🌟 **Username:** @{me.username or 'None'}"
        msg = await safe_respond(event, text)
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.interval\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def interval_handler(event):
        config = await get_user_config(getattr(client, 'user_id', 0))
        text = f"⏱ **Interval Settings:**\n├ Cycle Wait: `{config.get('interval_min', 20)}m` (Post-Cycle)\n└ Status: `{'ACTIVE ✅' if config.get('is_active') else 'PAUSED ⏸'}`"
        msg = await safe_respond(event, text)
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.addgroup(\s(?s).+)?', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def addgroup_handler(event):
        raw = event.pattern_match.group(1)
        if not raw:
            msg = await safe_respond(event, "❌ **Usage:** `.addgroup <link>`")
            asyncio.create_task(async_delete(event, msg)); return
            
        links = [l.strip() for l in re.split(r'[,\s\n]+', raw) if l.strip()]
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        msg = await safe_respond(event, f"⏳ **Importing {len(links)} groups/folders...**")
        success, failed = 0, 0
        for link in links:
            try:
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
                    chat_id, chat_username, title = parse_group_entry(link)
                    if chat_username: await client(JoinChannelRequest(chat_username))
                    elif "+ " in title: await client(ImportChatInviteRequest(title.split("+")[1]))
                    chat = await client.get_entity(chat_id if chat_id else chat_username)
                    await add_group(user_id, chat.id, chat.title, phone, chat_username=getattr(chat, 'username', None))
                    success += 1
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Addgroup failed for {link}: {e}")
                failed += 1
        await msg.edit(f"✅ **Import Complete!**\n📥 Added: `{success}` groups\n❌ Failed: `{failed}`")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.remfailed\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def remfailed_handler(event):
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        res = await get_database().groups.delete_many({"user_id": user_id, "account_phone": phone, "$or": [{"enabled": False}, {"first_fail_at": {"$exists": True}}]})
        msg = await safe_respond(event, f"🗑 **Cleaned!** Removed `{res.deleted_count}` failing groups.")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.leave\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def leave_handler(event):
        if not event.is_group:
            msg = await safe_respond(event, "❌ Group only.")
            asyncio.create_task(async_delete(event, msg)); return
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        await safe_respond(event, "👋 **Leaving...**")
        try:
            await remove_group(user_id, event.chat_id, phone=phone)
            await client.delete_dialog(event.chat_id)
        except Exception as e: logger.error(f"Leave failed: {e}")

    @client.on(events.NewMessage(pattern=r'\.setreply(\s.+)?', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def setreply_handler(event):
        text = event.pattern_match.group(1)
        if not text:
            msg = await safe_respond(event, "❌ Usage: `.setreply <msg>`")
            asyncio.create_task(async_delete(event, msg)); return
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        await get_database().sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"auto_reply_text": text.strip()}})
        msg = await safe_respond(event, "✅ Reply set!")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.onreply\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def onreply_handler(event):
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        await get_database().sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"auto_reply_enabled": True}})
        msg = await safe_respond(event, "✅ Responder ON!")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.offreply\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def offreply_handler(event):
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        await get_database().sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"auto_reply_enabled": False}})
        msg = await safe_respond(event, "❌ Responder OFF!")
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.help\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def help_handler(event):
        help_text = "🛠 **MASTER COMMANDS**\n\n`.addgroup` | `.sync` | `.leave` | `.remfailed`\n`.setreply` | `.onreply` | `.offreply`\n`.ping` | `.id` | `.me` | `.alive` | `.test`"
        msg = await safe_respond(event, help_text)
        asyncio.create_task(async_delete(event, msg))

    @client.on(events.NewMessage(pattern=r'\.sync\s*$', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def sync_handler(event):
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        msg = await safe_respond(event, "⏳ **Syncing...**")
        count = 0
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                try:
                    perms = await client.get_permissions(dialog.entity)
                    if perms.send_messages:
                        await add_group(user_id, dialog.id, dialog.name, phone, chat_username=getattr(dialog.entity, 'username', None))
                        count += 1
                except: pass
        await msg.edit(f"✅ **Synced!** Registered `{count}` groups.")
        asyncio.create_task(async_delete(event, msg))

    logger.info(f"[{phone}] HANDLERS REGISTERED SUCCESSFULLY")

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
