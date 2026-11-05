"""
Safe audio downloader module for Dissound.
Handles fetching audio files from Discord attachments and URLs.
"""
from typing import Optional, Tuple
import aiohttp
from config import MAX_SOUND_FILE_SIZE_BYTES
from core.logger import log

class AudioDownloader:
    """Asynchronously download audio files from Discord or web URLs."""

    @staticmethod
    async def download_file(url: str, max_size_bytes: int = MAX_SOUND_FILE_SIZE_BYTES * 4) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Download audio content from a URL safely with content size cap.
        Returns: (bytes, error_message)
        """
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return None, f"Failed to download audio: HTTP {resp.status}"

                    # Verify Content-Length header if present
                    cl = resp.headers.get("Content-Length")
                    if cl and int(cl) > max_size_bytes:
                        return None, f"File is too large ({int(cl) // 1024} KB). Max allowable download is {max_size_bytes // 1024} KB."

                    content = await resp.read()
                    if len(content) > max_size_bytes:
                        return None, f"Downloaded content exceeds {max_size_bytes // 1024} KB limit."

                    return content, None
        except Exception as e:
            log.error(f"Download exception: {e}")
            return None, f"Download failed: {str(e)}"
