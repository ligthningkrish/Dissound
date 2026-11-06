"""
Settings and permissions configuration cog for Dissound.
Handles /settings bot_role, /settings clear_role, /settings view, and /permissions.
"""
import discord
from discord import app_commands
from discord.ext import commands

from config import (
    EMBED_COLOR_DEFAULT,
    EMBED_COLOR_SUCCESS,
    EMBED_COLOR_ERROR,
    TIER_SOUNDBOARD_SLOTS
)
from database.repository import Repository
from core.permissions import check_bot_access, is_guild_admin_or_owner
from core.logger import log

repo = Repository()


class SettingsGroup(app_commands.Group):
    """Subcommands under /settings"""
    def __init__(self):
        super().__init__(name="settings", description="Configure server bot access roles and soundboard settings")


class SettingsCog(commands.Cog, name="Settings & Access Control"):
    """Server-level configuration and role-based access control."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    settings_group = SettingsGroup()

    @settings_group.command(name="bot_role", description="Designate a custom role that grants access to use Dissound on this server.")
    @app_commands.describe(role="The role to grant bot access (e.g. @Bot Permissions, @Soundboard Manager)")
    async def set_bot_role(self, interaction: discord.Interaction, role: discord.Role):
        """Set a designated role for bot usage."""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        if not is_guild_admin_or_owner(interaction.user):
            await interaction.response.send_message(
                "❌ Only the **Server Owner** or members with **Administrator** permission can change bot role settings.",
                ephemeral=True
            )
            return

        await repo.set_server_bot_role(str(interaction.guild.id), str(role.id))
        embed = discord.Embed(
            title="✅ Bot Access Role Configured",
            description=(
                f"Members with the {role.mention} role now have full access to Dissound on this server!\n\n"
                f"**Effective Access:**\n"
                f"• Server Owner & Administrators (Always allowed)\n"
                f"• Members with {role.mention}\n"
                f"• Members with **Manage Expressions** permission\n"
                f"• Members with roles named `'Bot Permissions'`, `'Soundboard Manager'`, etc."
            ),
            color=EMBED_COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=embed)

    @settings_group.command(name="clear_role", description="Reset custom bot role to default higher roles.")
    async def clear_bot_role(self, interaction: discord.Interaction):
        """Reset the custom bot role."""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        if not is_guild_admin_or_owner(interaction.user):
            await interaction.response.send_message(
                "❌ Only the **Server Owner** or members with **Administrator** permission can change bot role settings.",
                ephemeral=True
            )
            return

        await repo.set_server_bot_role(str(interaction.guild.id), None)
        embed = discord.Embed(
            title="🔄 Bot Role Reset to Default",
            description=(
                "Custom bot role has been cleared. Dissound access is now restricted to default higher roles:\n"
                "• **Administrator** or **Manage Expressions** permission\n"
                "• Roles named **'Bot Permissions'**, **'Soundboard Manager'**, or **Staff**"
            ),
            color=EMBED_COLOR_DEFAULT
        )
        await interaction.response.send_message(embed=embed)

    @settings_group.command(name="view", description="View current server access role and soundboard configuration.")
    async def view_settings(self, interaction: discord.Interaction):
        """View server settings and access configuration."""
        if not interaction.guild:
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        server = await repo.get_server(str(interaction.guild.id))
        role_mention = "Default Higher Roles (Bot Permissions / Admin)"
        if server and server.bot_role_id:
            role_obj = interaction.guild.get_role(int(server.bot_role_id))
            role_mention = role_obj.mention if role_obj else f"Unknown Role (ID: {server.bot_role_id})"

        try:
            sounds = await interaction.guild.fetch_soundboard_sounds()
        except Exception:
            sounds = interaction.guild.soundboard_sounds

        max_slots = TIER_SOUNDBOARD_SLOTS.get(interaction.guild.premium_tier, 8)
        used = len(sounds)

        embed = discord.Embed(
            title=f"⚙️ Dissound Server Settings: {interaction.guild.name}",
            color=EMBED_COLOR_DEFAULT
        )
        embed.add_field(name="Required Bot Role", value=role_mention, inline=False)
        embed.add_field(name="Soundboard Slots", value=f"`{used} / {max_slots}` slots used", inline=True)
        embed.add_field(name="Boost Level", value=f"Tier {interaction.guild.premium_tier}", inline=True)
        embed.add_field(
            name="Access Policy",
            value="Only members with higher roles (such as Administrator, Manage Expressions, or a role named 'Bot Permissions') can run commands and manage soundboards.",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="permissions", description="Check your permissions and verify if you have access to Dissound.")
    async def my_permissions(self, interaction: discord.Interaction):
        """Check personal access rights."""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Must be used in a Discord server.", ephemeral=True)
            return

        has_access, reason = await check_bot_access(interaction.user)
        embed = discord.Embed(
            title=f"🛡️ Permission Status: {interaction.user.display_name}",
            color=EMBED_COLOR_SUCCESS if has_access else EMBED_COLOR_ERROR
        )
        if has_access:
            embed.description = "✅ **Access Granted**: You have higher roles or bot permissions to use Dissound on this server."
        else:
            embed.description = f"⛔ **Access Denied**: You cannot use Dissound.\n\n{reason}"

        roles_list = [r.name for r in interaction.user.roles if r.name != "@everyone"]
        embed.add_field(
            name="Your Roles",
            value=", ".join(roles_list) if roles_list else "None",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="invite", description="Get an invite link to add Dissound to other Discord servers.")
    async def invite(self, interaction: discord.Interaction):
        """Generates an OAuth2 invite URL with necessary soundboard permissions."""
        client_id = self.bot.user.id if self.bot.user else ""
        perms_int = 414464731136
        invite_url = f"https://discord.com/oauth2/authorize?client_id={client_id}&permissions={perms_int}&scope=bot%20applications.commands"

        embed = discord.Embed(
            title="🤖 Invite Dissound to Your Server",
            description=(
                "Bring the AI Meme Soundboard Scout to your community!\n\n"
                "**Required Bot Permissions Included:**\n"
                "• **Create & Manage Expressions** (Upload and delete Soundboard sounds)\n"
                "• **Send Messages, Embed Links & Attach Files** (Audio player previews & menus)\n"
                "• **Slash Commands (`applications.commands`)**\n\n"
                "Click the button below to add Dissound to any server where you have *Manage Server* or *Admin* permissions."
            ),
            color=EMBED_COLOR_DEFAULT
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite Dissound", style=discord.ButtonStyle.link, url=invite_url, emoji="➕"))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SettingsCog(bot))
