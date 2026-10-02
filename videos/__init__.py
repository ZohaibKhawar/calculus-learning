"""Visual video lessons.

Hand-written lessons live in this package and are matched to uploads by the PDF's
SHA-256 fingerprint. Lessons made by the AI generator (video_ai.py) are stored in
the database. Both use the same format; see the SYSTEM prompt in video_ai.py.
"""
import hashlib
import re

from . import chain_rule

BUILTIN = {v["id"]: v for v in [chain_rule.VIDEO]}
BY_HASH = {h: v["id"] for v in BUILTIN.values() for h in v["sha256"]}

LEVELS = {"easy": 5, "intermediate": 5, "advanced": 5, "expert": 3}
SCENE_TYPES = {"title", "equation", "layers", "graph", "cards", "compare", "pause"}
WORDS_PER_SECOND = 2.6


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def episode_seconds(ep):
    words = beats = holds = 0
    for s in ep["scenes"]:
        for b in s["beats"]:
            words += len(b["say"].split())
            beats += 1
        if s["type"] == "pause":
            holds += s.get("seconds", 5)
    return round(words / WORDS_PER_SECOND + beats * 0.3 + holds)


MATH = re.compile(r"\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)")


def read_minutes(ep):
    """Reading time for the episode's article: 200 words a minute plus about 4 seconds per formula.
    Keep in sync with Reader.minutes in static/reader.js."""
    article = ep.get("article") or ""
    if not article:
        return 0
    formulas = len(MATH.findall(article))
    words = len(MATH.sub(" ", article).split())
    return max(1, round(words / 200 + formulas * 4 / 60))


def summary(video):
    """Title and episode list without the heavy scene data."""
    return {
        "title": video["title"],
        "source": video.get("source", ""),
        "episodes": [{"title": e["title"], "hook": e.get("hook", ""), "seconds": episode_seconds(e),
                      "read_minutes": read_minutes(e)} for e in video["episodes"]],
    }


def normalize(video):
    """Clean up a generated lesson: drop broken scenes and questions, enforce counts."""
    episodes = []
    for ep in video.get("episodes") or []:
        if not isinstance(ep, dict):
            continue
        scenes = []
        for s in ep.get("scenes") or []:
            if not isinstance(s, dict) or s.get("type") not in SCENE_TYPES:
                continue
            beats = [{"say": str(b.get("say", "")).strip(), **({"do": str(b["do"])} if b.get("do") else {})}
                     for b in s.get("beats") or [] if isinstance(b, dict) and str(b.get("say", "")).strip()]
            if beats:
                scenes.append({**s, "beats": beats})
        questions = {}
        for level, count in LEVELS.items():
            items = []
            for q in (ep.get("questions") or {}).get(level) or []:
                if not isinstance(q, dict) or not q.get("q"):
                    continue
                if level == "expert":
                    items.append({"q": q["q"], "hint": q.get("hint", ""), "steps": list(q.get("steps") or []),
                                  "answer": q.get("answer", "")})
                else:
                    choices = [str(c) for c in q.get("choices") or []]
                    answer = q.get("answer")
                    if len(choices) >= 2 and isinstance(answer, int) and 0 <= answer < len(choices):
                        items.append({"q": q["q"], "choices": choices, "answer": answer, "why": q.get("why", "")})
            questions[level] = items[:count]
        if scenes:
            episodes.append({"title": str(ep.get("title") or f"Episode {len(episodes) + 1}"),
                             "hook": str(ep.get("hook", "")), "scenes": scenes, "questions": questions,
                             "article": str(ep.get("article") or "")})
    return {"title": str(video.get("title") or "Your lesson"), "source": str(video.get("source", "")),
            "episodes": episodes}
