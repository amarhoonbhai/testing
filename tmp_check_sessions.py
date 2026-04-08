import asyncio
import os
import sys

sys.path.append(os.getcwd())

from core.database import get_database

async def check_sessions():
    db = get_database()
    print("🔍 Checking sessions...")
    cursor = db.sessions.find({"connected": True})
    sessions = await cursor.to_list(length=100)
    print(f"✅ Found {len(sessions)} connected sessions.")
    for s in sessions:
        print(f"📱 Phone: {s.get('phone')} | User: {s.get('user_id')} | IsActive: {s.get('is_active')}")

if __name__ == "__main__":
    asyncio.run(check_sessions())
