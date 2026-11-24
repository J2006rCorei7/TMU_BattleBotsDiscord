"""Exercise relay behavior without connecting to Discord or sending messages."""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord
from discord import app_commands

from bot import say, say_error


class SayTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.guild = SimpleNamespace(id=123, me=object())
        self.interaction = SimpleNamespace(
            guild=self.guild,
            user=object(),
            permissions=discord.Permissions(manage_guild=True),
            response=SimpleNamespace(
                send_message=AsyncMock(), defer=AsyncMock(), is_done=Mock(return_value=False)
            ),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        self.channel = SimpleNamespace(
            id=456,
            guild=self.guild,
            mention="<#456>",
            permissions_for=Mock(return_value=discord.Permissions(view_channel=True, send_messages=True)),
            send=AsyncMock(return_value=SimpleNamespace(jump_url="https://discord.com/channels/123/456/789")),
        )

    async def test_success_sends_once_with_no_pings_and_private_confirmation(self) -> None:
        await say.callback(self.interaction, "Hello @everyone!", self.channel)
        self.channel.send.assert_awaited_once()
        args, kwargs = self.channel.send.call_args
        self.assertEqual(args, ("Hello @everyone!",))
        self.assertEqual(kwargs["allowed_mentions"].to_dict(), {"parse": []})
        self.interaction.response.defer.assert_awaited_once_with(ephemeral=True, thinking=True)
        self.interaction.followup.send.assert_awaited_once_with(
            "Sent to <#456>: https://discord.com/channels/123/456/789", ephemeral=True
        )

    async def test_invalid_messages_never_send(self) -> None:
        for message in ("", " \n\t", "x" * 2001):
            with self.subTest(message_length=len(message)):
                await say.callback(self.interaction, message, self.channel)
        self.channel.send.assert_not_awaited()
        self.assertEqual(self.interaction.response.send_message.await_count, 3)

    async def test_2000_character_message_is_allowed(self) -> None:
        await say.callback(self.interaction, "x" * 2000, self.channel)
        self.channel.send.assert_awaited_once()

    async def test_other_server_destination_never_sends(self) -> None:
        self.channel.guild = SimpleNamespace(id=999)
        await say.callback(self.interaction, "Hello", self.channel)
        self.channel.send.assert_not_awaited()
        self.interaction.response.send_message.assert_awaited_once_with(
            "Choose a text channel in this server.", ephemeral=True
        )

    async def test_dm_never_sends(self) -> None:
        self.interaction.guild = None
        await say.callback(self.interaction, "Hello", self.channel)
        self.channel.send.assert_not_awaited()

    async def test_destination_permissions_required_for_both_sender_and_bot(self) -> None:
        allowed = discord.Permissions(view_channel=True, send_messages=True)
        for sender in (True, False):
            for missing in ("view_channel", "send_messages"):
                with self.subTest(sender=sender, missing=missing):
                    denied = discord.Permissions(view_channel=True, send_messages=True)
                    setattr(denied, missing, False)
                    self.channel.permissions_for.side_effect = [denied] if sender else [allowed, denied]
                    await say.callback(self.interaction, "Hello", self.channel)
        self.channel.send.assert_not_awaited()
        self.assertEqual(self.interaction.response.send_message.await_count, 4)

    async def test_manage_server_is_enforced_at_runtime(self) -> None:
        self.interaction.permissions = discord.Permissions.none()
        with self.assertRaises(app_commands.MissingPermissions):
            for check in say.checks:
                check(self.interaction)
        self.channel.send.assert_not_awaited()
        self.interaction.permissions = discord.Permissions(manage_guild=True)
        for check in say.checks:
            self.assertTrue(check(self.interaction))

    async def test_forbidden_after_permission_check_reports_failure_privately(self) -> None:
        self.channel.send.side_effect = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "Denied")
        await say.callback(self.interaction, "Hello", self.channel)
        self.channel.send.assert_awaited_once()
        self.interaction.followup.send.assert_awaited_once_with(
            "Discord denied access to that channel. Check my permissions.", ephemeral=True
        )

    async def test_http_error_reports_uncertain_send_without_retry(self) -> None:
        self.channel.send.side_effect = discord.HTTPException(SimpleNamespace(status=500, reason="Server Error"), "Error")
        with self.assertLogs("bot", level="WARNING"):
            await say.callback(self.interaction, "Hello", self.channel)
        self.channel.send.assert_awaited_once()
        self.interaction.followup.send.assert_awaited_once_with(
            "Discord could not confirm the send. Check the channel before trying again.", ephemeral=True
        )

    async def test_permission_error_gets_private_explanation(self) -> None:
        await say_error(self.interaction, app_commands.MissingPermissions(["manage_guild"]))
        self.interaction.response.send_message.assert_awaited_once_with(
            "You need Manage Server permission to use /say.", ephemeral=True
        )


if __name__ == "__main__":
    unittest.main()
