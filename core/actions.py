import collections
from typing import List, Dict, Any, Tuple, Optional
from utils.colors import *
from utils.parser import *
from utils.clear import clear_screen
from utils.storage import *
from datetime import timedelta
from utils.status_updater import auto_update_event_statuses


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
    select_event_for_detail(data, t)


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
    select_event_for_detail(filtered, t)


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
    select_event_for_detail(matched, t)


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
def view_event_detail(events: List[Dict[str, Any]], t: Dict[str, Any], direct=False):
    clear_screen()

    if direct:
        # events[0] adalah event yang benar-benar dipilih user
        e = events[0]
    else:
        # OLD behavior – digunakan jika masuk via menu lain
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


def select_event_for_detail(events: List[Dict[str, Any]], t: Dict[str, Any]):
    """Reusable helper: show table and allow selecting event by its table row number.

    IMPORTANT:
    - print_table() displays events sorted by datetime, so we must use the same sorted
      order here to make table row numbers match selection.
    - This function prints the sorted table, accepts a row number (1..n) and opens
      the detail view for the event shown on that row (no second selection).
    """
    if not events:
        print(color_text(t["no_events"], Colors.YELLOW))
        input(t["press_enter"])
        return

    # Sort events the same way print_table does so indices match what's displayed.
    sorted_events = sorted(events, key=lambda x: x["datetime"])

    while True:
        clear_screen()
        print_table(sorted_events, t)

        user_input = input(
            f"\n{t.get('enter_event_id_to_view','Masukkan nomor event untuk melihat detail')} (0=Quit): "
        ).strip()

        if user_input in ("0", ""):
            break

        if not user_input.isdigit():
            print(color_text(t.get("invalid_input", "Input tidak valid"), Colors.RED))
            input(t["press_enter"])
            continue

        num = int(user_input)

        # user selects by table row number (1-based)
        if 1 <= num <= len(sorted_events):
            selected = sorted_events[num - 1]
            # Directly show detail for the selected event (no re-picking)
            view_event_detail([selected], t, direct=True)
            # after closing detail, loop will re-render the same sorted table
        else:
            print(
                color_text(
                    t.get("event_not_found", "Event tidak ditemukan"), Colors.YELLOW
                )
            )
            input(t["press_enter"])
