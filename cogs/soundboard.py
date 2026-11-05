"""
Discord Soundboard management cog for Dissound.
Handles /add, /upload, /soundboard list, /soundboard status, and /soundboard delete.
"""
from typing import List, Optional
import discord
from discord import app_commands
from discord.ext import commands

from config import (
    EMBED_COLOR_DEFAULT,
    EMBED_COLOR_SUCCESS,
    EMBED_COLOR_ERROR,
    TIER_SOUNDBOARD_SLOTS,
    SOUNDS_DIR,
    DEFAULT_VOLUME
)
from database.models import Sound
from database.repository import Repository
from audio.processor import audio_processor
from audio.downloader import AudioDownloader
from ui.views import upload_sound_to_guild, SoundboardDeleteConfirmView
from core.logger import log

repo = Repository()

async def library_sound_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocomplete for adding sound from catalog."""
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

class SoundboardGroup(app_commands.Group):
    """Subcommands under /soundboard"""
    def __init__(self):
        super().__init__(name="soundboard", description="Manage server Soundboard sounds and slots")

class SoundboardCog(commands.Cog, name="Soundboard Management"):
    """Server soundboard upload and management operations."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    soundboard_group = SoundboardGroup()

    @app_commands.command(name="add", description="Add a meme sound from the catalog directly to your server Soundboard.")
    @app_commands.describe(
        sound_name="Sound from the Dissound catalog",
        custom_name="Optional custom name for your server's soundboard (2-32 chars)",
        volume="Playback volume between 0.1 and 1.0 (default 1.0)"
    )
    @app_commands.autocomplete(sound_name=library_sound_autocomplete)
    async def add(
        self,
        interaction: discord.Interaction,
        sound_name: str,
        custom_name: Optional[str] = None,
        volume: Optional[float] = DEFAULT_VOLUME
    ):
        """Add library sound to guild soundboard."""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This command can only be used in a Discord server.", ephemeral=True)
            return

        sound = await repo.get_sound_by_name(sound_name)
        if not sound:
            results = await repo.search_sounds(sound_name, limit=1)
            sound = results[0] if results else None

        if not sound:
            await interaction.response.send_message(
                f"Sound '**{sound_name}**' was not found in catalog. Use `/search` to find sounds.",
                ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        vol = max(0.1, min(1.0, volume or DEFAULT_VOLUME))
        success, message = await upload_sound_to_guild(
            guild=interaction.guild,
            user=interaction.user,
            sound=sound,
            custom_name=custom_name,
            volume=vol
        )

        embed = discord.Embed(
            title="✅ Sound Added to Soundboard!" if success else "❌ Failed to Add Sound",
            description=message,
            color=EMBED_COLOR_SUCCESS if success else EMBED_COLOR_ERROR
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="upload", description="Upload a custom audio file and automatically add it to your server's Soundboard.")
    @app_commands.describe(
        audio_file="Audio file to upload (MP3, OGG, WAV, etc.)",
        sound_name="Display name for the soundboard (2-32 characters)",
        category="Category for catalog indexing (default: Community)",
        volume="Playback volume between 0.1 and 1.0 (default: 1.0)"
    )
    async def upload(
        self,
        interaction: discord.Interaction,
        audio_file: discord.Attachment,
        sound_name: str,
        category: Optional[str] = "Community",
        volume: Optional[float] = DEFAULT_VOLUME
    ):
        """Upload custom audio file with automatic processing and optimization."""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        # Validate name
        is_valid_name, name_err = audio_processor.validate_sound_name(sound_name)
        if not is_valid_name:
            await interaction.response.send_message(f"Invalid sound name: {name_err}", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        # 1. Download attachment bytes safely
        raw_bytes, download_err = await AudioDownloader.download_file(audio_file.url)
        if download_err or not raw_bytes:
            await interaction.followup.send(f"Failed to read attached file: {download_err}")
            return

        # 2. Process, trim (> 5.2s auto-cut), normalize, and convert to MP3
        proc_result = audio_processor.process_and_optimize(raw_bytes, target_format="mp3")
        if not proc_result.success or not proc_result.processed_bytes:
            await interaction.followup.send(f"Audio processing failed: {proc_result.error}")
            return

        # 3. Save into local assets
        safe_id = "".join(c if c.isalnum() else "_" for c in sound_name.lower())[:32]
        saved_file = SOUNDS_DIR / f"custom_{interaction.guild.id}_{safe_id}.mp3"
        saved_file.write_bytes(proc_result.processed_bytes)

        # 4. Save into library repository
        sound_record = Sound(
            sound_id=f"guild_{interaction.guild.id}_{safe_id}",
            sound_name=sound_name[:32],
            category=category or "Community",
            file_path=str(saved_file),
            duration=proc_result.duration,
            file_size=proc_result.file_size,
            file_format="mp3",
            source_url=f"Uploaded by {interaction.user}",
            tags=f"custom, {sound_name.lower()}"
        )
        await repo.add_sound(sound_record)

        # 5. Upload to guild soundboard
        vol = max(0.1, min(1.0, volume or DEFAULT_VOLUME))
        success, message = await upload_sound_to_guild(
            guild=interaction.guild,
            user=interaction.user,
            sound=sound_record,
            custom_name=sound_name,
            volume=vol
        )

        embed = discord.Embed(
            title="✅ Custom Sound Uploaded & Installed!" if success else "⚠️ Sound Saved to Catalog, but Soundboard Upload Failed",
            description=message,
            color=EMBED_COLOR_SUCCESS if success else EMBED_COLOR_ERROR
        )
        embed.add_field(name="Processed Duration", value=f"`{proc_result.duration}s`", inline=True)
        embed.add_field(name="Processed Size", value=f"`{proc_result.file_size // 1024} KB`", inline=True)
        await interaction.followup.send(embed=embed)

    @soundboard_group.command(name="list", description="List all sounds currently active on this server's Soundboard.")
    async def list_soundboard(self, interaction: discord.Interaction):
        """List active soundboard sounds."""
        if not interaction.guild:
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        await interaction.response.defer()
        try:
            sounds = await interaction.guild.fetch_soundboard_sounds()
        except Exception:
            sounds = interaction.guild.soundboard_sounds

        max_slots = TIER_SOUNDBOARD_SLOTS.get(interaction.guild.premium_tier, 8)

        embed = discord.Embed(
            title=f"🔊 {interaction.guild.name} Soundboard Sounds",
            description=f"**Capacity:** `{len(sounds)} / {max_slots} slots used`\n"
                        f"**Server Boost Level:** `Tier {interaction.guild.premium_tier}`\n\n",
            color=EMBED_COLOR_DEFAULT
        )

        if not sounds:
            embed.description += "*No sounds on this server yet! Add some with `/search` or `/add`.*"
        else:
            for idx, s in enumerate(sounds, start=1):
                emoji_str = f"{s.emoji} " if s.emoji else ""
                creator = f"<@{s.user.id}>" if s.user else "Unknown"
                embed.add_field(
                    name=f"{idx}. {emoji_str}{s.name}",
                    value=f"Volume: `{s.volume}` | Added by {creator}",
                    inline=True
                )

        await interaction.followup.send(embed=embed)

    @soundboard_group.command(name="status", description="Check server Soundboard slot usage, capacity, and boost tier.")
    async def soundboard_status(self, interaction: discord.Interaction):
        """Display slot capacity and boost tier."""
        if not interaction.guild:
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        try:
            sounds = await interaction.guild.fetch_soundboard_sounds()
        except Exception:
            sounds = interaction.guild.soundboard_sounds

        tier = interaction.guild.premium_tier
        max_slots = TIER_SOUNDBOARD_SLOTS.get(tier, 8)
        used = len(sounds)
        available = max(0, max_slots - used)

        pct = int((used / max_slots) * 10)
        progress_bar = "█" * pct + "░" * (10 - pct)

        embed = discord.Embed(
            title=f"📊 Soundboard Capacity: {interaction.guild.name}",
            color=EMBED_COLOR_DEFAULT
        )
        embed.add_field(name="Slots Used", value=f"`{used} / {max_slots}` ({progress_bar})", inline=False)
        embed.add_field(name="Slots Remaining", value=f"`{available}` available", inline=True)
        embed.add_field(name="Boost Level", value=f"Tier {tier} ({interaction.guild.premium_subscription_count} boosts)", inline=True)
        embed.add_field(
            name="Tier Capacity Guide",
            value="• Tier 0 (No Boost): 8 slots\n• Tier 1: 24 slots\n• Tier 2: 36 slots\n• Tier 3: 48 slots",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @soundboard_group.command(name="delete", description="Remove a sound from this server's Soundboard.")
    @app_commands.describe(sound_name="The name of the sound to remove")
    async def delete_soundboard(self, interaction: discord.Interaction, sound_name: str):
        """Remove a soundboard sound with confirmation."""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        # Check permission
        user_perms = interaction.user.guild_permissions
        can_manage = (
            user_perms.administrator or 
            getattr(user_perms, "manage_guild_expressions", False) or 
            getattr(user_perms, "manage_expressions", False)
        )
        if not can_manage:
            await interaction.response.send_message("You need **Manage Expressions** permission to delete soundboard sounds.", ephemeral=True)
            return

        try:
            sounds = await interaction.guild.fetch_soundboard_sounds()
        except Exception:
            sounds = interaction.guild.soundboard_sounds

        target = next((s for s in sounds if s.name.lower() == sound_name.strip().lower()), None)
        if not target:
            await interaction.response.send_message(
                f"Sound '**{sound_name}**' was not found on this server's Soundboard.\nCheck `/soundboard list` for active sounds.",
                ephemeral=True
            )
            return

        view = SoundboardDeleteConfirmView(sound=target, author_id=interaction.user.id)
        embed = discord.Embed(
            title="⚠️ Confirm Sound Deletion",
            description=f"Are you sure you want to remove **{target.name}** from the server's Soundboard?",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SoundboardCog(bot))
