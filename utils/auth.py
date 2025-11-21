import os
import hashlib
import binascii
import getpass
from typing import Dict, Any, Optional
from utils.storage import load_users, save_users
from utils.colors import color_text, Colors


def hash_password(password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return {
        "salt": binascii.hexlify(salt).decode(),
        "hash": binascii.hexlify(dk).decode(),
    }


def verify_password(stored: Dict[str, str], attempt: str) -> bool:
    salt = binascii.unhexlify(stored["salt"].encode())
    dk = hashlib.pbkdf2_hmac("sha256", attempt.encode("utf-8"), salt, 100_000)
    return binascii.hexlify(dk).decode() == stored["hash"]


def register_user(t_default: Dict[str, Any]):
    users = load_users()
    print(color_text("Register new user (0 = cancel)", Colors.GREEN))
    username = input(t_default["prompt_username"]).strip()
    if username == "" or username == "0":
        return
    if any(u["username"].lower() == username.lower() for u in users):
        print(color_text(t_default["register_fail_exists"], Colors.RED))
        return
    password = getpass.getpass(t_default["prompt_password"]).strip()
    password2 = getpass.getpass("Confirm password: ").strip()
    if password != password2:
        print(color_text("Passwords do not match.", Colors.RED))
        return
    role = input(t_default["prompt_role_register"]).strip().lower()
    if role not in ("visitor", "organizer"):
        print(color_text("Invalid role. Use 'visitor' or 'organizer'.", Colors.RED))
        return
    hashed = hash_password(password)
    users.append({"username": username, "password": hashed, "role": role})
    save_users(users)
    print(color_text(t_default["register_success"], Colors.GREEN))


def login_user(t_default: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    users = load_users()
    print(color_text("Login (0 = cancel)", Colors.CYAN))
    username = input(t_default["prompt_username"]).strip()
    if username == "" or username == "0":
        return None
    password = getpass.getpass(t_default["prompt_password"]).strip()
    for u in users:
        if u["username"].lower() == username.lower():
            if verify_password(u["password"], password):
                print(color_text("Login sukses.", Colors.GREEN))
                return u
            else:
                print(color_text(t_default["login_fail"], Colors.RED))
                return None
    print(color_text(t_default["login_fail"], Colors.RED))
    return None
