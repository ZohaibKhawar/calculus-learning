/* CalcLearners video player.
 *
 * Plays an "episode": a list of animated scenes. Each scene has beats, and a beat is
 * one or two narrated sentences plus an optional animation action ("do"). Narration
 * uses the browser's built-in text-to-speech and shows as TikTok-style captions.
 * The episode format is documented in video_ai.py (SYSTEM prompt).
 */
window.VideoPlayer = (function () {
  "use strict";

  const COLORS = { cyan: "#25F4EE", pink: "#FE2C55", yellow: "#FFD84D", green: "#6FDC8C", white: "#F5F5F5" };
  // Hex colours without "#": inside a macro body "#" means "argument".
  const MACROS = {
    "\\hl": "\\textcolor{25F4EE}{#1}", "\\pk": "\\textcolor{FE2C55}{#1}",
    "\\yl": "\\textcolor{FFD84D}{#1}", "\\gr": "\\textcolor{6FDC8C}{#1}"
  };
  const WPS = 2.6; // spoken words per second at 1x

  // ---------- Small helpers ----------
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function tex(src, display = true) {
    if (!window.katex) return esc(src);
    return katex.renderToString(String(src ?? ""), { displayMode: display, throwOnError: false, macros: { ...MACROS } });
  }

  // Plain text with \( inline math \): the text is escaped, the math is rendered.
  function rich(s) {
    return String(s ?? "").split(/(\\\([\s\S]+?\\\))/)
      .map((part, i) => i % 2 ? tex(part.slice(2, -2), false) : esc(part)).join("");
  }

  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, value);
    } catch (e) { return null; }
  }

  const div = (cls, html = "") => {
    const d = document.createElement("div");
    d.className = cls;
    d.innerHTML = html;
    return d;
  };

  // Reveal an element: animated, or instantly when rebuilding a scene after a seek.
  function reveal(node, instant, opts = {}) {
    node.classList.remove("hid");
    if (instant || !window.anime) { node.style.opacity = ""; node.style.transform = ""; return null; }
    return anime({
      targets: node, opacity: [0, 1], translateY: [opts.y ?? 24, 0], scale: [opts.scale ?? 0.96, 1],
      duration: opts.duration ?? 550, delay: opts.delay ?? 0, easing: "easeOutCubic",
      // Hand styling back to CSS (e.g. dimmed "past" equation lines).
      complete: () => { node.style.opacity = ""; node.style.transform = ""; }
    });
  }

  function confetti(stage) {
    if (!window.anime) return;
    const colors = Object.values(COLORS);
    for (let i = 0; i < 46; i++) {
      const c = div("confetti");
      c.style.background = colors[i % colors.length];
      c.style.left = 50 + (Math.random() - 0.5) * 20 + "%";
      stage.appendChild(c);
      anime({
        targets: c,
        translateX: (Math.random() - 0.5) * stage.clientWidth * 0.9,
        translateY: [0, -stage.clientHeight * (0.3 + Math.random() * 0.4), stage.clientHeight * 0.2],
        rotate: Math.random() * 720, opacity: [1, 1, 0],
        duration: 1400 + Math.random() * 600, easing: "easeOutQuad",
        complete: () => c.remove()
      });
    }
  }

  // ---------- Safe math expression compiler (no eval) ----------
  const FUNCS = {
    sin: Math.sin, cos: Math.cos, tan: Math.tan, sec: x => 1 / Math.cos(x), csc: x => 1 / Math.sin(x),
    cot: x => 1 / Math.tan(x), exp: Math.exp, ln: Math.log, log: Math.log10, sqrt: Math.sqrt,
    abs: Math.abs, asin: Math.asin, acos: Math.acos, atan: Math.atan,
    arcsin: Math.asin, arccos: Math.acos, arctan: Math.atan, cbrt: Math.cbrt
  };
  const CONSTS = { pi: Math.PI, e: Math.E };
  const NAMES = [...Object.keys(FUNCS), ...Object.keys(CONSTS), "x", "y"].sort((a, b) => b.length - a.length);

  function compile(src) {
    // Tokenize; split glued names like "xy" or "pix" into known pieces.
    const raw = String(src).match(/\d+\.?\d*|\.\d+|[a-zA-Z]+|[-+*/^(),]|\S/g) || [];
    const toks = [];
    for (const t of raw) {
      if (!/^[a-zA-Z]+$/.test(t)) { toks.push(t); continue; }
      let w = t.toLowerCase();
      while (w) {
        const name = NAMES.find(n => w.startsWith(n));
        if (!name) throw new Error("Unknown name in expression: " + t);
        toks.push(name);
        w = w.slice(name.length);
      }
    }
    // Insert implicit multiplication: 2x, x(…), )(, 3sin(x) …
    const isValue = t => /^[\d.]/.test(t) || t === "x" || t === "y" || t in CONSTS;
    const out = [];
    toks.forEach((t, i) => {
      const prev = out[out.length - 1];
      if (i && (isValue(prev) || prev === ")") && (isValue(t) || t === "(" || t in FUNCS)) out.push("*");
      out.push(t);
    });

    let p = 0;
    const peek = () => out[p];
    const expect = t => { if (out[p++] !== t) throw new Error("Expected " + t + " in " + src); };
    const expr = () => {
      let f = term();
      while (peek() === "+" || peek() === "-") {
        const op = out[p++], a = f, b = term();
        f = op === "+" ? (x, y) => a(x, y) + b(x, y) : (x, y) => a(x, y) - b(x, y);
      }
      return f;
    };
    const term = () => {
      let f = unary();
      while (peek() === "*" || peek() === "/") {
        const op = out[p++], a = f, b = unary();
        f = op === "*" ? (x, y) => a(x, y) * b(x, y) : (x, y) => a(x, y) / b(x, y);
      }
      return f;
    };
    const unary = () => {
      if (peek() === "-") { p++; const a = unary(); return (x, y) => -a(x, y); }
      if (peek() === "+") { p++; return unary(); }
      return power();
    };
    const power = () => {
      const base = atom();
      if (peek() === "^") { p++; const ex = unary(); return (x, y) => Math.pow(base(x, y), ex(x, y)); }
      return base;
    };
    const atom = () => {
      const t = out[p++];
      if (t === undefined) throw new Error("Unexpected end of " + src);
      if (t === "(") { const f = expr(); expect(")"); return f; }
      if (/^[\d.]/.test(t)) { const v = parseFloat(t); return () => v; }
      if (t === "x") return x => x;
      if (t === "y") return (x, y) => y;
      if (t in CONSTS) { const v = CONSTS[t]; return () => v; }
      if (t in FUNCS) {
        const fn = FUNCS[t];
        let arg;
        if (peek() === "(") { p++; arg = expr(); expect(")"); } else arg = power();
        return (x, y) => fn(arg(x, y));
      }
      throw new Error("Unexpected '" + t + "' in " + src);
    };
    const f = expr();
    if (p < out.length) throw new Error("Unexpected '" + out[p] + "' in " + src);
    return f;
  }

  // ---------- Scenes ----------
  // Each scene builder fills `box` and returns { beat(i, instant, ms), hold?(i, ms) }.
  // Builders read the action for beat i from scene.beats[i].do (or a default sequence).
  const act = (scene, i, defaults, fallback = "hold") => scene.beats[i]?.do || defaults[i] || fallback;
  let graphCount = 0;

  const SCENES = {
    title(s, box) {
      const words = String(s.text || "").split(/\s+/).map(w => `<span class="w hid">${esc(w)}</span>`).join(" ");
      box.innerHTML = `<div class="sc-title">
        <div class="emoji hid">${esc(s.emoji || "✨")}</div>
        <h1>${words}</h1>
        <p class="hid">${esc(s.sub || "")}</p></div>`;
      const showSub = instant => reveal(box.querySelector("p"), instant, { delay: instant ? 0 : 300 });
      return {
        beat(i, instant) {
          if (i === 0) {
            reveal(box.querySelector(".emoji"), instant, { scale: 0.3, y: 0, duration: 700 });
            box.querySelectorAll(".w").forEach((w, k) => reveal(w, instant, { delay: 120 + k * 110, y: 40 }));
            if (s.beats.length === 1) showSub(instant);
          } else if (i === 1) showSub(instant);
        }
      };
    },

    equation(s, box) {
      const lines = s.lines || [];
      box.innerHTML = `<div class="sc-eq" style="--n:${Math.max(lines.length, 1)}">
        ${lines.map(l => `<div class="eq-line hid">${tex(l)}</div>`).join("")}</div>`;
      const nodes = [...box.querySelectorAll(".eq-line")];
      let shown = 0;
      return {
        beat(i, instant) {
          const a = act(s, i, [], "next");
          if (a === "next" && shown < nodes.length) {
            nodes.forEach(n => n.classList.remove("now"));
            nodes.slice(0, shown).forEach(n => n.classList.add("past"));
            const n = nodes[shown++];
            n.classList.add("now");
            reveal(n, instant, { y: 30 });
          } else if (a === "all") {
            while (shown < nodes.length) reveal(nodes[shown++], instant);
          }
        }
      };
    },

    layers(s, box) {
      const layers = s.layers || [];
      // Nested rings: outermost first.
      let html = "";
      layers.forEach((l, k) => {
        html += `<div class="ring hid" data-k="${k}" style="--k:${k}">
          <div class="ring-head"><span class="chip">${esc(l.label)}</span>${tex(l.expr, false)}</div>`;
      });
      html += "</div>".repeat(layers.length);
      box.innerHTML = `<div class="sc-layers" style="--n:${layers.length}">
        <div class="onion">${html}</div>
        <div class="chain"><div class="chain-row"></div></div>
        <div class="chain-result hid">${tex(s.result || "")}</div></div>`;
      const rings = [...box.querySelectorAll(".ring")];
      const row = box.querySelector(".chain-row");
      let peeled = 0;
      const defaults = ["build", ...layers.map(() => "peel"), "result"];
      return {
        beat(i, instant) {
          for (const a of act(s, i, defaults).split(";")) {
            if (a === "build") rings.forEach((r, k) => reveal(r, instant, { delay: k * 260, scale: 0.85, y: 0 }));
            if (a === "peel" && peeled < layers.length) {
              const k = peeled++;
              rings.forEach(r => r.classList.remove("peeling"));
              rings[k].classList.add("peeling");
              rings.slice(0, k).forEach(r => r.classList.add("peeled"));
              const chip = div("deriv hid", (k ? '<span class="times">×</span>' : "") + tex(layers[k].deriv, false));
              chip.style.setProperty("--k", k);
              row.appendChild(chip);
              reveal(chip, instant, { y: -40, scale: 0.6, duration: 650 });
            }
            if (a === "result") {
              rings.forEach(r => { r.classList.remove("peeling"); r.classList.add("peeled"); });
              reveal(box.querySelector(".chain-result"), instant, { y: 20, scale: 0.9, duration: 700 });
            }
          }
        }
      };
    },

    graph(s, box, player) {
      const W = Math.max(320, box.clientWidth || 800), H = Math.max(200, box.clientHeight || 400);
      let { xmin = -5, xmax = 5, ymin = -3, ymax = 3, equal = false } = s.view || {};
      if (equal) {
        // Same scale on both axes so circles look like circles.
        const ux = (xmax - xmin) / W, uy = (ymax - ymin) / H, u = Math.max(ux, uy);
        const cx = (xmin + xmax) / 2, cy = (ymin + ymax) / 2;
        xmin = cx - u * W / 2; xmax = cx + u * W / 2; ymin = cy - u * H / 2; ymax = cy + u * H / 2;
      }
      const X = x => (x - xmin) / (xmax - xmin) * W;
      const Y = y => H - (y - ymin) / (ymax - ymin) * H;
      const curves = (s.curves || []).map(c => {
        try { return { ...c, f: compile(c.fn || c.implicit) }; } catch (e) { console.warn(e.message); return null; }
      }).filter(Boolean);
      const main = curves.find(c => c.fn);
      const colors = [COLORS.cyan, COLORS.yellow, COLORS.green];

      // Grid, axes and tick labels.
      const nice = r => { const p = Math.pow(10, Math.floor(Math.log10(r))); const n = r / p; return (n < 1.5 ? 1 : n < 3.5 ? 2 : n < 7.5 ? 5 : 10) * p; };
      const sx = nice((xmax - xmin) / 8), sy = nice((ymax - ymin) / 5);
      const fmt = v => +v.toFixed(6) + "";
      let grid = "", labels = "";
      const ax = Math.min(Math.max(Y(0), 12), H - 6), ay = Math.min(Math.max(X(0), 6), W - 30);
      for (let v = Math.ceil(xmin / sx) * sx; v <= xmax; v += sx) {
        grid += `<line x1="${X(v)}" y1="0" x2="${X(v)}" y2="${H}"/>`;
        if (Math.abs(v) > sx / 2) labels += `<text x="${X(v)}" y="${ax + 16}" text-anchor="middle">${fmt(v)}</text>`;
      }
      for (let v = Math.ceil(ymin / sy) * sy; v <= ymax; v += sy) {
        grid += `<line x1="0" y1="${Y(v)}" x2="${W}" y2="${Y(v)}"/>`;
        if (Math.abs(v) > sy / 2) labels += `<text x="${ay - 6}" y="${Y(v) + 4}" text-anchor="end">${fmt(v)}</text>`;
      }

      // Curve paths.
      const paths = curves.map((c, k) => {
        let d = "";
        if (c.fn) {
          // Sample the curve; lift the pen at gaps (undefined points) and jumps (asymptotes).
          const N = 900, span = ymax - ymin;
          let pen = false, prev = null;
          for (let j = 0; j <= N; j++) {
            const x = xmin + (xmax - xmin) * j / N, y = c.f(x, 0);
            if (!isFinite(y)) { pen = false; prev = null; continue; }
            if (prev !== null && Math.abs(y - prev) > span * 1.5) pen = false;
            const py = Y(Math.max(ymin - span, Math.min(ymax + span, y)));
            d += (pen ? "L" : "M") + X(x).toFixed(1) + "," + py.toFixed(1);
            pen = true;
            prev = y;
          }
        } else {
          d = implicitPath(c.f, xmin, xmax, ymin, ymax, W, H, X, Y);
        }
        return `<path class="curve hid" data-k="${k}" d="${d}" stroke="${colors[k % colors.length]}"/>`;
      }).join("");

      const clipId = "gclip" + (++graphCount); // unique, since a page can show several graphs
      box.innerHTML = `<div class="sc-graph">
        <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">
          <defs><clipPath id="${clipId}"><rect width="${W}" height="${H}"/></clipPath></defs>
          <g class="grid">${grid}</g>
          <g class="axes"><line x1="0" y1="${Y(0)}" x2="${W}" y2="${Y(0)}"/><line x1="${X(0)}" y1="0" x2="${X(0)}" y2="${H}"/></g>
          <g class="ticks">${labels}</g>
          <g clip-path="url(#${clipId})">${paths}<g class="fx"></g></g>
        </svg>
        <div class="legend">${curves.filter(c => c.label).map((c, k) =>
          `<span style="--c:${colors[curves.indexOf(c) % colors.length]}">${rich(c.label)}</span>`).join("")}</div>
      </div>`;
      const fx = box.querySelector(".fx");
      const NS = "http://www.w3.org/2000/svg";
      const svgEl = (tag, attrs) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); fx.appendChild(e); return e; };
      const slopeAt = (f, a) => { const h = (xmax - xmin) * 1e-5; return (f(a + h, 0) - f(a - h, 0)) / (2 * h); };
      const fmtSlope = m => Math.abs(m) < 5e-3 ? "0" : (Math.abs(m - Math.round(m)) < 5e-3 ? Math.round(m) + "" : m.toFixed(2));
      // Unit direction of a line with slope m, in screen pixels.
      const dir = m => { const px = 1, py = -m * (H / (ymax - ymin)) / (W / (xmax - xmin)); const n = Math.hypot(px, py); return [px / n, py / n]; };

      function line(x0, y0, m, color, instant, labelText) {
        const [dx, dy] = dir(m), L = Math.hypot(W, H) * 0.32, cx = X(x0), cy = Y(y0);
        const ln = svgEl("line", { x1: cx, y1: cy, x2: cx, y2: cy, class: "tan", stroke: color });
        const dot = svgEl("circle", { cx, cy, r: 7, class: "dot", fill: color });
        const ends = { x1: cx - dx * L, y1: cy - dy * L, x2: cx + dx * L, y2: cy + dy * L };
        if (labelText) {
          const t = svgEl("text", { x: cx + 14, y: cy - 14, class: "glabel", fill: color });
          t.textContent = labelText;
        }
        if (instant || !window.anime) { for (const k in ends) ln.setAttribute(k, ends[k]); return; }
        anime({ targets: dot, r: [0, 7], duration: 400, easing: "easeOutBack" });
        return anime({ targets: ln, ...Object.fromEntries(Object.entries(ends).map(([k, v]) => [k, [k.startsWith("x") ? cx : cy, v]])), duration: 700, easing: "easeOutCubic" });
      }

      const actions = {
        draw(arg, instant) {
          box.querySelectorAll(".curve").forEach((p, k) => {
            if (arg !== undefined && arg !== "" && +arg !== k) return;
            p.classList.remove("hid");
            if (instant || !window.anime) return;
            if (curves[k].fn) {
              const len = p.getTotalLength();
              p.style.strokeDasharray = len;
              player.track(anime({ targets: p, strokeDashoffset: [len, 0], duration: 1600, easing: "easeInOutSine",
                complete: () => { p.style.strokeDasharray = ""; } }));
            } else {
              player.track(anime({ targets: p, opacity: [0, 1], duration: 900, easing: "easeOutQuad" }));
            }
          });
        },
        tangent(arg, instant) {
          if (!main) return;
          const a = +arg, m = slopeAt(main.f, a);
          line(a, main.f(a, 0), m, COLORS.pink, instant, "slope = " + fmtSlope(m));
        },
        tangentxy(arg, instant) {
          const [x0, y0, m] = arg.split(",").map(Number);
          line(x0, y0, m, COLORS.pink, instant, "slope = " + fmtSlope(m));
        },
        point(arg, instant) {
          const [x0, y0] = arg.split(",").map(Number);
          const c = svgEl("circle", { cx: X(x0), cy: Y(y0), r: 7, class: "dot", fill: COLORS.yellow });
          const t = svgEl("text", { x: X(x0) + 12, y: Y(y0) + 22, class: "glabel", fill: COLORS.yellow });
          t.textContent = `(${fmt(x0)}, ${fmt(y0)})`;
          if (!instant && window.anime) anime({ targets: c, r: [0, 7], duration: 500, easing: "easeOutBack" });
        },
        vline(arg, instant) {
          const a = +arg;
          const ln = svgEl("line", { x1: X(a), y1: 0, x2: X(a), y2: H, class: "vline" });
          if (!instant && window.anime) player.track(anime({ targets: ln, opacity: [0, 1], duration: 500 }));
        },
        trace(arg, instant, ms) {
          if (!main || instant) return;
          const x0 = xmin + (xmax - xmin) * 0.06, x1 = xmax - (xmax - xmin) * 0.06;
          const ln = svgEl("line", { class: "tan", stroke: COLORS.pink });
          const dot = svgEl("circle", { r: 8, class: "dot", fill: COLORS.pink });
          const t = svgEl("text", { class: "glabel", fill: COLORS.pink });
          const L = Math.hypot(W, H) * 0.12, o = { x: x0 };
          const update = () => {
            const y = main.f(o.x, 0), m = slopeAt(main.f, o.x);
            if (!isFinite(y)) return;
            const [dx, dy] = dir(m), cx = X(o.x), cy = Y(y);
            ln.setAttribute("x1", cx - dx * L); ln.setAttribute("y1", cy - dy * L);
            ln.setAttribute("x2", cx + dx * L); ln.setAttribute("y2", cy + dy * L);
            dot.setAttribute("cx", cx); dot.setAttribute("cy", cy);
            t.setAttribute("x", Math.min(cx + 14, W - 150)); t.setAttribute("y", Math.max(cy - 16, 20));
            t.textContent = "slope = " + fmtSlope(m);
          };
          update();
          if (window.anime) player.track(anime({ targets: o, x: [x0, x1], duration: Math.max(1800, ms - 400), easing: "easeInOutSine", update,
            complete: () => { ln.remove(); dot.remove(); t.remove(); } }));
        },
        clear() { fx.innerHTML = ""; }
      };
      return {
        beat(i, instant, ms) {
          for (const a of act(s, i, ["draw"]).split(";")) {
            const [name, arg] = a.trim().split(":");
            if (actions[name]) actions[name](arg, instant, ms);
          }
        }
      };
    },

    cards(s, box) {
      const items = s.items || [];
      box.innerHTML = `<div class="sc-cards" style="--n:${items.length}">${items.map(c => `
        <div class="card hid"><div class="icon">${esc(c.icon || "💡")}</div>
          <b>${rich(c.title)}</b><p>${rich(c.text)}</p></div>`).join("")}</div>`;
      const cards = [...box.querySelectorAll(".card")];
      let shown = 0;
      return {
        beat(i, instant) {
          const a = act(s, i, [], "next");
          if (a === "next" && shown < cards.length) reveal(cards[shown++], instant, { scale: 0.8, y: 30, duration: 600 });
          if (a === "all") while (shown < cards.length) reveal(cards[shown++], instant);
        }
      };
    },

    compare(s, box) {
      const side = (p, cls) => `<div class="side ${cls} hid"><b>${rich(p?.title)}</b>${(p?.lines || []).map(l => tex(l)).join("")}</div>`;
      box.innerHTML = `<div class="sc-compare">${side(s.left, "left")}<div class="link hid">=</div>${side(s.right, "right")}</div>`;
      return {
        beat(i, instant) {
          const a = act(s, i, ["left", "right", "link"]);
          if (a === "left") reveal(box.querySelector(".left"), instant, { y: 0, scale: 0.9 });
          if (a === "right") reveal(box.querySelector(".right"), instant, { y: 0, scale: 0.9 });
          if (a === "link") {
            reveal(box.querySelector(".link"), instant, { scale: 0.2, y: 0, duration: 700 });
            box.querySelector(".sc-compare").classList.add("linked");
          }
        }
      };
    },

    pause(s, box, player) {
      const secs = s.seconds || 5;
      box.innerHTML = `<div class="sc-pause">
        <div class="tag">⏸ Pause &amp; try it</div>
        <div class="q hid">${tex(s.question)}</div>
        <div class="timer hid"><svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="44"/><circle class="arc" cx="50" cy="50" r="44"/></svg><span>${secs}</span></div>
        <div class="a hid">${tex(s.answer)}</div></div>`;
      return {
        beat(i, instant) {
          if (i === 0) reveal(box.querySelector(".q"), instant, { scale: 0.8 });
          if (i >= 1) {
            box.querySelector(".timer").classList.add("hid");
            reveal(box.querySelector(".a"), instant, { scale: 0.7, duration: 700 });
            if (!instant) confetti(player.stage);
          }
        },
        hold(i, ms) {
          if (i !== 0) return;
          const t = box.querySelector(".timer"), num = t.querySelector("span"), arc = t.querySelector(".arc");
          reveal(t, false, { scale: 0.5, y: 0 });
          const o = { left: secs };
          if (window.anime) {
            player.track(anime({ targets: arc, strokeDashoffset: [0, 276.5], duration: ms, easing: "linear" }));
            player.track(anime({ targets: o, left: [secs, 0], duration: ms, easing: "linear",
              update: () => { num.textContent = Math.ceil(o.left); } }));
          }
        }
      };
    }
  };

  function implicitPath(F, xmin, xmax, ymin, ymax, W, H, X, Y) {
    // Marching squares: find where F(x, y) changes sign on a grid.
    const nx = 200, ny = Math.max(40, Math.round(nx * H / W));
    const dx = (xmax - xmin) / nx, dy = (ymax - ymin) / ny;
    const v = new Float64Array((nx + 1) * (ny + 1));
    for (let j = 0; j <= ny; j++) for (let i = 0; i <= nx; i++) v[j * (nx + 1) + i] = F(xmin + i * dx, ymin + j * dy);
    const SEG = { 1: [[3, 0]], 2: [[0, 1]], 3: [[3, 1]], 4: [[1, 2]], 5: [[3, 0], [1, 2]], 6: [[0, 2]], 7: [[3, 2]],
      8: [[2, 3]], 9: [[0, 2]], 10: [[0, 1], [2, 3]], 11: [[1, 2]], 12: [[1, 3]], 13: [[0, 1]], 14: [[3, 0]] };
    let d = "";
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const a = v[j * (nx + 1) + i], b = v[j * (nx + 1) + i + 1], c = v[(j + 1) * (nx + 1) + i + 1], e = v[(j + 1) * (nx + 1) + i];
        if (![a, b, c, e].every(isFinite)) continue;
        const code = (a > 0) | (b > 0) << 1 | (c > 0) << 2 | (e > 0) << 3;
        if (!SEG[code]) continue;
        const x0 = xmin + i * dx, y0 = ymin + j * dy;
        const pt = k => {
          if (k === 0) return [x0 + dx * a / (a - b), y0];
          if (k === 1) return [x0 + dx, y0 + dy * b / (b - c)];
          if (k === 2) return [x0 + dx * e / (e - c), y0 + dy];
          return [x0, y0 + dy * a / (a - e)];
        };
        for (const [p, q] of SEG[code]) {
          const P = pt(p), Q = pt(q);
          d += `M${X(P[0]).toFixed(1)},${Y(P[1]).toFixed(1)}L${X(Q[0]).toFixed(1)},${Y(Q[1]).toFixed(1)}`;
        }
      }
    }
    return d;
  }

  // ---------- Voice (browser text-to-speech) ----------
  const Voice = {
    ok: "speechSynthesis" in window,
    voice: null,
    pick() {
      const voices = speechSynthesis.getVoices().filter(v => /^en([-_]|$)/i.test(v.lang));
      const prefs = [/natural/i, /neural/i, /google us english/i, /samantha/i, /aria/i, /jenny/i, /google uk english female/i, /zira/i];
      for (const p of prefs) {
        const v = voices.find(v => p.test(v.name));
        if (v) { this.voice = v; return; }
      }
      this.voice = voices.find(v => /en-US/i.test(v.lang)) || voices[0] || null;
    },
    speak(text, rate, onend, onword) {
      const u = new SpeechSynthesisUtterance(text);
      if (this.voice) u.voice = this.voice;
      u.lang = this.voice?.lang || "en-US";
      u.rate = Math.min(rate, 2);
      u.onend = onend;
      u.onerror = onend;
      u.onboundary = e => { if (e.name === "word") onword(e.charIndex); };
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
    },
    stop() { if (this.ok) speechSynthesis.cancel(); }
  };
  if (Voice.ok) {
    Voice.pick();
    speechSynthesis.addEventListener("voiceschanged", () => Voice.pick());
  }

  // ---------- The player ----------
  let active = null; // only one player plays at a time

  const fmtTime = ms => {
    const s = Math.max(0, Math.round(ms / 1000));
    return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
  };

  class Player {
    constructor(root, episode, opts = {}) {
      if (active) active.destroy();
      active = this;
      this.root = root;
      this.ep = episode;
      this.opts = opts;
      this.rate = +(store("vp-rate") || 1);
      this.voiceOn = Voice.ok && store("vp-voice") !== "off";
      this.ccOn = store("vp-cc") !== "off";
      this.flat = [];
      episode.scenes.forEach((s, si) => (s.beats || []).forEach((b, bi) =>
        this.flat.push({ si, bi, say: String(b.say || ""), words: String(b.say || "").split(/\s+/).filter(Boolean) })));
      this.pos = 0;
      this.playing = false;
      this.ended = false;
      this.sceneIdx = -1;
      this.ctl = null;
      this.token = 0;
      this.timers = [];
      this.anims = [];
      this.build();
      this.timeline();
      this.show(0);
    }

    // ----- timing -----
    holdMs(k) {
      const { si, bi } = this.flat[k], s = this.ep.scenes[si];
      return s.type === "pause" && bi === 0 ? (s.seconds || 5) * 1000 : 0;
    }
    sayMs(k) { return Math.max(1500, this.flat[k].words.length / WPS * 1000) / this.rate + 300; }
    timeline() {
      this.starts = [];
      let t = 0;
      this.flat.forEach((_, k) => { this.starts.push(t); t += this.sayMs(k) + this.holdMs(k); });
      this.total = t;
      // Scene start ticks on the progress bar.
      this.ticks.innerHTML = this.ep.scenes.map((_, si) => {
        const k = this.flat.findIndex(f => f.si === si);
        return k > 0 ? `<i style="left:${100 * this.starts[k] / this.total}%"></i>` : "";
      }).join("");
    }
    now() {
      const k = this.pos;
      if (!this.playing) return this.starts[k] || 0;
      return this.starts[k] + Math.min(performance.now() - this.beatStart, this.sayMs(k) + this.holdMs(k));
    }

    // ----- DOM -----
    build() {
      this.root.innerHTML = `
        <div class="vp" tabindex="0" aria-label="Video lesson player">
          <div class="vp-stage">
            <div class="vp-heading"></div>
            <div class="vp-scene"></div>
            <div class="vp-cc" aria-live="off"></div>
            <button class="vp-big" aria-label="Play">▶</button>
            <div class="vp-end" hidden></div>
          </div>
          <div class="vp-bar">
            <button class="vp-prev" title="Previous scene (←)" aria-label="Previous scene">⏮</button>
            <button class="vp-play" title="Play / pause (space)" aria-label="Play">▶</button>
            <button class="vp-next" title="Next scene (→)" aria-label="Next scene">⏭</button>
            <span class="vp-time">0:00 / 0:00</span>
            <div class="vp-progress" role="slider" aria-label="Seek" tabindex="0"><div class="vp-fill"></div><div class="vp-ticks"></div></div>
            <button class="vp-speed" title="Playback speed">1×</button>
            <button class="vp-voice" title="Voiceover on/off"></button>
            <button class="vp-cc-btn" title="Captions on/off">CC</button>
            <button class="vp-fs" title="Fullscreen" aria-label="Fullscreen">⛶</button>
          </div>
        </div>`;
      const q = s => this.root.querySelector(s);
      this.vp = q(".vp");
      this.stage = q(".vp-stage");
      this.sceneBox = q(".vp-scene");
      this.heading = q(".vp-heading");
      this.cc = q(".vp-cc");
      this.big = q(".vp-big");
      this.endCard = q(".vp-end");
      this.ticks = q(".vp-ticks");
      this.fill = q(".vp-fill");
      this.timeEl = q(".vp-time");

      q(".vp-play").onclick = () => this.toggle();
      this.big.onclick = () => this.play();
      q(".vp-prev").onclick = () => this.prevScene();
      q(".vp-next").onclick = () => this.nextScene();
      const speeds = [1, 1.25, 1.5, 1.75, 2];
      const speedBtn = q(".vp-speed");
      speedBtn.textContent = this.rate + "×";
      speedBtn.onclick = () => {
        this.rate = speeds[(speeds.indexOf(this.rate) + 1) % speeds.length];
        store("vp-rate", this.rate);
        speedBtn.textContent = this.rate + "×";
        this.timeline();
        if (this.playing) this.run(this.pos);
      };
      const voiceBtn = q(".vp-voice");
      const paintVoice = () => {
        voiceBtn.textContent = this.voiceOn ? "🔊" : "🔇";
        voiceBtn.title = Voice.ok ? (this.voiceOn ? "Mute voiceover" : "Turn voiceover on") : "This browser has no text-to-speech";
      };
      paintVoice();
      voiceBtn.onclick = () => {
        if (!Voice.ok) return;
        this.voiceOn = !this.voiceOn;
        store("vp-voice", this.voiceOn ? "on" : "off");
        paintVoice();
        if (this.playing) this.run(this.pos);
      };
      const ccBtn = q(".vp-cc-btn");
      ccBtn.classList.toggle("off", !this.ccOn);
      ccBtn.onclick = () => {
        this.ccOn = !this.ccOn;
        store("vp-cc", this.ccOn ? "on" : "off");
        ccBtn.classList.toggle("off", !this.ccOn);
        this.cc.hidden = !this.ccOn;
      };
      this.cc.hidden = !this.ccOn;
      q(".vp-fs").onclick = () => {
        if (document.fullscreenElement) document.exitFullscreen();
        else this.vp.requestFullscreen?.();
      };
      const bar = q(".vp-progress");
      bar.onclick = e => {
        const r = bar.getBoundingClientRect();
        this.seekTime((e.clientX - r.left) / r.width * this.total);
      };
      this.vp.addEventListener("keydown", e => {
        if (e.target.closest("input, textarea")) return;
        if (e.key === " " || e.key === "k") { e.preventDefault(); this.toggle(); }
        if (e.key === "ArrowRight") { e.preventDefault(); this.nextScene(); }
        if (e.key === "ArrowLeft") { e.preventDefault(); this.prevScene(); }
      });
      this.stage.addEventListener("click", e => {
        if (e.target === this.stage || e.target.closest(".vp-scene")) this.toggle();
      });
      this.loop = () => {
        if (!this.root.isConnected) { this.destroy(); return; }
        this.paintTime();
        this.raf = requestAnimationFrame(this.loop);
      };
      this.raf = requestAnimationFrame(this.loop);
    }

    paintTime() {
      const t = this.ended ? this.total : this.now();
      this.fill.style.width = (100 * t / this.total) + "%";
      this.timeEl.textContent = fmtTime(t) + " / " + fmtTime(this.total);
    }

    paintPlay() {
      const b = this.root.querySelector(".vp-play");
      b.textContent = this.playing ? "⏸" : "▶";
      b.setAttribute("aria-label", this.playing ? "Pause" : "Play");
      // The big button is only for starting; after that the bar and a click on the screen do it.
      this.big.hidden = this.playing || this.ended || this.started;
    }

    // ----- scene rendering -----
    track(a) { if (a) this.anims.push(a); return a; }

    stopFx() {
      this.token++;
      this.timers.forEach(clearTimeout);
      this.timers = [];
      this.anims.forEach(a => a.pause());
      this.anims = [];
      Voice.stop();
    }

    // Render scene si with beats before `upto` already applied (no animation).
    enter(si, upto) {
      const s = this.ep.scenes[si];
      this.sceneIdx = si;
      this.heading.innerHTML = s.heading ? rich(s.heading) : "";
      this.heading.hidden = !s.heading;
      this.sceneBox.className = "vp-scene t-" + s.type;
      this.sceneBox.innerHTML = "";
      const make = SCENES[s.type];
      try {
        this.ctl = make ? make(s, this.sceneBox, this) : { beat() {} };
      } catch (e) {
        console.error("Scene failed", s, e);
        this.ctl = { beat() {} };
      }
      for (let b = 0; b < upto; b++) this.ctl.beat(b, true, 0);
      if (s.heading && window.anime && upto === 0) anime({ targets: this.heading, opacity: [0, 1], translateX: [-20, 0], duration: 500, easing: "easeOutCubic" });
    }

    captions(k, wordIdx = -1) {
      if (!this.ccOn) return;
      const words = this.flat[k].words;
      if (this.ccFor !== k) {
        this.ccFor = k;
        this.cc.innerHTML = words.map(w => `<span>${esc(w)}</span>`).join(" ");
      }
      this.cc.querySelectorAll("span").forEach((s, i) => s.classList.toggle("on", i === wordIdx));
    }

    // Show beat k (paused): scene state including beat k, no narration.
    show(k) {
      this.pos = k;
      const { si, bi } = this.flat[k];
      this.enter(si, bi + 1);
      this.captions(k);
      this.paintTime();
      this.paintPlay();
    }

    // Play beat k: animate it, narrate it, then move on.
    run(k) {
      this.stopFx();
      const token = this.token;
      this.pos = k;
      this.ended = false;
      this.endCard.hidden = true;
      const f = this.flat[k];
      if (f.si !== this.sceneIdx || f.bi === 0 || this.needsEnter) this.enter(f.si, f.bi);
      this.needsEnter = false;
      const sayMs = this.sayMs(k), holdMs = this.holdMs(k);
      this.beatStart = performance.now();
      this.ctl.beat(f.bi, false, sayMs);
      this.captions(k, 0);
      this.paintPlay();

      // Captions follow speech word boundaries when the browser reports them,
      // otherwise an estimate based on elapsed time.
      let boundary = false;
      const starts = [];
      let pos = 0;
      for (const w of f.words) { pos = f.say.indexOf(w, pos); starts.push(pos); pos += w.length; }
      const tick = () => {
        if (token !== this.token || boundary) return;
        const frac = (performance.now() - this.beatStart) / (sayMs - 300);
        this.captions(k, Math.min(f.words.length - 1, Math.floor(frac * f.words.length)));
        this.timers.push(setTimeout(tick, 90));
      };
      tick();

      const afterSay = () => {
        if (token !== this.token) return;
        this.captions(k, -1);
        if (holdMs && this.ctl.hold) this.ctl.hold(f.bi, holdMs);
        this.timers.push(setTimeout(() => token === this.token && this.advance(), holdMs + 250));
      };

      if (this.voiceOn && f.say) {
        let done = false;
        const finish = () => { if (!done) { done = true; afterSay(); } };
        Voice.speak(f.say, this.rate, () => token === this.token && finish(), ci => {
          if (token !== this.token) return;
          boundary = true;
          let w = 0;
          while (w + 1 < starts.length && starts[w + 1] <= ci) w++;
          this.captions(k, w);
        });
        // Safety net in case the speech engine never reports the end.
        this.timers.push(setTimeout(() => token === this.token && finish(), sayMs * 2.5 + 4000));
      } else {
        this.timers.push(setTimeout(afterSay, sayMs));
      }
    }

    advance() {
      if (this.pos + 1 < this.flat.length) this.run(this.pos + 1);
      else this.finish();
    }

    finish() {
      this.stopFx();
      this.playing = false;
      this.ended = true;
      this.paintPlay();
      this.paintTime();
      this.cc.innerHTML = "";
      this.endCard.hidden = false;
      this.endCard.innerHTML = `<div class="end-in">
        <div class="emoji">🔥</div><h2>Episode complete!</h2>
        <p>Now prove it: 18 questions, from easy to expert.</p>
        <div class="row"><button class="end-practice">Start practice</button>
        <button class="ghost end-replay">↺ Replay</button>
        ${this.opts.hasNext ? '<button class="ghost end-next">Next episode ▶</button>' : ""}</div></div>`;
      this.endCard.querySelector(".end-practice").onclick = () => this.opts.onPractice?.();
      this.endCard.querySelector(".end-replay").onclick = () => { this.endCard.hidden = true; this.pos = 0; this.play(); };
      const nx = this.endCard.querySelector(".end-next");
      if (nx) nx.onclick = () => this.opts.onNext?.();
      if (window.anime) anime({ targets: this.endCard.querySelector(".end-in"), scale: [0.8, 1], opacity: [0, 1], duration: 600, easing: "easeOutBack" });
      confetti(this.stage);
      this.opts.onEnd?.();
    }

    // ----- controls -----
    play() {
      if (this.ended) { this.ended = false; this.pos = 0; }
      this.playing = true;
      this.started = true;
      this.needsEnter = true; // rebuild the scene so the current beat replays cleanly
      this.run(this.pos);
      this.vp.focus({ preventScroll: true });
    }
    pause() {
      this.stopFx();
      this.playing = false;
      this.show(this.pos);
    }
    toggle() { this.playing ? this.pause() : this.play(); }
    goto(k) {
      k = Math.max(0, Math.min(this.flat.length - 1, k));
      this.ended = false;
      this.endCard.hidden = true;
      if (this.playing) { this.needsEnter = true; this.run(k); } else { this.stopFx(); this.show(k); }
    }
    seekTime(t) {
      let k = 0;
      while (k + 1 < this.starts.length && this.starts[k + 1] <= t) k++;
      this.goto(k);
    }
    sceneStart(si) { return this.flat.findIndex(f => f.si === si); }
    nextScene() {
      const si = this.flat[this.pos].si;
      if (si + 1 < this.ep.scenes.length) this.goto(this.sceneStart(si + 1));
    }
    prevScene() {
      const { si, bi } = this.flat[this.pos];
      this.goto(this.sceneStart(bi > 0 || si === 0 ? si : si - 1));
    }
    destroy() {
      this.stopFx();
      cancelAnimationFrame(this.raf);
      if (active === this) active = null;
    }
  }

  // Draw a scene's finished state as a still picture (used for figures in the reading version).
  function staticScene(scene, root) {
    root.innerHTML = `<div class="vp still"><div class="vp-stage">
      <div class="vp-heading"></div><div class="vp-scene"></div></div></div>`;
    const stage = root.querySelector(".vp-stage"), box = root.querySelector(".vp-scene"), head = root.querySelector(".vp-heading");
    head.innerHTML = scene.heading ? rich(scene.heading) : "";
    head.hidden = !scene.heading;
    box.className = "vp-scene t-" + scene.type;
    const make = SCENES[scene.type];
    if (!make) return;
    try {
      const ctl = make(scene, box, { track() {}, stage });
      (scene.beats || []).forEach((_, i) => ctl.beat(i, true, 0));
    } catch (e) { console.error("Figure failed", scene, e); }
  }

  return {
    Player,
    rich,
    tex,
    compile,
    confetti,
    staticScene,
    stopAll() { if (active) active.destroy(); },
    episodeSeconds(ep) {
      let words = 0, beats = 0, holds = 0;
      for (const s of ep.scenes) {
        for (const b of s.beats || []) { words += String(b.say || "").split(/\s+/).filter(Boolean).length; beats++; }
        if (s.type === "pause") holds += s.seconds || 5;
      }
      return Math.round(words / WPS + beats * 0.3 + holds);
    }
  };
})();
