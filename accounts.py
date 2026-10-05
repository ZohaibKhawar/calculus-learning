"""Sign-in helpers for CalcLearners: the rules for usernames and passwords, password
hashing, and recovery codes. The routes that use these live in server.py.

Accounts are optional and hold no email address, so there is nowhere to send a reset link.
A forgotten password is reset with a recovery code instead, shown once and kept as a hash.
"""
import re
import secrets

from werkzeug.security import check_password_hash, generate_password_hash

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,20}$")
PASSWORD_MAX = 200
TOO_COMMON = {
    "password", "password1", "password12", "password123", "passw0rd", "12345678", "123456789",
    "1234567890", "11111111", "00000000", "87654321", "qwertyuiop", "qwerty123", "iloveyou",
    "abcd1234", "abc12345", "letmein1", "welcome1", "football", "baseball", "sunshine",
    "princess", "superman", "calculus", "calclearners", "math1234",
}


def username_problem(username):
    if not USERNAME_RE.match(username):
        return "Usernames are 3 to 20 characters: letters, numbers and _ only."
    return None


def password_problem(password, username=""):
    if len(password) < 8:
        return "Use at least 8 characters for your password."
    if len(password) > PASSWORD_MAX:
        return f"That password is too long ({PASSWORD_MAX} characters at most)."
    lowered = password.lower()
    if lowered in TOO_COMMON or lowered == username.lower():
        return "That password is too easy to guess. Try a longer phrase or mix in numbers and symbols."
    return None


hash_password = generate_password_hash        # scrypt with a random salt
# Checked against when the account doesn't exist, so a wrong username takes as long
# as a wrong password and can't be told apart by timing.
DUMMY_HASH = generate_password_hash(secrets.token_hex(16))


def check_password(stored_hash, password):
    """True when the password matches. With no stored hash (an unknown username) it
    does the same work and answers False."""
    if len(password) > PASSWORD_MAX:
        password = ""
    ok = check_password_hash(stored_hash or DUMMY_HASH, password)
    return bool(stored_hash) and ok


# ---------- Recovery codes ----------
# 20 characters from an alphabet with no look-alikes (no I, L, O, 0 or 1), written in four
# groups of five. That is about 99 bits, far too many to guess.
RECOVERY_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
RECOVERY_LENGTH = 20


def new_recovery_code():
    code = "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(RECOVERY_LENGTH))
    return "-".join(code[i:i + 5] for i in range(0, RECOVERY_LENGTH, 5))


def clean_recovery_code(typed):
    """A code as typed, without its dashes, spaces or lower case."""
    return re.sub(r"[^A-Z0-9]", "", typed.upper())[:2 * RECOVERY_LENGTH]


def hash_recovery_code(code):
    return generate_password_hash(clean_recovery_code(code))


def check_recovery_code(stored_hash, typed):
    """Like check_password: the same work, and False, when there is no code to check against."""
    return check_password(stored_hash, clean_recovery_code(typed))
