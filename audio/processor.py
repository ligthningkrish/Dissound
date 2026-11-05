"""
Audio processing module for Dissound (MemeSound Bot).
Handles audio validation, trimming, format conversion, normalization, and size optimization.
"""
import os
import sys
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import imageio_ffmpeg

from config import (
    MAX_SOUND_DURATION_SEC,
    MAX_SOUND_FILE_SIZE_BYTES,
    MIN_SOUND_NAME_LEN,
    MAX_SOUND_NAME_LEN
)
from core.logger import log

# Ensure ffmpeg.exe exists in the binaries and Scripts folder for tools
def _ensure_ffmpeg() -> str:
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    dir_name = os.path.dirname(exe)
    shim = os.path.join(dir_name, "ffmpeg.exe")
    if not os.path.exists(shim):
        try:
            shutil.copyfile(exe, shim)
        except Exception:
            pass
    scripts_shim = os.path.join(sys.prefix, "Scripts", "ffmpeg.exe")
    if not os.path.exists(scripts_shim):
        try:
            shutil.copyfile(exe, scripts_shim)
        except Exception:
            pass
    # Update PATH
    if dir_name not in os.environ.get("PATH", ""):
        os.environ["PATH"] = dir_name + os.pathsep + os.environ.get("PATH", "")
    return exe

FFMPEG_EXE = _ensure_ffmpeg()

@dataclass
class AudioValidationResult:
    is_valid: bool
    duration: float
    file_size: int
    format: str
    error: Optional[str] = None

@dataclass
class AudioProcessResult:
    success: bool
    processed_bytes: Optional[bytes] = None
    duration: float = 0.0
    file_size: int = 0
    file_format: str = "mp3"
    error: Optional[str] = None

class AudioProcessor:
    """Handles audio inspection, format conversion, trimming, and loudness normalization."""

    def __init__(self, ffmpeg_path: str = FFMPEG_EXE):
        self.ffmpeg = ffmpeg_path

    def get_duration(self, file_path_or_bytes: Path | bytes) -> float:
        """
        Extract duration of an audio file in seconds using ffmpeg or fallback.
        """
        cmd = [self.ffmpeg]
        if isinstance(file_path_or_bytes, bytes):
            cmd.extend(["-i", "pipe:0"])
            proc = subprocess.run(cmd, input=file_path_or_bytes, capture_output=True)
            stderr = proc.stderr.decode("utf-8", errors="ignore")
        else:
            cmd.extend(["-i", str(file_path_or_bytes)])
            proc = subprocess.run(cmd, capture_output=True)
            stderr = proc.stderr.decode("utf-8", errors="ignore")

        # Parse duration from ffmpeg output: "Duration: 00:00:04.50,"
        for line in stderr.splitlines():
            line = line.strip()
            if "Duration:" in line and "N/A" not in line:
                try:
                    dur_str = line.split("Duration:")[1].split(",")[0].strip()
                    parts = dur_str.split(":")
                    hours = float(parts[0])
                    minutes = float(parts[1])
                    seconds = float(parts[2])
                    return round(hours * 3600 + minutes * 60 + seconds, 2)
                except Exception as e:
                    log.warning(f"Failed to parse duration string '{line}': {e}")

        # Fallback for piped mp3/raw bytes where header duration is N/A:
        # Estimate via standard 128kbps bitrate or fallback duration calculation
        if isinstance(file_path_or_bytes, bytes) and len(file_path_or_bytes) > 0:
            # size in bytes * 8 bits / (128000 bps)
            est = round(len(file_path_or_bytes) * 8 / 128000.0, 2)
            return est

        return 0.0

    def validate_sound_name(self, name: str) -> Tuple[bool, Optional[str]]:
        """Validate soundboard sound name length and characters."""
        cleaned = name.strip()
        if len(cleaned) < MIN_SOUND_NAME_LEN:
            return False, f"Sound name must be at least {MIN_SOUND_NAME_LEN} characters long."
        if len(cleaned) > MAX_SOUND_NAME_LEN:
            return False, f"Sound name cannot exceed {MAX_SOUND_NAME_LEN} characters."
        return True, None

    def validate_audio(self, file_path: Path) -> AudioValidationResult:
        """
        Check if an audio file conforms to Discord upload rules:
        - Must exist
        - Format: MP3 or OGG
        - Duration <= 5.2 seconds
        - File size <= 512 KB
        """
        if not file_path.exists():
            return AudioValidationResult(False, 0.0, 0, "", "Audio file does not exist.")

        file_size = file_path.stat().st_size
        ext = file_path.suffix.lower().lstrip(".")
        duration = self.get_duration(file_path)

        if ext not in ("mp3", "ogg", "wav"):
            return AudioValidationResult(
                False, duration, file_size, ext,
                f"Unsupported format '.{ext}'. Discord Soundboard requires MP3 or OGG."
            )

        if duration > MAX_SOUND_DURATION_SEC:
            return AudioValidationResult(
                False, duration, file_size, ext,
                f"Duration ({duration}s) exceeds Discord maximum limit of {MAX_SOUND_DURATION_SEC}s."
            )

        if file_size > MAX_SOUND_FILE_SIZE_BYTES:
            kb = round(file_size / 1024, 1)
            return AudioValidationResult(
                False, duration, file_size, ext,
                f"File size ({kb} KB) exceeds Discord limit of 512 KB."
            )

        return AudioValidationResult(True, duration, file_size, ext, None)

    def process_and_optimize(
        self,
        input_data: Path | bytes,
        target_format: str = "mp3",
        max_duration: float = MAX_SOUND_DURATION_SEC,
        normalize: bool = True
    ) -> AudioProcessResult:
        """
        Convert, trim, normalize, and optimize audio for Discord Soundboard.
        Guarantees:
        1. Output format is MP3 or OGG.
        2. Output duration <= max_duration (default 5.2s).
        3. Output size <= 512 KB.
        """
        target_format = target_format.lower()
        if target_format not in ("mp3", "ogg"):
            target_format = "mp3"

        codec = "libmp3lame" if target_format == "mp3" else "libvorbis"
        fmt = "mp3" if target_format == "mp3" else "ogg"

        # Multi-pass bitrate strategy to guarantee <= 512 KB
        bitrates = ["128k", "96k", "64k"]

        last_error = None
        for br in bitrates:
            filters = []
            if normalize:
                filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

            cmd = [
                self.ffmpeg,
                "-y",
                "-i", "pipe:0" if isinstance(input_data, bytes) else str(input_data),
                "-t", str(max_duration),
            ]

            if filters:
                cmd.extend(["-af", ",".join(filters)])

            cmd.extend([
                "-ac", "2",
                "-ar", "44100",
                "-codec:a", codec,
                "-b:a", br,
                "-f", fmt,
                "pipe:1"
            ])

            proc = subprocess.run(
                cmd,
                input=input_data if isinstance(input_data, bytes) else None,
                capture_output=True
            )

            if proc.returncode != 0:
                last_error = proc.stderr.decode("utf-8", errors="ignore")
                log.error(f"FFmpeg processing error: {last_error}")
                continue

            out_bytes = proc.stdout
            out_size = len(out_bytes)

            if out_size <= MAX_SOUND_FILE_SIZE_BYTES:
                duration = self.get_duration(out_bytes)
                return AudioProcessResult(
                    success=True,
                    processed_bytes=out_bytes,
                    duration=duration,
                    file_size=out_size,
                    file_format=target_format
                )

        return AudioProcessResult(
            success=False,
            error=last_error or "Processed audio exceeds 512 KB limit even after compression."
        )

# Global singleton
audio_processor = AudioProcessor()
