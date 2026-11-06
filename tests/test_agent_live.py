import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio.agent import meme_scout
from database.db import init_db

async def test_scout():
    await init_db()

    print("--- Testing Scout with 'vine boom' ---")
    sounds = await meme_scout.scout_and_index_meme_sounds("vine boom", max_candidates=4)
    print(f"Retrieved {len(sounds)} sounds for 'vine boom'")
    for idx, s in enumerate(sounds, 1):
        print(f"  {idx}. [{s.sound_name}] dur={s.duration}s, size={s.file_size}B, tags={s.tags}")
        assert s.duration <= 5.2, f"Duration {s.duration} > 5.2s"
        assert s.file_size <= 524288, f"File size {s.file_size} > 512KB"
        assert Path(s.file_path).exists(), f"File {s.file_path} does not exist"

    print("\n--- Testing Scout with 'emotional damage' ---")
    sounds2 = await meme_scout.scout_and_index_meme_sounds("emotional damage", max_candidates=4)
    print(f"Retrieved {len(sounds2)} sounds for 'emotional damage'")
    for idx, s in enumerate(sounds2, 1):
        print(f"  {idx}. [{s.sound_name}] dur={s.duration}s, size={s.file_size}B, tags={s.tags}")
        assert s.duration <= 5.2, f"Duration {s.duration} > 5.2s"
        assert s.file_size <= 524288, f"File size {s.file_size} > 512KB"
        assert Path(s.file_path).exists(), f"File {s.file_path} does not exist"

    print("\nAll live scout tests PASSED successfully!")

if __name__ == "__main__":
    asyncio.run(test_scout())
