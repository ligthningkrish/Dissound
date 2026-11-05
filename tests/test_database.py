"""
Unit tests for Dissound Database operations, repository queries, and history logging.
"""
import unittest
import asyncio
from pathlib import Path
import tempfile
import sys

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import init_db, get_connection
from database.models import Sound, Server, User, UploadHistoryItem
from database.repository import Repository

class TestDatabaseRepository(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Create a temporary SQLite database for isolated test execution
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_dissound.db"
        await init_db(self.db_path)

        def test_conn():
            return get_connection(self.db_path)

        self.repo = Repository(connection_factory=test_conn)

    async def asyncTearDown(self):
        self.temp_dir.cleanup()

    async def test_add_and_get_sound(self):
        """Test inserting and retrieving a sound by sound_id and sound_name."""
        sound = Sound(
            sound_id="test_vine_boom",
            sound_name="Vine Boom Test",
            category="Meme Sounds",
            file_path="assets/sounds/vine_boom.mp3",
            duration=1.5,
            file_size=25000,
            file_format="mp3",
            source_url="https://example.com/sound",
            tags="boom, vine, bass"
        )
        await self.repo.add_sound(sound)

        # Retrieve by ID
        fetched = await self.repo.get_sound("test_vine_boom")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.sound_name, "Vine Boom Test")
        self.assertEqual(fetched.category, "Meme Sounds")
        self.assertEqual(fetched.duration, 1.5)

        # Retrieve by Name (case-insensitive)
        by_name = await self.repo.get_sound_by_name("vine boom test")
        self.assertIsNotNone(by_name)
        self.assertEqual(by_name.sound_id, "test_vine_boom")

    async def test_search_sounds(self):
        """Test keyword searching across sound names, categories, and tags."""
        sound1 = Sound(
            sound_id="s1", sound_name="Metal Pipe", category="Random",
            file_path="p1", duration=1.8, file_size=20000, file_format="mp3", tags="clang, loud"
        )
        sound2 = Sound(
            sound_id="s2", sound_name="Windows XP Error", category="Classic",
            file_path="p2", duration=1.2, file_size=15000, file_format="mp3", tags="microsoft, chime"
        )
        await self.repo.add_sound(sound1)
        await self.repo.add_sound(sound2)

        # Search by tag
        res1 = await self.repo.search_sounds("clang")
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0].sound_name, "Metal Pipe")

        # Search by partial name
        res2 = await self.repo.search_sounds("pipe")
        self.assertEqual(len(res2), 1)

        # Search by category
        res3 = await self.repo.search_sounds("classic")
        self.assertEqual(len(res3), 1)
        self.assertEqual(res3[0].sound_name, "Windows XP Error")

        # Search nonexistent
        res4 = await self.repo.search_sounds("nonexistent123")
        self.assertEqual(len(res4), 0)

    async def test_categories(self):
        """Test retrieving unique categories."""
        sound1 = Sound("s1", "A", "Gaming", "p", 1.0, 10, "mp3")
        sound2 = Sound("s2", "B", "Reactions", "p", 1.0, 10, "mp3")
        sound3 = Sound("s3", "C", "Gaming", "p", 1.0, 10, "mp3")
        await self.repo.add_sound(sound1)
        await self.repo.add_sound(sound2)
        await self.repo.add_sound(sound3)

        cats = await self.repo.get_categories()
        self.assertEqual(sorted(cats), ["Gaming", "Reactions"])

    async def test_server_upsert_and_fetch(self):
        """Test server registration and retrieval."""
        await self.repo.upsert_server("123456789", "My Discord Server", 24)
        srv = await self.repo.get_server("123456789")
        self.assertIsNotNone(srv)
        self.assertEqual(srv.server_name, "My Discord Server")
        self.assertEqual(srv.sound_limit, 24)

    async def test_upload_history_logging(self):
        """Test upload history logging and retrieval."""
        await self.repo.log_upload(
            server_id="111",
            user_id="222",
            sound_id="vine_boom",
            sound_name="Vine Boom",
            status="SUCCESS"
        )
        await self.repo.log_upload(
            server_id="111",
            user_id="222",
            sound_id="airhorn",
            sound_name="Airhorn",
            status="FAILED",
            error_message="Capacity reached"
        )

        history = await self.repo.get_server_history("111", limit=10)
        self.assertEqual(len(history), 2)
        # Most recent first
        self.assertEqual(history[0].sound_name, "Airhorn")
        self.assertEqual(history[0].upload_status, "FAILED")
        self.assertEqual(history[0].error_message, "Capacity reached")
        self.assertEqual(history[1].sound_name, "Vine Boom")
        self.assertEqual(history[1].upload_status, "SUCCESS")

if __name__ == "__main__":
    unittest.main()
