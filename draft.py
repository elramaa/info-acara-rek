#!/usr/bin/env python3
"""
jatim_events_cli.py (final update)

Changes requested by user applied:
- Attendance uses logged-in username (no name prompt)
- Review uses logged-in username (no name prompt)
- Status selection uses numeric menu (1=scheduled,2=finished,3=postponed,4=cancelled)
- When adding event, status defaults to 'scheduled' (no prompt)
- Added 'address' field to event data (human-readable)
- Do not display internal event 'id' in tables
- Auto-update event status to 'finished' if scheduled and time has passed (performed at load and before listings)
- Detail view for selected event with full info and review list
- Default listing hides events occurring before today (but they remain in data and accessible via filter_menu)
- Compatible with existing login/register system and translations (TRANSLATIONS variable)
- Minimal external dependencies: only Python stdlib

Note: file paths used for persistence: events.json, users.json, settings.json
"""

import os
import sys
import json
import hashlib
import binascii
import getpass
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
import collections

# --------------------------
# File paths
# --------------------------
DATA_FILE = "events.json"
SETTINGS_FILE = "settings.json"
USERS_FILE = "users.json"

# --------------------------
# Translations (single variable, nested per language)
# --------------------------
TRANSLATIONS: Dict[str, Dict[str, Any]] = {
    "id": {
        "menu_title": "Manajemen Event & Tradisi Jatim",
        "prompt_register_or_login": "1=Register, 2=Login, 0=Keluar: ",
        "prompt_username": "Username: ",
        "prompt_password": "Password: ",
        "prompt_role_register": "Role (visitor/organizer): ",
        "register_success": "Registrasi berhasil. Silakan login.",
        "register_fail_exists": "Username sudah ada.",
        "login_fail": "Login gagal (username/password salah).",
        "menu_visitor_title": "Menu Pengunjung",
        "menu_organizer_title": "Menu Penyelenggara",
        "menu_options_visitor": [
            "Lihat semua acara (default hide acara lampau)",
            "Lihat acara pada hari tertentu",
            "Filter acara (menu lengkap, termasuk acara lampau)",
            "Filter berdasarkan waktu (hari/minggu/bulan)",
            "Filter rentang tanggal (dari - sampai)",
            "Filter minggu penuh (Senin - Minggu)",
            "Pilih hadir pada acara (menggunakan username login)",
            "Lihat jadwal hadir saya (menggunakan username login)",
            "Berikan review untuk acara (hanya acara selesai, menggunakan username login)",
            "Statistik",
            "Ganti bahasa",
            "Atur lokasi pengguna",
            "Detail acara (lihat informasi lengkap & review)",
        ],
        "menu_options_organizer": [
            "Tambah acara (status default = scheduled)",
            "Edit acara",
            "Hapus acara",
            "Lihat semua acara (default hide acara lampau)",
            "Lihat acara pada hari tertentu",
            "Filter acara (menu lengkap, termasuk acara lampau)",
            "Filter berdasarkan waktu (hari/minggu/bulan)",
            "Filter rentang tanggal (dari - sampai)",
            "Update status acara (pakai angka)",
            "Statistik",
            "Ganti bahasa",
            "Atur lokasi pengguna",
            "Detail acara (lihat informasi lengkap & review)",
        ],
        "prompt_choice": "Pilih opsi (angka, 0=keluar): ",
        "prompt_name": "Nama acara: ",
        "prompt_datetime": "Waktu acara (YYYY-MM-DD HH:MM) — contoh: 2025-11-21 18:00 : ",
        "prompt_date": "Masukkan tanggal (YYYY-MM-DD) atau kosong untuk hari ini: ",
        "prompt_location": "Lokasi (kota/desa): ",
        "prompt_address": "Alamat detail (jalan/RT/RW): ",
        "prompt_organizer": "Penyelenggara: ",
        "prompt_description": "Deskripsi singkat: ",
        "prompt_htm": "HTM / Harga tiket (angka atau 'gratis'): ",
        "prompt_category": "Kategori (Tradisi/Festival/Upacara Adat/Tari/Gamelan/Drama/Musik/LAINNYA): ",
        "prompt_status_num": "Pilih status: 1=scheduled, 2=finished, 3=postponed, 4=cancelled : ",
        "event_added": "Acara berhasil ditambahkan.",
        "event_updated": "Acara berhasil diperbarui.",
        "event_deleted": "Acara berhasil dihapus.",
        "status_updated": "Status acara diperbarui.",
        "no_events": "Tidak ada acara.",
        "list_header": "Daftar acara:",
        "event_format": "{idx}. {name} | {dt} | {loc} | {addr} | {org} | Kategori: {cat} | Status: {status} | HTM: {htm}\n   {desc}",
        "prompt_location_filter": "Masukkan lokasi untuk memfilter (substring, kosong = batal): ",
        "prompt_time_filter": "Pilih periode: 1=Hari, 2=Minggu, 3=Bulan : ",
        "prompt_reference_date": "Tanggal acuan (YYYY-MM-DD) atau kosong untuk hari ini: ",
        "prompt_range_start": "Mulai dari (YYYY-MM-DD): ",
        "prompt_range_end": "Sampai (YYYY-MM-DD): ",
        "prompt_select_index": "Masukkan nomor acara (index, 0 = batal): ",
        "prompt_confirm_delete": "Ketik 'YA' untuk mengonfirmasi penghapusan: ",
        "prompt_attend_confirm": "Anda akan terdaftar hadir menggunakan username: ",
        "attend_confirmed": "Anda telah terdaftar hadir pada acara ini.",
        "already_attending": "Anda sudah terdaftar hadir pada acara ini.",
        "prompt_review_rating": "Rating (1-5): ",
        "prompt_review_comment": "Komentar (opsional): ",
        "review_added": "Terima kasih — review telah disimpan.",
        "not_allowed_review": "Review hanya dapat diberikan untuk acara dengan status 'finished'.",
        "prompt_lang": "Pilih bahasa (id = Indonesia, jv = Jawa, en = English): ",
        "lang_changed": "Bahasa telah diubah ke: ",
        "prompt_set_location": "Masukkan lokasi pengguna (kota/desa) atau kosong untuk batal: ",
        "settings_saved": "Pengaturan disimpan.",
        "invalid_choice": "Pilihan tidak valid.",
        "invalid_date": "Format tanggal/waktu tidak valid. Gunakan YYYY-MM-DD atau YYYY-MM-DD HH:MM.",
        "invalid_index": "Index tidak valid.",
        "invalid_rating": "Rating tidak valid. Masukkan angka 1 sampai 5.",
        "press_enter": "Tekan Enter untuk melanjutkan...",
        "stats_title": "Statistik Event:",
        "stats_by_category": "Jumlah per kategori:",
        "stats_by_month": "Jumlah per bulan (YYYY-MM):",
        "stats_by_city": "Jumlah per lokasi/kota:",
        "header_table_cols": [
            "#",
            "Name",
            "When",
            "Location",
            "Address",
            "Organizer",
            "Category",
            "Status",
            "HTM",
            "Att",
            "Avg",
        ],
        "detail_back": "Tekan Enter untuk kembali...",
        "show_all_info_hint": "Catatan: tampilan default menyembunyikan acara yang sudah lewat (sebelum hari ini). Gunakan menu filter untuk melihat semua acara.",
    },
    "en": {
        "menu_title": "East Java Events & Traditions Manager",
        "prompt_register_or_login": "1=Register, 2=Login, 0=Quit: ",
        "prompt_username": "Username: ",
        "prompt_password": "Password: ",
        "prompt_role_register": "Role (visitor/organizer): ",
        "register_success": "Registration success. Please login.",
        "register_fail_exists": "Username already exists.",
        "login_fail": "Login failed (username/password incorrect).",
        "menu_visitor_title": "Visitor Menu",
        "menu_organizer_title": "Organizer Menu",
        "menu_options_visitor": [
            "View all events (default hide past events)",
            "View events for a specific day",
            "Filter events (full menu, includes past events)",
            "Filter by time (day/week/month)",
            "Filter by date range (from - to)",
            "Filter full week (Mon - Sun)",
            "Mark attend to an event (uses your username)",
            "View my scheduled attendance (uses your username)",
            "Review an event (only finished, uses your username)",
            "Statistics",
            "Change language",
            "Set user location",
            "Event detail (view full info & reviews)",
        ],
        "menu_options_organizer": [
            "Add event (default status = scheduled)",
            "Edit event",
            "Delete event",
            "View all events (default hide past events)",
            "View events for a specific day",
            "Filter events (full menu, includes past events)",
            "Filter by time (day/week/month)",
            "Filter by date range (from - to)",
            "Update event status (use numbers)",
            "Statistics",
            "Change language",
            "Set user location",
            "Event detail (view full info & reviews)",
        ],
        "prompt_choice": "Choose option (number, 0=quit): ",
        "prompt_name": "Event name: ",
        "prompt_datetime": "Event datetime (YYYY-MM-DD HH:MM) — e.g. 2025-11-21 18:00 : ",
        "prompt_date": "Enter date (YYYY-MM-DD) or empty for today: ",
        "prompt_location": "Location (city/village): ",
        "prompt_address": "Address (street/RT/RW): ",
        "prompt_organizer": "Organizer: ",
        "prompt_description": "Short description: ",
        "prompt_htm": "Ticket price (number or 'free'): ",
        "prompt_category": "Category (Tradition/Festival/Ceremony/Dance/Gamelan/Drama/Music/OTHER): ",
        "prompt_status_num": "Choose status: 1=scheduled, 2=finished, 3=postponed, 4=cancelled : ",
        "event_added": "Event successfully added.",
        "event_updated": "Event successfully updated.",
        "event_deleted": "Event successfully deleted.",
        "status_updated": "Event status updated.",
        "no_events": "No events.",
        "list_header": "Events list:",
        "event_format": "{idx}. {name} | {dt} | {loc} | {addr} | {org} | Category: {cat} | Status: {status} | HTM: {htm}\n   {desc}",
        "prompt_location_filter": "Enter location substring to filter (empty = cancel): ",
        "prompt_time_filter": "Choose period: 1=Day, 2=Week, 3=Month : ",
        "prompt_reference_date": "Reference date (YYYY-MM-DD) or empty for today: ",
        "prompt_range_start": "Start date (YYYY-MM-DD): ",
        "prompt_range_end": "End date (YYYY-MM-DD): ",
        "prompt_select_index": "Enter event number (index, 0 = cancel): ",
        "prompt_confirm_delete": "Type 'YES' to confirm deletion: ",
        "prompt_attend_confirm": "You will be marked as attending using username: ",
        "attend_confirmed": "You have been marked as attending this event.",
        "already_attending": "You are already marked as attending this event.",
        "prompt_review_rating": "Rating (1-5): ",
        "prompt_review_comment": "Comment (optional): ",
        "review_added": "Thank you — review saved.",
        "not_allowed_review": "You can only review events with status 'finished'.",
        "prompt_lang": "Choose language (id = Indonesia, jv = Javanese, en = English): ",
        "lang_changed": "Language changed to: ",
        "prompt_set_location": "Set user location (city/village) or empty to cancel: ",
        "settings_saved": "Settings saved.",
        "invalid_choice": "Invalid choice.",
        "invalid_date": "Invalid date/datetime format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM.",
        "invalid_index": "Invalid index.",
        "invalid_rating": "Invalid rating. Enter 1 to 5.",
        "press_enter": "Press Enter to continue...",
        "stats_title": "Event Statistics:",
        "stats_by_category": "Counts by category:",
        "stats_by_month": "Counts by month (YYYY-MM):",
        "stats_by_city": "Counts by location/city:",
        "header_table_cols": [
            "#",
            "Name",
            "When",
            "Location",
            "Address",
            "Organizer",
            "Category",
            "Status",
            "HTM",
            "Att",
            "Avg",
        ],
        "detail_back": "Press Enter to go back...",
        "show_all_info_hint": "Note: default view hides past events (before today). Use the filter menu to see all events.",
    },
    "jv": {
        # Minimal Javanese translations for key phrases
        "menu_title": "Manajemen Acara & Tradisi Jatim",
        "prompt_register_or_login": "1=Register, 2=Login, 0=Metu: ",
        "prompt_username": "Username: ",
        "prompt_password": "Password: ",
        "prompt_role_register": "Role (visitor/organizer): ",
        "register_success": "Registrasi kasil. Mangga login.",
        "register_fail_exists": "Username sampun ana.",
        "login_fail": "Login gagal (username/password salah).",
        "menu_visitor_title": "Menu Pangunjung",
        "menu_organizer_title": "Menu Panyelenggara",
        "menu_options_visitor": [
            "Deleng kabeh acara (default sembunyikan acara lawas)",
            "Deleng acara ing dina tartamtu",
            "Filter acara (menu lengkap, kalebu acara lawas)",
            "Filter wektu (dina/minggu/bulan)",
            "Filter rentang tanggal (saka - nganti)",
            "Filter minggu lengkap (Senin - Minggu)",
            "Milih rawuh ing acara (nganggo username)",
            "Deleng jadwal rawuhku (nganggo username)",
            "Menehi review kanggo acara (mung 'finished', nganggo username)",
            "Statistik",
            "Ganti basa",
            "Set lokasi pangguna",
            "Detail acara (informasi lengkap & review)",
        ],
        "menu_options_organizer": [
            "Tambah acara (default status = scheduled)",
            "Edit acara",
            "Busak acara",
            "Deleng kabeh acara (default sembunyikan acara lawas)",
            "Deleng acara ing dina tartamtu",
            "Filter acara (menu lengkap, kalebu acara lawas)",
            "Filter wektu (dina/minggu/bulan)",
            "Filter rentang tanggal (saka - nganti)",
            "Update status acara (gunakake angka)",
            "Statistik",
            "Ganti basa",
            "Set lokasi pangguna",
            "Detail acara (informasi lengkap & review)",
        ],
        "prompt_choice": "Pilih opsi (angka, 0=metu): ",
        "prompt_name": "Jeneng acara: ",
        "prompt_datetime": "Wektu acara (YYYY-MM-DD HH:MM): ",
        "prompt_date": "Tanggal (YYYY-MM-DD) utawa kosong = dina iki: ",
        "prompt_location": "Lokasi (kutha/desa): ",
        "prompt_address": "Alamat (jalan/RT/RW): ",
        "prompt_organizer": "Panyelenggara: ",
        "prompt_description": "Katrangan cekak: ",
        "prompt_htm": "HTM / Rega tiket: ",
        "prompt_category": "Kategori: ",
        "prompt_status_num": "Pilih status: 1=scheduled,2=finished,3=postponed,4=cancelled : ",
        "event_added": "Acara kasimpen.",
        "event_updated": "Acara kasimpen (diubah).",
        "event_deleted": "Acara wis dibusak.",
        "status_updated": "Status acara diupdate.",
        "no_events": "Ora ana acara.",
        "list_header": "Daftar acara:",
        "event_format": "{idx}. {name} | {dt} | {loc} | {addr} | {org} | Kategori: {cat} | Status: {status} | HTM: {htm}\n   {desc}",
        "prompt_select_index": "Lebokake nomer acara (index, 0 = batal): ",
        "prompt_confirm_delete": "Tulis 'YA' kanggo konfirmasi busak: ",
        "prompt_attend_confirm": "Sampeyan bakal kadhaptar nganggo username: ",
        "attend_confirmed": "Sampeyan wis kadhaptar rawuh ing acara iki.",
        "already_attending": "Sampeyan wis kadhaptar rawuh ing acara iki.",
        "prompt_review_rating": "Rating (1-5): ",
        "prompt_review_comment": "Komentar (opsional): ",
        "review_added": "Matur nuwun — review kasimpen.",
        "not_allowed_review": "Review mung kanggo acara 'finished'.",
        "prompt_lang": "Pilih basa (id/jv/en): ",
        "lang_changed": "Basa diganti dadi: ",
        "prompt_set_location": "Lebokake lokasi pangguna (kutha/desa) utawa kosong kanggo batal: ",
        "settings_saved": "Setelan kasimpen.",
        "invalid_choice": "Pilihan ora sah.",
        "invalid_date": "Format tanggal salah. Gunakake YYYY-MM-DD utawa YYYY-MM-DD HH:MM.",
        "invalid_index": "Index ora sah.",
        "invalid_rating": "Rating ora sah. Gunakake 1 sampai 5.",
        "press_enter": "Pencet Enter kanggo nerusake...",
        "stats_title": "Statistik Acara:",
        "stats_by_category": "Jumlah miturut kategori:",
        "stats_by_month": "Jumlah miturut wulan (YYYY-MM):",
        "stats_by_city": "Jumlah miturut lokasi/kutha:",
        "header_table_cols": [
            "#",
            "Name",
            "When",
            "Location",
            "Address",
            "Organizer",
            "Category",
            "Status",
            "HTM",
            "Att",
            "Avg",
        ],
        "detail_back": "Pencet Enter kanggo bali...",
        "show_all_info_hint": "Catetan: tampilan default ndhelikake acara sing wis liwat (sadurunge dina iki). Gunakake menu filter kanggo ndeleng kabeh acara.",
    },
}


# --------------------------
# ANSI Colors helper
# --------------------------
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def color_text(s: str, style: str) -> str:
    return f"{style}{s}{Colors.END}"


# --------------------------
# JSON utilities
# --------------------------
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


# --------------------------
# Password hashing (PBKDF2)
# --------------------------
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


# --------------------------
# Date/time helpers
# --------------------------
def parse_datetime(s: str) -> Optional[datetime]:
    s = s.strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def parse_date(s: str) -> Optional[date]:
    s = s.strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def format_dt(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.hour == 0 and dt.minute == 0:
            return dt.strftime("%Y-%m-%d")
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str


# --------------------------
# Event object constructor (adds address field)
# --------------------------
def new_event_object(
    name: str,
    dt: datetime,
    location: str,
    address: str,
    organizer: str,
    description: str,
    htm: str,
    category: str,
    status: str = "scheduled",
) -> Dict[str, Any]:
    return {
        "id": int(datetime.now().timestamp() * 1000),
        "name": name,
        "datetime": dt.isoformat(),
        "location": location,
        "address": address,
        "organizer": organizer,
        "description": description,
        "htm": htm,
        "category": category,
        "status": status,
        "attendees": [],  # list of {"username","timestamp"}
        "reviews": [],  # list of {"username","rating","comment","timestamp"}
    }


# --------------------------
# Auto-update statuses for past events
# --------------------------
def auto_update_event_statuses(events: List[Dict[str, Any]]) -> bool:
    """Update events in-place: if scheduled and datetime < now -> finished.
    Returns True if any changes were made (so caller can save)."""
    changed = False
    now = datetime.now()
    for e in events:
        try:
            dt = datetime.fromisoformat(e["datetime"])
        except Exception:
            continue
        # If event datetime < now (past) and status is scheduled => mark finished
        if dt < now and e.get("status") == "scheduled":
            e["status"] = "finished"
            changed = True
    return changed


# --------------------------
# Table printing (hide id)
# --------------------------
def print_table(events: List[Dict[str, Any]], t: Dict[str, Any]):
    if not events:
        print(color_text(t["no_events"], Colors.YELLOW))
        return
    headers = t.get(
        "header_table_cols",
        [
            "#",
            "Name",
            "When",
            "Location",
            "Address",
            "Organizer",
            "Category",
            "Status",
            "HTM",
            "Att",
            "Avg",
        ],
    )
    rows = []
    for i, e in enumerate(sorted(events, key=lambda x: x["datetime"]), start=1):
        att = len(e.get("attendees", []))
        revs = e.get("reviews", [])
        avg_rating = (
            round(sum(r.get("rating", 0) for r in revs) / len(revs), 2) if revs else "-"
        )
        rows.append(
            [
                str(i),
                e.get("name", ""),
                format_dt(e.get("datetime", "")),
                e.get("location", ""),
                e.get("address", ""),
                e.get("organizer", ""),
                e.get("category", ""),
                e.get("status", ""),
                str(e.get("htm", "")),
                str(att),
                str(avg_rating),
            ]
        )
    cols = len(headers)
    widths = [len(headers[i]) for i in range(cols)]
    for r in rows:
        for i in range(cols):
            widths[i] = max(widths[i], len(r[i]))
    hdr = " | ".join(headers[i].ljust(widths[i]) for i in range(cols))
    print(color_text(hdr, Colors.BOLD + Colors.CYAN))
    print("-" * (sum(widths) + 3 * (cols - 1)))
    for r in rows:
        print(" | ".join(r[i].ljust(widths[i]) for i in range(cols)))


# --------------------------
# CRUD and interactive functions (status numeric, default scheduled, address field)
# --------------------------
def add_event_interactive(events: List[Dict[str, Any]], t: Dict[str, Any]):
    clear_screen()
    print(color_text("Add Event", Colors.GREEN))
    name = input(t["prompt_name"]).strip()
    dt_raw = input(t["prompt_datetime"]).strip()
    dt = parse_datetime(dt_raw)
    if dt is None:
        print(color_text(t["invalid_date"], Colors.RED))
        input(t["press_enter"])
        return
    location = input(t["prompt_location"]).strip()
    address = input(t["prompt_address"]).strip()
    organizer = input(t["prompt_organizer"]).strip()
    description = input(t["prompt_description"]).strip()
    htm = input(t["prompt_htm"]).strip()
    category = input(t["prompt_category"]).strip() or "LAINNYA"
    # Default status = scheduled (no prompt)
    ev = new_event_object(
        name,
        dt,
        location,
        address,
        organizer,
        description,
        htm,
        category,
        status="scheduled",
    )
    events.append(ev)
    # Auto update statuses (in case dt already in past)
    if auto_update_event_statuses(events):
        save_events(events)
    else:
        save_events(events)
    print(color_text(t["event_added"], Colors.GREEN))
    input(t["press_enter"])


def pick_event_index(
    events: List[Dict[str, Any]], t: Dict[str, Any], allow_past: bool = False
) -> Optional[int]:
    """Show table and let user pick index. By default, hide past events (before today).
    If allow_past True, show all events regardless of date.
    Returns original index in events list, or None."""
    if not events:
        print(color_text(t["no_events"], Colors.YELLOW))
        input(t["press_enter"])
        return None
    # Optionally filter out events before today
    today = datetime.now().date()
    display_events = []
    mapping = []  # maps displayed index to original index
    for orig_idx, e in enumerate(sorted(events, key=lambda x: x["datetime"])):
        try:
            dt = datetime.fromisoformat(e["datetime"])
        except Exception:
            continue
        if (not allow_past) and dt.date() < today:
            continue
        display_events.append(e)
    if not display_events:
        # nothing to pick
        print(
            color_text(
                "No events to select (after applying default hiding of past events).",
                Colors.YELLOW,
            )
        )
        input(t["press_enter"])
        return None
    print_table(display_events, t)
    sel = input(t["prompt_select_index"]).strip()
    if sel == "" or sel == "0":
        return None
    if not sel.isdigit():
        print(color_text(t["invalid_index"], Colors.RED))
        input(t["press_enter"])
        return None
    idx = int(sel) - 1
    if idx < 0 or idx >= len(display_events):
        print(color_text(t["invalid_index"], Colors.RED))
        input(t["press_enter"])
        return None
    selected_event = display_events[idx]
    # find in original events by unique id
    for orig_idx, e in enumerate(events):
        if e.get("id") == selected_event.get("id"):
            return orig_idx
    return None


def edit_event_interactive(events: List[Dict[str, Any]], t: Dict[str, Any]):
    clear_screen()
    idx = pick_event_index(events, t, allow_past=True)
    if idx is None:
        return
    e = events[idx]
    print(color_text("Edit (enter = keep existing)", Colors.CYAN))
    new_name = input(f"{t['prompt_name']} [{e['name']}]: ").strip() or e["name"]
    dt_input = input(f"{t['prompt_datetime']} [{format_dt(e['datetime'])}]: ").strip()
    if dt_input:
        dt_parsed = parse_datetime(dt_input)
        if dt_parsed is None:
            print(color_text(t["invalid_date"], Colors.RED))
            input(t["press_enter"])
            return
        e["datetime"] = dt_parsed.isoformat()
    new_location = input(
        f"{t['prompt_location']} [{e.get('location','')}]: "
    ).strip() or e.get("location", "")
    new_address = input(
        f"{t['prompt_address']} [{e.get('address','')}]: "
    ).strip() or e.get("address", "")
    new_org = input(
        f"{t['prompt_organizer']} [{e.get('organizer','')}]: "
    ).strip() or e.get("organizer", "")
    new_desc = input(
        f"{t['prompt_description']} [{e.get('description','')}]: "
    ).strip() or e.get("description", "")
    new_htm = input(f"{t['prompt_htm']} [{e.get('htm','')}]: ").strip() or e.get(
        "htm", ""
    )
    new_cat = input(
        f"{t['prompt_category']} [{e.get('category','LAINNYA')}]: "
    ).strip() or e.get("category", "LAINNYA")
    # Status: allow numeric selection
    print("Current status:", e.get("status", "scheduled"))
    stat_in = input(t["prompt_status_num"]).strip()
    if stat_in in ("1", "2", "3", "4"):
        mapping = {
            "1": "scheduled",
            "2": "finished",
            "3": "postponed",
            "4": "cancelled",
        }
        e["status"] = mapping[stat_in]
    # apply rest
    e["name"] = new_name
    e["location"] = new_location
    e["address"] = new_address
    e["organizer"] = new_org
    e["description"] = new_desc
    e["htm"] = new_htm
    e["category"] = new_cat
    # auto update statuses then save
    if auto_update_event_statuses(events):
        save_events(events)
    else:
        save_events(events)
    print(color_text(t["event_updated"], Colors.GREEN))
    input(t["press_enter"])


def delete_event_interactive(events: List[Dict[str, Any]], t: Dict[str, Any]):
    clear_screen()
    idx = pick_event_index(events, t, allow_past=True)
    if idx is None:
        return
    confirm = input(t["prompt_confirm_delete"]).strip()
    if confirm.upper() in ("YA", "YES"):
        events.pop(idx)
        save_events(events)
        print(color_text(t["event_deleted"], Colors.GREEN))
    else:
        print(color_text(t["invalid_choice"], Colors.YELLOW))
    input(t["press_enter"])


def update_event_status_interactive(events: List[Dict[str, Any]], t: Dict[str, Any]):
    clear_screen()
    idx = pick_event_index(events, t, allow_past=True)
    if idx is None:
        return
    e = events[idx]
    print("Current status:", e.get("status", "scheduled"))
    stat_in = input(t["prompt_status_num"]).strip()
    if stat_in not in ("1", "2", "3", "4"):
        print(color_text(t["invalid_choice"], Colors.RED))
        input(t["press_enter"])
        return
    mapping = {"1": "scheduled", "2": "finished", "3": "postponed", "4": "cancelled"}
    e["status"] = mapping[stat_in]
    save_events(events)
    print(color_text(t["status_updated"], Colors.GREEN))
    input(t["press_enter"])


# --------------------------
# Listing & filters (default hides past events)
# --------------------------
def list_events(
    events: List[Dict[str, Any]],
    t: Dict[str, Any],
    allow_past: bool = False,
    filtered: Optional[List[Dict[str, Any]]] = None,
):
    # Always run auto-update before display
    if auto_update_event_statuses(events):
        save_events(events)
    data = filtered if filtered is not None else events
    # By default hide events before today unless allow_past True
    if not allow_past:
        today = datetime.now().date()
        data = [
            e for e in data if datetime.fromisoformat(e["datetime"]).date() >= today
        ]
    clear_screen()
    print(color_text(t.get("list_header", "List:"), Colors.BOLD))
    print(color_text(t.get("show_all_info_hint", ""), Colors.CYAN))
    print_table(data, t)
    input(t["press_enter"])


def events_on_day(events: List[Dict[str, Any]], target: date) -> List[Dict[str, Any]]:
    res = []
    for e in events:
        try:
            dt = datetime.fromisoformat(e["datetime"])
        except Exception:
            continue
        if dt.date() == target:
            res.append(e)
    return res


def filter_by_location(
    events: List[Dict[str, Any]], location_substr: str
) -> List[Dict[str, Any]]:
    s = location_substr.strip().lower()
    return [
        e
        for e in events
        if s in e.get("location", "").lower() or s in e.get("address", "").lower()
    ]


def filter_by_period(
    events: List[Dict[str, Any]], period: str, ref_date: date
) -> List[Dict[str, Any]]:
    if period == "day":
        start = ref_date
        end = start + timedelta(days=1)
    elif period == "week":
        d = ref_date
        start_of_week = d - timedelta(days=d.weekday())
        start = start_of_week
        end = start_of_week + timedelta(days=7)
    elif period == "month":
        start = ref_date.replace(day=1)
        if start.month == 12:
            next_month = start.replace(year=start.year + 1, month=1, day=1)
        else:
            next_month = start.replace(month=start.month + 1, day=1)
        end = next_month
    else:
        start = ref_date
        end = ref_date + timedelta(days=1)
    res = []
    for e in events:
        try:
            dt = datetime.fromisoformat(e["datetime"])
            if start <= dt.date() < end:
                res.append(e)
        except Exception:
            continue
    return res


def filter_by_date_range(
    events: List[Dict[str, Any]], start_date: date, end_date: date
) -> List[Dict[str, Any]]:
    res = []
    for e in events:
        try:
            dt = datetime.fromisoformat(e["datetime"])
            if start_date <= dt.date() <= end_date:
                res.append(e)
        except Exception:
            continue
    return res


def filter_week_full(
    events: List[Dict[str, Any]], ref_date: date
) -> Tuple[List[Dict[str, Any]], date, date]:
    start_of_week = ref_date - timedelta(days=ref_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    res = []
    for e in events:
        try:
            dt = datetime.fromisoformat(e["datetime"])
            if start_of_week <= dt.date() <= end_of_week:
                res.append(e)
        except Exception:
            continue
    return res, start_of_week, end_of_week


# --------------------------
# Advanced filter menu (allows access to past events too)
# --------------------------
def filter_menu(events: List[Dict[str, Any]], t: Dict[str, Any]):
    clear_screen()
    if not events:
        print(color_text(t["no_events"], Colors.YELLOW))
        input(t["press_enter"])
        return
    cols = [
        ("name", "Name / Nama"),
        ("datetime", "Date/Time"),
        ("location", "Location / Lokasi"),
        ("address", "Address / Alamat"),
        ("organizer", "Organizer"),
        ("category", "Category"),
        ("status", "Status"),
        ("htm", "HTM"),
    ]
    print(color_text("Filter Menu (0 = cancel)", Colors.CYAN))
    print("Pilih kolom untuk difilter (pisahkan dengan koma). Contoh: 1,3")
    for i, (_, label) in enumerate(cols, start=1):
        print(f"{i}. {label}")
    sel = input("Kolom: ").strip()
    if sel == "" or sel == "0":
        return
    chosen_idx = []
    for part in sel.split(","):
        if part.strip().isdigit():
            v = int(part.strip())
            if 1 <= v <= len(cols):
                chosen_idx.append(v - 1)
    if not chosen_idx:
        print(color_text(t["invalid_choice"], Colors.YELLOW))
        input(t["press_enter"])
        return
    filtered = events
    for idx in chosen_idx:
        key = cols[idx][0]
        if key == "datetime":
            print(
                "Pilih tipe filter untuk datetime: 1=exact date (YYYY-MM-DD), 2=range, 3=substring"
            )
            typ = input("Tipe: ").strip()
            if typ == "1":
                d_raw = input("Tanggal (YYYY-MM-DD): ").strip()
                d = parse_date(d_raw)
                if d is None:
                    print(color_text(t["invalid_date"], Colors.RED))
                    input(t["press_enter"])
                    return
                filtered = events_on_day(filtered, d)
            elif typ == "2":
                s_raw = input(t["prompt_range_start"]).strip()
                e_raw = input(t["prompt_range_end"]).strip()
                s_d = parse_date(s_raw)
                e_d = parse_date(e_raw)
                if s_d is None or e_d is None:
                    print(color_text(t["invalid_date"], Colors.RED))
                    input(t["press_enter"])
                    return
                filtered = filter_by_date_range(filtered, s_d, e_d)
            else:
                kw = input("Keyword untuk datetime (substring): ").strip().lower()
                filtered = [
                    ev for ev in filtered if kw in ev.get("datetime", "").lower()
                ]
        else:
            kw = (
                input(
                    f"Masukkan keyword untuk {cols[idx][1]} (substring, kosong = skip): "
                )
                .strip()
                .lower()
            )
            if kw == "":
                continue
            filtered = [ev for ev in filtered if kw in str(ev.get(key, "")).lower()]
    clear_screen()
    print(color_text("Hasil filter (termasuk acara lampau jika cocok):", Colors.GREEN))
    print_table(filtered, t)
    input(t["press_enter"])


# --------------------------
# Attendance & review using username (no extra name input)
# --------------------------
def attend_event(
    events: List[Dict[str, Any]], t: Dict[str, Any], current_user: Dict[str, Any]
):
    clear_screen()
    idx = pick_event_index(events, t, allow_past=False)
    if idx is None:
        return
    username = current_user["username"]
    e = events[idx]
    if any(
        a.get("username", "").strip().lower() == username.lower()
        for a in e.get("attendees", [])
    ):
        print(color_text(t["already_attending"], Colors.YELLOW))
        input(t["press_enter"])
        return
    e.setdefault("attendees", []).append(
        {"username": username, "timestamp": datetime.now().isoformat()}
    )
    save_events(events)
    print(color_text(t["attend_confirmed"], Colors.GREEN))
    input(t["press_enter"])


def view_my_attendance(
    events: List[Dict[str, Any]], t: Dict[str, Any], current_user: Dict[str, Any]
):
    username = current_user["username"]
    matched = []
    for e in events:
        for a in e.get("attendees", []):
            if a.get("username", "").strip().lower() == username.lower():
                matched.append(e)
                break
    clear_screen()
    if not matched:
        print(
            color_text(
                "Tidak ada jadwal hadir yang ditemukan untuk username Anda.",
                Colors.YELLOW,
            )
        )
        input(t["press_enter"])
        return
    print_table(matched, t)
    input(t["press_enter"])


def add_review(
    events: List[Dict[str, Any]], t: Dict[str, Any], current_user: Dict[str, Any]
):
    clear_screen()
    idx = pick_event_index(events, t, allow_past=False)
    if idx is None:
        return
    e = events[idx]
    if e.get("status", "") != "finished":
        print(color_text(t["not_allowed_review"], Colors.YELLOW))
        input(t["press_enter"])
        return
    username = current_user["username"]
    # check if user already reviewed? permit multiple reviews if desired; we'll allow one review per user per event
    if any(
        r.get("username", "").strip().lower() == username.lower()
        for r in e.get("reviews", [])
    ):
        print(color_text("Anda sudah memberi review untuk acara ini.", Colors.YELLOW))
        input(t["press_enter"])
        return
    rating_raw = input(t["prompt_review_rating"]).strip()
    if not rating_raw.isdigit():
        print(color_text(t["invalid_rating"], Colors.RED))
        input(t["press_enter"])
        return
    rating = int(rating_raw)
    if rating < 1 or rating > 5:
        print(color_text(t["invalid_rating"], Colors.RED))
        input(t["press_enter"])
        return
    comment = input(t["prompt_review_comment"]).strip()
    e.setdefault("reviews", []).append(
        {
            "username": username,
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.now().isoformat(),
        }
    )
    save_events(events)
    print(color_text(t["review_added"], Colors.GREEN))
    input(t["press_enter"])


# --------------------------
# Event detail view (with reviews)
# --------------------------
def view_event_detail(events: List[Dict[str, Any]], t: Dict[str, Any]):
    clear_screen()
    idx = pick_event_index(events, t, allow_past=True)
    if idx is None:
        return
    e = events[idx]
    clear_screen()
    print(color_text("Event Detail", Colors.BOLD + Colors.CYAN))
    print("-" * 40)
    print(f"Name     : {e.get('name','')}")
    print(f"When     : {format_dt(e.get('datetime',''))}")
    print(f"Location : {e.get('location','')}")
    print(f"Address  : {e.get('address','')}")
    print(f"Organizer: {e.get('organizer','')}")
    print(f"Category : {e.get('category','')}")
    print(f"Status   : {e.get('status','')}")
    print(f"HTM      : {e.get('htm','')}")
    print(f"Desc     : {e.get('description','')}")
    print("\nAttendees:")
    atts = e.get("attendees", [])
    if not atts:
        print("  - (no attendees)")
    else:
        for a in atts:
            print(f"  - {a.get('username','')} at {a.get('timestamp','')}")
    print("\nReviews:")
    revs = e.get("reviews", [])
    if not revs:
        print("  - (no reviews)")
    else:
        for r in revs:
            print(
                f"  - {r.get('username','')} | {r.get('rating','-')} | {r.get('comment','')} | {r.get('timestamp','')}"
            )
    input("\n" + t.get("detail_back", "Press Enter to go back..."))


# --------------------------
# Statistics
# --------------------------
def stats(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_category = collections.Counter()
    by_month = collections.Counter()
    by_city = collections.Counter()
    for e in events:
        cat = e.get("category", "LAINNYA")
        by_category[cat] += 1
        try:
            dt = datetime.fromisoformat(e["datetime"])
            ym = dt.strftime("%Y-%m")
            by_month[ym] += 1
        except Exception:
            pass
        loc = e.get("location", "Unknown")
        by_city[loc] += 1
    return {
        "by_category": dict(by_category),
        "by_month": dict(by_month),
        "by_city": dict(by_city),
    }


def show_stats(events: List[Dict[str, Any]], t: Dict[str, Any]):
    s = stats(events)
    print("\n" + color_text(t["stats_title"], Colors.BOLD))
    print("-" * 30)
    print(color_text(t["stats_by_category"], Colors.CYAN))
    for k, v in sorted(s["by_category"].items(), key=lambda x: (-x[1], x[0])):
        print(f"  {k}: {v}")
    print("\n" + color_text(t["stats_by_month"], Colors.CYAN))
    for k, v in sorted(s["by_month"].items(), key=lambda x: x[0]):
        print(f"  {k}: {v}")
    print("\n" + color_text(t["stats_by_city"], Colors.CYAN))
    for k, v in sorted(s["by_city"].items(), key=lambda x: (-x[1], x[0])):
        print(f"  {k}: {v}")
    input("\n" + t["press_enter"])


# --------------------------
# Clear screen
# --------------------------
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# --------------------------
# User management (register & login)
# --------------------------
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


# --------------------------
# Menus (visitor & organizer) now accept current_user for attendance/review
# --------------------------
def visitor_loop(
    events: List[Dict[str, Any]],
    settings: Dict[str, Any],
    t: Dict[str, Any],
    current_user: Dict[str, Any],
):
    while True:
        clear_screen()
        print(color_text(t["menu_visitor_title"], Colors.BOLD + Colors.CYAN))
        print(color_text("0. Keluar / Kembali", Colors.YELLOW))
        for idx, opt in enumerate(t["menu_options_visitor"], start=1):
            print(f"{idx}. {opt}")
        choice = input("\n" + t["prompt_choice"]).strip()
        if choice == "0":
            break
        if not choice.isdigit():
            print(color_text(t["invalid_choice"], Colors.RED))
            input(t["press_enter"])
            continue
        c = int(choice)
        if c == 1:
            list_events(events, t, allow_past=False)
        elif c == 2:
            ds = input(t["prompt_date"]).strip()
            target = datetime.now().date() if ds == "" else (parse_date(ds) or None)
            if target is None:
                print(color_text(t["invalid_date"], Colors.RED))
                input(t["press_enter"])
                continue
            matched = events_on_day(events, target)
            list_events(events, t, allow_past=True, filtered=matched)
        elif c == 3:
            filter_menu(events, t)
        elif c == 4:
            choice_p = input(t["prompt_time_filter"]).strip()
            if choice_p not in ("1", "2", "3"):
                print(color_text(t["invalid_choice"], Colors.RED))
                input(t["press_enter"])
                continue
            ref = input(t["prompt_reference_date"]).strip()
            ref_date = datetime.now().date() if ref == "" else (parse_date(ref) or None)
            if ref_date is None:
                print(color_text(t["invalid_date"], Colors.RED))
                input(t["press_enter"])
                continue
            period = {"1": "day", "2": "week", "3": "month"}[choice_p]
            matched = filter_by_period(events, period, ref_date)
            list_events(events, t, allow_past=True, filtered=matched)
        elif c == 5:
            start_raw = input(t["prompt_range_start"]).strip()
            end_raw = input(t["prompt_range_end"]).strip()
            start_d = parse_date(start_raw)
            end_d = parse_date(end_raw)
            if start_d is None or end_d is None:
                print(color_text(t["invalid_date"], Colors.RED))
                input(t["press_enter"])
                continue
            matched = filter_by_date_range(events, start_d, end_d)
            list_events(events, t, allow_past=True, filtered=matched)
        elif c == 6:
            ref_raw = input(t["prompt_reference_date"]).strip()
            ref_date = (
                datetime.now().date()
                if ref_raw == ""
                else (parse_date(ref_raw) or None)
            )
            if ref_date is None:
                print(color_text(t["invalid_date"], Colors.RED))
                input(t["press_enter"])
                continue
            matched, start_w, end_w = filter_week_full(events, ref_date)
            clear_screen()
            print(f"Menampilkan acara dari {start_w} sampai {end_w}")
            list_events(events, t, allow_past=True, filtered=matched)
        elif c == 7:
            attend_event(events, t, current_user)
        elif c == 8:
            view_my_attendance(events, t, current_user)
        elif c == 9:
            add_review(events, t, current_user)
        elif c == 10:
            clear_screen()
            show_stats(events, t)
        elif c == 11:
            new_lang = input(t["prompt_lang"]).strip().lower()
            if new_lang not in TRANSLATIONS:
                print(color_text(t["invalid_choice"], Colors.RED))
                input(t["press_enter"])
                continue
            settings["lang"] = new_lang
            save_settings(settings)
            t = TRANSLATIONS[new_lang]
            print(color_text(t["lang_changed"] + new_lang, Colors.GREEN))
            input(t["press_enter"])
        elif c == 12:
            new_loc = input(t["prompt_set_location"]).strip()
            if new_loc:
                settings["user_location"] = new_loc
                save_settings(settings)
                print(color_text(t["settings_saved"], Colors.GREEN))
            else:
                print(color_text(t["invalid_choice"], Colors.RED))
            input(t["press_enter"])
        elif c == 13:
            view_event_detail(events, t)
        else:
            print(color_text(t["invalid_choice"], Colors.RED))
            input(t["press_enter"])


def organizer_loop(
    events: List[Dict[str, Any]],
    settings: Dict[str, Any],
    t: Dict[str, Any],
    current_user: Dict[str, Any],
):
    while True:
        clear_screen()
        print(color_text(t["menu_organizer_title"], Colors.BOLD + Colors.CYAN))
        print(color_text("0. Keluar / Kembali", Colors.YELLOW))
        for idx, opt in enumerate(t["menu_options_organizer"], start=1):
            print(f"{idx}. {opt}")
        choice = input("\n" + t["prompt_choice"]).strip()
        if choice == "0":
            break
        if not choice.isdigit():
            print(color_text(t["invalid_choice"], Colors.RED))
            input(t["press_enter"])
            continue
        c = int(choice)
        if c == 1:
            add_event_interactive(events, t)
        elif c == 2:
            edit_event_interactive(events, t)
        elif c == 3:
            delete_event_interactive(events, t)
        elif c == 4:
            list_events(events, t, allow_past=False)
        elif c == 5:
            ds = input(t["prompt_date"]).strip()
            target = datetime.now().date() if ds == "" else (parse_date(ds) or None)
            if target is None:
                print(color_text(t["invalid_date"], Colors.RED))
                input(t["press_enter"])
                continue
            matched = events_on_day(events, target)
            list_events(events, t, allow_past=True, filtered=matched)
        elif c == 6:
            filter_menu(events, t)
        elif c == 7:
            choice_p = input(t["prompt_time_filter"]).strip()
            if choice_p not in ("1", "2", "3"):
                print(color_text(t["invalid_choice"], Colors.RED))
                input(t["press_enter"])
                continue
            ref = input(t["prompt_reference_date"]).strip()
            ref_date = datetime.now().date() if ref == "" else (parse_date(ref) or None)
            if ref_date is None:
                print(color_text(t["invalid_date"], Colors.RED))
                input(t["press_enter"])
                continue
            period = {"1": "day", "2": "week", "3": "month"}[choice_p]
            matched = filter_by_period(events, period, ref_date)
            list_events(events, t, allow_past=True, filtered=matched)
        elif c == 8:
            start_raw = input(t["prompt_range_start"]).strip()
            end_raw = input(t["prompt_range_end"]).strip()
            start_d = parse_date(start_raw)
            end_d = parse_date(end_raw)
            if start_d is None or end_d is None:
                print(color_text(t["invalid_date"], Colors.RED))
                input(t["press_enter"])
                continue
            matched = filter_by_date_range(events, start_d, end_d)
            list_events(events, t, allow_past=True, filtered=matched)
        elif c == 9:
            update_event_status_interactive(events, t)
        elif c == 10:
            clear_screen()
            show_stats(events, t)
        elif c == 11:
            new_lang = input(t["prompt_lang"]).strip().lower()
            if new_lang not in TRANSLATIONS:
                print(color_text(t["invalid_choice"], Colors.RED))
                input(t["press_enter"])
                continue
            settings["lang"] = new_lang
            save_settings(settings)
            t = TRANSLATIONS[new_lang]
            print(color_text(t["lang_changed"] + new_lang, Colors.GREEN))
            input(t["press_enter"])
        elif c == 12:
            new_loc = input(t["prompt_set_location"]).strip()
            if new_loc:
                settings["user_location"] = new_loc
                save_settings(settings)
                print(color_text(t["settings_saved"], Colors.GREEN))
            else:
                print(color_text(t["invalid_choice"], Colors.RED))
            input(t["press_enter"])
        elif c == 13:
            view_event_detail(events, t)
        else:
            print(color_text(t["invalid_choice"], Colors.RED))
            input(t["press_enter"])


# --------------------------
# Main entry (login/register) - auto-update statuses at startup
# --------------------------
def main_loop():
    settings = load_settings()
    events = load_events()
    # Auto-update statuses on load
    if auto_update_event_statuses(events):
        save_events(events)
    users = load_users()
    lang = settings.get("lang", "id")
    t = TRANSLATIONS.get(lang, TRANSLATIONS["id"])
    while True:
        clear_screen()
        print(color_text(t["menu_title"], Colors.BOLD + Colors.BLUE))
        print(color_text("1. Register", Colors.GREEN))
        print(color_text("2. Login", Colors.CYAN))
        print(color_text("0. Quit", Colors.YELLOW))
        choice = input(t["prompt_register_or_login"]).strip()
        if choice == "0":
            print(color_text("Bye.", Colors.GREEN))
            break
        elif choice == "1":
            register_user(t)
            input("Press Enter to continue...")
            continue
        elif choice == "2":
            user = login_user(t)
            if user is None:
                input("Press Enter to continue...")
                continue
            # refresh state
            settings = load_settings()
            lang = settings.get("lang", "id")
            t = TRANSLATIONS.get(lang, TRANSLATIONS["id"])
            events = load_events()
            # ensure statuses up to date
            if auto_update_event_statuses(events):
                save_events(events)
            if user.get("role") == "visitor":
                visitor_loop(events, settings, t, user)
            elif user.get("role") == "organizer":
                organizer_loop(events, settings, t, user)
            else:
                print(color_text("Unknown role assigned to user.", Colors.RED))
                input("Press Enter to continue...")
        else:
            print(color_text("Invalid choice.", Colors.RED))
            input("Press Enter to continue...")


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n" + color_text("Bye.", Colors.GREEN))
        try:
            sys.exit(0)
        except SystemExit:
            pass
