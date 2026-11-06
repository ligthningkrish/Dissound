"""
Database seeder for Dissound.
Pre-populates the sound catalog with authentic viral meme MP3s from the internet.
"""
import asyncio
import sys
import urllib.request
import urllib.parse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import init_db
from database.models import Sound
from database.repository import Repository
from audio.processor import audio_processor
from config import SOUNDS_DIR
from core.logger import log

# Canonical viral internet meme audio sources
STARTER_INTERNET_MEMES = [
    {
        "id": "vine_boom",
        "name": "Vine Boom",
        "category": "Meme Sounds",
        "url": "https://www.myinstants.com/media/sounds/vine-boom.mp3",
        "tags": "vine, boom, bass, thud, dramatic"
    },
    {
        "id": "metal_pipe",
        "name": "Metal Pipe Falling",
        "category": "Random & Funny",
        "url": "https://www.myinstants.com/media/sounds/metal-pipe-falling-sound-effect.mp3",
        "tags": "metal, pipe, falling, clang, loud, funny"
    },
    {
        "id": "emotional_damage",
        "name": "Emotional Damage",
        "category": "Meme Sounds",
        "url": "https://www.myinstants.com/media/sounds/emotional-damage.mp3",
        "tags": "emotional damage, steven he, failure, meme"
    },
    {
        "id": "windows_error",
        "name": "Windows XP Error",
        "category": "Classic Internet",
        "url": "https://www.myinstants.com/media/sounds/windows-xp-error.mp3",
        "tags": "windows, xp, error, classic, microsoft"
    },
    {
        "id": "airhorn",
        "name": "MLG Airhorn",
        "category": "Random & Funny",
        "url": "https://www.myinstants.com/media/sounds/mlg-air-horn.mp3",
        "tags": "airhorn, mlg, horn, hype, celebration"
    },
    {
        "id": "roblox_oof",
        "name": "Roblox Oof",
        "category": "Gaming",
        "url": "https://www.myinstants.com/media/sounds/roblox-death-sound_1.mp3",
        "tags": "roblox, oof, death, gaming, funny"
    },
    {
        "id": "bruh",
        "name": "Bruh Sound Effect #2",
        "category": "Meme Sounds",
        "url": "https://www.myinstants.com/media/sounds/bruh-sound-effect-2.mp3",
        "tags": "bruh, meme, reaction, disappointment"
    },
    {
        "id": "bonk",
        "name": "Bonk Mallet",
        "category": "Reactions",
        "url": "https://www.myinstants.com/media/sounds/bonk-sound-effect.mp3",
        "tags": "bonk, hammer, doge, cartoon"
    },
    {
        "id": "anime_wow",
        "name": "Anime Wow",
        "category": "Reactions",
        "url": "https://www.myinstants.com/media/sounds/anime-wow-sound-effect.mp3",
        "tags": "anime, wow, cute, reaction"
    },
    {
        "id": "directed_by_weide",
        "name": "Directed by Robert B. Weide",
        "category": "Movie & TV",
        "url": "https://www.myinstants.com/media/sounds/directed-by-robert-b_voI2Z4T.mp3",
        "tags": "directed by, curb your enthusiasm, fail, credits"
    }
]

async def seed_database():
    """Ensure schema is initialized and populate real internet meme audio files."""
    await init_db()
    repo = Repository()
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for item in STARTER_INTERNET_MEMES:
        out_file = SOUNDS_DIR / f"{item['id']}.mp3"

        # Download & process if not already on disk
        if not out_file.exists():
            log.info(f"Downloading real meme sound: {item['name']}...")
            try:
                req = urllib.request.Request(item["url"], headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw_audio = resp.read()

                # Process, auto-trim <= 5.2s, normalize
                proc = audio_processor.process_and_optimize(raw_audio, target_format="mp3")
                if proc.success and proc.processed_bytes:
                    out_file.write_bytes(proc.processed_bytes)
                else:
                    out_file.write_bytes(raw_audio)
            except Exception as e:
                log.warning(f"Failed to download internet audio for '{item['name']}': {e}")
                continue

        # Get verified duration and size
        dur = audio_processor.get_duration(out_file)
        size = out_file.stat().st_size

        sound = Sound(
            sound_id=item["id"],
            sound_name=item["name"],
            category=item["category"],
            file_path=str(out_file),
            duration=dur,
            file_size=size,
            file_format="mp3",
            source_url=item["url"],
            tags=item["tags"]
        )
        await repo.add_sound(sound)
        log.info(f"Catalog Sound Ready: {sound.sound_name} ({sound.duration}s, {size // 1024} KB)")

    log.info("Meme sound seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_database())
