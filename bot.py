"""Connect to Discord and let server managers relay messages with /say."""

import logging
import os
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


@app_commands.command(name="say", description="Send a message as the bot to a server text channel.")
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(message="The message to send (up to 2,000 characters).", channel="Where to send it.")
async def say(interaction: discord.Interaction, message: str, channel: discord.TextChannel) -> None:
    # default_permissions controls command visibility; the check above enforces
    # authorization at runtime, even if a server customizes command permissions.
    if interaction.guild is None or channel.guild.id != interaction.guild.id:
        await interaction.response.send_message("Choose a text channel in this server.", ephemeral=True)
        return

    if not message.strip() or len(message) > 2000:
        await interaction.response.send_message("Use a non-empty message of at most 2,000 characters.", ephemeral=True)
        return

    user_permissions = channel.permissions_for(interaction.user)
    if not (user_permissions.view_channel and user_permissions.send_messages):
        await interaction.response.send_message("You need View Channel and Send Messages in that channel.", ephemeral=True)
        return

    bot_permissions = channel.permissions_for(interaction.guild.me)
    if not (bot_permissions.view_channel and bot_permissions.send_messages):
        await interaction.response.send_message("I need View Channel and Send Messages in that channel.", ephemeral=True)
        return

    # Acknowledge promptly: Discord requires an initial response within seconds.
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        sent = await channel.send(message, allowed_mentions=discord.AllowedMentions.none())
    except discord.Forbidden:
        await interaction.followup.send("Discord denied access to that channel. Check my permissions.", ephemeral=True)
    except discord.HTTPException:
        logger.warning("Discord rejected a /say send to channel %s", channel.id, exc_info=True)
        await interaction.followup.send("Discord could not confirm the send. Check the channel before trying again.", ephemeral=True)
    else:
        await interaction.followup.send(f"Sent to {channel.mention}: {sent.jump_url}", ephemeral=True)


@say.error
async def say_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.NoPrivateMessage):
        message = "Use /say inside a server."
    elif isinstance(error, app_commands.MissingPermissions):
        message = "You need Manage Server permission to use /say."
    else:
        logger.error("Unexpected /say error", exc_info=(type(error), error, error.__traceback__))
        message = "Something went wrong. Check the bot's terminal logs for details."

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


class BattleBotsClient(discord.Client):
    def __init__(self, proxy: str | None = None) -> None:
        # Default intents do not request privileged access, such as message content.
        super().__init__(intents=discord.Intents.default(), proxy=proxy)
        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(say)

    async def setup_hook(self) -> None:
        # Sync once at startup, rather than every time the bot reconnects.
        commands = await self.tree.sync()
        print(f"Registered {len(commands)} slash command(s).", flush=True)

    async def on_ready(self) -> None:
        print(f"Ready: logged in as {self.user} (ID: {self.user.id})", flush=True)


def main() -> None:
    # Resolve .env beside this file, even when launched from another directory.
    load_dotenv(Path(__file__).with_name(".env"))
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set DISCORD_TOKEN in .env before starting the bot.")

    # Some cloud environments require an HTTPS proxy for outbound connections.
    proxy = os.getenv("https_proxy") or os.getenv("HTTPS_PROXY")
    client = BattleBotsClient(proxy=proxy)

    # run() manages the connection and keeps the process running until stopped.
    try:
        client.run(token)
    except discord.LoginFailure:
        raise SystemExit("Discord rejected DISCORD_TOKEN. Check your bot token in .env.") from None


if __name__ == "__main__":
    main()
