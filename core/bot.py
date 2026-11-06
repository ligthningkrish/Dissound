"""
Core Bot class for Dissound (MemeSound Bot).
"""
import discord
from discord.ext import commands
from discord import app_commands

from config import BOT_PREFIX, DEV_GUILD_ID
from core.logger import log
from database.db import init_db
from database.repository import Repository
from assets.seed_data import seed_database

INITIAL_EXTENSIONS = [
    "cogs.discovery",
    "cogs.preview",
    "cogs.soundboard",
    "cogs.history",
]

class DissoundBot(commands.Bot):
    """Dissound Discord Bot with slash command synchronization and database hooks."""

    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            help_command=None
        )
        self.repo = Repository()

    async def setup_hook(self) -> None:
        """Called automatically during bot initialization."""
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
        if DEV_GUILD_ID:
            guild_obj = discord.Object(id=DEV_GUILD_ID)
            self.tree.copy_global_to(guild=guild_obj)
            synced = await self.tree.sync(guild=guild_obj)
            log.info(f"⚡ Synced {len(synced)} slash commands instantly to DEV_GUILD_ID: {DEV_GUILD_ID}")
        else:
            synced = await self.tree.sync()
            log.info(f"🌐 Synced {len(synced)} slash commands globally across Discord.")

    async def on_ready(self) -> None:
        """Event triggered when Discord connection is established."""
        log.info(f"Bot connected as: {self.user} (ID: {self.user.id})")
        log.info(f"Serving {len(self.guilds)} Discord guilds.")

        # Set rich presence activity
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="/search • /browse • /help"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Store guild details in database when joined."""
        log.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        await self.repo.upsert_server(str(guild.id), guild.name)

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """Global error handler for slash commands."""
        log.error(f"Command '{interaction.command.name if interaction.command else 'Unknown'}' error: {error}")

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

        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
