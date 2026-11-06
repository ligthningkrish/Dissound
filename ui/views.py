"""
Interactive Discord UI Views (Buttons, Select Menus, Paginators) for Dissound.
"""
import io
from pathlib import Path
from typing import List, Optional
import discord

from config import (
    EMBED_COLOR_DEFAULT,
    EMBED_COLOR_SUCCESS,
    EMBED_COLOR_ERROR,
    TIER_SOUNDBOARD_SLOTS,
    MAX_SOUND_DURATION_SEC,
    MAX_SOUND_FILE_SIZE_BYTES
)
from database.models import Sound
from database.repository import Repository
from audio.processor import audio_processor
from ui.modals import SoundCustomizeModal
from core.logger import log

repo = Repository()

async def upload_sound_to_guild(
    guild: discord.Guild,
    user: discord.Member,
    sound: Sound,
    custom_name: Optional[str] = None,
    volume: float = 1.0
) -> tuple[bool, str]:
    """
    Core business logic for adding a sound to a guild's soundboard:
    1. Permission verification (user and bot)
    2. Capacity limit check
    3. Duplicate name check
    4. Audio file validation and processing
    5. Discord API call (guild.create_soundboard_sound)
    6. Database upload history logging
    """
    final_name = (custom_name or sound.sound_name).strip()[:32]

    # 1. Check user permission: CREATE_GUILD_EXPRESSIONS or MANAGE_GUILD_EXPRESSIONS or Administrator
    user_perms = user.guild_permissions
    has_user_perm = (
        user_perms.administrator or 
        getattr(user_perms, "create_guild_expressions", False) or 
        getattr(user_perms, "manage_guild_expressions", False) or 
        getattr(user_perms, "create_expressions", False) or 
        getattr(user_perms, "manage_expressions", False)
    )
    if not has_user_perm:
        err = "You need the **Create Expressions** or **Manage Expressions** permission in this server to add soundboard sounds."
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
        return False, err

    # 1b. Check bot permissions
    bot_member = guild.me
    bot_perms = bot_member.guild_permissions
    has_bot_perm = (
        bot_perms.administrator or
        getattr(bot_perms, "create_guild_expressions", False) or 
        getattr(bot_perms, "manage_guild_expressions", False) or 
        getattr(bot_perms, "create_expressions", False) or 
        getattr(bot_perms, "manage_expressions", False)
    )
    if not has_bot_perm:
        err = "Dissound bot is missing the **Create Expressions** permission on this server."
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
        return False, err

    # 2. Check guild soundboard capacity
    try:
        existing_sounds = await guild.fetch_soundboard_sounds()
    except Exception:
        existing_sounds = guild.soundboard_sounds

    max_slots = TIER_SOUNDBOARD_SLOTS.get(guild.premium_tier, 8)
    if len(existing_sounds) >= max_slots:
        err = (
            f"Soundboard capacity reached ({len(existing_sounds)}/{max_slots} slots used). "
            f"Server Boost Level {guild.premium_tier} allows a maximum of {max_slots} sounds."
        )
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
        return False, err

    # 3. Check duplicate sound name
    if any(s.name.lower() == final_name.lower() for s in existing_sounds):
        err = f"A sound named '**{final_name}**' already exists on this server's Soundboard."
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
        return False, err

    # 4. Audio preparation
    sound_path = Path(sound.file_path)
    if not sound_path.exists():
        err = f"Audio source file for '{sound.sound_name}' was not found on disk."
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
        return False, err

    # Read bytes and optimize if needed
    raw_bytes = sound_path.read_bytes()
    dur = sound.duration
    size = len(raw_bytes)

    # Process and optimize if duration or size exceeds or format isn't mp3/ogg
    if dur > MAX_SOUND_DURATION_SEC or size > MAX_SOUND_FILE_SIZE_BYTES or sound.file_format not in ("mp3", "ogg"):
        proc_result = audio_processor.process_and_optimize(raw_bytes, target_format="mp3")
        if not proc_result.success or not proc_result.processed_bytes:
            err = proc_result.error or "Failed to optimize audio for Discord Soundboard."
            await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
            return False, err
        sound_bytes = proc_result.processed_bytes
    else:
        sound_bytes = raw_bytes

    # 5. Call Discord API
    try:
        new_sound = await guild.create_soundboard_sound(
            name=final_name,
            sound=sound_bytes,
            volume=volume,
            reason=f"Added by {user} via Dissound bot"
        )
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "SUCCESS")
        await repo.upsert_server(str(guild.id), guild.name, max_slots)
        await repo.upsert_user(str(user.id), str(user))
        return True, f"Successfully added **{new_sound.name}** to the server Soundboard! ({len(existing_sounds) + 1}/{max_slots} slots used)"
    except discord.Forbidden:
        err = "Forbidden: The bot does not have permission to upload soundboard sounds."
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
        return False, err
    except discord.HTTPException as e:
        err = f"Discord API Error: {e.text} (Code: {e.code})"
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
        return False, err
    except Exception as e:
        err = f"Unexpected error during upload: {str(e)}"
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
        return False, err


class SoundCardView(discord.ui.View):
    """Interactive view for a single sound with Preview and Add actions."""

    def __init__(self, sound: Sound, author_id: int, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.sound = sound
        self.author_id = author_id

    @discord.ui.button(label="Add to Soundboard", style=discord.ButtonStyle.success, emoji="➕")
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This command can only be used in a Discord server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        success, message = await upload_sound_to_guild(
            guild=interaction.guild,
            user=interaction.user,
            sound=self.sound
        )
        embed = discord.Embed(
            title="Soundboard Upload: Success!" if success else "Soundboard Upload Failed",
            description=message,
            color=EMBED_COLOR_SUCCESS if success else EMBED_COLOR_ERROR
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Preview Audio", style=discord.ButtonStyle.primary, emoji="🔊")
    async def preview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        sound_path = Path(self.sound.file_path)
        if not sound_path.exists():
            await interaction.response.send_message("Audio file is missing from storage.", ephemeral=True)
            return

        file = discord.File(str(sound_path), filename=f"{self.sound.sound_id}.{self.sound.file_format}")
        embed = discord.Embed(
            title=f"🔊 Preview: {self.sound.sound_name}",
            description=f"**Category:** {self.sound.category}\n**Duration:** {self.sound.duration}s",
            color=EMBED_COLOR_DEFAULT
        )
        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

    @discord.ui.button(label="Customize & Add", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def customize_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a server.", ephemeral=True)
            return

        async def modal_callback(modal_interaction: discord.Interaction, name: str, volume: float):
            await modal_interaction.response.defer(ephemeral=True)
            success, message = await upload_sound_to_guild(
                guild=modal_interaction.guild, # type: ignore
                user=modal_interaction.user, # type: ignore
                sound=self.sound,
                custom_name=name,
                volume=volume
            )
            embed = discord.Embed(
                title="Soundboard Upload: Success!" if success else "Soundboard Upload Failed",
                description=message,
                color=EMBED_COLOR_SUCCESS if success else EMBED_COLOR_ERROR
            )
            await modal_interaction.followup.send(embed=embed, ephemeral=True)

        modal = SoundCustomizeModal(default_name=self.sound.sound_name, on_submit_callback=modal_callback)
        await interaction.response.send_modal(modal)


class SoundSelectDropdown(discord.ui.Select):
    """Dropdown for choosing between multiple sounds."""

    def __init__(self, sounds: List[Sound]):
        self.sounds_map = {s.sound_id: s for s in sounds}
        options = [
            discord.SelectOption(
                label=s.sound_name[:100],
                value=s.sound_id,
                description=f"[{s.category}] {s.duration}s | {(s.file_size // 1024)} KB"[:100],
                emoji="🎵"
            )
            for s in sounds[:25]
        ]
        super().__init__(placeholder="Select a meme sound to view...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_id = self.values[0]
        sound = self.sounds_map.get(selected_id)
        if not sound:
            await interaction.response.send_message("Sound not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🎵 {sound.sound_name}",
            description=f"**Category:** {sound.category}\n"
                        f"**Duration:** `{sound.duration}s` (Max 5.2s)\n"
                        f"**Size:** `{sound.file_size // 1024} KB` (Max 512 KB)\n"
                        f"**Format:** `{sound.file_format.upper()}`\n"
                        f"**Tags:** {sound.tags or 'None'}",
            color=EMBED_COLOR_DEFAULT
        )
        embed.set_footer(text="Click 'Add to Soundboard' to install it on your server!")

        view = SoundCardView(sound=sound, author_id=interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class SoundSelectView(discord.ui.View):
    """View container for the sound selection dropdown."""

    def __init__(self, sounds: List[Sound], timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.add_item(SoundSelectDropdown(sounds))


class CategorySelectDropdown(discord.ui.Select):
    """Dropdown for selecting a sound category."""

    def __init__(self, categories: List[str]):
        options = [
            discord.SelectOption(
                label=cat,
                value=cat,
                description=f"Browse {cat} sounds",
                emoji="📂"
            )
            for cat in categories[:25]
        ]
        super().__init__(placeholder="Choose a category to browse...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        sounds = await repo.get_sounds_by_category(cat)
        if not sounds:
            await interaction.response.send_message(f"No sounds found in '{cat}'.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📂 Category: {cat} ({len(sounds)} sounds)",
            description="Select a sound from the dropdown below to preview or add to your server's soundboard:",
            color=EMBED_COLOR_DEFAULT
        )
        view = SoundSelectView(sounds=sounds)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class CategorySelectView(discord.ui.View):
    """View container for category selection."""

    def __init__(self, categories: List[str], timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.add_item(CategorySelectDropdown(categories))


class SoundboardDeleteConfirmView(discord.ui.View):
    """Confirmation view for deleting a soundboard sound."""

    def __init__(self, sound: discord.SoundboardSound, author_id: int):
        super().__init__(timeout=60.0)
        self.sound = sound
        self.author_id = author_id

    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command initiator can confirm.", ephemeral=True)
            return

        try:
            name = self.sound.name
            await self.sound.delete(reason=f"Deleted by {interaction.user} via Dissound bot")
            embed = discord.Embed(
                title="Soundboard Sound Deleted",
                description=f"Successfully removed **{name}** from this server's soundboard.",
                color=EMBED_COLOR_SUCCESS
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            await interaction.response.send_message(f"Failed to delete sound: {e}", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Sound deletion canceled.", embed=None, view=None)


class MemeCandidateHunterView(discord.ui.View):
    """
    Interactive carousel view that lets the user preview multiple real internet sound candidates
    until they find the exact meme clip they want to add to their server soundboard.
    """

    def __init__(self, candidates: List[Sound], author_id: int, query: str, timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.candidates = candidates
        self.author_id = author_id
        self.query = query
        self.current_index = 0
        self._update_buttons()

    def _update_buttons(self):
        total = len(self.candidates)
        # Prev button is index 0
        self.prev_button.disabled = (self.current_index <= 0)
        # Next button is index 3
        self.next_button.disabled = (self.current_index >= total - 1)
        self.counter_button.label = f"{self.current_index + 1} / {total}"

    def build_embed(self) -> discord.Embed:
        sound = self.candidates[self.current_index]
        total = len(self.candidates)

        # Detect source website from tags or sound_id
        tags_lower = (sound.tags or "").lower()
        if "myinstants" in tags_lower or "myinstants" in sound.sound_id:
            source_badge = "Myinstants"
        elif "soundboardmax" in tags_lower or "sbmax" in sound.sound_id:
            source_badge = "SoundboardMax"
        elif "soundboard guy" in tags_lower or "sbguy" in sound.sound_id:
            source_badge = "Soundboard Guy"
        elif "orange" in tags_lower or "orange" in sound.sound_id:
            source_badge = "Orange Free Sounds"
        elif "freesound" in tags_lower or "freesound" in sound.sound_id:
            source_badge = "Freesound"
        elif sound.source_url:
            source_badge = "Web Sound Repository"
        else:
            source_badge = "Dissound Library"

        embed = discord.Embed(
            title=f"🌐 Internet Meme Scout: '{sound.sound_name}'",
            description=(
                f"**Search Query:** `{self.query}`\n"
                f"**Candidate:** `{self.current_index + 1} of {total}`\n\n"
                f"⏱️ **Duration:** `{sound.duration}s` (Auto-trimmed to Discord &le; 5.2s)\n"
                f"📦 **File Size:** `{(sound.file_size // 1024)} KB` (Discord &le; 512 KB)\n"
                f"🏷️ **Category:** `{sound.category}`\n"
                f"📡 **Source Website:** `{source_badge}`"
            ),
            color=EMBED_COLOR_DEFAULT
        )
        embed.set_footer(text="🎧 Click 'Preview Audio' to listen. Use ◀️ / ▶️ to browse other versions!")
        return embed

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the search initiator can browse versions.", ephemeral=True)
            return

        if self.current_index > 0:
            self.current_index -= 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.secondary, disabled=True, row=0)
    async def counter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.secondary, row=0)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the search initiator can browse versions.", ephemeral=True)
            return

        if self.current_index < len(self.candidates) - 1:
            self.current_index += 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="🔊 Preview Audio", style=discord.ButtonStyle.primary, emoji="🎧", row=1)
    async def preview_sound(self, interaction: discord.Interaction, button: discord.ui.Button):
        sound = self.candidates[self.current_index]
        sound_path = Path(sound.file_path)

        if not sound_path.exists():
            await interaction.response.send_message("Audio file is missing from cache.", ephemeral=True)
            return

        file = discord.File(str(sound_path), filename=f"{sound.sound_id}.mp3")
        embed = discord.Embed(
            title=f"🔊 Playing Preview: {sound.sound_name}",
            description=f"Candidate #{self.current_index + 1} ({sound.duration}s)\n*Listen in player above!*",
            color=EMBED_COLOR_DEFAULT
        )
        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

    @discord.ui.button(label="Add to Soundboard", style=discord.ButtonStyle.success, emoji="➕", row=1)
    async def add_soundboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        sound = self.candidates[self.current_index]
        success, message = await upload_sound_to_guild(
            guild=interaction.guild,
            user=interaction.user,
            sound=sound
        )
        embed = discord.Embed(
            title="Soundboard Upload: Success!" if success else "Soundboard Upload Failed",
            description=message,
            color=EMBED_COLOR_SUCCESS if success else EMBED_COLOR_ERROR
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
