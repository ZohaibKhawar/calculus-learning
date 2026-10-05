"""Settings for CalcLearners.

They come from environment variables or from a `secrets.env` file next to this
one (KEY=value per line, git-ignored). See secrets.env.example for the list.
"""
import os
from pathlib import Path

BASE = Path(__file__).parent
SETTINGS_FILE = BASE / "secrets.env"


def _read_settings_file():
    values = {}
    if SETTINGS_FILE.exists():
        for line in SETTINGS_FILE.read_text(encoding="utf8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("\"'")
    return values


_FILE = _read_settings_file()


def setting(name, default=""):
    return os.environ.get(name) or _FILE.get(name) or default


# Passcode that turns a browser into a forum moderator at #/admin. Switched off when it
# is missing or too short to be safe.
ADMIN_KEY = setting("ADMIN_KEY") if len(setting("ADMIN_KEY")) >= 12 else ""
# From the site's first kind of accounts (before October 2026). Read once, on the first start
# after that sign-in was removed, to keep those people's browsers as moderators.
ADMIN_USERS = {u.strip().lower() for u in setting("ADMIN_USERS").split(",") if u.strip()}
# The code Google Search Console gives ("HTML tag" method) to prove the site is yours.
# Put on the home page when set.
GOOGLE_SITE_VERIFICATION = setting("GOOGLE_SITE_VERIFICATION")
# Anthropic API key. Turns on CalcBot's AI answers and the forum's AI check (see ai.py);
# without it both fall back to built-in rules. Every message costs a little, so set a
# spend limit in the Anthropic Console.
ANTHROPIC_API_KEY = setting("ANTHROPIC_API_KEY")
