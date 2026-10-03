"""Sign-in helpers for CalcLearners: settings, passwords, and the
Google and Cloudflare Turnstile checks. The routes that use these live in server.py.

Settings come from environment variables or from a `secrets.env` file next to this
one (KEY=value per line, git-ignored). See secrets.env.example for the list.
"""
import json
import os
import re
import secrets
import time
import urllib.parse
import urllib.request
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

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


GOOGLE_CLIENT_ID = setting("GOOGLE_CLIENT_ID")
TURNSTILE_SITE_KEY = setting("TURNSTILE_SITE_KEY")
TURNSTILE_SECRET = setting("TURNSTILE_SECRET_KEY")
ADMIN_USERS = {u.strip().lower() for u in setting("ADMIN_USERS").split(",") if u.strip()}

# ---------- Usernames, passwords ----------
USERNAME_RE = re.compile(r"^[a-z0-9_]{2,20}$")
TOO_COMMON = {
    "password", "password1", "password12", "password123", "passw0rd", "12345678", "123456789",
    "1234567890", "11111111", "00000000", "87654321", "qwertyuiop", "qwerty123", "iloveyou",
    "abcd1234", "abc12345", "letmein1", "welcome1", "football", "baseball", "sunshine",
    "princess", "superman", "calculus", "calclearners", "math1234",
}


def username_problem(username):
    if not USERNAME_RE.match(username):
        return "Usernames are 2 to 20 characters: letters, numbers and _ only."
    return None


def password_problem(password, username=""):
    if len(password) < 8:
        return "Use at least 8 characters for your password."
    if len(password) > 200:
        return "That password is too long (200 characters at most)."
    lowered = password.lower()
    if lowered in TOO_COMMON or lowered == username.lower():
        return "That password is too easy to guess. Try a longer phrase or mix in numbers and symbols."
    return None


hash_password = generate_password_hash        # scrypt with a random salt
check_password = check_password_hash
# Checked against when the account doesn't exist, so a wrong username takes as long
# as a wrong password and can't be told apart by timing.
DUMMY_HASH = generate_password_hash(secrets.token_hex(16))


# ---------- Outside checks ----------
def _post_form(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def turnstile_ok(token, ip):
    """Cloudflare's free bot check. Skipped when no keys are set (local runs)."""
    if not TURNSTILE_SECRET:
        return True
    if not token or len(token) > 2048:
        return False
    try:
        result = _post_form("https://challenges.cloudflare.com/turnstile/v0/siteverify",
                            {"secret": TURNSTILE_SECRET, "response": token, "remoteip": ip})
    except Exception:
        return False
    return bool(result.get("success"))


def google_identity(credential):
    """Check a Google sign-in token. Returns {sub, name} or None."""
    if not GOOGLE_CLIENT_ID or not credential or len(credential) > 4096:
        return None
    url = "https://oauth2.googleapis.com/tokeninfo?" + urllib.parse.urlencode({"id_token": credential})
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            info = json.loads(resp.read().decode())
    except Exception:
        return None
    if (info.get("aud") != GOOGLE_CLIENT_ID
            or info.get("iss") not in ("accounts.google.com", "https://accounts.google.com")
            or int(info.get("exp", 0)) < time.time()):
        return None
    return {"sub": info["sub"], "name": (info.get("given_name") or "")[:40]}
