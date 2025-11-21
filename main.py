import sys

from localizations.translations import TRANSLATIONS
from utils.colors import Colors, color_text
from utils.clear import clear_screen
from utils.storage import *
from core.actions import *
from utils.status_updater import auto_update_event_statuses
from utils.auth import register_user, login_user
from core.menu_loop import visitor_loop, organizer_loop


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
