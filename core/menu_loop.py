# --------------------------
# Menus (visitor & organizer) now accept current_user for attendance/review
# --------------------------
from datetime import datetime
from typing import List, Dict, Any
from utils.colors import Colors, color_text
from utils.clear import clear_screen
from core.actions import *
from utils.parser import *
from utils.storage import *
from localizations.translations import TRANSLATIONS


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
        else:
            print(color_text(t["invalid_choice"], Colors.RED))
            input(t["press_enter"])
