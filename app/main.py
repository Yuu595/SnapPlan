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


@api.get("/greeting", response_class=HTMLResponse, summary="HTML greeting page")
def get_greeting():
    return HTMLResponse(greeting.render(), media_type="text/html; charset=utf-8")


app.include_router(api)
