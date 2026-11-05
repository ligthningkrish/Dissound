"""
Sound discovery commands and autocomplete cog for Dissound.
"""
from typing import List
import discord
from discord import app_commands
from discord.ext import commands

from config import EMBED_COLOR_DEFAULT
from database.models import Sound
from database.repository import Repository
from ui.views import SoundCardView, SoundSelectView, CategorySelectView

repo = Repository()

async def sound_name_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Dynamic autocomplete provider for sound names."""
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

class DiscoveryCog(commands.Cog, name="Sound Discovery"):
    """Commands to discover, search, and browse meme sounds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="search", description="Search the meme sound library by name, category, or tags.")
    @app_commands.describe(query="Name, keyword, or tag of the sound (e.g. vine boom, metal pipe, error)")
    @app_commands.autocomplete(query=sound_name_autocomplete)
    async def search(self, interaction: discord.Interaction, query: str):
        """Search sounds and return interactive card."""
        sounds = await repo.search_sounds(query, limit=25)

        if not sounds:
            embed = discord.Embed(
                title="🔍 No Sounds Found",
                description=f"Could not find any meme sounds matching '**{query}**'.\nTry searching for `vine boom`, `pipe`, `airhorn`, or browse with `/browse`.",
                color=discord.Color.dark_grey()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if len(sounds) == 1:
            # Single exact or best match
            sound = sounds[0]
            embed = discord.Embed(
                title=f"🎵 {sound.sound_name}",
                description=f"**Category:** {sound.category}\n"
                            f"**Duration:** `{sound.duration}s`\n"
                            f"**File Size:** `{sound.file_size // 1024} KB`\n"
                            f"**Format:** `{sound.file_format.upper()}`\n"
                            f"**Tags:** {sound.tags or 'None'}",
                color=EMBED_COLOR_DEFAULT
            )
            embed.set_footer(text="Click 'Add to Soundboard' to install it on your server!")
            view = SoundCardView(sound=sound, author_id=interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view)
        else:
            # Multiple matches -> Show summary with dropdown selector
            embed = discord.Embed(
                title=f"🔍 Search Results for '{query}' ({len(sounds)} found)",
                description="Select a sound from the menu below to preview or add to your soundboard:",
                color=EMBED_COLOR_DEFAULT
            )
            for idx, s in enumerate(sounds[:5], start=1):
                embed.add_field(
                    name=f"{idx}. {s.sound_name}",
                    value=f"**Cat:** {s.category} | **Dur:** {s.duration}s",
                    inline=True
                )
            if len(sounds) > 5:
                embed.set_footer(text=f"...and {len(sounds) - 5} more options in the dropdown below.")

            view = SoundSelectView(sounds=sounds)
            await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="browse", description="Browse sounds in the library by category.")
    @app_commands.describe(category="Optional category name to view immediately")
    async def browse(self, interaction: discord.Interaction, category: str = None):
        """Browse categories or sounds within a category."""
        categories = await repo.get_categories()

        if not category:
            embed = discord.Embed(
                title="📂 Sound Categories",
                description="Choose a category from the dropdown below to explore available sounds:",
                color=EMBED_COLOR_DEFAULT
            )
            view = CategorySelectView(categories=categories)
            await interaction.response.send_message(embed=embed, view=view)
            return

        # Direct category requested
        matching_cats = [c for c in categories if c.lower() == category.strip().lower()]
        target_cat = matching_cats[0] if matching_cats else category.strip()
        sounds = await repo.get_sounds_by_category(target_cat)

        if not sounds:
            embed = discord.Embed(
                title="Category Empty or Not Found",
                description=f"No sounds found for category '**{category}**'.\nAvailable categories: {', '.join(categories)}",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📂 {target_cat} ({len(sounds)} sounds)",
            description="Select a sound from the dropdown below to preview or add to your server:",
            color=EMBED_COLOR_DEFAULT
        )
        view = SoundSelectView(sounds=sounds)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="categories", description="List all sound categories available in Dissound.")
    async def categories(self, interaction: discord.Interaction):
        """Display list of all sound categories and stats."""
        cats = await repo.get_categories()
        embed = discord.Embed(
            title="📚 Dissound Sound Library Categories",
            description="Here are the available sound categories. Use `/browse <category>` or the menu to explore!",
            color=EMBED_COLOR_DEFAULT
        )
        for cat in cats:
            sounds = await repo.get_sounds_by_category(cat)
            embed.add_field(name=f"📁 {cat}", value=f"`{len(sounds)}` sound{'s' if len(sounds) != 1 else ''}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="trending", description="View the most popular meme sounds added to Discord servers.")
    async def trending(self, interaction: discord.Interaction):
        """View trending sounds."""
        sounds = await repo.get_trending_sounds(limit=10)
        embed = discord.Embed(
            title="🔥 Trending Meme Sounds",
            description="Most added sounds across Discord server soundboards:",
            color=0xFF7F50
        )
        if not sounds:
            embed.description = "No upload data yet. Be the first to add sounds using `/search` or `/browse`!"
            await interaction.response.send_message(embed=embed)
            return

        view = SoundSelectView(sounds=sounds)
        for idx, s in enumerate(sounds[:10], start=1):
            embed.add_field(name=f"#{idx} {s.sound_name}", value=f"Category: {s.category} ({s.duration}s)", inline=False)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="recent", description="View recently added sounds in the library.")
    async def recent(self, interaction: discord.Interaction):
        """View recently added sounds."""
        sounds = await repo.get_recent_sounds(limit=10)
        embed = discord.Embed(
            title="✨ Recently Added Sounds",
            description="Fresh sounds added to the Dissound catalog:",
            color=EMBED_COLOR_DEFAULT
        )
        view = SoundSelectView(sounds=sounds)
        for idx, s in enumerate(sounds[:10], start=1):
            embed.add_field(name=f"{idx}. {s.sound_name}", value=f"[{s.category}] - `{s.duration}s`", inline=False)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(DiscoveryCog(bot))
