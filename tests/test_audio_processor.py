"""
Unit and integration tests for Dissound Audio Processing Module.
Tests audio duration extraction, trimming, format validation, and size optimization.
"""
import unittest
from pathlib import Path
import sys

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import SOUNDS_DIR, MAX_SOUND_DURATION_SEC, MAX_SOUND_FILE_SIZE_BYTES
from audio.processor import AudioProcessor, audio_processor

class TestAudioProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = audio_processor
        self.test_sound = SOUNDS_DIR / "vine_boom.mp3"

    def test_file_exists_and_duration(self):
        """Test that generated sounds exist and duration is within Discord limits."""
        self.assertTrue(self.test_sound.exists(), f"Sample sound {self.test_sound} should exist.")
        dur = self.processor.get_duration(self.test_sound)
        self.assertGreater(dur, 0.0)
        self.assertLessEqual(dur, MAX_SOUND_DURATION_SEC, f"Duration {dur}s exceeds {MAX_SOUND_DURATION_SEC}s")

    def test_audio_validation_valid(self):
        """Validate a sound that meets all Discord criteria."""
        result = self.processor.validate_audio(self.test_sound)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error)
        self.assertLessEqual(result.duration, MAX_SOUND_DURATION_SEC)
        self.assertLessEqual(result.file_size, MAX_SOUND_FILE_SIZE_BYTES)

    def test_sound_name_validation(self):
        """Test soundboard sound name length rules (2-32 chars)."""
        valid, err = self.processor.validate_sound_name("Vine Boom")
        self.assertTrue(valid)
        self.assertIsNone(err)

        too_short, err = self.processor.validate_sound_name("A")
        self.assertFalse(too_short)
        self.assertIn("at least 2", err)

        too_long, err = self.processor.validate_sound_name("A" * 35)
        self.assertFalse(too_long)
        self.assertIn("cannot exceed 32", err)

    def test_audio_processing_and_trimming(self):
        """Test that the processor successfully optimizes audio to MP3 and <= 5.2s."""
        raw_bytes = self.test_sound.read_bytes()
        proc_result = self.processor.process_and_optimize(
            raw_bytes,
            target_format="mp3",
            max_duration=5.2
        )
        self.assertTrue(proc_result.success)
        self.assertIsNotNone(proc_result.processed_bytes)
        self.assertLessEqual(proc_result.duration, 5.2)
        self.assertLessEqual(proc_result.file_size, MAX_SOUND_FILE_SIZE_BYTES)
        self.assertEqual(proc_result.file_format, "mp3")

if __name__ == "__main__":
    unittest.main()
