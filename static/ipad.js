/* Landing page: scroll-driven tablet.
 *
 * Phase 1 (approach): a plain-JS port of Aceternity's ContainerScroll. As the section
 * scrolls into view the tablet tilts from rotateX(20deg) to flat, scales 1.05 -> 1
 * (0.92 -> 1 on phones), the title slides up 100px, and the pencil snaps onto the top edge.
 * Phase 2 (pinned): the tablet stays put while a touch circle swipes up the screen,
 * scrolling the real CalcLearners formula sheet in sync.
 */
window.IpadHero = (function () {
  "use strict";
  const section = document.getElementById("ipad-scroll");
  if (!section) return { fill() {} };

  const q = s => section.querySelector(s);
  const sticky = q(".ipad-sticky"), card = q(".ipad-card"), title = q(".ipad-title");
  const screen = q(".ipad-screen"), page = q(".ipad-page"), side = q(".mp-side");
  const viewport = q(".mp-main"), scroller = q(".mp-scroll");
  const ripple = q(".ripple"), pencil = q(".pencil");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");

  const PAGE_W = 1100;          // the mini site is laid out at this width, then scaled to fit
  const SWIPES = 8;             // touch swipes while the tablet is pinned
  const PRESS = 0.7;            // share of each swipe spent dragging (the rest is the pause between)
  const SWIPE_FROM = 540;       // touch circle travels up from here... (SVG's 1000 x 700 coordinates)
  const SWIPE_TO = 300;         // ...to here

  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const smooth = t => t * t * (3 - 2 * t);
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const tex = s => window.VideoPlayer ? VideoPlayer.tex(s) : esc(s);
  const rich = s => window.VideoPlayer ? VideoPlayer.rich(s) : esc(s);

  // Shown until the lessons arrive from the server (or if it isn't running).
  const FALLBACK = [
    { week: 2, unit: "Week 2", unit_title: "Limits", name: "Continuity", formulas: [["Continuity", "\\lim_{x\\to a} f(x) = f(a)"]] },
    { week: 3, unit: "Week 3", unit_title: "Derivatives", name: "Power Rule & Basic Rules", formulas: [
      ["Power rule", "\\frac{d}{dx}x^n = nx^{n-1}"], ["Product rule", "(fg)' = f'g + fg'"]] },
    { week: 5, unit: "Week 5", unit_title: "Chain & Quotient Rules", name: "Chain Rule", formulas: [["Chain rule", "\\frac{d}{dx}f(g(x)) = f'(g(x))\\,g'(x)"]] },
    { week: 8, unit: "Week 8", unit_title: "Antiderivatives & the FTC", name: "Fundamental Theorem of Calculus", formulas: [["FTC part 2", "\\int_a^b f(x)\\,dx = F(b)-F(a)"]] },
    { week: 12, unit: "Week 12", unit_title: "Partial Derivatives & Tangent Planes", name: "Tangent Planes", formulas: [["Tangent plane", "z - z_0 = f_x(x - x_0) + f_y(y - y_0)"]] }
  ];

  let maxScroll = 0, raf = 0, stickyTop = 0;

  function fill(lessons) {
    const list = lessons && lessons.length ? lessons : FALLBACK;
    // Group by course week, like the real site.
    const weeks = [...new Set(list.map(l => l.week))].sort((a, b) => a - b)
      .map(w => [list.find(l => l.week === w), list.filter(l => l.week === w)]);
    const label = l => l.unit === "Extra" ? "Extra topics" : l.unit;
    side.innerHTML = weeks.map(([first, ls]) =>
      `<h4>${esc(label(first))}</h4>` + ls.map(l => `<a>${esc(l.name)}</a>`).join("")).join("");
    scroller.innerHTML = `<h2>Formula sheet</h2><p class="mp-sub">Every key formula from your course, week by week.</p>` +
      weeks.map(([first, ls]) => `<h3>${esc(label(first))}: ${esc(first.unit_title)}</h3>` + ls.map(l => `
        <div class="mp-card"><b>${esc(l.name)}</b>
          ${l.formulas.map(([label, t]) => `<div class="mp-f"><small>${rich(label)}</small>${tex(t)}</div>`).join("")}
        </div>`).join("")).join("");
    fit();
    update();
  }

  // Scale the 1100px-wide mini site to the screen's size.
  function fit() {
    stickyTop = parseFloat(getComputedStyle(sticky).top) || 0; // header height (0 when not pinned)
    const w = screen.clientWidth, h = screen.clientHeight;
    if (!w || !h) return;
    const s = w / PAGE_W;
    page.style.transform = `scale(${s})`;
    page.style.height = h / s + "px";
    maxScroll = Math.max(0, scroller.scrollHeight - viewport.clientHeight);
  }

  function update() {
    raf = 0;
    if (section.offsetParent === null) return; // landing page hidden
    const r = section.getBoundingClientRect();
    const top = stickyTop;
    const still = reduce.matches;

    // Phase 1: section top travels from the bottom of the window up to the header.
    const enter = still ? 1 : clamp((innerHeight - r.top) / (innerHeight - top), 0, 1);
    // Phase 2: how far through the pinned stretch we are.
    const p = still ? 0 : clamp((top - r.top) / Math.max(1, r.height - sticky.clientHeight), 0, 1);

    const [s0, s1] = innerWidth <= 768 ? [0.92, 1] : [1.05, 1];
    card.style.transform = `rotateX(${20 * (1 - enter)}deg) scale(${s0 + (s1 - s0) * enter})`;
    title.style.transform = `translateY(${-100 * enter}px)`;
    pencil.setAttribute("transform", `translate(0 ${-60 * (1 - smooth(enter))})`);
    pencil.style.opacity = 0.2 + 0.8 * enter;

    // Each swipe: drag up while the page scrolls, then a short pause before the next one.
    const t = p * SWIPES;
    const k = Math.min(Math.floor(t), SWIPES - 1);
    const f = p >= 1 ? 1 : t - k;
    const drag = smooth(Math.min(f / PRESS, 1));
    const back = f > PRESS ? (f - PRESS) / (1 - PRESS) : 0;
    scroller.style.transform = `translateY(${-((k + drag) / SWIPES) * maxScroll}px)`;

    // Touch circle: lands low on the screen, glides up with the page, fades out, repeats.
    const pressing = !still && p > 0 && p < 1 && f <= PRESS;
    ripple.setAttribute("cy", (SWIPE_FROM - (SWIPE_FROM - SWIPE_TO) * drag).toFixed(1));
    ripple.setAttribute("r", (30 * (pressing ? 1 : 1 + 0.4 * back)).toFixed(1));
    ripple.style.opacity = pressing ? 0.6 : 0;
  }

  const schedule = () => { if (!raf) raf = requestAnimationFrame(update); };
  addEventListener("scroll", schedule, { passive: true });
  addEventListener("resize", () => { fit(); schedule(); });
  reduce.addEventListener?.("change", schedule);
  if (window.ResizeObserver) new ResizeObserver(() => { fit(); schedule(); }).observe(screen);

  fill(null);
  return { fill };
})();
