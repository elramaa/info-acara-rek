import os
import json
from typing import List, Dict, Any

DATA_FILE = "data/events.json"
SETTINGS_FILE = "data/settings.json"
USERS_FILE = "data/users.json"


def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default


def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_events() -> List[Dict[str, Any]]:
    return load_json(DATA_FILE, [])


def save_events(events: List[Dict[str, Any]]):
    save_json(DATA_FILE, events)


def load_settings() -> Dict[str, Any]:
    return load_json(SETTINGS_FILE, {"lang": "id", "user_location": ""})


def save_settings(s: Dict[str, Any]):
    save_json(SETTINGS_FILE, s)


def load_users() -> List[Dict[str, Any]]:
    return load_json(USERS_FILE, [])


def save_users(users: List[Dict[str, Any]]):
    save_json(USERS_FILE, users)
