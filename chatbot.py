"""CalcBot: the study helper chat in the corner of every page.

With an Anthropic key (see ai.py) Claude answers, knowing the site's lessons and the
lesson the student has open. Without one, or when the AI can't answer, the reply comes
from the site itself: small talk, how the site works, and the lessons closest to the
question.

Nothing typed into the chat is saved on the server.
"""
import re
from itertools import groupby

import ai
from lessons import LESSONS

MAX_CHARS = 1500   # one message from the student
MAX_TURNS = 16     # how much of the conversation is sent along for context

# Where things are on the site. CalcBot's AI is told all of these; without the AI,
# a message that matches the pattern gets that answer.
SITE = [
    (r"\b(sign ?up|sign ?in|log ?in|account|register|password|saves?|saved|saving|progress|streak)\b",
     "There's no sign-up. Your progress, quiz scores and notes save automatically in this browser, so come "
     "back in the same browser to pick up where you stopped. [My progress](#/dashboard) shows what you've "
     "finished and your streak."),
    (r"\b(formulas?|cheat ?sheet)\b",
     "The [formula sheet](#/formulas) has every formula from the course on one searchable, printable page."),
    (r"\b(videos?|watch|episodes?)\b",
     "[Video lessons](#/videos) are short animated episodes with voiceover and captions. Each one also has a "
     "reading version and practice questions from easy to expert."),
    (r"\b(forum|classmates?|posts?|likes?|dislikes?|report)\b",
     "On the [Q&A forum](#/forum) you can post a question and other learners reply. Likes push the best "
     "questions and replies to the top, and you can sort by most liked, newest, oldest or most replies."),
    (r"\b(quiz|quizzes|practice|hints?)\b",
     "Every lesson ends with practice problems (with hints) and a short quiz. Open any lesson from the "
     "[course page](#/learn)."),
    (r"\b(uploads?|pdf|my notes|own notes)\b",
     "On [Turn notes into videos](#/upload) you can upload your own notes (PDF, Word or text). The site finds "
     "the lessons they match and builds a study plan around them."),
    (r"\b(dark|light|theme|night mode)\b",
     "The moon or sun button at the top of the page switches between light and dark mode. On a phone it's "
     "in the menu."),
    (r"\b(free|costs?|pay|paid|price|subscription|ads?)\b",
     "CalcLearners is free. There's no sign-up, no subscription and no ads on the site."),
    (r"\b(delete|reset|privacy|my data|display name|username|nickname)\b",
     "On [My progress](#/dashboard) you can set the display name shown on your forum posts, reset your "
     "progress, or delete everything saved for this browser."),
    (r"\b(feedback|bugs?|broken|suggestions?)\b",
     "Tell us on the [feedback page](#/feedback). Bug reports and ideas are both welcome."),
    (r"\b(where (do|should) i (start|begin)|get started|what (should|do) i (learn|study|do) (first|next)|"
     r"which lesson|course|syllabus|weeks?)\b",
     f"The [course page](#/learn) lists all {len(LESSONS)} lessons week by week: precalculus review, limits, "
     "derivatives, integrals, differential equations and partial derivatives, plus extra topics. Each lesson "
     "has the big idea, key formulas, a worked example, common mistakes, practice problems and a quiz. The "
     "big button on the home page always points to your next lesson."),
]

STUDY_TIPS = """A plan that works for most people:
1. Take the lesson's quiz first to see what you already know.
2. Read the big idea and the worked example for what you missed. Try to predict each step before you reveal it.
3. Do the practice problems without the hints, then retake the quiz a day or two later.

Short sessions on several days beat one long one. [My progress](#/dashboard) shows which lessons are worth another look."""

HELLO = ("I'm CalcBot. Name a topic you're stuck on, like the chain rule or limits, and I'll point you to the "
         "right lesson. You can also ask how to study or how the site works.")

PAGES = {"home": "the home page", "learn": "the course page", "videos": "the video lessons page",
         "watch": "a video lesson", "formulas": "the formula sheet", "forum": "the Q&A forum",
         "dashboard": "the My progress page", "upload": "the Turn notes into videos page",
         "feedback": "the feedback page"}

RULES = r"""You are CalcBot, the study helper built into CalcLearners, a free website that teaches a 12-week calculus course (Calc 1 to 3 in one) to high school and university students. You are chatting with one student in a small window in the corner of the page.

What you help with
- Any math question: calculus first, and also the algebra, trig and precalculus underneath it, and other math or science homework when asked.
- Studying: how to prepare for a test, what to learn first, how to get unstuck, staying motivated.
- The website: where things are and how they work (see "The site" below).

How to talk
- This is a conversation. Short messages such as "ok", "mhm", "thanks", "good morning", "why?", "why is this", "how did that become that" or "wait what" are normal: answer them naturally, using what was said earlier in the chat and the lesson the student has open. If you can't tell what "this" or "that" refers to, ask a quick question instead of refusing.
- Be warm, encouraging and plain-spoken, like a friendly tutor a few years older. Never make a student feel dumb for asking.
- Keep replies short enough for a small chat window: usually 2 to 6 sentences, or a few short numbered steps for a worked problem. Go longer only when asked.
- When a student is working through a problem, guide them: show the next step or the idea they are missing, and check their thinking. Give the full solution when they ask for it or are clearly stuck.
- If something isn't about math, studying or the site, a friendly line or two is fine, then steer back. Don't write essays, code or other homework that has nothing to do with math; say what you can help with instead.
- Students can be as young as 13, so keep everything appropriate for that age. If someone seems upset or in trouble, be kind and suggest talking to an adult they trust.
- Never ask for personal details such as full names, schools, addresses or contact details, and don't repeat them back.

Formatting
- Write math in LaTeX, with \( ... \) for inline math and \[ ... \] for a formula on its own line. Never use dollar signs for math.
- You may use **bold**, short "- " bullet lists and "1. " numbered lists. No headings, tables or code blocks.
- Link to a lesson or page of the site like this: [Chain Rule](#/learn/chain-rule). Use only the links listed below.

Being right
- Double-check algebra and arithmetic before you answer. If you are not sure, say so.
- When a lesson on the site covers the question, mention it with its link so the student can read more or take its quiz."""


def _unit(l):
    return "Extra topics" if l["unit"] == "Extra" else f"{l['unit']}: {l['unit_title']}"


SYSTEM = "\n\n".join([
    RULES,
    "The site\n" + "\n".join("- " + answer for _, answer in SITE),
    "Lessons (link: name)\n" + "\n".join(
        unit + "\n" + "\n".join(f"- #/learn/{l['id']}: {l['name']}" for l in group)
        for unit, group in groupby(LESSONS, _unit)),
])


def _plain(text):
    """Lesson text marks emphasis with <b> and <i>; the chat uses **bold**."""
    return re.sub(r"</?i>", "", re.sub(r"</?b>", "**", text))


def _lesson_notes(l):
    """A lesson's content as plain text, for the AI."""
    ex = l["example"]
    return _plain("\n".join(
        [f"{l['name']} ({_unit(l)}), link #/learn/{l['id']}", "", "Big idea: " + l["idea"], "", "Key formulas:"]
        + [rf"- {label}: \[{tex}\]" for label, tex in l["formulas"]]
        + ["", "Worked example: " + ex["problem"]]
        + [f"{i}. {step}" for i, step in enumerate(ex["steps"], 1)]
        + ["Answer: " + ex["answer"], "", "Common mistakes:"]
        + ["- " + m for m in l["mistakes"]]))


def clean_history(raw):
    """The conversation as the page sent it, tidied into alternating turns that end on the
    student's message. Returns [] when there is nothing to answer; raises ValueError when
    the newest message is too long."""
    turns, newest = [], 0
    for m in raw if isinstance(raw, list) else []:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant"):
            continue
        text = m.get("content")
        if not isinstance(text, str) or not text.strip():
            continue
        text = text.strip()
        newest = len(text)
        text = text[:6000]  # older turns are only context
        if turns and turns[-1]["role"] == m["role"]:  # two in a row, e.g. after an answer failed
            turns[-1]["content"] += "\n\n" + text
        else:
            turns.append({"role": m["role"], "content": text})
    turns = turns[-MAX_TURNS:]
    while turns and turns[0]["role"] != "user":
        turns.pop(0)
    if not turns or turns[-1]["role"] != "user":
        return []
    if newest > MAX_CHARS:
        raise ValueError(f"That message is too long (max {MAX_CHARS} characters).")
    return turns


# ---------- Answers without the AI ----------
_SKIP = set("""how what why when where who the and for are can you use with does this that from into about
    find get need want know tell show give please help explain mean work have has rule rules""".split())
_INDEX = [(l, set(re.findall(r"[a-z']+", l["name"].lower())), set(re.findall(r"[a-z']+", l["keywords"].lower())))
          for l in LESSONS]


def find_lessons(low):
    """Up to three lessons whose name or keywords share words with the message: [(score, lesson)]."""
    words = {w[:-1] if w.endswith("s") and len(w) > 4 else w for w in re.findall(r"[a-z']{3,}", low)} - _SKIP

    def hit(w, hay):
        return any(h == w or (len(w) >= 4 and h.startswith(w)) for h in hay)

    scored = [(sum(3 if hit(w, name) else 1 if hit(w, keys) else 0 for w in words), l) for l, name, keys in _INDEX]
    return sorted((s for s in scored if s[0]), key=lambda s: -s[0])[:3]  # course order among equals


def _lesson_answer(hits):
    best = hits[0][1]
    reply = (f"**{best['name']}** covers that. {_plain(best['idea'])}\n\n"
             f"[Open the lesson](#/learn/{best['id']}) for the formulas, a worked example and a quiz.")
    more = ", ".join(f"[{l['name']}](#/learn/{l['id']})" for _, l in hits[1:])
    return reply + (f"\n\nRelated: {more}" if more else "")


def basic_reply(text, lesson=None):
    """An answer from the site itself: small talk, how the site works, or the closest lessons."""
    low = re.sub(r"[^a-z0-9']+", " ", text.lower()).strip()
    short = len(low.split()) <= 5
    hello = re.match(r"(hi+|hey+|hello+|yo|sup|hiya|howdy|good (morning|afternoon|evening|day))\b", low)
    if hello and short:
        return (f"Good {hello.group(2)}! " if hello.group(2) else "Hi! ") + HELLO
    if re.match(r"(thanks|thank you|thx|ty|tysm|cheers)\b", low):
        return "You're welcome! Ask me anything else whenever you like."
    if re.match(r"(bye|goodbye|see you|see ya|good night|gn)\b", low):
        return "Good luck with your studying. See you next time!"
    if short and re.match(r"(ok|okay|k|kk|mhm+|hm+|got it|i see|cool|nice|great|alright|sure|yes|yeah|yep|yup|no|"
                          r"nope|lol|haha+|makes sense|oh+|ah+|good|perfect|awesome|right|true)\b", low):
        return "Got it. What would you like to look at next?"
    hits = find_lessons(low)
    if hits and hits[0][0] >= 3:  # the message names a lesson
        return _lesson_answer(hits)
    if re.search(r"\b(who are you|what are you|what can you do|what do you do|your name)\b", low):
        return HELLO
    for pattern, answer in SITE:
        if re.search(pattern, low):
            return answer
    if re.search(r"\b(study|studying|prepare|preparing|prep|exams?|tests?|midterms?|finals?|revise|tips|"
                 r"motivat\w*|procrastinat\w*)\b", low):
        return STUDY_TIPS
    if hits:
        return _lesson_answer(hits)
    if lesson:
        return (f"Here's the big idea of **{lesson['name']}**: {_plain(lesson['idea'])}\n\n"
                "The worked example on the lesson page goes through it step by step. If it still doesn't "
                f"click, ask on the [Q&A forum](#/forum?topic={lesson['id']}).")
    return ("I can only look things up in the lessons right now. Try naming the topic, for example "
            "\"related rates\" or \"u-substitution\", or post your question on the [Q&A forum](#/forum).")


def reply(history, lesson=None, page="", use_ai=True):
    """CalcBot's answer to the last message in `history`. Returns (text, "ai" or "basic")."""
    if use_ai and ai.available():
        # The rules and lesson list never change, so they can be cached; what the student
        # is looking at goes after them.
        system = [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}]
        if lesson:
            system.append({"type": "text", "text": "The student has this lesson open right now, so \"this\" "
                           "or \"that\" probably refers to something in it:\n\n" + _lesson_notes(lesson)})
        elif page in PAGES:
            system.append({"type": "text", "text": f"The student is on {PAGES[page]} right now."})
        try:
            return ai.ask(system, history, max_tokens=3000, timeout=45), "ai"
        except ai.Unavailable:
            pass
    return basic_reply(history[-1]["content"], lesson), "basic"
