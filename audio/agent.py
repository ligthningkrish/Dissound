"""
AI Meme Sound Scout Agent for Dissound.
Searches multiple internet meme audio repositories (Myinstants, SoundboardMax, Soundboard Guy, Orange Free Sounds, Freesound),
downloads and auto-processes candidate audio files to Discord soundboard constraints (<= 5.2s, <= 512 KB),
and consolidates them into the central sound library with an interactive preview carousel.
"""
import hashlib
import os
import re
import urllib.parse
from pathlib import Path
from typing import List, Optional, Dict
import aiohttp

from config import SOUNDS_DIR
from database.models import Sound
from database.repository import Repository
from audio.processor import audio_processor
from core.logger import log

# Dedicated cache folder for internet meme downloads
INTERNET_CACHE_DIR = SOUNDS_DIR / "web_cache"
INTERNET_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# HTTP Request headers mimicking modern desktop browsers
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,audio/*,*/*;q=0.8"
}

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
    AI Scout Agent that scours multiple internet sound databases for real meme audio files,
    normalizes and auto-trims them to Discord constraints, and saves them to Dissound's library.
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

    # ---------------------------------------------------------
    # SOURCE 1: Myinstants API (https://www.myinstants.com)
    # ---------------------------------------------------------
    async def _search_myinstants(self, query: str, session: aiohttp.ClientSession) -> List[Dict]:
        """Searches Myinstants via REST API."""
        results = []
        encoded = urllib.parse.quote(query)
        url = f"https://www.myinstants.com/api/v1/instants/?name={encoded}&format=json"
        try:
            req_headers = {**BROWSER_HEADERS, "Accept": "application/json"}
            async with session.get(url, headers=req_headers, timeout=6) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    for item in data.get("results", [])[:8]:
                        sound_url = item.get("sound")
                        name = item.get("name", "").strip()
                        slug = str(item.get("slug") or item.get("id") or name)
                        if sound_url:
                            results.append({
                                "title": name,
                                "sound_url": sound_url,
                                "slug": f"myinstants_{slug}",
                                "source": "Myinstants"
                            })
        except Exception as e:
            log.debug(f"Myinstants query error for '{query}': {e}")
        return results

    # ---------------------------------------------------------
    # SOURCE 2: SoundboardMax (https://soundboardmax.com)
    # ---------------------------------------------------------
    async def _search_soundboardmax(self, query: str, session: aiohttp.ClientSession) -> List[Dict]:
        """Searches SoundboardMax's instant meme button database."""
        results = []
        encoded = urllib.parse.quote_plus(query)
        url = f"https://soundboardmax.com/?s={encoded}"
        try:
            async with session.get(url, timeout=6) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    pattern = r"play\(this,\s*(?:&#39;|['\"])(https://cdn\.soundboardmax\.com/[^'\"&]+\.mp3)(?:&#39;|['\"])\)[^>]*title=(?:&#39;|['\"])Play\s+(.*?)\s+sound(?:&#39;|['\"])"
                    matches = re.findall(pattern, html, re.I)
                    for sound_url, title in matches[:8]:
                        clean_title = title.replace("&#39;", "'").replace("&amp;", "&").strip()
                        slug_base = re.sub(r'[^a-zA-Z0-9]', '_', clean_title).strip('_').lower()
                        results.append({
                            "title": clean_title,
                            "sound_url": sound_url,
                            "slug": f"sbmax_{slug_base}",
                            "source": "SoundboardMax"
                        })
        except Exception as e:
            log.debug(f"SoundboardMax query error for '{query}': {e}")
        return results

    # ---------------------------------------------------------
    # SOURCE 3: Soundboard Guy (https://soundboardguy.com)
    # ---------------------------------------------------------
    async def _search_soundboardguy(self, query: str, session: aiohttp.ClientSession) -> List[Dict]:
        """Searches Soundboard Guy's library of instant sound buttons."""
        results = []
        encoded = urllib.parse.quote_plus(query)
        url = f"https://soundboardguy.com/?s={encoded}"
        try:
            async with session.get(url, timeout=6) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    pattern = r'class=["\']single_btn_trigger["\'][^>]*data-source=["\'](https?://soundboardguy\.com/wp-content/uploads/[^"\']+\.mp3)["\'][^>]*data-name=["\']([^"\']+)["\']'
                    matches = re.findall(pattern, html, re.I)
                    for sound_url, raw_name in matches[:8]:
                        clean_name = raw_name.replace("-sound-effect-button", "").replace("-button", "").replace("-", " ").title()
                        slug_base = re.sub(r'[^a-zA-Z0-9]', '_', raw_name).strip('_').lower()
                        results.append({
                            "title": clean_name,
                            "sound_url": sound_url,
                            "slug": f"sbguy_{slug_base}",
                            "source": "Soundboard Guy"
                        })
        except Exception as e:
            log.debug(f"SoundboardGuy query error for '{query}': {e}")
        return results

    # ---------------------------------------------------------
    # SOURCE 4: Orange Free Sounds (https://orangefreesounds.com)
    # ---------------------------------------------------------
    async def _search_orangefreesounds(self, query: str, session: aiohttp.ClientSession) -> List[Dict]:
        """Searches Orange Free Sounds for meme sound effects."""
        results = []
        encoded = urllib.parse.quote_plus(query)
        url = f"https://orangefreesounds.com/?s={encoded}"
        try:
            async with session.get(url, timeout=6) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    articles = re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL)
                    for a in articles[:8]:
                        title_m = re.search(r'title=["\']([^"\']+)["\']', a)
                        mp3_m = re.search(r'(https?://orangefreesounds\.com/wp-content/uploads/[^\s"\'<>]+\.mp3)', a)
                        if title_m and mp3_m:
                            t = title_m.group(1).replace("&#39;", "'").replace("&amp;", "&").strip()
                            u = mp3_m.group(1)
                            slug_base = re.sub(r'[^a-zA-Z0-9]', '_', t).strip('_').lower()
                            results.append({
                                "title": t,
                                "sound_url": u,
                                "slug": f"orange_{slug_base}",
                                "source": "Orange Free Sounds"
                            })
        except Exception as e:
            log.debug(f"OrangeFreeSounds query error for '{query}': {e}")
        return results

    # ---------------------------------------------------------
    # SOURCE 5: Freesound (https://freesound.org)
    # ---------------------------------------------------------
    async def _search_freesound(self, query: str, session: aiohttp.ClientSession) -> List[Dict]:
        """Searches Freesound's open community audio library."""
        results = []
        encoded = urllib.parse.quote_plus(query)
        url = f"https://freesound.org/search/?q={encoded}"
        try:
            async with session.get(url, timeout=6) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    previews = re.findall(r'(https://cdn\.freesound\.org/previews/\d+/(\d+)_[^"\']+-lq\.mp3)', html)
                    titles_map = dict(re.findall(r'href=["\']/people/[^/]+/sounds/(\d+)/["\']\s+title=["\']([^"\']+)["\']', html))
                    for mp3_url, sid in previews[:8]:
                        name = titles_map.get(sid, f"Meme Sound #{sid}")
                        results.append({
                            "title": name,
                            "sound_url": mp3_url,
                            "slug": f"freesound_{sid}",
                            "source": "Freesound"
                        })
        except Exception as e:
            log.debug(f"Freesound query error for '{query}': {e}")
        return results

    async def search_internet(self, query: str, limit: int = 8) -> List[Dict]:
        """
        Queries multiple internet meme sound repositories concurrently (Myinstants,
        SoundboardMax, Soundboard Guy, Orange Free Sounds, Freesound).
        Interleaves and deduplicates results fairly across providers.
        """
        queries_to_try = self.expand_query(query)
        seen_urls = set()
        seen_titles = set()
        collected_by_source: Dict[str, List[Dict]] = {
            "Myinstants": [],
            "SoundboardMax": [],
            "Soundboard Guy": [],
            "Orange Free Sounds": [],
            "Freesound": []
        }

        async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
            for q in queries_to_try[:2]:
                tasks = [
                    self._search_myinstants(q, session),
                    self._search_soundboardmax(q, session),
                    self._search_soundboardguy(q, session),
                    self._search_orangefreesounds(q, session),
                    self._search_freesound(q, session),
                ]
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                for r in responses:
                    if isinstance(r, list):
                        for item in r:
                            src = item.get("source", "Web")
                            url = item.get("sound_url", "")
                            t_norm = re.sub(r'[^a-z0-9]', '', item.get("title", "").lower())
                            if url and url not in seen_urls and t_norm not in seen_titles:
                                seen_urls.add(url)
                                seen_titles.add(t_norm)
                                if src in collected_by_source:
                                    collected_by_source[src].append(item)

                total_collected = sum(len(v) for v in collected_by_source.values())
                if total_collected >= limit * 2:
                    break

        # Round-robin fair interleaving across sources
        final_results: List[Dict] = []
        max_source_len = max((len(v) for v in collected_by_source.values()), default=0)
        source_order = ["Myinstants", "SoundboardMax", "Soundboard Guy", "Orange Free Sounds", "Freesound"]

        for idx in range(max_source_len):
            for src in source_order:
                src_list = collected_by_source[src]
                if idx < len(src_list):
                    final_results.append(src_list[idx])
                    if len(final_results) >= limit:
                        return final_results

        return final_results[:limit]

    async def fetch_and_process_candidate(self, candidate_info: dict, category: str = "Internet Meme") -> Optional[Sound]:
        """
        Downloads a candidate audio clip from the web, transcodes to standard MP3,
        preserves the full audio duration (up to 60s) for user previewing,
        and adds to Dissound's SQLite database.
        """
        sound_url = candidate_info["sound_url"]
        title = candidate_info["title"].strip()
        source = candidate_info.get("source", "Web Repository")

        # Stable unique identifier based on URL hash and slug
        url_hash = hashlib.md5(sound_url.encode("utf-8")).hexdigest()[:10]
        slug_clean = re.sub(r"[^a-zA-Z0-9_]", "_", candidate_info.get("slug", "sound").lower())[:20]
        safe_id = f"net_{slug_clean}_{url_hash}"

        # Check if already processed and stored in database
        existing = await self.repo.get_sound(safe_id)
        if existing and Path(existing.file_path).exists():
            return existing

        try:
            async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
                async with session.get(sound_url, timeout=12) as resp:
                    if resp.status != 200:
                        return None
                    raw_bytes = await resp.read()

            # Transcode & normalize full audio to playable MP3 (keeping up to 60s for full preview)
            proc = audio_processor.transcode_and_normalize_full(raw_bytes, max_duration=60.0, target_format="mp3")
            if not proc.success or not proc.processed_bytes:
                log.warning(f"Failed to transcode candidate '{title}' from {source}: {proc.error}")
                return None

            # Save to web_cache
            out_path = INTERNET_CACHE_DIR / f"{safe_id}.mp3"
            out_path.write_bytes(proc.processed_bytes)

            # Store in unified database library
            clean_name = title[:32].strip() or f"{source} Meme"
            sound_record = Sound(
                sound_id=safe_id,
                sound_name=clean_name,
                category=category,
                file_path=str(out_path),
                duration=proc.duration,
                file_size=proc.file_size,
                file_format="mp3",
                source_url=sound_url,
                tags=f"internet, meme, {source.lower()}, {title.lower()}"
            )
            await self.repo.add_sound(sound_record)
            log.info(f"AI Scout retrieved [{source}]: {sound_record.sound_name} ({sound_record.duration}s)")
            return sound_record
        except Exception as e:
            log.error(f"Error fetching candidate '{title}' from {source}: {e}")
            return None

    async def scout_and_index_meme_sounds(self, query: str, max_candidates: int = 5) -> List[Sound]:
        """
        Full agent pipeline:
        1. Searches multi-source internet repositories concurrently.
        2. Downloads candidate audio files.
        3. Validates and auto-trims each to <= 5.2s Discord soundboard standard.
        4. Saves them to the central library.
        5. Returns list of ready-to-preview Sound models.
        """
        candidates = await self.search_internet(query, limit=max_candidates * 2)
        processed_sounds: List[Sound] = []

        for cand in candidates:
            sound = await self.fetch_and_process_candidate(cand)
            if sound:
                processed_sounds.append(sound)
            if len(processed_sounds) >= max_candidates:
                break

        return processed_sounds


import asyncio

# Global instance
meme_scout = MemeSoundScoutAgent()
