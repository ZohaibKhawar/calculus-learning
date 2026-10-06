# CalcLearners

A study site for my 12-week calculus course (Calc 1–3 in one): lessons, quizzes,
animated video lessons, a formula sheet and a Q&A forum. Flask + SQLite backend,
plain HTML/CSS/JavaScript frontend.

## Features

- **42 lessons across 12 weeks** (precalc review → limits → derivatives → … → partial
  derivatives and tangent planes), each with the big idea, key formulas, a worked
  example, common mistakes, practice problems and a quiz, plus extra topics beyond the syllabus.
- **Practice**: extra questions for every week (13 to 15 each, 30 for Week 4, 190 in all), grouped by lesson,
  each with its answer and a worked solution (`practice.py` and the two `practice_weeks_*.py` files).
- **Video lessons**: animated episodes with voiceover and captions, a reading version,
  and 18 practice questions per episode (easy → expert). Your learning style picks
  whether a lesson opens as Watch, Read or Practice.
- **Progress tracking**, a **formula sheet**, and a scroll-animated landing page.
- **Optional accounts**: nobody has to sign in, but a username and password (no email) lets a learner open
  their progress on another device, and signing in can bring along what that device had saved on its own.
  A recovery code, shown once, resets a forgotten password. The profile page has sign-out everywhere, plus
  changing the username, password or recovery code and deleting the account, which each ask for the current
  password (`accounts.py`, the Accounts section of `server.py`).
- **Q&A forum** with likes and dislikes, sorting (most liked, newest, oldest, most replies) and an automatic
  check that scores every post from 1 to 10 in context, so thanks and study tips get through but spam and
  insults don't (`moderation.py`).
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
