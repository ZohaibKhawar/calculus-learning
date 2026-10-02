"""Small helpers for writing video lessons by hand.

A beat is "spoken text" or ("spoken text", "action"). See video_ai.py for the format.
"""


def beats(*items):
    return [{"say": i} if isinstance(i, str) else {"say": i[0], "do": i[1]} for i in items]


def title(emoji, text, sub, *b):
    return {"type": "title", "emoji": emoji, "text": text, "sub": sub, "beats": beats(*b)}


def equation(heading, lines, *b):
    return {"type": "equation", "heading": heading, "lines": lines, "beats": beats(*b)}


def layers(heading, rings, result, *b):
    return {"type": "layers", "heading": heading, "result": result, "beats": beats(*b),
            "layers": [{"label": label, "expr": expr, "deriv": deriv} for label, expr, deriv in rings]}


def graph(heading, curves, view, *b):
    return {"type": "graph", "heading": heading, "curves": curves, "view": view, "beats": beats(*b)}


def cards(heading, items, *b):
    return {"type": "cards", "heading": heading, "beats": beats(*b),
            "items": [{"icon": icon, "title": t, "text": text} for icon, t, text in items]}


def compare(heading, left, right, *b):
    return {"type": "compare", "heading": heading, "beats": beats(*b),
            "left": {"title": left[0], "lines": left[1]}, "right": {"title": right[0], "lines": right[1]}}


def pause(question, answer, *b, seconds=5):
    return {"type": "pause", "heading": "Your turn", "question": question, "answer": answer,
            "seconds": seconds, "beats": beats(*b)}


def mc(q, choices, answer, why):
    return {"q": q, "choices": choices, "answer": answer, "why": why}


def expert(q, hint, steps, answer):
    return {"q": q, "hint": hint, "steps": steps, "answer": answer}


def episode(title_, hook, scenes, easy, intermediate, advanced, expert):
    return {"title": title_, "hook": hook, "scenes": scenes,
            "questions": {"easy": easy, "intermediate": intermediate, "advanced": advanced, "expert": expert}}
