"""CalcLearners backend: a small Flask + SQLite server.

Run it:
    pip install -r requirements.txt
    python server.py
Then open http://localhost:5000

There are no accounts. The server gives each browser a random ID the first time
it visits, kept in a signed, HttpOnly cookie, so progress, notes and posts belong to it.
"""
import hmac
import json
import os
import random
import re
import secrets
import sqlite3
import threading
import time
import uuid
import zipfile
from datetime import date, timedelta
from itertools import groupby
from pathlib import Path

from flask import Flask, abort, g, jsonify, redirect, render_template, request, session, url_for
from markupsafe import escape
from werkzeug.exceptions import HTTPException, TooManyRequests
from werkzeug.middleware.proxy_fix import ProxyFix

import settings
import video_ai
import videos
from lessons import LESSON_IDS, LESSONS
from search_terms import SEARCH

BASE = Path(__file__).parent
DB_PATH = BASE / "calclearners.db"
UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)
SECRET_FILE = BASE / "secret_key"


def secret_key():
    """SECRET_KEY from the environment, or one generated once and kept next to the database."""
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    if not SECRET_FILE.exists():
        SECRET_FILE.write_text(secrets.token_hex(32))
    return SECRET_FILE.read_text().strip()


app = Flask(__name__, static_folder="static", static_url_path="")
# PythonAnywhere sits behind one proxy: trust its X-Forwarded-For / -Proto so we see
# the visitor's real IP (for rate limits) and know when the request came over HTTPS.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
app.config.update(
    SECRET_KEY=secret_key(),
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 10 MB uploads
    SESSION_COOKIE_NAME="cl_id",
    SESSION_COOKIE_HTTPONLY=True,          # page scripts can't read (or leak) the ID
    SESSION_COOKIE_SAMESITE="Lax",         # other sites can't send it with their POSTs
    SESSION_COOKIE_SECURE=True,            # HTTPS only (turned off for local runs below)
    PERMANENT_SESSION_LIFETIME=timedelta(days=365),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    last_topic TEXT,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS progress (
    user_id TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, topic_id)
);
CREATE TABLE IF NOT EXISTS quiz_scores (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS notes (
    user_id TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    body TEXT NOT NULL,
    updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, topic_id)
);
CREATE TABLE IF NOT EXISTS activity (
    user_id TEXT NOT NULL,
    day TEXT NOT NULL,
    PRIMARY KEY (user_id, day)
);
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    author TEXT NOT NULL,
    topic_id TEXT,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    author TEXT NOT NULL,
    body TEXT NOT NULL,
    helpful INTEGER NOT NULL DEFAULT 0,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS votes (
    user_id TEXT NOT NULL,
    kind TEXT NOT NULL,          -- 'q' for question, 'a' for answer
    target_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, kind, target_id)
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    answers TEXT NOT NULL,       -- JSON list of [question, answer]
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    style INTEGER NOT NULL,
    topics TEXT NOT NULL,        -- JSON list of topic ids
    video_id TEXT,               -- visual lesson made from this file, if any
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS videos (  -- AI-made lessons (hand-written ones live in videos/)
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,        -- generating | ready | failed
    message TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    data TEXT,                   -- JSON lesson, once ready
    source_file TEXT,
    source_hash TEXT,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS reports (  -- forum posts flagged for the moderators
    user_id TEXT NOT NULL,
    kind TEXT NOT NULL,          -- 'q' for question, 'a' for answer
    target_id INTEGER NOT NULL,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, kind, target_id)
);
CREATE TABLE IF NOT EXISTS rate_limits (
    key TEXT PRIMARY KEY,        -- rule:who:window length
    window INTEGER NOT NULL,     -- start of the current window (unix seconds)
    hits INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS video_progress (
    user_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    episode INTEGER NOT NULL,
    level TEXT NOT NULL,         -- watched | easy | intermediate | advanced | expert
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, video_id, episode, level)
);
"""


# ---------- Database helpers ----------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def rows(sql, args=()):
    return [dict(r) for r in db().execute(sql, args)]


def one(sql, args=()):
    r = db().execute(sql, args).fetchone()
    return dict(r) if r else None


def run(sql, args=()):
    cur = db().execute(sql, args)
    db().commit()
    return cur


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        # Databases made before videos existed lack this column.
        if "video_id" not in [r[1] for r in conn.execute("PRAGMA table_info(uploads)")]:
            conn.execute("ALTER TABLE uploads ADD COLUMN video_id TEXT")
        # Columns added after the first version.
        have = [r[1] for r in conn.execute("PRAGMA table_info(users)")]
        for column, kind in [("blocked", "INTEGER NOT NULL DEFAULT 0"), ("admin", "INTEGER NOT NULL DEFAULT 0"),
                             ("last_seen", "TEXT"), ("source", "TEXT")]:
            if column not in have:
                conn.execute(f"ALTER TABLE users ADD COLUMN {column} {kind}")  # fixed names from this list
        # Older versions had sign-in (email codes, usernames, passwords, Google). Forget all of
        # it; the browsers that were signed in under an ADMIN_USERS name stay moderators.
        if "username" in have:
            conn.execute("UPDATE users SET admin = 1 WHERE username IN (SELECT value FROM json_each(?))",
                         (json.dumps(sorted(settings.ADMIN_USERS)),))
        conn.execute("DROP TABLE IF EXISTS email_codes")
        for index in ("users_email", "users_google", "users_username"):
            conn.execute(f"DROP INDEX IF EXISTS {index}")  # fixed names from this list
        for column in ("email", "username", "password_hash", "google_sub"):
            if column in have:
                try:
                    conn.execute(f"ALTER TABLE users DROP COLUMN {column}")  # fixed names from this list
                except sqlite3.OperationalError:  # SQLite before 3.35 can't drop a column
                    conn.execute(f"UPDATE users SET {column} = NULL")
        # A restart kills any lesson that was still being generated.
        conn.execute("UPDATE videos SET status = 'failed', message = ? WHERE status = 'generating'",
                     ("The server restarted while building this lesson. Press Retry.",))
        # Link earlier uploads of a PDF that has a hand-written lesson.
        for upload_id, stored in conn.execute(
                "SELECT id, stored_name FROM uploads WHERE video_id IS NULL AND stored_name LIKE '%.pdf'").fetchall():
            path = UPLOADS / stored
            if path.exists() and (vid := videos.BY_HASH.get(videos.sha256_file(path))):
                conn.execute("UPDATE uploads SET video_id = ? WHERE id = ?", (vid, upload_id))


# ---------- Rate limiting ----------
# Fixed-window counters kept in SQLite, so every web worker shares them and they
# survive restarts. Each rule is (max hits, window in seconds).
def client_ip():
    return request.remote_addr or "unknown"


def _wait_text(seconds):
    if seconds < 90:
        return f"{max(1, seconds)} seconds"
    if seconds < 5400:
        return f"{round(seconds / 60)} minutes"
    return f"{round(seconds / 3600)} hours"


def limit(rule, who, max_hits, seconds, message="You're doing that too often."):
    """Count one hit for `who` under `rule`; answer 429 once they pass max_hits in the window."""
    now = int(time.time())
    window = now - now % seconds
    key = f"{rule}:{who}:{seconds}"
    run("""INSERT INTO rate_limits (key, window, hits) VALUES (?, ?, 1)
           ON CONFLICT (key) DO UPDATE SET
             hits = CASE WHEN window = excluded.window THEN hits + 1 ELSE 1 END,
             window = excluded.window""", (key, window))
    hits = one("SELECT hits FROM rate_limits WHERE key = ?", (key,))["hits"]
    if random.random() < 0.01:  # now and then, forget windows that ended long ago
        run("DELETE FROM rate_limits WHERE window < ?", (now - 2 * 86400,))
    if hits > max_hits:
        retry = window + seconds - now
        raise TooManyRequests(f"{message} Try again in {_wait_text(retry)}.", retry_after=retry)


# ---------- Identity ----------
# There is no sign-in. A browser's first API call gets a random visitor ID, kept in a
# signed, HttpOnly cookie; its progress, notes and posts belong to that ID.
# Before cookies, the browser made its own ID and sent it as X-User. A browser that
# still has one of those can claim it once, so nobody loses their progress; brand-new
# IDs are only ever made here, and are rate limited per IP.
LEGACY_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


def current_user():
    """Return this browser's visitor ID from its signed cookie, issuing a new one if needed."""
    uid = session.get("uid")
    u = one("SELECT blocked, last_seen FROM users WHERE id = ?", (uid,)) if uid else None
    if not u:
        legacy = request.headers.get("X-User", "")
        u = one("SELECT blocked, last_seen FROM users WHERE id = ?", (legacy,)) if LEGACY_ID_RE.match(legacy) else None
        if u:
            uid = legacy
        else:
            limit("new-id", client_ip(), 30, 3600, "Too many new visitors from your network.")
            limit("new-id", client_ip(), 200, 86400, "Too many new visitors from your network.")
            uid = secrets.token_urlsafe(24)
            run("INSERT INTO users (id) VALUES (?)", (uid,))
            u = {"blocked": 0, "last_seen": None}
        session.permanent = True
        session["uid"] = uid
    if u["blocked"]:
        abort(403, "This browser has been blocked from CalcLearners.")
    today = date.today().isoformat()
    if u["last_seen"] != today:  # first request of the day from this browser
        run("UPDATE users SET last_seen = ? WHERE id = ?", (today, uid))
        if random.random() < 0.05:
            forget_inactive()
    return uid


# Links in our ads end in ?utm_source=google. A new visitor who arrives through one has that
# word saved with their ID, so ad_report.py can count how many of them studied or came back.
SOURCE_RE = re.compile(r"^[a-z0-9_-]{1,20}$")
BOT_RE = re.compile(r"bot|crawl|spider|preview", re.I)


def note_visit():
    """On a page (not an API call): count today's visit for a browser we know or one an ad sent."""
    source = request.args.get("utm_source", "").lower() or ("google" if "gclid" in request.args else "")
    if not SOURCE_RE.match(source):
        source = ""
    known = bool(session.get("uid"))
    if not (source or known) or BOT_RE.search(request.headers.get("User-Agent", "")):
        return
    try:
        uid = current_user()
    except HTTPException:  # blocked, or too many new visitors: the page itself should still load
        return
    if source and not known:
        run("UPDATE users SET source = ? WHERE id = ?", (source, uid))


def is_admin(uid):
    """Moderators: browsers unlocked with the ADMIN_KEY passcode (see /api/admin/unlock)."""
    u = one("SELECT admin FROM users WHERE id = ?", (uid,))
    return bool(u and u["admin"])


# ---------- Forgetting visitors ----------
RETENTION_DAYS = 365  # the privacy policy promises this: keep it in step with privacy.html


def forget_visitor(uid, posts):
    """Delete what is saved for a visitor ID. Their forum posts go too when `posts` is true;
    otherwise the posts stay up, linked to no one."""
    mine = rows("SELECT stored_name, video_id FROM uploads WHERE user_id = ?", (uid,))
    # One fixed statement per table, as in /api/reset.
    for sql in ("DELETE FROM progress WHERE user_id = ?",
                "DELETE FROM quiz_scores WHERE user_id = ?",
                "DELETE FROM notes WHERE user_id = ?",
                "DELETE FROM activity WHERE user_id = ?",
                "DELETE FROM video_progress WHERE user_id = ?",
                "DELETE FROM feedback WHERE user_id = ?",
                "DELETE FROM uploads WHERE user_id = ?",
                "DELETE FROM reports WHERE user_id = ?",
                "DELETE FROM votes WHERE user_id = ?"):
        run(sql, (uid,))
    if posts:  # the same way as in block_author
        for sql in ("DELETE FROM votes WHERE kind = 'a' AND target_id IN (SELECT id FROM answers WHERE user_id = ?)",
                    """DELETE FROM votes WHERE kind = 'a' AND target_id IN
                       (SELECT a.id FROM answers a JOIN questions q ON q.id = a.question_id WHERE q.user_id = ?)""",
                    "DELETE FROM votes WHERE kind = 'q' AND target_id IN (SELECT id FROM questions WHERE user_id = ?)",
                    "DELETE FROM answers WHERE user_id = ?",
                    "DELETE FROM questions WHERE user_id = ?"):
            run(sql, (uid,))
    # AI lessons and the PDFs kept for them go too, unless someone else's upload still uses them.
    for video_id in {u["video_id"] for u in mine if u["video_id"]}:
        run("DELETE FROM videos WHERE id = ? AND NOT EXISTS (SELECT 1 FROM uploads WHERE video_id = ?)",
            (video_id, video_id))
    for stored in {u["stored_name"] for u in mine}:
        if not one("SELECT 1 FROM videos WHERE source_file = ?", (stored,)):
            try:
                (UPLOADS / stored).unlink(missing_ok=True)
            except OSError:  # still open (a lesson being built from it): don't let that stop the deletion
                app.logger.warning("Couldn't remove upload %s of a deleted visitor", stored)
    run("DELETE FROM users WHERE id = ?", (uid,))


def forget_inactive():
    """Browsers that haven't visited for a year are forgotten, a few at a time."""
    cutoff = (date.today() - timedelta(days=RETENTION_DAYS)).isoformat()
    for r in rows("""SELECT id FROM users WHERE COALESCE(last_seen, substr(created, 1, 10)) < ?
                     AND blocked = 0 AND admin = 0 LIMIT 25""", (cutoff,)):
        forget_visitor(r["id"], posts=False)


# ---------- Request guards & security headers ----------
@app.before_request
def force_https():
    # Behind the hosting proxy, send plain-HTTP visitors to HTTPS (local runs have no proxy header).
    if request.headers.get("X-Forwarded-Proto") == "http":
        return redirect(request.url.replace("http://", "https://", 1), code=301)


@app.before_request
def guard_api():
    if not request.path.startswith("/api/"):
        return
    # Backstop for scripts hammering the API from one address (schools share IPs, so it's generous).
    limit("ip", client_ip(), 300, 60, "Too many requests from your network.")
    # Cross-site request forgery: a page on another site can't add this header
    # without a CORS preflight, which we never approve.
    if request.method in ("POST", "PUT", "DELETE") and request.headers.get("X-Requested-With") != "CalcLearners":
        abort(403, "Missing request header.")


CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' https://cdn.jsdelivr.net",
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
    "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net",
    "img-src 'self' data:",
    "connect-src 'self' http://localhost:5000",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])


@app.after_request
def security_headers(resp):
    resp.headers["Content-Security-Policy"] = CSP
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if request.is_secure:
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["X-Robots-Tag"] = "noindex"  # API answers (forum posts, progress) stay out of search results
    return resp


def body():
    return request.get_json(silent=True) or {}


def topic_or_400(topic):
    if topic not in LESSON_IDS:
        abort(400, "Unknown topic.")
    return topic


def author_name(uid):
    return one("SELECT name FROM users WHERE id = ?", (uid,))["name"] or "Anonymous learner"


def mark_active(uid):
    run("INSERT OR IGNORE INTO activity (user_id, day) VALUES (?, ?)", (uid, date.today().isoformat()))


def streak(uid):
    """Days in a row with any study activity, ending today (or yesterday)."""
    days = {r["day"] for r in rows("SELECT day FROM activity WHERE user_id = ?", (uid,))}
    day = date.today()
    if day.isoformat() not in days:
        day -= timedelta(days=1)
    count = 0
    while day.isoformat() in days:
        count += 1
        day -= timedelta(days=1)
    return count


LOCAL_ORIGIN = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")


@app.after_request
def allow_local_probe(resp):
    """Let a copy of the page opened another way (e.g. VS Code Live Server) detect
    that server.py is running, so it can switch over to http://localhost:5000."""
    origin = request.headers.get("Origin", "")
    if request.path == "/api/lessons" and LOCAL_ORIGIN.match(origin):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
    return resp


@app.errorhandler(HTTPException)
def json_error(e):
    resp = jsonify(error=e.description)
    if getattr(e, "retry_after", None):
        resp.headers["Retry-After"] = str(e.retry_after)
    return resp, e.code


# ---------- Moderation ----------
# Simple rule-based filter. Could be swapped for an AI moderation call later.
BAD_WORDS = re.compile(r"\b(butt|stupid|idiot|dumb|shut up|ur mom|fuck|shit)\b", re.I)
MATHY = re.compile(r"[\d=^+\-*/]|integral|derivative|limit|sum|series|chain|rule|because|then", re.I)


def check_post(text, min_len, what):
    text = text.strip()
    if len(text) < min_len:
        abort(400, f"Your {what} is too short. Add a bit more detail (at least {min_len} characters).")
    if len(text) > 5000:
        abort(400, f"Your {what} is too long (max 5000 characters).")
    if BAD_WORDS.search(text):
        abort(400, "Please keep it kind. Posts with insults or joke content are filtered out.")
    return text


def check_answer(question, answer):
    answer = check_post(answer, 8, "answer")
    q_words = re.findall(r"[a-z]{4,}", question.lower())
    if not MATHY.search(answer) and not any(w in answer.lower() for w in q_words):
        abort(400, "This doesn't look related to the question. Try explaining a step or showing some math.")
    return answer


# ---------- Pages ----------
@app.get("/")
def index():
    # The page's own address and the Search Console code depend on where the site runs,
    # so they are added to the <head> here instead of being written into index.html.
    note_visit()
    head = f'  <link rel="canonical" href="{escape(request.url_root)}">\n'
    if settings.GOOGLE_SITE_VERIFICATION:
        head += f'  <meta name="google-site-verification" content="{escape(settings.GOOGLE_SITE_VERIFICATION)}">\n'
    page = (BASE / "static" / "index.html").read_text(encoding="utf8")
    return page.replace("</head>", head + "</head>", 1)


# The app shows lessons at /#/learn/<id>, and search engines ignore everything after the "#".
# These pages give every lesson an address of its own that can be found, and link into the app.
LESSON_BY_ID = {l["id"]: l for l in LESSONS}


def unit_label(lesson):
    return "Extra topics" if lesson["unit"] == "Extra" else f"{lesson['unit']}: {lesson['unit_title']}"


@app.get("/lessons")
def lesson_list():
    units = [(label, list(group)) for label, group in groupby(LESSONS, unit_label)]
    return render_template("lessons.html", units=units, count=len(LESSONS))


@app.get("/lessons/<lesson_id>")
def lesson_page(lesson_id):
    lesson = LESSON_BY_ID.get(lesson_id)
    if not lesson:
        abort(404)
    note_visit()
    i = LESSONS.index(lesson)
    title, also_called = SEARCH[lesson_id]
    return render_template(
        "lesson.html",
        lesson=lesson,
        title=title,
        also_called=also_called,
        unit=unit_label(lesson),
        prereqs=[LESSON_BY_ID[p] for p in lesson["prereqs"] if p in LESSON_BY_ID],
        prev=LESSONS[i - 1] if i else None,
        next=LESSONS[i + 1] if i + 1 < len(LESSONS) else None,
    )


@app.get("/sitemap.xml")
def sitemap():
    pages = [url_for("index", _external=True), url_for("lesson_list", _external=True)]
    pages += [url_for("lesson_page", lesson_id=l["id"], _external=True) for l in LESSONS]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "".join(f"  <url><loc>{escape(page)}</loc></url>\n" for page in pages)
    return app.response_class(xml + "</urlset>\n", mimetype="application/xml")


@app.get("/robots.txt")
def robots():
    # Crawlers stay out of the API, apart from the two calls the home page needs to draw itself.
    lines = ["User-agent: *", "Allow: /api/me$", "Allow: /api/lessons$", "Disallow: /api/",
             "", "Sitemap: " + url_for("sitemap", _external=True)]
    return app.response_class("\n".join(lines) + "\n", mimetype="text/plain")


# ---------- Lessons ----------
@app.get("/api/lessons")
def lessons():
    return jsonify(LESSONS)


# ---------- Learner profile & progress ----------
@app.get("/api/me")
def me():
    uid = current_user()
    user = one("SELECT name, last_topic FROM users WHERE id = ?", (uid,))
    # Only report topics that still exist (lessons get reorganized over time).
    quiz = {}
    for r in rows("""SELECT topic_id, score, total FROM quiz_scores
                     WHERE user_id = ? ORDER BY created, id""", (uid,)):
        if r["topic_id"] not in LESSON_IDS:
            continue
        pct = round(100 * r["score"] / r["total"])
        q = quiz.setdefault(r["topic_id"], {"best": 0, "last": 0, "attempts": 0})
        q["best"] = max(q["best"], pct)
        q["last"] = pct
        q["attempts"] += 1
    return jsonify(
        name=user["name"],
        admin=is_admin(uid),
        last_topic=user["last_topic"] if user["last_topic"] in LESSON_IDS else None,
        done=[r["topic_id"] for r in rows("SELECT topic_id FROM progress WHERE user_id = ?", (uid,))
              if r["topic_id"] in LESSON_IDS],
        quiz=quiz,
        notes=[r["topic_id"] for r in rows(
            "SELECT topic_id FROM notes WHERE user_id = ? AND body != '' AND topic_id NOT LIKE 'video:%'", (uid,))
               if r["topic_id"] in LESSON_IDS],
        streak=streak(uid),
    )


def limit_saves(uid):
    """Progress, quiz scores, notes: the page saves these often, but never this often."""
    limit("save", uid, 120, 60, "You're saving too quickly.")


@app.post("/api/me")
def set_name():
    uid = current_user()
    limit("name", uid, 10, 3600, "You've changed your name a lot.")
    name = str(body().get("name", "")).strip()[:40]
    if BAD_WORDS.search(name):
        abort(400, "Please choose a different name.")
    run("UPDATE users SET name = ? WHERE id = ?", (name, uid))
    return jsonify(name=name)


@app.post("/api/visit")
def visit():
    uid = current_user()
    limit_saves(uid)
    topic = topic_or_400(body().get("topic"))
    run("UPDATE users SET last_topic = ? WHERE id = ?", (topic, uid))
    mark_active(uid)
    return jsonify(ok=True)


@app.post("/api/progress")
def progress():
    uid = current_user()
    limit_saves(uid)
    data = body()
    topic = topic_or_400(data.get("topic"))
    if data.get("done"):
        run("INSERT OR REPLACE INTO progress (user_id, topic_id) VALUES (?, ?)", (uid, topic))
    else:
        run("DELETE FROM progress WHERE user_id = ? AND topic_id = ?", (uid, topic))
    mark_active(uid)
    return jsonify(ok=True)


@app.post("/api/quiz")
def quiz():
    uid = current_user()
    limit_saves(uid)
    data = body()
    topic = topic_or_400(data.get("topic"))
    try:
        score, total = int(data["score"]), int(data["total"])
    except (KeyError, TypeError, ValueError):
        abort(400, "Score and total are required.")
    if total < 1 or not 0 <= score <= total:
        abort(400, "Invalid score.")
    run("INSERT INTO quiz_scores (user_id, topic_id, score, total) VALUES (?, ?, ?, ?)", (uid, topic, score, total))
    mark_active(uid)
    return jsonify(ok=True)


@app.post("/api/reset")
def reset():
    uid = current_user()
    limit("reset", uid, 5, 3600, "You've reset your progress a lot.")
    # One fixed statement per table: no SQL is ever built from strings.
    for sql in ("DELETE FROM progress WHERE user_id = ?",
                "DELETE FROM quiz_scores WHERE user_id = ?",
                "DELETE FROM notes WHERE user_id = ?",
                "DELETE FROM activity WHERE user_id = ?",
                "DELETE FROM video_progress WHERE user_id = ?",
                "UPDATE users SET last_topic = NULL WHERE id = ?"):
        run(sql, (uid,))
    return jsonify(ok=True)


@app.post("/api/me/delete")
def delete_my_data():
    """Delete everything saved for this browser's visitor ID, then forget the ID."""
    uid = current_user()
    limit("delete-me", uid, 5, 3600, "Too many tries at deleting your data.")
    limit("delete-me-ip", client_ip(), 20, 3600, "Too many tries at deleting data from your network.")
    # It can't be undone, so the page asks for a typed word first.
    if str(body().get("confirm", "")).strip().upper() != "DELETE":
        abort(400, "Type DELETE to confirm.")

    forget_visitor(uid, posts=True)
    session.clear()
    return jsonify(ok=True)


# ---------- Notes ----------
@app.get("/api/notes/<topic>")
def get_note(topic):
    uid = current_user()
    topic_or_400(topic)
    note = one("SELECT body, updated FROM notes WHERE user_id = ? AND topic_id = ?", (uid, topic))
    return jsonify(note or {"body": "", "updated": None})


@app.put("/api/notes/<topic>")
def put_note(topic):
    uid = current_user()
    limit_saves(uid)
    topic_or_400(topic)
    text = str(body().get("body", ""))[:10000]
    run("""INSERT INTO notes (user_id, topic_id, body) VALUES (?, ?, ?)
           ON CONFLICT (user_id, topic_id) DO UPDATE SET body = excluded.body, updated = CURRENT_TIMESTAMP""",
        (uid, topic, text))
    return jsonify(ok=True)


# ---------- Forum ----------
# The whole forum query is one fixed string. Sorting and the "unanswered" filter are
# switched by parameters (? = 'top' ...), so user input only ever travels as data.
QUESTIONS_SQL = """
    SELECT * FROM (
        SELECT q.id, q.author, q.topic_id, q.title, q.body, q.created,
               q.user_id = :uid AS mine,
               (SELECT COUNT(*) FROM votes v WHERE v.kind = 'q' AND v.target_id = q.id) AS votes,
               EXISTS (SELECT 1 FROM votes v WHERE v.kind = 'q' AND v.target_id = q.id AND v.user_id = :uid) AS voted,
               (SELECT COUNT(*) FROM answers a WHERE a.question_id = q.id) AS answer_count
        FROM questions q
        WHERE (:topic = '' OR q.topic_id = :topic)
          AND (:search = '' OR q.title LIKE :like ESCAPE '\\' OR q.body LIKE :like ESCAPE '\\')
    )
    WHERE (:sort != 'unanswered' OR answer_count = 0)
    ORDER BY CASE WHEN :sort = 'top' THEN votes END DESC, created DESC, id DESC
    LIMIT 100"""

ANSWERS_SQL = """
    SELECT a.id, a.question_id, a.author, a.body, a.helpful, a.created,
           a.user_id = :uid AS mine,
           (SELECT COUNT(*) FROM votes v WHERE v.kind = 'a' AND v.target_id = a.id) AS votes,
           EXISTS (SELECT 1 FROM votes v WHERE v.kind = 'a' AND v.target_id = a.id AND v.user_id = :uid) AS voted
    FROM answers a
    WHERE a.question_id IN (SELECT value FROM json_each(:ids))
    ORDER BY a.helpful DESC, votes DESC, a.created"""


@app.get("/api/questions")
def list_questions():
    uid = current_user()
    topic = request.args.get("topic", "")[:80]
    search = request.args.get("q", "").strip()[:100]
    sort = request.args.get("sort", "new")
    if sort not in ("new", "top", "unanswered"):
        sort = "new"
    # % and _ are LIKE wildcards: escape them so a search for "50%" means just that.
    like = "%" + re.sub(r"([\\%_])", r"\\\1", search) + "%"
    qs = rows(QUESTIONS_SQL, {"uid": uid, "topic": topic, "search": search, "like": like, "sort": sort})

    answers = {}
    for a in rows(ANSWERS_SQL, {"uid": uid, "ids": json.dumps([q["id"] for q in qs])}):
        answers.setdefault(a["question_id"], []).append(a)
    for q in qs:
        q["answers"] = answers.get(q["id"], [])
    return jsonify(qs)


@app.post("/api/questions")
def ask():
    uid = current_user()
    limit("ask", uid, 5, 600, "You've asked a lot of questions.")
    limit("ask", uid, 30, 86400, "You've reached today's question limit.")
    limit("ask-ip", client_ip(), 40, 3600, "Lots of questions are coming from your network.")
    data = body()
    title = check_post(str(data.get("title", "")), 10, "question")
    details = str(data.get("body", "")).strip()
    if details:
        details = check_post(details, 1, "details")
    topic = data.get("topic") or None
    if topic:
        topic_or_400(topic)
    cur = run("INSERT INTO questions (user_id, author, topic_id, title, body) VALUES (?, ?, ?, ?, ?)",
              (uid, author_name(uid), topic, title, details))
    return jsonify(id=cur.lastrowid)


@app.delete("/api/questions/<int:qid>")
def delete_question(qid):
    uid = current_user()
    limit("delete", uid, 30, 3600)
    q = one("SELECT user_id FROM questions WHERE id = ?", (qid,)) or abort(404, "Question not found.")
    if q["user_id"] != uid and not is_admin(uid):
        abort(403, "You can only delete your own questions.")
    run("DELETE FROM votes WHERE kind = 'a' AND target_id IN (SELECT id FROM answers WHERE question_id = ?)", (qid,))
    run("DELETE FROM votes WHERE kind = 'q' AND target_id = ?", (qid,))
    run("DELETE FROM questions WHERE id = ?", (qid,))
    return jsonify(ok=True)


@app.delete("/api/answers/<int:aid>")
def delete_answer(aid):
    uid = current_user()
    limit("delete", uid, 30, 3600)
    a = one("SELECT user_id FROM answers WHERE id = ?", (aid,)) or abort(404, "Answer not found.")
    if a["user_id"] != uid and not is_admin(uid):
        abort(403, "You can only delete your own answers.")
    run("DELETE FROM votes WHERE kind = 'a' AND target_id = ?", (aid,))
    run("DELETE FROM answers WHERE id = ?", (aid,))
    return jsonify(ok=True)


@app.post("/api/admin/block")
def block_author():
    """Admins: block the author of a post and remove everything they posted."""
    uid = current_user()
    if not is_admin(uid):
        abort(403, "Only moderators can block people.")
    data = body()
    owner_sql = {"q": "SELECT user_id FROM questions WHERE id = ?",
                 "a": "SELECT user_id FROM answers WHERE id = ?"}.get(data.get("kind")) or abort(400, "Unknown post.")
    try:
        target = int(data.get("id"))
    except (TypeError, ValueError):
        abort(400, "Unknown post.")
    author = (one(owner_sql, (target,)) or abort(404, "Post not found."))["user_id"]
    if author == uid:
        abort(400, "You can't block yourself.")
    run("UPDATE users SET blocked = 1 WHERE id = ?", (author,))
    for sql in ("DELETE FROM votes WHERE kind = 'a' AND target_id IN (SELECT id FROM answers WHERE user_id = ?)",
                """DELETE FROM votes WHERE kind = 'a' AND target_id IN
                   (SELECT a.id FROM answers a JOIN questions q ON q.id = a.question_id WHERE q.user_id = ?)""",
                "DELETE FROM votes WHERE kind = 'q' AND target_id IN (SELECT id FROM questions WHERE user_id = ?)",
                "DELETE FROM votes WHERE user_id = ?",
                "DELETE FROM answers WHERE user_id = ?",
                "DELETE FROM questions WHERE user_id = ?"):
        run(sql, (author,))
    return jsonify(ok=True)


@app.post("/api/report")
def report():
    """Flag a forum post for the moderators."""
    uid = current_user()
    limit("report", uid, 10, 3600, "You've reported a lot of posts.")
    limit("report-ip", client_ip(), 40, 3600, "Lots of reports are coming from your network.")
    data = body()
    kind = data.get("kind")
    try:
        target = int(data.get("id"))
    except (TypeError, ValueError):
        abort(400, "Unknown post.")
    post_sql = {"q": "SELECT 1 FROM questions WHERE id = ?",
                "a": "SELECT 1 FROM answers WHERE id = ?"}.get(kind) or abort(400, "Unknown post.")
    one(post_sql, (target,)) or abort(404, "Post not found.")
    run("INSERT OR IGNORE INTO reports (user_id, kind, target_id) VALUES (?, ?, ?)", (uid, kind, target))
    return jsonify(ok=True)


@app.post("/api/admin/unlock")
def admin_unlock():
    """Make this browser a moderator, given the ADMIN_KEY passcode from secrets.env."""
    uid = current_user()
    limit("admin-unlock", client_ip(), 5, 3600, "Too many tries at the passcode.")
    key = str(body().get("key", ""))[:200]
    if not settings.ADMIN_KEY or not hmac.compare_digest(key.encode(), settings.ADMIN_KEY.encode()):
        abort(403, "That passcode isn't right.")
    run("UPDATE users SET admin = 1 WHERE id = ?", (uid,))
    return jsonify(ok=True)


@app.post("/api/admin/lock")
def admin_lock():
    run("UPDATE users SET admin = 0 WHERE id = ?", (current_user(),))
    return jsonify(ok=True)


REPORTS_SQL = """
    SELECT r.kind, r.target_id AS id, COUNT(*) AS reports, MAX(r.created) AS last,
           COALESCE(q.author, a.author) AS author,
           COALESCE(q.title, aq.title) AS title,
           COALESCE(a.body, q.body) AS body
    FROM reports r
    LEFT JOIN questions q ON r.kind = 'q' AND q.id = r.target_id
    LEFT JOIN answers a ON r.kind = 'a' AND a.id = r.target_id
    LEFT JOIN questions aq ON aq.id = a.question_id
    GROUP BY r.kind, r.target_id
    ORDER BY reports DESC, last DESC
    LIMIT 100"""


@app.get("/api/admin/reports")
def reported_posts():
    if not is_admin(current_user()):
        abort(403, "Only moderators can see reports.")
    # Reports on posts that have since been deleted are of no use.
    run("""DELETE FROM reports WHERE (kind = 'q' AND target_id NOT IN (SELECT id FROM questions))
                                  OR (kind = 'a' AND target_id NOT IN (SELECT id FROM answers))""")
    return jsonify(rows(REPORTS_SQL))


@app.post("/api/admin/reports/dismiss")
def dismiss_reports():
    """Moderators: the post is fine, drop the reports on it."""
    if not is_admin(current_user()):
        abort(403, "Only moderators can dismiss reports.")
    data = body()
    try:
        target = int(data.get("id"))
    except (TypeError, ValueError):
        abort(400, "Unknown post.")
    run("DELETE FROM reports WHERE kind = ? AND target_id = ?", (str(data.get("kind")), target))
    return jsonify(ok=True)


@app.post("/api/questions/<int:qid>/answers")
def answer(qid):
    uid = current_user()
    limit("answer", uid, 10, 600, "You've posted a lot of answers.")
    limit("answer", uid, 100, 86400, "You've reached today's answer limit.")
    limit("answer-ip", client_ip(), 80, 3600, "Lots of answers are coming from your network.")
    q = one("SELECT title, body FROM questions WHERE id = ?", (qid,)) or abort(404, "Question not found.")
    text = check_answer(q["title"] + " " + q["body"], str(body().get("body", "")))
    run("INSERT INTO answers (question_id, user_id, author, body) VALUES (?, ?, ?, ?)",
        (qid, uid, author_name(uid), text))
    return jsonify(ok=True)


@app.post("/api/answers/<int:aid>/helpful")
def helpful(aid):
    uid = current_user()
    limit("helpful", uid, 60, 3600)
    a = one("""SELECT a.helpful, q.user_id AS asker FROM answers a
               JOIN questions q ON q.id = a.question_id WHERE a.id = ?""", (aid,)) or abort(404, "Answer not found.")
    if a["asker"] != uid:
        abort(403, "Only the person who asked can mark an answer as helpful.")
    run("UPDATE answers SET helpful = ? WHERE id = ?", (0 if a["helpful"] else 1, aid))
    return jsonify(ok=True)


@app.post("/api/vote")
def vote():
    uid = current_user()
    limit("vote", uid, 30, 60, "You're voting very fast.")
    limit("vote", uid, 300, 86400, "You've reached today's voting limit.")
    data = body()
    kind = data.get("kind")
    try:
        target = int(data.get("id"))
    except (TypeError, ValueError):
        abort(400, "Unknown post.")
    owner_sql = {"q": "SELECT user_id FROM questions WHERE id = ?",
                 "a": "SELECT user_id FROM answers WHERE id = ?"}.get(kind) or abort(400, "Unknown vote type.")
    post = one(owner_sql, (target,)) or abort(404, "Post not found.")
    if post["user_id"] == uid:
        abort(400, "You can't upvote your own post.")
    key = (uid, kind, target)
    if one("SELECT 1 FROM votes WHERE user_id = ? AND kind = ? AND target_id = ?", key):
        run("DELETE FROM votes WHERE user_id = ? AND kind = ? AND target_id = ?", key)
    else:
        run("INSERT INTO votes (user_id, kind, target_id) VALUES (?, ?, ?)", key)
    return jsonify(ok=True)


# ---------- Feedback ----------
@app.get("/api/feedback")
def feedback_count():
    uid = current_user()
    return jsonify(count=one("SELECT COUNT(*) AS n FROM feedback WHERE user_id = ?", (uid,))["n"])


@app.post("/api/feedback")
def feedback():
    uid = current_user()
    limit("feedback", uid, 5, 3600, "Thanks, we've got plenty of feedback from you for now.")
    answers = body().get("answers")
    if not isinstance(answers, list):
        abort(400, "Please answer at least one question.")
    # Keep only [question, answer] pairs, each trimmed, so the stored JSON is always valid.
    answers = [[str(q)[:300], str(a).strip()[:3000]] for q, a in
               (p for p in answers[:10] if isinstance(p, list) and len(p) == 2)]
    if not any(a for _, a in answers):
        abort(400, "Please answer at least one question.")
    run("INSERT INTO feedback (user_id, answers) VALUES (?, ?)", (uid, json.dumps(answers)))
    return jsonify(ok=True)


# ---------- Uploads ----------
ALLOWED = {".pdf", ".docx", ".txt"}
UPLOADS_CAP = 300 * 1024 * 1024        # stop taking uploads before the host's disk quota fills
DOCX_XML_CAP = 20 * 1024 * 1024        # a .docx whose text unzips past this is a zip bomb
TEXT_CAP = 200_000                     # characters of text kept for topic matching


def looks_like(path, ext):
    """Check the file really is what its extension says (first bytes), so nothing else gets parsed."""
    with open(path, "rb") as fh:
        head = fh.read(8)
    if ext == ".pdf":
        return head.startswith(b"%PDF-")
    if ext == ".docx":
        return head.startswith(b"PK\x03\x04")
    return b"\x00" not in head  # plain text has no NUL bytes


def extract_text(path):
    """Best-effort text extraction so we can guess which topics a file covers."""
    ext = path.suffix.lower()
    try:
        if ext == ".txt":
            with open(path, encoding="utf8", errors="ignore") as fh:
                return fh.read(TEXT_CAP)
        if ext == ".docx":
            with zipfile.ZipFile(path) as z:
                info = z.getinfo("word/document.xml")
                if info.file_size > DOCX_XML_CAP:
                    return ""
                with z.open(info) as fh:
                    xml = fh.read(DOCX_XML_CAP).decode("utf8", "ignore")
            return re.sub(r"<[^>]+>", " ", xml)[:TEXT_CAP]
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(path)
            text = ""
            for page in reader.pages[:20]:
                text += (page.extract_text() or "") + " "
                if len(text) > TEXT_CAP:
                    break
            return text[:TEXT_CAP]
    except Exception:
        pass
    return ""


def uploads_size():
    return sum(p.stat().st_size for p in UPLOADS.iterdir() if p.is_file())


def match_topics(text):
    """Score each lesson by how often its name and keywords appear in the text."""
    text = text.lower()
    scores = []
    for l in LESSONS:
        words = {w for w in re.findall(r"[a-z']{3,}", (l["name"] + " " + l["keywords"]).lower())}
        words -= {"and", "the", "test", "rule", "rules", "series", "integral", "integrals"}  # too generic on their own
        score = sum(len(re.findall(r"\b" + re.escape(w) + r"\b", text)) for w in words)
        if score:
            scores.append((score, l["id"]))
    scores.sort(reverse=True)
    return [t for _, t in scores[:5]]


@app.post("/api/upload")
def upload():
    uid = current_user()
    limit("upload", uid, 5, 3600, "You've uploaded a lot of files.")
    limit("upload", uid, 15, 86400, "You've reached today's upload limit.")
    limit("upload-ip", client_ip(), 40, 86400, "Lots of uploads are coming from your network.")
    f = request.files.get("file")
    if not f or not f.filename:
        abort(400, "Choose a file first.")
    filename = f.filename[:200]
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED:
        abort(400, "Please upload a PDF, Word (.docx) or text file.")
    if uploads_size() > UPLOADS_CAP:
        abort(503, "Uploads are paused for now because storage is full. Please try again later.")
    try:
        style = min(4, max(0, int(request.form.get("style", 0))))
    except ValueError:
        style = 0
    stored = f"{uuid.uuid4().hex}{ext}"
    path = UPLOADS / stored
    f.save(path)
    if not looks_like(path, ext):
        path.unlink(missing_ok=True)
        abort(400, f"That file isn't a real {ext} file. Please upload a PDF, Word (.docx) or text file.")

    text = extract_text(path)
    topics = match_topics(text + " " + filename)
    video_id = find_or_start_video(path, stored) if ext == ".pdf" else None
    # Keep the file only while an AI lesson might still need it (for Retry); otherwise
    # we already have what we need from it.
    if not one("SELECT 1 FROM videos WHERE source_file = ?", (stored,)):
        path.unlink(missing_ok=True)
    run("INSERT INTO uploads (user_id, filename, stored_name, style, topics, video_id) VALUES (?, ?, ?, ?, ?, ?)",
        (uid, filename, stored, style, json.dumps(topics), video_id))
    return jsonify(filename=filename, style=style, topics=topics, read_text=bool(text.strip()),
                   video=video_info(video_id) if video_id else None, ai_available=video_ai.available())


@app.get("/api/uploads")
def list_uploads():
    uid = current_user()
    items = rows("""SELECT filename, style, topics, video_id, created FROM uploads
                    WHERE user_id = ? ORDER BY id DESC LIMIT 20""", (uid,))
    for i in items:
        i["topics"] = json.loads(i["topics"])
        i["video"] = video_info(i.pop("video_id")) if i["video_id"] else None
    return jsonify(items)


# ---------- Visual video lessons ----------
def find_or_start_video(path, stored):
    """Return the id of a lesson for this PDF: hand-written, already generated, or newly started."""
    digest = videos.sha256_file(path)
    if digest in videos.BY_HASH:
        return videos.BY_HASH[digest]
    existing = one("SELECT id FROM videos WHERE source_hash = ? AND status != 'failed'", (digest,))
    if existing:
        return existing["id"]
    if not video_ai.available():
        return None
    # AI lessons cost real money per PDF: cap them for the whole site, and per person.
    limit("ai", "site", 10, 86400, "Today's AI lesson limit for the site is used up.")
    limit("ai-user", current_user(), 2, 86400, "You can make 2 AI lessons a day.")
    video_id = "v" + uuid.uuid4().hex[:12]
    run("INSERT INTO videos (id, status, message, source_file, source_hash) VALUES (?, 'generating', ?, ?, ?)",
        (video_id, "Starting…", stored, digest))
    start_generation(video_id, path)
    return video_id


def start_generation(video_id, path):
    """Build the lesson in a background thread; the page polls /api/videos/<id> for progress."""
    def work():
        conn = sqlite3.connect(DB_PATH)

        def progress(message):
            conn.execute("UPDATE videos SET message = ? WHERE id = ?", (message, video_id))
            conn.commit()

        try:
            data = videos.normalize(video_ai.generate(path, progress))
            if not data["episodes"]:
                raise video_ai.GenerationError("The AI couldn't build any episodes from this file.")
            conn.execute("UPDATE videos SET status = 'ready', title = ?, data = ?, message = '' WHERE id = ?",
                         (data["title"], json.dumps(data), video_id))
        except video_ai.GenerationError as e:
            conn.execute("UPDATE videos SET status = 'failed', message = ? WHERE id = ?", (str(e), video_id))
        except Exception:
            app.logger.exception("Video generation failed")
            conn.execute("UPDATE videos SET status = 'failed', message = ? WHERE id = ?",
                         ("Something went wrong while building the lesson. Press Retry.", video_id))
        conn.commit()
        conn.close()

    threading.Thread(target=work, daemon=True).start()


def load_video(video_id):
    """(status, message, lesson-or-None) for a hand-written or generated lesson."""
    if video_id in videos.BUILTIN:
        return "ready", "", videos.BUILTIN[video_id]
    row = one("SELECT status, message, data FROM videos WHERE id = ?", (video_id,))
    if not row:
        return None
    return row["status"], row["message"], json.loads(row["data"]) if row["data"] else None


def video_info(video_id):
    """Small summary for lists: status plus title and episode lengths when ready."""
    loaded = load_video(video_id)
    if not loaded:
        return None
    status, message, data = loaded
    return {"id": video_id, "status": status, "message": message, **(videos.summary(data) if data else {})}


def video_or_404(uid, video_id):
    loaded = load_video(video_id)
    owns = one("SELECT 1 FROM uploads WHERE user_id = ? AND video_id = ?", (uid, video_id))
    if not loaded or (video_id not in videos.BUILTIN and not owns):
        abort(404, "Video lesson not found.")
    return loaded


def video_progress(uid, video_id):
    progress = {}
    for r in rows("SELECT episode, level, score, total FROM video_progress WHERE user_id = ? AND video_id = ?",
                  (uid, video_id)):
        progress.setdefault(str(r["episode"]), {})[r["level"]] = {"score": r["score"], "total": r["total"]}
    return progress


@app.get("/api/videos")
def list_videos():
    uid = current_user()
    items = []
    for r in rows("""SELECT video_id, MIN(filename) AS filename, MAX(id) AS last FROM uploads
                     WHERE user_id = ? AND video_id IS NOT NULL GROUP BY video_id ORDER BY last DESC""", (uid,)):
        info = video_info(r["video_id"])
        if info:
            info["filename"] = r["filename"]
            info["progress"] = video_progress(uid, r["video_id"])
            items.append(info)
    return jsonify(videos=items, ai_available=video_ai.available())


@app.get("/api/videos/<video_id>")
def get_video(video_id):
    uid = current_user()
    status, message, data = video_or_404(uid, video_id)
    return jsonify(id=video_id, status=status, message=message, lesson=data,
                   progress=video_progress(uid, video_id), ai_available=video_ai.available())


@app.post("/api/videos/<video_id>/progress")
def save_video_progress(video_id):
    uid = current_user()
    limit_saves(uid)
    _, _, data = video_or_404(uid, video_id)
    body_ = body()
    level = body_.get("level")
    try:
        episode, score, total = int(body_["episode"]), int(body_.get("score", 1)), int(body_.get("total", 1))
    except (KeyError, TypeError, ValueError):
        abort(400, "Episode, score and total are required.")
    if not data or not 0 <= episode < len(data["episodes"]) or (level not in ("watched", "read") and level not in videos.LEVELS):
        abort(400, "Unknown episode or level.")
    if total < 1 or not 0 <= score <= total:
        abort(400, "Invalid score.")
    # Keep the best score for each level.
    run("""INSERT INTO video_progress (user_id, video_id, episode, level, score, total) VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT (user_id, video_id, episode, level)
           DO UPDATE SET score = MAX(score, excluded.score), total = excluded.total, updated = CURRENT_TIMESTAMP""",
        (uid, video_id, episode, level, score, total))
    mark_active(uid)
    return jsonify(progress=video_progress(uid, video_id))


@app.get("/api/videos/<video_id>/notes/<int:episode>")
def get_video_note(video_id, episode):
    uid = current_user()
    video_or_404(uid, video_id)
    note = one("SELECT body FROM notes WHERE user_id = ? AND topic_id = ?", (uid, f"video:{video_id}:{episode}"))
    return jsonify(body=note["body"] if note else "")


@app.put("/api/videos/<video_id>/notes/<int:episode>")
def put_video_note(video_id, episode):
    uid = current_user()
    limit_saves(uid)
    video_or_404(uid, video_id)
    run("""INSERT INTO notes (user_id, topic_id, body) VALUES (?, ?, ?)
           ON CONFLICT (user_id, topic_id) DO UPDATE SET body = excluded.body, updated = CURRENT_TIMESTAMP""",
        (uid, f"video:{video_id}:{episode}", str(body().get("body", ""))[:10000]))
    return jsonify(ok=True)


@app.post("/api/videos/<video_id>/retry")
def retry_video(video_id):
    uid = current_user()
    limit("retry", uid, 3, 3600, "You've retried a lot.")
    video_or_404(uid, video_id)
    row = one("SELECT status, source_file FROM videos WHERE id = ?", (video_id,))
    if not row or row["status"] != "failed":
        abort(400, "This lesson isn't in a failed state.")
    if not video_ai.available():
        abort(400, "AI lessons are turned off. Set an ANTHROPIC_API_KEY and restart the server.")
    path = UPLOADS / (row["source_file"] or "")
    if not path.is_file():
        abort(400, "The original file is gone. Upload it again.")
    limit("ai", "site", 10, 86400, "Today's AI lesson limit for the site is used up.")
    run("UPDATE videos SET status = 'generating', message = 'Starting…' WHERE id = ?", (video_id,))
    start_generation(video_id, path)
    return jsonify(ok=True)


init_db()

if __name__ == "__main__":
    print("CalcLearners running at http://localhost:5000")
    app.config["SESSION_COOKIE_SECURE"] = False  # local runs are plain http://localhost
    # "stat" reloader: restart only when an already-loaded file is edited. The default
    # watchdog reloader also restarts when pypdf imports new modules mid-upload,
    # which kills the request.
    app.run(debug=True, port=5000, reloader_type="stat")
