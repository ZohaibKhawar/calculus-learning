r"""Helpers for writing lessons.

Math is written in LaTeX: \( ... \) for inline math. Formulas are listed as
[label, latex] and are shown as display math by the website.
Avoid a bare "<" in text (it breaks HTML); use \lt inside math instead.
"""


def lesson(id, week, name, keywords, level, minutes, prereqs, idea,
           formulas, example, mistakes, practice, quiz):
    return {
        "id": id, "week": week, "name": name, "keywords": keywords,
        "level": level, "minutes": minutes, "prereqs": prereqs, "idea": idea,
        "formulas": formulas, "example": example, "mistakes": mistakes,
        "practice": practice, "quiz": quiz,
    }


def ex(problem, steps, answer):
    return {"problem": problem, "steps": steps, "answer": answer}


def pr(q, hint, a):
    return {"q": q, "hint": hint, "a": a}


def mc(q, choices, answer, why):
    return {"q": q, "choices": choices, "answer": answer, "why": why}


def pset(title, lesson, questions):
    return {"title": title, "lesson": lesson, "questions": questions}


def pq(q, steps, a):
    return {"q": q, "steps": steps, "a": a}
