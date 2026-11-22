# SnapPlan API Documentation (v1)

Base URL: `http://127.0.0.1:8000/api/v1` · Interactive Swagger UI: `http://127.0.0.1:8000/docs` · OpenAPI JSON: `/openapi.json`

Main resource: **`items`** — a schedule item (event, task, exam or deadline) extracted from a screenshot.

## 1. Conventions

### Authentication
Send a mock token in every `/items` request:
```http
Authorization: Bearer <token>
```
| Role | Token | Permissions |
|---|---|---|
| Regular user A (`user-a`) | `user-a-token` | Manages only own items |
| Regular user B (`user-b`) | `user-b-token` | Manages only own items |
| Administrator (`admin`) | `admin-token` | Reads, updates and deletes **all** items |

Missing token, wrong format or unknown token → `401 UNAUTHORIZED`. `/greeting` needs no token.

### Authorization choice: 404 instead of 403
When a regular user touches another user's item, the API returns **`404 Not Found`**, the same answer as for an item that does not exist. A `403` would confirm that the item exists, which leaks private data (an attacker could probe IDs). `403 FORBIDDEN` is reserved for role-based denials; the current mock API has no admin-only endpoints, so it is defined but not triggered.

### Response envelope
Success:
```json
{ "success": true, "message": "Item created successfully.", "data": { } }
```
List responses add `"meta": {"total": 5, "page": 1, "perPage": 10}`. Delete returns `"data": null`.

Error:
```json
{ "success": false,
  "error": { "code": "VALIDATION_ERROR",
             "message": "The request contains invalid or missing fields.",
             "details": [ { "field": "title", "message": "Title must contain between 3 and 100 characters." } ] } }
```
`details` appears only for validation errors. Messages never contain stack traces, SQL, file paths or internals. The HTTP status always matches the envelope (`2xx` ↔ `success: true`).

### Error codes
| `error.code` | HTTP | Meaning |
|---|---:|---|
| `VALIDATION_ERROR` | 400 | Invalid/missing body fields, invalid JSON, bad query parameters |
| `UNAUTHORIZED` | 401 | Token missing, malformed or invalid |
| `FORBIDDEN` | 403 | Authenticated but not allowed (reserved; see authorization choice) |
| `NOT_FOUND` | 404 | Item does not exist, belongs to someone else, or unknown endpoint |
| `METHOD_NOT_ALLOWED` | 405 | HTTP method not supported for the endpoint |
| `CONFLICT` | 409 | Duplicate item, or illegal status change |
| `INTERNAL_ERROR` | 500 | Unexpected server error (generic message only) |

### The item object
| Field | Type | Notes |
|---|---|---|
| `id` | string | e.g. `item_101`, read-only |
| `title` | string | required, 3–100 chars |
| `category` | string | required: `event`, `task`, `exam`, `deadline`, `other` |
| `date` | string | required, real date `YYYY-MM-DD` |
| `time` | string \| null | optional, `HH:MM` (24h) |
| `location` | string \| null | optional, ≤100 chars |
| `description` | string \| null | optional, ≤500 chars |
| `status` | string | `pending` (default), `confirmed`, `done` |
| `ownerId` | string | read-only, set from the token |
| `createdAt`, `updatedAt` | string | read-only, ISO 8601 UTC |

Sending an unknown or read-only field (`id`, `ownerId`, `createdAt`, …) → `400`.

### Mock data (resets on restart)
| ID | Owner | Title |
|---|---|---|
| `item_101`, `item_102` | user-a | CSCI 3509 Midterm; Hackathon poster |
| `item_201`, `item_202` | user-b | Submit essay draft; Dentist appointment (done) |
| `item_301` | admin | Review system alerts |
| `item_999` | — | **does not exist**, use it to demo `404` |

Check order for item endpoints: authentication (401) → resource lookup/ownership (404) → body validation (400) → conflict (409).

---

## 2. Endpoints

### GET `/api/v1/greeting`
HTML page: project description, team, endpoint list, status. **Auth:** none. **Response:** `200`, `Content-Type: text/html; charset=utf-8`. **Errors:** `405` for non-GET methods.

---

### GET `/api/v1/items` — list items
**Auth:** any valid token. A regular user sees own items; admin sees all.
**Headers:** `Authorization: Bearer <token>`

| Query param | Type | Default | Rule |
|---|---|---|---|
| `category` | string | — | one of the categories |
| `status` | string | — | `pending`/`confirmed`/`done` |
| `page` | integer | 1 | ≥ 1 |
| `perPage` | integer | 10 | 1–100 |

Unknown query parameters → `400`. Sorted by date, time, id.
**Success `200`**, **Errors:** `400`, `401`.

Example: `GET /api/v1/items?category=exam` with `user-a-token`
```json
{ "success": true, "message": "Items retrieved successfully.",
  "data": [ { "id": "item_101", "title": "CSCI 3509 Midterm", "category": "exam", "date": "2026-11-20",
              "time": "10:00", "location": "Room 301", "description": "Chapters 1-6.",
              "status": "confirmed", "ownerId": "user-a",
              "createdAt": "2026-11-01T09:00:00Z", "updatedAt": "2026-11-01T09:00:00Z" } ],
  "meta": { "total": 1, "page": 1, "perPage": 10 } }
```

---

### GET `/api/v1/items/{id}` — get one item
**Auth:** owner or admin. **Path:** `id` (string, e.g. `item_101`).
**Success `200`**. **Errors:** `401`; `404` (missing or not yours).

Example: `GET /api/v1/items/item_201` with `user-a-token` →
```json
{ "success": false, "error": { "code": "NOT_FOUND", "message": "Item 'item_201' was not found." } }
```

---

### POST `/api/v1/items` — create
**Auth:** any valid token; `ownerId` is taken from the token.
**Headers:** `Authorization`, `Content-Type: application/json`
**Body:** item fields (`title`, `category`, `date` required; others optional).
**Validation:** required fields; types; title 3–100; category/status enum; real `YYYY-MM-DD` date; `HH:MM` time; location ≤100; description ≤500; no unknown fields; body must be a JSON object.
**Success `201`**. **Errors:** `400`, `401`, `409` (same owner already has an item with the same title on the same date; case-insensitive).

Request:
```json
{ "title": "Physics quiz", "category": "exam", "date": "2026-12-10", "time": "09:30" }
```
Response `201`:
```json
{ "success": true, "message": "Item created successfully.",
  "data": { "id": "item_1000", "title": "Physics quiz", "category": "exam", "date": "2026-12-10",
            "time": "09:30", "location": null, "description": null, "status": "pending",
            "ownerId": "user-a", "createdAt": "2026-11-21T10:00:00Z", "updatedAt": "2026-11-21T10:00:00Z" } }
```
Validation error `400`:
```json
{ "success": false,
  "error": { "code": "VALIDATION_ERROR", "message": "The request contains invalid or missing fields.",
             "details": [ { "field": "title", "message": "Title must contain between 3 and 100 characters." },
                          { "field": "category", "message": "Category must be one of: event, task, exam, deadline, other." },
                          { "field": "date", "message": "Date must be a real calendar date in YYYY-MM-DD format." } ] } }
```

---

### PUT `/api/v1/items/{id}` — update (replace)
**Auth:** owner or admin (the owner never changes). **Body:** same as POST. `title`, `category`, `date` are required; omitted optional fields are reset to `null`; omitted `status` keeps the current value.
**Success `200`**. **Errors:** `400`, `401`, `404`, `409` (duplicate title+date for the owner, or moving a `done` item back to `pending`/`confirmed`).

Request: `PUT /api/v1/items/item_102` (user-a)
```json
{ "title": "Hackathon poster (updated)", "category": "event", "date": "2026-12-06", "status": "confirmed" }
```
Response `200` → `{"success": true, "message": "Item updated successfully.", "data": { ...updated item... }}`

Conflict `409`:
```json
{ "success": false, "error": { "code": "CONFLICT",
  "message": "A completed item cannot be moved back to 'pending'. Delete it or create a new item instead." } }
```

---

### DELETE `/api/v1/items/{id}` — delete
**Auth:** owner or admin. **Success `200`**, **Errors:** `401`, `404`.
```json
{ "success": true, "message": "Item deleted successfully.", "data": null }
```

---

### Other errors on every endpoint
Unknown path → `404 NOT_FOUND`; unsupported method (e.g. `PATCH /items/item_101`, `DELETE /items`) → `405 METHOD_NOT_ALLOWED`; unexpected failure → `500 INTERNAL_ERROR` with a generic message.
