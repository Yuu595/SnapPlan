"""Validation of item request bodies and list query parameters."""
import re
from datetime import datetime

CATEGORIES = ("event", "task", "exam", "deadline", "other")
STATUSES = ("pending", "confirmed", "done")
WRITABLE = {"title", "category", "date", "time", "location", "description", "status"}
REQUIRED = ("title", "category", "date")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _valid_date(v) -> bool:
    if not isinstance(v, str) or not _DATE_RE.match(v):
        return False
    try:
        datetime.strptime(v, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_item_body(body, partial_status_default: bool = True):
    """Return (clean_fields, details). `details` is empty when the body is valid."""
    details: list[dict] = []

    def err(field, msg):
        details.append({"field": field, "message": msg})

    if not isinstance(body, dict):
        return {}, [{"field": "body", "message": "Request body must be a JSON object."}]

    for key in body:
        if key not in WRITABLE:
            err(key, f"Unknown or read-only field '{key}'. Allowed fields: "
                     + ", ".join(sorted(WRITABLE)) + ".")

    for key in REQUIRED:
        if key not in body or body[key] is None:
            err(key, f"{key.capitalize()} is required.")

    clean: dict = {}

    t = body.get("title")
    if t is not None:
        if not isinstance(t, str):
            err("title", "Title must be a string.")
        elif not 3 <= len(t.strip()) <= 100:
            err("title", "Title must contain between 3 and 100 characters.")
        else:
            clean["title"] = t.strip()

    c = body.get("category")
    if c is not None:
        if not isinstance(c, str) or c not in CATEGORIES:
            err("category", "Category must be one of: " + ", ".join(CATEGORIES) + ".")
        else:
            clean["category"] = c

    d = body.get("date")
    if d is not None:
        if not _valid_date(d):
            err("date", "Date must be a real calendar date in YYYY-MM-DD format.")
        else:
            clean["date"] = d

    tm = body.get("time")
    if tm is not None:
        if not isinstance(tm, str) or not _TIME_RE.match(tm):
            err("time", "Time must be in HH:MM 24-hour format, or null.")
    clean["time"] = tm if isinstance(tm, str) and _TIME_RE.match(tm) else None

    for key, limit in (("location", 100), ("description", 500)):
        v = body.get(key)
        if v is not None:
            if not isinstance(v, str):
                err(key, f"{key.capitalize()} must be a string or null.")
            elif len(v) > limit:
                err(key, f"{key.capitalize()} must be at most {limit} characters.")
        clean[key] = v if isinstance(v, str) and len(v) <= limit else None

    if "status" in body:
        s = body["status"]
        if not isinstance(s, str) or s not in STATUSES:
            err("status", "Status must be one of: " + ", ".join(STATUSES) + ".")
        else:
            clean["status"] = s

    return clean, details


def validate_list_query(params) -> tuple[dict, list[dict]]:
    """Validate query parameters of GET /items. `params` is a Starlette QueryParams."""
    details: list[dict] = []
    allowed = {"category", "status", "page", "perPage"}
    for key in params.keys():
        if key not in allowed:
            details.append({"field": key, "message": f"Unknown query parameter '{key}'. "
                            "Allowed: " + ", ".join(sorted(allowed)) + "."})
    q: dict = {"page": 1, "perPage": 10, "category": None, "status": None}

    cat = params.get("category")
    if cat is not None:
        if cat not in CATEGORIES:
            details.append({"field": "category",
                            "message": "Category must be one of: " + ", ".join(CATEGORIES) + "."})
        q["category"] = cat
    st = params.get("status")
    if st is not None:
        if st not in STATUSES:
            details.append({"field": "status",
                            "message": "Status must be one of: " + ", ".join(STATUSES) + "."})
        q["status"] = st

    for key, lo, hi in (("page", 1, None), ("perPage", 1, 100)):
        raw = params.get(key)
        if raw is None:
            continue
        try:
            n = int(raw)
            if n < lo or (hi and n > hi):
                raise ValueError
            q[key] = n
        except ValueError:
            rng = f"an integer between {lo} and {hi}" if hi else f"an integer >= {lo}"
            details.append({"field": key, "message": f"{key} must be {rng}."})
    return q, details
