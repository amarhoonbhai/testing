import os
import sys
import asyncio
import logging

# Ensure root directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telethon import TelegramClient
from core.database import init_database, get_database
from core.config import (
    MAIN_BOT_TOKEN, 
    LOGIN_BOT_TOKEN, 
    MONGODB_URI,
    validate_config
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestSuite")

async def test_mongodb():
    print("\n--- 1. Testing MongoDB ---")
    try:
        await init_database()
        db = get_database()
        # Test write
        test_doc = {"test": "data", "timestamp": "now"}
        res = await db.test_collection.insert_one(test_doc)
        print(f"✅ DB Write Success (ID: {res.inserted_id})")
        # Test read
        read_doc = await db.test_collection.find_one({"_id": res.inserted_id})
        if read_doc:
            print("✅ DB Read Success")
        # Cleanup
        await db.test_collection.delete_one({"_id": res.inserted_id})
        print("✅ DB Cleanup Success")
    except Exception as e:
        print(f"❌ MongoDB Test Failed: {e}")

async def test_bot_tokens():
    print("\n--- 2. Testing Bot Tokens ---")
    for name, token in [("Main Bot", MAIN_BOT_TOKEN), ("Login Bot", LOGIN_BOT_TOKEN)]:
        if not token:
            print(f"❌ {name}: Token MISSING in .env")
            continue
        try:
            # We'll just check if the token format is valid (Telethon client start)
            client = TelegramClient(f'test_{name.lower().replace(" ", "_")}', 2040, 'b18441a1ffaf627441427cfedc516563')
            await client.connect()
            await client.sign_in(bot_token=token)
            me = await client.get_me()
            print(f"✅ {name}: Valid (@{me.username})")
            await client.disconnect()
        except Exception as e:
            print(f"❌ {name}: Invalid or Connection Failed - {e}")

async def run_diagnostics():
    print("="*40)
    print("💎 STARTING BOT HEALTH DIAGNOSTICS 💎")
    print("="*40)
    
    # 0. Validate Config
    print("\n--- 0. Validating Configuration ---")
    try:
        validate_config()
        print("✅ Config validation passed.")
    except SystemExit:
        print("❌ Config validation FAILED (Check .env)")
        return

    # 1. Mongo
    await test_mongodb()

    # 2. Bots
    await test_bot_tokens()

    print("\n" + "="*40)
    print("DIAGNOSTICS COMPLETE")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
