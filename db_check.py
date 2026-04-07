import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def check_connection():
    uri = os.getenv("MONGODB_URI")
    print(f"--- DATABASE DIAGNOSTICS ---")
    
    # 1. Check Public IP
    try:
        ip = requests.get('https://api.ipify.org').text
        print(f"Current Public IP: {ip}")
    except Exception as e:
        print(f"Failed to fetch public IP: {e}")

    # 2. Test MongoDB Connection
    if not uri:
        print("ERROR: MONGODB_URI not found in .env")
        return

    print(f"Testing connection to: {uri.split('@')[-1]}") # Protect credentials
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ SUCCESS: Successfully connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ FAILED: Connection error: {e}")
        print("\nSUGGESTION: Ensure 'Allow Access from Anywhere' (0.0.0.0/0) is enabled in your MongoDB Atlas Network Access dashboard, OR whitelist the IP above.")

if __name__ == "__main__":
    check_connection()
