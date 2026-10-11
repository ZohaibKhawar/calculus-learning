"""A quick check that the site still stands up: every lesson and practice set is well formed,
every page and the main API calls answer, and saved progress follows an account.

Run it:  python tests/test_smoke.py
It works on a copy of the tracked files in a throwaway folder, because starting the server
creates its database next to itself. The real calclearners.db is never opened, and the AI is off.
"""
import os, secrets, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
tmp = Path(tempfile.mkdtemp())
for name in subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n"):
    if name and (ROOT / name).exists():
        (tmp / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, tmp / name)
# Files that are new and not committed yet are part of the site too.
for name in subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n"):
    if name and (ROOT / name).is_file():
        (tmp / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, tmp / name)
os.environ.pop("ANTHROPIC_API_KEY", None)
os.chdir(tmp)
sys.path.insert(0, str(tmp))
import server
from lessons import EXTRA_WEEK, LESSONS, WEEK_TITLES
from practice import PRACTICE

assert Path(server.DB_PATH).parent == tmp, "the test must never open the real database"
server.app.config["SESSION_COOKIE_SECURE"] = False
passed = 0


def ok(cond, what):
    global passed
    assert cond, "FAILED: " + what
    passed += 1


def browser():
    """A visitor with its own cookies. Every request carries the header the page sends."""
    client = server.app.test_client()
    client.environ_base["HTTP_X_REQUESTED_WITH"] = "CalcLearners"
    return client


# ---------- The lessons ----------
ids = [l["id"] for l in LESSONS]
order = {id: i for i, id in enumerate(ids)}
ok(len(ids) == len(set(ids)), "no two lessons share an id")
ok(all(l["week"] in WEEK_TITLES for l in LESSONS), "every lesson is in a week that has a title")
for l in LESSONS:
    here = l["id"]
    ok(l["idea"].strip() and l["formulas"] and l["example"]["steps"] and l["mistakes"], here + " has its idea, formulas, example and mistakes")
    ok(l["example"] in l["examples"], here + " lists its own worked example")
    ok(len(l["practice"]) >= 2 and all(p["q"] and p["a"] for p in l["practice"]), here + " has practice problems with answers")
    ok(len(l["quiz"]) >= 2, here + " has a quiz")
    for q in l["quiz"]:
        ok(len(q["choices"]) == 4 and len(set(q["choices"])) == 4 and 0 <= q["answer"] < 4 and q["why"],
           here + ": a quiz question has four different choices, an answer among them and a reason")
    for p in l["prereqs"]:
        ok(p in order, here + f": the prerequisite {p} exists")
        if l["week"] != EXTRA_WEEK:
            ok(order[p] < order[here], here + f": the prerequisite {p} comes earlier in the course")
    ok(10 <= l["minutes"] <= 60, here + " has a believable length")
    ok(here in server.SEARCH, here + " has a title for its search-engine page")

# ---------- The practice bank ----------
ok([w["week"] for w in PRACTICE] == list(range(1, 13)), "there is practice for each of the 12 weeks")
texts = set()
for week in PRACTICE:
    for s in week["sets"]:
        ok(s["lesson"] is None or s["lesson"] in order, f"Week {week['week']}, {s['title']}: goes with a lesson that exists")
        for q in s["questions"]:
            ok(q["q"] and q["a"] and q["steps"] and q["kind"], f"Week {week['week']}, {s['title']}: a question has steps, an answer and a type")
            ok((week["week"], q["q"]) not in texts, f"Week {week['week']}: no question appears twice ({q['q'][:40]})")
            texts.add((week["week"], q["q"]))

# ---------- Pages ----------
a = browser()
for path in ["/", "/lessons", "/sitemap.xml", "/robots.txt", "/privacy.html", "/terms.html", "/cookies.html",
             "/app.js", "/style.css", "/plot.js", "/start.js"]:
    ok(a.get(path).status_code == 200, path + " answers")
for id in ids:
    r = a.get("/lessons/" + id)
    ok(r.status_code == 200 and b"<h1" in r.data, f"/lessons/{id} answers")
ok(a.get("/lessons/no-such-lesson").status_code == 404, "an unknown lesson is a 404")
ok(all(f"/lessons/{id}<".encode() in a.get("/sitemap.xml").data for id in ids), "the sitemap lists every lesson")

# ---------- The API ----------
ok(len(a.get("/api/lessons").get_json()) == len(LESSONS), "/api/lessons returns every lesson")
ok(len(a.get("/api/practice").get_json()) == 12, "/api/practice returns every week")
ok(server.app.test_client().post("/api/progress", json={"topic": ids[0], "done": True}).status_code == 403,
   "a POST without the page's header is refused")
ok(a.post("/api/progress", json={"topic": ids[0], "done": True}).status_code == 200, "a lesson can be marked done")
ok(a.post("/api/progress", json={"topic": "no-such-lesson", "done": True}).status_code == 400, "an unknown lesson can't be")
ok(a.post("/api/quiz", json={"topic": ids[0], "score": 4, "total": 5}).status_code == 200, "a quiz score is saved")
ok(a.post("/api/quiz", json={"topic": ids[0], "score": 6, "total": 5}).status_code == 400, "an impossible score is refused")
me = a.get("/api/me").get_json()
ok(me["done"] == [ids[0]] and me["quiz"][ids[0]]["best"] == 80 and me["username"] is None, "/api/me reports them")
chat = a.post("/api/chat", json={"messages": [{"role": "user", "content": "what is the chain rule?"}]})
ok(chat.status_code == 200 and chat.get_json()["reply"], "CalcBot answers without the AI")

# ---------- Practice marks ----------
ok(a.get("/api/practice/marks").get_json() == {}, "a new visitor has no practice marks")
ok(a.post("/api/practice/marks", json={"marks": {"4:abc12": 1, "5:zz9": 0}}).status_code == 200, "marks are saved")
ok(a.post("/api/practice/marks", json={"marks": {"5:zz9": None}}).status_code == 200, "a mark can be taken back")
ok(a.get("/api/practice/marks").get_json() == {"4:abc12": 1}, "the saved marks come back")
for bad in [{"marks": {"<script>": 1}}, {"marks": {"4:abc12": 7}}, {"marks": {}}, {"marks": [1]}, {}]:
    ok(a.post("/api/practice/marks", json=bad).status_code == 400, f"bad marks are refused: {bad}")

# ---------- An account carries it all to another browser ----------
username, password = "smoke" + secrets.token_hex(4), secrets.token_urlsafe(16)
ok(a.post("/api/auth/signup", json={"username": username, "password": password}).status_code == 200, "an account can be made")
b = browser()
ok(b.post("/api/practice/marks", json={"marks": {"6:own1": 0}}).status_code == 200, "a second browser saves a mark of its own")
ok(b.post("/api/auth/login", json={"username": username, "password": "not the password"}).status_code == 400, "a wrong password is refused")
ok(b.post("/api/auth/login", json={"username": username, "password": password, "merge": True}).status_code == 200, "the second browser signs in")
ok(b.get("/api/me").get_json()["done"] == [ids[0]], "the second browser sees the lesson that was done")
ok(b.get("/api/practice/marks").get_json() == {"4:abc12": 1, "6:own1": 0}, "and both browsers' practice marks")
ok(b.post("/api/reset").status_code == 200 and b.get("/api/practice/marks").get_json() == {}, "resetting progress clears the marks")

print(f"All {passed} checks passed.")
