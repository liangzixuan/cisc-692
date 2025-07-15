# Real Python functions for each tool
import pathlib, aiosqlite, json, csv, os, datetime, uuid

DB_PATH = "data/prospects.db"
LOG_CSV = "logs/action_log.csv"
os.makedirs("sent", exist_ok=True)
os.makedirs("logs", exist_ok=True)

DB_PATH = "data/prospects.db"
TABLE_SQL = """
CREATE TABLE IF NOT EXISTS prospects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  company TEXT,
  email TEXT,
  tier TEXT,
  last_demo_date TEXT
);
"""

async def lookup_prospect(name: str, company: str):
    # ensure DB and table exist
    pathlib.Path("data").mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(TABLE_SQL)
        await db.commit()
        # (optional) INSERT a placeholder row if prospect not found
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM prospects WHERE name=? AND company=? LIMIT 1",
            (name, company)
        )
        row = await cur.fetchone()
        return dict(row) if row else {}

def craft_email(prospect_json: dict | None = None, **kwargs):
    """
    Accept either a single dict (preferred) or loose kwargs (name, email, company).
    """
    if prospect_json is None:
        # fallback to kwargs
        prospect_json = kwargs

    name    = prospect_json.get("name", "there")
    company = prospect_json.get("company", "your company")
    email   = prospect_json.get("email", "unknown@example.com")

    return {
        "to": email,
        "subject": f"{name}, let’s schedule your {company} product demo 🚀",
        "body": (
            f"Hi {name},\n\n"
            "Thanks for your interest! We’d love to show you a 15-minute live demo "
            "tailored to your goals. What time works best next week?\n\n"
            "Best,\nSales AI Assistant"
        )
    }


def send_email(email_dict: dict):
    fname = f"sent/{uuid.uuid4()}.txt"
    with open(fname, "w") as f:
        f.write(json.dumps(email_dict, indent=2))
    return {"status": "sent", "path": fname}

def record_action(action_type: str | None = None,
                  payload: dict | None = None,
                  **kwargs):
    """
    Append a row to logs/action_log.csv.

    Accepts either:
      • record_action(action_type="demo_invite", payload={...})
      • record_action(demo_invite_sent={...})      ← fallback (kwargs)
    """
    # Fallback: if model supplied something like {"demo_invite_sent": {...}}
    if action_type is None and kwargs:
        # grab first key/value
        action_type, payload = next(iter(kwargs.items()))

    if action_type is None:
        action_type = "unknown"
    if payload is None:
        payload = {}

    now = datetime.datetime.utcnow().isoformat()
    with open(LOG_CSV, "a", newline="") as f:
        csv.writer(f).writerow([now, action_type, json.dumps(payload)])

    return {"logged": True, "action_type": action_type}
