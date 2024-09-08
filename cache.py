import json
import sqlite3
from pathlib import Path
from typing import Optional

CACHE_DB = Path.home() / ".yr_cli_cache.sqlite"


def init_db():
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                query TEXT PRIMARY KEY,
                location_data JSON,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )


def get_cached_location(query: str) -> Optional[dict]:
    init_db()
    with sqlite3.connect(CACHE_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT json(location_data) as location_data FROM locations WHERE query = ?",
            (query,),
        )
        result = cursor.fetchone()
        if result:
            return json.loads(result["location_data"])
    return None


def cache_location(query: str, location: dict):
    init_db()
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO locations (query, location_data) VALUES (?, json(?))",
            (query, json.dumps(location)),
        )


def clear_cache():
    init_db()
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute("DELETE FROM locations")
    return True
