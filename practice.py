"""Extra practice for each week of the course, shown on the Practice page.

Every week has sets of questions, one set per topic, and every question has a
worked solution. A set's "lesson" is the id of the lesson it goes with, if any.
"""
from lessons import WEEK_TITLES
from practice_weeks_1_6 import PRACTICE_1_6
from practice_weeks_7_12 import PRACTICE_7_12

PRACTICE = [
    {"week": week, "title": WEEK_TITLES[week], "sets": sets}
    for week, sets in sorted({**PRACTICE_1_6, **PRACTICE_7_12}.items())
]
