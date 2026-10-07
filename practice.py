"""Extra practice for each week of the course, shown on the Practice page.

Every week has sets of questions, one set per topic, and every question has a
worked solution and the name of its type. A set's "lesson" is the id of the
lesson it goes with, if any. A set starts with quick questions (from the
practice_weeks files) and goes on to longer ones at the level of a midterm
(from the practice_more files).
"""
from lessons import WEEK_TITLES
from practice_more_1_6 import MORE_1_6
from practice_more_7_12 import MORE_7_12
from practice_weeks_1_6 import PRACTICE_1_6
from practice_weeks_7_12 import PRACTICE_7_12


def _merge(sets, more):
    """Add the extra sets to a week's own. A set whose title is already there has its
    questions added to that set. A new set goes after the last set for the same lesson,
    or at the end when no set shares its lesson."""
    sets = [dict(s, questions=list(s["questions"])) for s in sets]
    for extra in more:
        same = next((s for s in sets if s["title"] == extra["title"]), None)
        if same:
            same["questions"] += extra["questions"]
            continue
        spots = [i for i, s in enumerate(sets) if extra["lesson"] and s["lesson"] == extra["lesson"]]
        sets.insert(spots[-1] + 1 if spots else len(sets), extra)
    return sets


_QUICK = {**PRACTICE_1_6, **PRACTICE_7_12}
_MORE = {**MORE_1_6, **MORE_7_12}

PRACTICE = [
    {"week": week, "title": WEEK_TITLES[week], "sets": _merge(sets, _MORE.get(week, []))}
    for week, sets in sorted(_QUICK.items())
]
