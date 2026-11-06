"""
Core Bot class for Dissound (MemeSound Bot).
"""
import discord
from discord.ext import commands
from discord import app_commands

from config import BOT_PREFIX, DEV_GUILD_ID
from core.logger import log
from core.permissions import check_bot_access
from database.db import init_db
from database.repository import Repository
from assets.seed_data import seed_database

INITIAL_EXTENSIONS = [
    "cogs.discovery",
    "cogs.preview",
    "cogs.soundboard",
    "cogs.history",
    "cogs.settings",
]

class DissoundBot(commands.Bot):
    """Dissound Discord Bot with slash command synchronization, access control, and database hooks."""

    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            help_command=None
        )
        self.repo = Repository()

    async def global_bot_access_check(self, interaction: discord.Interaction) -> bool:
        """Global interaction check ensuring user has higher roles or bot permissions."""
        # All commands must be run within a guild
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Dissound commands can only be used inside a Discord server.",
                    ephemeral=True
                )
            return False

        allowed, reason = await check_bot_access(interaction.user)
        if not allowed:
            embed = discord.Embed(
                title="⛔ Higher Roles Required",
                description=reason,
                color=discord.Color.red()
            )
            embed.set_footer(text="Ask a server administrator to grant you the 'Bot Permissions' role.")
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return False

        return True

    async def setup_hook(self) -> None:
        """Called automatically during bot initialization."""
        # 1. Wire global tree handlers
        self.tree.interaction_check = self.global_bot_access_check
        self.tree.on_error = self.on_app_command_error

        log.info("Running pre-flight checks and initializing database...")
        await init_db()
        await seed_database()

        # Load extension cogs
        for ext in INITIAL_EXTENSIONS:
            try:
                await self.load_extension(ext)
                log.info(f"Loaded extension: {ext}")
            except Exception as e:
                log.error(f"Failed to load extension {ext}: {e}", exc_info=True)

        # Sync application commands
        # 1. Global sync so any server the bot joins has access to all slash commands
        synced = await self.tree.sync()
        log.info(f"🌐 Synced {len(synced)} slash commands globally across Discord.")

        # 2. Instant sync to dev guild if configured
        if DEV_GUILD_ID:
            try:
                guild_obj = discord.Object(id=DEV_GUILD_ID)
                self.tree.copy_global_to(guild=guild_obj)
                synced_dev = await self.tree.sync(guild=guild_obj)
                log.info(f"⚡ Synced {len(synced_dev)} slash commands instantly to DEV_GUILD_ID: {DEV_GUILD_ID}")
            except Exception as e:
                log.warning(f"Could not sync to DEV_GUILD_ID: {e}")

    async def on_ready(self) -> None:
        """Event triggered when Discord connection is established."""
        log.info(f"Bot connected as: {self.user} (ID: {self.user.id})")
        log.info(f"Serving {len(self.guilds)} Discord guilds.")

        # Set rich presence activity
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="/soundboard • /find • /settings"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Store guild details in database and sync slash commands instantly to the new server."""
        log.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        await self.repo.upsert_server(str(guild.id), guild.name)
        try:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info(f"⚡ Instantly synced {len(synced)} slash commands to newly joined guild: {guild.name}")
        except Exception as e:
            log.warning(f"Could not instant sync to {guild.name}: {e}")

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """Global error handler for slash commands."""
        log.error(f"Command '{interaction.command.name if interaction.command else 'Unknown'}' error: {error}", exc_info=True)

        if isinstance(error, app_commands.CheckFailure):
            # Already handled in interaction_check
            if not interaction.response.is_done():
                await interaction.response.send_message("⛔ You do not have permission to use this command.", ephemeral=True)
            return

        if isinstance(error, app_commands.MissingPermissions):
            missing = ", ".join(error.missing_permissions)
            msg = f"❌ You are missing required permissions: `{missing}`"
        elif isinstance(error, app_commands.BotMissingPermissions):
            missing = ", ".join(error.missing_permissions)
            msg = f"❌ The bot is missing required permissions on this server: `{missing}`"
        elif isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ Command is on cooldown. Try again in {error.retry_after:.1f}s."
        else:
            msg = f"⚠️ An error occurred while executing this command: {str(error)}"

        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception as e:
            log.warning(f"Failed to deliver command error response: {e}")
