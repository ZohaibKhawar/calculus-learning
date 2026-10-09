/* CalcLearners plots: the pictures inside the lessons.
 *
 * A lesson describes a picture as plain data (see lessons_deep.py), for example
 *   { view: [-1, 3, -1, 4], curves: [{ f: "x^2" }], tool: { type: "tangent" } }
 * and Plot.hydrate() draws every <figure class="fig-plot" data-plot="..."> it finds.
 * "view" is [x from, x to, y from, y to]. Besides curves a picture can hold points (open or
 * filled), segments, dashed lines, shading, rectangles and labels. A "tool" makes it
 * something to play with: a slider or a drag changes the picture and the line of text under it.
 *
 *   trace     slide a point along the curve and read its coordinates
 *   tangent   the same, with the tangent line and its slope
 *   secant    a second point closes in on a fixed one: the secant turns into the tangent
 *   approach  two points close in on x = a from both sides (limits)
 *   band      the epsilon band and the widest delta window that fits it
 *   riemann   rectangles under the curve, as many as you like
 *   newton    Newton's method, one tangent at a time
 *   field     a direction field; pick a start and a solution curve is drawn
 *   euler     Euler's method with a choice of step size, against the true solution
 *   family    sliders for the letters in a formula (a, h, k, C)
 *
 * Formulas are read by the small parser below: the site's security policy forbids eval.
 * Used by the app (app.js) and by the lesson pages at /lessons (lesson.js).
 */
window.Plot = (function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const W = 640;

  // ---------- Reading a formula such as "(x^2 - 1)/(x - 1)" ----------
  const FUNCS = { sin: Math.sin, cos: Math.cos, tan: Math.tan, exp: Math.exp, ln: Math.log, sqrt: Math.sqrt, abs: Math.abs };
  const CONSTS = { pi: Math.PI, e: Math.E };

  // Returns a function of an object of variables: compile("x^2 + C")({ x: 2, C: 1 }) is 5.
  function compile(src) {
    const toks = String(src).match(/\d+\.?\d*|\.\d+|[a-zA-Z]+|[-+*/^()]/g) || [];
    let i = 0;
    const peek = () => toks[i], next = () => toks[i++];
    function sum() {
      let a = product();
      while (peek() === "+" || peek() === "-") {
        const op = next(), l = a, r = product();
        a = op === "+" ? v => l(v) + r(v) : v => l(v) - r(v);
      }
      return a;
    }
    function product() {
      let a = unary();
      while (peek() === "*" || peek() === "/") {
        const op = next(), l = a, r = unary();
        a = op === "*" ? v => l(v) * r(v) : v => l(v) / r(v);
      }
      return a;
    }
    function unary() {
      if (peek() !== "-") return power();
      next();
      const a = unary();
      return v => -a(v);
    }
    function power() {
      const a = atom();
      if (peek() !== "^") return a;
      next();
      const b = unary();
      return v => Math.pow(a(v), b(v));
    }
    function atom() {
      const t = next();
      if (t === "(") { const a = sum(); next(); return a; }
      if (/^[\d.]/.test(t)) { const n = parseFloat(t); return () => n; }
      if (FUNCS[t]) { next(); const a = sum(), fn = FUNCS[t]; next(); return v => fn(a(v)); }
      if (t in CONSTS) { const c = CONSTS[t]; return () => c; }
      return v => v[t];  // a variable: x, y or a slider's letter
    }
    return sum();
  }

  // ---------- Helpers ----------
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  // A number for people: no "-0.00", a real minus sign, no trailing zeros unless `keep`.
  function fmt(v, digits = 2, keep = false) {
    if (!isFinite(v)) return v > 0 ? "∞" : v < 0 ? "−∞" : "undefined";
    let s = Math.abs(v).toFixed(digits);
    if (!keep && s.includes(".")) s = s.replace(/\.?0+$/, "");
    return (v < 0 && +s !== 0 ? "−" : "") + s;
  }
  // Grid spacing that gives a handful of lines for any range.
  function gridStep(range) {
    for (const s of [0.1, 0.2, 0.25, 0.5, 1, 2, 5, 10, 20, 25, 50, 100, 200, 500]) if (range / s <= 12) return s;
    return range / 10;
  }
  // Fills "{x}" and friends in a template with numbers.
  const fill = (template, values) => template.replace(/\{(\w+)\}/g, (_, k) => `<b>${fmt(values[k], k === "n" ? 0 : 2)}</b>`);

  // ---------- Drawing one picture ----------
  function draw(fig, spec) {
    const [x0, x1, y0, y1] = spec.view;
    const H = spec.h || 360;
    const sx = x => (x - x0) / (x1 - x0) * W, sy = y => H - (y - y0) / (y1 - y0) * H;
    const env = Object.assign({}, spec.vars);
    const at = (f, x) => { env.x = x; return f(env); };

    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("class", "graph lesson-graph");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", spec.alt || "Graph");
    const el = (tag, cls, attrs = {}, parent = svg) => {
      const e = document.createElementNS(NS, tag);
      if (cls) e.setAttribute("class", cls);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      parent.appendChild(e);
      return e;
    };
    const line = (cls, xa, ya, xb, yb, parent) => el("line", cls, { x1: sx(xa), y1: sy(ya), x2: sx(xb), y2: sy(yb) }, parent);
    const POS = { n: [0, -12, "middle"], s: [0, 19, "middle"], e: [12, 5, "start"], w: [-12, 5, "end"],
      ne: [10, -10, "start"], nw: [-10, -10, "end"], se: [10, 20, "start"], sw: [-10, 20, "end"] };
    const text = (str, x, y, pos = "ne", cls = "g-label", parent) => {
      const [dx, dy, anchor] = POS[pos] || POS.ne;
      const t = el("text", cls, { x: sx(x) + dx, y: sy(y) + dy, "text-anchor": anchor }, parent);
      t.textContent = str;
      return t;
    };
    const dot = (x, y, open, parent, cls = "") =>
      el("circle", (open ? "g-hole " : "g-pt ") + cls, { cx: sx(x), cy: sy(y), r: cls.includes("g-small") ? 4 : 6 }, parent);

    // The path of a curve between two x-values, lifted where it leaves the picture or jumps.
    function pathOf(f, a = x0, b = x1) {
      const span = y1 - y0, n = 320;
      let d = "", pen = false, last = 0;
      for (let i = 0; i <= n; i++) {
        const x = a + (b - a) * i / n, y = at(f, x);
        if (!isFinite(y) || y < y0 - 2 * span || y > y1 + 2 * span || (pen && Math.abs(y - last) > 1.5 * span)) { pen = false; continue; }
        d += (pen ? "L" : "M") + sx(x).toFixed(1) + " " + sy(y).toFixed(1);
        pen = true;
        last = y;
      }
      return d;
    }

    // Graph paper, axes and their numbers.
    if (spec.axes !== false) {
      const gx = gridStep(x1 - x0), gy = gridStep(y1 - y0);
      const ax = clamp(0, x0, x1), ay = clamp(0, y0, y1);  // where the axes sit (an edge, if 0 is out of view)
      for (let x = Math.ceil(x0 / gx) * gx; x <= x1 + 1e-9; x += gx) line("g-grid", x, y0, x, y1);
      for (let y = Math.ceil(y0 / gy) * gy; y <= y1 + 1e-9; y += gy) line("g-grid", x0, y, x1, y);
      line("g-axis", ax, y0, ax, y1);
      line("g-axis", x0, ay, x1, ay);
      const skip = n => Math.abs(n) < 1e-9;
      for (let x = Math.ceil(x0 / gx) * gx; x <= x1 - gx / 3; x += gx) {
        if (!skip(x) && x > x0 + gx / 3) text(fmt(x), x, ay, sy(ay) > H - 26 ? "n" : "s", "g-tick");
      }
      for (let y = Math.ceil(y0 / gy) * gy; y <= y1 - gy / 3; y += gy) {
        if (!skip(y) && y > y0 + gy / 3) text(fmt(y), ax, y, sx(ax) < 30 ? "e" : "w", "g-tick");
      }
    }

    // What the lesson put in the picture.
    for (const s of spec.shade || []) {
      const f = compile(s.f), g = compile(s.g || "0"), [a, b] = s.dom, n = 80;
      let d = "";
      for (let i = 0; i <= n; i++) { const x = a + (b - a) * i / n; d += (i ? "L" : "M") + sx(x).toFixed(1) + " " + sy(at(f, x)).toFixed(1); }
      for (let i = n; i >= 0; i--) { const x = a + (b - a) * i / n; d += "L" + sx(x).toFixed(1) + " " + sy(at(g, x)).toFixed(1); }
      el("path", "g-fill", { d: d + "Z" });
    }
    for (const r of spec.rects || []) {
      el("rect", "g-rect " + (r.style || ""), { x: sx(r.x), y: sy(r.y + r.h), width: sx(r.x + r.w) - sx(r.x), height: sy(r.y) - sy(r.y + r.h) });
    }
    for (const v of spec.vlines || []) line("g-dash", v, y0, v, y1);
    for (const h of spec.hlines || []) line("g-dash", x0, h, x1, h);
    const curves = (spec.curves || []).map(c => ({ ...c, fn: compile(c.f) }));
    const curveLayer = el("g");
    const drawCurves = () => {
      curveLayer.textContent = "";
      for (const c of curves) el("path", "g-curve " + (c.style || ""), { d: pathOf(c.fn, ...(c.dom || [])) }, curveLayer);
    };
    drawCurves();
    for (const s of spec.segments || []) line("g-seg " + (s.style || ""), s.from[0], s.from[1], s.to[0], s.to[1]);
    for (const p of spec.points || []) {
      dot(p.at[0], p.at[1], p.open);
      if (p.label) text(p.label, p.at[0], p.at[1], p.pos);
    }
    for (const l of spec.labels || []) text(l.text, l.at[0], l.at[1], l.pos || "e");

    // The part that moves, the controls under the picture and the line of text that reports on it.
    const layer = el("g");
    const controls = document.createElement("div");
    controls.className = "plot-controls";
    const read = document.createElement("p");
    read.className = "plot-read";
    read.setAttribute("aria-live", "polite");
    const cap = fig.querySelector("figcaption");
    fig.insertBefore(svg, cap);
    const tool = spec.tool && TOOLS[spec.tool.type];
    if (!tool) return;
    fig.insertBefore(controls, cap);
    fig.insertBefore(read, cap);

    const ui = {
      spec, t: spec.tool, env, at, sx, sy, x0, x1, y0, y1, H, el, line, text, dot, layer, pathOf, curves, drawCurves, read, controls,
      f: curves[0] && curves[0].fn,
      clear() { layer.textContent = ""; },
      // The slope of f at x, measured from two very close points.
      slope(f, x) { const k = (x1 - x0) * 1e-5; return (at(f, x + k) - at(f, x - k)) / (2 * k); },
      // A line through (x, y) with slope m, drawn the same length on screen whatever its tilt.
      through(cls, x, y, m, half = 120) {
        const ux = W / (x1 - x0), uy = H / (y1 - y0);        // pixels per unit
        const len = Math.hypot(ux, m * uy), dx = half / len;  // how far to go in x for `half` pixels
        return line(cls, x - dx, y - m * dx, x + dx, y + m * dx, layer);
      },
      slider(label, min, max, value, step, onInput) {
        const wrap = document.createElement("label");
        wrap.className = "plot-slider";
        const name = document.createElement("span");
        name.textContent = label;
        const input = document.createElement("input");
        Object.assign(input, { type: "range", min, max, step, value });
        input.addEventListener("input", () => onInput(+input.value));
        wrap.append(name, input);
        controls.appendChild(wrap);
        return input;
      },
      button(label, onClick, cls = "ghost small") {
        const b = document.createElement("button");
        b.type = "button";
        b.className = cls;
        b.textContent = label;
        b.addEventListener("click", onClick);
        controls.appendChild(b);
        return b;
      },
      // Dragging or tapping on the picture calls back with the x (and y) under the pointer.
      // Up-and-down swipes still scroll the page on a phone.
      drag(onMove) {
        const move = e => {
          const r = svg.getBoundingClientRect();
          onMove(x0 + (e.clientX - r.left) / r.width * (x1 - x0), y1 - (e.clientY - r.top) / r.height * (y1 - y0));
        };
        svg.classList.add("draggable");
        svg.addEventListener("pointerdown", move);
        svg.addEventListener("pointermove", e => { if (e.pointerType === "mouse" ? e.buttons : e.pressure > 0) move(e); });
      }
    };
    tool(ui);
  }

  // ---------- The tools ----------
  const TOOLS = {
    // Slide a point along the curve.
    trace(ui, withTangent) {
      const { t, f } = ui;
      const [a, b] = t.dom || [ui.x0, ui.x1];
      const template = t.read || (withTangent ? "At x = {x} the height is {y} and the slope is {m}." : "x = {x}, y = {y}");
      // A round step (0.01, 0.02, 0.05 ...) so that the readout lands on round numbers.
      const raw = (b - a) / 300, unit = Math.pow(10, Math.floor(Math.log10(raw)));
      const step = [1, 2, 5, 10].map(m => m * unit).find(v => v >= raw);
      const input = ui.slider(t.label || "x", a, b, t.start ?? (a + b) / 2, step, show);
      function show(x) {
        x = clamp(x, a, b);
        input.value = x;
        const y = ui.at(f, x), m = ui.slope(f, x);
        ui.clear();
        if (withTangent) ui.through("g-tan", x, y, m);
        else { ui.line("g-guide", x, 0, x, y, ui.layer); ui.line("g-guide", 0, y, x, y, ui.layer); }
        ui.dot(x, y, false, ui.layer, "g-move");
        ui.read.innerHTML = fill(template, { x, y, m });
      }
      ui.drag(show);
      show(+input.value);
    },
    tangent(ui) { TOOLS.trace(ui, true); },

    // A fixed point and a second one h further along: the secant through them, and the tangent it heads for.
    secant(ui) {
      const { t, f } = ui, a = t.a, max = t.max || 1.5;
      const ya = ui.at(f, a), target = ui.slope(f, a);
      const input = ui.slider("h", 0.01, max, t.start || max, 0.01, show);
      function show(h) {
        h = clamp(h, 0.01, max);
        input.value = h;
        const yb = ui.at(f, a + h), m = (yb - ya) / h;
        ui.clear();
        ui.through("g-soft-line", a, ya, target, 150);
        ui.through("g-tan", a + h / 2, (ya + yb) / 2, m, 190);
        ui.dot(a, ya, false, ui.layer);
        ui.dot(a + h, yb, false, ui.layer, "g-move");
        ui.read.innerHTML = `h = <b>${fmt(h, 2, true)}</b>: the secant's slope is <b>${fmt(m, 3, true)}</b>. As h shrinks it heads to <b>${fmt(target, 2)}</b>, the slope of the tangent.`;
      }
      ui.drag(x => show(x - a));
      show(+input.value);
    },

    // Two points closing in on x = a, one from each side. "left" and "right" give the two
    // sides their own formulas when the function changes rule at a.
    approach(ui) {
      const { t } = ui, a = t.a, max = t.max || 1, min = 0.001;
      const fl = t.left ? compile(t.left) : ui.f, fr = t.right ? compile(t.right) : ui.f;
      // The slider runs from far (0) to very close (1), and gets finer as it closes in.
      const input = ui.slider("Distance from x = " + fmt(a), 0, 1, 0.15, 0.005, show);
      function show(s) {
        const d = max * Math.pow(min / max, s);
        ui.clear();
        const rows = [];
        for (const [side, f, x] of [["left", fl, a - d], ["right", fr, a + d]]) {
          const y = ui.at(f, x);
          ui.line("g-guide", x, 0, x, y, ui.layer);
          ui.line("g-guide", 0, y, x, y, ui.layer);
          ui.dot(x, y, false, ui.layer, "g-move");
          rows.push(`From the ${side}: x = <b>${fmt(x, 4)}</b> gives <b>${fmt(y, 4)}</b>.`);
        }
        ui.read.innerHTML = rows.join(" ");
      }
      ui.drag(x => {
        const d = clamp(Math.abs(x - a), min, max);
        input.value = Math.log(d / max) / Math.log(min / max);
        show(+input.value);
      });
      show(+input.value);
    },

    // The epsilon band around L, and the widest window around a that keeps the curve inside it.
    band(ui) {
      const { t, f } = ui, a = t.a, L = t.L, max = t.max || 2;
      const input = ui.slider("ε (epsilon)", 0.05, max, t.start || max / 2, 0.05, show);
      function show(eps) {
        const step = (ui.x1 - ui.x0) / 4000;
        let delta = 0;
        while (delta < ui.x1 - ui.x0 && Math.abs(ui.at(f, a + delta + step) - L) < eps && Math.abs(ui.at(f, a - delta - step) - L) < eps) delta += step;
        ui.clear();
        ui.el("rect", "g-band-y", { x: 0, y: ui.sy(L + eps), width: W, height: ui.sy(L - eps) - ui.sy(L + eps) }, ui.layer);
        ui.el("rect", "g-band-x", { x: ui.sx(a - delta), y: 0, width: ui.sx(a + delta) - ui.sx(a - delta), height: ui.H }, ui.layer);
        ui.el("path", "g-curve", { d: ui.pathOf(f) }, ui.layer);
        ui.dot(a, L, false, ui.layer);
        ui.text("L + ε", ui.x0, L + eps, "ne", "g-label", ui.layer);
        ui.text("L − ε", ui.x0, L - eps, "se", "g-label", ui.layer);
        ui.read.innerHTML = `ε = <b>${fmt(eps, 2, true)}</b>: every x within δ = <b>${fmt(delta, 3, true)}</b> of ${fmt(a)} keeps f(x) inside the band.`;
      }
      show(+input.value);
    },

    // Rectangles under the curve.
    riemann(ui) {
      const { t, f } = ui, [a, b] = t.dom;
      let n = t.start || 4, rule = "right";
      // The true area, from Simpson's rule with far more strips than any picture needs.
      let exact = t.exact;
      if (exact === undefined) {
        const m = 2000, w = (b - a) / m;
        exact = ui.at(f, a) + ui.at(f, b);
        for (let i = 1; i < m; i++) exact += (i % 2 ? 4 : 2) * ui.at(f, a + i * w);
        exact *= w / 3;
      }
      ui.slider("Rectangles", 1, t.max || 40, n, 1, v => { n = v; show(); });
      const pick = document.createElement("select");
      pick.setAttribute("aria-label", "Where each rectangle takes its height");
      pick.innerHTML = `<option value="left">Left endpoints</option><option value="right" selected>Right endpoints</option><option value="mid">Midpoints</option>`;
      pick.addEventListener("change", () => { rule = pick.value; show(); });
      pick.className = "plot-select";
      ui.controls.appendChild(pick);
      function show() {
        const w = (b - a) / n, shift = { left: 0, right: 1, mid: 0.5 }[rule];
        let sum = 0;
        ui.clear();
        for (let i = 0; i < n; i++) {
          const h = ui.at(f, a + (i + shift) * w);
          sum += h * w;
          ui.el("rect", "g-rect", { x: ui.sx(a + i * w), y: ui.sy(Math.max(h, 0)), width: ui.sx(a + w) - ui.sx(a), height: Math.abs(ui.sy(h) - ui.sy(0)) }, ui.layer);
        }
        ui.el("path", "g-curve", { d: ui.pathOf(f) }, ui.layer);
        ui.read.innerHTML = `<b>${n}</b> ${n === 1 ? "rectangle adds" : "rectangles add"} up to <b>${fmt(sum, 4, true)}</b>. The exact area is <b>${fmt(exact, 4, true)}</b>.`;
      }
      show();
    },

    // Newton's method: follow the tangent down to the axis, and start again from there.
    newton(ui) {
      const { t, f } = ui;
      let xs = [t.x0];
      const nextBtn = ui.button("Take a step", () => { const x = xs[xs.length - 1]; xs.push(x - ui.at(f, x) / ui.slope(f, x)); show(); }, "small");
      ui.button("Start over", () => { xs = [t.x0]; show(); });
      function show() {
        ui.clear();
        xs.forEach((x, i) => {
          const y = ui.at(f, x);
          ui.line("g-guide", x, 0, x, y, ui.layer);
          if (i + 1 < xs.length) ui.line("g-tan", x, y, xs[i + 1], 0, ui.layer);
          ui.dot(x, y, false, ui.layer, i === xs.length - 1 ? "g-move" : "");
        });
        nextBtn.disabled = xs.length > 6;
        ui.read.innerHTML = xs.map((x, i) => `x<sub>${i}</sub> = <b>${fmt(x, 5)}</b>`).join(", ");
      }
      show();
    },

    // A direction field for y' = F(x, y). Picking a start draws the solution through it.
    field(ui) {
      const { t } = ui, F = compile(t.F);
      const slope = (x, y) => { ui.env.x = x; ui.env.y = y; return F(ui.env); };
      const cols = 18, rows = 11, curvesLayer = ui.el("g");
      for (let i = 0; i <= cols; i++) for (let j = 0; j <= rows; j++) {
        const x = ui.x0 + (ui.x1 - ui.x0) * (i + 0.5) / (cols + 1), y = ui.y0 + (ui.y1 - ui.y0) * (j + 0.5) / (rows + 1);
        ui.through("g-field", x, y, slope(x, y), 11);
      }
      function solve(xs, ys) {
        let d = "";
        for (const dir of [1, -1]) {
          let x = xs, y = ys;
          const h = dir * (ui.x1 - ui.x0) / 400;
          d += `M${ui.sx(x).toFixed(1)} ${ui.sy(y).toFixed(1)}`;
          for (let k = 0; k < 800 && x >= ui.x0 && x <= ui.x1 && y > ui.y0 - 1 && y < ui.y1 + 1; k++) {
            // Runge-Kutta: four slopes averaged, far steadier than following one.
            const k1 = slope(x, y), k2 = slope(x + h / 2, y + h * k1 / 2), k3 = slope(x + h / 2, y + h * k2 / 2), k4 = slope(x + h, y + h * k3);
            y += h * (k1 + 2 * k2 + 2 * k3 + k4) / 6;
            x += h;
            d += `L${ui.sx(x).toFixed(1)} ${ui.sy(y).toFixed(1)}`;
          }
        }
        ui.el("path", "g-curve g-sol", { d }, curvesLayer);
        ui.dot(xs, ys, false, curvesLayer, "g-move");
      }
      for (const y of t.starts || []) ui.button(`Start at y(${fmt(t.x ?? 0)}) = ${fmt(y)}`, () => solve(t.x ?? 0, y));
      ui.button("Clear", () => { curvesLayer.textContent = ""; });
      ui.drag(solve);
      ui.read.textContent = t.read || "Tap the picture, or press a button, to draw the solution through that point.";
    },

    // Euler's method from (x0, y0) with a chosen step, beside the true solution (the picture's curve).
    euler(ui) {
      const { t, f } = ui, F = compile(t.F), steps = t.steps || [0.5, 0.25, 0.1, 0.05];
      const pick = ui.slider("Step size", 0, steps.length - 1, 0, 1, show);
      function show(k) {
        const h = steps[k];
        let x = t.x0, y = t.y0, d = `M${ui.sx(x)} ${ui.sy(y)}`;
        ui.clear();
        ui.dot(x, y, false, ui.layer);
        for (let i = 0; i < Math.round((t.to - t.x0) / h); i++) {
          ui.env.x = x; ui.env.y = y;
          y += h * F(ui.env);
          x += h;
          d += `L${ui.sx(x).toFixed(1)} ${ui.sy(y).toFixed(1)}`;
          ui.dot(x, y, false, ui.layer, "g-move g-small");
        }
        ui.el("path", "g-tan g-thin", { d, fill: "none" }, ui.layer);
        ui.read.innerHTML = `Step size <b>${fmt(h)}</b>: Euler lands on y(${fmt(t.to)}) ≈ <b>${fmt(y, 4, true)}</b>. The true value is <b>${fmt(ui.at(f, t.to), 4, true)}</b>.`;
      }
      show(+pick.value);
    },

    // Sliders for the letters in the first curve's formula.
    family(ui) {
      const { t } = ui;
      const show = () => {
        ui.drawCurves();
        if (t.read) ui.read.innerHTML = fill(t.read, ui.env);
      };
      for (const [name, [min, max, start, step]] of Object.entries(t.params)) {
        ui.env[name] = start;
        ui.slider(name, min, max, start, step || 0.25, v => { ui.env[name] = v; show(); });
      }
      show();
    }
  };

  // Draws every picture under `root` that hasn't been drawn yet.
  function hydrate(root) {
    (root || document).querySelectorAll("figure.fig-plot[data-plot]").forEach(fig => {
      if (fig.dataset.ready) return;
      fig.dataset.ready = "1";
      try { draw(fig, JSON.parse(fig.dataset.plot)); }
      catch (e) { fig.hidden = true; }  // a picture that can't be drawn shouldn't take the lesson down with it
    });
  }

  // The HTML for a picture, ready for hydrate(). The caption may hold math.
  const escAttr = s => String(s).replace(/&/g, "&amp;").replace(/'/g, "&#39;").replace(/</g, "&lt;");
  const figure = (spec, caption) =>
    `<figure class="fig-plot" data-plot='${escAttr(JSON.stringify(spec))}'><figcaption>${caption || ""}</figcaption></figure>`;

  return { hydrate, figure, compile };
})();