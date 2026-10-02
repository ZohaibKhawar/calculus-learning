# CalcLearners

A study site for my 12-week calculus course (Calc 1–3 in one): lessons, quizzes,
animated video lessons, a formula sheet and a Q&A forum. Flask + SQLite backend,
plain HTML/CSS/JavaScript frontend.

## Features

- **42 lessons across 12 weeks** (precalc review → limits → derivatives → … → partial
  derivatives and tangent planes), each with the big idea, key formulas, a worked
  example, common mistakes, practice problems and a quiz, plus extra topics beyond the syllabus.
- **Video lessons**: animated episodes with voiceover and captions, a reading version,
  and 18 practice questions per episode (easy → expert). Your learning style picks
  whether a lesson opens as Watch, Read or Practice.
- **Progress tracking**, a **formula sheet**, a moderated **Q&A forum**, and a scroll-animated landing page.

## Run it

```bash
pip install -r requirements.txt
python server.py
```

Then open http://localhost:5000.

Your progress, forum posts and uploaded files are stored locally in `calclearners.db`
and `uploads/` (both git-ignored).

Optional: set `ANTHROPIC_API_KEY` before starting the server to turn newly uploaded PDFs
into video lessons with Claude.
