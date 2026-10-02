r"""Extra topics beyond the 12-week course (series, vectors, multiple integrals, ...).

Math is written in LaTeX: \( ... \) for inline math. Formulas are listed as
[label, latex] and are shown as display math by the website.
Avoid a bare "<" in text (it breaks HTML); use \lt inside math instead.
"""


def lesson(id, course, name, keywords, level, minutes, prereqs, idea,
           formulas, example, mistakes, practice, quiz):
    return {
        "id": id, "course": course, "name": name, "keywords": keywords,
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


EXTRA_LESSONS = [
    lesson(
        "related-rates", 1, "Related Rates", "related rates ladder balloon dt",
        "Intermediate", 25, ["implicit"],
        r"Two or more quantities are linked by an equation and they all change over time. Differentiate the equation "
        r"with respect to <b>time \(t\)</b> to get an equation linking their rates. <b>Recipe:</b> (1) draw a picture, "
        r"(2) list what you know and what you want, (3) write an equation relating the quantities, "
        r"(4) differentiate with respect to \(t\), (5) only <i>then</i> plug in the numbers.",
        [
            ["Circle area", r"A=\pi r^2 \;\Rightarrow\; \frac{dA}{dt} = 2\pi r\frac{dr}{dt}"],
            ["Pythagoras", r"x^2+y^2=z^2 \;\Rightarrow\; x\frac{dx}{dt}+y\frac{dy}{dt}=z\frac{dz}{dt}"],
            ["Sphere volume", r"V=\tfrac43\pi r^3 \;\Rightarrow\; \frac{dV}{dt} = 4\pi r^2\frac{dr}{dt}"],
        ],
        ex(r"A ripple's radius grows at 2 cm/s. How fast is the area growing when \(r=5\) cm?",
           [r"Equation linking them: \(A=\pi r^2\).",
            r"Differentiate with respect to \(t\): \(\frac{dA}{dt}=2\pi r\frac{dr}{dt}\).",
            r"Now plug in \(r=5\) and \(\frac{dr}{dt}=2\): \(2\pi(5)(2)\)."],
           r"\(20\pi\approx 62.8\) cm²/s"),
        [r"Plugging in numbers <i>before</i> differentiating. That turns changing quantities into constants and their rates become 0.",
         r"Getting the sign wrong. A quantity that is shrinking has a <b>negative</b> rate.",
         r"Mixing up units, e.g. feet and inches, or seconds and minutes."],
        [pr(r"A 10 ft ladder slides down a wall. The bottom moves away at 1 ft/s. How fast does the top fall when the bottom is 6 ft from the wall?",
            r"\(x^2+y^2=100\). When \(x=6\), \(y=8\).",
            r"\(2x x' + 2y y' = 0\Rightarrow 6(1)+8y'=0\Rightarrow y'=-\frac34\). The top falls at \(\frac34\) ft/s."),
         pr(r"A sphere's volume grows at \(4\pi\) cm³/s. How fast is the radius growing when \(r=1\)?",
            r"\(\frac{dV}{dt}=4\pi r^2\frac{dr}{dt}\)", r"\(4\pi = 4\pi(1)^2\frac{dr}{dt}\Rightarrow \frac{dr}{dt}=1\) cm/s")],
        [mc("When should you plug in the specific numbers?", ["Before differentiating", "After differentiating", "Never", "Only at the very start"], 1,
            "Differentiate first, while everything is still a variable."),
         mc(r"A square's side grows at 3 m/s. How fast is the area growing when the side is 4 m?", ["12", "24", "48", "16"], 1,
            r"\(A=s^2\Rightarrow A'=2s\,s' = 2(4)(3)=24\) m²/s.")],
    ),
    lesson(
        "lhopital", 1, "L'Hôpital's Rule", "lhopital l'hopital indeterminate 0/0 infinity",
        "Intermediate", 15, ["limits", "derivative-rules"],
        r"If plugging in gives \(\frac00\) or \(\frac{\infty}{\infty}\), you can replace \(\frac{f}{g}\) with "
        r"\(\frac{f'}{g'}\): differentiate the top and bottom <b>separately</b> (not the quotient rule!) and try "
        r"the limit again. You can repeat this if it is still indeterminate.",
        [
            [r"L'Hôpital's rule (for \(\frac00\) or \(\frac\infty\infty\) only)", r"\lim_{x\to a}\frac{f(x)}{g(x)} = \lim_{x\to a}\frac{f'(x)}{g'(x)}"],
            [r"Turn \(0\cdot\infty\) into a fraction", r"f\cdot g = \frac{f}{1/g}"],
            [r"For \(1^\infty,\ 0^0,\ \infty^0\): take logs first", r"y=f^g \;\Rightarrow\; \ln y = g\ln f"],
        ],
        ex(r"Find \(\displaystyle\lim_{x\to 0}\frac{e^x-1-x}{x^2}\).",
           [r"Plug in: \(\frac{1-1-0}{0}=\frac00\). Indeterminate, so L'Hôpital applies.",
            r"Differentiate top and bottom: \(\frac{e^x-1}{2x}\). Still \(\frac00\).",
            r"Apply it again: \(\frac{e^x}{2}\).",
            r"Plug in \(x=0\): \(\frac12\)."],
           r"\(\frac12\)"),
        ["Using the quotient rule. L'Hôpital differentiates the top and bottom separately.",
         r"Using it when the limit is not \(\frac00\) or \(\frac\infty\infty\). It gives wrong answers then.",
         r"Forgetting to rewrite \(0\cdot\infty\) or \(\infty-\infty\) as a fraction first."],
        [pr(r"\(\displaystyle\lim_{x\to 0}\frac{\sin 5x}{x}\)", r"\(\frac00\), so differentiate top and bottom.", r"\(\frac{5\cos 5x}{1}\to 5\)"),
         pr(r"\(\displaystyle\lim_{x\to\infty}\frac{\ln x}{x}\)", r"\(\frac\infty\infty\).", r"\(\frac{1/x}{1}\to 0\)"),
         pr(r"\(\displaystyle\lim_{x\to 0^+}x\ln x\)", r"Rewrite as \(\frac{\ln x}{1/x}\).", r"\(\frac{1/x}{-1/x^2}=-x\to 0\)")],
        [mc(r"\(\displaystyle\lim_{x\to 0}\frac{1-\cos x}{x^2}=\)", ["0", r"\(\frac12\)", "1", r"\(\infty\)"], 1,
            r"Once gives \(\frac{\sin x}{2x}\); again gives \(\frac{\cos x}{2}\to\frac12\)."),
         mc("L'Hôpital's rule applies directly to which form?", [r"\(\frac00\)", r"\(\frac10\)", r"\(0\cdot\infty\)", r"\(\frac23\)"], 0,
            r"Only \(\frac00\) and \(\frac\infty\infty\). \(0\cdot\infty\) must be rewritten first."),
         mc(r"\(\displaystyle\lim_{x\to\infty}\frac{x^2}{e^x}=\)", [r"\(\infty\)", "1", "0", "2"], 2,
            r"Twice: \(\frac{2}{e^x}\to 0\). Exponentials beat polynomials.")],
    ),
    lesson(
        "ibp", 2, "Integration by Parts", "parts ibp integral liate tabular",
        "Intermediate", 25, ["u-sub"],
        r"Integration by parts is the <b>product rule in reverse</b>, used when the integrand is a product of two "
        r"different types of functions. Choose \(u\) to be the part that gets <i>simpler</i> when you differentiate it. "
        r"The acronym <b>LIATE</b> (Logs, Inverse trig, Algebraic, Trig, Exponential) gives a good order for picking \(u\).",
        [
            ["Integration by parts", r"\int u\,dv = uv - \int v\,du"],
            [r"Choosing \(u\) (first in the list wins)", r"\text{L}\text{ogs} \to \text{I}\text{nverse trig} \to \text{A}\text{lgebraic} \to \text{T}\text{rig} \to \text{E}\text{xponential}"],
        ],
        ex(r"Compute \(\displaystyle\int xe^x\,dx\).",
           [r"\(x\) is Algebraic and \(e^x\) is Exponential, so \(u=x\) and \(dv=e^x\,dx\).",
            r"Then \(du=dx\) and \(v=e^x\).",
            r"Plug in: \(xe^x-\int e^x\,dx\).",
            r"\(=xe^x-e^x+C\)."],
           r"\(e^x(x-1)+C\)"),
        [r"Choosing a \(u\) that gets more complicated, which makes the new integral harder.",
         r"Sign errors in \(uv-\int v\,du\).",
         r"Going in circles with integrals like \(\int e^x\sin x\,dx\). Apply parts twice, then solve for the integral algebraically."],
        [pr(r"\(\displaystyle\int\ln x\,dx\)", r"\(u=\ln x\), \(dv=dx\).", r"\(x\ln x-x+C\)"),
         pr(r"\(\displaystyle\int x\cos x\,dx\)", r"\(u=x\), \(dv=\cos x\,dx\).", r"\(x\sin x+\cos x+C\)"),
         pr(r"\(\displaystyle\int x^2e^x\,dx\)", "Apply parts twice, or use the tabular method.", r"\(e^x(x^2-2x+2)+C\)")],
        [mc(r"For \(\displaystyle\int x\sin x\,dx\), choose \(u=\)", [r"\(x\)", r"\(\sin x\)", r"\(x\sin x\)", r"\(\cos x\)"], 0, "Algebraic comes before Trig in LIATE."),
         mc(r"\(\displaystyle\int xe^{2x}\,dx=\)", [r"\(e^{2x}\left(\frac x2-\frac14\right)+C\)", r"\(\frac{xe^{2x}}{2}+C\)", r"\(e^{2x}(x-1)+C\)", r"\(\frac{x^2e^{2x}}{2}+C\)"], 0,
            r"\(u=x,\ v=\frac12e^{2x}\): \(\frac x2e^{2x}-\frac14e^{2x}+C\).")],
    ),
    lesson(
        "trig-integrals", 2, "Trig Integrals & Substitution", "trig sub integral sin cos sqrt identity",
        "Advanced", 35, ["u-sub"],
        r"For powers of sine and cosine, use identities to rewrite the integrand. With an <b>odd</b> power, save one "
        r"factor and convert the rest using \(\sin^2+\cos^2=1\). With <b>even</b> powers, use the half-angle formulas. "
        r"For square roots like \(\sqrt{a^2-x^2}\), substitute a trig function so the root simplifies away.",
        [
            ["Pythagorean identity", r"\sin^2x+\cos^2x=1"],
            ["Half-angle formulas", r"\sin^2 x = \frac{1-\cos 2x}{2},\qquad \cos^2 x = \frac{1+\cos 2x}{2}"],
            ["Trig substitution", r"\sqrt{a^2-x^2}:\ x=a\sin\theta \qquad \sqrt{a^2+x^2}:\ x=a\tan\theta \qquad \sqrt{x^2-a^2}:\ x=a\sec\theta"],
            ["Results worth memorizing", r"\int\frac{dx}{\sqrt{1-x^2}}=\arcsin x+C,\qquad \int\frac{dx}{1+x^2}=\arctan x+C"],
        ],
        ex(r"Compute \(\displaystyle\int\sin^2x\,dx\).",
           [r"Even power, so use the half-angle formula: \(\sin^2x=\frac{1-\cos 2x}{2}\).",
            r"\(\int\frac12\,dx-\int\frac{\cos 2x}{2}\,dx\).",
            r"\(=\frac x2-\frac{\sin 2x}{4}+C\)."],
           r"\(\frac x2-\frac{\sin 2x}{4}+C\)"),
        [r"Forgetting to convert \(dx\) (for example \(x=a\sin\theta\) gives \(dx=a\cos\theta\,d\theta\)).",
         r"Not converting back to \(x\) at the end. Draw a right triangle to help.",
         "Using half-angle formulas on odd powers, where saving one factor is much easier."],
        [pr(r"\(\displaystyle\int\sin^3x\,dx\)", r"Write \(\sin^3x=(1-\cos^2x)\sin x\) and let \(u=\cos x\).", r"\(-\cos x+\frac{\cos^3x}{3}+C\)"),
         pr(r"\(\displaystyle\int\frac{dx}{\sqrt{1-x^2}}\)", r"\(x=\sin\theta\).", r"\(\arcsin x+C\)"),
         pr(r"\(\displaystyle\int\frac{dx}{1+x^2}\)", r"\(x=\tan\theta\).", r"\(\arctan x+C\)")],
        [mc(r"For \(\sqrt{9-x^2}\), substitute:", [r"\(x=3\sin\theta\)", r"\(x=3\tan\theta\)", r"\(x=3\sec\theta\)", r"\(x=9\sin\theta\)"], 0,
            r"\(9-9\sin^2\theta=9\cos^2\theta\)."),
         mc(r"\(\displaystyle\int\cos^2x\,dx=\)", [r"\(\frac x2+\frac{\sin 2x}{4}+C\)", r"\(\sin^2x+C\)", r"\(\frac{\cos^3x}{3}+C\)", r"\(\frac x2-\frac{\sin 2x}{4}+C\)"], 0,
            "Half-angle formula with a plus sign.")],
    ),
    lesson(
        "partial-fractions", 2, "Partial Fractions", "partial fractions rational decomposition",
        "Intermediate", 25, ["u-sub"],
        r"A rational function (polynomial over polynomial) can be split into a sum of simpler fractions, which "
        r"integrate to logs and arctans. Factor the bottom, write the right form for each factor, then solve for "
        r"the unknown constants. Tip: plugging in the roots of the bottom finds the constants fast.",
        [
            ["Distinct linear factors", r"\frac{P(x)}{(x-a)(x-b)} = \frac{A}{x-a}+\frac{B}{x-b}"],
            ["Repeated factor", r"\frac{P(x)}{(x-a)^2} = \frac{A}{x-a}+\frac{B}{(x-a)^2}"],
            ["Irreducible quadratic", r"\frac{Ax+B}{x^2+c}"],
            ["Top degree ≥ bottom degree?", r"\text{Do polynomial long division first}"],
        ],
        ex(r"Compute \(\displaystyle\int\frac{1}{x^2-1}\,dx\).",
           [r"Factor: \(\frac{1}{(x-1)(x+1)}=\frac{A}{x-1}+\frac{B}{x+1}\).",
            r"Multiply out: \(1=A(x+1)+B(x-1)\).",
            r"Plug in \(x=1\): \(A=\frac12\). Plug in \(x=-1\): \(B=-\frac12\).",
            r"Integrate each piece: \(\frac12\ln|x-1|-\frac12\ln|x+1|+C\)."],
           r"\(\frac12\ln\left|\frac{x-1}{x+1}\right|+C\)"),
        ["Skipping long division when the top degree is too big.",
         r"Using the wrong form for repeated factors (you need one term for each power).",
         r"Forgetting the absolute value inside \(\ln\)."],
        [pr(r"\(\displaystyle\int\frac{3x+5}{(x+1)(x+2)}\,dx\)", r"\(3x+5=A(x+2)+B(x+1)\). Try \(x=-1\) and \(x=-2\).", r"\(A=2,\ B=1\): \(2\ln|x+1|+\ln|x+2|+C\)"),
         pr(r"\(\displaystyle\int\frac{x+1}{x^2}\,dx\)", r"Split it into \(\frac1x+\frac1{x^2}\).", r"\(\ln|x|-\frac1x+C\)")],
        [mc(r"The partial-fraction form of \(\frac{1}{x(x+3)}\) is:", [r"\(\frac Ax+\frac B{x+3}\)", r"\(\frac Ax+\frac{Bx}{x+3}\)", r"\(\frac{Ax+B}{x(x+3)}\)", r"\(\frac A{x^2}+\frac B{x+3}\)"], 0,
            "Two distinct linear factors, so one constant over each."),
         mc("When do you need long division first?", ["When the top degree ≥ the bottom degree", "Always", "Never", "When the bottom has a square"], 0,
            "Partial fractions only works on proper fractions.")],
    ),
    lesson(
        "improper-integrals", 2, "Improper Integrals", "improper convergence divergence infinite p-test",
        "Intermediate", 20, ["riemann-ftc"],
        r"An integral is improper when a limit is infinite or the function blows up somewhere on the interval. "
        r"Replace the bad spot with a variable, integrate, and take a limit. If the limit is a finite number the "
        r"integral <b>converges</b>; otherwise it <b>diverges</b>.",
        [
            ["Infinite limit", r"\int_a^\infty f(x)\,dx = \lim_{t\to\infty}\int_a^t f(x)\,dx"],
            ["p-test", r"\int_1^\infty\frac{1}{x^p}\,dx \text{ converges} \iff p\gt 1"],
            ["Comparison", r"0\le f\le g \text{ and } \int g \text{ converges} \Rightarrow \int f \text{ converges}"],
        ],
        ex(r"Does \(\displaystyle\int_1^\infty\frac{1}{x^2}\,dx\) converge?",
           [r"Write it as a limit: \(\lim_{t\to\infty}\int_1^t x^{-2}\,dx\).",
            r"Integrate: \(\left[-\frac1x\right]_1^t = 1-\frac1t\).",
            r"As \(t\to\infty\), \(\frac1t\to 0\)."],
           "It converges to 1."),
        [r"Missing a blow-up inside the interval. \(\int_{-1}^{1}\frac{1}{x^2}dx\) diverges; it is not \(-2\).",
         r"Treating \(\infty\) like a regular number instead of taking a limit.",
         r"Mixing up the p-test. Convergence needs \(p\gt 1\)."],
        [pr(r"\(\displaystyle\int_1^\infty\frac{1}{\sqrt x}\,dx\)", r"p-test with \(p=\frac12\).", "Diverges."),
         pr(r"\(\displaystyle\int_0^1\frac{1}{\sqrt x}\,dx\)", r"The function blows up at 0. \(\int x^{-1/2}dx=2\sqrt x\).", "Converges to 2."),
         pr(r"\(\displaystyle\int_0^\infty e^{-x}\,dx\)", r"\(\left[-e^{-x}\right]_0^t\).", "Converges to 1.")],
        [mc(r"\(\displaystyle\int_1^\infty\frac1x\,dx\)", ["Converges to 1", "Diverges", "Converges to 0", r"\(\ln 2\)"], 1, r"\(\ln t\to\infty\). This is the \(p=1\) case."),
         mc(r"\(\displaystyle\int_1^\infty\frac{1}{x^3}\,dx=\)", [r"\(\frac12\)", r"\(\frac13\)", "Diverges", "1"], 0, r"\(\left[-\frac{1}{2x^2}\right]_1^\infty=\frac12\).")],
    ),
    lesson(
        "series-tests", 2, "Series Convergence Tests", "series ratio root comparison alternating geometric divergence harmonic",
        "Advanced", 40, ["limits", "improper-integrals"],
        r"An infinite series converges if its running total (the partial sums) settles on a single number. "
        r"The tests below tell you whether that happens without computing the sum. <b>Start with the divergence "
        r"test</b>: if the terms don't go to 0, you're done, it diverges. Then pick a test based on what the terms look like.",
        [
            ["Divergence test", r"\lim a_n \ne 0 \Rightarrow \sum a_n \text{ diverges}"],
            ["Geometric series", r"\sum_{n=0}^\infty ar^n = \frac{a}{1-r} \text{ if } |r|\lt 1"],
            ["p-series", r"\sum\frac{1}{n^p} \text{ converges} \iff p\gt 1"],
            ["Ratio test", r"L=\lim\left|\frac{a_{n+1}}{a_n}\right|:\quad L\lt 1 \text{ conv.},\ L\gt 1 \text{ div.},\ L=1 \text{ no info}"],
            ["Alternating series test", r"\sum(-1)^n b_n \text{ converges if } b_n \text{ decreases to } 0"],
        ],
        ex(r"Does \(\displaystyle\sum_{n=1}^\infty\frac{n}{2^n}\) converge?",
           [r"There's an exponential, so try the ratio test.",
            r"\(\frac{a_{n+1}}{a_n}=\frac{n+1}{2^{n+1}}\cdot\frac{2^n}{n}=\frac{n+1}{2n}\).",
            r"\(L=\lim\frac{n+1}{2n}=\frac12\).",
            r"\(L\lt 1\), so it converges."],
           "Converges (ratio test, L = 1/2)."),
        [r"Thinking \(a_n\to 0\) means it converges. The harmonic series \(\sum\frac1n\) has terms going to 0 but diverges.",
         r"Concluding anything when the ratio test gives \(L=1\).",
         "Mixing up the sequence (the terms) with the series (the sum)."],
        [pr(r"\(\displaystyle\sum\frac{1}{n^2}\)", "Which family of series is this?", r"p-series with \(p=2\gt 1\): converges."),
         pr(r"\(\displaystyle\sum\frac{(-1)^n}{n}\)", "Alternating series test.", r"Converges (conditionally, since \(\sum\frac1n\) diverges)."),
         pr(r"\(\displaystyle\sum_{n=0}^\infty 3\left(\tfrac23\right)^n\)", r"Geometric with \(a=3,\ r=\frac23\).", r"\(\frac{3}{1-2/3}=9\)"),
         pr(r"\(\displaystyle\sum\frac{n}{n+1}\)", "Check the divergence test first.", r"Terms \(\to 1\ne 0\): diverges.")],
        [mc(r"\(\displaystyle\sum_{n=1}^\infty\frac1n\)", ["Converges", "Diverges", "Converges to 1", "Depends"], 1, "The harmonic series diverges (p = 1)."),
         mc(r"\(\displaystyle\sum_{n=0}^\infty\left(\tfrac12\right)^n=\)", ["1", "2", r"\(\frac12\)", r"\(\infty\)"], 1, r"\(\frac{1}{1-1/2}=2\)."),
         mc("If the ratio test gives L = 1, the series:", ["Converges", "Diverges", "Could do either; the test is inconclusive", "Converges absolutely"], 2,
            "Try another test.")],
    ),
    lesson(
        "taylor", 2, "Power & Taylor Series", "taylor maclaurin power series radius interval convergence",
        "Advanced", 35, ["series-tests"],
        r"A Taylor series rebuilds a function as an infinite polynomial that matches all of its derivatives at one "
        r"point. Cutting it off after a few terms gives a great approximation near that point. A Maclaurin series is "
        r"just a Taylor series centered at 0. Power series only converge within some <b>radius</b> of the center. "
        r"Shortcut: build new series by substituting into known ones.",
        [
            [r"Taylor series at \(a\)", r"f(x) = \sum_{n=0}^\infty \frac{f^{(n)}(a)}{n!}(x-a)^n"],
            [r"\(e^x\)", r"e^x = 1+x+\frac{x^2}{2!}+\frac{x^3}{3!}+\cdots"],
            [r"\(\sin x\)", r"\sin x = x - \frac{x^3}{3!}+\frac{x^5}{5!}-\cdots"],
            [r"\(\cos x\)", r"\cos x = 1 - \frac{x^2}{2!}+\frac{x^4}{4!}-\cdots"],
            ["Geometric", r"\frac{1}{1-x} = 1+x+x^2+\cdots,\quad |x|\lt 1"],
        ],
        ex(r"Find the first four terms of the Maclaurin series for \(e^{2x}\).",
           [r"Start from \(e^u=1+u+\frac{u^2}{2}+\frac{u^3}{6}+\cdots\).",
            r"Substitute \(u=2x\): \(1+2x+\frac{4x^2}{2}+\frac{8x^3}{6}\).",
            r"Simplify."],
           r"\(1+2x+2x^2+\frac43x^3+\cdots\)"),
        ["Forgetting the factorials in the denominators.",
         "Skipping the endpoint check when finding the interval of convergence.",
         r"Using powers of \(x\) when the series is centered at \(a\ne 0\) (they should be powers of \(x-a\))."],
        [pr(r"Maclaurin series for \(\frac{1}{1+x^2}\).", r"Substitute \(-x^2\) into \(\frac1{1-x}\).", r"\(1-x^2+x^4-x^6+\cdots\), for \(|x|\lt 1\)"),
         pr(r"Radius of convergence of \(\displaystyle\sum\frac{x^n}{n}\).", "Ratio test.", r"\(R=1\)"),
         pr(r"Estimate \(e^{0.1}\) using 3 terms.", r"\(1+x+\frac{x^2}{2}\).", r"\(1+0.1+0.005=1.105\)")],
        [mc(r"The coefficient of \(x^3\) in the Maclaurin series of \(e^x\) is:", [r"\(\frac13\)", r"\(\frac16\)", "3", "1"], 1, r"\(\frac{1}{3!}=\frac16\)."),
         mc(r"The first two nonzero terms of \(\sin x\) are:", [r"\(x-\frac{x^3}{6}\)", r"\(1-\frac{x^2}{2}\)", r"\(x+\frac{x^3}{6}\)", r"\(x-\frac{x^2}{2}\)"], 0, "Odd powers with alternating signs.")],
    ),
    lesson(
        "parametric-polar", 2, "Parametric & Polar", "parametric polar arc length area curve",
        "Intermediate", 30, ["derivative-rules", "riemann-ftc"],
        r"<b>Parametric</b> curves give \(x\) and \(y\) as separate functions of a third variable \(t\) (think of \(t\) "
        r"as time). <b>Polar</b> coordinates describe a point by its distance \(r\) from the origin and its angle \(\theta\). "
        r"Both make circles, spirals and loops much easier to describe than \(y=f(x)\).",
        [
            ["Parametric slope", r"\frac{dy}{dx} = \frac{dy/dt}{dx/dt}"],
            ["Arc length", r"L=\int_a^b\sqrt{\left(\tfrac{dx}{dt}\right)^2+\left(\tfrac{dy}{dt}\right)^2}\,dt"],
            ["Polar ↔ rectangular", r"x=r\cos\theta,\quad y=r\sin\theta,\quad r^2=x^2+y^2"],
            ["Polar area", r"A=\frac12\int_\alpha^\beta r^2\,d\theta"],
        ],
        ex(r"Find the slope of \(x=t^2,\ y=t^3\) at \(t=1\).",
           [r"\(\frac{dy}{dt}=3t^2\) and \(\frac{dx}{dt}=2t\).",
            r"\(\frac{dy}{dx}=\frac{3t^2}{2t}=\frac{3t}{2}\).",
            r"At \(t=1\): \(\frac32\)."],
           r"\(\frac32\)"),
        [r"Dividing in the wrong order. It is \(\frac{dy/dt}{dx/dt}\).",
         r"Forgetting the \(\frac12\) or forgetting to square \(r\) in polar area.",
         r"Using \(\theta\) limits that trace the curve twice."],
        [pr(r"Convert \((x,y)=(0,2)\) to polar.", "The point is straight up from the origin.", r"\(r=2,\ \theta=\frac\pi2\)"),
         pr(r"Area inside \(r=2\) using the polar area formula.", r"\(\theta\) goes from 0 to \(2\pi\).", r"\(\frac12\int_0^{2\pi}4\,d\theta=4\pi\)"),
         pr(r"\(x=\cos t,\ y=\sin t\). Find \(\frac{dy}{dx}\) at \(t=\frac\pi4\).", r"\(\frac{\cos t}{-\sin t}\).", r"\(-1\)")],
        [mc(r"The polar curve \(r=3\) is a:", ["Circle of radius 3", "Line", "Spiral", "Cardioid"], 0, "Every point is distance 3 from the origin."),
         mc(r"\(x=2t,\ y=t^2\): \(\frac{dy}{dx}=\)", [r"\(t\)", r"\(2t\)", r"\(\frac t2\)", "1"], 0, r"\(\frac{2t}{2}=t\).")],
    ),
    lesson(
        "vectors", 3, "Vectors, Dot & Cross Product", "vector dot cross magnitude angle 3d",
        "Beginner", 25, [],
        r"A vector has a <b>size and a direction</b>, written \(\langle a,b,c\rangle\). The <b>dot product</b> gives a "
        r"number that measures how much two vectors point the same way (0 means perpendicular). The <b>cross product</b> "
        r"(3D only) gives a new vector perpendicular to both, whose length equals the area of the parallelogram they span.",
        [
            ["Magnitude", r"|\mathbf v| = \sqrt{v_1^2+v_2^2+v_3^2}"],
            ["Dot product", r"\mathbf a\cdot\mathbf b = a_1b_1+a_2b_2+a_3b_3 = |\mathbf a||\mathbf b|\cos\theta"],
            ["Cross product", r"\mathbf a\times\mathbf b = \langle a_2b_3-a_3b_2,\ a_3b_1-a_1b_3,\ a_1b_2-a_2b_1\rangle"],
            ["Perpendicular test", r"\mathbf a\perp\mathbf b \iff \mathbf a\cdot\mathbf b=0"],
        ],
        ex(r"For \(\mathbf a=\langle1,2,3\rangle\) and \(\mathbf b=\langle4,5,6\rangle\), find \(\mathbf a\cdot\mathbf b\) and \(\mathbf a\times\mathbf b\).",
           [r"Dot product: \(1\cdot4+2\cdot5+3\cdot6=4+10+18=32\).",
            r"Cross product, first part: \(2\cdot6-3\cdot5=-3\).",
            r"Second part: \(3\cdot4-1\cdot6=6\).",
            r"Third part: \(1\cdot5-2\cdot4=-3\)."],
           r"\(\mathbf a\cdot\mathbf b=32,\quad \mathbf a\times\mathbf b=\langle-3,6,-3\rangle\)"),
        ["Mixing them up: the dot product is a number, the cross product is a vector.",
         r"Forgetting that order matters: \(\mathbf a\times\mathbf b=-(\mathbf b\times\mathbf a)\).",
         "Sign error in the middle component when using the determinant method."],
        [pr(r"Angle between \(\langle1,0\rangle\) and \(\langle1,1\rangle\).", r"\(\cos\theta=\frac{\mathbf a\cdot\mathbf b}{|\mathbf a||\mathbf b|}\).", r"\(\cos\theta=\frac{1}{\sqrt2}\Rightarrow 45^\circ\)"),
         pr(r"Are \(\langle2,-1,3\rangle\) and \(\langle1,5,1\rangle\) perpendicular?", "Compute the dot product.", r"\(2-5+3=0\). Yes."),
         pr(r"\(|\langle2,3,6\rangle|\)", "Square, add, square root.", r"\(\sqrt{4+9+36}=7\)")],
        [mc(r"\(\langle1,2\rangle\cdot\langle3,4\rangle=\)", ["11", "10", r"\(\langle3,8\rangle\)", "7"], 0, r"\(3+8=11\)."),
         mc(r"\(\mathbf i\times\mathbf j=\)", [r"\(\mathbf k\)", r"\(-\mathbf k\)", "0", "1"], 0, "Right-hand rule.")],
    ),
    lesson(
        "lines-planes", 3, "Lines & Planes", "plane line 3d normal distance",
        "Intermediate", 20, ["vectors"],
        r"A line in 3D needs a point and a <b>direction vector</b>. A plane needs a point and a <b>normal vector</b> "
        r"(one that sticks straight out of the plane). To get a normal from points in the plane, take the cross "
        r"product of two vectors that lie in it.",
        [
            ["Line", r"\mathbf r(t) = \mathbf r_0 + t\,\mathbf v"],
            [r"Plane with normal \(\langle a,b,c\rangle\)", r"a(x-x_0)+b(y-y_0)+c(z-z_0)=0"],
            [r"Distance from a point to \(ax+by+cz+d=0\)", r"D=\frac{|ax_1+by_1+cz_1+d|}{\sqrt{a^2+b^2+c^2}}"],
        ],
        ex(r"Find the plane through \(P(1,0,0),\ Q(0,1,0),\ R(0,0,1)\).",
           [r"Two vectors in the plane: \(\vec{PQ}=\langle-1,1,0\rangle,\ \vec{PR}=\langle-1,0,1\rangle\).",
            r"Normal: \(\vec{PQ}\times\vec{PR}=\langle1,1,1\rangle\).",
            r"Use point \(P\): \(1(x-1)+1(y-0)+1(z-0)=0\)."],
           r"\(x+y+z=1\)"),
        ["Confusing a line's direction vector with a plane's normal vector.",
         "Forgetting that parallel planes have parallel (proportional) normals.",
         "Using two points instead of two vectors when taking the cross product."],
        [pr(r"Line through \((1,2,3)\) in direction \(\langle2,0,-1\rangle\).", r"\(\mathbf r_0+t\mathbf v\).", r"\(\langle1+2t,\ 2,\ 3-t\rangle\)"),
         pr(r"Distance from the origin to \(x+2y+2z=6\).", "Use the distance formula with d = -6.", r"\(\frac{6}{\sqrt{9}}=2\)")],
        [mc(r"The normal of \(2x-y+5z=7\) is:", [r"\(\langle2,-1,5\rangle\)", r"\(\langle2,1,5\rangle\)", r"\(\langle7,0,0\rangle\)", r"\(\langle-1,5,2\rangle\)"], 0, "Read off the coefficients."),
         mc("Two planes are parallel when:", ["Their normals are parallel", "Their normals are perpendicular", "They have the same constant", "Both pass through the origin"], 0,
            "Same orientation means the same normal direction.")],
    ),
    lesson(
        "partial-gradient", 3, "Partial Derivatives & Gradient", "partial gradient directional multivariable chain",
        "Intermediate", 30, ["derivative-rules", "vectors"],
        r"For a function of several variables, a <b>partial derivative</b> measures the rate of change in one direction "
        r"while holding the other variables fixed (treat them as constants). The <b>gradient</b> collects all partials into "
        r"a vector that points in the direction of <b>steepest increase</b>, and its length is that steepest rate.",
        [
            ["Partial derivative", r"f_x=\frac{\partial f}{\partial x}\ \text{(treat other variables as constants)}"],
            ["Gradient", r"\nabla f = \langle f_x,\ f_y,\ f_z\rangle"],
            [r"Directional derivative (\(\mathbf u\) a unit vector)", r"D_{\mathbf u}f = \nabla f\cdot\mathbf u"],
            ["Chain rule", r"\frac{dz}{dt} = f_x\frac{dx}{dt}+f_y\frac{dy}{dt}"],
        ],
        ex(r"For \(f=x^2y+3y\), find \(\nabla f(1,2)\) and the directional derivative toward \(\langle3,4\rangle\).",
           [r"\(f_x=2xy\) and \(f_y=x^2+3\).",
            r"At \((1,2)\): \(\nabla f=\langle4,4\rangle\).",
            r"Make the direction a unit vector: \(\mathbf u=\langle\frac35,\frac45\rangle\).",
            r"\(D_{\mathbf u}f=4\cdot\frac35+4\cdot\frac45=\frac{28}{5}\)."],
           r"\(\nabla f=\langle4,4\rangle,\ D_{\mathbf u}f=\frac{28}{5}\)"),
        [r"Forgetting to make the direction a unit vector.",
         r"Treating \(y\) as a variable when finding \(f_x\).",
         "Writing the gradient as a number. It is a vector."],
        [pr(r"Partials of \(f=e^{xy}\).", "Chain rule on each variable.", r"\(f_x=ye^{xy},\ f_y=xe^{xy}\)"),
         pr(r"Maximum rate of increase of \(f=x^2+y^2\) at \((3,4)\).", r"It is \(|\nabla f|\).", r"\(|\langle6,8\rangle|=10\)")],
        [mc(r"\(\frac{\partial}{\partial x}(x^3y^2)=\)", [r"\(3x^2y^2\)", r"\(2x^3y\)", r"\(3x^2\)", r"\(6x^2y\)"], 0, r"\(y^2\) acts as a constant."),
         mc("The gradient points in the direction of:", ["Steepest increase", "Steepest decrease", "Along the level curve", "The origin"], 0,
            "It is perpendicular to level curves, pointing uphill.")],
    ),
    lesson(
        "lagrange", 3, "Lagrange Multipliers", "lagrange constraint multiplier optimization",
        "Advanced", 25, ["partial-gradient"],
        r"To optimize \(f\) while staying on a constraint curve \(g=k\): at the best points, the level curves of \(f\) "
        r"just touch the constraint, so their gradients are parallel. Solve \(\nabla f=\lambda\nabla g\) together with "
        r"the constraint, then evaluate \(f\) at every solution you find.",
        [
            ["Lagrange condition", r"\nabla f = \lambda\,\nabla g,\qquad g(x,y)=k"],
            ["Final step", r"\text{largest } f \text{ value = max, smallest = min}"],
        ],
        ex(r"Maximize \(f=xy\) subject to \(x+y=10\).",
           [r"\(\nabla f=\langle y,x\rangle\) and \(\nabla g=\langle1,1\rangle\).",
            r"\(y=\lambda\) and \(x=\lambda\), so \(x=y\).",
            r"Constraint: \(2x=10\Rightarrow x=y=5\).",
            r"\(f(5,5)=25\)."],
           r"Maximum 25 at \((5,5)\)"),
        ["Forgetting to include the constraint equation in the system.",
         "Dividing by a variable that might be 0 and losing solutions.",
         "Not comparing all the candidate points."],
        [pr(r"Minimize \(x^2+y^2\) on \(x+y=2\).", r"\(2x=\lambda,\ 2y=\lambda\).", r"\(x=y=1\), minimum 2"),
         pr(r"Max and min of \(x+y\) on \(x^2+y^2=2\).", r"\(1=2\lambda x,\ 1=2\lambda y\Rightarrow x=y\).", r"Max 2 at \((1,1)\), min \(-2\) at \((-1,-1)\)")],
        [mc("The Lagrange condition is:", [r"\(\nabla f=\lambda\nabla g\)", r"\(\nabla f=0\)", r"\(f=\lambda g\)", r"\(\nabla g=0\)"], 0, "The gradients are parallel."),
         mc(r"Minimum of \(x^2+y^2\) on \(x+y=4\):", ["4", "8", "16", "2"], 1, r"\(x=y=2\), giving 8.")],
    ),
    lesson(
        "double-triple", 3, "Double & Triple Integrals", "double triple multiple integral jacobian fubini volume",
        "Intermediate", 35, ["riemann-ftc", "partial-gradient"],
        r"A double integral adds up \(f(x,y)\) over a 2D region (volume under a surface); a triple integral does the same "
        r"over a 3D solid. Work from the <b>inside out</b>: do the inner integral while treating the other variables as "
        r"constants. <b>Always sketch the region</b> to get the limits right.",
        [
            ["Iterated integral", r"\iint_R f\,dA = \int_a^b\!\!\int_c^d f(x,y)\,dy\,dx"],
            ["Area and volume", r"\text{Area}=\iint_R 1\,dA,\qquad \text{Volume}=\iint_R f\,dA"],
            ["Change of variables", r"dA = \left|\frac{\partial(x,y)}{\partial(u,v)}\right|du\,dv"],
        ],
        ex(r"Compute \(\displaystyle\int_0^1\!\!\int_0^2(x+y)\,dy\,dx\).",
           [r"Inner integral (in \(y\), with \(x\) constant): \(\left[xy+\frac{y^2}{2}\right]_0^2=2x+2\).",
            r"Outer integral: \(\int_0^1(2x+2)\,dx=\left[x^2+2x\right]_0^1\).",
            r"\(=1+2=3\)."],
           r"\(3\)"),
        ["Wrong limits after swapping the order of integration. Sketch the region first.",
         "Putting a variable in the outer limits. Only inner limits can depend on outer variables.",
         "Forgetting the Jacobian when changing variables."],
        [pr(r"\(\iint 1\,dA\) over the triangle \(0\le y\le x\le 1\).", r"\(\int_0^1\int_0^x dy\,dx\).", r"\(\frac12\)"),
         pr(r"\(\displaystyle\int_0^1\!\!\int_0^1\!\!\int_0^1 xyz\,dz\,dy\,dx\)", "It splits into three identical integrals.", r"\(\left(\frac12\right)^3=\frac18\)")],
        [mc(r"\(\displaystyle\int_0^2\!\!\int_0^3 1\,dy\,dx=\)", ["5", "6", "3", "2"], 1, "The area of a 2 by 3 rectangle."),
         mc("The inner limits of integration can depend on:", ["The outer variables", "The inner variable", "Nothing", "Any variable"], 0, "Never the variable you're integrating.")],
    ),
    lesson(
        "cyl-sph", 3, "Cylindrical & Spherical", "cylindrical spherical polar coordinates jacobian",
        "Advanced", 30, ["double-triple"],
        r"Circles, cylinders, cones and spheres are painful in \(x,y,z\) but simple in the right coordinates. Use "
        r"<b>polar/cylindrical</b> when there's circular symmetry around an axis, and <b>spherical</b> for balls and cones. "
        r"Don't forget the extra factor (\(r\) or \(\rho^2\sin\phi\)) in the volume element.",
        [
            ["Polar / cylindrical", r"x=r\cos\theta,\ y=r\sin\theta,\quad dA=r\,dr\,d\theta,\quad dV=r\,dz\,dr\,d\theta"],
            ["Spherical", r"x=\rho\sin\phi\cos\theta,\ y=\rho\sin\phi\sin\theta,\ z=\rho\cos\phi"],
            ["Spherical volume element", r"dV=\rho^2\sin\phi\,d\rho\,d\phi\,d\theta,\qquad 0\le\phi\le\pi"],
        ],
        ex(r"Find the volume of a ball of radius \(R\).",
           [r"Set up: \(\int_0^{2\pi}\int_0^\pi\int_0^R\rho^2\sin\phi\,d\rho\,d\phi\,d\theta\).",
            r"\(\rho\) integral: \(\frac{R^3}{3}\). \(\phi\) integral: \(\int_0^\pi\sin\phi\,d\phi=2\). \(\theta\) integral: \(2\pi\).",
            r"Multiply: \(\frac{R^3}{3}\cdot2\cdot2\pi\)."],
           r"\(\frac43\pi R^3\)"),
        [r"Forgetting the \(r\) or the \(\rho^2\sin\phi\).",
         r"Letting \(\phi\) run from 0 to \(2\pi\). It only goes from 0 to \(\pi\).",
         "Picking spherical coordinates for a cylinder (or the other way around)."],
        [pr(r"Area of the disk \(x^2+y^2\le 4\) using polar.", r"\(\int_0^{2\pi}\int_0^2 r\,dr\,d\theta\).", r"\(4\pi\)"),
         pr(r"\(\iint(x^2+y^2)\,dA\) over the unit disk.", r"\(x^2+y^2=r^2\), and don't forget the extra \(r\).", r"\(\int_0^{2\pi}\int_0^1 r^3\,dr\,d\theta=\frac\pi2\)")],
        [mc("In polar coordinates, dA =", [r"\(r\,dr\,d\theta\)", r"\(dr\,d\theta\)", r"\(r^2\,dr\,d\theta\)", r"\(\rho^2\sin\phi\)"], 0, "The Jacobian of polar coordinates is r."),
         mc(r"The range of \(\phi\) in spherical coordinates is:", [r"\(0\) to \(\pi\)", r"\(0\) to \(2\pi\)", r"\(0\) to \(\frac\pi2\)", r"\(-\pi\) to \(\pi\)"], 0, "From the north pole to the south pole.")],
    ),
    lesson(
        "vector-calc", 3, "Line Integrals, Green, Stokes, Divergence", "line integral green stokes divergence curl flux conservative",
        "Advanced", 45, ["partial-gradient", "double-triple"],
        r"A <b>line integral</b> adds up a vector field along a path (think of work done by a force). The big theorems "
        r"all say the same thing in different dimensions: <b>what happens on the boundary equals the total of a "
        r"derivative inside</b>. Green's theorem covers flat regions, Stokes' theorem covers surfaces, and the Divergence theorem covers solids.",
        [
            ["Line integral", r"\int_C\mathbf F\cdot d\mathbf r = \int_a^b\mathbf F(\mathbf r(t))\cdot\mathbf r'(t)\,dt"],
            ["Conservative field (path doesn't matter)", r"\mathbf F=\nabla f \;\Rightarrow\; \int_C\mathbf F\cdot d\mathbf r = f(B)-f(A)"],
            ["Green's theorem", r"\oint_C P\,dx+Q\,dy = \iint_D\left(\frac{\partial Q}{\partial x}-\frac{\partial P}{\partial y}\right)dA"],
            ["Stokes' theorem", r"\oint_C\mathbf F\cdot d\mathbf r = \iint_S(\nabla\times\mathbf F)\cdot d\mathbf S"],
            ["Divergence theorem", r"\iint_S\mathbf F\cdot d\mathbf S = \iiint_E\nabla\cdot\mathbf F\,dV"],
        ],
        ex(r"Use Green's theorem for \(\mathbf F=\langle-y,x\rangle\) counterclockwise around the unit circle.",
           [r"\(P=-y,\ Q=x\), so \(Q_x-P_y=1-(-1)=2\).",
            r"Green's theorem: \(\iint_D 2\,dA = 2\cdot(\text{area of the unit disk})\).",
            r"\(=2\pi\)."],
           r"\(2\pi\)"),
        ["Getting the orientation wrong. Counterclockwise is positive.",
         "Using Green's theorem on a curve that isn't closed.",
         r"Forgetting to check if a field is conservative first (in 2D: \(P_y=Q_x\)), which can save a lot of work."],
        [pr(r"\(\int_C\langle2x,2y\rangle\cdot d\mathbf r\) from \((0,0)\) to \((1,2)\).", r"\(\mathbf F=\nabla(x^2+y^2)\).", r"\(f(1,2)-f(0,0)=5\)"),
         pr(r"Divergence of \(\mathbf F=\langle x^2,y^2,z^2\rangle\).", r"\(\nabla\cdot\mathbf F=P_x+Q_y+R_z\).", r"\(2x+2y+2z\)"),
         pr(r"Curl of \(\langle-y,x,0\rangle\).", "Use the determinant formula.", r"\(\langle0,0,2\rangle\)")],
        [mc("Green's theorem turns a line integral around a closed curve into:", ["A double integral over the region", "A triple integral", "A surface integral", "A derivative"], 0, "It covers flat 2D regions."),
         mc(r"If \(\mathbf F=\nabla f\), then \(\oint_C\mathbf F\cdot d\mathbf r\) around a closed loop is:", ["0", r"\(2\pi\)", "Depends on the path", r"\(f(B)\)"], 0, r"Start = end, so \(f(B)-f(A)=0\)."),
         mc(r"\(\nabla\cdot\langle x,y,z\rangle=\)", ["0", "1", "3", r"\(\langle1,1,1\rangle\)"], 2, r"\(1+1+1=3\).")],
    ),
]
