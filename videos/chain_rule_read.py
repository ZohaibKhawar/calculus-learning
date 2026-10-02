r"""Reading versions of the six Chain Rule & Implicit Differentiation episodes.

Markup is described in static/reader.js. "::: figure N" shows scene N of the same
episode as a still picture.
"""

ARTICLE_1 = r"""
## Why we need the chain rule
The power rule handles \(x^{16}\), but not \((2x+1)^{16}\). The thing being raised to the 16th isn't just \(x\), and expanding sixteen brackets would take pages. Functions like this are **composite**: one function sits inside another.

## Seeing the layers
Think of \(f(x) = (2x+1)^{16}\) as an onion with two layers:
- **Inside layer:** \(2x+1\)
- **Outside layer:** take whatever is inside and raise it to the 16th

To differentiate, peel the layers one at a time: differentiate the outside while leaving the inside alone, then multiply by the derivative of the inside.

::: figure 2
Peeling the layers of \((2x+1)^{16}\): one derivative per layer, multiplied together.
:::

## The rule
Give the inside layer its own name: let \(u = g(x)\). Then the outside layer is \(y = f(u)\), and each layer has its own derivative, \(\frac{du}{dx} = g'(x)\) and \(\frac{dy}{du} = f'(u)\). Multiplying them gives the chain rule in Leibniz notation:

\[\frac{dy}{dx} = \frac{dy}{du}\cdot\frac{du}{dx}\]

In function notation, the same rule says:

\[\big[f(g(x))\big]' = f'(g(x))\cdot g'(x)\]

In words: **the derivative of the outside (with the inside left alone), times the derivative of the inside.** The \(du\)'s look like they cancel. They aren't really fractions, but it's a handy way to remember the rule.

> **Why multiply?** Rates stack. If gear B turns 3× as fast as gear A, and gear C turns 2× as fast as gear B, then gear C turns \(3\times 2 = 6\)× as fast as gear A.

::: example Example 5.1A: find \(f'(x)\) for \(f(x) = (2x+1)^{16}\)
1. Let \(u = 2x+1\). Then \(\frac{du}{dx} = 2\).
2. Then \(f = u^{16}\), so \(\frac{df}{du} = 16u^{15}\).
3. Chain rule: \(\frac{df}{dx} = \frac{df}{du}\cdot\frac{du}{dx} = 16u^{15}\cdot 2 = 32u^{15}\).
4. Substitute \(u = 2x+1\) back in.
Answer: \(f'(x) = 32(2x+1)^{15}\)
:::

::: example Example 5.1B: find \(g'(x)\) for \(g(x) = 4(x^2-x+2)^{12}\)
1. Let \(u = x^2 - x + 2\). Then \(\frac{du}{dx} = 2x - 1\).
2. Then \(g = 4u^{12}\), so \(\frac{dg}{du} = 48u^{11}\). The constant 4 just comes along.
3. Multiply: \(\frac{dg}{dx} = 48u^{11}(2x-1)\), then substitute \(u\) back in.
Answer: \(g'(x) = 48(2x-1)(x^2-x+2)^{11}\)
:::

## Checking it on a graph
For \(y = (2x+1)^3\), the chain rule gives \(y' = 3(2x+1)^2\cdot 2 = 6(2x+1)^2\). At \(x = 0\) that's 6, and the tangent line there has slope exactly 6.

::: figure 7
The tangent to \(y=(2x+1)^3\) at \(x=0\) has slope 6, as the chain rule predicts.
:::

::: try Find \(\frac{d}{dx}(5x-3)^4\).
\(4(5x-3)^3\cdot 5 = 20(5x-3)^3\). The outside gives \(4(5x-3)^3\) and the inside \(5x-3\) has derivative 5.
:::

## Key takeaways
- Spot the layers: what's inside, and what is the outside doing to it?
- Differentiate the outside, leaving the inside alone.
- Multiply by the derivative of the inside: \(\frac{dy}{dx} = \frac{dy}{du}\cdot\frac{du}{dx}\).
"""

ARTICLE_2 = r"""
## The chain rule rarely works alone
Most real questions combine the chain rule with the rules you already know:
- **Sum rule:** \((f+g)' = f' + g'\)
- **Power rule:** \((x^n)' = nx^{n-1}\)
- **Product rule:** \((fg)' = f'g + fg'\)
- **Chain rule:** \(\big[f(g(x))\big]' = f'(g(x))\,g'(x)\)

Find the **main move** first: is the whole function a sum, a product, or one big layer? Then use the chain rule on any piece that has an inside function.

> **Notation trap:** \(\sin^3 x\) means \((\sin x)^3\). The inside layer is \(\sin x\) and the outside layer is cubing, so \(\frac{d}{dx}\sin^3 x = 3\sin^2 x\cos x\).

::: example Example 5.1C, part 1: differentiate \(f(x) = 4x^3 + \sin^3 x\)
1. It's a sum, so differentiate each term separately.
2. Power rule: \(\frac{d}{dx}4x^3 = 12x^2\).
3. Chain rule: \(\frac{d}{dx}(\sin x)^3 = 3(\sin x)^2\cdot\cos x\).
Answer: \(f'(x) = 12x^2 + 3\sin^2 x\cos x\)
:::

::: example Example 5.1C, part 2: differentiate \(g(x) = (3x^2-x)(4x+1)^3\)
1. It's a product, so start with the product rule: \(g' = (3x^2-x)'(4x+1)^3 + (3x^2-x)\big[(4x+1)^3\big]'\).
2. \((3x^2-x)' = 6x - 1\).
3. Chain rule on the second factor: \(\big[(4x+1)^3\big]' = 3(4x+1)^2\cdot 4 = 12(4x+1)^2\).
4. Put it together.
Answer: \(g'(x) = (6x-1)(4x+1)^3 + 12(3x^2-x)(4x+1)^2\)
:::

## Factor your answer
Both terms share \((4x+1)^2\). Factoring it out makes the derivative far easier to use:

\[g'(x) = (4x+1)^2\big[(6x-1)(4x+1) + 12(3x^2-x)\big]\]

\[= (4x+1)^2\big[24x^2+2x-1 + 36x^2-12x\big] = (4x+1)^2(60x^2-10x-1)\]

Now finding horizontal tangents is easy. \(g'(x) = 0\) when \(x = -\frac14\), or when \(60x^2 - 10x - 1 = 0\), which gives \(x = \frac{5 \pm \sqrt{85}}{60}\) (about \(-0.07\) and \(0.24\)).

::: figure 6
The three flat tangents of \(g(x) = (3x^2-x)(4x+1)^3\), found from the factored derivative.
:::

::: try Differentiate \(x^2(x+1)^3\) and factor your answer.
\(2x(x+1)^3 + 3x^2(x+1)^2 = x(x+1)^2(5x+2)\).
:::

## Key takeaways
- Identify the main move: sum, product, or layers.
- Use the chain rule on every piece with an inside function.
- Factor out common powers at the end.
"""

ARTICLE_3 = r"""
## Any number of layers
The chain rule works the same way no matter how many layers a function has. For three functions nested inside each other:

\[\big[f(g(h(x)))\big]' = f'\big(g(h(x))\big)\cdot g'\big(h(x)\big)\cdot h'(x)\]

Each layer contributes one factor. Work from the outside in, and leave everything inside a layer untouched while you differentiate it.

::: example Peel \(y = \sin^3(2x)\)
1. The layers, from the outside in: cubing, sine, then \(2x\).
2. Cube: \(3\sin^2(2x)\).
3. Sine: \(\cos(2x)\).
4. Core: \(\frac{d}{dx}2x = 2\). Multiply all three factors.
Answer: \(\frac{dy}{dx} = 6\sin^2(2x)\cos(2x)\)
:::

## Example 5.1D: five layers
Find the slope of the tangent to \(f(x) = \cos^2\!\big((e^{2x}+1)^3\big)\) at \(x = 0\). Rewriting it as \(\Big[\cos\big((e^{2x}+1)^3\big)\Big]^2\) shows that the square is the outermost layer.

::: figure 4
The five layers of \(\cos^2\big((e^{2x}+1)^3\big)\) and the factor each one contributes.
:::

Layer by layer, writing \(u = (e^{2x}+1)^3\):
- Square: \(2\cos(u)\)
- Cosine: \(-\sin(u)\)
- Cube: \(3(e^{2x}+1)^2\)
- Exponential plus one: \(e^{2x}\)
- Core \(2x\): \(2\)

\[f'(x) = 2\cos(u)\cdot(-\sin u)\cdot 3(e^{2x}+1)^2\cdot e^{2x}\cdot 2\]

::: example Evaluate the slope at \(x = 0\)
1. \(e^0 = 1\), so \(u = (1+1)^3 = 8\).
2. \(f'(0) = 2\cos 8\cdot(-\sin 8)\cdot 3(2)^2\cdot 1\cdot 2 = -48\sin 8\cos 8\).
3. Using \(2\sin\theta\cos\theta = \sin 2\theta\): \(-48\sin 8\cos 8 = -24\sin 16\).
4. Evaluate with your calculator in radians.
Answer: \(f'(0) = -24\sin 16 \approx 6.91\)
:::

> **Tip:** don't simplify before plugging in. Write one factor per layer, substitute \(x = 0\), then simplify the numbers.

::: figure 6
The function wiggles faster and faster as \(x\) grows, but its tangent at \(x=0\) has slope 6.91.
:::

::: try Find \(\frac{d}{dx}\sqrt{\cos(3x)}\).
\(\frac{1}{2\sqrt{\cos 3x}}\cdot(-\sin 3x)\cdot 3 = -\frac{3\sin 3x}{2\sqrt{\cos 3x}}\). Three layers: square root, cosine, and \(3x\).
:::

## Key takeaways
- The number of layers equals the number of factors.
- Peel from the outside in.
- For a slope at a point, substitute after differentiating.
"""

ARTICLE_4 = r"""
## When y can't be isolated
Some relations, like the circle \(x^2 + y^2 = 9\), fail the vertical line test: one \(x\)-value gives two \(y\)-values, so the curve can't be written as \(y = f(x)\). It still has a tangent line with a slope at each point. **Implicit differentiation** finds that slope without solving for \(y\).

::: figure 1
The circle fails the vertical line test, but every point still has a tangent line.
:::

## The key idea
Apply \(\frac{d}{dx}\) to both sides of the equation, remembering that \(y\) is secretly a function of \(x\):

\[\frac{d}{dx}\big[f(x)\big] = f'(x) \qquad \frac{d}{dx}\big[f(y)\big] = f'(y)\,\frac{dy}{dx}\]

The extra \(\frac{dy}{dx}\) comes from the chain rule. For example, \(y^3\) has an outside layer (cubing) and an inside layer (\(y\), which depends on \(x\)), so \(\frac{d}{dx}\big[y^3\big] = 3y^2\frac{dy}{dx}\).

::: example The circle \(x^2 + y^2 = 9\)
1. Differentiate both sides: \(2x + 2y\frac{dy}{dx} = 0\). The 9 is a constant, so its derivative is 0.
2. Solve for the slope: \(\frac{dy}{dx} = -\frac{x}{y}\).
3. At the point \((1.8,\ 2.4)\): \(\frac{dy}{dx} = -\frac{1.8}{2.4}\).
Answer: the slope is \(-0.75\) at \((1.8, 2.4)\)
:::

## The four-step recipe
1. Differentiate both sides with respect to \(x\).
2. Tag the derivative of every \(y\)-term with \(\frac{dy}{dx}\).
3. Collect all the \(\frac{dy}{dx}\) terms on one side.
4. Factor out \(\frac{dy}{dx}\) and divide.

::: example Example 5.2A: find \(\frac{dy}{dx}\) for \(2x^2 - 3y^2 = 4x^3y\)
1. Differentiate. The right side is a product: \(4x - 6y\frac{dy}{dx} = 12x^2y + 4x^3\frac{dy}{dx}\).
2. Collect: \(4x - 12x^2y = 4x^3\frac{dy}{dx} + 6y\frac{dy}{dx}\).
3. Factor: \(4x - 12x^2y = \frac{dy}{dx}\big(4x^3 + 6y\big)\).
4. Divide, then cancel a common factor of 2.
Answer: \(\frac{dy}{dx} = \frac{2x - 6x^2y}{2x^3+3y}\)
:::

::: example Homework #1: find \(\frac{dy}{dx}\) for \(y - xy^3 = 2\)
1. Differentiate, using the product rule on \(xy^3\): \(\frac{dy}{dx} - \Big(y^3 + 3xy^2\frac{dy}{dx}\Big) = 0\).
2. Collect: \(\frac{dy}{dx} - 3xy^2\frac{dy}{dx} = y^3\).
3. Factor: \(\frac{dy}{dx}\big(1 - 3xy^2\big) = y^3\).
Answer: \(\frac{dy}{dx} = \frac{y^3}{1-3xy^2}\)
:::

> **Common mistake:** forgetting the product rule on terms like \(xy\) or \(xy^3\). Both factors depend on \(x\).

::: try Find \(\frac{dy}{dx}\) for \(x^2 + xy + y^2 = 7\).
\(2x + y + x\frac{dy}{dx} + 2y\frac{dy}{dx} = 0\), so \(\frac{dy}{dx} = -\frac{2x+y}{x+2y}\).
:::

## Key takeaways
- Use implicit differentiation when \(y\) can't easily be isolated.
- Every \(y\)-term picks up a \(\frac{dy}{dx}\). That's the chain rule.
- Watch for products, which need the product rule too.
"""

ARTICLE_5 = r"""
## More than one tangent at the same x
Implicit curves can pass through the same \(x\)-value more than once. That's why homework question 2 asks for the slopes of the tangent lines (plural) to \(x^2y + xy^2 + x^3 = 3\) at \(x = 1\).

::: figure 1
The line \(x = 1\) crosses the curve twice, at \((1,-2)\) and \((1,1)\).
:::

::: example Step 1: find the points where \(x = 1\)
1. Substitute \(x = 1\) into the equation: \(y + y^2 + 1 = 3\).
2. Rearrange: \(y^2 + y - 2 = 0\).
3. Factor: \((y+2)(y-1) = 0\), so \(y = -2\) or \(y = 1\).
Answer: the points \((1, -2)\) and \((1, 1)\)
:::

::: example Step 2: differentiate implicitly
1. Use the product rule on \(x^2y\) and \(xy^2\): \(2xy + x^2\frac{dy}{dx} + y^2 + 2xy\frac{dy}{dx} + 3x^2 = 0\).
2. Collect: \(\frac{dy}{dx}\big(x^2 + 2xy\big) = -\big(3x^2 + 2xy + y^2\big)\).
Answer: \(\frac{dy}{dx} = -\frac{3x^2 + 2xy + y^2}{x^2 + 2xy}\)
:::

You can also substitute the point before isolating \(\frac{dy}{dx}\). Both orders give the same slope.

::: example Step 3: the slope at each point
1. At \((1,-2)\): \(m = -\frac{3 - 4 + 4}{1 - 4} = -\frac{3}{-3} = 1\).
2. At \((1, 1)\): \(m = -\frac{3 + 2 + 1}{1 + 2} = -\frac{6}{3} = -2\).
Answer: slopes \(1\) and \(-2\)
:::

## Tangent line equations (homework #3)
Use point-slope form, \(y - y_1 = m(x - x_1)\):
- Through \((1,-2)\) with slope 1: \(y + 2 = x - 1\), so \(y = x - 3\).
- Through \((1,1)\) with slope \(-2\): \(y - 1 = -2(x - 1)\), so \(y = -2x + 3\).

::: figure 6
Both tangent lines touch the curve exactly at the two points.
:::

## Working backwards (homework #4)
The relation \(y + \sqrt{y} = x\) has a tangent with slope \(\frac14\). Where does it occur?

::: example Find the point where the slope is \(\frac14\)
1. Differentiate: \(\frac{dy}{dx} + \frac{1}{2\sqrt y}\frac{dy}{dx} = 1\).
2. Substitute \(\frac{dy}{dx} = \frac14\): \(\frac14 + \frac{1}{8\sqrt y} = 1\), so \(\frac{1}{8\sqrt y} = \frac34\).
3. Solve: \(\sqrt y = \frac16\), so \(y = \frac{1}{36}\).
4. Use the original equation to find \(x\): \(x = \frac1{36} + \frac16 = \frac{7}{36}\).
Answer: \(\left(\frac{7}{36}, \frac{1}{36}\right)\)
:::

The tangent line there is \(y = \frac14x - \frac1{48}\). Its \(y\)-intercept, \(-\frac{1}{48}\approx -0.021\), matches the graph in the notes.

::: figure 8
The tangent with slope \(\frac14\) at \(\left(\frac{7}{36}, \frac{1}{36}\right)\).
:::

::: try Find the tangent line to \(x^2 + y^2 = 25\) at \((3, 4)\).
The slope is \(-\frac{x}{y} = -\frac34\), so \(y - 4 = -\frac34(x - 3)\), which simplifies to \(y = -\frac34x + \frac{25}{4}\).
:::

## Key takeaways
- Find the point or points from the original equation.
- Differentiate implicitly, then substitute each point to get its slope.
- Write each tangent line in point-slope form.
"""

ARTICLE_6 = r"""
## Proving new rules
Implicit differentiation is also a tool for proving derivative rules. Earlier, the power rule \(\frac{d}{dx}x^n = nx^{n-1}\) was proven only for whole-number powers \(n = 0, 1, 2, \dots\). Roots like \(\sqrt{x} = x^{1/2}\) and \(\sqrt[3]{x^2} = x^{2/3}\) need more.

::: example Proof: the power rule for rational powers \(n = \frac ab\)
1. Let \(y = x^{a/b}\), where \(a\) and \(b\) are integers.
2. Raise both sides to the power \(b\): \(y^b = x^a\). Now there are only whole-number powers.
3. Differentiate implicitly: \(b\,y^{b-1}\frac{dy}{dx} = a\,x^{a-1}\).
4. Solve: \(\frac{dy}{dx} = \frac ab\cdot\frac{x^{a-1}}{y^{b-1}}\).
5. Substitute \(y = x^{a/b}\), so \(y^{b-1} = x^{a - a/b}\), and simplify: \(\frac ab\cdot\frac{x^{a-1}}{x^{a-a/b}} = \frac ab\,x^{\frac ab - 1}\).
Answer: \(\frac{d}{dx}x^{a/b} = \frac{a}{b}\,x^{\frac{a}{b}-1}\), so the power rule works for fractions too.
:::

::: example Example 5.2B: a router transfers \(f(x) = 2x + 6\sqrt{x}\) MB in the first \(x\) minutes. How fast is data moving at 4 minutes?
1. Rewrite the root as a power: \(f(x) = 2x + 6x^{1/2}\).
2. Differentiate: \(f'(x) = 2 + 6\cdot\frac12x^{-1/2} = 2 + \frac{3}{\sqrt x}\).
3. Evaluate: \(f'(4) = 2 + \frac32\).
Answer: 3.5 MB per minute
:::

::: figure 4
The data curve and its tangent at 4 minutes, with slope 3.5.
:::

## The derivative of ln x

::: example Example 5.2C: show that \(\frac{d}{dx}\ln x = \frac1x\)
1. Let \(y = \ln x\).
2. Rewrite in exponential form: \(e^y = x\).
3. Differentiate implicitly: \(e^y\frac{dy}{dx} = 1\).
4. Solve: \(\frac{dy}{dx} = \frac{1}{e^y}\), and \(e^y\) is just \(x\).
Answer: \(\frac{d}{dx}\ln x = \frac1x\)
:::

For a logarithm with any base \(b\):

\[\frac{d}{dx}\log_b x = \frac{1}{x\ln b}\]

Combined with the chain rule, the derivative of \(\ln\) of a function is its derivative over itself:

\[\frac{d}{dx}\ln\big(g(x)\big) = \frac{g'(x)}{g(x)}, \qquad \text{for example } \frac{d}{dx}\ln(x^2+1) = \frac{2x}{x^2+1}\]

::: try Find \(\frac{d}{dx}\,4\sqrt[3]{x^2}\).
Rewrite it as \(4x^{2/3}\). The power rule gives \(\frac83x^{-1/3} = \frac{8}{3\sqrt[3]{x}}\).
:::

## Lesson summary
- **Chain rule:** multiply the derivative of every layer, \(\frac{dy}{dx} = \frac{dy}{du}\cdot\frac{du}{dx}\).
- **Implicit differentiation:** every \(y\)-term picks up a \(\frac{dy}{dx}\).
- **New rules:** \(\frac{d}{dx}x^{a/b} = \frac ab x^{\frac ab - 1}\), \(\frac{d}{dx}\ln x = \frac1x\), and \(\frac{d}{dx}\log_b x = \frac{1}{x\ln b}\).
"""

ARTICLES = [ARTICLE_1, ARTICLE_2, ARTICLE_3, ARTICLE_4, ARTICLE_5, ARTICLE_6]
