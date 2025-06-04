import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "notegpt.db")

def initialize_database():
    """
    Creates the SQLite database and all required tables if they don't exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            role TEXT NOT NULL,                -- FreeUser, PremiumUser, Reviewer, Admin
            subscription_tier TEXT NOT NULL     -- e.g., Free, Premium
        );
    """)

    # Create documents table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            original_filename TEXT,
            raw_text TEXT,
            doc_type TEXT,
            status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)

    # Create summaries table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT NOT NULL,
            summary_text TEXT,
            notes_json TEXT,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
        );
    """)

    # Create policies table (key_name, value stored as JSON or string)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        );
    """)

    # Create digests table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS digests (
            digest_id INTEGER PRIMARY KEY AUTOINCREMENT,
            digest_date DATE NOT NULL,
            file_path TEXT NOT NULL
        );
    """)

    conn.commit()
    conn.close()


def get_db_connection():
    """Helper to get a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def insert_user(user_id: str, username: str, role: str, tier: str):
    """Insert a new user into the users table."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO users (user_id, username, role, subscription_tier)
        VALUES (?, ?, ?, ?);
    """, (user_id, username, role, tier))
    conn.commit()
    conn.close()


def insert_document(doc_id: str, user_id: str, filename: str, raw_text: str, doc_type: str, status: str):
    """Insert a new document record."""
    now = datetime.utcnow()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO documents
        (doc_id, user_id, original_filename, raw_text, doc_type, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (doc_id, user_id, filename, raw_text, doc_type, status, now))
    conn.commit()
    conn.close()


def update_document_status(doc_id: str, status: str, doc_type: str = None):
    """Update status (and optionally doc_type) of an existing document."""
    now = datetime.utcnow()
    conn = get_db_connection()
    cur = conn.cursor()
    if doc_type:
        cur.execute("""
            UPDATE documents 
            SET status = ?, doc_type = ?, updated_at = ?
            WHERE doc_id = ?;
        """, (status, doc_type, now, doc_id))
    else:
        cur.execute("""
            UPDATE documents 
            SET status = ?, updated_at = ?
            WHERE doc_id = ?;
        """, (status, now, doc_id))
    conn.commit()
    conn.close()


def insert_summary(doc_id: str, summary_text: str, notes_json: str):
    """Insert the generated summary and notes."""
    now = datetime.utcnow()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO summaries (doc_id, summary_text, notes_json, created_at)
        VALUES (?, ?, ?, ?);
    """, (doc_id, summary_text, notes_json, now))
    conn.commit()
    conn.close()


def fetch_policies():
    """
    Return all policies as a dictionary { key_name: value }.
    The value is the raw text string stored in the table.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT key_name, value FROM policies;")
    rows = cur.fetchall()
    conn.close()
    policies = { row["key_name"]: row["value"] for row in rows }
    return policies


def upsert_policy(key_name: str, value: str):
    """Insert or update a policy key/value."""
    conn = get_db_connection()
    cur = conn.cursor()
    # If key_name exists, update; else, insert
    cur.execute("""
        INSERT INTO policies (key_name, value) 
        VALUES (?, ?)
        ON CONFLICT(key_name) DO UPDATE SET value=excluded.value;
    """, (key_name, value))
    conn.commit()
    conn.close()
