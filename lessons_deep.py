r"""The teaching part of the lessons: explanations from zero, pictures, more examples.

The lesson files (lessons_weeks_*.py) hold each topic's summary: one paragraph, the formulas, one
worked example. That is enough to revise from and not enough to learn from. DEEP adds, per lesson:

  "learn"     a list of blocks, each {"h": heading, "body": HTML, "fig": picture, "cap": caption}.
              They explain the idea in plain words, one step at a time. A picture is data for
              static/plot.js (its header lists what a picture can hold).
  "example"   replaces the lesson's worked example, when the original assumed too much.
  "examples"  the worked examples in order, easiest first. "main" stands for the lesson's own.
  "steps"     worked solutions for the lesson's practice problems, by position (0, 1, 2).
  "quiz"      extra quiz questions, added after the lesson's own.

lessons.py merges all of this into the lessons. Weeks 2 and 3 (limits and the first derivatives)
are written out in full, because that is where calculus starts and where beginners get lost. So
are the rules a midterm leans on: the quotient rule, the derivatives of e^x and a^x, the chain
rule, implicit differentiation, the Fundamental Theorem and substitution.
Other lessons have a picture where the topic is one.
"""
from lesson_helpers import ex, mc


def block(h, body, fig=None, cap=""):
    b = {"h": h, "body": body}
    if fig:
        b["fig"] = fig
        b["cap"] = cap
    return b


def picture(fig, cap, h="See it"):
    """A lesson whose only addition is a picture."""
    return {"learn": [block(h, "", fig, cap)]}


DEEP = {
    # ============================ WEEK 1 ============================
    "review-factoring": {
        "learn": [
            block(r"When the \(x^2\) has a number in front",
                  r"""<p>The trinomial formula above only covers \(x^2 + bx + c\). For \(ax^2 + bx + c\) with a number
                  \(a\) in front, use the <b>ac method</b>:</p>
                  <ol><li>Find two numbers that multiply to \(a \cdot c\) and add to \(b\).</li>
                  <li>Use them to split the middle term into two terms.</li>
                  <li>Factor the first pair and the last pair. The same bracket appears twice: pull it out.</li></ol>
                  <p>Take \(2x^2 + 7x + 3\). Here \(a \cdot c = 6\) and \(b = 7\), and the numbers are \(6\) and \(1\).
                  Split the middle: \(2x^2 + 6x + x + 3\). Factor in pairs: \(2x(x + 3) + 1(x + 3)\). The bracket
                  \((x + 3)\) is common to both, so the answer is \((x + 3)(2x + 1)\).</p>"""),
        ],
        "steps": {
            1: [r"The \(x^2\) has a 6 in front, so use the ac method: \(a \cdot c = 6 \cdot (-2) = -12\) and \(b = 1\).",
                r"Two numbers that multiply to \(-12\) and add to \(1\): \(4\) and \(-3\).",
                r"Split the middle term: \(6x^2 + 4x - 3x - 2\).",
                r"Factor in pairs: \(2x(3x + 2) - 1(3x + 2)\). The bracket \((3x + 2)\) is common: \((3x + 2)(2x - 1)\)."],
        },
    },
    "review-graphing": {
        "learn": [
            block("See it: sliding and stretching a parabola",
                  r"""<p>Every parabola is the basic one, \(y = x^2\), moved or stretched. In \(y = a(x - h)^2 + k\) the
                  letter \(h\) slides it sideways, \(k\) slides it up or down, and \(a\) stretches it (a negative \(a\)
                  flips it over). The lowest or highest point, the <b>vertex</b>, always lands at \((h, k)\).</p>""",
                  {"view": [-6, 6, -5, 9], "alt": "A parabola you can shift and stretch with three sliders, beside the basic parabola y equals x squared",
                   "curves": [{"f": "a*(x-h)^2+k"}, {"f": "x^2", "style": "dash"}],
                   "tool": {"type": "family", "params": {"a": [-2, 2, 1, 0.25], "h": [-4, 4, 2, 0.5], "k": [-4, 6, -1, 0.5]},
                            "read": "y = {a}(x − {h})² + {k}, with its vertex at ({h}, {k})"}},
                  r"The dashed curve is \(y = x^2\). Notice that \(h = 2\) moves the parabola 2 to the <b>right</b>, even though the formula says \(x - 2\)."),
        ],
    },

    # ============================ WEEK 2: LIMITS ============================
    "limits": {
        "learn": [
            block("Start here: the question a limit answers",
                  r"""<p>Take the recipe \(f(x) = \dfrac{x^2 - 1}{x - 1}\). Feed it \(x = 1\) and you get \(\frac00\), which is
                  not a number. The recipe has no value at exactly 1.</p>
                  <p>Nothing stops you getting <b>close</b> to 1, though. Feed it 0.9, then 0.99, then 0.999, and out
                  come 1.9, 1.99, 1.999. From the other side, 1.1, 1.01 and 1.001 give 2.1, 2.01, 2.001. Both sides
                  are closing in on 2.</p>
                  <p>That target is the <b>limit</b>. We write \(\displaystyle\lim_{x\to 1} f(x) = 2\) and say "the limit
                  of \(f(x)\) as \(x\) approaches 1 is 2". A limit is about where the outputs are <b>heading</b>, never
                  about what happens at the point itself.</p>""",
                  {"view": [-1, 3, -0.5, 4], "alt": "The line y equals x plus 1 with a hole at the point 1, 2, and two points that close in on the hole from each side",
                   "curves": [{"f": "(x^2-1)/(x-1)"}], "points": [{"at": [1, 2], "open": True, "label": "hole at (1, 2)", "pos": "se"}],
                   "tool": {"type": "approach", "a": 1}},
                  r"Move the slider to send both points toward \(x = 1\). The graph has a hole there, and the heights still close in on 2."),
            block("Two ways to find one",
                  r"""<ul><li><b>With a table.</b> Pick \(x\)-values that close in on \(a\) from the left and from the right,
                  work out \(f(x)\) for each, and see what the outputs approach.</li>
                  <li><b>With a graph.</b> Put a finger on the curve to the left of \(a\) and slide toward \(a\). The height
                  you are heading for is the <b>left-hand limit</b>, written \(\displaystyle\lim_{x\to a^-} f(x)\). Do the
                  same from the right for the <b>right-hand limit</b>, \(\displaystyle\lim_{x\to a^+} f(x)\).</li></ul>
                  <p>If both sides head for the same height, that height is the limit. If they head for different
                  heights, the limit <b>does not exist</b>.</p>""",
                  {"view": [-1, 5, -0.5, 4.5], "alt": "A graph in two pieces that end at different heights where x is 2",
                   "curves": [{"f": "x+1", "dom": [-1, 2]}, {"f": "0.5*x", "dom": [2, 5]}],
                   "points": [{"at": [2, 3], "open": True}, {"at": [2, 1]}],
                   "tool": {"type": "approach", "a": 2, "left": "x+1", "right": "0.5*x", "max": 1.5}},
                  r"Here the left side heads for 3 and the right side heads for 1. They disagree, so the limit at \(x = 2\) does not exist."),
            block("The limit ignores the point itself",
                  r"""<p>A function can be undefined at \(a\), or have some unrelated value there, and the limit doesn't care.
                  In the first picture \(f(1)\) doesn't exist and the limit is still 2. So never assume that
                  \(\displaystyle\lim_{x\to a} f(x)\) is the same as \(f(a)\). It is for some functions (the continuous
                  ones, later this week) and not for others.</p>"""),
        ],
        "example": ex(r"Estimate \(\displaystyle\lim_{x\to 0}\frac{\sin x}{x}\) with a table (calculator in radians).",
                      [r"Close in from the right. \(x = 0.1\): \(\dfrac{\sin 0.1}{0.1} \approx 0.99833\).",
                       r"\(x = 0.01\): \(\approx 0.99998\). The outputs are climbing toward 1.",
                       r"Now from the left. \(x = -0.1\): \(\dfrac{\sin(-0.1)}{-0.1} = \dfrac{-0.09983}{-0.1} \approx 0.99833\), and \(x = -0.01\) gives \(\approx 0.99998\) again.",
                       r"Both sides are closing in on 1, even though \(f(0) = \frac00\) is undefined."],
                      r"\(1\)"),
        "examples": [
            ex(r"Use a table to estimate \(\displaystyle\lim_{x\to 2}(3x + 1)\).",
               [r"From the left: \(x = 1.9\) gives \(6.7\), \(x = 1.99\) gives \(6.97\), \(x = 1.999\) gives \(6.997\).",
                r"From the right: \(x = 2.1\) gives \(7.3\), \(x = 2.01\) gives \(7.03\), \(x = 2.001\) gives \(7.003\).",
                r"Both sides close in on 7. (Here \(f(2) = 7\) as well, so plugging in would have worked. The next lesson says when that is allowed.)"],
               r"\(7\)"),
            "main",
            ex(r"For \(f(x) = \begin{cases} x^2 & x \lt 1 \\ 3 & x = 1 \\ 2 - x & x \gt 1 \end{cases}\) find \(\displaystyle\lim_{x\to 1^-} f(x)\), \(\displaystyle\lim_{x\to 1^+} f(x)\), \(\displaystyle\lim_{x\to 1} f(x)\) and \(f(1)\).",
               [r"Left of 1 the rule is \(x^2\). As \(x\) climbs toward 1, \(x^2\) heads for \(1\). So \(\displaystyle\lim_{x\to 1^-} f(x) = 1\).",
                r"Right of 1 the rule is \(2 - x\). As \(x\) drops toward 1, \(2 - x\) heads for \(1\). So \(\displaystyle\lim_{x\to 1^+} f(x) = 1\).",
                r"The two sides agree, so \(\displaystyle\lim_{x\to 1} f(x) = 1\).",
                r"The value at the point comes from the middle rule: \(f(1) = 3\). It differs from the limit, and that is allowed."],
               r"Both one-sided limits are 1, so the limit is 1, while \(f(1) = 3\)"),
        ],
        "steps": {
            0: [r"From the left use \(x + 1\): as \(x \to 2^-\) it heads for \(2 + 1 = 3\).",
                r"From the right use \(5 - x\): as \(x \to 2^+\) it heads for \(5 - 2 = 3\).",
                "Both sides agree, so the limit is 3."],
            1: [r"\(x = 0.9\): \(\dfrac{0.81 - 1}{0.9 - 1} = \dfrac{-0.19}{-0.1} = 1.9\). In the same way \(x = 0.99\) gives \(1.99\).",
                r"\(x = 1.1\): \(\dfrac{1.21 - 1}{0.1} = 2.1\), and \(x = 1.01\) gives \(2.01\).",
                "Both sides close in on 2."],
            2: [r"For \(x \lt 0\), \(|x| = -x\), so \(\dfrac{|x|}{x} = \dfrac{-x}{x} = -1\). The left-hand limit is \(-1\).",
                r"For \(x \gt 0\), \(|x| = x\), so the fraction is \(1\). The right-hand limit is \(1\).",
                r"\(-1 \ne 1\), so the limit does not exist."],
        },
        "quiz": [
            mc(r"A table gives \(f(2.9) = 5.8\), \(f(2.99) = 5.98\), \(f(3.01) = 6.02\) and \(f(3.1) = 6.2\). The best estimate of \(\displaystyle\lim_{x\to 3} f(x)\) is:",
               ["5.8", "6", "6.2", "3"], 1, "From both sides the outputs close in on 6."),
            mc(r"\(\displaystyle\lim_{x\to 4^-} f(x) = 7\) and \(\displaystyle\lim_{x\to 4^+} f(x) = 7\), but \(f(4) = 10\). Then \(\displaystyle\lim_{x\to 4} f(x)\) is:",
               ["10", "7", "8.5", "does not exist"], 1, "Both sides agree on 7. The value at the point doesn't matter."),
        ],
    },
    "limits-algebraic": {
        "learn": [
            block("First move: just plug in",
                  r"""<p>For the functions you meet most (polynomials, roots, fractions of polynomials, sine and cosine), the
                  outputs near \(a\) head exactly where you would expect: to \(f(a)\). So the first thing to try is always
                  <b>direct substitution</b>: replace \(x\) with \(a\) and work it out.</p>
                  <p>If a real number comes out, you are done. For example
                  \(\displaystyle\lim_{x\to 2}(x^2 + 3x) = 4 + 6 = 10\).</p>"""),
            block(r"When plugging in gives \(\frac00\)",
                  r"""<p>\(\frac00\) is not an answer. It is a signal that the top and the bottom are both heading for zero and
                  you can't yet see which one wins. It is called an <b>indeterminate form</b>, and it means: do some
                  algebra, then plug in again.</p>
                  <ul><li><b>Factor and cancel</b> when both parts are polynomials. Getting \(\frac00\) at \(x = a\) means
                  \((x - a)\) is a factor of both.</li>
                  <li><b>Multiply by the conjugate</b> when there is a square root. The conjugate of \(\sqrt{x} - 2\) is
                  \(\sqrt{x} + 2\).</li>
                  <li><b>Combine into one fraction</b> when there are fractions inside a fraction.</li></ul>
                  <p>Cancelling is legal because a limit only looks at \(x\) <b>near</b> \(a\), where \(x - a\) is not zero.</p>""",
                  {"view": [-1, 6, -1, 10], "alt": "The line y equals x plus 3 with a hole at the point 3, 6",
                   "curves": [{"f": "(x^2-9)/(x-3)"}], "points": [{"at": [3, 6], "open": True, "label": "hole at (3, 6)", "pos": "se"}],
                   "tool": {"type": "approach", "a": 3, "max": 2}},
                  r"\(\dfrac{x^2 - 9}{x - 3}\) is the line \(y = x + 3\) with one point missing. Cancelling the common factor finds the height of the hole."),
            block("When plugging in gives a number over 0",
                  r"""<p>Something like \(\frac{5}{0}\) is a different case: the top stays away from zero while the bottom
                  shrinks, so the outputs blow up. The limit is \(\infty\), \(-\infty\) or does not exist, and the graph
                  has a vertical asymptote. Don't try to cancel anything. That case is the next lesson.</p>"""),
        ],
        "examples": [
            ex(r"Find \(\displaystyle\lim_{x\to 2}\dfrac{x^2 + 1}{x + 3}\).",
               [r"Try direct substitution: the top is \(2^2 + 1 = 5\) and the bottom is \(2 + 3 = 5\).",
                r"The bottom is not zero, so there is nothing to fix. The limit is \(\frac55\)."],
               r"\(1\)"),
            "main",
            ex(r"Find \(\displaystyle\lim_{x\to 9}\dfrac{\sqrt{x} - 3}{x - 9}\).",
               [r"Substitute: \(\dfrac{3 - 3}{9 - 9} = \dfrac00\). Indeterminate, and there is a root, so use the conjugate.",
                r"Multiply top and bottom by \(\sqrt{x} + 3\). The top becomes \((\sqrt{x})^2 - 3^2 = x - 9\).",
                r"Now you have \(\dfrac{x - 9}{(x - 9)(\sqrt{x} + 3)}\). Cancel \(x - 9\) to get \(\dfrac{1}{\sqrt{x} + 3}\).",
                r"Substitute again: \(\dfrac{1}{3 + 3}\)."],
               r"\(\dfrac16\)"),
        ],
        "steps": {
            0: [r"Substituting gives \(\dfrac{2 - 2}{0} = \dfrac00\), so multiply top and bottom by the conjugate \(\sqrt{x + 4} + 2\).",
                r"The top becomes \((x + 4) - 4 = x\), which gives \(\dfrac{x}{x(\sqrt{x + 4} + 2)}\).",
                r"Cancel \(x\): \(\dfrac{1}{\sqrt{x + 4} + 2}\). At \(x = 0\) this is \(\dfrac{1}{2 + 2} = \dfrac14\)."],
            1: [r"Substituting gives \(\frac00\). Combine the top over the common denominator \(2x\): \(\dfrac1x - \dfrac12 = \dfrac{2 - x}{2x}\).",
                r"Dividing by \(x - 2\) gives \(\dfrac{2 - x}{2x(x - 2)}\). Since \(2 - x = -(x - 2)\), this cancels to \(-\dfrac{1}{2x}\).",
                r"At \(x = 2\): \(-\dfrac14\)."],
            2: [r"\(\sin\frac1x\) always lies between \(-1\) and \(1\). Multiply through by \(x^2\), which is never negative: \(-x^2 \le x^2\sin\frac1x \le x^2\).",
                r"As \(x \to 0\), both \(-x^2\) and \(x^2\) head for 0.",
                "The function is trapped between them, so by the squeeze theorem its limit is 0 as well."],
        },
        "quiz": [
            mc(r"Direct substitution in \(\displaystyle\lim_{x\to 5}\frac{x^2 - 25}{x - 5}\) gives \(\frac00\). That means:",
               ["the limit is 0", "the limit does not exist", "simplify first, then substitute again", "the limit is 1"], 2,
               r"\(\frac00\) is indeterminate. Here factoring leaves \(x + 5\), which heads for 10."),
            mc(r"\(\displaystyle\lim_{x\to 3}(x^2 - 2x + 1) =\)", ["4", "1", "16", "0"], 0,
               r"A polynomial, so substitute: \(9 - 6 + 1 = 4\)."),
        ],
    },
    "limits-infinity": {
        "learn": [
            block("Two different questions with infinity in them",
                  r"""<p>\(\infty\) is not a number you can plug in. It is shorthand for "growing without any bound".</p>
                  <ul><li><b>Limits at infinity</b> ask what the outputs do as \(x\) gets huge:
                  \(\displaystyle\lim_{x\to\infty} f(x)\). If they settle toward a number \(L\), the graph flattens out
                  along the horizontal line \(y = L\), a <b>horizontal asymptote</b>.</li>
                  <li><b>Infinite limits</b> ask what happens near a point where the outputs blow up:
                  \(\displaystyle\lim_{x\to a} f(x) = \infty\). The graph shoots up or down along the vertical line
                  \(x = a\), a <b>vertical asymptote</b>.</li></ul>""",
                  {"view": [-6, 10, -6, 10], "alt": "The graph of 2x plus 1 over x minus 1, with a horizontal asymptote at y equals 2 and a vertical asymptote at x equals 1",
                   "curves": [{"f": "(2*x+1)/(x-1)"}], "hlines": [2], "vlines": [1],
                   "labels": [{"at": [6.3, 2], "text": "y = 2", "pos": "s"}, {"at": [1, -4.6], "text": "x = 1", "pos": "e"}],
                   "tool": {"type": "trace", "start": 4, "read": "x = {x} gives f(x) = {y}"}},
                  r"This is \(f(x) = \dfrac{2x + 1}{x - 1}\). Slide right and the curve hugs \(y = 2\). Slide toward \(x = 1\) and it runs off the top on one side and off the bottom on the other."),
            block("The one fact that does all the work",
                  r"""<p>When \(x\) is huge, \(\frac1x\) is tiny and \(\frac{1}{x^2}\) is tinier still:
                  \(\displaystyle\lim_{x\to\pm\infty}\frac{1}{x^n} = 0\). So for a fraction of polynomials, divide every
                  term by the highest power of \(x\) in the bottom. Every term that still has an \(x\) underneath dies
                  away, and what is left is the limit.</p>
                  <p>The shortcut that comes out of it: compare the <b>degree</b> (highest power) of the top and of the
                  bottom. Bottom bigger: the limit is 0. Same degree: the ratio of the leading coefficients. Top bigger:
                  the outputs grow without bound and there is no horizontal asymptote.</p>"""),
            block("Which way does it blow up?",
                  r"""<p>Near a vertical asymptote, check the <b>sign</b> on each side. Take \(\dfrac{1}{x - 2}\). Just right of 2
                  the bottom is a tiny positive number, so the fraction is huge and positive: \(+\infty\). Just left of 2
                  the bottom is tiny and negative, so the fraction is huge and negative: \(-\infty\).</p>"""),
        ],
        "examples": [
            ex(r"Find \(\displaystyle\lim_{x\to\infty}\frac{3x^2 - x}{x^2 + 4}\).",
               [r"The highest power in the bottom is \(x^2\). Divide every term by it: \(\dfrac{3 - \frac1x}{1 + \frac{4}{x^2}}\).",
                r"As \(x \to \infty\), \(\frac1x \to 0\) and \(\frac{4}{x^2} \to 0\).",
                r"What is left is \(\dfrac{3 - 0}{1 + 0}\). (Shortcut: the degrees are equal, so take the ratio of the leading coefficients, \(\frac31\).)"],
               r"\(3\)"),
            "main",
            ex(r"Find \(\displaystyle\lim_{x\to 3^-}\frac{x + 1}{x - 3}\) and \(\displaystyle\lim_{x\to 3^+}\frac{x + 1}{x - 3}\).",
               [r"Substituting \(x = 3\) gives \(\frac40\): a number that isn't zero, over zero. The outputs blow up, and only the sign is left to find.",
                r"Just left of 3 (say \(x = 2.99\)): the top is about \(4\), positive, and the bottom is \(-0.01\), negative. Positive over tiny negative is huge and negative.",
                r"Just right of 3 (say \(x = 3.01\)): the top is about \(4\) and the bottom is \(+0.01\). Huge and positive."],
               r"\(-\infty\) from the left and \(+\infty\) from the right, so \(x = 3\) is a vertical asymptote"),
        ],
        "steps": {
            0: [r"Divide every term by \(x^2\): \(\dfrac{3 + \frac{1}{x^2}}{5 - \frac1x}\).",
                r"As \(x \to \infty\) the small fractions go to 0, leaving \(\dfrac35\)."],
            1: [r"Right of 2 the bottom \(x - 2\) is a tiny positive number, so \(\dfrac{1}{x - 2} \to +\infty\).",
                r"Left of 2 the bottom is a tiny negative number, so \(\dfrac{1}{x - 2} \to -\infty\).",
                r"Outputs that blow up at \(x = 2\) mean a vertical asymptote there."],
            2: [r"This is \(\infty - \infty\), which is indeterminate. Multiply by the conjugate over itself: \(\dfrac{(\sqrt{x^2 + x} - x)(\sqrt{x^2 + x} + x)}{\sqrt{x^2 + x} + x} = \dfrac{x}{\sqrt{x^2 + x} + x}\).",
                r"Divide top and bottom by \(x\). For \(x \gt 0\), \(\sqrt{x^2 + x} = x\sqrt{1 + \frac1x}\), so this is \(\dfrac{1}{\sqrt{1 + \frac1x} + 1}\).",
                r"As \(x \to \infty\), \(\frac1x \to 0\), leaving \(\dfrac{1}{1 + 1} = \dfrac12\)."],
        },
        "quiz": [
            mc(r"\(\displaystyle\lim_{x\to\infty}\frac{5}{x^2} =\)", ["5", "0", r"\(\infty\)", "does not exist"], 1,
               "A constant over something that grows without bound heads for 0."),
            mc(r"\(\displaystyle\lim_{x\to 0^+}\frac{1}{x} =\)", ["0", r"\(-\infty\)", r"\(\infty\)", "1"], 2,
               "Just right of 0 the bottom is tiny and positive, so the fraction is huge and positive."),
        ],
    },    "epsilon-delta": {
        "learn": [
            block("Why be this precise?",
                  r"""<p>"Gets close to" is fine for building a feel for limits, but it isn't a definition you can prove
                  anything with. How close is close? The epsilon–delta definition swaps the vague words for a test that
                  anyone can check.</p>"""),
            block("The challenge game",
                  r"""<p>You claim that \(\displaystyle\lim_{x\to a} f(x) = L\). A doubter challenges you: "Get the outputs
                  within 0.1 of \(L\)." You answer with a window around \(a\): "Keep \(x\) this close to \(a\) and they
                  will be." Then they demand 0.01. Then 0.000001. If you can answer <b>every</b> challenge, however
                  small, the limit really is \(L\).</p>
                  <ul><li>\(\varepsilon\) (epsilon) is the doubter's tolerance: how close \(f(x)\) must be to \(L\).</li>
                  <li>\(\delta\) (delta) is your reply: how close \(x\) must stay to \(a\).</li>
                  <li>\(|f(x) - L| \lt \varepsilon\) says "the distance from \(f(x)\) to \(L\) is less than \(\varepsilon\)".</li>
                  <li>\(0 \lt |x - a| \lt \delta\) says "\(x\) is within \(\delta\) of \(a\), but is not \(a\) itself".</li></ul>""",
                  {"view": [0, 4, 0, 10], "alt": "The line y equals 3x minus 1, a horizontal band around height 5 and a vertical window around x equals 2",
                   "curves": [{"f": "3*x-1"}], "tool": {"type": "band", "a": 2, "L": 5, "max": 3, "start": 1.5}},
                  r"The claim is \(\displaystyle\lim_{x\to 2}(3x - 1) = 5\). Shrink \(\varepsilon\) (the yellow band) and the widest window that keeps the line inside it shrinks too. For this line it is always \(\varepsilon / 3\)."),
            block("How to read the definition",
                  r"""<p>\(\forall \varepsilon \gt 0\ \exists \delta \gt 0\) reads "for every positive epsilon there exists a
                  positive delta". The symbol \(\forall\) means <b>for all</b>, \(\exists\) means <b>there exists</b>, and
                  the arrow \(\Rightarrow\) means <b>guarantees</b>. Altogether: for every tolerance there is a window,
                  such that staying inside the window guarantees the outputs stay inside the tolerance.</p>
                  <p>Every proof has the same two parts. <b>Scratch work:</b> start from \(|f(x) - L| \lt \varepsilon\) and
                  work backwards to a condition on \(|x - a|\). That tells you which \(\delta\) to pick. <b>The proof:</b>
                  announce that \(\delta\), then show forwards that it works.</p>"""),
        ],
        "examples": [
            ex(r"For \(\displaystyle\lim_{x\to 4}(2x + 1) = 9\), find a \(\delta\) that works when \(\varepsilon = 0.1\).",
               [r"We need \(|(2x + 1) - 9| \lt 0.1\). Tidy the inside: \(|2x - 8| = 2|x - 4|\).",
                r"So we need \(2|x - 4| \lt 0.1\), which is \(|x - 4| \lt 0.05\).",
                r"Any \(x\) within \(0.05\) of 4 works. Check one: \(x = 4.04\) gives \(9.08\), which is within \(0.1\) of 9. ✓"],
               r"\(\delta = 0.05\)"),
            "main",
            ex(r"Prove \(\displaystyle\lim_{x\to 1}(4 - 2x) = 2\).",
               [r"Scratch work: \(|(4 - 2x) - 2| = |2 - 2x| = 2|x - 1|\). (An absolute value drops the minus sign.) We need \(2|x - 1| \lt \varepsilon\), so \(|x - 1| \lt \frac{\varepsilon}{2}\).",
                r"Proof: let \(\varepsilon \gt 0\) and choose \(\delta = \frac{\varepsilon}{2}\).",
                r"If \(0 \lt |x - 1| \lt \delta\), then \(|(4 - 2x) - 2| = 2|x - 1| \lt 2\delta = \varepsilon\). ∎"],
               r"\(\delta = \frac{\varepsilon}{2}\) works for every \(\varepsilon \gt 0\)"),
        ],
        "steps": {
            0: [r"Scratch work: \(|(5x + 2) - 7| = |5x - 5| = 5|x - 1|\). We need \(5|x - 1| \lt \varepsilon\), so \(|x - 1| \lt \frac{\varepsilon}{5}\).",
                r"Proof: let \(\varepsilon \gt 0\) and choose \(\delta = \frac{\varepsilon}{5}\).",
                r"If \(0 \lt |x - 1| \lt \delta\), then \(|(5x + 2) - 7| = 5|x - 1| \lt 5\delta = \varepsilon\). ∎"],
            1: [r"\(|2x - 6| = 2|x - 3|\), and we need this below \(0.1\).",
                r"Divide by 2: \(|x - 3| \lt 0.05\). So \(\delta = 0.05\) works, and so does anything smaller."],
            2: [r"Scratch work: \(|x^2 - 4| = |x - 2|\,|x + 2|\). The factor \(|x - 2|\) is the one we control, so we need a ceiling on \(|x + 2|\).",
                r"Agree to keep \(\delta \le 1\). Then \(|x - 2| \lt 1\) means \(1 \lt x \lt 3\), so \(|x + 2| \lt 5\).",
                r"Then \(|x^2 - 4| \lt 5|x - 2|\), which is below \(\varepsilon\) once \(|x - 2| \lt \frac{\varepsilon}{5}\). Both conditions hold when \(\delta = \min\left(1, \frac{\varepsilon}{5}\right)\).",
                r"Proof: let \(\varepsilon \gt 0\) and choose that \(\delta\). If \(0 \lt |x - 2| \lt \delta\), then \(|x + 2| \lt 5\) and \(|x^2 - 4| = |x - 2|\,|x + 2| \lt \frac{\varepsilon}{5}\cdot 5 = \varepsilon\). ∎"],
        },
        "quiz": [
            mc(r"In the definition, \(\varepsilon\) measures:",
               [r"how close \(x\) is to \(a\)", r"how close \(f(x)\) must be to \(L\)", "the slope of the function", "the value of the limit"], 1,
               r"\(\varepsilon\) is the tolerance on the outputs. \(\delta\) is the window on the inputs."),
            mc(r"For \(\displaystyle\lim_{x\to 0} 5x = 0\) and \(\varepsilon = 1\), which \(\delta\) works?",
               [r"\(\delta = 0.2\)", r"\(\delta = 1\)", r"\(\delta = 5\)", r"\(\delta = 0.5\)"], 0,
               r"We need \(5|x| \lt 1\), which is \(|x| \lt 0.2\)."),
        ],
    },
    "continuity": {
        "learn": [
            block("The idea: no surprises",
                  r"""<p>A function is continuous at a point when its value there is exactly what the nearby values led you to
                  expect. You can draw through the point without lifting your pen. In the language of limits: <b>the
                  limit equals the value</b>, \(\displaystyle\lim_{x\to a} f(x) = f(a)\).</p>
                  <p>That short statement hides three things that all have to be true: \(f(a)\) exists, the limit exists,
                  and the two are the same number.</p>"""),
            block("Three ways it can break",
                  r"""<ul><li><b>Removable (a hole):</b> the limit exists, but \(f(a)\) is missing or is some other number. One
                  point is out of place, and moving it would mend the graph.</li>
                  <li><b>Jump:</b> the left and right sides head for different heights, so the limit doesn't exist.</li>
                  <li><b>Infinite:</b> the outputs blow up near \(a\). The graph has a vertical asymptote.</li></ul>""",
                  {"view": [-0.5, 7.5, -1.5, 5], "alt": "One graph with a hole where x is 1, a jump where x is 3 and a vertical asymptote where x is 5",
                   "curves": [{"f": "0.5*x+1", "dom": [-0.5, 3]}, {"f": "0.5+0.4/(5-x)", "dom": [3, 4.99]}, {"f": "0.5-0.4/(x-5)", "dom": [5.01, 7.5]}],
                   "vlines": [5],
                   "points": [{"at": [1, 1.5], "open": True, "label": "hole", "pos": "se"}, {"at": [1, 2.6]},
                              {"at": [3, 2.5], "open": True, "label": "jump", "pos": "n"}, {"at": [3, 0.7]}],
                   "labels": [{"at": [5, 4.3], "text": "asymptote", "pos": "e"}]},
                  r"Three breaks in one graph: a hole at \(x = 1\) (the point that belongs there sits higher up), a jump at \(x = 3\), and a vertical asymptote at \(x = 5\)."),
            block("The good news",
                  r"""<p>Polynomials, roots, \(\sin\), \(\cos\), \(e^x\), logs, and fractions made of these are continuous
                  everywhere they are defined. That is why direct substitution worked in the last lessons: for a
                  continuous function the limit <b>is</b> the value. A break can only happen where the formula is
                  undefined, or where a piecewise function changes rule, so those are the only points to check.</p>"""),
        ],
        "examples": [
            ex(r"Is \(f(x) = \begin{cases} x + 2 & x \lt 1 \\ 4 - x & x \ge 1 \end{cases}\) continuous at \(x = 1\)?",
               [r"The value: \(x = 1\) uses the second rule, so \(f(1) = 4 - 1 = 3\). It exists.",
                r"The limit: from the left, \(x + 2\) heads for 3. From the right, \(4 - x\) heads for 3. Both sides agree, so the limit is 3.",
                r"The limit equals the value (\(3 = 3\)), so all three conditions hold."],
               r"Yes, \(f\) is continuous at \(x = 1\)"),
            "main",
            ex(r"Find and classify every discontinuity of \(f(x) = \dfrac{x^2 - 4}{x^2 - x - 2}\).",
               [r"A fraction of polynomials can only break where the bottom is 0. Factor it: \(x^2 - x - 2 = (x - 2)(x + 1)\), so check \(x = 2\) and \(x = -1\).",
                r"Factor the top as well: \(\dfrac{(x - 2)(x + 2)}{(x - 2)(x + 1)}\). Near \(x = 2\) the common factor cancels, leaving \(\dfrac{x + 2}{x + 1}\), which heads for \(\dfrac43\). The limit exists but \(f(2)\) doesn't: a removable discontinuity, a hole at \(\left(2, \frac43\right)\).",
                r"At \(x = -1\) nothing cancels: the top heads for \(1\) while the bottom heads for 0, so the outputs blow up. That is an infinite discontinuity, a vertical asymptote."],
               r"Removable at \(x = 2\), infinite at \(x = -1\)"),
        ],
        "steps": {
            0: [r"\(f(1)\) is \(\frac00\), so it is undefined: there is a break of some kind.",
                r"Factor and cancel: \(\dfrac{(x - 1)(x + 1)}{x - 1} = x + 1\) for \(x \ne 1\), which heads for 2.",
                r"The limit exists (it is 2) but the value doesn't, so the break is removable: a hole at \((1, 2)\)."],
            1: [r"\(f(0)\) is undefined.",
                r"Near 0, \(x^2\) is tiny and positive on both sides, so \(\dfrac{1}{x^2}\) is huge and positive: the outputs go to \(+\infty\).",
                r"Outputs that blow up mean an infinite discontinuity, with a vertical asymptote at \(x = 0\)."],
            2: [r"The only place it can break is \(x = 1\), where the rule changes.",
                r"Left side and value: \(c(1)^2 = c\). Right side: \(3(1) = 3\).",
                r"For the two pieces to meet, \(c = 3\)."],
        },
        "quiz": [
            mc(r"\(f(x) = \begin{cases} 2x & x \lt 3 \\ x + 5 & x \ge 3 \end{cases}\) at \(x = 3\) has:",
               ["no discontinuity", "a removable discontinuity", "a jump discontinuity", "an infinite discontinuity"], 2,
               "The left side heads for 6 and the right side for 8."),
            mc(r"Where is \(f(x) = \dfrac{x + 1}{x - 4}\) not continuous?",
               [r"\(x = -1\)", r"\(x = 4\)", r"\(x = 0\)", "nowhere"], 1,
               "A fraction of polynomials only breaks where the bottom is 0."),
        ],
    },

    # ============================ WEEK 3: DERIVATIVES ============================
    "derivative-definition": {
        "learn": [
            block("The problem: slope at a single point",
                  r"""<p>The slope of a straight line is rise over run between any two of its points. A curve is different:
                  its steepness changes as you move along it. So what could "the slope at one point" even mean? A slope
                  needs two points, and one point on its own gives \(\frac00\).</p>
                  <p>The way out is the idea you already have: a limit.</p>"""),
            block("From secant to tangent",
                  r"""<p>Pick the point you care about, \((x, f(x))\), and a second point a little further along,
                  \((x + h, f(x + h))\). The line through both is called a <b>secant line</b>, and its slope is ordinary
                  rise over run:</p>
                  \[\frac{f(x + h) - f(x)}{h}\]
                  <p>This is the <b>difference quotient</b>. Now slide the second point toward the first by shrinking
                  \(h\). The secant swings toward the line that just touches the curve at your point, the <b>tangent
                  line</b>, and its slope heads for a limit. That limit is the derivative, written \(f'(x)\) and read
                  "f prime of x".</p>""",
                  {"view": [-1, 4, -1, 10], "alt": "The parabola y equals x squared with a secant line through two of its points and the tangent at x equals 1",
                   "curves": [{"f": "x^2"}], "tool": {"type": "secant", "a": 1, "max": 2, "start": 1.6}},
                  r"This is \(f(x) = x^2\) with the fixed point at \(x = 1\). Shrink \(h\): the yellow secant swings onto the dotted tangent, and its slope heads for 2."),
            block("What the derivative tells you",
                  r"""<p>\(f'(x)\) is a new function: give it an \(x\) and it returns the slope of \(f\) there. Slope means
                  <b>rate of change</b>. If \(f(t)\) is your position at time \(t\), then \(f'(t)\) is your speed at that
                  instant: the number on the speedometer.</p>
                  <p>The recipe never changes. Write out \(f(x + h)\), subtract \(f(x)\), simplify until an \(h\) factors
                  out of the top, cancel it against the \(h\) underneath, then let \(h \to 0\).</p>"""),
        ],
        "examples": [
            ex(r"Use the definition to find the slope of \(f(x) = x^2\) at \(x = 3\).",
               [r"Two points: \((3, 9)\) and \((3 + h, (3 + h)^2)\). Expand the second height: \((3 + h)^2 = 9 + 6h + h^2\).",
                r"Rise over run: \(\dfrac{(9 + 6h + h^2) - 9}{h} = \dfrac{6h + h^2}{h}\).",
                r"Factor \(h\) out of the top and cancel: \(6 + h\).",
                r"Let \(h \to 0\): the slope heads for \(6\)."],
               r"\(f'(3) = 6\)"),
            "main",
            ex(r"Use the definition to differentiate \(f(x) = x^3\).",
               [r"\(f(x + h) = (x + h)^3 = x^3 + 3x^2h + 3xh^2 + h^3\) (the cube of a sum, from the Expanding lesson).",
                r"Subtract \(f(x)\): \(3x^2h + 3xh^2 + h^3\).",
                r"Divide by \(h\): \(3x^2 + 3xh + h^2\).",
                r"Let \(h \to 0\): the last two terms vanish."],
               r"\(f'(x) = 3x^2\)"),
        ],
        "steps": {
            0: [r"\(f(x + h) - f(x) = \dfrac{1}{x + h} - \dfrac1x\). Combine over the common denominator \(x(x + h)\): \(\dfrac{x - (x + h)}{x(x + h)} = \dfrac{-h}{x(x + h)}\).",
                r"Divide by \(h\): \(\dfrac{-1}{x(x + h)}\).",
                r"Let \(h \to 0\): \(-\dfrac{1}{x \cdot x} = -\dfrac{1}{x^2}\)."],
            1: [r"The difference quotient is \(\dfrac{\sqrt{x + h} - \sqrt{x}}{h}\). Multiply top and bottom by the conjugate \(\sqrt{x + h} + \sqrt{x}\).",
                r"The top becomes \((x + h) - x = h\), which gives \(\dfrac{h}{h(\sqrt{x + h} + \sqrt{x})} = \dfrac{1}{\sqrt{x + h} + \sqrt{x}}\).",
                r"Let \(h \to 0\): \(\dfrac{1}{\sqrt{x} + \sqrt{x}} = \dfrac{1}{2\sqrt{x}}\)."],
            2: [r"The point: \(f(1) = 1 + 3 = 4\), so the line goes through \((1, 4)\).",
                r"The slope: the worked example found \(f'(x) = 2x + 3\), so \(f'(1) = 5\).",
                r"Point-slope form: \(y - 4 = 5(x - 1)\), which simplifies to \(y = 5x - 1\)."],
        },
        "quiz": [
            mc(r"\(\dfrac{f(x+h) - f(x)}{h}\) is the slope of:",
               [r"the tangent line at \(x\)", "the secant line through two points of the graph", r"the \(x\)-axis", r"the graph of \(f'\)"], 1,
               r"It is rise over run between \((x, f(x))\) and \((x+h, f(x+h))\). It becomes the tangent's slope only in the limit."),
            mc(r"\(s(t)\) is the distance a car has travelled after \(t\) hours. Then \(s'(2)\) is:",
               ["the distance after 2 hours", "the average speed over the first 2 hours", "the speed at the 2-hour mark", "the time it takes to go 2 km"], 2,
               "A derivative is an instantaneous rate of change. Here that is the speed at that moment."),
        ],
    },
    "derivative-rules": {
        "learn": [
            block("Spot the pattern",
                  r"""<p>Run the limit definition on a few powers and the answers line up:</p>
                  <ul><li>\(x^2\) has derivative \(2x\)</li><li>\(x^3\) has derivative \(3x^2\)</li>
                  <li>\(x^4\) has derivative \(4x^3\)</li></ul>
                  <p>Each time the power comes down in front, and the new power is one less. That is the <b>power
                  rule</b>: the derivative of \(x^n\) is \(n\,x^{n-1}\). It works for every real number \(n\): negative
                  powers, fractions, all of them.</p>""",
                  {"view": [-3, 3, -1, 9], "alt": "The parabola y equals x squared with a tangent line you can slide along it",
                   "curves": [{"f": "x^2"}], "tool": {"type": "tangent", "start": 1, "read": "At x = {x} the slope is {m}: exactly twice x."}},
                  r"Slide the point along \(y = x^2\). Its slope is always twice the \(x\)-value, which is what \(\frac{d}{dx}x^2 = 2x\) says."),
            block(r"New notation: \(\frac{d}{dx}\)",
                  r"""<p>\(\dfrac{d}{dx}\) is an instruction: "take the derivative, with respect to \(x\), of whatever comes
                  next". So \(\dfrac{d}{dx}x^3 = 3x^2\) says the same as "if \(f(x) = x^3\) then \(f'(x) = 3x^2\)".</p>
                  <p>When a function is written as \(y = \ldots\), its derivative is written \(\dfrac{dy}{dx}\) or \(y'\).
                  It is not a fraction you can cancel. Treat it as one symbol.</p>"""),
            block("Three rules that let you go term by term",
                  r"""<ul><li><b>Constants disappear.</b> A constant never changes, so its rate of change is 0:
                  \(\dfrac{d}{dx}7 = 0\).</li>
                  <li><b>Constant multiples wait outside.</b> \(\dfrac{d}{dx}5x^3 = 5 \cdot 3x^2 = 15x^2\).</li>
                  <li><b>Sums and differences split.</b> Differentiate each term on its own and keep the signs.</li></ul>
                  <p>Before you start, rewrite roots and fractions as powers: \(\sqrt{x} = x^{1/2}\) and
                  \(\dfrac{1}{x^3} = x^{-3}\). Then every term is a power rule.</p>"""),
        ],
        "examples": [
            ex(r"Differentiate \(f(x) = x^4 + 3x^2 - 5x + 2\).",
               [r"Go term by term. \(x^4\): bring down the 4 and drop the power by one, \(4x^3\).",
                r"\(3x^2\): the 3 waits outside while \(x^2\) becomes \(2x\), giving \(6x\).",
                r"\(-5x\): \(x = x^1\) becomes \(1x^0 = 1\), so this term gives \(-5\). The constant \(2\) gives 0."],
               r"\(f'(x) = 4x^3 + 6x - 5\)"),
            "main",
            ex(r"Where does the graph of \(y = x^3 - 12x\) have a horizontal tangent?",
               [r"A horizontal tangent has slope 0, so we want the points where \(\dfrac{dy}{dx} = 0\).",
                r"Differentiate: \(\dfrac{dy}{dx} = 3x^2 - 12\).",
                r"Solve \(3x^2 - 12 = 0\): \(x^2 = 4\), so \(x = 2\) or \(x = -2\).",
                r"Find the heights: \(y(2) = 8 - 24 = -16\) and \(y(-2) = -8 + 24 = 16\)."],
               r"At \((2, -16)\) and \((-2, 16)\)"),
        ],
        "steps": {
            0: [r"Term by term: \(x^3 \to 3x^2\), \(-6x^2 \to -12x\), \(9x \to 9\).",
                r"Put them together: \(3x^2 - 12x + 9\)."],
            1: [r"Rewrite as a power: \(\dfrac5x = 5x^{-1}\).",
                r"Power rule: \(5 \cdot (-1)x^{-2} = -5x^{-2}\).",
                r"Write it without the negative exponent: \(-\dfrac{5}{x^2}\)."],
            2: [r"Bring the \(\frac23\) down and subtract 1 from the power: \(\frac23 - 1 = -\frac13\).",
                r"So the derivative is \(\frac23x^{-1/3}\), which is also \(\dfrac{2}{3\sqrt[3]{x}}\)."],
        },
        "quiz": [
            mc(r"\(\dfrac{d}{dx}\left(3x^2 + 4x - 9\right) =\)", [r"\(6x + 4\)", r"\(6x - 9\)", r"\(3x + 4\)", r"\(6x^2 + 4\)"], 0,
               r"\(3x^2 \to 6x\), \(4x \to 4\), and the constant gives 0."),
            mc(r"\(\dfrac{d}{dx}\) means:", ["divide by x", "take the derivative with respect to x", "d times x", "the slope is d over x"], 1,
               "It is an instruction to differentiate whatever comes next."),
        ],
    },
    "product-rule": {
        "learn": [
            block("Why you can't just multiply the derivatives",
                  r"""<p>Test the tempting shortcut on something you can check. \(x^2 \cdot x^3\) is \(x^5\), so its true
                  derivative is \(5x^4\). Multiplying the two derivatives gives \(2x \cdot 3x^2 = 6x^3\). Wrong power,
                  wrong number. A product needs a rule of its own.</p>"""),
            block("Where the rule comes from",
                  r"""<p>Picture a rectangle with sides \(f\) and \(g\), so its area is \(fg\). Let both sides grow a little. The
                  area grows by two thin strips: one of size (change in \(f\)) × \(g\) along one edge, and one of size
                  \(f\) × (change in \(g\)) along the other. The tiny corner where the two changes overlap is too small to
                  matter. That is the product rule:</p>
                  \[(fg)' = f'g + fg'\]
                  <p>In words: <b>the derivative of the first times the second, plus the first times the derivative of
                  the second</b>. Each factor takes one turn being differentiated while the other waits.</p>""",
                  {"view": [-0.6, 6.2, -0.6, 4.4], "axes": False, "h": 330,
                   "alt": "A rectangle with sides f and g, with a thin strip added along its right edge and another along its top",
                   "rects": [{"x": 0, "y": 0, "w": 4, "h": 2.6, "style": "soft"}, {"x": 4, "y": 0, "w": 0.9, "h": 2.6},
                             {"x": 0, "y": 2.6, "w": 4, "h": 0.7}, {"x": 4, "y": 2.6, "w": 0.9, "h": 0.7, "style": "dash"}],
                   "labels": [{"at": [2, 1.3], "text": "area f × g", "pos": "n"}, {"at": [2, 0], "text": "f", "pos": "s"},
                              {"at": [0, 1.3], "text": "g", "pos": "w"}, {"at": [4.9, 1.3], "text": "(change in f) × g", "pos": "e"},
                              {"at": [2, 3.3], "text": "f × (change in g)", "pos": "n"}]},
                  "When both sides grow, the new area is the two yellow strips. The dashed corner shrinks away to nothing."),
            block("Using it",
                  r"""<p>Name the two factors \(f\) and \(g\), write \(f'\) and \(g'\) underneath, then assemble \(f'g + fg'\).
                  Writing the four pieces out first prevents almost every mistake. When both factors are simple
                  polynomials you can check yourself by expanding first and using the power rule.</p>"""),
        ],
        "examples": [
            ex(r"Differentiate \(y = x^2(x + 4)\) with the product rule, then check by expanding.",
               [r"\(f = x^2\), so \(f' = 2x\). \(g = x + 4\), so \(g' = 1\).",
                r"Assemble \(f'g + fg'\): \(2x(x + 4) + x^2(1) = 2x^2 + 8x + x^2\).",
                r"Collect: \(3x^2 + 8x\).",
                r"Check: expanding first gives \(y = x^3 + 4x^2\), and the power rule gives \(3x^2 + 8x\). The same. ✓"],
               r"\(y' = 3x^2 + 8x\)"),
            "main",
            ex(r"Find the slope of \(y = (2x - 1)(x^2 + 3)\) at \(x = 1\).",
               [r"\(f = 2x - 1\), \(f' = 2\). \(g = x^2 + 3\), \(g' = 2x\).",
                r"Product rule: \(y' = 2(x^2 + 3) + (2x - 1)(2x)\).",
                r"A slope doesn't need a tidy formula. Substitute \(x = 1\) straight away: \(2(1 + 3) + (2 - 1)(2) = 8 + 2\)."],
               r"The slope at \(x = 1\) is \(10\)"),
        ],
        "steps": {
            0: [r"\(f = x^3\), \(f' = 3x^2\). \(g = 2x + 5\), \(g' = 2\).",
                r"\(f'g + fg' = 3x^2(2x + 5) + x^3(2) = 6x^3 + 15x^2 + 2x^3\).",
                r"Collect: \(8x^3 + 15x^2\)."],
            1: [r"\(f = \sqrt{x} = x^{1/2}\), \(f' = \dfrac{1}{2\sqrt{x}}\). \(g = x^2 - 1\), \(g' = 2x\).",
                r"\(f'g + fg' = \dfrac{x^2 - 1}{2\sqrt{x}} + 2x\sqrt{x}\).",
                r"Put both over \(2\sqrt{x}\): \(2x\sqrt{x} = \dfrac{4x^2}{2\sqrt{x}}\), so the sum is \(\dfrac{x^2 - 1 + 4x^2}{2\sqrt{x}} = \dfrac{5x^2 - 1}{2\sqrt{x}}\)."],
            2: [r"\(f = x + 1\), \(f' = 1\). \(g = x^2 - 3\), \(g' = 2x\).",
                r"\(y' = 1 \cdot (x^2 - 3) + (x + 1)(2x)\).",
                r"At \(x = 2\): \((4 - 3) + (3)(4) = 1 + 12 = 13\)."],
        },
        "quiz": [
            mc(r"For \(y = (x^2 + 1)(x - 5)\), the product rule gives \(y' =\)",
               [r"\(2x \cdot 1\)", r"\(2x(x - 5) + (x^2 + 1)\)", r"\(2x(x - 5) - (x^2 + 1)\)", r"\((x^2 + 1) + (x - 5)\)"], 1,
               r"\(f'g + fg'\) with \(f' = 2x\) and \(g' = 1\)."),
            mc(r"\(\dfrac{d}{dx}\big[x \cdot x^4\big]\) by the product rule is:", [r"\(4x^3\)", r"\(5x^4\)", r"\(x^4\)", r"\(4x^4\)"], 1,
               r"\(1 \cdot x^4 + x \cdot 4x^3 = 5x^4\), which matches the power rule on \(x^5\)."),
        ],
    },
    # ============================ WEEK 4: QUOTIENT RULE, DERIVATIVES OF e^x AND a^x ============================
    "quotient-rule": {
        "learn": [
            block("Why you can't just divide the derivatives",
                  r"""<p>Test the tempting shortcut on something you can check. \(\dfrac{x^5}{x^2}\) is \(x^3\), so its true
                  derivative is \(3x^2\). Dividing the two derivatives gives \(\dfrac{5x^4}{2x} = \dfrac52x^3\). Wrong
                  power, wrong number. Like a product, a fraction needs a rule of its own.</p>"""),
            block("The rule, and a way to say it",
                  r"""<p>Call the top \(f\) and the bottom \(g\). Then</p>
                  \[\left(\frac fg\right)' = \frac{f'g - fg'}{g^2}\]
                  <p>Many people remember it as <b>"low d-high minus high d-low, over low squared"</b>: the bottom times
                  the derivative of the top, minus the top times the derivative of the bottom, all over the bottom
                  squared.</p>
                  <p>The order on top matters, because of the minus sign. It always starts with the derivative of the
                  <b>top</b>. Swap the two halves and every answer comes out with the wrong sign.</p>
                  <ol><li>Write down \(f\), \(g\), \(f'\) and \(g'\) before anything else.</li>
                  <li>Assemble \(f'g - fg'\) on top, with brackets around each piece.</li>
                  <li>Put \(g^2\) underneath. Leave it squared: there is no need to expand it.</li>
                  <li>Tidy up the top.</li></ol>""",
                  {"view": [-5, 5, -0.8, 0.8], "alt": "The curve x over x squared plus 1, with a tangent line you can slide along it",
                   "curves": [{"f": "x/(x^2+1)"}],
                   "tool": {"type": "tangent", "start": 0, "read": "At x = {x} the slope is {m}."}},
                  r"This is \(y = \dfrac{x}{x^2 + 1}\). The quotient rule gives \(y' = \dfrac{1 - x^2}{(x^2 + 1)^2}\). Slide to \(x = 1\) and \(x = -1\): the tangent goes flat exactly where \(1 - x^2 = 0\)."),
            block("When you don't need it",
                  r"""<ul><li><b>A number on the bottom.</b> \(\dfrac{x^3 + 2x}{5}\) is just \(\frac15(x^3 + 2x)\). The
                  \(\frac15\) waits outside: \(\frac15(3x^2 + 2)\).</li>
                  <li><b>A single power of \(x\) on the bottom.</b> Split the fraction first:
                  \(\dfrac{x^2 + 1}{x} = x + x^{-1}\), and the power rule gives \(1 - x^{-2}\).</li>
                  <li><b>A number on top.</b> The rule shrinks to \(\left(\dfrac cg\right)' = -\dfrac{c\,g'}{g^2}\), because
                  the derivative of the top is 0.</li></ul>
                  <p>The quotient rule always works. These are just faster when they apply.</p>"""),
        ],
        "examples": [
            ex(r"Differentiate \(y = \dfrac{2x + 1}{x + 3}\).",
               [r"Top: \(f = 2x + 1\), so \(f' = 2\). Bottom: \(g = x + 3\), so \(g' = 1\).",
                r"Assemble \(\dfrac{f'g - fg'}{g^2}\): \(\dfrac{2(x + 3) - (2x + 1)(1)}{(x + 3)^2}\).",
                r"Tidy the top: \(2x + 6 - 2x - 1 = 5\)."],
               r"\(y' = \dfrac{5}{(x + 3)^2}\)"),
            "main",
            ex(r"Find the slope of \(y = \dfrac{x^2}{x + 1}\) at \(x = 1\).",
               [r"Top: \(f = x^2\), \(f' = 2x\). Bottom: \(g = x + 1\), \(g' = 1\).",
                r"\(y' = \dfrac{2x(x + 1) - x^2(1)}{(x + 1)^2} = \dfrac{x^2 + 2x}{(x + 1)^2}\).",
                r"Substitute \(x = 1\): \(\dfrac{1 + 2}{2^2}\)."],
               r"The slope at \(x = 1\) is \(\frac34\)"),
        ],
        "steps": {
            0: [r"Top: \(f = x\), \(f' = 1\). Bottom: \(g = x + 1\), \(g' = 1\).",
                r"\(\dfrac{f'g - fg'}{g^2} = \dfrac{1(x + 1) - x(1)}{(x + 1)^2}\).",
                r"The top is \(x + 1 - x = 1\), so the answer is \(\dfrac{1}{(x + 1)^2}\)."],
            1: [r"Top: \(f = \sin x\), \(f' = \cos x\). Bottom: \(g = x\), \(g' = 1\).",
                r"\(\dfrac{f'g - fg'}{g^2} = \dfrac{\cos x \cdot x - \sin x \cdot 1}{x^2}\).",
                r"Write it neatly: \(\dfrac{x\cos x - \sin x}{x^2}\)."],
            2: [r"The top is the constant 3, so \(f' = 0\). Bottom: \(g = x^2 + 1\), \(g' = 2x\).",
                r"\(\dfrac{0\cdot(x^2 + 1) - 3\cdot 2x}{(x^2 + 1)^2}\).",
                r"Only the second piece survives: \(-\dfrac{6x}{(x^2 + 1)^2}\)."],
        },
        "quiz": [
            mc(r"The top of the quotient rule is \(f'g - fg'\). Which piece comes first?", ["the top times the bottom", "the derivative of the top, times the bottom", "the two derivatives multiplied", "the bottom squared"], 1,
               "It starts with the derivative of the top, times the bottom."),
            mc(r"\(\dfrac{d}{dx}\dfrac{x + 1}{x - 1} =\)", [r"\(\dfrac{2}{(x - 1)^2}\)", r"\(-\dfrac{2}{(x - 1)^2}\)", "1", r"\(-\dfrac{2}{x - 1}\)"], 1,
               r"\(\dfrac{1(x - 1) - (x + 1)(1)}{(x - 1)^2}\), and the top is \(-2\)."),
        ],
    },
    "exp-derivatives": {
        "learn": [
            block("What makes e special",
                  r"""<p>Every exponential curve has the same habit: the higher it is, the steeper it is. For \(2^x\) the
                  slope at any point is about \(0.693\) times the height there. For \(3^x\) it is about \(1.099\) times
                  the height.</p>
                  <p>One multiplier is below 1 and the other is above it. So somewhere between 2 and 3 there is a base
                  whose multiplier is <b>exactly 1</b>, where the slope simply equals the height. That base is
                  \(e \approx 2.718\), and it is why</p>
                  \[\frac{d}{dx}e^x = e^x\]
                  <p>\(e^x\) is the one function (apart from multiples of itself) that is its own derivative.</p>""",
                  {"view": [-3, 2.5, -0.5, 8], "alt": "The curve y equals e to the x with a tangent line you can slide along it",
                   "curves": [{"f": "exp(x)"}],
                   "tool": {"type": "tangent", "start": 1, "read": "At x = {x} the height is {y} and the slope is {m}: the same number."}},
                  r"For \(e^x\) the slope at every point equals the height there. That is all \(\frac{d}{dx}e^x = e^x\) says."),
            block(r"Every other base picks up \(\ln a\)",
                  r"""<p>Those multipliers have a name. The multiplier for base \(a\) is \(\ln a\), the <b>natural
                  logarithm</b> of \(a\):</p>
                  \[\frac{d}{dx}a^x = a^x\ln a\]
                  <p>Logarithms get a lesson of their own in Week 5. For now \(\ln a\) is just a number, the one the
                  <b>ln</b> key on a calculator gives: \(\ln 2 \approx 0.693\), \(\ln 3 \approx 1.099\), and
                  \(\ln e = 1\). Because it is a constant, it sits in front like any other constant.</p>"""),
            block("Power or exponential? Look at where the x is",
                  r"""<ul><li>\(x^3\) has the \(x\) in the <b>base</b>. It is a power: bring the 3 down, \(3x^2\).</li>
                  <li>\(3^x\) has the \(x\) in the <b>exponent</b>. It is an exponential: it keeps its shape and gains
                  \(\ln 3\), giving \(3^x\ln 3\).</li>
                  <li>\(e^2\) has no \(x\) at all. It is a number, about 7.39, and its derivative is 0.</li></ul>
                  <p>This week the exponent is always a plain \(x\). Exponents like \(e^{3x}\) or \(2^{x^2}\) need the
                  chain rule, which comes in Week 5.</p>"""),
        ],
        "examples": [
            ex(r"Differentiate \(f(x) = 5e^x + x^2\).",
               [r"Term by term. The 5 waits outside while \(e^x\) stays as it is: \(5e^x\).",
                r"\(x^2\) is a power: \(2x\)."],
               r"\(f'(x) = 5e^x + 2x\)"),
            "main",
            ex(r"Find the equation of the tangent line to \(y = e^x\) at \(x = 0\).",
               [r"The point: \(y(0) = e^0 = 1\), so the line touches the curve at \((0, 1)\).",
                r"The slope: \(y' = e^x\), so \(y'(0) = 1\) as well.",
                r"Point-slope form: \(y - 1 = 1(x - 0)\)."],
               r"\(y = x + 1\)"),
        ],
        "steps": {
            0: [r"\(3e^x\): the 3 waits outside and \(e^x\) is its own derivative, giving \(3e^x\).",
                r"\(-4x^2\): the power rule gives \(-8x\)."],
            1: [r"The \(x\) is in the exponent, so this is an exponential with base \(a = 2\).",
                r"Use \(\dfrac{d}{dx}a^x = a^x\ln a\): \(2^x\ln 2\)."],
            2: [r"Top: \(f = e^x\), \(f' = e^x\). Bottom: \(g = x\), \(g' = 1\).",
                r"Quotient rule: \(\dfrac{e^x\cdot x - e^x\cdot 1}{x^2}\).",
                r"Factor \(e^x\) out of the top: \(\dfrac{e^x(x - 1)}{x^2}\)."],
        },
        "quiz": [
            mc(r"\(\dfrac{d}{dx}\left(e^x + e^2\right) =\)", [r"\(e^x + e^2\)", r"\(e^x + 2e\)", r"\(e^x\)", r"\(xe^{x-1}\)"], 2,
               r"\(e^2\) has no \(x\) in it. It is a constant, so it contributes 0."),
            mc(r"The slope of \(y = 10^x\) at \(x = 0\) is:", ["0", "1", r"\(\ln 10\)", "10"], 2,
               r"\(y' = 10^x\ln 10\), and \(10^0 = 1\)."),
        ],
    },

    # ============================ WEEK 5: CHAIN RULE, IMPLICIT DIFFERENTIATION ============================
    "chain-rule": {
        "learn": [
            block("Spot a function inside a function",
                  r"""<p>In \((3x^2 + 1)^5\) there are two jobs. First work out \(3x^2 + 1\), then raise the result to the
                  fifth power. The first job is the <b>inside</b> function and the second is the <b>outside</b> one.</p>
                  <ul><li>\(\sin(4x)\): inside \(4x\), outside the sine.</li>
                  <li>\(\sqrt{x^2 + 1}\): inside \(x^2 + 1\), outside the square root.</li>
                  <li>\(\cos^3x\), which means \((\cos x)^3\): inside \(\cos x\), outside the cube.</li></ul>
                  <p>A quick test: imagine working it out on a calculator for some \(x\). The <b>last</b> button you
                  press is the outside function.</p>"""),
            block("Why you multiply",
                  r"""<p>Rates multiply. If you walk twice as fast as a friend, and the friend walks three times as fast as
                  a tortoise, you are going \(2 \times 3 = 6\) times as fast as the tortoise.</p>
                  <p>A function inside a function is the same chain: \(x\) drives the inside, and the inside drives the
                  outside. So the rate of the whole thing is the outside's rate times the inside's rate:</p>
                  \[\frac{dy}{dx} = \frac{dy}{du}\cdot\frac{du}{dx}\]
                  <p>Here \(u\) stands for the inside function.</p>""",
                  {"view": [-0.5, 6.5, -1.6, 1.6], "alt": "The curve sine of 2x with a tangent line you can slide along it, and the curve sine of x dashed",
                   "curves": [{"f": "sin(2*x)"}, {"f": "sin(x)", "style": "dash"}],
                   "tool": {"type": "tangent", "start": 0, "read": "At x = {x} the slope of sin(2x) is {m}."}},
                  r"The dashed curve is \(\sin x\) and the solid one is \(\sin(2x)\). The inside \(2x\) runs twice as fast, so the wave is squeezed and every slope is doubled. At \(x = 0\) the slope is 2, not 1: that extra 2 is the derivative of the inside."),
            block("The method: outside, keep the inside, times the inside's derivative",
                  r"""<ol><li>Name the inside function.</li>
                  <li>Differentiate the <b>outside</b>, and leave the inside sitting in it untouched.</li>
                  <li>Multiply by the derivative of the <b>inside</b>.</li></ol>
                  <p>For \((3x^2 + 1)^5\): the fifth power on the outside becomes \(5(3x^2 + 1)^4\), with the inside
                  left alone, and the inside's derivative is \(6x\). Together: \(5(3x^2 + 1)^4 \cdot 6x\).</p>
                  <p>With three layers, keep going inward: one factor for each layer. And from here on the chain rule
                  is everywhere. Whenever the thing inside a power, a root, a sine, an exponential or a logarithm is
                  more than a plain \(x\), you need it.</p>"""),
        ],
        "examples": [
            ex(r"Differentiate \(y = (2x + 3)^2\) with the chain rule, then check by expanding.",
               [r"Inside: \(2x + 3\), with derivative 2. Outside: the square, whose derivative is 2 times what is inside.",
                r"Chain rule: \(2(2x + 3)\cdot 2 = 4(2x + 3) = 8x + 12\).",
                r"Check: expanding first gives \(4x^2 + 12x + 9\), and the power rule gives \(8x + 12\). The same. ✓"],
               r"\(y' = 8x + 12\)"),
            "main",
            ex(r"Differentiate \(y = \sin^2(3x)\).",
               [r"Rewrite it so the layers show: \(y = \big(\sin(3x)\big)^2\). There are three: the square, the sine, and \(3x\).",
                r"Outermost, the square: \(2\sin(3x)\), times the derivative of what is inside it.",
                r"Next, the sine: \(\cos(3x)\), times the derivative of what is inside it.",
                r"Innermost: \(3x\) has derivative 3. Multiply all three factors."],
               r"\(y' = 6\sin(3x)\cos(3x)\)"),
        ],
        "steps": {
            0: [r"Write the root as a power: \((x^2 + 1)^{1/2}\). Inside: \(x^2 + 1\), with derivative \(2x\).",
                r"Outside: the power \(\frac12\) comes down and drops by one, giving \(\frac12(x^2 + 1)^{-1/2}\).",
                r"Multiply by the inside's derivative: \(\frac12(x^2 + 1)^{-1/2}\cdot 2x = \dfrac{x}{\sqrt{x^2 + 1}}\)."],
            1: [r"Inside: \(4x\), with derivative 4. Outside: sine, which becomes cosine.",
                r"\(\cos(4x)\cdot 4 = 4\cos(4x)\)."],
            2: [r"\(\cos^3x\) means \((\cos x)^3\). Inside: \(\cos x\), with derivative \(-\sin x\).",
                r"Outside: the cube. The 3 comes down and the power drops to 2, giving \(3\cos^2x\).",
                r"Multiply: \(3\cos^2x\cdot(-\sin x) = -3\cos^2x\sin x\)."],
        },
        "quiz": [
            mc(r"In \(\cos(x^3)\), the inside function is:", [r"\(\cos\)", r"\(x^3\)", r"\(3x^2\)", r"\(\cos x\)"], 1,
               r"You work out \(x^3\) first, then take its cosine."),
            mc(r"\(\dfrac{d}{dx}\sqrt{4x + 1} =\)", [r"\(\dfrac{1}{2\sqrt{4x + 1}}\)", r"\(\dfrac{2}{\sqrt{4x + 1}}\)", r"\(4\sqrt{4x + 1}\)", r"\(2\sqrt{4x + 1}\)"], 1,
               r"\(\frac12(4x + 1)^{-1/2}\cdot 4\)."),
        ],
    },
    "implicit": {
        "learn": [
            block("When y won't come out on its own",
                  r"""<p>So far every function has been handed to you as \(y = \ldots\). Some curves aren't. The circle
                  \(x^2 + y^2 = 25\) mixes \(x\) and \(y\) together. Solving for \(y\) gives two answers,
                  \(y = \pm\sqrt{25 - x^2}\), and for a curve like \(x^3 + y^3 = 6xy\) you can't solve for \(y\) in any
                  useful way.</p>
                  <p>The curve still has a slope at each point. <b>Implicit differentiation</b> finds it without ever
                  solving for \(y\).</p>""",
                  {"view": [-8, 8, -6.5, 6.5], "alt": "A circle of radius 5 with the tangent line at the point 3, 4",
                   "curves": [{"f": "sqrt(25-x^2)", "dom": [-5, 5]}, {"f": "-sqrt(25-x^2)", "dom": [-5, 5]}],
                   "segments": [{"from": [-0.2, 6.4], "to": [6.2, 1.6], "style": "hi"}],
                   "points": [{"at": [3, 4], "label": "(3, 4)", "pos": "sw"}]},
                  r"The circle \(x^2 + y^2 = 25\) is not the graph of one function, and it still has a tangent at \((3, 4)\). The worked example finds its slope: \(-\frac34\)."),
            block("The one idea: y is a function of x",
                  r"""<p>Treat \(y\) as a function of \(x\) whose formula you don't know. Then anything built from \(y\) is a
                  function inside a function, and the chain rule applies with \(y\) as the inside:</p>
                  <ul><li>\(\dfrac{d}{dx}\,x^2 = 2x\), as always.</li>
                  <li>\(\dfrac{d}{dx}\,y^2 = 2y\cdot\dfrac{dy}{dx}\). The outside gives \(2y\), and the inside's derivative
                  is \(\dfrac{dy}{dx}\).</li>
                  <li>\(\dfrac{d}{dx}\,\sin y = \cos y\cdot\dfrac{dy}{dx}\).</li>
                  <li>\(\dfrac{d}{dx}\,(xy) = y + x\dfrac{dy}{dx}\), by the product rule.</li></ul>
                  <p>The rule of thumb: differentiate a \(y\) term the way you would an \(x\) term, then attach
                  \(\dfrac{dy}{dx}\).</p>"""),
            block("The four steps",
                  r"""<ol><li>Differentiate <b>both sides</b> of the equation with respect to \(x\).</li>
                  <li>Attach \(\dfrac{dy}{dx}\) every time you differentiate something with \(y\) in it.</li>
                  <li>Move every term with \(\dfrac{dy}{dx}\) to one side and everything else to the other.</li>
                  <li>Factor out \(\dfrac{dy}{dx}\) and divide.</li></ol>
                  <p>The answer usually has both \(x\) and \(y\) in it. That is normal: to get a slope you need both
                  coordinates of the point.</p>"""),
        ],
        "examples": [
            ex(r"Find \(\dfrac{dy}{dx}\) if \(x^2 + y^3 = 10\).",
               [r"Differentiate both sides. \(x^2\) gives \(2x\). \(y^3\) gives \(3y^2\dfrac{dy}{dx}\). The constant 10 gives 0.",
                r"So \(2x + 3y^2\dfrac{dy}{dx} = 0\).",
                r"Move the \(2x\) across: \(3y^2\dfrac{dy}{dx} = -2x\). Divide by \(3y^2\)."],
               r"\(\dfrac{dy}{dx} = -\dfrac{2x}{3y^2}\)"),
            "main",
            ex(r"Find the tangent line to \(x^2 + xy + y^2 = 7\) at the point \((1, 2)\).",
               [r"Check the point is on the curve: \(1 + 2 + 4 = 7\). ✓",
                r"Differentiate both sides. \(xy\) needs the product rule: \(2x + \left(y + x\dfrac{dy}{dx}\right) + 2y\dfrac{dy}{dx} = 0\).",
                r"Collect the \(\dfrac{dy}{dx}\) terms: \((x + 2y)\dfrac{dy}{dx} = -(2x + y)\), so \(\dfrac{dy}{dx} = -\dfrac{2x + y}{x + 2y}\).",
                r"At \((1, 2)\): \(-\dfrac{2 + 2}{1 + 4} = -\dfrac45\).",
                r"Point-slope form: \(y - 2 = -\frac45(x - 1)\)."],
               r"\(y = -\frac45x + \frac{14}{5}\)"),
        ],
        "steps": {
            0: [r"Differentiate both sides. Left: \(3x^2 + 3y^2y'\). Right, by the product rule: \(6y + 6xy'\).",
                r"Put the \(y'\) terms on the left and the rest on the right: \(3y^2y' - 6xy' = 6y - 3x^2\).",
                r"Factor: \(y'(3y^2 - 6x) = 6y - 3x^2\).",
                r"Divide, and cancel the 3: \(y' = \dfrac{2y - x^2}{y^2 - 2x}\)."],
            1: [r"Left side: \(\sin y\) has \(y\) inside, so it gives \(\cos y\cdot y'\). Right side: \(x\) gives 1.",
                r"\(\cos y\cdot y' = 1\), so \(y' = \dfrac{1}{\cos y}\)."],
        },
        "quiz": [
            mc(r"\(\dfrac{d}{dx}\left[xy\right] =\)", [r"\(y\)", r"\(x\dfrac{dy}{dx}\)", r"\(y + x\dfrac{dy}{dx}\)", r"\(\dfrac{dy}{dx}\)"], 2,
               r"Product rule: the derivative of \(x\) times \(y\), plus \(x\) times the derivative of \(y\)."),
            mc(r"On the circle \(x^2 + y^2 = 1\), \(\dfrac{dy}{dx} = -\dfrac xy\). The slope at \((0, 1)\) is:", ["0", "1", "−1", "undefined"], 0,
               "The top of the circle, where the tangent is flat."),
            mc(r"If \(y^3 = x\), then \(\dfrac{dy}{dx} =\)", [r"\(3y^2\)", r"\(\dfrac{1}{3y^2}\)", r"\(\dfrac13\)", r"\(3x^2\)"], 1,
               r"\(3y^2\dfrac{dy}{dx} = 1\)."),
        ],
    },

    # ============================ WEEKS 8 AND 9: THE FTC, SUBSTITUTION ============================
    "ftc": {
        "learn": [
            block("Two ideas that turn out to be one",
                  r"""<p>Up to now calculus has had two separate halves. Derivatives measure <b>slopes</b>. Integrals measure
                  <b>areas</b>, and last lesson that meant adding up more and more rectangles.</p>
                  <p>The Fundamental Theorem says the two halves undo each other. That has a very practical
                  consequence: you can find an exact area by <b>antidifferentiating</b>, with no rectangles at all.</p>"""),
            block("Part 2: the shortcut for areas",
                  r"""<p>To work out \(\displaystyle\int_a^b f(x)\,dx\):</p>
                  <ol><li>Find an antiderivative \(F\), a function whose derivative is \(f\).</li>
                  <li>Work out \(F\) at the top limit and at the bottom limit.</li>
                  <li>Subtract: <b>top minus bottom</b>, \(F(b) - F(a)\).</li></ol>
                  <p>The bracket \(\Big[F(x)\Big]_a^b\) is shorthand for \(F(b) - F(a)\). You will see it in every
                  solution.</p>
                  <p>Leave out the \(+C\). With it you would get \(\big(F(b) + C\big) - \big(F(a) + C\big)\), and the two
                  \(C\)s cancel.</p>""",
                  {"view": [0, 2.4, 0, 4.6], "alt": "The area under the curve y equals x squared between x equals 0 and x equals 2, shaded",
                   "shade": [{"f": "x^2", "dom": [0, 2]}], "curves": [{"f": "x^2"}],
                   "segments": [{"from": [2, 0], "to": [2, 4], "style": "dash"}],
                   "labels": [{"at": [1.5, 0.8], "text": "area = 8/3", "pos": "n"}]},
                  r"The worked example's area under \(y = x^2\) from 0 to 2. Rectangles could only close in on it. The antiderivative \(\frac{x^3}{3}\) gives it exactly: \(\frac83\)."),
            block("Why it works: speed and distance",
                  r"""<p>Drive at a steady 60 km/h for 2 hours and you cover 120 km: a rectangle of height 60 and width 2
                  under the speed graph. When the speed changes, the distance is still the area under the speed
                  graph, which is the integral of the speed.</p>
                  <p>There is a second way to get the distance: read the odometer at the end and at the start, and
                  subtract. Position is an antiderivative of speed, because speed is the derivative of position. So
                  the area under the speed graph equals the change in its antiderivative. That is Part 2, and it is
                  also called the <b>net change</b> rule: the integral of a rate of change is the total change.</p>"""),
            block("Part 1: the area-so-far function",
                  r"""<p>Fix a starting point \(a\) and let the right-hand edge move. The area collected so far depends on
                  where the edge is, so it is a function of \(x\):</p>
                  \[A(x) = \int_a^x f(t)\,dt\]
                  <p>(The letter \(t\) is only a placeholder, used because \(x\) is busy being the edge.) Push the edge a
                  little to the right and the area grows by a thin strip whose height is \(f(x)\). So the area grows
                  at a rate equal to the height of the curve: \(A'(x) = f(x)\). That is Part 1.</p>
                  <p>If the top limit is a function such as \(x^2\) and not a plain \(x\), the chain rule adds its
                  derivative: replace \(t\) with the top limit, then multiply by the top limit's derivative.</p>"""),
        ],
        "examples": [
            ex(r"Evaluate \(\displaystyle\int_1^3 2x\,dx\), and check it with geometry.",
               [r"An antiderivative of \(2x\) is \(x^2\).",
                r"\(\Big[x^2\Big]_1^3 = 3^2 - 1^2 = 9 - 1 = 8\).",
                r"Check: the region under the line \(y = 2x\) from 1 to 3 is a trapezoid with parallel sides 2 and 6 and width 2. Its area is \(\frac{2 + 6}{2}\cdot 2 = 8\). ✓"],
               r"\(8\)"),
            "main",
            ex(r"Evaluate \(\displaystyle\int_0^2\left(3x^2 - 4x + 1\right)dx\).",
               [r"Antidifferentiate term by term: \(F(x) = x^3 - 2x^2 + x\).",
                r"Top limit: \(F(2) = 8 - 8 + 2 = 2\).",
                r"Bottom limit: \(F(0) = 0\).",
                r"Top minus bottom: \(2 - 0\)."],
               r"\(2\)"),
        ],
        "steps": {
            0: [r"Write the root as a power: \(\sqrt{x} = x^{1/2}\). Add 1 to the power and divide by the new power: \(F(x) = \frac23x^{3/2}\).",
                r"Top limit: \(4^{3/2} = (\sqrt4)^3 = 8\), so \(F(4) = \frac{16}{3}\).",
                r"Bottom limit: \(F(1) = \frac23\).",
                r"Top minus bottom: \(\frac{16}{3} - \frac23 = \frac{14}{3}\)."],
            1: [r"Part 1 says: replace \(t\) with the top limit. That gives \(\cos(x^2)\).",
                r"The top limit is \(x^2\), not a plain \(x\), so multiply by its derivative, \(2x\).",
                r"\(2x\cos(x^2)\)."],
            2: [r"An antiderivative of \(\sin x\) is \(-\cos x\) (check: its derivative is \(\sin x\)).",
                r"Top limit: \(-\cos\pi = -(-1) = 1\). Bottom limit: \(-\cos 0 = -1\).",
                r"Top minus bottom: \(1 - (-1) = 2\)."],
        },
        "quiz": [
            mc(r"\(\displaystyle\int_1^2 4x^3\,dx =\)", ["16", "15", "12", "28"], 1, r"\(\Big[x^4\Big]_1^2 = 16 - 1\)."),
            mc(r"\(F' = f\), \(F(1) = 3\) and \(F(5) = 10\). Then \(\displaystyle\int_1^5 f(x)\,dx =\)", ["13", "7", "−7", "30"], 1,
               r"Top minus bottom: \(F(5) - F(1) = 10 - 3\)."),
        ],
    },
    "u-sub": {
        "learn": [
            block("Run the chain rule backwards",
                  r"""<p>The chain rule says \(\dfrac{d}{dx}\sin(x^2) = \cos(x^2)\cdot 2x\). Read that from right to left and it
                  is an integral you can do:</p>
                  \[\int\cos(x^2)\cdot 2x\,dx = \sin(x^2) + C\]
                  <p>Every chain rule derivative has this shape: an outside function with an inside function in it,
                  <b>times the derivative of the inside</b>. Substitution is how you spot that shape in an integral
                  and undo it.</p>"""),
            block("The method",
                  r"""<ol><li><b>Choose \(u\)</b>: the inside function, the one whose derivative is also sitting in the
                  integral.</li>
                  <li><b>Find \(du\)</b>: differentiate \(u\) and attach \(dx\). If \(u = x^2\) then \(du = 2x\,dx\).</li>
                  <li><b>Rewrite everything</b> in terms of \(u\). The \(dx\) has to go as well: it is part of \(du\).</li>
                  <li><b>Integrate</b> in \(u\). It should now be one of the basic integrals.</li>
                  <li><b>Put \(x\) back.</b></li></ol>
                  <p>You can always check the answer: differentiate it, and you should get back what you started
                  with.</p>"""),
            block("When the number in front is off",
                  r"""<p>Take \(\displaystyle\int x\cos(x^2)\,dx\). With \(u = x^2\) you need \(du = 2x\,dx\), and the integral
                  only has \(x\,dx\). Solve for what you do have: \(x\,dx = \frac12\,du\). The integral becomes
                  \(\frac12\displaystyle\int\cos u\,du = \frac12\sin(x^2) + C\).</p>
                  <p>This works for a missing <b>number</b> only. If what's missing has an \(x\) in it, you cannot
                  patch it up, and that choice of \(u\) doesn't work.</p>"""),
            block("Definite integrals: change the limits",
                  r"""<p>The limits on \(\displaystyle\int_a^b\) are values of \(x\). Once the integral is written in \(u\),
                  they have to be values of \(u\): put each limit into the formula for \(u\). Then finish in \(u\).
                  There is no need to go back to \(x\).</p>"""),
        ],
        "examples": [
            ex(r"Compute \(\displaystyle\int 2(2x + 1)^3\,dx\).",
               [r"The inside is \(2x + 1\). Let \(u = 2x + 1\), so \(du = 2\,dx\), and that 2 is already there.",
                r"The integral becomes \(\displaystyle\int u^3\,du = \frac{u^4}{4} + C\).",
                r"Put \(x\) back: \(\dfrac{(2x + 1)^4}{4} + C\).",
                r"Check by differentiating: \(\frac14\cdot 4(2x + 1)^3\cdot 2 = 2(2x + 1)^3\). ✓"],
               r"\(\dfrac{(2x + 1)^4}{4} + C\)"),
            "main",
            ex(r"Compute \(\displaystyle\int x^2\sqrt{x^3 + 1}\,dx\).",
               [r"The inside is \(x^3 + 1\). Let \(u = x^3 + 1\), so \(du = 3x^2\,dx\).",
                r"The integral has \(x^2\,dx\), which is \(\frac13\,du\).",
                r"It becomes \(\frac13\displaystyle\int u^{1/2}\,du = \frac13\cdot\frac23u^{3/2} + C = \frac29u^{3/2} + C\).",
                r"Put \(x\) back."],
               r"\(\frac29(x^3 + 1)^{3/2} + C\)"),
            ex(r"Evaluate \(\displaystyle\int_0^2\frac{x}{x^2 + 1}\,dx\).",
               [r"Let \(u = x^2 + 1\), so \(du = 2x\,dx\) and \(x\,dx = \frac12\,du\).",
                r"Change the limits: \(x = 0\) gives \(u = 1\), and \(x = 2\) gives \(u = 5\).",
                r"The integral becomes \(\frac12\displaystyle\int_1^5\frac1u\,du = \frac12\Big[\ln u\Big]_1^5\).",
                r"\(\frac12(\ln 5 - \ln 1) = \frac12\ln 5\), since \(\ln 1 = 0\)."],
               r"\(\frac12\ln 5 \approx 0.805\)"),
        ],
        "steps": {
            0: [r"The inside is \(x^2 + 1\). Let \(u = x^2 + 1\), so \(du = 2x\,dx\) and \(x\,dx = \frac12\,du\).",
                r"The integral becomes \(\frac12\displaystyle\int u^4\,du = \frac12\cdot\frac{u^5}{5} + C\).",
                r"Put \(x\) back: \(\frac{1}{10}(x^2 + 1)^5 + C\)."],
            1: [r"Let \(u = 3x\), so \(du = 3\,dx\) and \(dx = \frac13\,du\).",
                r"Change the limits: \(x = 0\) gives \(u = 0\), and \(x = 1\) gives \(u = 3\).",
                r"\(\frac13\displaystyle\int_0^3 e^u\,du = \frac13\Big[e^u\Big]_0^3 = \frac13(e^3 - 1)\)."],
            2: [r"Write \(\tan x = \dfrac{\sin x}{\cos x}\). The bottom's derivative is almost the top, so let \(u = \cos x\).",
                r"\(du = -\sin x\,dx\), so \(\sin x\,dx = -du\).",
                r"The integral becomes \(-\displaystyle\int\frac1u\,du = -\ln|u| + C = -\ln|\cos x| + C\)."],
        },
        "quiz": [
            mc(r"\(\displaystyle\int\cos(5x)\,dx =\)", [r"\(\sin(5x) + C\)", r"\(5\sin(5x) + C\)", r"\(\frac15\sin(5x) + C\)", r"\(-\frac15\sin(5x) + C\)"], 2,
               r"\(u = 5x\), so \(dx = \frac15\,du\)."),
            mc(r"With \(u = x^2 + 1\), the integral \(\displaystyle\int_0^2 2x(x^2 + 1)^3\,dx\) becomes:",
               [r"\(\displaystyle\int_0^2 u^3\,du\)", r"\(\displaystyle\int_1^5 u^3\,du\)", r"\(\displaystyle\int_0^4 u^3\,du\)", r"\(\displaystyle\int_1^5 2u^3\,du\)"], 1,
               r"\(du = 2x\,dx\) uses up the \(2x\), and the limits become \(u(0) = 1\) and \(u(2) = 5\)."),
            mc(r"\(\displaystyle\int 2xe^{x^2}\,dx =\)", [r"\(e^{x^2} + C\)", r"\(2e^{x^2} + C\)", r"\(x^2e^{x^2} + C\)", r"\(\dfrac{e^{x^2}}{2x} + C\)"], 0,
               r"\(u = x^2\), \(du = 2x\,dx\), so it is \(\displaystyle\int e^u\,du\)."),
        ],
    },
    # ============================ PICTURES FOR OTHER LESSONS ============================
    "inverse-functions": picture(
        {"view": [-0.5, 5, -0.5, 5], "alt": "The curves y equals x squared and y equals the square root of x, mirror images in the line y equals x",
         "curves": [{"f": "x^2", "dom": [0, 5]}, {"f": "sqrt(x)", "dom": [0, 5]}, {"f": "x", "style": "dash"}],
         "points": [{"at": [2, 4], "label": "(2, 4)", "pos": "w"}, {"at": [4, 2], "label": "(4, 2)", "pos": "s"}]},
        r"\(\sqrt{x}\) is \(x^2\) (for \(x \ge 0\)) reflected in the dashed line \(y = x\). The point \((2, 4)\) on one becomes \((4, 2)\) on the other."),
    "exponential-functions": picture(
        {"view": [-4, 4, -0.5, 8], "alt": "The curves y equals 2 to the x, rising, and y equals one half to the x, falling",
         "curves": [{"f": "2^x"}, {"f": "0.5^x", "style": "dash"}], "points": [{"at": [0, 1], "label": "(0, 1)", "pos": "e"}],
         "tool": {"type": "trace", "start": 2, "read": "2 to the power {x} is {y}"}},
        r"Growth (\(2^x\), solid) and decay (\(\left(\frac12\right)^x\), dashed). Both pass through \((0, 1)\), and each flattens onto the \(x\)-axis on one side."),
    "trig-functions": picture(
        {"view": [-1, 7, -1.6, 1.6], "alt": "The sine curve with a tangent line you can slide along it, and the cosine curve dashed",
         "curves": [{"f": "sin(x)"}, {"f": "cos(x)", "style": "dash"}],
         "tool": {"type": "tangent", "start": 1, "read": "At x = {x} the slope of sin x is {m}."}},
        r"The solid curve is \(\sin x\) and the dashed one is \(\cos x\). At every \(x\), the slope of the solid curve is the height of the dashed one: that is \(\frac{d}{dx}\sin x = \cos x\)."),
    "log-functions": picture(
        {"view": [-3, 6, -3, 6], "alt": "The curves y equals e to the x and y equals the natural log of x, mirror images in the line y equals x",
         "curves": [{"f": "exp(x)"}, {"f": "ln(x)", "dom": [0.02, 6]}, {"f": "x", "style": "dash"}],
         "labels": [{"at": [1.4, 4.6], "text": "e to the x", "pos": "w"}, {"at": [4.4, 1.3], "text": "ln x", "pos": "s"}]},
        r"\(\ln x\) is the mirror image of \(e^x\) in the dashed line \(y = x\). Each one undoes the other."),
    "exp-log-derivatives": picture(
        {"view": [-0.5, 6, -3, 2.5], "alt": "The curve y equals the natural log of x with a tangent line you can slide along it",
         "curves": [{"f": "ln(x)", "dom": [0.05, 6]}],
         "tool": {"type": "tangent", "dom": [0.25, 6], "start": 1, "read": "At x = {x} the slope of ln x is {m}."}},
        r"The slope of \(\ln x\) at any point is 1 divided by the \(x\)-value there: steep near 0, and flatter the further right you go. That is \(\frac{d}{dx}\ln x = \frac1x\)."),
    "critical-points": picture(
        {"view": [-3.5, 5.5, -30, 12], "alt": "The cubic from the worked example, with a tangent line you can slide along it",
         "curves": [{"f": "x^3-3*x^2-9*x+2"}], "tool": {"type": "tangent", "start": -2, "read": "At x = {x} the slope is {m}."}},
        r"This is the function from the worked example. Slide to where the tangent goes flat: the peak at \(x = -1\) and the valley at \(x = 3\). A positive slope means the graph is rising, a negative one that it is falling."),
    "concavity": picture(
        {"view": [-3.5, 5.5, -30, 12], "alt": "The same cubic, with its inflection point marked and a tangent line you can slide along it",
         "curves": [{"f": "x^3-3*x^2-9*x+2"}], "points": [{"at": [1, -9], "label": "inflection point (1, −9)", "pos": "e"}],
         "tool": {"type": "tangent", "start": -1.5, "read": "At x = {x} the slope is {m}."}},
        r"Left of \(x = 1\) the curve bends downward and the tangent sits above it. Right of \(x = 1\) it bends upward and the tangent sits below. The switch happens at the inflection point."),
    "curve-sketching": picture(
        {"view": [-6, 6, -0.8, 0.8], "alt": "The finished sketch of x over x squared plus 1, with its peak, valley and inflection points",
         "curves": [{"f": "x/(x^2+1)"}],
         "points": [{"at": [1, 0.5], "label": "peak (1, ½)", "pos": "n"}, {"at": [-1, -0.5], "label": "valley (−1, −½)", "pos": "s"},
                    {"at": [1.732, 0.433], "open": True}, {"at": [-1.732, -0.433], "open": True}, {"at": [0, 0], "open": True}],
         "tool": {"type": "trace", "start": 3, "read": "x = {x}, f(x) = {y}"}},
        r"The finished sketch of \(\dfrac{x}{x^2 + 1}\) from the worked example. The open circles are the three inflection points, and both ends flatten onto the \(x\)-axis."),
    "ivt": picture(
        {"view": [-0.3, 1.4, -1.4, 1.6], "alt": "A curve that starts below the x-axis where x is 0 and ends above it where x is 1",
         "curves": [{"f": "x^3+x-1"}],
         "points": [{"at": [0, -1], "label": "f(0) = −1", "pos": "e"}, {"at": [1, 1], "label": "f(1) = 1", "pos": "w"},
                    {"at": [0.6823, 0], "open": True, "label": "it must cross", "pos": "se"}]},
        r"The curve \(y = x^3 + x - 1\) starts below the axis and ends above it, with no break in between. So it has to cross somewhere, and that crossing is a root."),
    "mvt": picture(
        {"view": [0, 4, -1, 10], "alt": "A parabola with a line joining two of its points and a parallel tangent line between them",
         "curves": [{"f": "x^2"}],
         "segments": [{"from": [1, 1], "to": [3, 9], "style": "hi"}, {"from": [1.1, 0.4], "to": [2.9, 7.6], "style": "dash"}],
         "points": [{"at": [1, 1]}, {"at": [3, 9]}, {"at": [2, 4], "label": "c = 2", "pos": "se"}]},
        r"The yellow line joins the endpoints of \(y = x^2\) on \([1, 3]\): average slope 4. At \(c = 2\) the tangent (dashed) is parallel to it. The Mean Value Theorem promises at least one point like that."),
    "newtons-method": picture(
        {"view": [0, 2.2, -1.6, 3], "alt": "The curve y equals x squared minus 2, with the tangent steps of Newton's method",
         "curves": [{"f": "x^2-2"}], "points": [{"at": [1.41421, 0], "open": True, "label": "√2", "pos": "se"}],
         "tool": {"type": "newton", "x0": 1}},
        r"The worked example, one tangent at a time. Each step slides down the tangent to the axis and starts again from there. Three steps from \(x_0 = 1\) agree with \(\sqrt2\) to four decimals."),
    "optimization": picture(
        {"view": [0, 50, 0, 700], "alt": "The area of the fenced rectangle as a hill-shaped curve against its width",
         "curves": [{"f": "x*(50-x)"}], "tool": {"type": "trace", "start": 10, "read": "A width of {x} m gives an area of {y} m²."}},
        r"The area \(A = x(50 - x)\) from the worked example. Slide to the top of the hill: a width of 25 m, where the tangent is flat."),
    "antiderivatives": picture(
        {"view": [-3, 3, -4, 8], "alt": "A parabola that slides up and down as the constant C changes",
         "curves": [{"f": "x^2+C"}], "tool": {"type": "family", "params": {"C": [-3, 5, 0, 0.5]}, "read": "y = x² + C with C = {C}"}},
        r"Every antiderivative of \(2x\) is this parabola slid up or down. Sliding it changes no slope anywhere, which is why a derivative can't see the \(+C\)."),
    "area-under-curves": picture(
        {"view": [0, 2.2, 0, 4.4], "alt": "Rectangles under the curve y equals x squared between 0 and 2",
         "curves": [{"f": "x^2"}], "tool": {"type": "riemann", "dom": [0, 2], "start": 4, "max": 50, "exact": 2.6666667}},
        r"The worked example's area under \(y = x^2\) from 0 to 2. Add rectangles and the total closes in on the exact area, \(\frac83\)."),
    "area-between": picture(
        {"view": [-0.2, 1.4, -0.2, 1.4], "alt": "The region between the line y equals x and the parabola y equals x squared",
         "shade": [{"f": "x", "g": "x^2", "dom": [0, 1]}], "curves": [{"f": "x"}, {"f": "x^2"}],
         "points": [{"at": [0, 0]}, {"at": [1, 1]}],
         "labels": [{"at": [0.55, 0.62], "text": "y = x", "pos": "nw"}, {"at": [0.8, 0.6], "text": "y = x²", "pos": "se"}]},
        r"The worked example's region: \(y = x\) on top and \(y = x^2\) underneath, meeting at \(x = 0\) and \(x = 1\). Its area is \(\frac16\)."),
    "average-value": picture(
        {"view": [0, 3.4, 0, 10], "alt": "The area under y equals x squared from 0 to 3, and a horizontal line at its average height",
         "shade": [{"f": "x^2", "dom": [0, 3]}], "curves": [{"f": "x^2", "dom": [0, 3]}], "hlines": [3],
         "segments": [{"from": [3, 0], "to": [3, 9], "style": "dash"}],
         "points": [{"at": [1.732, 3], "label": "c = √3", "pos": "nw"}]},
        r"The dashed line is the average height of \(x^2\) on \([0, 3]\), which is 3. A rectangle of that height over \([0, 3]\) has the same area as the shaded region, and the curve passes through that height at \(c = \sqrt3\)."),
    "direction-fields": picture(
        {"view": [-0.4, 6, -1, 3.5], "alt": "The direction field of y prime equals y times 2 minus y",
         "hlines": [0, 2], "tool": {"type": "field", "F": "y*(2-y)", "x": 0, "starts": [0.3, 1, 3, -0.15]}},
        r"The direction field of \(y' = y(2 - y)\) from the worked example. A solution that starts anywhere above 0 settles onto \(y = 2\) (stable). One that starts below 0 runs away from \(y = 0\) (unstable)."),
    "eulers-method": picture(
        {"view": [0, 1.1, 0.8, 3.8], "alt": "The true solution curve and the straight steps of Euler's method beside it",
         "curves": [{"f": "2*exp(x)-x-1"}], "tool": {"type": "euler", "F": "x+y", "x0": 0, "y0": 1, "to": 1}},
        r"The curve is the true solution of \(y' = x + y\), \(y(0) = 1\). The yellow path is Euler's method. Smaller steps stay closer to the curve, and the gap at the end roughly halves when the step does."),
}