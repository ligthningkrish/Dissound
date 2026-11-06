import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio.processor import audio_processor
from database.db import init_db
from database.repository import Repository

async def clean_and_retrim():
    await init_db()
    repo = Repository()

    sounds = await repo.get_all_sounds(limit=500)
    print(f"Scanning {len(sounds)} sounds in catalog for stale/over-length audio...")

    retrimmed_count = 0
    for s in sounds:
        p = Path(s.file_path)
        if not p.exists():
            continue

        raw_bytes = p.read_bytes()
        actual_dur = audio_processor.get_duration(raw_bytes)

        if actual_dur > 5.0 or s.duration > 5.0:
            print(f"Re-trimming '{s.sound_name}' (was {actual_dur}s / {s.duration}s)...")
            res = audio_processor.process_and_optimize(raw_bytes, target_format="mp3", max_duration=4.85)
            if res.success and res.processed_bytes:
                p.write_bytes(res.processed_bytes)
                s.duration = res.duration
                s.file_size = res.file_size
                await repo.add_sound(s)
                retrimmed_count += 1
                print(f"  -> Successfully optimized to {res.duration}s (viral climax: {res.viral_climax_sec}s, size: {res.file_size}B)")

    # Also scan web_cache for any orphaned files
    cache_dir = Path("assets/sounds/web_cache")
    if cache_dir.exists():
        for f in cache_dir.glob("*.mp3"):
            d = audio_processor.get_duration(f)
            if d > 5.0:
                print(f"Re-trimming orphaned cache file {f.name} (was {d}s)...")
                data = f.read_bytes()
                res = audio_processor.process_and_optimize(data, target_format="mp3", max_duration=4.85)
                if res.success and res.processed_bytes:
                    f.write_bytes(res.processed_bytes)
                    print(f"  -> Safe duration: {res.duration}s")

    print(f"\nDone! Re-trimmed and optimized {retrimmed_count} sounds.")

if __name__ == "__main__":
    asyncio.run(clean_and_retrim())
