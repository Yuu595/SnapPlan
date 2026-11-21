"""SnapPlan API prototype (mock data, token auth, RBAC). Run: uvicorn app.main:app --reload"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from . import greeting, store
from .auth import get_current_user
from .errors import (ApiError, CONFLICT, NOT_FOUND, VALIDATION_ERROR, ok, register_handlers)
from .validation import validate_item_body, validate_list_query

app = FastAPI(title="SnapPlan API", version="1.0.0",
              description="Mocked REST API for SnapPlan schedule items. "
                          "Authorize with Bearer tokens: user-a-token, user-b-token, admin-token.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
register_handlers(app)

api = APIRouter(prefix="/api/v1")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get_accessible(item_id: str, user: dict) -> dict:
    """Return the item if it exists AND the user may access it, else 404.

    A regular user asking for someone else's item gets the same 404 as for a missing item,
    so the API does not reveal that another user's private item exists.
    """
    item = store.ITEMS.get(item_id)
    if item is None or (user["role"] != "admin" and item["ownerId"] != user["id"]):
        raise ApiError(404, NOT_FOUND, f"Item '{item_id}' was not found.")
    return item


def _is_duplicate(owner: str, title: str, date: str, exclude_id: str | None = None) -> bool:
    return any(i["ownerId"] == owner and i["date"] == date and i["id"] != exclude_id
               and i["title"].lower() == title.lower() for i in store.ITEMS.values())


async def _read_body(request: Request):
    try:
        return await request.json()
    except Exception:
        raise ApiError(400, VALIDATION_ERROR, "The request body must be valid JSON.",
                       [{"field": "body", "message": "Send a valid JSON object with the header "
                                                     "'Content-Type: application/json'."}])


def _raise_if_invalid(details):
    if details:
        raise ApiError(400, VALIDATION_ERROR, "The request contains invalid or missing fields.", details)


_BODY_SCHEMA = {"requestBody": {"required": True, "content": {"application/json": {"schema": {
    "type": "object", "required": ["title", "category", "date"],
    "properties": {
        "title": {"type": "string", "minLength": 3, "maxLength": 100, "example": "Physics quiz"},
        "category": {"type": "string", "enum": list(("event", "task", "exam", "deadline", "other"))},
        "date": {"type": "string", "example": "2026-12-10"},
        "time": {"type": "string", "nullable": True, "example": "09:30"},
        "location": {"type": "string", "nullable": True},
        "description": {"type": "string", "nullable": True},
        "status": {"type": "string", "enum": ["pending", "confirmed", "done"]}}}}}}}


@api.get("/greeting", response_class=HTMLResponse, summary="HTML greeting page")
def get_greeting():
    return HTMLResponse(greeting.render(), media_type="text/html; charset=utf-8")


@api.get("/items", summary="List items")
def list_items(request: Request, user: dict = Depends(get_current_user),
               category: str | None = Query(None), status: str | None = Query(None),
               page: int | None = Query(None), perPage: int | None = Query(None)):
    q, details = validate_list_query(request.query_params)
    _raise_if_invalid(details)
    rows = [i for i in store.ITEMS.values() if user["role"] == "admin" or i["ownerId"] == user["id"]]
    if q["category"]:
        rows = [i for i in rows if i["category"] == q["category"]]
    if q["status"]:
        rows = [i for i in rows if i["status"] == q["status"]]
    rows.sort(key=lambda i: (i["date"], i["time"] or "", i["id"]))
    start = (q["page"] - 1) * q["perPage"]
    return ok("Items retrieved successfully.", rows[start:start + q["perPage"]],
              meta={"total": len(rows), "page": q["page"], "perPage": q["perPage"]})


@api.get("/items/{item_id}", summary="Get one item")
def get_item(item_id: str, user: dict = Depends(get_current_user)):
    return ok("Item retrieved successfully.", _get_accessible(item_id, user))


@api.post("/items", status_code=201, summary="Create an item", openapi_extra=_BODY_SCHEMA)
async def create_item(request: Request, user: dict = Depends(get_current_user)):
    clean, details = validate_item_body(await _read_body(request))
    _raise_if_invalid(details)
    if _is_duplicate(user["id"], clean["title"], clean["date"]):
        raise ApiError(409, CONFLICT, "You already have an item with this title on this date.")
    now = _now()
    item = {"id": store.new_id(), **clean, "status": clean.get("status", "pending"),
            "ownerId": user["id"], "createdAt": now, "updatedAt": now}
    store.ITEMS[item["id"]] = item
    return ok("Item created successfully.", item, status=201)


@api.put("/items/{item_id}", summary="Update (replace) an item", openapi_extra=_BODY_SCHEMA)
async def update_item(item_id: str, request: Request, user: dict = Depends(get_current_user)):
    item = _get_accessible(item_id, user)  # 401 -> 404 -> 400 -> 409
    clean, details = validate_item_body(await _read_body(request))
    _raise_if_invalid(details)
    new_status = clean.get("status", item["status"])
    if item["status"] == "done" and new_status != "done":
        raise ApiError(409, CONFLICT, "A completed item cannot be moved back to "
                                      f"'{new_status}'. Delete it or create a new item instead.")
    if _is_duplicate(item["ownerId"], clean["title"], clean["date"], exclude_id=item_id):
        raise ApiError(409, CONFLICT, "The owner already has an item with this title on this date.")
    item.update(clean)
    item["status"] = new_status
    item["updatedAt"] = _now()
    return ok("Item updated successfully.", item)


app.include_router(api)
