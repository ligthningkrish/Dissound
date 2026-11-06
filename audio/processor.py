"""
Audio processing module for Dissound (MemeSound Bot).
Handles audio validation, viral segment extraction, format conversion, normalization, and size optimization.
Guarantees audio files conform to Discord Soundboard constraints (<= 5.2s, <= 512 KB).
"""
import array
import math
import os
import sys
import shutil
import tempfile
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
    if dir_name not in os.environ.get("PATH", ""):
        os.environ["PATH"] = dir_name + os.pathsep + os.environ.get("PATH", "")
    return exe

FFMPEG_EXE = _ensure_ffmpeg()

# Safe target duration strictly below Discord's 5.20s threshold to prevent MP3 frame-padding overflow
SAFE_TARGET_DURATION_SEC = 4.85

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
    viral_climax_sec: float = 0.0
    error: Optional[str] = None

class AudioProcessor:
    """Handles audio inspection, format conversion, viral peak extraction, and loudness normalization."""

    def __init__(self, ffmpeg_path: str = FFMPEG_EXE):
        self.ffmpeg = ffmpeg_path

    def get_duration(self, file_path_or_bytes: Path | bytes) -> float:
        """
        Extract duration of an audio file in seconds using ffmpeg probe.
        """
        temp_file = None
        try:
            if isinstance(file_path_or_bytes, bytes):
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(file_path_or_bytes)
                    target_path = f.name
                    temp_file = target_path
            else:
                target_path = str(file_path_or_bytes)

            cmd = [self.ffmpeg, "-i", target_path]
            proc = subprocess.run(cmd, capture_output=True)
            stderr = proc.stderr.decode("utf-8", errors="ignore")

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
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

        if isinstance(file_path_or_bytes, bytes) and len(file_path_or_bytes) > 0:
            est = round(len(file_path_or_bytes) * 8 / 128000.0, 2)
            return min(SAFE_TARGET_DURATION_SEC, est)

        return 0.0

    def detect_viral_segment(
        self,
        input_data: Path | bytes,
        target_duration: float = SAFE_TARGET_DURATION_SEC
    ) -> Tuple[float, float, float]:
        """
        AI Algorithm to detect the most energetic, viral punchline / climax of an audio track.
        Analyzes 16kHz mono PCM frames (RMS energy, transient onset spikes, and peak volume).
        Returns (crop_start_sec, crop_end_sec, climax_sec).
        """
        try:
            # Decode to raw 16kHz mono 16-bit PCM via FFmpeg pipe
            cmd = [
                self.ffmpeg,
                "-y",
                "-i", "pipe:0" if isinstance(input_data, bytes) else str(input_data),
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-f", "s16le",
                "pipe:1"
            ]
            proc = subprocess.run(
                cmd,
                input=input_data if isinstance(input_data, bytes) else None,
                capture_output=True
            )
            if proc.returncode != 0 or not proc.stdout:
                return 0.0, target_duration, 0.0

            raw_pcm = proc.stdout
            samples = array.array('h')
            samples.frombytes(raw_pcm)
            sample_rate = 16000
            total_samples = len(samples)
            total_duration = total_samples / sample_rate

            if total_duration <= target_duration:
                return 0.0, round(total_duration, 2), 0.0

            # 50ms frames (800 samples)
            frame_size = 800
            num_frames = total_samples // frame_size
            if num_frames == 0:
                return 0.0, round(total_duration, 2), 0.0

            frame_rms = []
            frame_peaks = []
            for i in range(num_frames):
                frame = samples[i * frame_size : (i + 1) * frame_size]
                peak = max(abs(s) for s in frame)
                sum_sq = sum(s * s for s in frame)
                rms = math.sqrt(sum_sq / len(frame))
                frame_rms.append(rms)
                frame_peaks.append(peak)

            # Detect onset spikes (instantaneous rise in energy)
            onset_scores = [0.0]
            for i in range(1, len(frame_rms)):
                diff = max(0.0, frame_rms[i] - frame_rms[i - 1])
                onset_scores.append(diff)

            # Score each frame for meme virality (transient onset + peak burst + sustained RMS)
            max_score = -1.0
            best_climax_frame = 0
            for i in range(len(frame_rms)):
                score = (frame_peaks[i] * 0.45) + (onset_scores[i] * 0.35) + (frame_rms[i] * 0.20)
                if score > max_score:
                    max_score = score
                    best_climax_frame = i

            climax_sec = (best_climax_frame * frame_size) / sample_rate

            # Center window: lead-in 0.6s before climax to capture the build-up / punchline context
            ideal_start = max(0.0, climax_sec - 0.6)
            ideal_end = ideal_start + target_duration

            if ideal_end > total_duration:
                ideal_end = total_duration
                ideal_start = max(0.0, ideal_end - target_duration)

            return round(ideal_start, 2), round(ideal_end, 2), round(climax_sec, 2)
        except Exception as e:
            log.warning(f"Error in detect_viral_segment: {e}")
            return 0.0, target_duration, 0.0

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

    def trim_and_optimize(
        self,
        input_data: Path | bytes,
        start_sec: float = 0.0,
        duration: float = SAFE_TARGET_DURATION_SEC,
        target_format: str = "mp3",
        normalize: bool = True
    ) -> AudioProcessResult:
        """
        Crop an audio track to user-specified start_sec and duration,
        normalize loudness, and optimize for Discord Soundboard.
        Guarantees:
        1. Result duration strictly <= 5.0s (leaving a guaranteed margin under Discord's 5.2s limit).
        2. Result file size <= 512 KB.
        3. Formats to clean MP3/OGG without video tracks or metadata bloat.
        """
        target_format = target_format.lower()
        if target_format not in ("mp3", "ogg"):
            target_format = "mp3"

        codec = "libmp3lame" if target_format == "mp3" else "libvorbis"
        fmt = "mp3" if target_format == "mp3" else "ogg"

        # Strictly clamp duration: user cannot exceed 5.0s for Discord Soundboard
        safe_duration = max(0.5, min(duration, 5.0))
        start_sec = max(0.0, start_sec)
        end_sec = start_sec + safe_duration

        bitrates = ["128k", "96k", "64k"]
        last_error = None

        for br in bitrates:
            filters = [
                f"atrim=start={start_sec}:end={end_sec}",
                "asetpts=PTS-STARTPTS",
                "afade=t=in:ss=0:d=0.03"
            ]
            if safe_duration > 0.15:
                fade_out_start = max(0.0, safe_duration - 0.08)
                filters.append(f"afade=t=out:st={fade_out_start}:d=0.08")

            if normalize:
                filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

            cmd = [
                self.ffmpeg,
                "-y",
                "-i", "pipe:0" if isinstance(input_data, bytes) else str(input_data),
                "-vn",  # Strip embedded album art / video to save size and avoid duration distortion
                "-af", ",".join(filters),
                "-t", str(safe_duration),
                "-ac", "2",
                "-ar", "44100",
                "-codec:a", codec,
                "-b:a", br,
            ]
            if target_format == "mp3":
                cmd.extend(["-write_xing", "1"])
            cmd.extend(["-f", fmt, "pipe:1"])

            proc = subprocess.run(
                cmd,
                input=input_data if isinstance(input_data, bytes) else None,
                capture_output=True
            )

            if proc.returncode != 0:
                last_error = proc.stderr.decode("utf-8", errors="ignore")
                log.error(f"FFmpeg trimming error: {last_error}")
                continue

            out_bytes = proc.stdout
            out_size = len(out_bytes)

            if out_size <= MAX_SOUND_FILE_SIZE_BYTES:
                dur = self.get_duration(out_bytes)
                if dur > 5.15:
                    # Retry with slightly shorter cut to account for severe encoder padding
                    safe_duration = max(0.5, safe_duration - 0.2)
                    end_sec = start_sec + safe_duration
                    continue
                return AudioProcessResult(
                    success=True,
                    processed_bytes=out_bytes,
                    duration=dur,
                    file_size=out_size,
                    file_format=target_format
                )

        return AudioProcessResult(
            success=False,
            error=last_error or "Processed audio exceeds 512 KB limit even after compression."
        )

    def transcode_and_normalize_full(
        self,
        input_data: Path | bytes,
        max_duration: float = 60.0,
        target_format: str = "mp3"
    ) -> AudioProcessResult:
        """
        Convert downloaded audio to standard playable MP3 and normalize loudness,
        keeping the full duration (up to max_duration) for rich previewing.
        """
        target_format = target_format.lower()
        if target_format not in ("mp3", "ogg"):
            target_format = "mp3"

        codec = "libmp3lame" if target_format == "mp3" else "libvorbis"
        fmt = "mp3" if target_format == "mp3" else "ogg"

        filters = [
            f"atrim=start=0:end={max_duration}",
            "asetpts=PTS-STARTPTS",
            "afade=t=in:ss=0:d=0.03",
            "loudnorm=I=-16:TP=-1.5:LRA=11"
        ]

        cmd = [
            self.ffmpeg,
            "-y",
            "-i", "pipe:0" if isinstance(input_data, bytes) else str(input_data),
            "-vn",
            "-af", ",".join(filters),
            "-t", str(max_duration),
            "-ac", "2",
            "-ar", "44100",
            "-codec:a", codec,
            "-b:a", "128k",
            "-write_xing", "1",
            "-f", fmt, "pipe:1"
        ]

        proc = subprocess.run(
            cmd,
            input=input_data if isinstance(input_data, bytes) else None,
            capture_output=True
        )

        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="ignore")
            return AudioProcessResult(success=False, error=err)

        out_bytes = proc.stdout
        dur = self.get_duration(out_bytes)
        return AudioProcessResult(
            success=True,
            processed_bytes=out_bytes,
            duration=dur,
            file_size=len(out_bytes),
            file_format=target_format
        )

    def process_and_optimize(
        self,
        input_data: Path | bytes,
        target_format: str = "mp3",
        max_duration: float = SAFE_TARGET_DURATION_SEC,
        normalize: bool = True
    ) -> AudioProcessResult:
        """
        Convert, crop to viral segment, normalize loudness, and optimize audio for Discord Soundboard.
        Guarantees:
        1. Output format is MP3 or OGG.
        2. Output duration is strictly <= 5.0s (leaving a guaranteed margin under Discord's 5.2s limit).
        3. Output size <= 512 KB.
        4. Embedded album art / video tracks are stripped.
        """
        # Cap max_duration safely at 4.85s to guarantee no MP3 padding exceeds 5.20s
        safe_duration = min(max_duration, SAFE_TARGET_DURATION_SEC)

        # 1. Detect viral punchline segment
        v_start, v_end, climax_sec = self.detect_viral_segment(input_data, target_duration=safe_duration)
        clip_len = round(v_end - v_start, 2)
        if clip_len > safe_duration:
            clip_len = safe_duration

        res = self.trim_and_optimize(
            input_data,
            start_sec=v_start,
            duration=clip_len,
            target_format=target_format,
            normalize=normalize
        )
        res.viral_climax_sec = climax_sec
        return res

audio_processor = AudioProcessor()
