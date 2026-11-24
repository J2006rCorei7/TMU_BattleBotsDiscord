"""Connect the TMU Battle Bots bot to Discord."""

import os
from pathlib import Path

import discord
from dotenv import load_dotenv


def main() -> None:
    # Resolve .env beside this file, even when launched from another directory.
    load_dotenv(Path(__file__).with_name(".env"))
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set DISCORD_TOKEN in .env before starting the bot.")

    # Default intents do not request privileged access, such as message content.
    # Some cloud environments require an HTTPS proxy for outbound connections.
    proxy = os.getenv("https_proxy") or os.getenv("HTTPS_PROXY")
    client = discord.Client(intents=discord.Intents.default(), proxy=proxy)

    @client.event
    async def on_ready() -> None:
        # Discord calls this after connecting; it can also fire after reconnects.
        print(f"Ready: logged in as {client.user} (ID: {client.user.id})", flush=True)

    # run() manages the connection and keeps the process running until stopped.
    try:
        client.run(token)
    except discord.LoginFailure:
        raise SystemExit("Discord rejected DISCORD_TOKEN. Check your bot token in .env.") from None


if __name__ == "__main__":
    main()
