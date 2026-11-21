import pytest
from fastapi.testclient import TestClient

from app import store
from app.main import app

client = TestClient(app, raise_server_exceptions=False)
A = {"Authorization": "Bearer user-a-token"}
B = {"Authorization": "Bearer user-b-token"}
ADMIN = {"Authorization": "Bearer admin-token"}
BASE = "/api/v1/items"
GOOD = {"title": "Physics quiz", "category": "exam", "date": "2026-12-10"}


@pytest.fixture(autouse=True)
def fresh():
    store.reset()


def err(r, status, code):
    assert r.status_code == status, r.text
    b = r.json()
    assert b["success"] is False and b["error"]["code"] == code and b["error"]["message"]
    return b["error"]


# ---- auth
def test_no_token_401():
    err(client.get(BASE), 401, "UNAUTHORIZED")

def test_bad_token_401():
    err(client.get(BASE, headers={"Authorization": "Bearer nope"}), 401, "UNAUTHORIZED")

def test_malformed_header_401():
    err(client.get(BASE, headers={"Authorization": "user-a-token"}), 401, "UNAUTHORIZED")

def test_401_on_every_item_endpoint():
    for m, p in [("get", BASE), ("get", BASE + "/item_101"), ("post", BASE),
                 ("put", BASE + "/item_101"), ("delete", BASE + "/item_101")]:
        err(getattr(client, m)(p), 401, "UNAUTHORIZED")


# ---- list
def test_list_own_only():
    r = client.get(BASE, headers=A)
    assert r.status_code == 200
    b = r.json()
    assert b["success"] and {i["ownerId"] for i in b["data"]} == {"user-a"}
    assert b["meta"] == {"total": 2, "page": 1, "perPage": 10}

def test_admin_lists_all():
    assert client.get(BASE, headers=ADMIN).json()["meta"]["total"] == 5

def test_filters_and_pagination():
    b = client.get(BASE + "?category=exam", headers=A).json()
    assert [i["id"] for i in b["data"]] == ["item_101"]
    b = client.get(BASE + "?page=2&perPage=1", headers=A).json()
    assert len(b["data"]) == 1 and b["meta"] == {"total": 2, "page": 2, "perPage": 1}

@pytest.mark.parametrize("q", ["category=x", "status=x", "page=0", "perPage=101", "page=abc", "foo=1"])
def test_bad_query_400(q):
    e = err(client.get(f"{BASE}?{q}", headers=A), 400, "VALIDATION_ERROR")
    assert e["details"]


# ---- get one + ownership
def test_get_own():
    r = client.get(BASE + "/item_101", headers=A)
    assert r.status_code == 200 and r.json()["data"]["id"] == "item_101"

def test_cross_user_isolation_all_ops():
    body = dict(GOOD)
    for h, other in ((A, "item_201"), (B, "item_101")):
        err(client.get(f"{BASE}/{other}", headers=h), 404, "NOT_FOUND")
        err(client.put(f"{BASE}/{other}", headers=h, json=body), 404, "NOT_FOUND")
        err(client.delete(f"{BASE}/{other}", headers=h), 404, "NOT_FOUND")
    assert "item_101" in store.ITEMS and "item_201" in store.ITEMS

def test_admin_access_any():
    assert client.get(BASE + "/item_101", headers=ADMIN).status_code == 200
    assert client.put(BASE + "/item_201", headers=ADMIN, json=GOOD).status_code == 200
    assert client.delete(BASE + "/item_102", headers=ADMIN).status_code == 200

def test_nonexistent_404():
    for m in ("get", "delete"):
        err(getattr(client, m)(BASE + "/item_999", headers=A), 404, "NOT_FOUND")
    err(client.put(BASE + "/item_999", headers=ADMIN, json=GOOD), 404, "NOT_FOUND")


# ---- create
def test_create_201():
    r = client.post(BASE, headers=A, json={**GOOD, "location": "Lab"})
    assert r.status_code == 201
    d = r.json()["data"]
    assert d["ownerId"] == "user-a" and d["status"] == "pending" and d["location"] == "Lab"
    assert client.get(f"{BASE}/{d['id']}", headers=A).status_code == 200
    err(client.get(f"{BASE}/{d['id']}", headers=B), 404, "NOT_FOUND")

@pytest.mark.parametrize("body,field", [
    ({}, "title"),
    ({**GOOD, "title": "ab"}, "title"),
    ({**GOOD, "title": 5}, "title"),
    ({**GOOD, "title": "x" * 101}, "title"),
    ({**GOOD, "category": "party"}, "category"),
    ({**GOOD, "date": "10-12-2026"}, "date"),
    ({**GOOD, "date": "2026-02-30"}, "date"),
    ({**GOOD, "date": "20261210"}, "date"),
    ({**GOOD, "time": "25:00"}, "time"),
    ({**GOOD, "location": 3}, "location"),
    ({**GOOD, "description": "x" * 501}, "description"),
    ({**GOOD, "status": "weird"}, "status"),
    ({**GOOD, "ownerId": "admin"}, "ownerId"),
    ({**GOOD, "id": "item_1"}, "id"),
    ({**GOOD, "bogus": 1}, "bogus"),
])
def test_create_validation_400(body, field):
    e = err(client.post(BASE, headers=A, json=body), 400, "VALIDATION_ERROR")
    assert field in [d["field"] for d in e["details"]]

def test_create_bad_json_and_non_object():
    err(client.post(BASE, headers={**A, "Content-Type": "application/json"}, content="{bad"), 400, "VALIDATION_ERROR")
    err(client.post(BASE, headers=A, json=[1]), 400, "VALIDATION_ERROR")

def test_create_duplicate_409():
    assert client.post(BASE, headers=A, json=GOOD).status_code == 201
    err(client.post(BASE, headers=A, json=GOOD), 409, "CONFLICT")
    assert client.post(BASE, headers=B, json=GOOD).status_code == 201  # other user is fine


# ---- update
def test_put_200_and_replace_semantics():
    r = client.put(BASE + "/item_101", headers=A, json=GOOD)
    d = r.json()["data"]
    assert r.status_code == 200 and d["title"] == "Physics quiz"
    assert d["location"] is None and d["status"] == "confirmed" and d["ownerId"] == "user-a"

def test_put_validation_400():
    err(client.put(BASE + "/item_101", headers=A, json={"title": "x"}), 400, "VALIDATION_ERROR")

def test_put_done_back_to_pending_409():
    err(client.put(BASE + "/item_202", headers=B, json={**GOOD, "status": "pending"}), 409, "CONFLICT")

def test_put_duplicate_409():
    err(client.put(BASE + "/item_102", headers=A,
                   json={"title": "CSCI 3509 Midterm", "category": "exam", "date": "2026-11-20"}), 409, "CONFLICT")


# ---- delete
def test_delete_200_then_404():
    r = client.delete(BASE + "/item_101", headers=A)
    assert r.status_code == 200 and r.json() == {
        "success": True, "message": "Item deleted successfully.", "data": None}
    err(client.get(BASE + "/item_101", headers=A), 404, "NOT_FOUND")


# ---- 404 / 405 / 500 envelope
def test_unknown_path_404():
    err(client.get("/api/v1/nothing"), 404, "NOT_FOUND")

def test_405():
    r = client.patch(BASE + "/item_101", headers=A)
    err(r, 405, "METHOD_NOT_ALLOWED")
    err(client.delete(BASE, headers=A), 405, "METHOD_NOT_ALLOWED")
    err(client.post("/api/v1/greeting"), 405, "METHOD_NOT_ALLOWED")

def test_500_hides_internals(monkeypatch):
    def boom(*a, **k): raise RuntimeError("secret /etc/passwd SELECT *")
    monkeypatch.setattr("app.main.store.new_id", boom)
    r = client.post(BASE, headers=A, json=GOOD)
    e = err(r, 500, "INTERNAL_ERROR")
    assert "secret" not in r.text and "passwd" not in r.text


# ---- greeting
def test_greeting_html():
    r = client.get("/api/v1/greeting")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/html; charset=utf-8"
    t = r.text
    for s in ("<!DOCTYPE html>", "viewport", "SnapPlan", "Nazim Aliyev", "Abdulaziz Khalmetov",
              "Nihat Abdullayev", "/api/v1/items/{id}", "v1", "running"):
        assert s in t
