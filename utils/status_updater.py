from datetime import datetime
from typing import List, Dict, Any


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
