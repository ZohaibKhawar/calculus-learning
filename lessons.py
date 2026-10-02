"""All CalcLearners lessons, organized by the 12-week course.

Each lesson gets "week" (1-12, or 13 for extras), "unit" (e.g. "Week 3") and
"unit_title" (e.g. "Derivatives").
"""
from lessons_extra import EXTRA_LESSONS
from lessons_weeks_1_6 import WEEKS_1_6
from lessons_weeks_7_12 import WEEKS_7_12

EXTRA_WEEK = 13
WEEK_TITLES = {
    1: "Precalculus Review",
    2: "Limits",
    3: "Derivatives",
    4: "Inverse, Exponential & Trig Functions",
    5: "Chain & Quotient Rules, Implicit Differentiation, Logarithms",
    6: "Critical Points & Curve Sketching",
    7: "IVT, MVT, Newton's Method & Optimization",
    8: "Antiderivatives, Areas Under Curves & the FTC",
    9: "Substitution, Areas Between Curves & Average Value",
    10: "Differential Equations",
    11: "Direction Fields, Euler's Method & Multivariable Functions",
    12: "Partial Derivatives & Tangent Planes",
    EXTRA_WEEK: "Beyond your syllabus",
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


LESSONS = WEEKS_1_6 + WEEKS_7_12 + [_extra(l) for l in EXTRA_LESSONS]
for _l in LESSONS:
    _l["unit"] = "Extra" if _l["week"] == EXTRA_WEEK else f"Week {_l['week']}"
    _l["unit_title"] = WEEK_TITLES[_l["week"]]

LESSON_IDS = {l["id"] for l in LESSONS}
