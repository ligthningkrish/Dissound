"""
AI Meme Sound Scout Agent for Dissound.
Searches the internet for authentic meme audio files, downloads and auto-processes them,
and consolidates them into the central sound library.
"""
import os
import re
import urllib.parse
from pathlib import Path
from typing import List, Optional
import aiohttp

from config import SOUNDS_DIR
from database.models import Sound
from database.repository import Repository
from audio.processor import audio_processor
from core.logger import log

# Dedicated cache folder for internet meme downloads
INTERNET_CACHE_DIR = SOUNDS_DIR / "web_cache"
INTERNET_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Common viral meme synonym and expansion mappings
MEME_QUERY_EXPANSIONS = {
    "coffin dance": ["astronomia", "coffin dance"],
    "emotional damage": ["emotional damage", "steven he failure"],
    "metal pipe": ["metal pipe falling", "metal pipe"],
    "vine boom": ["vine boom", "vine dramatic boom"],
    "airhorn": ["mlg airhorn", "airhorn"],
    "oof": ["roblox oof", "oof sound"],
    "bruh": ["bruh sound effect", "bruh"],
    "windows error": ["windows xp error", "windows error"],
    "spongebob": ["spongebob fail", "spongebob disappointed"],
    "directed by": ["directed by robert b weide", "curb your enthusiasm"],
    "sad violin": ["sad violin", "titanic flute fail"],
    "anime wow": ["anime wow", "fairy tail wow"],
    "run": ["awolnation run", "run meme"],
    "what the dog doin": ["what the dog doin", "what da dog doin"],
}

class MemeSoundScoutAgent:
    """
    AI Scout Agent that scours internet meme repositories for real audio clips,
    normalizes and trims them to Discord constraints, and saves them to Dissound's library.
    """

    def __init__(self, repo: Optional[Repository] = None):
        self.repo = repo or Repository()

    def expand_query(self, query: str) -> List[str]:
        """Expands query with viral meme variations for broader discovery."""
        q_clean = query.strip().lower()
        variants = [q_clean]
        for key, exp_list in MEME_QUERY_EXPANSIONS.items():
            if key in q_clean:
                variants.extend(exp_list)
        return list(dict.fromkeys(variants))

    async def search_internet(self, query: str, limit: int = 6) -> List[dict]:
        """
        Queries open internet sound databases (Myinstants open API) for real meme audio files.
        """
        queries_to_try = self.expand_query(query)
        results = []
        seen_urls = set()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            for q in queries_to_try[:2]:
                encoded = urllib.parse.quote(q)
                url = f"https://www.myinstants.com/api/v1/instants/?name={encoded}"
                try:
                    async with session.get(url, timeout=7) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            raw_items = data.get("results", [])
                            for item in raw_items:
                                sound_url = item.get("sound")
                                name = item.get("name", "").strip()
                                slug = item.get("slug") or item.get("id") or name
                                if sound_url and sound_url not in seen_urls:
                                    seen_urls.add(sound_url)
                                    results.append({
                                        "title": name,
                                        "sound_url": sound_url,
                                        "slug": slug,
                                        "source": "Internet Meme Repository"
                                    })
                                if len(results) >= limit:
                                    break
                except Exception as e:
                    log.warning(f"Internet sound search error for query '{q}': {e}")

                if len(results) >= limit:
                    break

        return results[:limit]

    async def fetch_and_process_candidate(self, candidate_info: dict, category: str = "Internet Meme") -> Optional[Sound]:
        """
        Downloads a candidate audio from the internet, auto-trims to <=5.2s,
        normalizes loudness, and adds to Dissound's SQLite database.
        """
        sound_url = candidate_info["sound_url"]
        title = candidate_info["title"]
        safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", candidate_info["slug"].lower())[:32]

        # Check if already processed and stored in database
        existing = await self.repo.get_sound(f"net_{safe_id}")
        if existing and Path(existing.file_path).exists():
            return existing

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(sound_url, timeout=12) as resp:
                    if resp.status != 200:
                        return None
                    raw_bytes = await resp.read()

            # Process and auto-trim using FFmpeg to enforce Discord rules (<= 5.2s, <= 512KB)
            proc = audio_processor.process_and_optimize(raw_bytes, target_format="mp3")
            if not proc.success or not proc.processed_bytes:
                log.warning(f"Failed to optimize sound '{title}': {proc.error}")
                return None

            # Save to web_cache
            out_path = INTERNET_CACHE_DIR / f"{safe_id}.mp3"
            out_path.write_bytes(proc.processed_bytes)

            # Store in unified database library
            sound_record = Sound(
                sound_id=f"net_{safe_id}",
                sound_name=title[:32],
                category=category,
                file_path=str(out_path),
                duration=proc.duration,
                file_size=proc.file_size,
                file_format="mp3",
                source_url=sound_url,
                tags=f"internet, meme, {title.lower()}"
            )
            await self.repo.add_sound(sound_record)
            log.info(f"AI Scout retrieved & indexed: {sound_record.sound_name} ({sound_record.duration}s)")
            return sound_record
        except Exception as e:
            log.error(f"Error fetching candidate '{title}': {e}")
            return None

    async def scout_and_index_meme_sounds(self, query: str, max_candidates: int = 5) -> List[Sound]:
        """
        Full agent pipeline:
        1. Searches internet for audio clips.
        2. Downloads candidate audio files.
        3. Validates and auto-trims each to <= 5.2s Discord standard.
        4. Saves them to the central library.
        5. Returns list of ready-to-preview Sound models.
        """
        candidates = await self.search_internet(query, limit=max_candidates)
        processed_sounds: List[Sound] = []

        for cand in candidates:
            sound = await self.fetch_and_process_candidate(cand)
            if sound:
                processed_sounds.append(sound)

        return processed_sounds

# Global instance
meme_scout = MemeSoundScoutAgent()
