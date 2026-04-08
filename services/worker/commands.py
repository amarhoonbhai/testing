"""
Master Command System — Kurup Ads V5 Elite Edition.
Ports professional command logic with auto-delete and owner management.
Supports multi-group adds, folders, and chatlists.
"""

import time
import asyncio
import logging
import re
import datetime
from telethon import events, TelegramClient, types, functions
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, GetDialogFiltersRequest
from telethon.tl.functions.chatlists import CheckChatlistInviteRequest, JoinChatlistInviteRequest

from core.database import get_database
from models.stats import get_account_stats
from models.group import add_group, remove_group, get_user_groups, get_group_count
from models.user import update_user_config, get_user_config
from models.plan import get_plan, extend_plan, activate_plan
from models.settings import get_global_settings, update_global_settings
from core.utils import escape_markdown, parse_group_entry
from core.config import OWNER_ID, MIN_INTERVAL_MINUTES, MAX_GROUPS_PER_USER

# Loggers
debug_logger = logging.getLogger("commands.debug")
logger = logging.getLogger(__name__)

def register_userbot_handlers(client: TelegramClient):
    """Registers the Master Command Suite."""
    if hasattr(client, '_userbot_handlers_registered'):
        return
    client._userbot_handlers_registered = True

    # --- HELPERS ---
    async def async_delete(event, response, delay=30):
        """Auto-cleaner for bot commands."""
        await asyncio.sleep(delay)
        try:
            await event.delete()
            if hasattr(response, 'delete'): await response.delete()
        except: pass

    async def safe_respond(event, text):
        """Intelligent response logic (Edit vs Reply)."""
        try:
            if event.out: return await event.edit(text)
            else: return await event.reply(text)
        except Exception as e:
            logger.error(f"Response failed: {e}")
            return await event.respond(text)

    # --- DISPATCHER ---
    @client.on(events.NewMessage(pattern=r'\.([a-zA-Z0-9]+)(\s(?s).+)?', func=lambda e: e.out or e.sender_id == OWNER_ID))
    async def command_dispatcher(event):
        cmd = event.pattern_match.group(1).lower()
        args = (event.pattern_match.group(2) or "").strip()
        phone = getattr(client, 'phone', 'unknown')
        user_id = getattr(client, 'user_id', 0)
        
        debug_logger.critical(f"[{phone}] ⚡ MASTER CMD: .{cmd} | Args: {args[:50]}...")
        # General logger for standard output
        logger.info(f"[{phone}] Command detected: .{cmd}")

        response = None
        try:
            if cmd == "help":
                response = await handle_help(event)
            elif cmd == "ping":
                response = await handle_ping(event)
            elif cmd in ("status", "stats"):
                response = await handle_status(event)
            elif cmd == "id":
                response = await handle_id(event)
            elif cmd == "me":
                response = await handle_me(event)
            elif cmd == "groups":
                response = await handle_groups(event)
            elif cmd == "addgroup":
                response = await handle_addgroup(event, args)
            elif cmd == "addlist":
                response = await handle_addlist(event, args)
            elif cmd == "addfolder":
                response = await handle_addfolder(event, args)
            elif cmd == "folders":
                response = await handle_folders(event)
            elif cmd == "interval":
                response = await handle_interval(event, args)
            elif cmd == "copymode":
                response = await handle_copymode(event, args)
            elif cmd == "responder":
                response = await handle_responder(event, args)
            elif cmd == "remfailed":
                response = await handle_remfailed(event)
            elif cmd == "leave":
                response = await handle_leave(event)
            
            # OWNER COMMANDS
            elif cmd == "addplan" and event.sender_id == OWNER_ID:
                response = await handle_addplan(event, args)
            elif cmd == "userstatus" and event.sender_id == OWNER_ID:
                response = await handle_userstatus(event, args)
            elif cmd == "nightmode" and event.sender_id == OWNER_ID:
                response = await handle_nightmode(event, args)
            
            if response:
                asyncio.create_task(async_delete(event, response))

        except Exception as e:
            logger.error(f"Command Error: {e}", exc_info=True)
            err = await safe_respond(event, f"❌ **Error:** `{str(e)}`")
            asyncio.create_task(async_delete(event, err))

    # --- HANDLERS ---

    async def handle_help(event):
        text = (
            "🏆 **KURUP ADS ELITE — MASTER COMMANDS**\n\n"
            "👥 **GROUPS & IMPORTS**\n"
            "├ `.addgroup link1 link2` — Multi-add\n"
            "├ `.addlist <addlist_url>` — Import Folder/Chatlist\n"
            "├ `.addfolder <name>` — Import a Telegram folder\n"
            "├ `.folders` — List your local folders\n"
            "└ `.groups` | `.remfailed` | `.leave`\n\n"
            "⚙️ **CAMPAIGN SETTINGS**\n"
            "├ `.interval <min>` — Set loop delay (min: 20m)\n"
            "├ `.copymode on/off` — Use fresh copy vs forward\n"
            "└ `.responder <msg>` | `.responder off`\n\n"
            "⚡ **SYSTEM & INFO**\n"
            "└ `.status` | `.ping` | `.me` | `.id`\n\n"
            "👑 **OWNER COMMANDS**\n"
            "└ `.addplan` | `.userstatus` | `.nightmode`"
        )
        return await safe_respond(event, text)

    async def handle_ping(event):
        start = time.time()
        msg = await safe_respond(event, "🏓 **PONG**")
        ms = (time.time() - start) * 1000
        await msg.edit(f"🏓 **PONG**\n⏱ `{ms:.2f}ms` | Elite ⚡")
        return msg

    async def handle_status(event):
        user_id = getattr(client, 'user_id', 0)
        phone = getattr(client, 'phone', 'unknown')
        plan = await get_plan(user_id)
        config = await get_user_config(user_id)
        groups = await get_user_groups(user_id, phone=phone)
        enabled = len([g for g in groups if g.get('enabled', True)])
        
        plan_status = "💎 PREMIUM" if plan and plan.get('plan_type') == 'premium' else "🆓 FREE"
        text = (
            f"📊 **WORKER STATUS — {phone}**\n\n"
            f"👤 **Account:** `{phone}`\n"
            f"🏷 **Tier:** `{plan_status}`\n\n"
            f"📂 **Campaign List:**\n"
            f"├ Groups: `{enabled}/{len(groups)}` active\n"
            f"├ Interval: `{config.get('interval_min', 20)}m`\n"
            f"└ Copy Mode: `{'🟢 ON' if config.get('copy_mode') else '⚫ OFF'}`\n\n"
            f"🚀 **Worker is Active 24/7**"
        )
        return await safe_respond(event, text)

    async def handle_addgroup(event, args):
        if not args: return await safe_respond(event, "❌ Usage: `.addgroup <link1> <link2>...`")
        links = [l.strip() for l in re.split(r'[,\s\n]+', args) if l.strip()]
        user_id, phone = getattr(client, 'user_id', 0), getattr(client, 'phone', None)
        msg = await safe_respond(event, f"⏳ **Adding {len(links)} groups...**")
        success, failed = 0, 0
        for link in links:
            try:
                # Catch Chatlists in addgroup too for convenience
                if "/addlist/" in link: 
                    await handle_addlist(event, link, internal=True)
                    success += 1; continue
                
                chat_id, chat_username, title = parse_group_entry(link)
                if chat_username: await client(JoinChannelRequest(chat_username))
                elif "+ " in title: await client(ImportChatInviteRequest(title.split("+")[1]))
                chat = await client.get_entity(chat_id if chat_id else chat_username)
                await add_group(user_id, chat.id, chat.title, phone, chat_username=getattr(chat, 'username', None))
                success += 1
            except: failed += 1
        await msg.edit(f"✅ **Import Complete!**\n📥 Added: `{success}`\n❌ Failed: `{failed}`")
        return msg

    async def handle_addlist(event, args, internal=False):
        if not args: return await safe_respond(event, "❌ Usage: `.addlist <t.me/addlist/...>`")
        user_id, phone = getattr(client, 'user_id', 0), getattr(client, 'phone', None)
        msg = None if internal else await safe_respond(event, "📂 **Expanding Chatlist...**")
        try:
            slug = args.split("/addlist/")[1].split("?")[0]
            check = await client(CheckChatlistInviteRequest(slug=slug))
            await client(JoinChatlistInviteRequest(slug=slug, peers=check.missing_peers))
            success = 0
            for peer in check.already_peers + check.missing_peers:
                try:
                    entity = await client.get_entity(peer)
                    if isinstance(entity, (types.Chat, types.Channel)):
                        await add_group(user_id, entity.id, entity.title, phone, chat_username=getattr(entity, 'username', None))
                        success += 1
                except: pass
            if not internal: await msg.edit(f"✅ **Chatlist Imported!**\n📥 Added `{success}` groups from folder.")
            return msg
        except Exception as e:
            if not internal: await msg.edit(f"❌ **Chatlist Error:** `{str(e)}`")
            return msg

    async def handle_groups(event):
        user_id, phone = getattr(client, 'user_id', 0), getattr(client, 'phone', None)
        groups = await get_user_groups(user_id, phone=phone)
        if not groups: return await safe_respond(event, "📁 **No groups added yet.**")
        text = f"📁 **GROUPS — {phone}**\n\n"
        for i, g in enumerate(groups[:40], 1): # Cap at 40 for display
            status = "🟢" if g.get('enabled', True) else "🔴"
            text += f"{i}. {status} {g.get('chat_title', 'Unknown')}\n"
        if len(groups) > 40: text += f"\n... and {len(groups)-40} more groups."
        text += f"\n\n💡 Use `.remfailed` to clean your list."
        return await safe_respond(event, text)

    async def handle_interval(event, args):
        if not args.isdigit(): return await safe_respond(event, "❌ Usage: `.interval <minutes>` (min 20)")
        mins = max(20, int(args))
        user_id = getattr(client, 'user_id', 0)
        await update_user_config(user_id, interval_min=mins)
        return await safe_respond(event, f"✅ **Interval set to {mins} minutes.**")

    async def handle_copymode(event, args):
        user_id = getattr(client, 'user_id', 0)
        enable = args.lower() == "on"
        await update_user_config(user_id, copy_mode=enable)
        return await safe_respond(event, f"■ **Copy Mode {'ENABLED' if enable else 'DISABLED'}**")

    async def handle_responder(event, args):
        user_id, phone = getattr(client, 'user_id', 0), getattr(client, 'phone', None)
        if args.lower() == "off":
            await get_database().sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"auto_reply_enabled": False}})
            return await safe_respond(event, "❌ **Auto-Responder OFF**")
        await get_database().sessions.update_one({"user_id": user_id, "phone": phone}, {"$set": {"auto_reply_enabled": True, "auto_reply_text": args}})
        return await safe_respond(event, f"✅ **Auto-Responder ON!**\nMsg: `{args}`")

    # --- OWNER COMMANDS ---

    async def handle_addplan(event, args):
        try:
            parts = args.split()
            target_id = int(parts[0])
            days = int(parts[1])
            await extend_plan(target_id, days)
            return await safe_respond(event, f"✅ **PLAN UPGRADED!**\nUser: `{target_id}`\nDuration: `+{days} days`")
        except: return await safe_respond(event, "❌ Usage: `.addplan <user_id> <days>`")

    async def handle_userstatus(event, args):
        if not args.isdigit(): return await safe_respond(event, "❌ Usage: `.userstatus <user_id>`")
        target_id = int(args)
        plan = await get_plan(target_id)
        config = await get_user_config(target_id)
        text = (
            f"👤 **USER AUDIT: {target_id}**\n\n"
            f"🏷 Tier: `{plan.get('plan_type', 'None').upper()}`\n"
            f"⌛ Expiry: `{plan.get('expires_at', 'Never')}`\n"
            f"⚙️ Interval: `{config.get('interval_min', 'N/A')}m`"
        )
        return await safe_respond(event, text)

    async def handle_nightmode(event, args):
        mode = args.lower()
        if mode not in ("on", "off", "auto"): return await safe_respond(event, "❌ Use: `.nightmode on/off/auto`")
        await update_global_settings(night_mode_force=mode)
        return await safe_respond(event, f"✅ **Global Night Mode set to: {mode.upper()}**")

    # --- OTHER HANDLERS ---
    async def handle_id(event):
        return await safe_respond(event, f"🆔 **User ID:** `{getattr(client, 'user_id', 'Unknown')}`\n🏘 **Chat ID:** `{event.chat_id}`")

    async def handle_me(event):
        me = await client.get_me()
        text = f"👤 **ACCOUNT INFO**\n📞 **Phone:** `{getattr(client, 'phone', 'Unknown')}`\n🆔 **ID:** `{me.id}`\n📝 **Name:** {me.first_name} {me.last_name or ''}\n🌟 **Username:** @{me.username or 'None'}"
        return await safe_respond(event, text)

    async def handle_folders(event):
        filters = await client(GetDialogFiltersRequest())
        if not filters: return await safe_respond(event, "📁 No folders found.")
        text = "📁 **YOUR FOLDERS**\n\n"
        for f in filters:
            if hasattr(f, 'title') and f.title: text += f"▪ `{f.title}`\n"
        text += "\n💡 Use `.addfolder <name>` to import."
        return await safe_respond(event, text)

    async def handle_addfolder(event, args):
        # Implementation similar to handle_addgroup but from internal folder
        filters = await client(GetDialogFiltersRequest())
        target = next((f for f in filters if hasattr(f, 'title') and f.title.lower() == args.lower()), None)
        if not target: return await safe_respond(event, f"❌ Folder `{args}` not found.")
        peers = getattr(target, 'include_peers', [])
        user_id, phone = getattr(client, 'user_id', 0), getattr(client, 'phone', None)
        msg = await safe_respond(event, f"⏳ Found {len(peers)} items. Importing...")
        success = 0
        for peer in peers:
            try:
                entity = await client.get_entity(peer)
                if isinstance(entity, (types.Chat, types.Channel)):
                    await add_group(user_id, entity.id, entity.title, phone, chat_username=getattr(entity, 'username', None))
                    success += 1
            except: pass
        await msg.edit(f"✅ **Folder Imported!** Added `{success}` groups.")
        return msg

    async def handle_remfailed(event):
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        res = await get_database().groups.delete_many({"user_id": user_id, "account_phone": phone, "$or": [{"enabled": False}, {"first_fail_at": {"$exists": True}}]})
        return await safe_respond(event, f"🗑 **Cleaned!** Removed `{res.deleted_count}` failing groups.")

    async def handle_leave(event):
        if not event.is_group: return await safe_respond(event, "❌ Group only.")
        user_id, phone = getattr(client, 'user_id', None), getattr(client, 'phone', None)
        await safe_respond(event, "👋 **Leaving...**")
        try:
            await remove_group(user_id, event.chat_id, phone=phone)
            await client.delete_dialog(event.chat_id)
        except: pass

    logger.info(f"[{getattr(client, 'phone', 'unknown')}] MASTER COMMAND SUITE LOADED SUCCESSFULLY")

def register_auto_responder(client: TelegramClient):
    """Registers the auto-reply listener."""
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
