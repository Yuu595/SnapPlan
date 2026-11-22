"""HTML greeting page for GET /api/v1/greeting."""
from html import escape

API_VERSION = "v1"
PROJECT_NAME = "SnapPlan"
DESCRIPTION = (
    "SnapPlan is a mobile-friendly web app that turns screenshots of event posters, assignment "
    "deadlines and exam dates into an organized schedule with reminders. It is built for students "
    "and young professionals who save information as screenshots and then lose track of it."
)

TEAM = [
    ("Nazim Aliyev", "19937", "Items CRUD endpoints, seed data, tests, API docs and README"),
    ("Abdulaziz Khalmetov", "27725", "Token auth, validation, error handling, greeting page, example requests"),
    ("Nihat Abdullayev", "10657", "Project proposal: monitoring and alerting (Assignment 1)"),
]

# (method, path, description) -- every endpoint of the API.
ENDPOINTS = [
    ("GET", "/api/v1/greeting", "This HTML page (no token required)."),
    ("GET", "/api/v1/items", "List items (own items; all items for admin). Supports filters and pagination."),
    ("GET", "/api/v1/items/{id}", "Get one item by ID."),
    ("POST", "/api/v1/items", "Create a new item owned by the caller."),
    ("PUT", "/api/v1/items/{id}", "Update (replace) an existing item."),
    ("DELETE", "/api/v1/items/{id}", "Delete an item."),
]


def render() -> str:
    team = "".join(
        f"<tr><td>{escape(n)}</td><td>{escape(i)}</td><td>{escape(r)}</td></tr>" for n, i, r in TEAM)
    eps = "".join(
        f'<tr><td><span class="m {m.lower()}">{m}</span></td><td><code>{escape(p)}</code></td>'
        f"<td>{escape(d)}</td></tr>" for m, p, d in ENDPOINTS)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{PROJECT_NAME} API</title>
<style>
  :root {{ --bg:#f6f7fb; --card:#fff; --ink:#1c2333; --muted:#5b6478; --accent:#3b5bdb; --line:#e3e6ef; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         background:var(--bg); color:var(--ink); line-height:1.6; }}
  main {{ max-width:880px; margin:0 auto; padding:24px 16px 48px; }}
  h1 {{ font-size:2rem; margin:0 0 8px; }}
  h2 {{ font-size:1.2rem; margin:0 0 12px; }}
  section {{ background:var(--card); border:1px solid var(--line); border-radius:12px;
            padding:20px; margin-top:20px; overflow-x:auto; }}
  .status {{ display:inline-block; background:#e6f7ec; color:#17693a; border-radius:999px;
            padding:4px 12px; font-weight:600; font-size:.9rem; }}
  table {{ width:100%; border-collapse:collapse; font-size:.95rem; }}
  th, td {{ text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; }}
  code {{ background:#eef1f8; padding:2px 6px; border-radius:6px; font-size:.9em; word-break:break-all; }}
  .m {{ font-weight:700; font-size:.8rem; padding:2px 8px; border-radius:6px; color:#fff; }}
  .get {{ background:#2f9e44; }} .post {{ background:#1971c2; }}
  .put {{ background:#e8590c; }} .delete {{ background:#e03131; }}
  p {{ margin:0 0 8px; }}
  @media (max-width:600px) {{ h1 {{ font-size:1.6rem; }} th, td {{ padding:6px 6px; font-size:.88rem; }} }}
</style>
</head>
<body>
<main>
  <h1>Welcome to {PROJECT_NAME}</h1>
  <p>{escape(DESCRIPTION)}</p>

  <section>
    <h2>Status</h2>
    <p><span class="status">&#9679; API is running</span> &nbsp; Version: <strong>{API_VERSION}</strong></p>
    <p>Authenticate with <code>Authorization: Bearer user-a-token</code>
       (also <code>user-b-token</code> or <code>admin-token</code>). Data is mocked and resets on restart.</p>
  </section>

  <section>
    <h2>Team members</h2>
    <table><thead><tr><th>Name</th><th>Student ID</th><th>What they built</th></tr></thead>
    <tbody>{team}</tbody></table>
  </section>

  <section>
    <h2>Available endpoints</h2>
    <table><thead><tr><th>Method</th><th>Path</th><th>Description</th></tr></thead>
    <tbody>{eps}</tbody></table>
  </section>
</main>
</body>
</html>"""
