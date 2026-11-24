# TMU Battle Bots Discord bot

A Python bot that connects to Discord and lets server managers send messages as
the bot using `/say`.

## Setup and run

Use Python 3.10 or newer. From the project directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

If `.env` already exists, edit it instead of copying over it. In `.env`, set:

```dotenv
DISCORD_TOKEN=your_bot_token_here
```

Use the **bot token** from your application's **Bot** page in the
[Discord Developer Portal](https://discord.com/developers/applications), not the
application ID, public key, or client secret. Keep the token private; do not paste
it into chat or commit it. `.env` is ignored by Git.

If the bot has not joined your server, use the application's installation link
with the `bot` and `applications.commands` scopes to invite it. In destination
channels, give the bot **View Channel** and **Send Messages** permissions.
No privileged intents are needed; leave Requires OAuth2 Code Grant off.

Start it:

```bash
.venv/bin/python bot.py
```

Wait for `Ready: logged in as ...` to confirm it connected. The process stays
running; press Ctrl+C to stop it. It will only stay online while this process and
the machine running it are active.

## Send a message as the bot

In a server where the bot is installed, type `/say`, enter `message`, and choose
a destination `channel` using Discord's picker. For example:

```text
/say message:Meeting at 6! channel:#announcements
```

The bot posts the supplied text under its own name, then privately confirms with
a link to the sent message. You need **Manage Server** permission to use the
command, plus **View Channel** and **Send Messages** in the destination. The bot
also needs those channel permissions. The destination must be a text channel in
the same server; DMs and threads are not supported by this command.

Messages must contain non-whitespace text and be at most 2,000 characters.
Mentions appear as text/mentions but do not trigger notifications, including
`@everyone`, role mentions, and user mentions.

At startup, `Registered 1 slash command(s).` means Discord accepted the command
registration. Global commands can take time to appear in Discord; try reopening
Discord if necessary. If `/say` is missing, check your Manage Server permission,
the channel's **Use Application Commands** permission, and the app's integration
settings. If needed, reauthorize the app with `bot` and `applications.commands`.

## How the code works

- `load_dotenv(...)` reads the local `.env` file. An existing environment variable
  takes precedence, allowing the same code to run on a host with secret settings.
- `BattleBotsClient` extends `discord.Client` with a slash command tree. Intents describe which
  events Discord should send; the defaults do not request privileged intents.
  If `https_proxy` or `HTTPS_PROXY` is configured by your host, the client uses
  it for both HTTPS requests and the Discord gateway WebSocket connection.
- `setup_hook()` registers the slash commands with Discord once at startup.
- `on_ready()` runs after the client is ready and may run again after reconnecting.
- The `/say` decorators define its inputs, server-only use, and Manage Server
  requirement. Its callback checks destination permissions, defers the private
  response, sends the message, and privately confirms success or reports errors.
- `client.run(token)` logs in and manages the asynchronous connection until stopped.
- The `if __name__ == "__main__"` guard starts the bot when run directly, while
  allowing other code to import the file without starting a connection.

## Updating the server

Code changes made in Codex are checked, committed, and pushed to `main`. Run the
bot on your own computer or server to test its connection to Discord.

After the first setup, stop the running bot with Ctrl+C, then run these commands
from the project directory on a Linux/macOS server:

```bash
git pull --ff-only origin main
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python bot.py
```

`git pull` downloads the new code; `--ff-only` stops if local and remote commits
have diverged so you can resolve that explicitly. Installing requirements picks
up dependency changes. Starting the program again loads the updated code.
The server's `.env` stays local and is not replaced by a pull. Create it on the
server during the first setup, since Git does not transfer it.

## Debugging startup

- **Set DISCORD_TOKEN:** `.env` is missing the token or its value is empty.
- **Discord rejected DISCORD_TOKEN:** check or reset the bot token in the portal,
  update `.env`, and restart the process.
- **ModuleNotFoundError:** install requirements and run with `.venv/bin/python`.
- **Ready prints, but the bot is absent from your server:** confirm the application
  was invited to that server. Login alone does not add a bot to a server.
- Connection errors appear in the terminal; check network access to Discord.
  Restricted cloud hosts must allow `discord.com` and `gateway.discord.gg`.
  A proxy error such as `CONNECT ... 403` can indicate a network policy denial
  before Discord receives the login request.

## Local checks

```bash
.venv/bin/python -m unittest discover -s tests -v
```

These tests use simulated Discord objects; they do not send real messages or need
a token. Test `/say` in Discord after restarting the bot to verify the complete
flow with your server's permissions.
