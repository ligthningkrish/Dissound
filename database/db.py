"""
Database initialization and connection management using aiosqlite.
"""
import aiosqlite
from pathlib import Path
from config import DATABASE_PATH
from core.logger import log

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sounds (
    sound_id TEXT PRIMARY KEY,
    sound_name TEXT NOT NULL,
    category TEXT NOT NULL,
    file_path TEXT NOT NULL,
    duration REAL NOT NULL,
    file_size INTEGER NOT NULL,
    file_format TEXT NOT NULL,
    source_url TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servers (
    server_id TEXT PRIMARY KEY,
    server_name TEXT NOT NULL,
    sound_limit INTEGER NOT NULL DEFAULT 8,
    bot_role_id TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    permissions TEXT DEFAULT 'member'
);

CREATE TABLE IF NOT EXISTS upload_history (
    upload_id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    sound_id TEXT NOT NULL,
    sound_name TEXT NOT NULL,
    upload_status TEXT NOT NULL,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sounds_category ON sounds(category);
CREATE INDEX IF NOT EXISTS idx_sounds_tags ON sounds(tags);
CREATE INDEX IF NOT EXISTS idx_upload_history_server ON upload_history(server_id);
"""

async def init_db(db_path: Path = DATABASE_PATH) -> None:
    """Initialize database tables and indexes."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA_SQL)
        # Migrate schema if bot_role_id column is missing
        try:
            await db.execute("ALTER TABLE servers ADD COLUMN bot_role_id TEXT DEFAULT NULL")
        except Exception:
            pass
        await db.commit()
    log.info(f"Database initialized successfully at {db_path}")

def get_connection(db_path: Path = DATABASE_PATH):
    """Context manager for obtaining an aiosqlite connection."""
    return aiosqlite.connect(db_path)
