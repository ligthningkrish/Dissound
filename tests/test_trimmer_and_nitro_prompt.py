"""
Unit tests for Audio Trimmer, Discord Nitro Prompt View, and Discord 5.2s duration interception.
"""
import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import os
import discord

from database.models import Sound
from audio.processor import audio_processor, AudioProcessResult
from ui.modals import SoundTrimModal
from ui.views import (
    LongSoundNitroPromptView,
    SoundCardView,
    MemeCandidateHunterView,
    upload_sound_to_guild
)


class TestAudioTrimmerAndNitroPrompt(unittest.IsolatedAsyncioTestCase):
    """Test suite covering trimmer modal, Nitro prompt view, and 5.2s safety interception."""

    def setUp(self):
        # Create a synthetic 6.0 second audio file using ffmpeg tone
        self.temp_dir = tempfile.TemporaryDirectory()
        self.long_audio_path = Path(self.temp_dir.name) / "long_test.mp3"

        # Generate a 6.0s synthetic sine wave MP3 using ffmpeg
        import subprocess
        cmd = [
            audio_processor.ffmpeg, "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=6.0",
            "-ac", "2", "-ar", "44100",
            "-codec:a", "libmp3lame", "-b:a", "128k",
            str(self.long_audio_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        self.long_sound = Sound(
            sound_id="test_long_clip",
            sound_name="Super Long Meme Clip",
            category="Internet Meme",
            file_path=str(self.long_audio_path),
            duration=6.0,
            file_size=self.long_audio_path.stat().st_size,
            file_format="mp3"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_trim_and_optimize_custom_window(self):
        """Verify trim_and_optimize crops to user-specified start and duration <= 5.0s."""
        raw_bytes = self.long_audio_path.read_bytes()
        res = audio_processor.trim_and_optimize(
            raw_bytes,
            start_sec=1.0,
            duration=3.5,
            target_format="mp3"
        )

        self.assertTrue(res.success)
        self.assertIsNotNone(res.processed_bytes)
        self.assertLessEqual(res.duration, 5.0)
        self.assertGreaterEqual(res.duration, 3.2)
        self.assertLessEqual(res.file_size, 512 * 1024)

    def test_trim_and_optimize_clamps_oversized_duration_to_safe_limit(self):
        """Verify that duration requests > 5.0s are strictly clamped to avoid Discord 50124 errors."""
        raw_bytes = self.long_audio_path.read_bytes()
        res = audio_processor.trim_and_optimize(
            raw_bytes,
            start_sec=0.0,
            duration=8.0,
            target_format="mp3"
        )

        self.assertTrue(res.success)
        self.assertLessEqual(res.duration, 5.10, "Trimmed duration must never exceed Discord's 5.2s limit")
        self.assertLessEqual(res.file_size, 512 * 1024)

    def test_transcode_and_normalize_full_preserves_preview_duration(self):
        """Verify transcode_and_normalize_full preserves full audio duration for previewing."""
        raw_bytes = self.long_audio_path.read_bytes()
        res = audio_processor.transcode_and_normalize_full(raw_bytes, max_duration=60.0)

        self.assertTrue(res.success)
        # Should retain the full ~6.0s for playback preview
        self.assertGreaterEqual(res.duration, 5.5)

    def test_nitro_prompt_view_structure_and_embed(self):
        """Verify LongSoundNitroPromptView contains Discord Shop link and trimming controls."""
        view = LongSoundNitroPromptView(sound=self.long_sound, author_id=12345)
        embed = view.build_embed(6.0)

        # Check embed details
        self.assertIn("Exceeds Discord 5.2s", embed.title)
        self.assertIn("6.0s", embed.description)
        self.assertIn("Discord Nitro", embed.description)
        self.assertIn("Audio Trimmer Settings", embed.description)
        self.assertIn("AI Auto-Crop", embed.description)

        # Check link button to Discord Nitro Shop
        button_labels = [getattr(item, "label", None) for item in view.children]
        button_urls = [getattr(item, "url", None) for item in view.children]

        self.assertIn("Buy Discord Nitro", button_labels)
        self.assertIn("https://discord.com/nitro", button_urls)
        self.assertIn("Audio Trimmer Settings", button_labels)
        self.assertIn("AI Auto-Crop (Viral Hook)", button_labels)

    def test_sound_trim_modal_parsing(self):
        """Verify SoundTrimModal parses user inputs and enforces boundaries."""
        modal = SoundTrimModal(
            sound_name="Custom Trimmed Meme",
            total_duration=6.0,
            suggested_start=1.2,
            suggested_duration=4.5
        )

        self.assertEqual(modal.name_input.default, "Custom Trimmed Meme")
        self.assertEqual(modal.start_input.default, "1.2")
        self.assertEqual(modal.duration_input.default, "4.5")

    async def test_candidate_hunter_view_intercepts_long_audio(self):
        """Verify MemeCandidateHunterView prompts user with Nitro view when sound > 5.0s."""
        view = MemeCandidateHunterView(
            candidates=[self.long_sound],
            author_id=12345,
            query="test meme"
        )

        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.guild = MagicMock(spec=discord.Guild)
        mock_user = MagicMock(spec=discord.Member)
        mock_user.id = 12345
        mock_user.guild = mock_interaction.guild
        perms = MagicMock()
        perms.administrator = True
        mock_user.guild_permissions = perms
        mock_interaction.user = mock_user
        mock_interaction.response = MagicMock()
        mock_interaction.response.send_message = AsyncMock()

        # Simulate clicking "Add to Soundboard"
        await view.add_soundboard.callback(mock_interaction)

        # Must intercept and send LongSoundNitroPromptView, NOT call upload_sound_to_guild
        mock_interaction.response.send_message.assert_called_once()
        sent_view = mock_interaction.response.send_message.call_args[1].get("view")
        self.assertIsInstance(sent_view, LongSoundNitroPromptView)

    async def test_sound_card_view_intercepts_long_audio(self):
        """Verify SoundCardView intercepts sound > 5.0s and offers Nitro/Trimmer options."""
        view = SoundCardView(sound=self.long_sound, author_id=12345)

        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.guild = MagicMock(spec=discord.Guild)
        mock_user = MagicMock(spec=discord.Member)
        mock_user.id = 12345
        mock_user.guild = mock_interaction.guild
        perms = MagicMock()
        perms.administrator = True
        mock_user.guild_permissions = perms
        mock_interaction.user = mock_user
        mock_interaction.response = MagicMock()
        mock_interaction.response.send_message = AsyncMock()

        # Simulate clicking "Add to Soundboard"
        await view.add_button.callback(mock_interaction)

        mock_interaction.response.send_message.assert_called_once()
        sent_view = mock_interaction.response.send_message.call_args[1].get("view")
        self.assertIsInstance(sent_view, LongSoundNitroPromptView)

    async def test_upload_sound_to_guild_with_override_bytes(self):
        """Verify upload_sound_to_guild accepts trimmed override_bytes directly."""
        mock_guild = MagicMock(spec=discord.Guild)
        mock_guild.id = 999
        mock_guild.name = "Test Server"
        mock_guild.premium_tier = 1
        mock_guild.fetch_soundboard_sounds = AsyncMock(return_value=[])

        created_sound = MagicMock(spec=discord.SoundboardSound)
        created_sound.name = "Trimmed Meme"
        mock_guild.create_soundboard_sound = AsyncMock(return_value=created_sound)

        bot_member = MagicMock(spec=discord.Member)
        bot_perms = MagicMock()
        bot_perms.administrator = True
        bot_member.guild_permissions = bot_perms
        mock_guild.me = bot_member

        mock_user = MagicMock(spec=discord.Member)
        mock_user.id = 123
        mock_user.name = "TestAdmin"
        mock_user.guild = mock_guild
        user_perms = MagicMock()
        user_perms.administrator = True
        mock_user.guild_permissions = user_perms

        raw_bytes = self.long_audio_path.read_bytes()
        trimmed_res = audio_processor.trim_and_optimize(raw_bytes, start_sec=0.0, duration=4.5)

        success, msg = await upload_sound_to_guild(
            guild=mock_guild,
            user=mock_user,
            sound=self.long_sound,
            custom_name="Trimmed Meme",
            volume=0.8,
            override_bytes=trimmed_res.processed_bytes
        )

        self.assertTrue(success, f"Upload failed: {msg}")
        self.assertIn("Successfully added", msg)
        mock_guild.create_soundboard_sound.assert_called_once()
        # Verify passed bytes duration is <= 5.15s
        called_sound_bytes = mock_guild.create_soundboard_sound.call_args[1]["sound"]
        self.assertLessEqual(audio_processor.get_duration(called_sound_bytes), 5.15)


if __name__ == "__main__":
    unittest.main()
