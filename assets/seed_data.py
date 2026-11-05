"""
Database seeder for default meme sounds.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import init_db
from database.models import Sound
from database.repository import Repository
from assets.sound_generator import generate_all_bundled_sounds
from core.logger import log

async def seed_database():
    """Ensure database schema is ready and populate default sounds."""
    await init_db()
    repo = Repository()

    # Generate sounds if not present on disk
    sound_items = generate_all_bundled_sounds()

    for item in sound_items:
        existing = await repo.get_sound(item["sound_id"])
        if not existing:
            sound = Sound(
                sound_id=item["sound_id"],
                sound_name=item["sound_name"],
                category=item["category"],
                file_path=item["file_path"],
                duration=item["duration"],
                file_size=item["file_size"],
                file_format=item["file_format"],
                source_url=item["source_url"],
                tags=item["tags"]
            )
            await repo.add_sound(sound)
            log.info(f"Seeded sound: {sound.sound_name} ({sound.category})")
        else:
            log.info(f"Sound already exists: {existing.sound_name}")

    log.info("Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_database())
