"""
History and help commands cog for Dissound.
"""
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from config import EMBED_COLOR_DEFAULT
from database.repository import Repository

repo = Repository()

class HistoryCog(commands.Cog, name="History & Help"):
    """Server upload logs and bot help."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="history", description="View soundboard upload history and audit log for this server.")
    @app_commands.describe(limit="Number of log entries to retrieve (default 10, max 25)")
    async def history(self, interaction: discord.Interaction, limit: Optional[int] = 10):
        """View upload history for this guild."""
        if not interaction.guild:
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        clamped_limit = max(1, min(25, limit or 10))
        logs = await repo.get_server_history(str(interaction.guild.id), limit=clamped_limit)

        embed = discord.Embed(
            title=f"📜 Soundboard Upload History: {interaction.guild.name}",
            description=f"Showing the last {len(logs)} upload attempts:",
            color=EMBED_COLOR_DEFAULT
        )

        if not logs:
            embed.description = "No soundboard upload activity recorded yet for this server."
            await interaction.response.send_message(embed=embed)
            return

        for item in logs:
            icon = "✅" if item.upload_status == "SUCCESS" else "❌"
            dt_str = item.timestamp.strftime("%Y-%m-%d %H:%M:%S") if hasattr(item.timestamp, "strftime") else str(item.timestamp)
            reason = f" - *Error: {item.error_message}*" if item.error_message else ""
            embed.add_field(
                name=f"{icon} {item.sound_name}",
                value=f"**Status:** `{item.upload_status}`\n**Requested by:** <@{item.user_id}>\n**Time:** `{dt_str}`{reason}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Learn how to use Dissound to manage your server Soundboard.")
    async def help_command(self, interaction: discord.Interaction):
        """Displays help guide and all available commands."""
        embed = discord.Embed(
            title="🔊 Welcome to Dissound (MemeSound Bot)",
            description=(
                "Dissound eliminates the hassle of finding, downloading, converting, "
                "and manually uploading meme sounds to your Discord Server Soundboard!\n\n"
                "**Quick Workflow:**\n"
                "1️⃣ Type `/search <sound>` or `/browse` to discover funny sounds.\n"
                "2️⃣ Click **Preview** to listen to the sound in chat.\n"
                "3️⃣ Click **Add to Soundboard** to install it directly to your server!"
            ),
            color=EMBED_COLOR_DEFAULT
        )

        embed.add_field(
            name="🔍 Sound Discovery",
            value=(
                "`/search <query>` - Search library by name, category, or tags with live autocomplete\n"
                "`/browse [category]` - Browse sounds organized by categories\n"
                "`/categories` - View all available sound categories and counts\n"
                "`/trending` - See the most popular soundboard additions\n"
                "`/recent` - View latest additions to the catalog"
            ),
            inline=False
        )

        embed.add_field(
            name="🔊 Previews & Direct Adding",
            value=(
                "`/preview <sound>` - Listen to any sound with an 'Add to Soundboard' button\n"
                "`/add <sound> [custom_name] [volume]` - Directly add a catalog sound to your server"
            ),
            inline=False
        )

        embed.add_field(
            name="⚙️ Server Soundboard Management",
            value=(
                "`/soundboard list` - View active soundboard sounds on this server\n"
                "`/soundboard status` - Check soundboard slots, capacity, and server boost tier\n"
                "`/soundboard delete <name>` - Delete a sound from this server's soundboard\n"
                "`/upload <file> [name]` - Auto-trim and add custom audio file to your server\n"
                "`/history` - View upload history and audit log"
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ Required Permissions",
            value="To add sounds, users and the bot need the **Create Expressions** permission on the server.",
            inline=False
        )

        embed.set_footer(text="Dissound • Built for everyday Discord voice fun")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HistoryCog(bot))
