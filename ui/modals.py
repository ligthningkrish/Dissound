"""
Discord UI Modals for Dissound.
"""
import discord
from typing import Optional, Callable, Awaitable


class SoundCustomizeModal(discord.ui.Modal, title="Customize Soundboard Sound"):
    """Modal to allow user to adjust sound name and volume before adding to server soundboard."""

    def __init__(
        self,
        default_name: str,
        default_volume: float = 1.0,
        on_submit_callback: Optional[Callable[[discord.Interaction, str, float], Awaitable[None]]] = None
    ):
        super().__init__()
        self.on_submit_callback = on_submit_callback

        self.sound_name_input = discord.ui.TextInput(
            label="Soundboard Name (2-32 characters)",
            placeholder="e.g. Vine Boom",
            default=default_name[:32],
            min_length=2,
            max_length=32,
            required=True
        )
        self.add_item(self.sound_name_input)

        self.volume_input = discord.ui.TextInput(
            label="Playback Volume (0.1 to 1.0)",
            placeholder="1.0",
            default=str(default_volume),
            min_length=1,
            max_length=4,
            required=False
        )
        self.add_item(self.volume_input)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.sound_name_input.value.strip()
        vol_str = self.volume_input.value.strip()

        try:
            vol = float(vol_str) if vol_str else 1.0
            vol = max(0.1, min(1.0, vol))
        except ValueError:
            vol = 1.0

        if self.on_submit_callback:
            await self.on_submit_callback(interaction, name, vol)
        else:
            await interaction.response.send_message(
                f"Configured sound: **{name}** with volume `{vol}`",
                ephemeral=True
            )


class SoundTrimModal(discord.ui.Modal, title="Audio Trimmer & Soundboard Settings"):
    """
    Interactive modal allowing users to trim audio clips to <= 5.0s,
    customize sound name, start offset, and playback volume for Discord Soundboard.
    """

    def __init__(
        self,
        sound_name: str,
        total_duration: float,
        suggested_start: float = 0.0,
        suggested_duration: float = 4.85,
        default_volume: float = 1.0,
        on_submit_callback: Optional[Callable[[discord.Interaction, str, float, float, float], Awaitable[None]]] = None
    ):
        super().__init__()
        self.total_duration = total_duration
        self.on_submit_callback = on_submit_callback

        self.name_input = discord.ui.TextInput(
            label="Soundboard Name (2-32 characters)",
            placeholder="Meme sound name",
            default=sound_name[:32],
            min_length=2,
            max_length=32,
            required=True
        )
        self.add_item(self.name_input)

        max_start = max(0.0, round(total_duration - 0.5, 1))
        self.start_input = discord.ui.TextInput(
            label=f"Trim Start Time (sec, 0.0 to {max_start})",
            placeholder="0.0",
            default=str(round(suggested_start, 2)),
            min_length=1,
            max_length=6,
            required=True
        )
        self.add_item(self.start_input)

        self.duration_input = discord.ui.TextInput(
            label="Duration (sec, Discord Max 5.0s)",
            placeholder="4.85",
            default=str(round(min(5.0, suggested_duration), 2)),
            min_length=1,
            max_length=5,
            required=True
        )
        self.add_item(self.duration_input)

        self.volume_input = discord.ui.TextInput(
            label="Playback Volume (0.1 - 1.0)",
            placeholder="1.0",
            default=str(default_volume),
            min_length=1,
            max_length=4,
            required=False
        )
        self.add_item(self.volume_input)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name_input.value.strip()
        try:
            start_sec = max(0.0, float(self.start_input.value.strip()))
        except ValueError:
            start_sec = 0.0

        try:
            dur_sec = max(0.5, min(5.0, float(self.duration_input.value.strip())))
        except ValueError:
            dur_sec = 4.85

        try:
            vol_val = self.volume_input.value.strip()
            vol = max(0.1, min(1.0, float(vol_val))) if vol_val else 1.0
        except ValueError:
            vol = 1.0

        if self.on_submit_callback:
            await self.on_submit_callback(interaction, name, start_sec, dur_sec, vol)
        else:
            await interaction.response.send_message(
                f"Trimmed: **{name}** from {start_sec}s for {dur_sec}s with volume {vol}",
                ephemeral=True
            )
