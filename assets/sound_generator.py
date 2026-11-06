"""
Generates bundled meme sounds using mathematical synthesis and encodes them to MP3.
Ensures Dissound has an out-of-the-box working catalog of iconic meme sounds.
"""
import math
import struct
import wave
import io
import sys
import subprocess
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import imageio_ffmpeg
from config import SOUNDS_DIR
from core.logger import log

def synthesize_wav(duration: float, sample_func) -> bytes:
    """Helper to synthesize 44100Hz 16-bit mono WAV in-memory."""
    sr = 44100
    total_samples = int(sr * duration)
    frames = bytearray()
    for i in range(total_samples):
        t = i / sr
        val = sample_func(t, duration)
        # Clamp to -1.0 .. 1.0
        val = max(-1.0, min(1.0, val))
        sample_int16 = int(val * 32767)
        frames.extend(struct.pack('<h', sample_int16))

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(frames)
    return buf.getvalue()

def wav_to_mp3(wav_bytes: bytes, output_path: Path) -> None:
    """Convert WAV bytes to MP3 file using bundled FFmpeg."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "wav", "-i", "pipe:0",
            "-codec:a", "libmp3lame",
            "-b:a", "128k",
            str(output_path)
        ],
        input=wav_bytes,
        capture_output=True,
        check=True
    )

def generate_vine_boom(t, dur):
    # Deep distorted sub-bass drop
    freq = 110 * math.exp(-3.5 * t) + 32
    decay = math.exp(-2.2 * t)
    s = math.sin(2 * math.pi * freq * t) * decay
    # Add punchy distortion
    s = math.tanh(s * 3.5)
    return s

def generate_metal_pipe(t, dur):
    # Harsh metallic clang with resonant overtone modes
    modes = [(850, 1.0), (1340, 0.8), (2100, 0.6), (3450, 0.4), (5200, 0.2)]
    s = 0.0
    for freq, amp in modes:
        # Metallic dissonance
        s += amp * math.sin(2 * math.pi * freq * t) * math.exp(-t * (4 + freq/1000))
    # Sharp initial impact noise
    impact = (math.sin(10000 * t) * 0.5) * math.exp(-40 * t)
    return math.tanh((s + impact) * 2.2)

def generate_windows_error(t, dur):
    # Classic Windows two-tone chord: 523Hz (C5) + 659Hz (E5) with gentle decay
    s1 = math.sin(2 * math.pi * 523.25 * t)
    s2 = math.sin(2 * math.pi * 659.25 * t)
    decay = math.exp(-2.5 * t)
    return 0.5 * (s1 + s2) * decay

def generate_airhorn(t, dur):
    # Iconic triple-reggae airhorn blasts
    # Blast pattern: 0-0.25s, 0.35-0.6s, 0.7-1.1s
    def blast(local_t):
        f = 466.16  # Bb4
        # Sawtooth harmonic buzz
        val = sum(math.sin(2 * math.pi * f * k * local_t) / k for k in range(1, 8))
        return val * 0.3

    if 0.0 <= t < 0.22:
        return blast(t) * min(1.0, t * 50)
    elif 0.28 <= t < 0.50:
        return blast(t - 0.28) * min(1.0, (t - 0.28) * 50)
    elif 0.56 <= t < 1.05:
        # Final blast with pitch bend up
        local_t = t - 0.56
        f = 466.16 + 25 * local_t
        val = sum(math.sin(2 * math.pi * f * k * local_t) / k for k in range(1, 8))
        env = math.exp(-local_t * 1.5)
        return val * 0.3 * env
    return 0.0

def generate_roblox_oof(t, dur):
    # Fast vocal descending pitch 450Hz -> 180Hz
    freq = 450 * math.exp(-4.5 * t) + 160
    env = math.exp(-3.5 * t)
    harmonics = math.sin(2 * math.pi * freq * t) + 0.4 * math.sin(4 * math.pi * freq * t)
    return math.tanh(harmonics * env * 1.8)

def generate_bruh(t, dur):
    # Resonant vowel formant sweep (600Hz -> 200Hz)
    f0 = 130 * math.exp(-1.8 * t) + 75
    env = math.exp(-1.8 * t)
    val = math.sin(2 * math.pi * f0 * t) + 0.6 * math.sin(2 * math.pi * (f0 * 2.1) * t)
    return val * env * 0.8

def generate_bonk(t, dur):
    # High pitch wood block / cartoon mallet bonk
    f = 1100 * math.exp(-8 * t) + 300
    env = math.exp(-12 * t)
    s = math.sin(2 * math.pi * f * t) * env
    return math.tanh(s * 2.5)

def generate_among_us(t, dur):
    # 4 note eerie suspense chime
    notes = [440, 523.25, 622.25, 587.33]  # A4, C5, D#5, D5
    step = 0.28
    idx = int(t / step)
    if idx < len(notes):
        local_t = t - (idx * step)
        f = notes[idx]
        env = math.exp(-local_t * 5.0)
        return (math.sin(2 * math.pi * f * local_t) + 0.3 * math.sin(4 * math.pi * f * local_t)) * env * 0.7
    return 0.0

def generate_anime_wow(t, dur):
    # Upward cheerful arpeggio
    notes = [523.25, 659.25, 783.99, 1046.50]
    step = 0.18
    idx = int(t / step)
    if idx < len(notes):
        local_t = t - (idx * step)
        f = notes[idx]
        env = math.exp(-local_t * 4.0)
        return math.sin(2 * math.pi * f * local_t) * env * 0.75
    return 0.0

def generate_tada(t, dur):
    # Major chord fanfare resolution
    chord = [523.25, 659.25, 783.99, 1046.50]
    s = sum(math.sin(2 * math.pi * f * t) for f in chord) * 0.25
    decay = math.exp(-1.5 * t)
    return s * decay

SOUND_DEFINITIONS = [
    ("vine_boom", "Vine Boom", "Meme Sounds", 1.5, generate_vine_boom, "vine, boom, bass, thud, dramatic, sound effect"),
    ("metal_pipe", "Metal Pipe", "Random & Funny", 1.8, generate_metal_pipe, "metal, pipe, falling, clang, loud, funny"),
    ("windows_error", "Windows XP Error", "Classic Internet", 1.2, generate_windows_error, "windows, xp, error, alert, classic, microsoft"),
    ("airhorn", "Airhorn", "Random & Funny", 1.2, generate_airhorn, "airhorn, mlg, hype, horn, celebration"),
    ("roblox_oof", "Roblox Oof", "Gaming", 0.9, generate_roblox_oof, "roblox, oof, death, gaming, funny"),
    ("bruh", "Bruh Sound Effect", "Meme Sounds", 1.2, generate_bruh, "bruh, meme, reaction, disappointment"),
    ("bonk", "Bonk", "Reactions", 0.8, generate_bonk, "bonk, hammer, cartoon, doge, horny jail"),
    ("among_us", "Among Us Impostor", "Gaming", 1.4, generate_among_us, "among us, sus, impostor, kill, gaming"),
    ("anime_wow", "Anime Wow", "Reactions", 1.0, generate_anime_wow, "anime, wow, cute, reaction, fairy"),
    ("tada", "Tada Fanfare", "Reactions", 1.5, generate_tada, "tada, success, fanfare, winner, cheer"),
]

def generate_all_bundled_sounds():
    """Generates all starter sounds and outputs them to assets/sounds/."""
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    for sid, name, cat, dur, fn, tags in SOUND_DEFINITIONS:
        out_file = SOUNDS_DIR / f"{sid}.mp3"
        wav_data = synthesize_wav(dur, fn)
        wav_to_mp3(wav_data, out_file)
        size = out_file.stat().st_size
        log.info(f"Generated sound '{name}' -> {out_file.name} ({size} bytes, {dur}s)")
        generated.append({
            "sound_id": sid,
            "sound_name": name,
            "category": cat,
            "file_path": str(out_file),
            "duration": dur,
            "file_size": size,
            "file_format": "mp3",
            "source_url": "Built-in Synthesizer",
            "tags": tags
        })
    return generated

if __name__ == "__main__":
    generate_all_bundled_sounds()
