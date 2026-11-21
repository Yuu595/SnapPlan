"""In-memory mock data. Resets whenever the server restarts."""
import copy
from itertools import count

_SEED = [
    # Owned by User A
    {"id": "item_101", "title": "CSCI 3509 Midterm", "category": "exam", "date": "2026-11-20",
     "time": "10:00", "location": "Room 301", "description": "Chapters 1-6.",
     "status": "confirmed", "ownerId": "user-a"},
    {"id": "item_102", "title": "Hackathon poster", "category": "event", "date": "2026-12-05",
     "time": None, "location": "Main hall", "description": None,
     "status": "pending", "ownerId": "user-a"},
    # Owned by User B
    {"id": "item_201", "title": "Submit essay draft", "category": "deadline", "date": "2026-11-25",
     "time": "23:59", "location": None, "description": "Upload to the course portal.",
     "status": "pending", "ownerId": "user-b"},
    {"id": "item_202", "title": "Dentist appointment", "category": "task", "date": "2026-11-28",
     "time": "14:30", "location": "City clinic", "description": None,
     "status": "done", "ownerId": "user-b"},
    # Owned by the administrator
    {"id": "item_301", "title": "Review system alerts", "category": "task", "date": "2026-12-01",
     "time": None, "location": None, "description": "Check the Telegram channel.",
     "status": "pending", "ownerId": "admin"},
]
# Note: "item_999" is intentionally NOT in the data -- use it to demo 404 Not Found.

ITEMS: dict[str, dict] = {}
_counter = count(1000)


def reset() -> None:
    ITEMS.clear()
    for it in _SEED:
        row = copy.deepcopy(it)
        row["createdAt"] = row["updatedAt"] = "2026-11-01T09:00:00Z"
        ITEMS[row["id"]] = row


def new_id() -> str:
    return f"item_{next(_counter)}"


reset()
