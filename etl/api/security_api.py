import os
import json
from fastapi import HTTPException, Header

API_KEYS_FILE = os.getenv("API_KEYS_FILE", "api_keys.json")
SUPER_API_KEY = os.getenv("SUPER_API_KEY", "superapikey")  # superUserKey

def load_keys():
    if not os.path.exists(API_KEYS_FILE):
        return {}
    with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_keys(data):
    with open(API_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key == SUPER_API_KEY:
        return {"user": "superuser", "superuser": True}
    keys = load_keys()
    if x_api_key not in keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"user": keys[x_api_key], "superuser": False}

def create_api_key(name: str):
    import secrets
    keys = load_keys()
    key = secrets.token_urlsafe(16)
    keys[key] = name
    save_keys(keys)
    return key

def delete_api_key(key: str):
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
        return True
    return False

def get_api_keys():
    keys = load_keys()
    return keys
