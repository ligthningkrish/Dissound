"""
Data Access Object (DAO) repository for Dissound database.
"""
from typing import List, Optional
import aiosqlite
from database.db import get_connection
from database.models import Sound, Server, User, UploadHistoryItem

class Repository:
    def __init__(self, connection_factory=get_connection):
        self._get_conn = connection_factory

    # --- Sound Operations ---

    async def add_sound(self, sound: Sound) -> None:
        """Insert or replace a sound record."""
        async with self._get_conn() as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO sounds 
                (sound_id, sound_name, category, file_path, duration, file_size, file_format, source_url, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sound.sound_id,
                    sound.sound_name,
                    sound.category,
                    sound.file_path,
                    sound.duration,
                    sound.file_size,
                    sound.file_format,
                    sound.source_url,
                    sound.tags
                )
            )
            await db.commit()

    async def get_sound(self, sound_id: str) -> Optional[Sound]:
        """Retrieve a sound by its unique ID."""
        async with self._get_conn() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sounds WHERE sound_id = ?", (sound_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Sound(**dict(row))
        return None

    async def get_sound_by_name(self, sound_name: str) -> Optional[Sound]:
        """Retrieve a sound by name (case-insensitive)."""
        async with self._get_conn() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM sounds WHERE LOWER(sound_name) = LOWER(?) LIMIT 1",
                (sound_name,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Sound(**dict(row))
        return None

    async def search_sounds(self, query: str, limit: int = 25) -> List[Sound]:
        """Search sounds by query in sound_name, category, or tags."""
        term = f"%{query.strip().lower()}%"
        async with self._get_conn() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM sounds 
                WHERE LOWER(sound_name) LIKE ? 
                   OR LOWER(category) LIKE ? 
                   OR LOWER(tags) LIKE ?
                ORDER BY 
                    CASE WHEN LOWER(sound_name) LIKE ? THEN 1 ELSE 2 END,
                    sound_name ASC
                LIMIT ?
                """,
                (term, term, term, term, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Sound(**dict(row)) for row in rows]

    async def get_all_sounds(self, limit: int = 100) -> List[Sound]:
        """Retrieve all sounds in the library."""
        async with self._get_conn() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sounds ORDER BY sound_name ASC LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [Sound(**dict(row)) for row in rows]

    async def get_sounds_by_category(self, category: str) -> List[Sound]:
        """Retrieve all sounds belonging to a given category."""
        async with self._get_conn() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM sounds WHERE LOWER(category) = LOWER(?) ORDER BY sound_name ASC",
                (category,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Sound(**dict(row)) for row in rows]

    async def get_categories(self) -> List[str]:
        """Get distinct list of sound categories."""
        async with self._get_conn() as db:
            async with db.execute("SELECT DISTINCT category FROM sounds ORDER BY category ASC") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows if row[0]]

    async def get_trending_sounds(self, limit: int = 10) -> List[Sound]:
        """Get trending sounds based on successful uploads."""
        async with self._get_conn() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT s.*, COUNT(h.upload_id) as upload_count
                FROM sounds s
                LEFT JOIN upload_history h ON s.sound_id = h.sound_id AND h.upload_status = 'SUCCESS'
                GROUP BY s.sound_id
                ORDER BY upload_count DESC, s.sound_name ASC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Sound(**{k: v for k, v in dict(row).items() if k != "upload_count"}) for row in rows]

    async def get_recent_sounds(self, limit: int = 10) -> List[Sound]:
        """Get most recently added sounds in library."""
        async with self._get_conn() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sounds ORDER BY created_at DESC LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [Sound(**dict(row)) for row in rows]

    # --- Server Operations ---

    async def upsert_server(self, server_id: str, server_name: str, sound_limit: int = 8, bot_role_id: Optional[str] = None) -> None:
        """Register or update server details."""
        async with self._get_conn() as db:
            await db.execute(
                """
                INSERT INTO servers (server_id, server_name, sound_limit, bot_role_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(server_id) DO UPDATE SET
                    server_name = excluded.server_name,
                    sound_limit = excluded.sound_limit,
                    bot_role_id = COALESCE(excluded.bot_role_id, servers.bot_role_id)
                """,
                (str(server_id), server_name, sound_limit, str(bot_role_id) if bot_role_id else None)
            )
            await db.commit()

    async def set_server_bot_role(self, server_id: str, role_id: Optional[str]) -> None:
        """Configure designated role required to use the bot in a server."""
        async with self._get_conn() as db:
            await db.execute(
                """
                INSERT INTO servers (server_id, server_name, bot_role_id)
                VALUES (?, 'Unknown Server', ?)
                ON CONFLICT(server_id) DO UPDATE SET
                    bot_role_id = excluded.bot_role_id
                """,
                (str(server_id), str(role_id) if role_id else None)
            )
            await db.commit()

    async def get_server(self, server_id: str) -> Optional[Server]:
        """Retrieve server record."""
        async with self._get_conn() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM servers WHERE server_id = ?", (str(server_id),)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Server(**dict(row))
        return None

    # --- User Operations ---

    async def upsert_user(self, user_id: str, username: str, permissions: str = "member") -> None:
        """Record or update user."""
        async with self._get_conn() as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username, permissions)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    permissions = excluded.permissions
                """,
                (str(user_id), username, permissions)
            )
            await db.commit()

    # --- Upload History Operations ---

    async def log_upload(
        self,
        server_id: str,
        user_id: str,
        sound_id: str,
        sound_name: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Log a soundboard upload attempt."""
        async with self._get_conn() as db:
            await db.execute(
                """
                INSERT INTO upload_history 
                (server_id, user_id, sound_id, sound_name, upload_status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (str(server_id), str(user_id), sound_id, sound_name, status, error_message)
            )
            await db.commit()

    async def get_server_history(self, server_id: str, limit: int = 10) -> List[UploadHistoryItem]:
        """Fetch upload history for a server ordered by most recent."""
        async with self._get_conn() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM upload_history 
                WHERE server_id = ? 
                ORDER BY upload_id DESC, timestamp DESC 
                LIMIT ?
                """,
                (str(server_id), limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [UploadHistoryItem(**dict(row)) for row in rows]
