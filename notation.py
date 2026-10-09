r"""How to read the symbols.

A lesson that uses a symbol for the first time shouldn't assume the reader has met it. Each
entry here is (pattern, symbol in LaTeX, how to say it, what it means). The pattern is a regular
expression looked for in the LaTeX of a lesson: lessons.py gives each lesson a "symbols" list
of the ones it uses, each marked as new when no earlier lesson in the course has used it.
The whole list is also a page of its own on the site.
"""
import re

SYMBOLS = [
    (r"\\to\b", r"x \to a", "x approaches a",
     "x gets closer and closer to a. It doesn't have to reach it."),
    (r"\\lim", r"\lim_{x\to a} f(x)", "the limit of f of x as x approaches a",
     "The value f(x) heads toward as x gets close to a. What happens at a itself doesn't matter."),
    (r"\\to\s*-?\w+\^\{?[-+]", r"x \to a^- \quad x \to a^+", "x approaches a from the left, from the right",
     "The little minus means through values below a; the little plus means through values above a."),
    (r"\\infty", r"\infty", "infinity",
     "Not a number. It says a quantity grows without any bound."),
    (r"\|", r"|x|", "the absolute value of x",
     "The distance from x to 0, so it is never negative. In the same way |x - a| is the distance from x to a."),
    (r"\\ne\b", r"\ne", "is not equal to", "The two sides are different."),
    (r"\\approx", r"\approx", "is approximately", "Close to, after rounding."),
    (r"\\pm", r"\pm", "plus or minus", "Two answers at once: one with plus and one with minus."),
    (r"\\Rightarrow", r"\Rightarrow", "implies", "If what is on the left is true, then so is what is on the right."),
    (r"\\iff", r"\iff", "if and only if", "Each side is true exactly when the other one is."),
    (r"\\varepsilon", r"\varepsilon", "epsilon",
     "A small positive distance on the output side: how close f(x) has to be to L."),
    (r"\\delta", r"\delta", "delta",
     "A small positive distance on the input side: how close x has to stay to a."),
    (r"\\forall", r"\forall", "for all", "The statement after it holds for every value, with no exceptions."),
    (r"\\exists", r"\exists", "there exists", "At least one value can be found that makes the statement true."),
    (r"\\in\b", r"c \in (a, b)", "c is in the interval from a to b",
     "c is one of the numbers strictly between a and b. Square brackets, as in [a, b], include the two ends."),
    (r"(?<![a-zA-Z])[fgyh]'(?![a-zA-Z'])", r"f'(x)", "f prime of x",
     "The derivative of f: its slope, or rate of change, at x. For y = f(x) it is also written y'."),
    (r"\\d?frac\{d\}\{dx\}", r"\frac{d}{dx}", "d by d x of",
     "An instruction: take the derivative, with respect to x, of whatever comes next."),
    (r"\\d?frac\{dy\}\{dx\}", r"\frac{dy}{dx}", "d y by d x",
     "The derivative of y with respect to x. It means the same as y' and is one symbol, not a fraction to cancel."),
    (r"(?<![a-zA-Z])[fgy]''", r"f''(x)", "f double prime of x",
     "The second derivative: the derivative of the derivative. It measures how the slope itself is changing."),
    (r"f\^\{-1\}", r"f^{-1}(x)", "f inverse of x",
     "The function that undoes f. It is not 1 divided by f."),
    (r"\\ln\b", r"\ln x", "the natural log of x", "The power you raise e to in order to get x."),
    (r"\\log_", r"\log_b x", "log base b of x", "The power you raise b to in order to get x."),
    (r"\\Delta", r"\Delta x", "delta x", "A change in x, usually one small step along the x-axis."),
    (r"\\sum", r"\sum_{i=1}^{n} a_i", "the sum of a i, for i from 1 to n",
     "Add up the terms a_1, a_2 and so on, as far as a_n."),
    (r"\\int(?!_)", r"\int f(x)\,dx", "the integral of f of x, d x",
     "Every function whose derivative is f. The dx names the variable."),
    (r"\\int_", r"\int_a^b f(x)\,dx", "the integral from a to b of f of x, d x",
     "The area between the graph of f and the x-axis from a to b, with area below the axis counted as negative."),
    (r"\\partial", r"\frac{\partial f}{\partial x}", "partial f, partial x",
     "The derivative of f with respect to x while every other variable is held fixed. Also written f_x."),
    (r"\\mathbb\{R\}", r"\mathbb{R}", "the real numbers", "Every number on the number line."),
    (r"\\langle", r"\langle a, b, c \rangle", "the vector a, b, c",
     "An arrow with those three components: how far it goes in each direction."),
    (r"\\nabla", r"\nabla f", "grad f, the gradient of f",
     "The vector made of all the partial derivatives of f. It points in the direction of steepest increase."),
    (r"\\iint", r"\iint_R f\,dA", "the double integral of f over R",
     "The volume between the surface z = f(x, y) and the region R."),
    (r"\\oint", r"\oint_C", "the integral around the closed curve C",
     "A line integral whose path ends where it started."),
]

_COMPILED = [(re.compile(pattern), tex, say, meaning) for pattern, tex, say, meaning in SYMBOLS]


def _latex(lesson):
    """Every piece of a lesson that can hold math, as one string."""
    parts = [lesson["idea"], lesson["example"]["problem"], lesson["example"]["answer"]]
    parts += lesson["example"]["steps"] + lesson["mistakes"]
    parts += [tex for _, tex in lesson["formulas"]] + [label for label, _ in lesson["formulas"]]
    for block in lesson.get("learn", []):
        parts.append(block.get("body", ""))
    return " ".join(parts)


def add_symbols(lessons):
    """Give each lesson "symbols": [latex, how to say it, meaning, new here?], in the order of SYMBOLS."""
    seen = set()
    for lesson in lessons:
        text = _latex(lesson)
        found = [(tex, say, meaning) for pattern, tex, say, meaning in _COMPILED if pattern.search(text)]
        lesson["symbols"] = [[tex, say, meaning, tex not in seen] for tex, say, meaning in found]
        seen.update(tex for tex, _, _ in found)


ALL_SYMBOLS = [[tex, say, meaning] for _, tex, say, meaning in SYMBOLS]