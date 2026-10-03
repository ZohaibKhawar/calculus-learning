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
# From when the site had accounts. Read once, on the first start after sign-in was removed,
# to keep those people's browsers as moderators.
ADMIN_USERS = {u.strip().lower() for u in setting("ADMIN_USERS").split(",") if u.strip()}
