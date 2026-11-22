# SnapPlan API: Assignment 2 prototype

First functional prototype of **SnapPlan**, an app that turns screenshots into schedule items and reminders. This repo contains the **backend REST API** with **mocked in-memory data**, token authentication, role-based authorization, structured responses, validation and an HTML greeting page.

Course: CSCI 3509 Intro to Software Engineering · Team: Snap Squad · Instructor: Kamila Ismayilova

## Requirements
Python 3.10+.

## Install and run
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
- Greeting page: http://127.0.0.1:8000/api/v1/greeting
- Swagger UI: http://127.0.0.1:8000/docs
- API documentation: [docs/API.md](docs/API.md) · Example requests: [requests.http](requests.http)

### Run the tests
```bash
pytest -q
```

## Mock users
| Role | Header |
|---|---|
| Regular user A | `Authorization: Bearer user-a-token` |
| Regular user B | `Authorization: Bearer user-b-token` |
| Administrator | `Authorization: Bearer admin-token` |

Quick try:
```bash
curl -H "Authorization: Bearer user-a-token" http://127.0.0.1:8000/api/v1/items
```

## Mock data
Data lives in memory (`app/store.py`). **It resets every time the server restarts.** Seed: 2 items for user A, 2 for user B, 1 for admin; `item_999` does not exist (use it for the `404` demo).

## Design decisions
- Resource: `items`, versioned under `/api/v1`, plural nouns, HTTP methods express the action.
- Another user's item returns `404` (not `403`) so private data is not revealed; see docs/API.md.
- All JSON uses the `success` / `message` / `data` (+ `meta`) or `success` / `error` envelope.

## Project structure
```
app/main.py        routes (items CRUD, greeting)
app/auth.py        mock tokens -> user, 401 handling
app/validation.py  body and query validation
app/errors.py      error codes, envelope, exception handlers (400/401/404/405/409/500)
app/store.py       in-memory seed data
app/greeting.py    HTML greeting page
tests/             pytest suite
docs/API.md        full API documentation
```

## Team and contributions
See [CONTRIBUTORS.md](CONTRIBUTORS.md).

| Member | Worked on |
|---|---|
| Nazim Aliyev | Items CRUD endpoints, seed data, tests, API documentation, README |
| Abdulaziz Khalmetov | Authentication, validation, error handling, greeting page, example requests |
| Nihat Abdullayev | Project proposal: monitoring and alerting (Assignment 1) |

### `git shortlog -sn --all`
```
<paste the output of `git shortlog -sn --all` here before submitting>
```

## Demo video
Demo video (CRUD, authorization failures, validation errors, greeting page): https://drive.google.com/drive/folders/122hN96tdHKiawQYyYOtIMnA7PuNjifx-?usp=sharing
