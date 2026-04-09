"""
Command handler for processing dot commands from user's Saved Messages.
Commands are sent by user to their own Saved Messages and processed by Worker.
"""

import logging
import re
from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    ChannelInvalidError,
    UsernameNotOccupiedError,
    UsernameInvalidError,
    InviteHashInvalidError,
    InviteHashExpiredError,
)
from telethon.tl.types import InputPeerSelf, InputPeerChannel, InputPeerChat
from telethon.tl.functions.messages import GetDialogFiltersRequest

from core.config import MAX_GROUPS_PER_USER, MIN_INTERVAL_MINUTES
from models.session import get_session
from models.user import get_user_config, update_user_config
from models.group import get_user_groups, add_group, remove_group, get_group_count, toggle_group

logger = logging.getLogger(__name__)


async def process_command(client: TelegramClient, user_id: int, message) -> bool:
    """
    Process a dot command from user's Saved Messages.
    Returns True if the message was a command and was processed.
    """
    if not message.text:
        return False
    
    text = message.text.strip()
    
    if not text.startswith("."):
        return False
    
    cmd = text.lower().split()[0]
    
    try:
        if cmd == ".help":
            await handle_help(client, user_id, message)
            return True
        elif cmd == ".status" or cmd == ".stats":
            await handle_status(client, user_id, message, text)
            return True
        elif cmd == ".rmpaused":
            await handle_rmpaused(client, user_id, message)
            return True
        elif cmd == ".groups":
            await handle_groups(client, user_id, message)
            return True
        elif cmd == ".addgroup":
            await handle_addgroup(client, user_id, message, text)
            return True
        elif cmd == ".rmgroup":
            await handle_rmgroup(client, user_id, message, text)
            return True
        elif cmd == ".interval":
            await handle_interval(client, user_id, message, text)
            return True
        elif cmd == ".shuffle":
            await handle_shuffle(client, user_id, message, text)
            return True
        elif cmd == ".copymode":
            await handle_copymode(client, user_id, message, text)
            return True
        elif cmd == ".sendmode":
            await handle_sendmode(client, user_id, message, text)
            return True
        elif cmd == ".responder":
            await handle_responder(client, user_id, message, text)
            return True
        elif cmd == ".ping":
            await reply_to_command(client, message, "● Pong! Worker is active ⚡")
            return True
        elif cmd == ".nightmode":
            await handle_nightmode(client, user_id, message, text)
            return True
        elif cmd == ".folders":
            await handle_folders(client, user_id, message)
            return True
        elif cmd == ".addfolder":
            await handle_addfolder(client, user_id, message, text)
            return True
    except Exception as e:
        logger.error(f"[User {user_id}] Command error: {e}")
        await reply_to_command(client, message, f"Error: {str(e)}")
    
    return False


async def reply_to_command(client: TelegramClient, message, text: str):
    """Send a reply to the message that triggered the command, auto-delete after 30s."""
    import asyncio
    reply = await message.reply(text)
    
    async def _auto_delete():
        await asyncio.sleep(30)
        try:
            await reply.delete()
            await message.delete()
        except Exception:
            pass  # Message may already be deleted
    
    asyncio.create_task(_auto_delete())


async def handle_help(client: TelegramClient, user_id: int, message):
    """Handle .help command with professional styling."""
    from core.config import MIN_INTERVAL_MINUTES
    text = (
        "🏆 *KURUP ADS ELITE — MASTER COMMANDS*\n\n"
        "👥 *GROUPS & IMPORTS*\n"
        "├ `.addgroup link1 link2` — Multi-add\n"
        "├ `.addlist <addlist_url>` — Import Folder/Chatlist\n"
        "├ `.addfolder <name>` — Import a Telegram folder\n"
        "├ `.folders` — List your local folders\n"
        "└ `.groups` | `.remfailed` | `.leave`\n\n"
        "⚙️ *CAMPAIGN SETTINGS*\n"
        "├ `.interval <min>` — Set loop delay (min: {min}m)\n"
        "├ `.copymode on/off` — Use fresh copy vs forward\n"
        "└ `.responder <msg>` | `.responder off`\n\n"
        "⚡ *SYSTEM & INFO*\n"
        "└ `.status` | `.ping` | `.me` | `.id`\n\n"
        "👑 *OWNER COMMANDS*\n"
        "└ `.addplan` | `.userstatus` | `.nightmode`\n"
        "".format(min=MIN_INTERVAL_MINUTES)
    )
    
    await reply_to_command(client, message, text)


async def handle_status(client: TelegramClient, user_id: int, message, text: str = ""):
    """Handle .status command with detailed information."""
    from core.config import OWNER_ID
    
    target_user_id = user_id
    parts = text.split()
    
    # Owner can check other users: .status <user_id>
    if len(parts) > 1 and user_id == OWNER_ID:
        try:
            target_user_id = int(parts[1])
        except ValueError:
            pass # Use self if invalid ID
            
    # Get specifically this account's session
    phone = getattr(client, 'phone', None)
    session = await get_session(target_user_id, phone if target_user_id == user_id else None)
    
    # Get config (User-wide)
    config = await get_user_config(target_user_id)
    
    # Get groups (all groups for this user)
    groups = await get_user_groups(target_user_id)
    total_groups = len(groups)
    enabled_groups = len([g for g in groups if g.get("enabled", True)])
    
    # Branding Verification (Live check or from worker state)
    branding_status = "🟢 ACTIVE" if getattr(client, 'is_branded', True) else "🔴 MISSING"
    
    phone_display = session.get("phone", "Unknown") if session else ("Owner Check" if target_user_id != user_id else "Unknown")
    from core.config import DEFAULT_INTERVAL_MINUTES
    interval = config.get("interval_min", DEFAULT_INTERVAL_MINUTES)
    
    # Setting indicators
    send_mode = config.get("send_mode", "sequential").title()
    total_reach = sum(g.get("member_count", 0) for g in groups)
    
    header = "📊 *WORKER DIAGNOSTICS*" if target_user_id == user_id else f"📊 *USER PROFILE: {target_user_id}*"
    
    text = f"""{header}
    
📱 *ACCOUNT PROFILE*
├ Phone: {phone_display}
├ Status: 🟢 Connected
└ Branding: {branding_status}

⚡ *LIVE SETTINGS*
├ Interval: {interval}m
├ Send Mode: {send_mode}
├ Shuffle: {"🟢 ON" if config.get("shuffle_mode") else "⚫ OFF"}
├ Copy Mode: {"🟢 ON" if config.get("copy_mode") else "⚫ OFF"}
├ Auto-Responder: {"🟢 ON" if config.get("auto_reply_enabled") else "⚫ OFF"}
└ Night Mode: {await get_night_mode_label()}

👥 *GROUPS ({enabled_groups}/{total_groups})*
└ 📢 Potential Reach: {total_reach:,} members

Type `.help` for available commands
"""
    await reply_to_command(client, message, text)


async def handle_groups(client: TelegramClient, user_id: int, message):
    """Handle .groups command - list groups for THIS account."""
    phone = getattr(client, 'phone', None)
    groups = await get_user_groups(user_id)
    
    if not groups:
        await reply_to_command(client, message, 
            f"📁 GROUPS — {phone}\n"
            f"══════════════════════════\n\n"
            f"⚪ No groups added yet.\n\n"
            f"💡 Use .addgroup <url> to add one."
        )
        return
    
    enabled = len([g for g in groups if g.get("enabled", True)])
    text = f"📁 GROUPS — {phone}\n"
    text += f"══════════════════════════\n\n"
    text += f"🟢 {enabled} active \u25aa {len(groups) - enabled} paused \u25aa {len(groups)}/{MAX_GROUPS_PER_USER} slots\n\n"
    
    for i, group in enumerate(groups, 1):
        title = group.get("chat_title", "Unknown")
        enabled = group.get("enabled", True)
        reason = group.get("pause_reason")
        
        if enabled:
            icon = "🟢"
            status_suffix = ""
        else:
            icon = "🔴"
            status_suffix = f" (Paused: {reason})" if reason else " (Paused)"
            
        text += f"  {i}. {icon} {title}{status_suffix}\n"
    
    text += f"\n══════════════════════════\n"
    text += "💡 .rmgroup <number> to remove."
    
    await reply_to_command(client, message, text)


async def handle_addgroup(client: TelegramClient, user_id: int, message, text: str):
    """Handle .addgroup <url> [url2] [url3] command - supports multiple groups."""
    # Parse URLs/usernames (split by spaces or newlines)
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await reply_to_command(client, message, 
            "○ Usage: .addgroup <url> [url2] [url3]...\n\n"
            "Examples:\n"
            "  ◦ .addgroup @group1\n"
            "  ◦ .addgroup @group1 @group2 @group3\n"
            "  ◦ .addgroup https://t.me/group1 https://t.me/group2"
        )
        return
    
    # Split input by spaces and newlines to get multiple groups
    group_inputs = parts[1].replace('\n', ' ').split()
    
    if not group_inputs:
        await reply_to_command(client, message, "○ No groups provided")
        return
    
    # Check group limit
    count = await get_group_count(user_id)
    available_slots = MAX_GROUPS_PER_USER - count
    
    if available_slots <= 0:
        await reply_to_command(client, message,
            f"○ Maximum groups reached!\n\n"
            f"You can only add up to {MAX_GROUPS_PER_USER} groups.\n"
            f"Remove a group with .rmgroup first."
        )
        return
    
    # Limit to available slots
    if len(group_inputs) > available_slots:
        group_inputs = group_inputs[:available_slots]
        await reply_to_command(client, message, 
            f"▪ Only processing {available_slots} group(s) due to limit..."
        )
    
    await reply_to_command(client, message, f"➤ Checking {len(group_inputs)} group(s)...")
    
    # Fetch existing group IDs for this account to prevent duplicate entries
    existing_groups = await get_user_groups(user_id, phone=getattr(client, 'phone', None))
    existing_ids = {g["chat_id"] for g in existing_groups}
    
    added = []
    failed = []
    
    for group_input in group_inputs:
        group_input = group_input.strip()
        if not group_input:
            continue
        
        # Parse group identifier
        group_identifier = parse_group_input(group_input)
        
        if not group_identifier:
            failed.append((group_input, "Invalid URL"))
            continue
        
        try:
            # Get the entity (group/channel)
            entity = await client.get_entity(group_identifier)
            
            # Check if user is actually a member of the group/channel
            if getattr(entity, 'left', False):
                failed.append((group_input, "You are not a member! Join first."))
                continue
            
            chat_id = entity.id
            chat_title = getattr(entity, 'title', None) or getattr(entity, 'username', str(chat_id))
            
            if chat_id in existing_ids:
                failed.append((group_input, "Already added to this account"))
                continue

            
            # Get member count
            member_count = 0
            try:
                from telethon.tl.functions.channels import GetFullChannelRequest
                full_chat = await client(GetFullChannelRequest(entity))
                member_count = full_chat.full_chat.participants_count
            except Exception:
                pass
                
            # Save to database
            # Link to the current account's phone for multi-account support
            success = await add_group(user_id, chat_id, chat_title, account_phone=getattr(client, 'phone', None), member_count=member_count)
            
            if success:
                added.append(chat_title)
            else:
                failed.append((group_input, "Already exists or limit reached"))
                
        except (UsernameNotOccupiedError, UsernameInvalidError):
            failed.append((group_input, "Not found"))
        except (ChannelPrivateError, ChannelInvalidError):
            failed.append((group_input, "Private/No access"))
        except (InviteHashInvalidError, InviteHashExpiredError):
            failed.append((group_input, "Invalid invite"))
        except Exception as e:
            failed.append((group_input, str(e)[:20]))
    
    # Build response
    response = ""
    
    if added:
        response += f"✅ Added {len(added)} group(s):\n"
        for title in added:
            response += f"  ▸ 🟢 {title}\n"
    
    if failed:
        response += f"\n❌ Failed {len(failed)}:\n"
        for name, reason in failed:
            response += f"  ▸ 🔴 {name[:15]}... — {reason}\n"
    
    if not response:
        response = "⚪ No groups were added."
    
    # Add current count
    new_count = await get_group_count(user_id)
    response += f"\n📁 Total: {new_count}/{MAX_GROUPS_PER_USER} slots used."
    
    await reply_to_command(client, message, response.strip())


async def handle_rmgroup(client: TelegramClient, user_id: int, message, text: str):
    """Handle .rmgroup <number or url> command."""
    # Parse the input
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await reply_to_command(client, message,
            "○ Usage: .rmgroup <number or url>\n\n"
            "Examples:\n"
            "  ◦ .rmgroup 1\n"
            "  ◦ .rmgroup @groupname\n\n"
            "▪ Use .groups to see your groups first."
        )
        return
    
    group_input = parts[1].strip()
    
    # Get user's groups FOR THIS ACCOUNT
    phone = getattr(client, 'phone', None)
    groups = await get_user_groups(user_id, phone=phone)
    
    if not groups:
        await reply_to_command(client, message, 
            f"○ No groups found for this account ({phone}).\n\n"
            "▪ Use .addgroup to add groups first."
        )
        return
    
    chat_id = None
    chat_title = None
    
    # Check if input is a number (remove by position)
    if group_input.isdigit():
        group_num = int(group_input)
        if 1 <= group_num <= len(groups):
            group = groups[group_num - 1]
            chat_id = group["chat_id"]
            chat_title = group.get("chat_title", "Unknown")
        else:
            await reply_to_command(client, message,
                f"○ Invalid group number\n\n"
                f"You have {len(groups)} group(s). Use a number between 1 and {len(groups)}."
            )
            return
    else:
        # Try to parse as URL/username
        group_identifier = parse_group_input(group_input)
        
        if not group_identifier:
            await reply_to_command(client, message, "○ Invalid group URL or username")
            return
        
        try:
            # Try to resolve entity
            entity = await client.get_entity(group_identifier)
            chat_id = entity.id
            chat_title = getattr(entity, 'title', str(chat_id))
        except Exception:
            # Try to match by name in existing groups
            search_term = group_identifier.lstrip("@").lower()
            for g in groups:
                if search_term in g.get("chat_title", "").lower():
                    chat_id = g["chat_id"]
                    chat_title = g["chat_title"]
                    break
            
            if not chat_id:
                await reply_to_command(client, message,
                    "○ Group not found in your list\n\n"
                    "▪ Use .groups to see your groups."
                )
                return
    
    try:
        # Remove from database
        await remove_group(user_id, chat_id)
        remaining = await get_group_count(user_id)
        await reply_to_command(client, message, 
            f"✅ Group removed!\n\n"
            f"  ▸ {chat_title}\n\n"
            f"📁 Remaining: {remaining}/{MAX_GROUPS_PER_USER} slots."
        )
        
    except Exception as e:
        logger.error(f"Error removing group: {e}")
        await reply_to_command(client, message, f"❌ Error: {str(e)}")


async def handle_interval(client: TelegramClient, user_id: int, message, text: str):
    """Handle .interval <minutes> command."""
    # Parse the interval
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        config = await get_user_config(user_id)
        current = config.get("interval_min", MIN_INTERVAL_MINUTES)
        await reply_to_command(client, message,
            f"➤ Current Interval: {current} minutes\n\n"
            f"Usage: .interval <minutes>\n"
            f"Minimum: {MIN_INTERVAL_MINUTES} minutes\n\n"
            f"Example: .interval 30"
        )
        return
    
    try:
        interval = int(parts[1].strip())
    except ValueError:
        await reply_to_command(client, message,
            f"○ Invalid number\n\n"
            f"Please enter a valid number of minutes.\n"
            f"Example: .interval 30"
        )
        return
    
    # Validate interval
    if interval < MIN_INTERVAL_MINUTES:
        await reply_to_command(client, message,
            f"○ Interval too low\n\n"
            f"Minimum interval is {MIN_INTERVAL_MINUTES} minutes."
        )
        return
    
    if interval > 1440:  # 24 hours max
        await reply_to_command(client, message,
            "○ Interval too high\n\n"
            "Maximum interval is 1440 minutes (24 hours)."
        )
        return
    
    # Update config
    await update_user_config(user_id, interval_min=interval)
    
    await reply_to_command(client, message,
        f"● Interval updated!\n\n"
        f"➤ New interval: {interval} minutes\n\n"
        f"Messages will be forwarded every {interval} minutes."
    )


async def handle_shuffle(client: TelegramClient, user_id: int, message, text: str):
    """Handle .shuffle on/off command."""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        config = await get_user_config(user_id)
        current = "ON" if config.get("shuffle_mode", False) else "OFF"
        await reply_to_command(client, message,
            f"➤ Shuffle Mode: {current}\n\n"
            f"Usage: .shuffle on/off\n"
            f"Randomizes group order each cycle."
        )
        return
    
    val = parts[1].strip().lower()
    enable = val == "on"
    
    await update_user_config(user_id, shuffle_mode=enable)
    status_text = "ENABLED ●" if enable else "DISABLED ○"
    
    await reply_to_command(client, message,
        f"■ Shuffle Mode {status_text}\n\n"
        f"Groups will now be {'randomized' if enable else 'sent in order'} each cycle."
    )


async def handle_copymode(client: TelegramClient, user_id: int, message, text: str):
    """Handle .copymode on/off command."""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        config = await get_user_config(user_id)
        current = "ON" if config.get("copy_mode", False) else "OFF"
        await reply_to_command(client, message,
            f"➤ Copy Mode: {current}\n\n"
            f"Usage: .copymode on/off\n"
            f"Sends as new message instead of forwarding."
        )
        return
    
    val = parts[1].strip().lower()
    enable = val == "on"
    
    await update_user_config(user_id, copy_mode=enable)
    status_text = "ENABLED ●" if enable else "DISABLED ○"
    
    await reply_to_command(client, message,
        f"■ Copy Mode {status_text}\n\n"
        f"Messages will now be {'sent as new copies' if enable else 'forwarded normally'}."
    )


async def handle_sendmode(client: TelegramClient, user_id: int, message, text: str):
    """Handle .sendmode <sequential/rotate/random> command."""
    parts = text.split(maxsplit=1)
    config = await get_user_config(user_id)
    current = config.get("send_mode", "sequential")
    
    if len(parts) < 2:
        await reply_to_command(client, message,
            f"➤ Send Mode: {current.title()}\n\n"
            f"Usage: .sendmode <mode>\n"
            f"Modes:\n"
            f"  ◦ sequential: Ad 1 to all groups, then Ad 2...\n"
            f"  ◦ rotate: Grp 1 gets Ad 1, Grp 2 gets Ad 2...\n"
            f"  ◦ random: Random ad sent to each group"
        )
        return
    
    val = parts[1].strip().lower()
    if val in ["seq", "sequential"]:
        val = "sequential"
    elif val in ["rot", "rotate"]:
        val = "rotate"
    elif val in ["rand", "random"]:
        val = "random"
    else:
        await reply_to_command(client, message, "○ Invalid mode! Choose: sequential, rotate, or random.")
        return
    
    await update_user_config(user_id, send_mode=val)
    
    await reply_to_command(client, message,
        f"■ Send Mode Updated: {val.title()} ●\n\n"
        f"Message distribution pattern changed."
    )


async def handle_responder(client: TelegramClient, user_id: int, message, text: str):
    """Handle .responder on/off or .responder <message>."""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        config = await get_user_config(user_id)
        current = "ON" if config.get("auto_reply_enabled", False) else "OFF"
        await reply_to_command(client, message,
            f"➤ Auto-Responder: {current}\n\n"
            f"Usage:\n"
            f"  .responder on/off\n"
            f"  .responder <your message>\n\n"
            f"Current message:\n"
            f"\"{config.get('auto_reply_text')}\""
        )
        return
    
    val = parts[1].strip()
    
    if val.lower() == "on":
        await update_user_config(user_id, auto_reply_enabled=True)
        await reply_to_command(client, message, "■ Auto-Responder ENABLED ●")
    elif val.lower() == "off":
        await update_user_config(user_id, auto_reply_enabled=False)
        await reply_to_command(client, message, "■ Auto-Responder DISABLED ○")
    else:
        # Set message
        await update_user_config(user_id, auto_reply_text=val, auto_reply_enabled=True)
        await reply_to_command(client, message, 
            f"● Auto-Responder set and ENABLED!\n\n"
            f"➤ New message: {val}"
        )



async def handle_rmpaused(client: TelegramClient, user_id: int, message):
    """Remove all paused groups."""
    groups = await get_user_groups(user_id)
    paused = [g for g in groups if not g.get("enabled", True)]
    
    if not paused:
        await reply_to_command(client, message, "⚪ No paused groups to remove.")
        return
        
    count = 0
    for g in paused:
        await remove_group(user_id, g["chat_id"])
        count += 1
        
    await reply_to_command(client, message, f"✅ Removed {count} paused group(s).")

def parse_group_input(input_str: str) -> str:
    """Parse group URL or username to identifier."""
    input_str = input_str.strip()
    
    # Handle @username
    if input_str.startswith("@"):
        return input_str
    
    # Handle t.me links with + (newer invite links)
    if "t.me/+" in input_str or "telegram.me/+" in input_str:
        return input_str
    
    # Handle joinchat links
    if "joinchat/" in input_str:
        return input_str
    
    # Handle message links (extract chat identifier)
    # https://t.me/c/123456789/123 -> -100123456789
    # https://t.me/groupname/123 -> groupname
    message_link_pattern = r"(?:https?://)?(?:t\.me|telegram\.me)/(?:c/)?([a-zA-Z0-9_-]+)/(\d+)"
    match = re.match(message_link_pattern, input_str)
    if match:
        extracted = match.group(1)
        if "/c/" in input_str and extracted.isdigit():
            return int("-100" + extracted)
        if extracted.isdigit() or extracted.startswith("-"):
            return int(extracted)
        return extracted

    # Handle various domain variations and protocols
    patterns = [
        r"(?:https?://)?(?:t\.me|telegram\.me|telegram\.dog)/([a-zA-Z0-9_]+)",
        r"tg://resolve\?domain=([a-zA-Z0-9_]+)",
        r"tg://join\?invite=([a-zA-Z0-9_-]+)",
    ]
    
    for pattern in patterns:
        match = re.match(pattern, input_str)
        if match:
            if "invite=" in pattern:
                return f"https://t.me/+{match.group(1)}"
            return match.group(1)
    
    # If it looks like a numeric ID
    if re.match(r"^-?\d+$", input_str):
        # Ensure proper casting so Telethon treats it as an ID, not a string username
        val = int(input_str)
        # If user pasted a large positive ID from Rose bot or similar, it often misses the -100
        if val > 1000000000:
            return int(f"-100{val}")
        return val

    # If it looks like a username without @
    if re.match(r"^[a-zA-Z0-9_]+$", input_str):
        return f"@{input_str}"
    
    return None
async def handle_nightmode(client: TelegramClient, user_id: int, message, text: str):
    """Handle .nightmode on/off/auto command (Owner only)."""
    from core.config import OWNER_ID
    if user_id != OWNER_ID:
        await reply_to_command(client, message, "❌ This command is restricted to the BOT OWNER.")
        return
        
    parts = text.split()
    if len(parts) < 2:
        from models.settings import get_global_settings
        settings = await get_global_settings()
        current = settings.get("night_mode_force", "auto").upper()
        await reply_to_command(client, message, 
            f"🌙 GLOBAL NIGHT MODE\n\n"
            f"➤ Current: {current}\n\n"
            f"Usage: .nightmode <on/off/auto>\n"
            f"  ◦ `on`: Force night mode NOW\n"
            f"  ◦ `off`: Disable night mode NOW\n"
            f"  ◦ `auto`: Use standard 00:00-06:00 IST"
        )
        return
        
    val = parts[1].lower()
    if val not in ["on", "off", "auto"]:
        await reply_to_command(client, message, "❌ Use: .nightmode on/off/auto")
        return
        
    from models.settings import update_global_settings
    await update_global_settings(night_mode_force=val)
    
    await reply_to_command(client, message, 
        f"✅ GLOBAL NIGHT MODE updated to: *{val.upper()}*\n\n"
        f"This change affects all accounts globally."
    )

async def get_night_mode_label() -> str:
    """Helper to get a human-friendly night mode status label."""
    from models.settings import get_global_settings
    from services.worker.utils import is_night_mode
    
    settings = await get_global_settings()
    force = settings.get("night_mode_force", "auto")
    active = await is_night_mode()
    
    if force == "on":
        return "🔴 FORCED ON"
    if force == "off":
         return "🟢 FORCED OFF"
    
    return "🌙 Active (00-06 IST)" if active else "☀️ Inactive (Daytime)"


async def handle_folders(client: TelegramClient, user_id: int, message):
    """List all Telegram chat folders (filters)."""
    try:
        from telethon.tl.functions.messages import GetDialogFiltersRequest
        filters = await client(GetDialogFiltersRequest())
        
        if not filters:
            await reply_to_command(client, message, "📁 No folders found on your account.")
            return
            
        text = "📁 *YOUR TELEGRAM FOLDERS*\n"
        text += "══════════════════════════\n\n"
        
        count = 0
        for f in filters:
            if hasattr(f, 'title') and f.title:
                text += f"▪ `{f.title}`\n"
                count += 1
                
        if count == 0:
            await reply_to_command(client, message, "📁 No custom folders found.")
            return
            
        text += f"\n💡 Use `.addfolder <name>` to add all groups from a folder."
        await reply_to_command(client, message, text)
        
    except Exception as e:
        logger.error(f"Error fetching folders: {e}")
        await reply_to_command(client, message, f"❌ Error: {str(e)}")


async def handle_addfolder(client: TelegramClient, user_id: int, message, text: str):
    """Add all groups from a specific Telegram folder."""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await reply_to_command(client, message, "○ Usage: `.addfolder <folder_name>`\n\nExample: `.addfolder Crypto`")
        return
        
    folder_name = parts[1].strip()
    await reply_to_command(client, message, f"🔍 Searching for folder: `{folder_name}`...")
    
    try:
        from telethon.tl.functions.messages import GetDialogFiltersRequest
        filters = await client(GetDialogFiltersRequest())
        
        target_filter = None
        for f in filters:
            if hasattr(f, 'title') and f.title and f.title.lower() == folder_name.lower():
                target_filter = f
                break
                
        if not target_filter:
            await reply_to_command(client, message, f"❌ Folder `{folder_name}` not found.\n\nType `.folders` to see all available folders.")
            return
            
        # Get peers from filter
        peers = getattr(target_filter, 'include_peers', [])
        if not peers:
            await reply_to_command(client, message, f"⚪ Folder `{folder_name}` is empty or contains no groups.")
            return
            
        await reply_to_command(client, message, f"⏳ Found {len(peers)} items in `{folder_name}`. Resolving...")
        
        # Check current group count
        count = await get_group_count(user_id)
        available_slots = MAX_GROUPS_PER_USER - count
        
        if available_slots <= 0:
            await reply_to_command(client, message, f"❌ Maximum groups ({MAX_GROUPS_PER_USER}) reached.")
            return
            
        added = []
        failed = []
        
        # Limit to available slots
        to_process = peers
        if len(peers) > available_slots:
            to_process = peers[:available_slots]
            await reply_to_command(client, message, f"⚠️ Note: only {available_slots} slots available. Processing first {available_slots} chats...")
            
        for peer in to_process:
            try:
                # Resolve entity
                entity = await client.get_entity(peer)
                
                # We only want groups or channels (not users/bots)
                from telethon.tl.types import Channel, Chat
                if not isinstance(entity, (Channel, Chat)):
                    continue
                    
                chat_id = entity.id
                chat_title = entity.title
                
                # Get member count
                member_count = 0
                try:
                    from telethon.tl.functions.channels import GetFullChannelRequest
                    full_chat = await client(GetFullChannelRequest(entity))
                    member_count = full_chat.full_chat.participants_count
                except Exception:
                    pass
                
                success = await add_group(user_id, chat_id, chat_title, account_phone=getattr(client, 'phone', None), member_count=member_count)
                if success:
                    added.append(chat_title)
                else:
                    failed.append(chat_title)
                    
            except Exception as e:
                logger.warning(f"Failed to resolve/add peer from folder: {e}")
                
        # Final response
        res = f"✅ *FOLDER IMPORT COMPLETE*\n"
        res += f"📁 Folder: `{folder_name}`\n"
        res += f"🎯 Groups Added: {len(added)}\n"
        
        if failed:
            res += f"❌ Skip (exists): {len(failed)}\n"
            
        new_total = await get_group_count(user_id)
        res += f"\nTotal Groups: {new_total}/{MAX_GROUPS_PER_USER}"
        
        await reply_to_command(client, message, res)
        
    except Exception as e:
        logger.error(f"Error adding folder: {e}")
        await reply_to_command(client, message, f"❌ Error: {str(e)}")
