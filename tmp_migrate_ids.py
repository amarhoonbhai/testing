"""
One-time migration to fix Supergroup IDs in the database.
Ensures IDs missing the -100 prefix are corrected to prevent 'Invalid ID' errors.
"""
import asyncio
import logging
import sys
import os

# Add current directory to path so imports work
sys.path.append(os.getcwd())

from core.database import get_database

async def migrate_ids():
    db = get_database()
    print("🎬 Starting ID Normalization...")
    
    # Cursor for all groups
    cursor = db.groups.find({})
    fixed_count = 0
    total_count = 0
    
    async for group in cursor:
        total_count += 1
        old_id = group.get("chat_id")
        
        # Supergroups usually have 10-14 digits.
        # If it's a negative ID but missing -100 (e.g. -1234567890)
        # We need to normalize it to -1001234567890
        if isinstance(old_id, int) and old_id < 0 and -9999999999 < old_id < -100000000:
            new_id = int(f"-100{abs(old_id)}")
            print(f"🔧 Fixing ID: {old_id} -> {new_id} ({group.get('chat_title')})")
            
            # Update the ID
            await db.groups.update_one(
                {"_id": group["_id"]},
                {"$set": {"chat_id": new_id}}
            )
            fixed_count += 1
            
    print(f"✅ Normalization Complete!")
    print(f"📊 Total checked: {total_count} | Modified: {fixed_count}")

if __name__ == "__main__":
    asyncio.run(migrate_ids())
