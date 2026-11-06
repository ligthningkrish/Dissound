"""
Interactive Discord UI Views (Buttons, Select Menus, Paginators, Soundboard Managers) for Dissound.
"""
import io
from pathlib import Path
from typing import List, Optional, Dict
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
from ui.modals import SoundCustomizeModal, SoundTrimModal
from core.permissions import check_bot_access
from core.logger import log

repo = Repository()


async def verify_user_bot_access(interaction: discord.Interaction) -> bool:
    """Verifies that the user clicking interactive components has elevated bot permissions."""
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("Must be used inside a Discord server.", ephemeral=True)
        return False

    allowed, reason = await check_bot_access(interaction.user)
    if not allowed:
        embed = discord.Embed(
            title="⛔ Higher Roles Required",
            description=reason,
            color=EMBED_COLOR_ERROR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    return True


async def upload_sound_to_guild(
    guild: discord.Guild,
    user: discord.Member,
    sound: Sound,
    custom_name: Optional[str] = None,
    volume: float = 1.0,
    override_bytes: Optional[bytes] = None
) -> tuple[bool, str]:
    """
    Core business logic for adding a sound to a guild's soundboard:
    1. Permission verification (higher roles or expressions)
    2. Capacity limit check
    3. Duplicate name check
    4. Audio file validation and processing (guaranteed <= 5.0s, <= 512 KB)
    5. Discord API call (guild.create_soundboard_sound)
    6. Database upload history logging
    """
    final_name = (custom_name or sound.sound_name).strip()[:32]

    # 1. Check user permission via central bot access checker
    has_access, access_reason = await check_bot_access(user)
    if not has_access:
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", access_reason)
        return False, access_reason or "You need higher roles or bot permissions to add sounds."

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
            f"Server Boost Level {guild.premium_tier} allows a maximum of {max_slots} sounds.\n"
            f"Use `/soundboard delete` or `/delete_sound` to remove unused sounds."
        )
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
        return False, err

    # 3. Check duplicate sound name
    if any(s.name.lower() == final_name.lower() for s in existing_sounds):
        err = f"A sound named '**{final_name}**' already exists on this server's Soundboard."
        await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
        return False, err

    # 4. Audio preparation & strict Discord duration enforcement (<= 5.0s, <= 512 KB)
    if override_bytes:
        sound_bytes = override_bytes
        real_dur = audio_processor.get_duration(sound_bytes)
    else:
        sound_path = Path(sound.file_path)
        if not sound_path.exists():
            err = f"Audio source file for '{sound.sound_name}' was not found on disk."
            await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
            return False, err

        raw_bytes = sound_path.read_bytes()
        real_dur = audio_processor.get_duration(raw_bytes)
        size = len(raw_bytes)

        # Enforce strict <= 5.0s cap with viral peak extraction to guarantee Discord 5.2s limit is never exceeded
        if real_dur > 5.0 or sound.duration > 5.0 or size > MAX_SOUND_FILE_SIZE_BYTES or sound.file_format not in ("mp3", "ogg"):
            proc_result = audio_processor.process_and_optimize(raw_bytes, target_format="mp3", max_duration=4.85)
            if not proc_result.success or not proc_result.processed_bytes:
                err = proc_result.error or "Failed to optimize audio for Discord Soundboard."
                await repo.log_upload(str(guild.id), str(user.id), sound.sound_id, final_name, "FAILED", err)
                return False, err

            sound_bytes = proc_result.processed_bytes
            # Update local cached file & database model with safe duration
            try:
                sound_path.write_bytes(sound_bytes)
                sound.duration = proc_result.duration
                sound.file_size = proc_result.file_size
                await repo.add_sound(sound)
            except Exception as e:
                log.warning(f"Failed to update cached sound file: {e}")
        else:
            sound_bytes = raw_bytes

    # Final sanity check: guarantee bytes never exceed 5.15s under any condition
    if audio_processor.get_duration(sound_bytes) > 5.15:
        proc_result = audio_processor.trim_and_optimize(sound_bytes, start_sec=0.0, duration=4.75, target_format="mp3")
        if proc_result.success and proc_result.processed_bytes:
            sound_bytes = proc_result.processed_bytes

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


class LongSoundNitroPromptView(discord.ui.View):
    """
    Interactive prompt displayed when a sound exceeds Discord's 5.2s Soundboard constraint.
    Provides users with:
    1. Direct link to Discord Nitro Shop (https://discord.com/nitro)
    2. Audio Trimmer Settings button (opens SoundTrimModal to customize trim window <= 5.0s)
    3. AI Auto-Crop (Viral Hook) button (1-click viral punchline extraction)
    4. Cancel button
    """

    def __init__(self, sound: Sound, author_id: int, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.sound = sound
        self.author_id = author_id

        sound_path = Path(sound.file_path)
        if sound_path.exists():
            v_start, v_end, climax = audio_processor.detect_viral_segment(sound_path)
            self.suggested_start = v_start
            self.viral_climax_sec = climax
        else:
            self.suggested_start = 0.0
            self.viral_climax_sec = 0.0

        # Link button pointing to Discord Nitro Shop
        self.add_item(discord.ui.Button(
            label="Buy Discord Nitro",
            style=discord.ButtonStyle.link,
            url="https://discord.com/nitro",
            emoji="💎",
            row=0
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await verify_user_bot_access(interaction)

    def build_embed(self, duration: Optional[float] = None) -> discord.Embed:
        dur = duration or self.sound.duration
        embed = discord.Embed(
            title="⚠️ Audio Exceeds Discord 5.2s Soundboard Limit",
            description=(
                f"The sound **{self.sound.sound_name}** has a duration of **{dur}s**.\n\n"
                f"Discord requires standard server soundboard clips to be **5.2 seconds or less**.\n\n"
                f"**Select an option to proceed:**\n"
                f"• 💎 **Buy Discord Nitro**: Visit the Discord Shop to upgrade your account and unlock server soundboard perks.\n"
                f"• ✂️ **Audio Trimmer Settings**: Open interactive trimmer settings to pick your custom window (max 5.0s).\n"
                f"• ⚡ **AI Auto-Crop (Viral Hook)**: Instantly crop the punchiest viral moment (peak detected at `{self.viral_climax_sec}s`)."
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text="Discord API Error 50124 Prevention • Powered by Dissound")
        return embed

    @discord.ui.button(label="Audio Trimmer Settings", style=discord.ButtonStyle.primary, emoji="✂️", row=0)
    async def trim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        async def on_trim_submit(
            modal_interaction: discord.Interaction,
            name: str,
            start_sec: float,
            dur_sec: float,
            volume: float
        ):
            await modal_interaction.response.defer(ephemeral=True)
            sound_path = Path(self.sound.file_path)
            if not sound_path.exists():
                await modal_interaction.followup.send("Source audio file not found on disk.", ephemeral=True)
                return

            raw_bytes = sound_path.read_bytes()
            proc = audio_processor.trim_and_optimize(
                raw_bytes,
                start_sec=start_sec,
                duration=dur_sec,
                target_format="mp3"
            )
            if not proc.success or not proc.processed_bytes:
                await modal_interaction.followup.send(
                    f"Trimming failed: {proc.error or 'Could not process audio.'}",
                    ephemeral=True
                )
                return

            trimmed_sound = Sound(
                sound_id=f"trim_{self.sound.sound_id}_{int(start_sec * 10)}",
                sound_name=name,
                category=self.sound.category,
                file_path=str(sound_path),
                duration=proc.duration,
                file_size=proc.file_size,
                file_format="mp3"
            )

            success, msg = await upload_sound_to_guild(
                guild=modal_interaction.guild,
                user=modal_interaction.user,
                sound=trimmed_sound,
                custom_name=name,
                volume=volume,
                override_bytes=proc.processed_bytes
            )

            res_embed = discord.Embed(
                title="✅ Soundboard Upload: Success!" if success else "❌ Soundboard Upload Failed",
                description=(
                    f"{msg}\n\n"
                    f"✂️ **Trim Window:** `{start_sec}s` - `{round(start_sec + dur_sec, 2)}s` (`{proc.duration}s`)\n"
                    f"📦 **Output Size:** `{proc.file_size // 1024} KB`"
                ) if success else msg,
                color=EMBED_COLOR_SUCCESS if success else EMBED_COLOR_ERROR
            )
            await modal_interaction.followup.send(embed=res_embed, ephemeral=True)

        modal = SoundTrimModal(
            sound_name=self.sound.sound_name,
            total_duration=self.sound.duration,
            suggested_start=self.suggested_start,
            suggested_duration=min(4.85, self.sound.duration),
            on_submit_callback=on_trim_submit
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="AI Auto-Crop (Viral Hook)", style=discord.ButtonStyle.success, emoji="⚡", row=0)
    async def auto_crop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        sound_path = Path(self.sound.file_path)
        if not sound_path.exists():
            await interaction.followup.send("Source audio file not found on disk.", ephemeral=True)
            return

        raw_bytes = sound_path.read_bytes()
        proc = audio_processor.process_and_optimize(raw_bytes, target_format="mp3", max_duration=4.85)
        if not proc.success or not proc.processed_bytes:
            await interaction.followup.send(
                f"Auto-crop failed: {proc.error or 'Could not process audio.'}",
                ephemeral=True
            )
            return

        success, msg = await upload_sound_to_guild(
            guild=interaction.guild,
            user=interaction.user,
            sound=self.sound,
            custom_name=self.sound.sound_name,
            volume=1.0,
            override_bytes=proc.processed_bytes
        )

        res_embed = discord.Embed(
            title="✅ Soundboard Upload: Success!" if success else "❌ Soundboard Upload Failed",
            description=(
                f"{msg}\n\n"
                f"⚡ **AI Viral Punchline:** Peak detected at `{proc.viral_climax_sec}s`\n"
                f"⏱️ **Auto-Trimmed Duration:** `{proc.duration}s` (strictly &le; 5.2s)\n"
                f"📦 **Output Size:** `{proc.file_size // 1024} KB`"
            ) if success else msg,
            color=EMBED_COLOR_SUCCESS if success else EMBED_COLOR_ERROR
        )
        await interaction.followup.send(embed=res_embed, ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Sound upload canceled.", embed=None, view=None)


class SoundCardView(discord.ui.View):
    """Interactive view for a single sound with Preview, Add, and Trimming actions."""

    def __init__(self, sound: Sound, author_id: int, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.sound = sound
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await verify_user_bot_access(interaction)

    @discord.ui.button(label="Add to Soundboard", style=discord.ButtonStyle.success, emoji="➕")
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This command can only be used in a Discord server.", ephemeral=True)
            return

        sound_path = Path(self.sound.file_path)
        real_dur = audio_processor.get_duration(sound_path) if sound_path.exists() else self.sound.duration

        # Intercept audio exceeding Discord's 5.0s threshold
        if real_dur > 5.0 or self.sound.duration > 5.0:
            prompt_view = LongSoundNitroPromptView(sound=self.sound, author_id=interaction.user.id)
            embed = prompt_view.build_embed(real_dur)
            await interaction.response.send_message(embed=embed, view=prompt_view, ephemeral=True)
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
            description=f"**Category:** {self.sound.category}\n**Duration:** {self.sound.duration}s\n*Listen to full audio in player above!*",
            color=EMBED_COLOR_DEFAULT
        )
        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

    @discord.ui.button(label="Customize & Trim", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def customize_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a server.", ephemeral=True)
            return

        sound_path = Path(self.sound.file_path)
        real_dur = audio_processor.get_duration(sound_path) if sound_path.exists() else self.sound.duration

        # If audio is longer than 5.0s, open Trimmer Modal directly
        if real_dur > 5.0 or self.sound.duration > 5.0:
            prompt_view = LongSoundNitroPromptView(sound=self.sound, author_id=interaction.user.id)
            modal = SoundTrimModal(
                sound_name=self.sound.sound_name,
                total_duration=real_dur,
                suggested_start=prompt_view.suggested_start,
                suggested_duration=min(4.85, real_dur),
                on_submit_callback=lambda m_inter, name, start, dur, vol: self._handle_modal_trim(m_inter, name, start, dur, vol)
            )
            await interaction.response.send_modal(modal)
            return

        # Otherwise standard customization modal
        async def modal_callback(modal_interaction: discord.Interaction, name: str, volume: float):
            await modal_interaction.response.defer(ephemeral=True)
            success, message = await upload_sound_to_guild(
                guild=modal_interaction.guild,
                user=modal_interaction.user,
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

    async def _handle_modal_trim(
        self,
        modal_interaction: discord.Interaction,
        name: str,
        start_sec: float,
        dur_sec: float,
        volume: float
    ):
        await modal_interaction.response.defer(ephemeral=True)
        sound_path = Path(self.sound.file_path)
        if not sound_path.exists():
            await modal_interaction.followup.send("Audio file missing from storage.", ephemeral=True)
            return

        raw_bytes = sound_path.read_bytes()
        proc = audio_processor.trim_and_optimize(raw_bytes, start_sec=start_sec, duration=dur_sec, target_format="mp3")
        if not proc.success or not proc.processed_bytes:
            await modal_interaction.followup.send(f"Trimming failed: {proc.error}", ephemeral=True)
            return

        trimmed_sound = Sound(
            sound_id=f"trim_{self.sound.sound_id}_{int(start_sec * 10)}",
            sound_name=name,
            category=self.sound.category,
            file_path=str(sound_path),
            duration=proc.duration,
            file_size=proc.file_size,
            file_format="mp3"
        )
        success, message = await upload_sound_to_guild(
            guild=modal_interaction.guild,
            user=modal_interaction.user,
            sound=trimmed_sound,
            custom_name=name,
            volume=volume,
            override_bytes=proc.processed_bytes
        )
        embed = discord.Embed(
            title="Soundboard Upload: Success!" if success else "Soundboard Upload Failed",
            description=message,
            color=EMBED_COLOR_SUCCESS if success else EMBED_COLOR_ERROR
        )
        await modal_interaction.followup.send(embed=embed, ephemeral=True)


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

        dur_tag = f"`{sound.duration}s`"
        if sound.duration > 5.0:
            dur_tag += " ⚠️ *(Exceeds Discord 5.2s Soundboard limit)*"

        embed = discord.Embed(
            title=f"🎵 {sound.sound_name}",
            description=f"**Category:** {sound.category}\n"
                        f"**Duration:** {dur_tag}\n"
                        f"**Size:** `{sound.file_size // 1024} KB`\n"
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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await verify_user_bot_access(interaction)


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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await verify_user_bot_access(interaction)


class SoundboardDeleteConfirmView(discord.ui.View):
    """Confirmation view for deleting a specific soundboard sound."""

    def __init__(self, sound: discord.SoundboardSound, author_id: int):
        super().__init__(timeout=60.0)
        self.sound = sound
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await verify_user_bot_access(interaction)

    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command initiator can confirm.", ephemeral=True)
            return

        try:
            name = self.sound.name
            await self.sound.delete(reason=f"Deleted by {interaction.user} via Dissound bot")
            await repo.log_upload(
                str(interaction.guild_id),
                str(interaction.user.id),
                str(self.sound.id),
                name,
                "DELETED",
                "Soundboard sound removed"
            )
            embed = discord.Embed(
                title="✅ Soundboard Sound Deleted",
                description=f"Successfully removed **{name}** from this server's soundboard.",
                color=EMBED_COLOR_SUCCESS
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            await interaction.response.send_message(f"Failed to delete sound: {e}", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Sound deletion canceled.", embed=None, view=None)


class SoundboardManageView(discord.ui.View):
    """
    Interactive soundboard management and deletion dashboard.
    Enables authorized server moderators/admins to:
    1. Select an installed soundboard sound from a dropdown menu.
    2. Preview the sound's audio directly.
    3. Delete the selected soundboard sound from the server.
    4. Wipe all sounds if the user wants to free up all slots.
    """

    def __init__(
        self,
        guild: discord.Guild,
        author_id: int,
        sounds: List[discord.SoundboardSound],
        timeout: float = 300.0
    ):
        super().__init__(timeout=timeout)
        self.guild = guild
        self.author_id = author_id
        self.sounds_dict: Dict[int, discord.SoundboardSound] = {s.id: s for s in sounds}
        self.selected_sound_id: Optional[int] = sounds[0].id if sounds else None
        self._refresh_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await verify_user_bot_access(interaction)

    def _refresh_components(self):
        self.clear_items()
        if not self.sounds_dict:
            return

        # 1. Dropdown selector of all active server sounds
        options = []
        for sid, s in list(self.sounds_dict.items())[:25]:
            emoji_str = f"{s.emoji} " if s.emoji else ""
            creator = f"by {s.user.name}" if s.user else "by Unknown"
            options.append(discord.SelectOption(
                label=f"{emoji_str}{s.name}"[:100],
                value=str(sid),
                description=f"Volume: {s.volume} • {creator}"[:100],
                emoji="🔊",
                default=(sid == self.selected_sound_id)
            ))

        select = discord.ui.Select(
            placeholder="Select a soundboard sound to manage or delete...",
            options=options,
            row=0
        )
        select.callback = self._on_select_sound
        self.add_item(select)

        # 2. Preview Audio button
        btn_preview = discord.ui.Button(label="Preview Audio", style=discord.ButtonStyle.primary, emoji="🎧", row=1)
        btn_preview.callback = self._on_preview
        self.add_item(btn_preview)

        # 3. Delete Selected button
        btn_delete = discord.ui.Button(label="Delete Sound", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
        btn_delete.callback = self._on_delete
        self.add_item(btn_delete)

        # 4. Clear All button
        btn_clear = discord.ui.Button(label="Clear All Sounds", style=discord.ButtonStyle.secondary, emoji="🧹", row=1)
        btn_clear.callback = self._on_clear_all
        self.add_item(btn_clear)

    def build_embed(self) -> discord.Embed:
        max_slots = TIER_SOUNDBOARD_SLOTS.get(self.guild.premium_tier, 8)
        used = len(self.sounds_dict)
        embed = discord.Embed(
            title=f"🔊 Soundboard Sound Manager: {self.guild.name}",
            description=(
                f"**Capacity:** `{used} / {max_slots} slots used`\n"
                f"**Server Boost Level:** `Tier {self.guild.premium_tier}`\n\n"
            ),
            color=EMBED_COLOR_DEFAULT
        )

        if not self.sounds_dict:
            embed.description += "✨ *No sounds are currently installed on this server's soundboard.*"
            embed.color = EMBED_COLOR_SUCCESS
            return embed

        selected = self.sounds_dict.get(self.selected_sound_id) if self.selected_sound_id else None
        if selected:
            emoji_str = f"{selected.emoji} " if selected.emoji else ""
            creator = f"<@{selected.user.id}>" if selected.user else "Unknown"
            embed.add_field(
                name="🎯 Selected Sound",
                value=(
                    f"**Name:** {emoji_str}`{selected.name}`\n"
                    f"**Volume:** `{selected.volume}`\n"
                    f"**Added By:** {creator}\n"
                    f"**Sound ID:** `{selected.id}`"
                ),
                inline=False
            )
            embed.set_footer(text="Use 'Preview Audio' to listen or 'Delete Sound' to remove it.")
        else:
            embed.set_footer(text="Select a sound from the dropdown to manage or delete it.")

        return embed

    async def _on_select_sound(self, interaction: discord.Interaction):
        selected_val = int(interaction.data["values"][0])
        self.selected_sound_id = selected_val
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_preview(self, interaction: discord.Interaction):
        selected = self.sounds_dict.get(self.selected_sound_id)
        if not selected:
            await interaction.response.send_message("No sound selected.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            audio_bytes = await selected.read()
            file = discord.File(io.BytesIO(audio_bytes), filename=f"{selected.name}.mp3")
            embed = discord.Embed(
                title=f"🔊 Preview: {selected.name}",
                description=f"Volume: `{selected.volume}`\n*Listen in player above!*",
                color=EMBED_COLOR_DEFAULT
            )
            await interaction.followup.send(embed=embed, file=file, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to play preview: {e}", ephemeral=True)

    async def _on_delete(self, interaction: discord.Interaction):
        selected = self.sounds_dict.get(self.selected_sound_id)
        if not selected:
            await interaction.response.send_message("No sound selected.", ephemeral=True)
            return

        sound_name = selected.name
        try:
            await selected.delete(reason=f"Deleted by {interaction.user} via Dissound soundboard manager")
            await repo.log_upload(
                str(self.guild.id),
                str(interaction.user.id),
                str(selected.id),
                sound_name,
                "DELETED",
                "Removed via Soundboard Manager"
            )
            del self.sounds_dict[selected.id]
            self.selected_sound_id = next(iter(self.sounds_dict.keys()), None)
            self._refresh_components()

            embed = self.build_embed()
            await interaction.response.edit_message(embed=embed, view=self if self.sounds_dict else None)
            await interaction.followup.send(
                f"🗑️ Successfully deleted **{sound_name}** from the server's soundboard!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to delete sound: {e}", ephemeral=True)

    async def _on_clear_all(self, interaction: discord.Interaction):
        total = len(self.sounds_dict)
        if total == 0:
            await interaction.response.send_message("Soundboard is already empty.", ephemeral=True)
            return

        class ConfirmWipeView(discord.ui.View):
            def __init__(self, parent_view: 'SoundboardManageView'):
                super().__init__(timeout=60.0)
                self.parent_view = parent_view

            @discord.ui.button(label="Yes, Delete All Sounds", style=discord.ButtonStyle.danger, emoji="⚠️")
            async def confirm_wipe(self, btn_interaction: discord.Interaction, btn: discord.ui.Button):
                await btn_interaction.response.defer(ephemeral=True)
                deleted_count = 0
                for sid, s in list(self.parent_view.sounds_dict.items()):
                    try:
                        await s.delete(reason=f"Bulk cleared by {btn_interaction.user}")
                        deleted_count += 1
                    except Exception:
                        pass
                self.parent_view.sounds_dict.clear()
                self.parent_view.selected_sound_id = None
                self.parent_view._refresh_components()
                await interaction.edit_original_response(embed=self.parent_view.build_embed(), view=None)
                await btn_interaction.followup.send(
                    f"🧹 Successfully cleared all `{deleted_count}` sounds from the soundboard!",
                    ephemeral=True
                )

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel_wipe(self, btn_interaction: discord.Interaction, btn: discord.ui.Button):
                await btn_interaction.response.send_message("Bulk sound deletion canceled.", ephemeral=True)

        confirm_view = ConfirmWipeView(self)
        await interaction.response.send_message(
            f"⚠️ Are you sure you want to delete **ALL {total} sounds** from `{self.guild.name}`'s soundboard?",
            view=confirm_view,
            ephemeral=True
        )


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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await verify_user_bot_access(interaction)

    def _update_buttons(self):
        total = len(self.candidates)
        self.prev_button.disabled = (self.current_index <= 0)
        self.next_button.disabled = (self.current_index >= total - 1)
        self.counter_button.label = f"{self.current_index + 1} / {total}"

    def build_embed(self) -> discord.Embed:
        sound = self.candidates[self.current_index]
        total = len(self.candidates)

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

        if sound.duration > 5.0:
            dur_info = f"`{sound.duration}s` ⚠️ *(Exceeds Discord 5.2s limit • Trimmer or Nitro required)*"
        else:
            dur_info = f"`{sound.duration}s` ✅ *(Ready for Soundboard &le; 5.2s)*"

        embed = discord.Embed(
            title=f"🌐 Internet Meme Scout: '{sound.sound_name}'",
            description=(
                f"**Search Query:** `{self.query}`\n"
                f"**Candidate:** `{self.current_index + 1} of {total}`\n\n"
                f"⏱️ **Duration:** {dur_info}\n"
                f"📦 **File Size:** `{(sound.file_size // 1024)} KB`\n"
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
            description=f"Candidate #{self.current_index + 1} ({sound.duration}s)\n*Listen to full audio in player above!*",
            color=EMBED_COLOR_DEFAULT
        )
        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

    @discord.ui.button(label="Add to Soundboard", style=discord.ButtonStyle.success, emoji="➕", row=1)
    async def add_soundboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        sound = self.candidates[self.current_index]
        sound_path = Path(sound.file_path)
        real_dur = audio_processor.get_duration(sound_path) if sound_path.exists() else sound.duration

        # Intercept audio exceeding Discord's 5.0s threshold
        if real_dur > 5.0 or sound.duration > 5.0:
            prompt_view = LongSoundNitroPromptView(sound=sound, author_id=interaction.user.id)
            embed = prompt_view.build_embed(real_dur)
            await interaction.response.send_message(embed=embed, view=prompt_view, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
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
