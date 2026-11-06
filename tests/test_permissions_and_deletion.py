import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import discord

from core.permissions import check_bot_access, is_guild_admin_or_owner
from database.db import init_db
from database.repository import Repository
from ui.views import SoundboardManageView, SoundboardDeleteConfirmView


class TestPermissionsAndDeletion(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()
        self.repo = Repository()

    def _create_mock_member(self, user_id=123, is_owner=False, is_admin=False, can_expressions=False, role_names=None, role_ids=None):
        member = MagicMock(spec=discord.Member)
        member.id = user_id
        member.display_name = f"User_{user_id}"
        member.name = f"user_{user_id}"

        guild = MagicMock(spec=discord.Guild)
        guild.id = 999
        guild.name = "Test Guild"
        guild.owner_id = user_id if is_owner else 888
        guild.premium_tier = 0

        member.guild = guild

        perms = MagicMock()
        perms.administrator = is_admin
        perms.manage_guild = is_admin
        perms.manage_guild_expressions = can_expressions
        perms.create_guild_expressions = can_expressions
        perms.manage_expressions = can_expressions
        perms.create_expressions = can_expressions
        member.guild_permissions = perms

        roles = []
        if role_names:
            for idx, r_name in enumerate(role_names):
                rid = role_ids[idx] if role_ids and idx < len(role_ids) else 1000 + idx
                r = MagicMock(spec=discord.Role)
                r.id = rid
                r.name = r_name
                roles.append(r)
        member.roles = roles

        return member

    async def test_owner_always_has_access(self):
        owner = self._create_mock_member(user_id=888, is_owner=True)
        allowed, reason = await check_bot_access(owner)
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    async def test_admin_has_access(self):
        admin = self._create_mock_member(user_id=101, is_admin=True)
        allowed, reason = await check_bot_access(admin)
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    async def test_manage_expressions_has_access(self):
        mod = self._create_mock_member(user_id=102, can_expressions=True)
        allowed, reason = await check_bot_access(mod)
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    async def test_bot_permissions_role_has_access(self):
        member = self._create_mock_member(user_id=103, role_names=["Bot Permissions"])
        allowed, reason = await check_bot_access(member)
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    async def test_soundboard_manager_role_has_access(self):
        member = self._create_mock_member(user_id=104, role_names=["Soundboard Manager"])
        allowed, reason = await check_bot_access(member)
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    async def test_regular_member_denied(self):
        regular = self._create_mock_member(user_id=105, role_names=["Member", "Gamer"])
        allowed, reason = await check_bot_access(regular)
        self.assertFalse(allowed)
        self.assertIsNotNone(reason)
        self.assertIn("Higher Role Required", reason)

    async def test_custom_server_role_configuration(self):
        guild_id = "999"
        custom_role_id = "5555"
        await self.repo.set_server_bot_role(guild_id, custom_role_id)

        # Member with custom role 5555
        member_with_role = self._create_mock_member(
            user_id=106,
            role_names=["Custom VIP Bot Role"],
            role_ids=[5555]
        )
        allowed, _ = await check_bot_access(member_with_role)
        self.assertTrue(allowed)

        # Member without custom role 5555
        member_without_role = self._create_mock_member(
            user_id=107,
            role_names=["Other Role"],
            role_ids=[9999]
        )
        allowed, _ = await check_bot_access(member_without_role)
        self.assertFalse(allowed)

    async def test_soundboard_manage_view_structure(self):
        guild = MagicMock(spec=discord.Guild)
        guild.name = "Test Guild"
        guild.premium_tier = 1

        mock_sound1 = MagicMock(spec=discord.SoundboardSound)
        mock_sound1.id = 111
        mock_sound1.name = "Vine Boom"
        mock_sound1.emoji = "💥"
        mock_sound1.volume = 1.0
        mock_sound1.user = MagicMock()
        mock_sound1.user.name = "Admin"
        mock_sound1.user.id = 12345
        mock_sound1.delete = AsyncMock()

        mock_sound2 = MagicMock(spec=discord.SoundboardSound)
        mock_sound2.id = 222
        mock_sound2.name = "Airhorn"
        mock_sound2.emoji = "📢"
        mock_sound2.volume = 0.8
        mock_sound2.user = None
        mock_sound2.delete = AsyncMock()

        view = SoundboardManageView(guild=guild, author_id=123, sounds=[mock_sound1, mock_sound2])
        self.assertEqual(len(view.sounds_dict), 2)
        self.assertEqual(view.selected_sound_id, 111)

        embed = view.build_embed()
        self.assertIn("Soundboard Sound Manager", embed.title)
        self.assertIn("Vine Boom", embed.fields[0].value)

        # Test delete logic
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.user = MagicMock()
        interaction.user.id = 123
        interaction.response.edit_message = AsyncMock()
        interaction.followup.send = AsyncMock()

        await view._on_delete(interaction)
        mock_sound1.delete.assert_awaited_once()
        self.assertEqual(len(view.sounds_dict), 1)
        self.assertEqual(view.selected_sound_id, 222)


if __name__ == "__main__":
    unittest.main()
