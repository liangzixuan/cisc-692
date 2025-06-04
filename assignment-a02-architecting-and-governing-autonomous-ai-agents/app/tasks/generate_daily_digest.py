import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "notegpt.db")

def generate_daily_digest():
    """
    1) Query all academic summaries created in the last day
    2) Write them to archives/digest_{date}.txt
    3) Insert a record into the digests table
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Compute yesterday’s midnight in UTC
    yesterday_midnight = (datetime.utcnow() - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).strftime("%Y-%m-%d %H:%M:%S")

    # Fetch academic summaries created since yesterday midnight
    cur.execute("""
        SELECT s.summary_text 
        FROM summaries s
        JOIN documents d ON s.doc_id = d.doc_id
        WHERE d.doc_type = 'academic'
          AND s.created_at >= ?
    """, (yesterday_midnight,))
    rows = cur.fetchall()

    if not rows:
        print("No academic summaries found for yesterday.")
        conn.close()
        return

    # Prepare archive directory
    archive_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "archives")
    os.makedirs(archive_dir, exist_ok=True)

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    digest_filename = os.path.join(archive_dir, f"digest_{today_str}.txt")

    with open(digest_filename, "w", encoding="utf-8") as f:
        f.write(f"Daily Academic Study Guide for {today_str}\n")
        f.write("="*50 + "\n\n")
        for idx, (summary,) in enumerate(rows, start=1):
            f.write(f"{idx}. {summary}\n\n")

    # Record digest in SQL
    digest_date = today_str  # just the date portion
    cur.execute("""
        INSERT INTO digests (digest_date, file_path)
        VALUES (?, ?);
    """, (digest_date, digest_filename))
    conn.commit()
    conn.close()

    print(f"Generated daily digest: {digest_filename}")

if __name__ == "__main__":
    generate_daily_digest()
