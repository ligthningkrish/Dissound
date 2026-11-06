"""
Sound preview cog for Dissound.
Sends audio clips and interactive cards directly into Discord text channels.
"""
from pathlib import Path
from typing import List
import discord
from discord import app_commands
from discord.ext import commands

from config import EMBED_COLOR_DEFAULT
from database.repository import Repository
from ui.views import SoundCardView

repo = Repository()

async def preview_sound_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocomplete for sound to preview."""
    if not current.strip():
        sounds = await repo.get_all_sounds(limit=25)
    else:
        sounds = await repo.search_sounds(current, limit=25)

    return [
        app_commands.Choice(
            name=f"{s.sound_name} [{s.category}]"[:100],
            value=s.sound_name
        )
        for s in sounds
    ][:25]

class PreviewCog(commands.Cog, name="Sound Preview"):
    """Cog for previewing meme sound effects before adding."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="preview", description="Listen to an audio preview of a sound with one-click Add to Soundboard.")
    @app_commands.describe(sound_name="The name of the sound you want to listen to")
    @app_commands.autocomplete(sound_name=preview_sound_autocomplete)
    async def preview(self, interaction: discord.Interaction, sound_name: str):
        """Play or send sound preview with Add button."""
        sound = await repo.get_sound_by_name(sound_name)
        if not sound:
            # Fallback to search
            results = await repo.search_sounds(sound_name, limit=1)
            sound = results[0] if results else None

        if not sound:
            embed = discord.Embed(
                title="Sound Not Found",
                description=f"Could not find sound '**{sound_name}**'. Try searching with `/search`.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        sound_path = Path(sound.file_path)
        if not sound_path.exists():
            await interaction.response.send_message(
                f"Audio file for '{sound.sound_name}' is currently unavailable on disk.",
                ephemeral=True
            )
            return

        file = discord.File(str(sound_path), filename=f"{sound.sound_id}.{sound.file_format}")
        embed = discord.Embed(
            title=f"🔊 Sound Preview: {sound.sound_name}",
            description=f"**Category:** {sound.category}\n"
                        f"**Duration:** `{sound.duration}s`\n"
                        f"**Size:** `{sound.file_size // 1024} KB`\n"
                        f"**Source:** {sound.source_url or 'Built-in library'}\n"
                        f"**Tags:** {sound.tags or 'None'}",
            color=EMBED_COLOR_DEFAULT
        )
        embed.set_footer(text="Listen to the audio above, then click 'Add to Soundboard' to install it!")

        view = SoundCardView(sound=sound, author_id=interaction.user.id)
        await interaction.response.send_message(embed=embed, file=file, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(PreviewCog(bot))
