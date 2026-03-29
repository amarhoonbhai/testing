
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

async def test_verification():
    print("Verification Script Started")
    try:
        from models.user import get_user_config
        from main_bot.handlers.dashboard import _parse_group_entry
        from core.config import MIN_INTERVAL_MINUTES, DEFAULT_INTERVAL_MINUTES
        
        print(f"--- Configuration Verification ---")
        print(f"MIN_INTERVAL_MINUTES: {MIN_INTERVAL_MINUTES}")
        print(f"DEFAULT_INTERVAL_MINUTES: {DEFAULT_INTERVAL_MINUTES}")
        
        print(f"\n--- User Model Verification ---")
        # Test get_user_config for a non-existent user
        config = await get_user_config(999999999)
        print(f"Default interval_min for new user: {config.get('interval_min')}")
        
        print(f"\n--- Group Parsing Verification ---")
        test_links = [
            "https://t.me/public_group",
            "@another_public",
            "https://t.me/+private_hash",
            "https://t.me/addlist/folder_hash",
            "-100123456789",
            "tg://resolve?domain=deeplink"
        ]
        
        for link in test_links:
            try:
                res = _parse_group_entry(link)
                print(f"Link: {link:40} -> Result: {res}")
            except Exception as e:
                print(f"Link: {link:40} -> Error: {e}")
                
        print("\nVerification Script Completed Successfully")
    except Exception as e:
        print(f"CRITICAL ERROR in verification script: {e}")

if __name__ == "__main__":
    asyncio.run(test_verification())
