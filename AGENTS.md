# Working agreement

- Explain changes and relevant debugging steps so the user can understand and
  maintain the bot.
- The bot runs on the user's physical server. Do local checks here; the user
  tests the Discord connection on their server.
- After completing each requested code update, run appropriate checks, commit
  the changes, and push to `origin/main` so the user can pull and test. The user
  has authorized this workflow; no separate push confirmation is needed.
- Use normal pushes. Never force-push or commit `.env`, bot tokens, or `.venv`.
