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
