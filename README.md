# CalcLearners

A site for learning calculus from zero: a 12-week course (Calc 1–3 in one) with lessons that
explain each idea in plain words, graphs you can move, worked examples, practice and quizzes. Flask + SQLite backend, plain HTML/CSS/JavaScript frontend.

## Features

- **Start here** (`#/start`, `static/start.js`): what calculus is, the algebra it needs and how a
  lesson works, for someone who has never seen it. It offers a skip test for Week 1 (`#/skip/1`):
  two quiz questions per lesson, and 80% completes the week.
- **42 lessons across 12 weeks** (precalc review → limits → derivatives → … → partial
  derivatives and tangent planes), each with the big idea, key formulas, worked examples, common
  mistakes, practice problems and a quiz, plus 16 extra topics beyond the 12 weeks
  (`lessons_weeks_*.py`, `lessons_extra.py`).
- **Lessons that teach** (`lessons_deep.py`): limits and the first derivatives (Weeks 2 and 3) are
  written out in full. The idea is built up in steps, with three worked examples from a warm-up
  to a harder one, worked steps for every practice problem and five quiz questions.
- **Graphs you can move** (`static/plot.js`): a lesson describes a picture as plain data, and a
  tool makes it something to play with: points closing in on a limit, a secant becoming a
  tangent, an epsilon band, Riemann rectangles, Newton's method, a direction field. 27 lessons
  have one.
- **Symbols explained** (`notation.py`): each lesson lists the notation it uses with how to say
  it out loud, flags what is new, and `#/symbols` has all of it.
- **Search that understands beginners** (`lesson_words.py`): whole words, a forgiven typo, and
  the names newcomers use ("rate of change", "max and min").
- **Practice**: questions for every week (28 to 40 each, 70 for Week 4, 436 in all), grouped by lesson and
  labelled by type, each with its answer and a worked solution. A set runs from quick questions
  (`practice_weeks_*.py`) up to midterm level, and each week ends with long exam-style questions
  (`practice_more_*.py`). `practice.py` joins the two. A question can be marked "Got it" or
  "Not yet" once its answer is open, and the page can be narrowed to the ones to retry. The
  marks stay in the browser.
- **Video lessons**: animated episodes with voiceover and captions, a reading version,
  and 18 practice questions per episode (easy → expert), built from a PDF you upload. The
  Videos link shows only when the AI that builds them is switched on, or you already have
  lessons; without it, uploading gives a study plan.
- **Progress tracking** tied to the quizzes, and a **formula sheet** whose formulas stack on a
  phone instead of running off the side (`static/formula.js`).
- **Optional accounts**: nobody has to sign in, but a username and password (no email) lets a learner open
  their progress on another device, and signing in can bring along what that device had saved on its own.
  A recovery code, shown once, resets a forgotten password. The profile page has sign-out everywhere, plus
  changing the username, password or recovery code and deleting the account, which each ask for the current
  password (`accounts.py`, the Accounts section of `server.py`).
- **Q&A forum** with likes (and dislikes on replies only: nobody is marked down for asking), sorting
  (most liked, newest, oldest, most replies) and an automatic check that scores every post from 1 to 10
  in context, so thanks and study tips get through but spam and insults don't (`moderation.py`). Posts
  from a moderator's browser carry a "CalcLearners team" badge.
- **CalcBot**, a study helper chat on every page that answers math, study and site questions (`chatbot.py`).
  It opens as a panel down the side of the screen, a third of its width, or as a small window in the corner.
  With the AI on it also takes a picture of a problem, your notes or the site, types out the question it
  reads there before answering, and turns away pictures of anything else.
- **A page per lesson for search engines** at `/lessons/<id>`, listed in `/sitemap.xml`
  (the app itself lives at one address, which search engines see as a single page).

## Run it

```bash
pip install -r requirements.txt
python server.py
```

Then open http://localhost:5000.

Your progress, forum posts and uploaded files are stored locally in `calclearners.db`
and `uploads/` (both git-ignored).

## Optional AI features

Without a key the site still works: CalcBot answers from the lessons, and the forum check uses built-in rules.

- Put `ANTHROPIC_API_KEY=...` in `secrets.env` (see `secrets.env.example`) and CalcBot's answers and the
  forum check are done by Claude, and CalcBot can look at pictures. Each chat message, picture or post costs
  a little; the daily caps are at the top of the chat and moderation sections in `server.py`.
- Set `ANTHROPIC_API_KEY` as an environment variable before starting the server to also turn newly uploaded
  PDFs into video lessons with Claude.
