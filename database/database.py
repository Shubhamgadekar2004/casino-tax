"""
Database Connection & Initialization
"""
import sqlite3
import os
from pathlib import Path
from config.settings import DATABASE_PATH, BASE_DIR


def get_connection() -> sqlite3.Connection:
    """Get a database connection with foreign keys enabled."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database schema."""
    schema_path = BASE_DIR / "database" / "schema.sql"
    conn = get_connection()
    try:
        with open(schema_path, "r") as f:
            sql = f.read()
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def reset_database():
    """Reset the database by removing it and re-initializing."""
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    init_database()


def execute_query(query: str, params: tuple = (), fetch: bool = True):
    """Execute a query and return results."""
    conn = get_connection()
    try:
        cursor = conn.execute(query, params)
        if fetch:
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        else:
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


def execute_many(query: str, params_list: list):
    """Execute a query with multiple parameter sets."""
    conn = get_connection()
    try:
        conn.executemany(query, params_list)
        conn.commit()
    finally:
        conn.close()


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    result = execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return len(result) > 0


def get_row_count(table_name: str) -> int:
    """Get the row count of a table."""
    result = execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
    return result[0]["cnt"] if result else 0


def is_database_seeded() -> bool:
    """Check if the database has been seeded with demo data."""
    try:
        if not table_exists("individuals"):
            return False
        return get_row_count("individuals") >= 20
    except Exception:
        return False
