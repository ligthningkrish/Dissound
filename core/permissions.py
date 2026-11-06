"""
Role and permission verification for Dissound.
Ensures only members with higher roles or bot permissions can use Dissound.
"""
import discord
from typing import Tuple, Optional
from database.repository import Repository
from core.logger import log

repo = Repository()

# Known role names representing elevated bot/soundboard privileges
ELEVATED_ROLE_KEYWORDS = {
    "bot permissions",
    "bot permission",
    "bot perms",
    "bot perm",
    "bot manager",
    "bot admin",
    "bot master",
    "soundboard manager",
    "soundboard mod",
    "soundboard admin",
    "soundboard",
    "mod",
    "moderator",
    "admin",
    "administrator",
    "staff",
    "dj",
}


def is_guild_admin_or_owner(member: discord.Member) -> bool:
    """Checks if member is server owner or has Administrator permission."""
    if not isinstance(member, discord.Member) or not member.guild:
        return False
    if member.id == member.guild.owner_id:
        return True
    return member.guild_permissions.administrator


async def check_bot_access(member: discord.Member) -> Tuple[bool, Optional[str]]:
    """
    Checks if a guild member has elevated privileges to use Dissound:
    1. Server Owner (always allowed)
    2. Administrator permission
    3. Manage Server (manage_guild) permission
    4. Manage Expressions / Create Expressions permission
    5. Member has the custom role configured via /settings role in SQLite
    6. Member has a role matching higher bot roles (e.g., 'Bot Permissions', 'Soundboard Manager')

    Returns (is_allowed, error_message).
    """
    if not isinstance(member, discord.Member):
        return False, "Dissound can only be used by server members inside a Discord server."

    guild = member.guild
    if not guild:
        return False, "Must be used inside a Discord server."

    # 1. Server Owner
    if member.id == guild.owner_id:
        return True, None

    # 2. Key Guild Permissions
    perms = member.guild_permissions
    if perms.administrator:
        return True, None
    if getattr(perms, "manage_guild", False):
        return True, None
    if getattr(perms, "manage_guild_expressions", False) or getattr(perms, "manage_expressions", False):
        return True, None
    if getattr(perms, "create_guild_expressions", False) or getattr(perms, "create_expressions", False):
        return True, None

    # 3. Custom Server Configured Role
    try:
        server_record = await repo.get_server(str(guild.id))
        if server_record and server_record.bot_role_id:
            target_role_id = int(server_record.bot_role_id)
            if any(role.id == target_role_id for role in member.roles):
                return True, None
    except Exception as e:
        log.warning(f"Error checking server bot_role_id: {e}")

    # 4. Elevated Role Names (e.g. 'Bot Permissions', 'Soundboard Manager', 'Mod', etc.)
    for role in member.roles:
        r_name = getattr(role, "name", "")
        if not r_name:
            continue
        r_name_clean = r_name.strip().lower()
        if r_name_clean in ELEVATED_ROLE_KEYWORDS:
            return True, None
        if "bot perm" in r_name_clean or "soundboard" in r_name_clean:
            return True, None

    denial_msg = (
        "⛔ **Access Restricted — Higher Role Required**\n\n"
        "You do not have the required permissions or roles to use Dissound.\n\n"
        "**Allowed Users:**\n"
        "• Members with **Administrator** or **Manage Expressions** permission\n"
        "• Members with a role named **'Bot Permissions'**, **'Soundboard Manager'**, or **Staff**\n"
        "• Or the custom role configured by the server administrator (`/settings bot_role`)\n\n"
        "*Please ask a server administrator or moderator for access.*"
    )
    return False, denial_msg
