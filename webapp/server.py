import hmac
import hashlib
import json
import time
import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

from core.config import MAIN_BOT_TOKEN, MONGODB_URI, MONGODB_DB_NAME
from core.database import get_database, init_database
from models.user import get_user_config, update_user_config
from models.group import get_user_groups, add_group, remove_group, toggle_group
from models.session import get_all_user_sessions, disconnect_session, is_session_paused, get_session_paused_until
from models.stats import get_account_stats
from shared.utils import parse_group_entry

app = FastAPI(title="KURUP ADS BOT API")

# Store for active login sessions with timestamp
active_logins = {}

async def cleanup_active_logins():
    """Background task to close idle login sessions."""
    while True:
        await asyncio.sleep(600) # Check every 10 mins
        now = time.time()
        to_delete = []
        for user_id, data in active_logins.items():
            if now - data['timestamp'] > 1800: # 30 min timeout
                to_delete.append(user_id)
        
        for user_id in to_delete:
            client = active_logins[user_id]['client']
            await client.disconnect()
            del active_logins[user_id]
            print(f"Cleanup: Disconnected idle login for user {user_id}")

# Helper for Telegram initData validation
def validate_telegram_data(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing initData")
    
    try:
        parsed_data = dict(x.split('=') for x in init_data.split('&'))
        hash_check = parsed_data.pop('hash')
        
        # Security: Check auth_date (prevent replay)
        auth_date = int(parsed_data.get('auth_date', 0))
        if time.time() - auth_date > 86400: # 24 hour expiry
            raise HTTPException(status_code=401, detail="initData expired")

        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        secret_key = hmac.new(b"WebAppData", MAIN_BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash != hash_check:
            raise HTTPException(status_code=401, detail="Invalid hash")
            
        user_data = json.loads(parsed_data['user'])
        return user_data
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Auth failed: {str(e)}")

# Dependency to get current user from Telegram header
async def get_current_user(x_telegram_init_data: Optional[str] = Header(None)):
    return validate_telegram_data(x_telegram_init_data)

@app.on_event("startup")
async def startup_event():
    await init_database()
    asyncio.create_task(cleanup_active_logins())

@app.on_event("shutdown")
async def shutdown_event():
    for data in active_logins.values():
        await data['client'].disconnect()
    print("Shutdown: All active login clients disconnected.")

# --- API Endpoints ---

@app.get("/api/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)):
    user_id = user['id']
    sessions = await get_all_user_sessions(user_id)
    groups = await get_user_groups(user_id)
    config = await get_user_config(user_id)
    
    # Simple stats
    total_sent = 0
    accounts_status = []
    for s in sessions:
        stats = await get_account_stats(user_id, s['phone'])
        total_sent += stats.get('total_sent', 0)
        
        paused_until = await get_session_paused_until(user_id, s['phone'])
        is_paused = await is_session_paused(user_id, s['phone'])
        
        accounts_status.append({
            "phone": s['phone'],
            "connected": s.get('connected', False),
            "sent": stats.get('total_sent', 0),
            "last_active": stats.get('last_active'),
            "is_paused": is_paused,
            "paused_until": paused_until.isoformat() if paused_until else None
        })
        
    return {
        "user_name": user.get('first_name', 'User'),
        "total_sent": total_sent,
        "group_count": len(groups),
        "account_count": len(sessions),
        "accounts": accounts_status,
        "config": config,
        "is_active": config.get('is_active', True),
        "saved_api_id": config.get('api_id'),
        "has_api_hash": bool(config.get('api_hash'))
    }

@app.get("/api/groups")
async def list_groups(user: dict = Depends(get_current_user)):
    return await get_user_groups(user['id'])

@app.post("/api/groups/add")
async def add_new_group(data: dict, user: dict = Depends(get_current_user)):
    url = data.get('url')
    if not url:
        raise HTTPException(status_code=400, detail="URL required")
    try:
        chat_id, chat_username, title = parse_group_entry(url)
        await add_group(user['id'], chat_id, title, chat_username=chat_username)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/groups/{chat_id}")
async def delete_group_api(chat_id: int, user: dict = Depends(get_current_user)):
    await remove_group(user['id'], chat_id)
    return {"status": "ok"}

@app.post("/api/groups/toggle/{chat_id}")
async def toggle_group_api(chat_id: int, data: dict, user: dict = Depends(get_current_user)):
    enabled = data.get('enabled', True)
    await toggle_group(user['id'], chat_id, enabled)
    return {"status": "ok"}

@app.post("/api/settings")
async def update_settings(settings: dict, user: dict = Depends(get_current_user)):
    await update_user_config(user['id'], **settings)
    return {"status": "ok"}

@app.post("/api/config/toggle_active")
async def toggle_active_api(data: dict, user: dict = Depends(get_current_user)):
    is_active = data.get('is_active', True)
    await update_user_config(user['id'], is_active=is_active)
    return {"status": "ok", "is_active": is_active}

# --- Login Flow ---

class LoginStart(BaseModel):
    phone: str
    api_id: int
    api_hash: str

@app.post("/api/login/start")
async def login_start(data: LoginStart, user: dict = Depends(get_current_user)):
    user_id = user['id']
    client = TelegramClient(StringSession(), data.api_id, data.api_hash)
    await client.connect()
    
    try:
        sent_code = await client.send_code_request(data.phone)
        active_logins[user_id] = {
            "client": client,
            "phone": data.phone,
            "phone_code_hash": sent_code.phone_code_hash,
            "api_id": data.api_id,
            "api_hash": data.api_hash,
            "timestamp": time.time()
        }
        return {"status": "otp_required"}
    except Exception as e:
        await client.disconnect()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login/otp")
async def login_otp(data: dict, user: dict = Depends(get_current_user)):
    user_id = user['id']
    login_data = active_logins.get(user_id)
    if not login_data:
        raise HTTPException(status_code=400, detail="No active login session")
    
    client = login_data['client']
    code = data.get('code')
    
    try:
        await client.sign_in(login_data['phone'], code, phone_code_hash=login_data['phone_code_hash'])
        # Success! Save credentials to config for next time
        await update_user_config(user_id, api_id=login_data['api_id'], api_hash=login_data['api_hash'])
        
        session_str = client.session.save()
        from models.session import create_session
        await create_session(user_id, login_data['phone'], session_str, login_data['api_id'], login_data['api_hash'])
        await client.disconnect()
        del active_logins[user_id]
        return {"status": "success"}
    except SessionPasswordNeededError:
        return {"status": "2fa_required"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login/2fa")
async def login_2fa(data: dict, user: dict = Depends(get_current_user)):
    user_id = user['id']
    login_data = active_logins.get(user_id)
    if not login_data:
        raise HTTPException(status_code=400, detail="No active login session")
    
    client = login_data['client']
    password = data.get('password')
    
    try:
        await client.sign_in(password=password)
        session_str = client.session.save()
        from models.session import create_session
        await create_session(user_id, login_data['phone'], session_str, login_data['api_id'], login_data['api_hash'])
        await client.disconnect()
        del active_logins[user_id]
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Static files ---
app.mount("/", StaticFiles(directory="webapp/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
