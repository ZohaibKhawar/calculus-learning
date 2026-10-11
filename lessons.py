"""All CalcLearners lessons, organized by the 12-week course.

Each lesson gets "week" (1-12, or 13 for extras), "unit" (e.g. "Week 3"),
"unit_title" (e.g. "Derivatives") and "also" (other things people call the topic,
which the site's search matches). The teaching material from lessons_deep.py is merged
in: "learn" (explanations and pictures), "examples" (every worked example, easiest
first), worked "steps" on practice problems and extra quiz questions. "symbols" lists
the notation a lesson uses, with how to read it (notation.py).
"""
from lesson_words import EVERYDAY
from lessons_deep import DEEP
from lessons_extra import EXTRA_LESSONS
from lessons_weeks_1_6 import WEEKS_1_6
from lessons_weeks_7_12 import WEEKS_7_12
from notation import add_symbols
from search_terms import SEARCH

EXTRA_WEEK = 13
WEEK_TITLES = {
    1: "Precalculus Review",
    2: "Limits",
    3: "Derivatives",
    4: "Inverse, Exponential & Trig Functions, Quotient Rule",
    5: "Chain Rule, Implicit Differentiation & Logarithms",
    6: "Critical Points & Curve Sketching",
    7: "IVT, MVT, Newton's Method & Optimization",
    8: "Antiderivatives, Areas Under Curves & the FTC",
    9: "Substitution, Areas Between Curves & Average Value",
    10: "Differential Equations",
    11: "Direction Fields, Euler's Method & Multivariable Functions",
    12: "Partial Derivatives & Tangent Planes",
    EXTRA_WEEK: "Beyond the 12 weeks",
}

# Old prerequisite ids that were split or renamed in the 12-week layout.
_RENAMED = {"riemann-ftc": "ftc", "partial-gradient": "partial-derivatives"}


def _extra(lesson):
    lesson = {k: v for k, v in lesson.items() if k != "course"}
    lesson["week"] = EXTRA_WEEK
    lesson["prereqs"] = [_RENAMED.get(p, p) for p in lesson["prereqs"]]
    if lesson["id"] == "partial-gradient":  # partials now have their own Week 12 lesson
        lesson["name"] = "Gradient & Directional Derivatives"
        lesson["prereqs"] = ["partial-derivatives"]
    return lesson


def _minutes(lesson):
    """About how long a lesson takes, worked out from what is in it, so that a short lesson
    doesn't claim to be a long one: reading speed for the text, and a few minutes for each
    worked example, practice problem and quiz question. Rounded to five minutes."""
    words = len(lesson["idea"].split()) + sum(len((b["body"] + b.get("cap", "")).split()) for b in lesson["learn"])
    minutes = words / 120 + 2 + 3 * len(lesson["examples"]) + 2 * len(lesson["practice"]) + len(lesson["quiz"])
    return max(10, 5 * round(minutes / 5))


def _deepen(lesson):
    """Merge in what lessons_deep.py has for this lesson."""
    more = DEEP.get(lesson["id"], {})
    if "example" in more:
        lesson["example"] = more["example"]
    lesson["learn"] = more.get("learn", [])
    lesson["examples"] = [lesson["example"] if e == "main" else e for e in more.get("examples", ["main"])]
    for i, steps in more.get("steps", {}).items():
        lesson["practice"][i]["steps"] = steps
    lesson["quiz"] = lesson["quiz"] + more.get("quiz", [])


LESSONS = WEEKS_1_6 + WEEKS_7_12 + [_extra(l) for l in EXTRA_LESSONS]
for _l in LESSONS:
    _l["unit"] = "Extra" if _l["week"] == EXTRA_WEEK else f"Week {_l['week']}"
    _l["unit_title"] = WEEK_TITLES[_l["week"]]
    _l["also"] = EVERYDAY.get(_l["id"], []) + SEARCH.get(_l["id"], ("", []))[1]
    _deepen(_l)
    _l["minutes"] = _minutes(_l)
add_symbols(LESSONS)

LESSON_IDS = {l["id"] for l in LESSONS}
