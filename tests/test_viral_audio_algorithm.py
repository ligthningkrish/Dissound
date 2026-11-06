import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import discord

from audio.processor import audio_processor, SAFE_TARGET_DURATION_SEC
from database.db import init_db
from database.models import Sound
from database.repository import Repository
from ui.views import upload_sound_to_guild


class TestViralAudioAlgorithm(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()
        self.repo = Repository()

    def test_detect_viral_segment_on_short_audio(self):
        # A 2.0-second sine wave
        short_sound = Path("tests/test_short_sine.mp3")
        import subprocess
        subprocess.run([
            audio_processor.ffmpeg, "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-codec:a", "libmp3lame", str(short_sound)
        ], capture_output=True)

        data = short_sound.read_bytes()
        start, end, climax = audio_processor.detect_viral_segment(data, target_duration=4.85)
        self.assertAlmostEqual(start, 0.0, delta=0.1)
        self.assertTrue(end <= 2.2)
        if short_sound.exists():
            short_sound.unlink()

    def test_detect_viral_segment_on_long_audio_with_climax(self):
        # A 12-second track with quiet intro and loud explosion at 6s
        long_sound = Path("tests/test_long_climax.mp3")
        import subprocess
        subprocess.run([
            audio_processor.ffmpeg, "-y",
            "-f", "lavfi", "-i", "sine=frequency=220:duration=5",
            "-f", "lavfi", "-i", "sine=frequency=880:duration=2",
            "-f", "lavfi", "-i", "sine=frequency=220:duration=5",
            "-filter_complex", "[0:a]volume=0.02[a0];[1:a]volume=1.0[a1];[2:a]volume=0.02[a2];[a0][a1][a2]concat=n=3:v=0:a=1[out]",
            "-map", "[out]", "-codec:a", "libmp3lame", str(long_sound)
        ], capture_output=True)

        data = long_sound.read_bytes()
        start, end, climax = audio_processor.detect_viral_segment(data, target_duration=4.85)
        # Climax should be detected near 5s-7s
        self.assertTrue(4.5 <= climax <= 7.5, f"Climax was {climax}")
        self.assertTrue(end - start <= 4.86, f"Window duration {end - start} exceeds target")
        self.assertTrue(start >= 4.0, f"Start {start} should be near the blast")

        # Process with process_and_optimize
        res = audio_processor.process_and_optimize(data, max_duration=4.85)
        self.assertTrue(res.success)
        self.assertTrue(res.duration <= 5.0, f"Processed duration {res.duration} > 5.0s")
        self.assertTrue(res.file_size <= 524288)

        if long_sound.exists():
            long_sound.unlink()

    async def test_upload_sound_to_guild_re_trims_stale_overlength_audio(self):
        # Create a mock guild and user
        guild = MagicMock(spec=discord.Guild)
        guild.id = 12345
        guild.name = "Test Guild"
        guild.premium_tier = 0
        guild.fetch_soundboard_sounds = AsyncMock(return_value=[])

        user = MagicMock(spec=discord.Member)
        user.id = 67890
        user.guild = guild
        perms = MagicMock()
        perms.administrator = True
        user.guild_permissions = perms

        bot_member = MagicMock(spec=discord.Member)
        bot_perms = MagicMock()
        bot_perms.administrator = True
        bot_member.guild_permissions = bot_perms
        guild.me = bot_member

        # Simulate create_soundboard_sound checking duration
        created_sound = MagicMock(spec=discord.SoundboardSound)
        created_sound.name = "Test Siren"
        
        async def mock_create_sound(name, sound, volume, reason):
            dur = audio_processor.get_duration(sound)
            if dur > 5.20:
                raise discord.HTTPException(response=MagicMock(), message="The provided file duration exceeds maximum of 5.2 seconds.")
            return created_sound

        guild.create_soundboard_sound = AsyncMock(side_effect=mock_create_sound)

        # Sound model pointing to an audio file
        test_file = Path("tests/test_upload_retrim.mp3")
        import subprocess
        subprocess.run([
            audio_processor.ffmpeg, "-y",
            "-f", "lavfi", "-i", "sine=frequency=300:duration=8",
            "-codec:a", "libmp3lame", str(test_file)
        ], capture_output=True)

        sound_model = Sound(
            sound_id="test_stale_sound",
            sound_name="Test Siren",
            category="SFX",
            file_path=str(test_file),
            duration=8.0,  # Deliberately over 5.2s
            file_size=test_file.stat().st_size,
            file_format="mp3"
        )

        success, message = await upload_sound_to_guild(
            guild=guild,
            user=user,
            sound=sound_model
        )

        self.assertTrue(success, f"Upload failed: {message}")
        self.assertIn("Successfully added", message)
        guild.create_soundboard_sound.assert_awaited_once()

        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    unittest.main()
