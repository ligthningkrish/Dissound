"""
Configuration management for Dissound (MemeSound Bot).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Discord credentials
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID", None)
if DEV_GUILD_ID and DEV_GUILD_ID.strip():
    try:
        DEV_GUILD_ID = int(DEV_GUILD_ID.strip())
    except ValueError:
        DEV_GUILD_ID = None
else:
    DEV_GUILD_ID = None

BOT_PREFIX = os.getenv("BOT_PREFIX", "!")

# Storage Paths
DATA_DIR = BASE_DIR / "data"
SOUNDS_DIR = BASE_DIR / "assets" / "sounds"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "data/dissound.db")

# Discord Soundboard Limits & Constraints (From Discord API specifications)
MAX_SOUND_DURATION_SEC = float(os.getenv("MAX_SOUND_DURATION_SEC", "5.2"))
MAX_SOUND_FILE_SIZE_BYTES = int(os.getenv("MAX_SOUND_FILE_SIZE_KB", "512")) * 1024  # 512 KB
DEFAULT_VOLUME = float(os.getenv("DEFAULT_VOLUME", "1.0"))

MIN_SOUND_NAME_LEN = 2
MAX_SOUND_NAME_LEN = 32

SUPPORTED_AUDIO_FORMATS = ("mp3", "ogg", "wav")

# Guild Soundboard Slots by Premium Tier
# Tier 0 (Default): 8 slots
# Tier 1: 24 slots
# Tier 2: 36 slots
# Tier 3: 48 slots
TIER_SOUNDBOARD_SLOTS = {
    0: 8,
    1: 24,
    2: 36,
    3: 48
}

# Color palette for embeds
EMBED_COLOR_DEFAULT = 0x5865F2  # Blurple
EMBED_COLOR_SUCCESS = 0x57F287  # Green
EMBED_COLOR_WARNING = 0xFEE75C  # Yellow
EMBED_COLOR_ERROR = 0xED4245    # Red
