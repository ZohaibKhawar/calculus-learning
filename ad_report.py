"""How the visitors each ad brought used the site.

Run it next to the database:
    python ad_report.py

Lesson links in an ad end in ?utm_source=google, and server.py saves that word with each new
visitor the ad brings (see note_visit). The "(no ad)" row is everyone else who has a visitor ID.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "calclearners.db"

COLUMNS = ["Source", "Visitors", "Opened a lesson in the app", "Finished a lesson or quiz", "Came back another day"]
REPORT = """
SELECT COALESCE(source, '(no ad)'),
       COUNT(*),
       SUM(EXISTS (SELECT 1 FROM activity WHERE user_id = users.id)),
       SUM(EXISTS (SELECT 1 FROM progress WHERE user_id = users.id)
           OR EXISTS (SELECT 1 FROM quiz_scores WHERE user_id = users.id)),
       SUM(COALESCE(last_seen > date(created, 'localtime'), 0))
FROM users GROUP BY source ORDER BY source IS NULL, source
"""

if __name__ == "__main__":
    with sqlite3.connect(DB_PATH) as conn:
        found = conn.execute(REPORT).fetchall()
    for row in [COLUMNS] + found:
        print("  ".join(str(cell).ljust(len(title)) for cell, title in zip(row, COLUMNS)))
