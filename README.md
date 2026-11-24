# TMU Battle Bots Discord bot

A minimal Python bot: it connects to Discord and prints its identity when ready.
It has no commands or message handlers yet.

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
with the `bot` scope to invite it. This empty bot needs no extra permissions or
privileged intents.

Start it:

```bash
.venv/bin/python bot.py
```

Wait for `Ready: logged in as ...` to confirm it connected. The process stays
running; press Ctrl+C to stop it. It will only stay online while this process and
the machine running it are active.

## How the code works

- `load_dotenv(...)` reads the local `.env` file. An existing environment variable
  takes precedence, allowing the same code to run on a host with secret settings.
- `discord.Client(...)` creates the connection client. Intents describe which
  events Discord should send; the defaults do not request privileged intents.
  If `https_proxy` or `HTTPS_PROXY` is configured by your host, the client uses
  it for both HTTPS requests and the Discord gateway WebSocket connection.
- `@client.event` registers `on_ready()` as a callback. Discord invokes this async
  function after the client is ready. It may be invoked again after reconnecting.
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
