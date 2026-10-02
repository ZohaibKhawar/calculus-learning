"""CalcLearners backend: a small Flask + SQLite server.

Run it:
    pip install -r requirements.txt
    python server.py
Then open http://localhost:5000

There are no accounts. Each browser makes a random ID the first time it visits
and sends it in the X-User header, so progress, notes and posts belong to it.
"""
import json
import re
import sqlite3
import threading
import uuid
import zipfile
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, abort, g, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

import video_ai
import videos
from lessons import LESSON_IDS, LESSONS

BASE = Path(__file__).parent
DB_PATH = BASE / "calclearners.db"
UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB uploads

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
        # A restart kills any lesson that was still being generated.
        conn.execute("UPDATE videos SET status = 'failed', message = ? WHERE status = 'generating'",
                     ("The server restarted while building this lesson. Press Retry.",))
        # Link earlier uploads of a PDF that has a hand-written lesson.
        for upload_id, stored in conn.execute(
                "SELECT id, stored_name FROM uploads WHERE video_id IS NULL AND stored_name LIKE '%.pdf'").fetchall():
            path = UPLOADS / stored
            if path.exists() and (vid := videos.BY_HASH.get(videos.sha256_file(path))):
                conn.execute("UPDATE uploads SET video_id = ? WHERE id = ?", (vid, upload_id))


# ---------- Request helpers ----------
USER_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def current_user():
    """Return the caller's ID from the X-User header, creating the user if new."""
    uid = request.headers.get("X-User", "")
    if not USER_RE.match(uid):
        abort(400, "Missing or invalid X-User header.")
    run("INSERT OR IGNORE INTO users (id) VALUES (?)", (uid,))
    return uid


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
    return jsonify(error=e.description), e.code


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
    return send_from_directory(app.static_folder, "index.html")


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
        last_topic=user["last_topic"] if user["last_topic"] in LESSON_IDS else None,
        done=[r["topic_id"] for r in rows("SELECT topic_id FROM progress WHERE user_id = ?", (uid,))
              if r["topic_id"] in LESSON_IDS],
        quiz=quiz,
        notes=[r["topic_id"] for r in rows(
            "SELECT topic_id FROM notes WHERE user_id = ? AND body != '' AND topic_id NOT LIKE 'video:%'", (uid,))
               if r["topic_id"] in LESSON_IDS],
        streak=streak(uid),
    )


@app.post("/api/me")
def set_name():
    uid = current_user()
    name = str(body().get("name", "")).strip()[:40]
    if BAD_WORDS.search(name):
        abort(400, "Please choose a different name.")
    run("UPDATE users SET name = ? WHERE id = ?", (name, uid))
    return jsonify(name=name)


@app.post("/api/visit")
def visit():
    uid = current_user()
    topic = topic_or_400(body().get("topic"))
    run("UPDATE users SET last_topic = ? WHERE id = ?", (topic, uid))
    mark_active(uid)
    return jsonify(ok=True)


@app.post("/api/progress")
def progress():
    uid = current_user()
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
    for table in ("progress", "quiz_scores", "notes", "activity", "video_progress"):
        run(f"DELETE FROM {table} WHERE user_id = ?", (uid,))
    run("UPDATE users SET last_topic = NULL WHERE id = ?", (uid,))
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
    topic_or_400(topic)
    text = str(body().get("body", ""))[:10000]
    run("""INSERT INTO notes (user_id, topic_id, body) VALUES (?, ?, ?)
           ON CONFLICT (user_id, topic_id) DO UPDATE SET body = excluded.body, updated = CURRENT_TIMESTAMP""",
        (uid, topic, text))
    return jsonify(ok=True)


# ---------- Forum ----------
@app.get("/api/questions")
def list_questions():
    uid = current_user()
    topic = request.args.get("topic", "")
    search = request.args.get("q", "").strip()
    sort = request.args.get("sort", "new")
    like = f"%{search}%"
    qs = rows(f"""
        SELECT q.id, q.author, q.topic_id, q.title, q.body, q.created,
               q.user_id = ? AS mine,
               (SELECT COUNT(*) FROM votes v WHERE v.kind = 'q' AND v.target_id = q.id) AS votes,
               EXISTS (SELECT 1 FROM votes v WHERE v.kind = 'q' AND v.target_id = q.id AND v.user_id = ?) AS voted,
               (SELECT COUNT(*) FROM answers a WHERE a.question_id = q.id) AS answer_count
        FROM questions q
        WHERE (? = '' OR q.topic_id = ?)
          AND (? = '' OR q.title LIKE ? OR q.body LIKE ?)
        {"AND answer_count = 0" if sort == "unanswered" else ""}
        ORDER BY {"votes DESC, q.created DESC" if sort == "top" else "q.created DESC, q.id DESC"}
        LIMIT 100""", (uid, uid, topic, topic, search, like, like))

    ids = [q["id"] for q in qs]
    answers = {}
    if ids:
        marks = ",".join("?" * len(ids))
        for a in rows(f"""
            SELECT a.id, a.question_id, a.author, a.body, a.helpful, a.created,
                   a.user_id = ? AS mine,
                   (SELECT COUNT(*) FROM votes v WHERE v.kind = 'a' AND v.target_id = a.id) AS votes,
                   EXISTS (SELECT 1 FROM votes v WHERE v.kind = 'a' AND v.target_id = a.id AND v.user_id = ?) AS voted
            FROM answers a WHERE a.question_id IN ({marks})
            ORDER BY a.helpful DESC, votes DESC, a.created""", (uid, uid, *ids)):
            answers.setdefault(a["question_id"], []).append(a)
    for q in qs:
        q["answers"] = answers.get(q["id"], [])
    return jsonify(qs)


@app.post("/api/questions")
def ask():
    uid = current_user()
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
    q = one("SELECT user_id FROM questions WHERE id = ?", (qid,)) or abort(404, "Question not found.")
    if q["user_id"] != uid:
        abort(403, "You can only delete your own questions.")
    run("DELETE FROM votes WHERE kind = 'a' AND target_id IN (SELECT id FROM answers WHERE question_id = ?)", (qid,))
    run("DELETE FROM votes WHERE kind = 'q' AND target_id = ?", (qid,))
    run("DELETE FROM questions WHERE id = ?", (qid,))
    return jsonify(ok=True)


@app.post("/api/questions/<int:qid>/answers")
def answer(qid):
    uid = current_user()
    q = one("SELECT title, body FROM questions WHERE id = ?", (qid,)) or abort(404, "Question not found.")
    text = check_answer(q["title"] + " " + q["body"], str(body().get("body", "")))
    run("INSERT INTO answers (question_id, user_id, author, body) VALUES (?, ?, ?, ?)",
        (qid, uid, author_name(uid), text))
    return jsonify(ok=True)


@app.post("/api/answers/<int:aid>/helpful")
def helpful(aid):
    uid = current_user()
    a = one("""SELECT a.helpful, q.user_id AS asker FROM answers a
               JOIN questions q ON q.id = a.question_id WHERE a.id = ?""", (aid,)) or abort(404, "Answer not found.")
    if a["asker"] != uid:
        abort(403, "Only the person who asked can mark an answer as helpful.")
    run("UPDATE answers SET helpful = ? WHERE id = ?", (0 if a["helpful"] else 1, aid))
    return jsonify(ok=True)


@app.post("/api/vote")
def vote():
    uid = current_user()
    data = body()
    kind, target = data.get("kind"), data.get("id")
    table = {"q": "questions", "a": "answers"}.get(kind) or abort(400, "Unknown vote type.")
    post = one(f"SELECT user_id FROM {table} WHERE id = ?", (target,)) or abort(404, "Post not found.")
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
    answers = body().get("answers")
    if not isinstance(answers, list) or not any(str(a[1]).strip() for a in answers if isinstance(a, list) and len(a) == 2):
        abort(400, "Please answer at least one question.")
    run("INSERT INTO feedback (user_id, answers) VALUES (?, ?)", (uid, json.dumps(answers)[:20000]))
    return jsonify(ok=True)


# ---------- Uploads ----------
ALLOWED = {".pdf", ".docx", ".txt", ".doc"}


def extract_text(path):
    """Best-effort text extraction so we can guess which topics a file covers."""
    ext = path.suffix.lower()
    try:
        if ext == ".txt":
            return path.read_text(errors="ignore")
        if ext == ".docx":
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode("utf8", "ignore")
            return re.sub(r"<[^>]+>", " ", xml)
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(path)
            return " ".join((p.extract_text() or "") for p in reader.pages[:30])
    except Exception:
        pass
    return ""


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
    f = request.files.get("file")
    if not f or not f.filename:
        abort(400, "Choose a file first.")
    ext = Path(f.filename).suffix.lower()
    if ext not in ALLOWED:
        abort(400, "Please upload a PDF, Word (.docx) or text file.")
    try:
        style = int(request.form.get("style", 0))
    except ValueError:
        style = 0
    stored = f"{uuid.uuid4().hex}{ext}"
    path = UPLOADS / stored
    f.save(path)

    text = extract_text(path)
    topics = match_topics(text + " " + f.filename)
    video_id = find_or_start_video(path, stored) if ext == ".pdf" else None
    run("INSERT INTO uploads (user_id, filename, stored_name, style, topics, video_id) VALUES (?, ?, ?, ?, ?, ?)",
        (uid, f.filename[:200], stored, style, json.dumps(topics), video_id))
    return jsonify(filename=f.filename, style=style, topics=topics, read_text=bool(text.strip()),
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
    video_or_404(uid, video_id)
    run("""INSERT INTO notes (user_id, topic_id, body) VALUES (?, ?, ?)
           ON CONFLICT (user_id, topic_id) DO UPDATE SET body = excluded.body, updated = CURRENT_TIMESTAMP""",
        (uid, f"video:{video_id}:{episode}", str(body().get("body", ""))[:10000]))
    return jsonify(ok=True)


@app.post("/api/videos/<video_id>/retry")
def retry_video(video_id):
    uid = current_user()
    video_or_404(uid, video_id)
    row = one("SELECT status, source_file FROM videos WHERE id = ?", (video_id,))
    if not row or row["status"] != "failed":
        abort(400, "This lesson isn't in a failed state.")
    if not video_ai.available():
        abort(400, "AI lessons are turned off. Set an ANTHROPIC_API_KEY and restart the server.")
    path = UPLOADS / (row["source_file"] or "")
    if not path.is_file():
        abort(400, "The original file is gone. Upload it again.")
    run("UPDATE videos SET status = 'generating', message = 'Starting…' WHERE id = ?", (video_id,))
    start_generation(video_id, path)
    return jsonify(ok=True)


init_db()

if __name__ == "__main__":
    print("CalcLearners running at http://localhost:5000")
    # "stat" reloader: restart only when an already-loaded file is edited. The default
    # watchdog reloader also restarts when pypdf imports new modules mid-upload,
    # which kills the request.
    app.run(debug=True, port=5000, reloader_type="stat")
