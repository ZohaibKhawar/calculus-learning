// ---------- Helpers ----------
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const yt = q => "https://www.youtube.com/results?search_query=" + encodeURIComponent(q);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const V = $("#view");

// localStorage that never throws (private windows can block it).
function store(key, value) {
  try {
    if (value === undefined) return localStorage.getItem(key);
    localStorage.setItem(key, value);
  } catch (e) { return null; }
}

// Your learner ID lives in a secure cookie the server sets. No sign-up is needed; an account
// (see "Account" below) is optional.
// Browsers from before that change kept their ID here; it's sent once so the server
// can move it into the cookie, then forgotten.
let LEGACY_UID = store("uid");

const isJson = res => res.ok && (res.headers.get("content-type") || "").includes("json");

// The site must be served by server.py. If it was opened another way (e.g. VS Code
// Live Server on port 5500) and server.py is running, switch to server.py's address:
// Live Server reloads the page every time server.py saves a file, which breaks
// uploads and saving.
async function useLocalServer() {
  if (!/^(localhost|127\.0\.0\.1)$/.test(location.hostname) || location.port === "5000") return;
  try {
    if (isJson(await fetch("http://localhost:5000/api/lessons"))) {
      location.replace("http://localhost:5000/" + location.hash);
      await new Promise(() => {}); // the browser is navigating away
    }
  } catch (e) { /* server.py isn't running */ }
}

class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

async function api(path, { method = "GET", body } = {}) {
  const opts = { method, credentials: "same-origin", headers: { "X-Requested-With": "CalcLearners" } };
  if (LEGACY_UID) opts.headers["X-User"] = LEGACY_UID;
  if (body instanceof FormData) opts.body = body;
  else if (body !== undefined) {
    opts.body = JSON.stringify(body);
    opts.headers["Content-Type"] = "application/json";
  }
  let res;
  try { res = await fetch("/api" + path, opts); }
  catch (e) { offline(); throw new ApiError("Can't reach the server.", 0); }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(data.error || "Something went wrong. Please try again.", res.status);
  return data;
}

function offline() { $("#banner").hidden = false; }

let toastTimer;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2800);
}

// Render \( inline \) and \[ display \] math with KaTeX.
function math(el) {
  if (window.renderMathInElement && el) {
    renderMathInElement(el, {
      delimiters: [
        { left: "\\[", right: "\\]", display: true },
        { left: "\\(", right: "\\)", display: false }
      ],
      throwOnError: false
    });
  }
}

function timeAgo(ts) {
  const secs = (Date.now() - new Date(ts.replace(" ", "T") + "Z")) / 1000;
  if (secs < 60) return "just now";
  for (const [unit, size] of [["year", 31536000], ["month", 2592000], ["day", 86400], ["hour", 3600], ["minute", 60]]) {
    const n = Math.floor(secs / size);
    if (n >= 1) return `${n} ${unit}${n > 1 ? "s" : ""} ago`;
  }
}

const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

// ---------- State ----------
let LESSONS = [];
let BY_ID = {};
let ME = { name: "", username: null, saved: false, done: [], quiz: {}, notes: [], last_topic: null, streak: 0 };
const isDone = id => ME.done.includes(id);

async function refreshMe() { ME = await api("/me"); }

// ---------- Static data ----------
// Creators: [name, description, search queries]
const CREATORS = [
  ["Professor Leonard", "Full-length lectures for Calc 1-3", ["Professor Leonard Calculus 1", "Professor Leonard Calculus 3"]],
  ["3Blue1Brown", "Visual intuition (Essence of Calculus)", ["3Blue1Brown essence of calculus"]],
  ["The Organic Chemistry Tutor", "Fast worked examples, lots of practice", ["Organic Chemistry Tutor calculus"]],
  ["Dr. Trefor Bazett", "Clear Calc 3 / vector calculus", ["Trefor Bazett multivariable calculus"]],
  ["MIT OpenCourseWare", "University lectures", ["MIT OpenCourseWare single variable calculus"]]
];

// Study styles: [name, description, plan steps]
const STYLES = [
  ["Practice-problem learner", "You learn by doing. Testing yourself is among the best-supported study methods.",
    ["Take the quick quiz first to find out what you already know.",
     "Do the practice problems. Only open a hint after a real attempt.",
     "Re-read the lesson sections that cover what you missed, then retake the quiz."]],
  ["Worked-example learner", "Study solved problems step by step first, then fade the help. Great for beginners.",
    ["Go through the worked example one step at a time. Try to predict each step before you reveal it.",
     "Try the practice problems, using hints as training wheels.",
     "Take the quiz once the practice feels easy."]],
  ["Visual learner", "Graphs, animations and diagrams to build intuition.",
    ["Watch a 3Blue1Brown or Professor Leonard video on the topic (links are in each lesson).",
     "Sketch a picture or graph for the worked example as you go through it.",
     "Do the practice problems and the quiz."]],
  ["Written / notes learner", "Read explanations, rewrite them in your own words, build a formula sheet.",
    ["Read the big idea, then rewrite it in your own words in the lesson's My notes box.",
     "Copy the key formulas onto your own sheet (or print the Formulas page).",
     "Do the practice problems and the quiz."]],
  ["Long-term memory learner", "Spaced repetition: revisit each topic over growing gaps.",
    ["Study the topic today and take the quiz.",
     "Retake the quiz on each review date below. Spacing it out is what makes it stick.",
     "Mark it as understood once you score 100% on a later day."]]
];

const FEEDBACK_QUESTIONS = [
  "If you made this website, what changes would you make?",
  "Which topic was hardest to find help for?",
  "What would make the forum more useful?",
  "Anything else? Privacy questions and requests go here too."
];

// ---------- Weeks ----------
// Lessons are grouped by course week (Week 1-12), then "Extra" topics beyond the syllabus.
function units() {
  const byWeek = new Map();
  for (const l of LESSONS) {
    if (!byWeek.has(l.week)) byWeek.set(l.week, { week: l.week, label: l.unit === "Extra" ? "Extra topics" : l.unit, title: l.unit_title, lessons: [] });
    byWeek.get(l.week).lessons.push(l);
  }
  return [...byWeek.values()].sort((a, b) => a.week - b.week);
}

// "Week 3: Derivatives" or "Extra topic".
const unitLabel = l => l.unit === "Extra" ? "Extra topic" : `${l.unit}: ${l.unit_title}`;

// The 12-week course without the extra topics.
const courseLessons = () => LESSONS.filter(l => l.unit !== "Extra");

// Progress ring in the header: course lessons understood.
function updateProgress() {
  const course = courseLessons();
  const done = course.filter(l => isDone(l.id)).length;
  const C = 2 * Math.PI * 14;
  const arc = $("#progress-arc");
  arc.setAttribute("stroke-dasharray", `${course.length ? (C * done / course.length).toFixed(1) : 0} ${C.toFixed(1)}`);
  arc.style.visibility = done ? "visible" : "hidden"; // a round cap would draw a dot at 0
  $("#progress-text").textContent = course.length ? `${done} / ${course.length}` : "My progress";
  $("#progress-link").setAttribute("aria-label", course.length
    ? `My progress: ${done} of ${course.length} lessons understood` : "My progress");
}

// ---------- Sidebar ----------
function renderSidebar() {
  const filter = $("#q").value.trim().toLowerCase();
  const cur = currentTopicId();
  if (!LESSONS.length) {
    $("#side").innerHTML = "<small>Topics load from the server.</small>";
    return;
  }
  let html = "";
  for (const u of units()) {
    const all = u.lessons;
    const list = all.filter(l => (l.name + " " + l.keywords + " " + l.unit_title).toLowerCase().includes(filter));
    if (!list.length) continue;
    const done = all.filter(l => isDone(l.id)).length;
    html += `<h4>${u.label} <span>${done}/${all.length}</span></h4><div class="unit-sub">${esc(u.title)}</div>` + list.map(l =>
      `<a class="t ${l.id === cur ? "on" : ""} ${isDone(l.id) ? "done" : ""}" href="#/learn/${l.id}"
          ${l.id === cur ? 'aria-current="page"' : ""}>
         <span class="tick" aria-hidden="true">${isDone(l.id) ? "✓" : ""}</span>${esc(l.name)}</a>`
    ).join("");
  }
  $("#side").innerHTML = html ||
    `<small>No topic matches "${esc(filter)}". Try a simpler word like "integral" or "vector".</small>`;
}

$("#q").addEventListener("input", renderSidebar);
$("#q").addEventListener("keydown", e => {
  if (e.key === "Enter") {
    const first = $("#side a.t");
    if (first) location.hash = first.getAttribute("href");
  }
});

// Topic search: the big box on the home page, or the topics list everywhere else.
function openSearch() {
  if (!$("#landing").hidden) {
    $("#find").focus();
    $("#find").scrollIntoView({ block: "center" });
    return;
  }
  openTopics(true);
}

// Press "/" anywhere to jump to topic search.
document.addEventListener("keydown", e => {
  if (e.key !== "/" || /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) return;
  e.preventDefault();
  openSearch();
});
$("#search-btn").addEventListener("click", openSearch);

// ---------- Phone layout: menu and topics drawer ----------
const isPhone = () => matchMedia("(max-width: 860px)").matches;
const menuBtn = $("#menu-btn"), nav = $("#nav");

function setMenu(open) {
  nav.classList.toggle("open", open);
  menuBtn.setAttribute("aria-expanded", open);
  menuBtn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  document.body.classList.toggle("menu-open", open);
}
menuBtn.addEventListener("click", () => setMenu(!nav.classList.contains("open")));
document.addEventListener("click", e => {
  if (nav.classList.contains("open") && !e.target.closest("#nav, #menu-btn")) setMenu(false);
});

// Wide screens: a button folds the topics list down to a narrow strip, and the choice is remembered.
const sideToggle = $("#side-toggle");
const sideOpen = () => document.documentElement.dataset.side !== "closed";
function setSide(open) {
  document.documentElement.dataset.side = open ? "open" : "closed";
  sideToggle.setAttribute("aria-expanded", open);
  sideToggle.setAttribute("aria-label", open ? "Hide topics" : "Show topics");
  sideToggle.title = open ? "Hide topics" : "Show topics";
}
setSide(sideOpen());

// Folding and unfolding: style.css slides the list, and this smears it sideways like motion
// blur, strongest while it moves fastest and gone when it comes to rest.
const FOLD_MS = 360;  // the same as --fold in style.css
const foldBlur = $("#fold-blur feGaussianBlur");
let foldFrame = 0;
function foldSide(open) {
  if (open === sideOpen()) return;
  setSide(open);
  const moving = [$("#side"), $("#q")];
  const blur = on => moving.forEach(el => (el.style.filter = on ? "url(#fold-blur)" : ""));
  cancelAnimationFrame(foldFrame);
  blur(false);
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const start = performance.now();
  const frame = now => {
    const t = Math.min(1, (now - start) / FOLD_MS);
    foldBlur.setAttribute("stdDeviation", `${(18 * Math.sin(Math.PI * t ** 0.6)).toFixed(1)} 0`);
    if (t < 1) foldFrame = requestAnimationFrame(frame);
    else blur(false);
  };
  blur(true);
  frame(start);
}
sideToggle.addEventListener("click", () => {
  foldSide(!sideOpen());
  store("topics", sideOpen() ? "open" : "closed");
});

const topicsBtn = $("#topics-btn");
function openTopics(focusSearch) {
  if (!isPhone()) { foldSide(true); $("#q").focus(); return; }
  document.body.classList.add("topics-open");
  $("#scrim").hidden = false;
  topicsBtn.setAttribute("aria-expanded", "true");
  $("#side a.t.on")?.scrollIntoView({ block: "center" });
  // Wait for the drawer to become visible before moving focus into it.
  requestAnimationFrame(() => (focusSearch ? $("#q") : $("#topics-close")).focus());
}
function closeTopics(restoreFocus) {
  if (!document.body.classList.contains("topics-open")) return;
  document.body.classList.remove("topics-open");
  $("#scrim").hidden = true;
  topicsBtn.setAttribute("aria-expanded", "false");
  if (restoreFocus) topicsBtn.focus();
}
topicsBtn.addEventListener("click", () => openTopics(false));
$("#topics-close").addEventListener("click", () => closeTopics(true));
$("#scrim").addEventListener("click", () => closeTopics(true));

document.addEventListener("keydown", e => {
  if (e.key !== "Escape") return;
  if (nav.classList.contains("open")) { setMenu(false); menuBtn.focus(); }
  closeTopics(true);
});
// Leaving phone width (rotating a tablet, resizing a window) closes both panels.
matchMedia("(max-width: 860px)").addEventListener?.("change", () => { setMenu(false); closeTopics(false); });

// ---------- Routing (#/view/arg?params) ----------
function parseHash() {
  const [path, qs] = location.hash.replace(/^#\/?/, "").split("?");
  const [view = "", arg = ""] = path.split("/");
  return { view, arg: decodeURIComponent(arg), params: new URLSearchParams(qs || "") };
}

function currentTopicId() {
  const h = parseHash();
  return h.view === "learn" ? h.arg : null;
}

document.addEventListener("click", e => {
  const el = e.target.closest("[data-v]");
  if (!el) return;
  const target = "#/" + el.dataset.v;
  if (location.hash === target) route(); else location.hash = target;
});

window.addEventListener("hashchange", route);

async function route() {
  const { view, arg, params } = parseHash();
  const home = !view || view === "home";
  if (view !== "account") guestReturn = location.hash || "#/";
  window.VideoPlayer?.stopAll();
  clearTimeout(pollTimer);
  $("#landing").hidden = !home;
  $("#app").hidden = home;
  setMenu(false);
  closeTopics(false);
  const navView = view === "watch" ? "videos" : view;
  $$("[data-nav]").forEach(a => {
    if (a.dataset.nav === navView) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  window.scrollTo(0, 0);
  if (home) {
    renderLanding();
    return;
  }
  renderSidebar();
  const views = { learn, practice: practicePage, dashboard, formulas, forum, upload, feedback, videos: videosView, watch, admin, account };
  await (views[view] || learn)(arg, params);
  math(V);
  // A quick fade shows the page changed (skipped when motion is turned off).
  if (window.anime && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    anime({ targets: "#view", opacity: [0, 1], duration: 220, easing: "easeOutQuad" });
  }
}

function serverMissing() {
  V.innerHTML = `<h2>Almost there</h2>
    <div class="card">
      <p>This page needs the CalcLearners server for lessons, quizzes and saving progress.</p>
      <ol>
        <li>Open a terminal in the <code>calculus website</code> folder.</li>
        <li>Run <code>pip install -r requirements.txt</code> (first time only).</li>
        <li>Run <code>python server.py</code> and leave that terminal open.</li>
        <li>Refresh this page (or open <a href="http://localhost:5000">http://localhost:5000</a>).</li>
      </ol>
    </div>`;
}

function topicOptions(selected, emptyLabel) {
  return `<option value="">${emptyLabel}</option>` + units().map(u =>
    `<optgroup label="${esc(u.label)}: ${esc(u.title)}">` + u.lessons.map(l =>
      `<option value="${l.id}" ${l.id === selected ? "selected" : ""}>${esc(l.name)}</option>`
    ).join("") + `</optgroup>`
  ).join("");
}

// First topic not yet understood whose prerequisites are all done.
function recommendNext() {
  const open = LESSONS.filter(l => !isDone(l.id));
  return open.find(l => l.prereqs.every(isDone)) || open[0] || null;
}

function badge(level) {
  return `<span class="badge lvl-${level.toLowerCase()}">${level}</span>`;
}

// ---------- Learn ----------
async function learn(id) {
  if (!LESSONS.length) return serverMissing();
  const l = BY_ID[id];
  if (!l) return topicPicker();

  api("/visit", { method: "POST", body: { topic: id } }).then(() => (ME.last_topic = id)).catch(() => {});
  const idx = LESSONS.indexOf(l);
  const prev = LESSONS[idx - 1], next = LESSONS[idx + 1];
  const best = ME.quiz[id]?.best;

  const sections = [
    ["s-idea", "Big idea"], ["s-formulas", "Formulas"], ["s-example", "Example"],
    ["s-mistakes", "Mistakes"], ["s-practice", "Practice"], ["s-quiz", "Quiz"],
    ["s-videos", "Videos"], ["s-notes", "Notes"]
  ];

  V.innerHTML = `
    <div class="crumbs"><span>${esc(unitLabel(l))}</span>${badge(l.level)}<span>About ${l.minutes} min</span></div>
    <h2>${esc(l.name)}</h2>
    <div class="row lesson-actions">
      <button id="done-btn"></button>
      <button class="ghost" data-v="forum?topic=${l.id}">Ask a question about this</button>
    </div>

    ${l.prereqs.length ? `<div class="card prereq">
      <b>Before you start:</b> this lesson builds on
      <div class="chips">${l.prereqs.map(p => `<a class="chip ${isDone(p) ? "done" : ""}" href="#/learn/${p}">${isDone(p) ? "✓ " : ""}${esc(BY_ID[p].name)}</a>`).join(" ")}</div>
      <p class="muted prereq-note">${l.prereqs.every(isDone) ? "You've covered these, nice." : "Shaky on any of them? Review those first. It makes this topic much easier."}</p>
    </div>` : ""}

    <nav class="jump" aria-label="Lesson sections">
      ${sections.map(([s, name], i) => `<button data-jump="${s}"><span>${i + 1}</span>${name}</button>`).join("")}
    </nav>

    <section id="s-idea" class="card">
      <h3>1. The big idea</h3>
      <p>${l.idea}</p>
    </section>

    <section id="s-formulas" class="card">
      <h3>2. Key formulas</h3>
      ${l.formulas.map(([label, tex]) => `<div class="formula"><small>${label}</small>\\[${tex}\\]</div>`).join("")}
    </section>

    <section id="s-example" class="card">
      <h3>3. Worked example</h3>
      <p class="problem">${l.example.problem}</p>
      <ol class="steps">${l.example.steps.map(s => `<li hidden>${s}</li>`).join("")}</ol>
      <p class="answer" hidden><b>Answer:</b> ${l.example.answer}</p>
      <div class="row">
        <button id="next-step">Show step 1 of ${l.example.steps.length}</button>
        <button class="ghost" id="all-steps">Show everything</button>
      </div>
      <small>Tip: try to predict each step before you reveal it. That's where the learning happens.</small>
    </section>

    <section id="s-mistakes" class="card">
      <h3>4. Common mistakes</h3>
      <ul class="mistakes">${l.mistakes.map(m => `<li>${m}</li>`).join("")}</ul>
    </section>

    <section id="s-practice" class="card">
      <h3>5. Practice problems</h3>
      <p class="muted">Give each one an honest try on paper first.</p>
      ${l.practice.map((p, i) => `
        <div class="prob">
          <p><b>${i + 1}.</b> ${p.q}</p>
          <div class="row">
            <button class="ghost small" data-toggle="hint">💡 Hint</button>
            <button class="ghost small" data-toggle="ans">Show answer</button>
          </div>
          <div class="box hint" hidden>${p.hint}</div>
          <div class="box ans" hidden>${p.a}</div>
        </div>`).join("")}
      ${l.unit === "Extra" ? "" : `<p class="more-practice"><a href="#/practice/${l.week}">More ${esc(l.unit)} practice, with worked solutions</a></p>`}
    </section>

    <section id="s-quiz" class="card">
      <h3>6. Quick quiz</h3>
      <p class="muted">${best === undefined ? "Check yourself. You get instant feedback on every answer."
        : `Your best score so far: <b>${best}%</b>. Try to beat it!`}</p>
      <div id="quiz"></div>
    </section>

    <section id="s-videos" class="card">
      <h3>7. Watch it explained</h3>
      <p class="muted">YouTube searches for this exact topic from trusted teachers:</p>
      <ul class="videos">${CREATORS.map(c =>
        `<li><a target="_blank" rel="noopener" href="${yt(c[0] + " " + l.name)}">${c[0]}</a> <small>${c[1]}</small></li>`
      ).join("")}</ul>
    </section>

    <section id="s-notes" class="card">
      <h3>8. My notes</h3>
      <textarea id="note" rows="5" placeholder="Explain this topic in your own words, or jot down what confused you. Saves automatically."></textarea>
      <small id="note-status"></small>
    </section>

    <div class="pager">
      ${prev ? `<a class="prev" href="#/learn/${prev.id}"><small>Previous lesson</small>${esc(prev.name)}</a>` : ""}
      ${next ? `<a class="next" href="#/learn/${next.id}"><small>Next lesson</small>${esc(next.name)}</a>`
        : `<a class="next" href="#/dashboard"><small>You reached the end</small>See my progress</a>`}
    </div>`;

  // Mark as understood
  const doneBtn = $("#done-btn");
  const paintDone = () => {
    doneBtn.textContent = isDone(id) ? "✓ Understood" : "Mark as understood";
    doneBtn.classList.toggle("ghost", !isDone(id));
    doneBtn.setAttribute("aria-pressed", isDone(id));
  };
  paintDone();
  doneBtn.onclick = async () => {
    try {
      await setDone(id, !isDone(id));
      paintDone();
      if (isDone(id)) {
        const n = recommendNext();
        toast(n ? `Nice! Up next: ${n.name}` : "You've finished every topic! 🎉");
      }
    } catch (e) { toast(e.message); }
  };

  // Section jump buttons
  V.querySelector(".jump").onclick = e => {
    const b = e.target.closest("[data-jump]");
    if (b) document.getElementById(b.dataset.jump).scrollIntoView({ behavior: "smooth" });
  };

  // Worked example, one step at a time
  const steps = $$("#s-example .steps li");
  const nextBtn = $("#next-step"), allBtn = $("#all-steps");
  let shown = 0;
  const showUpTo = n => {
    while (shown < n) steps[shown++].hidden = false;
    if (shown >= steps.length) {
      $("#s-example .answer").hidden = false;
      nextBtn.hidden = allBtn.hidden = true;
    } else {
      nextBtn.textContent = `Show step ${shown + 1} of ${steps.length}`;
    }
  };
  nextBtn.onclick = () => showUpTo(shown + 1);
  allBtn.onclick = () => showUpTo(steps.length);

  // Practice hints / answers
  $("#s-practice").onclick = e => {
    const b = e.target.closest("[data-toggle]");
    if (!b) return;
    const box = b.closest(".prob").querySelector(".box." + b.dataset.toggle);
    box.hidden = !box.hidden;
    if (b.dataset.toggle === "ans") b.textContent = box.hidden ? "Show answer" : "Hide answer";
  };

  renderQuiz(l);

  // Notes (autosave)
  const note = $("#note"), status = $("#note-status");
  api("/notes/" + id).then(n => { note.value = n.body; }).catch(() => {});
  note.oninput = debounce(async () => {
    status.textContent = "Saving…";
    try {
      await api("/notes/" + id, { method: "PUT", body: { body: note.value } });
      status.textContent = "Saved ✓";
    } catch (e) { status.textContent = e.message; }
  }, 700);
}

async function setDone(id, done) {
  await api("/progress", { method: "POST", body: { topic: id, done } });
  ME.done = done ? [...new Set([...ME.done, id])] : ME.done.filter(t => t !== id);
  renderSidebar();
  updateProgress();
}

function renderQuiz(l) {
  const box = $("#quiz");
  let answered = 0, correct = 0;
  box.innerHTML = l.quiz.map((q, i) => `
    <div class="qq" data-i="${i}">
      <p><b>${i + 1}.</b> ${q.q}</p>
      <div class="choices">${q.choices.map((c, j) => `<button class="choice" data-j="${j}">${c}</button>`).join("")}</div>
      <p class="why" hidden></p>
    </div>`).join("") + `<div id="quiz-result"></div>`;

  box.onclick = async e => {
    const btn = e.target.closest(".choice");
    if (!btn) return;
    const qq = btn.closest(".qq");
    if (qq.dataset.answered) return;
    qq.dataset.answered = "1";
    const q = l.quiz[qq.dataset.i];
    const right = +btn.dataset.j === q.answer;
    answered++;
    if (right) correct++;
    qq.querySelectorAll(".choice").forEach((b, k) => {
      b.disabled = true;
      if (k === q.answer) b.classList.add("right");
    });
    if (!right) btn.classList.add("wrong");
    const why = qq.querySelector(".why");
    why.hidden = false;
    why.innerHTML = `<b class="${right ? "ok" : "bad"}">${right ? "Correct!" : "Not quite."}</b> ${q.why}`;
    math(why);
    if (answered === l.quiz.length) finishQuiz(l, correct);
  };
}

async function finishQuiz(l, correct) {
  const total = l.quiz.length;
  const pct = Math.round(100 * correct / total);
  const msg = pct === 100 ? "Perfect score! You've really got this."
    : pct >= 70 ? "Nice work! Look over the explanations for the ones you missed."
    : "Good effort. Go back through the worked example and practice problems, then try again. You'll get there.";
  const res = $("#quiz-result");
  res.innerHTML = `
    <div class="result ${pct >= 70 ? "good" : ""}">
      <div class="score">${correct}/${total}</div>
      <div><b>${pct}%</b> · ${msg}</div>
    </div>
    <div class="row">
      <button class="ghost" id="retry">Retry quiz</button>
      ${pct === 100 && !isDone(l.id) ? `<button id="quiz-done">Mark as understood</button>` : ""}
    </div>`;
  $("#retry").onclick = () => { renderQuiz(l); math($("#quiz")); };
  const qd = $("#quiz-done");
  if (qd) qd.onclick = async () => {
    await setDone(l.id, true);
    $("#done-btn").textContent = "✓ Understood";
    $("#done-btn").classList.remove("ghost");
    qd.remove();
    toast("Marked as understood ✓");
  };
  try {
    await api("/quiz", { method: "POST", body: { topic: l.id, score: correct, total } });
    const q = ME.quiz[l.id] || { best: 0, attempts: 0 };
    ME.quiz[l.id] = { best: Math.max(q.best, pct), last: pct, attempts: q.attempts + 1 };
  } catch (e) { toast("Couldn't save your score: " + e.message); }
}

function topicPicker() {
  const next = recommendNext();
  V.innerHTML = `
    <h2>Pick a topic</h2>
    <p>No need to start at the beginning. Jump straight to whatever you're stuck on, using the list or the search box (press <kbd>/</kbd>).</p>
    ${next ? `<div class="card hl">
      <b>Not sure where to start?</b> We suggest <a href="#/learn/${next.id}">${esc(next.name)}</a>
      <small>(${esc(unitLabel(next))}, ${next.prereqs.length ? "you've done its prerequisites" : "no prerequisites needed"})</small>
    </div>` : ""}
    ${units().map(u => `
      <h3>${esc(u.label)} <small class="muted">${esc(u.title)}</small></h3>
      <div class="topic-grid">${u.lessons.map(l => {
        const q = ME.quiz[l.id];
        return `<a class="topic ${isDone(l.id) ? "done" : ""}" href="#/learn/${l.id}">
          <b>${isDone(l.id) ? "✓ " : ""}${esc(l.name)}</b>
          <span>${badge(l.level)} ${l.minutes} min${q ? ` · quiz best ${q.best}%` : ""}</span>
        </a>`;
      }).join("")}</div>`).join("")}`;
}

// ---------- Dashboard ----------
async function dashboard() {
  if (!LESSONS.length) return serverMissing();
  try { await refreshMe(); updateProgress(); } catch (e) { /* show what we have */ }
  const course = courseLessons();
  const total = course.length;
  const quizTopics = Object.keys(ME.quiz).filter(t => BY_ID[t]);
  const avg = quizTopics.length
    ? Math.round(quizTopics.reduce((s, t) => s + ME.quiz[t].best, 0) / quizTopics.length) : null;
  const last = BY_ID[ME.last_topic];
  const next = recommendNext();
  const review = quizTopics.filter(t => ME.quiz[t].best < 70);
  const hour = new Date().getHours();
  const hello = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  V.innerHTML = `
    <h2>${hello}, ${esc(ME.name || "learner")} 👋</h2>
    <div class="tiles">
      <div class="tile"><b>${course.filter(l => isDone(l.id)).length}<small>/${total}</small></b><span>course topics understood</span></div>
      <div class="tile"><b>${ME.streak}${ME.streak ? " 🔥" : ""}</b><span>day streak</span></div>
      <div class="tile"><b>${quizTopics.length}</b><span>${quizTopics.length === 1 ? "quiz" : "quizzes"} taken</span></div>
      <div class="tile"><b>${avg === null ? "–" : avg + "%"}</b><span>average best score</span></div>
    </div>

    <div class="two">
      ${last ? `<div class="card">
        <small>Continue where you left off</small>
        <h3>${esc(last.name)}</h3>
        <button data-v="learn/${last.id}">Resume lesson</button>
      </div>` : ""}
      ${next ? `<div class="card">
        <small>Recommended next</small>
        <h3>${esc(next.name)}</h3>
        <p class="muted">${next.prereqs.length ? "You've done everything it builds on." : "A great place to start, with no prerequisites."}</p>
        <button class="${last ? "ghost" : ""}" data-v="learn/${next.id}">Start lesson</button>
      </div>` : `<div class="card"><h3>You've finished every topic! 🎉</h3><p>Keep it fresh by retaking quizzes now and then.</p></div>`}
    </div>

    <h3>Your weeks</h3>
    ${units().map(u => {
      const all = u.lessons;
      const done = all.filter(l => isDone(l.id)).length;
      return `<div class="card course">
        <div class="row between"><b>${esc(u.label)} <small class="muted">${esc(u.title)}</small></b><small>${done}/${all.length} understood</small></div>
        <div class="bar" role="progressbar" aria-valuenow="${done}" aria-valuemax="${all.length}" aria-label="${esc(u.label)} progress">
          <i style="width:${100 * done / all.length}%"></i></div>
        <div class="chips">${all.map(l => {
          const q = ME.quiz[l.id];
          return `<a class="chip ${isDone(l.id) ? "done" : q && q.best < 70 ? "weak" : ""}" href="#/learn/${l.id}">
            ${isDone(l.id) ? "✓ " : ""}${esc(l.name)}${q ? ` · ${q.best}%` : ""}</a>`;
        }).join("")}</div>
      </div>`;
    }).join("")}

    ${review.length ? `<h3>Worth another look</h3>
      <div class="card"><p class="muted">Your best quiz score on these is under 70%. A quick review will help.</p>
      <div class="chips">${review.map(t => `<a class="chip weak" href="#/learn/${t}">${esc(BY_ID[t].name)} · ${ME.quiz[t].best}%</a>`).join("")}</div></div>` : ""}

    <h3>Your data</h3>
    <div class="card">
      ${nameRow()}
      ${ME.username ? `
      <p><b>Signed in as ${esc(ME.username)}.</b> Your progress is saved to your account, so it's there on any
        phone or computer where you sign in.</p>
      <div class="row">
        <a class="btn ghost small" href="#/account">Open my profile</a>
        <button class="ghost small" data-sign-out>Sign out</button>
      </div>
      <p><small>An account that isn't used for 12 months is deleted, along with what is saved in it.</small></p>` : `
      <p><b>You're using CalcLearners as a guest.</b> Your progress is saved on the server and linked to this browser by a
        cookie, so clearing your cookies or switching browsers starts you fresh. An account lets you open it
        on another phone or computer.</p>
      <div class="row">
        <a class="btn small" href="#/account?new=1">Create an account</a>
        <a class="btn ghost small" href="#/account">Sign in</a>
      </div>
      <p><small>What is saved for a browser that hasn't visited for 12 months is deleted.</small></p>`}
      <div class="row account-actions">
        <button class="ghost small" id="reset">Reset my progress</button>
        ${ME.username ? "" : deleteControls().button}
      </div>
      ${ME.username ? "" : deleteControls().form}
    </div>`;

  wireName(() => dashboard().then(() => math(V)));
  $("#reset").onclick = async () => {
    if (!confirm("Reset all your progress, quiz scores and notes? This can't be undone.")) return;
    await api("/reset", { method: "POST" });
    await refreshMe();
    renderSidebar();
    updateProgress();
    dashboard();
    toast("Progress reset");
  };
  if (!ME.username) wireDelete();
}

// The display name box, on My progress and on the profile page.
function nameRow() {
  return `<label for="name">Display name <small>(shown on your forum posts)</small></label>
      <div class="row"><input id="name" value="${esc(ME.name)}" maxlength="40" placeholder="Anonymous learner">
        <button id="save-name">Save name</button></div>`;
}

function wireName(redraw) {
  $("#save-name").onclick = async () => {
    try {
      const r = await api("/me", { method: "POST", body: { name: $("#name").value } });
      ME.name = r.name;
      toast("Name saved");
      redraw();
    } catch (e) { toast(e.message); }
  };
}

// Deleting can't be undone, so the form says what goes and asks for the account's password, or
// for a typed word when there is no account. A browser on its own gets these on My progress;
// an account gets them on its profile page.
function deleteControls() {
  const acct = !!ME.username;
  return {
    button: `<button class="ghost small danger" id="delete-data" aria-expanded="false" aria-controls="delete-form">${acct ? "Delete my account" : "Delete my data"}</button>`,
    form: `<form id="delete-form" class="delete-data" hidden novalidate>
        <p><b>${acct ? "Delete your account and everything saved in it?" : "Delete everything saved for this browser?"}</b>
          Your progress, quiz scores, notes, uploads and the lessons made from them, feedback, votes and forum
          posts are removed, along with the answers under your questions. This can't be undone.</p>
        <div class="field">
          ${acct ? `<label for="delete-confirm">Enter your password to prove it's you</label>
          <input id="delete-confirm" type="password" autocomplete="current-password" required>`
          : `<label for="delete-confirm">Type DELETE to confirm</label>
          <input id="delete-confirm" autocomplete="off" autocapitalize="characters" spellcheck="false" required>`}
        </div>
        <p class="form-error" role="alert"></p>
        <div class="row">
          <button type="submit" class="danger">${acct ? "Delete my account" : "Delete my data"}</button>
          <button type="button" class="ghost" id="delete-cancel">${acct ? "Keep my account" : "Keep my data"}</button>
        </div>
      </form>`
  };
}

function wireDelete() {
  const form = $("#delete-form"), error = form.querySelector(".form-error");
  const show = open => {
    form.hidden = !open;
    form.reset();
    error.textContent = "";
    $("#delete-data").setAttribute("aria-expanded", open);
    (open ? $("#delete-confirm") : $("#delete-data")).focus();
  };
  $("#delete-data").onclick = () => show(form.hidden);
  $("#delete-cancel").onclick = () => show(false);
  form.oninput = () => { error.textContent = ""; };
  form.onsubmit = async e => {
    e.preventDefault();
    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    try {
      const typed = $("#delete-confirm").value;
      await api("/me/delete", { method: "POST", body: ME.username ? { password: typed } : { confirm: typed } });
    } catch (err) {
      error.textContent = err.message;
      btn.disabled = false;
      return;
    }
    // Nothing of the old data stays on the page: start over as a new visitor.
    location.hash = "#/";
    location.reload();
  };
}

// ---------- Account (#/account): optional sign-in, and the profile page once signed in ----------
const USERNAME_OK = /^[a-z0-9_]{3,20}$/i;
// Where "Continue as guest" goes: the page you were on before the sign-in page, or the course
// if you came straight to it.
let guestReturn = "#/learn";
// Under the sign-in and sign-up buttons. Nobody needs an account, so there is always a way on.
const guestOption = () => `<div class="guest-option">
    <span class="or">or</span>
    <a class="btn ghost" href="${esc(guestReturn)}">Continue as guest</a>
    <small>No account needed. Your progress saves in this browser.</small>
  </div>`;
const PLAIN_TEXT = 'autocapitalize="none" autocorrect="off" spellcheck="false"';

// The account links in the header and the phone menu: "Sign in", or "Profile" once you have.
function updateAccountLinks() {
  $$(".account-entry").forEach(a => { a.textContent = ME.username ? "Profile" : "Sign in"; });
}

// Signing in or out changes whose progress every part of the page shows, so the page starts
// over. The message is shown once it has.
function restart(hash, message) {
  try { sessionStorage.setItem("flash", message); } catch (e) { /* private window */ }
  location.hash = hash;
  location.reload();
}

async function signOut(everywhere) {
  try { await api("/auth/logout", { method: "POST", body: { everywhere } }); }
  catch (e) { toast(e.message); return; }
  restart("#/account", everywhere ? "Signed out of every browser" : "Signed out");
}
document.addEventListener("click", e => {
  const b = e.target.closest("[data-sign-out]");
  if (b) signOut(b.dataset.signOut === "all");
});

// A form field: a visible label, the input, and one line under it that shows the hint or,
// after a mistake, what to fix.
function field(id, label, attrs, hint = "") {
  return `<div class="field">
    <label for="${id}">${label}</label>
    <input id="${id}" ${attrs} aria-describedby="${id}-msg">
    <small class="hint" id="${id}-msg" aria-live="polite" data-hint="${esc(hint)}">${esc(hint)}</small>
  </div>`;
}
const SHOW_PASSWORD = `<label class="check"><input type="checkbox" data-show-passwords> Show password</label>`;

// A field is checked when you leave it or send the form, never while you type, and one that
// shows a problem goes back to its hint at the next keystroke. The button always works: with
// something missing it takes you to the first field to fix.
function wireForm(form, rules, send) {
  const inputs = [...form.querySelectorAll("input[name]")];
  const error = form.querySelector(".form-error");
  const btn = form.querySelector("button[type=submit]");
  const problem = input => (rules[input.name] ? rules[input.name](input.value) : "");
  const mark = (input, text) => {
    const msg = document.getElementById(input.id + "-msg");
    input.closest(".field").classList.toggle("invalid", !!text);
    if (text) input.setAttribute("aria-invalid", "true"); else input.removeAttribute("aria-invalid");
    msg.textContent = text || msg.dataset.hint;
  };
  for (const input of inputs) {
    input.addEventListener("blur", () => mark(input, problem(input)));
    input.addEventListener("input", () => { mark(input, ""); error.textContent = ""; });
  }
  form.addEventListener("change", e => {
    if (!e.target.matches("[data-show-passwords]")) return;
    form.querySelectorAll("[data-pw]").forEach(i => { i.type = e.target.checked ? "text" : "password"; });
  });
  form.addEventListener("submit", async e => {
    e.preventDefault();
    if (btn.getAttribute("aria-busy")) return;  // already sending
    error.textContent = "";
    for (const input of inputs) mark(input, problem(input));
    const first = inputs.find(i => i.getAttribute("aria-invalid"));
    if (first) { first.focus(); return; }
    const label = btn.textContent;
    btn.setAttribute("aria-busy", "true");
    btn.textContent = "One moment…";
    try {
      await send(Object.fromEntries(inputs.map(i => [i.name, i.value])));
    } catch (err) {
      // A taken username is that field's problem; anything else goes above the button.
      const name = err.status === 409 && form.elements.username;
      if (name) { mark(name, err.message); name.focus(); } else error.textContent = err.message;
    }
    btn.removeAttribute("aria-busy");
    btn.textContent = label;
  });
  // Phones: don't throw the keyboard over the page before the person has read it.
  if (!isPhone() && form.dataset.focus !== undefined) inputs[0].focus();
}

// Everything already on the page that depends on who is signed in.
async function refreshAll() {
  try { await refreshMe(); } catch (e) { /* show what we have */ }
  renderSidebar();
  updateProgress();
  updateAccountLinks();
}

async function account(_, params) {
  try { await refreshMe(); } catch (e) { /* show what we have */ }
  updateAccountLinks();
  if (ME.username) return profile();
  if (params.get("new") === "1") return signUpView();
  if (params.get("reset") === "1") return resetView();
  signInView();
}

const USERNAME_RULE = v => !v.trim() ? "Choose a username." : USERNAME_OK.test(v.trim()) ? ""
  : "Use 3 to 20 letters, numbers or _ (no spaces).";
const NEW_PASSWORD_RULE = v => !v ? "Choose a password." : v.length < 8 ? "Use at least 8 characters." : "";

function signUpView() {
  V.innerHTML = `
    <h2>Create an account</h2>
    <p>An account is optional. It puts what this browser has saved (your progress, quiz scores, notes and
      forum posts) under a username and password, so you can open it on another phone or computer.</p>
    <form class="card account-form" id="account-form" novalidate data-focus>
      ${field("a-user", "Username", `name="username" autocomplete="username" maxlength="20" ${PLAIN_TEXT} required`,
        "3 to 20 letters, numbers or _. It isn't shown to anyone on the site, and it's safer not to use your real name.")}
      ${field("a-pass", "Password", 'name="password" type="password" autocomplete="new-password" maxlength="200" data-pw required',
        "At least 8 characters.")}
      ${SHOW_PASSWORD}
      <p class="form-error" role="alert"></p>
      <button type="submit">Create account</button>
      ${guestOption()}
    </form>
    <p class="account-switch">Already have an account? <a href="#/account">Sign in</a></p>
    <p><small>We store your username and a scrambled copy of your password, never the password itself. Next
      you'll get a recovery code to save, in case you forget the password. An account that isn't used for
      12 months is deleted. <a href="privacy.html">Privacy Policy</a></small></p>`;
  wireForm($("#account-form"), { username: USERNAME_RULE, password: NEW_PASSWORD_RULE }, async data => {
    const r = await api("/auth/signup", { method: "POST", body: data });
    await refreshAll();
    recoveryView(r.recovery, `Your account <b>${esc(r.username)}</b> is ready, and you're signed in.`,
      () => restart("#/dashboard", `You're signed in as ${r.username}.`));
  });
}

function signInView() {
  V.innerHTML = `
    <h2>Sign in</h2>
    <p>Pick up your progress, quiz scores and notes on this browser.</p>
    <form class="card account-form" id="account-form" novalidate data-focus>
      ${field("a-user", "Username", `name="username" autocomplete="username" maxlength="20" ${PLAIN_TEXT} required`)}
      ${field("a-pass", "Password", 'name="password" type="password" autocomplete="current-password" maxlength="200" data-pw required')}
      ${SHOW_PASSWORD}
      ${ME.saved ? `<label class="check"><input type="checkbox" id="a-merge" checked> Add what this browser has saved to my account</label>
      <small class="hint">Its progress, quiz scores, notes and posts move into your account. On a shared
        computer, untick this: they then stay here for whoever uses it after you sign out.</small>` : ""}
      <p class="form-error" role="alert"></p>
      <button type="submit">Sign in</button>
      ${guestOption()}
    </form>
    <p class="account-switch"><a href="#/account?reset=1">Forgot your password?</a></p>
    <p class="account-switch">New here? <a href="#/account?new=1">Create an account</a></p>`;
  wireForm($("#account-form"), {
    username: v => v.trim() ? "" : "Enter your username.",
    password: v => v ? "" : "Enter your password."
  }, async data => {
    const r = await api("/auth/login", { method: "POST", body: { ...data, merge: !!$("#a-merge")?.checked } });
    restart("#/dashboard", r.merged ? `Signed in as ${r.username}. What this browser had saved is now in your account.`
      : `Signed in as ${r.username}`);
  });
}

// For someone who forgot their password. The recovery code stands in for it, once.
function resetView() {
  V.innerHTML = `
    <h2>Reset your password</h2>
    <p>Enter your username and the recovery code you saved when you created your account, then choose a new
      password.</p>
    <form class="card account-form" id="account-form" novalidate data-focus>
      ${field("a-user", "Username", `name="username" autocomplete="username" maxlength="20" ${PLAIN_TEXT} required`)}
      ${field("a-code", "Recovery code", 'name="code" autocomplete="off" autocapitalize="characters" autocorrect="off" spellcheck="false" maxlength="40" required',
        "20 letters and numbers, like ABCDE-FGHJK-MNPQR-STUVW.")}
      ${field("a-pass", "New password", 'name="password" type="password" autocomplete="new-password" maxlength="200" data-pw required',
        "At least 8 characters.")}
      ${SHOW_PASSWORD}
      <p class="form-error" role="alert"></p>
      <button type="submit">Reset password</button>
    </form>
    <p class="account-switch"><a href="#/account">Back to sign in</a></p>
    <p><small>No recovery code? Without it we have no way to check that the account is yours, so its password
      can't be reset. You can <a href="#/account?new=1">create a new account</a>.</small></p>`;
  wireForm($("#account-form"), {
    username: v => v.trim() ? "" : "Enter your username.",
    code: v => {
      const n = v.replace(/[^a-z0-9]/gi, "").length;
      return !n ? "Enter your recovery code." : n !== 20 ? "Enter all 20 letters and numbers of the code." : "";
    },
    password: NEW_PASSWORD_RULE
  }, async data => {
    const r = await api("/auth/reset", { method: "POST", body: data });
    await refreshAll();
    recoveryView(r.recovery, `Your password is changed, and you're signed in as <b>${esc(r.username)}</b>.
      Your old recovery code no longer works, so here is a new one.`,
      () => restart("#/dashboard", `Password reset. You're signed in as ${r.username}.`));
  });
}

// A recovery code is shown once, here, and is never stored in the browser. `done` runs after
// the person says they have saved it.
function recoveryView(code, intro, done) {
  V.innerHTML = `
    <h2>Save your recovery code</h2>
    <div class="card account-form">
      <p>${intro}</p>
      <p>If you ever forget your password, this code is the only way to reset it. We don't keep an email
        address for you, and we can't show the code again.</p>
      <p class="recovery-code">${esc(code)}</p>
      <p><button type="button" class="ghost small" id="copy-code">Copy code</button></p>
      <form id="code-form" novalidate>
        <label class="check"><input type="checkbox" id="code-saved"> I've saved my recovery code</label>
        <p class="form-error" role="alert"></p>
        <button type="submit">Continue</button>
      </form>
    </div>
    <p><small>Lost the code later on? While you still know your password, you can make a new one on your
      profile page.</small></p>`;
  window.scrollTo(0, 0);
  $("#copy-code").onclick = async () => {
    try {
      await navigator.clipboard.writeText(code);
      toast("Recovery code copied");
    } catch (e) { toast("Couldn't copy it. Select the code and copy it yourself."); }
  };
  const form = $("#code-form"), error = form.querySelector(".form-error");
  $("#code-saved").onchange = () => { error.textContent = ""; };
  form.onsubmit = e => {
    e.preventDefault();
    if (!$("#code-saved").checked) {
      error.textContent = "Save the code somewhere safe, then tick the box.";
      $("#code-saved").focus();
      return;
    }
    done();
  };
}

// Who you are on the site, with the things only the account's owner may do. Changing the
// username or password, making a new recovery code and deleting the account each ask for the
// current password first.
function profile() {
  const course = courseLessons();
  const quizzes = Object.keys(ME.quiz).filter(t => BY_ID[t]).length;
  const joined = ME.joined ? new Date(ME.joined.replace(" ", "T") + "Z")
    .toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" }) : "";
  const remove = deleteControls();
  // Lets a password manager tie each password box to the account.
  const who = `<input type="text" autocomplete="username" value="${esc(ME.username)}" hidden>`;
  const current = id => field(id, "Current password",
    'name="current" type="password" autocomplete="current-password" maxlength="200" data-pw required');
  const CURRENT_RULE = v => v ? "" : "Enter your current password.";
  V.innerHTML = `
    <h2>Your profile</h2>
    <div class="card">
      <dl class="facts">
        <div><dt>Username</dt><dd>${esc(ME.username)}</dd></div>
        ${joined ? `<div><dt>Member since</dt><dd>${joined}</dd></div>` : ""}
      </dl>
      <p><small>Your username is only for signing in. Other people see your display name.</small></p>
      ${nameRow()}
    </div>

    <div class="tiles">
      <div class="tile"><b>${course.filter(l => isDone(l.id)).length}<small>/${course.length}</small></b><span>course topics understood</span></div>
      <div class="tile"><b>${ME.streak}${ME.streak ? " \u{1F525}" : ""}</b><span>day streak</span></div>
      <div class="tile"><b>${quizzes}</b><span>${quizzes === 1 ? "quiz" : "quizzes"} taken</span></div>
    </div>
    <p><a href="#/dashboard">See all my progress</a></p>

    <h3>Username</h3>
    <form class="card account-form" id="username-form" novalidate>
      <p>To change the name you sign in with, enter the new one and your current password.</p>
      ${field("u-new", "New username", `name="username" autocomplete="off" maxlength="20" ${PLAIN_TEXT} required`,
        "3 to 20 letters, numbers or _.")}
      ${current("u-pass")}
      <p class="form-error" role="alert"></p>
      <button type="submit">Change username</button>
    </form>

    <h3>Password</h3>
    <form class="card account-form" id="password-form" novalidate>
      <p>To prove this is your account, enter your current password first.</p>
      ${who}
      ${current("p-current")}
      ${field("p-new", "New password", 'name="new" type="password" autocomplete="new-password" maxlength="200" data-pw required',
        "At least 8 characters. Changing it signs you out of every other browser.")}
      ${SHOW_PASSWORD.replace("Show password", "Show passwords")}
      <p class="form-error" role="alert"></p>
      <button type="submit">Change password</button>
    </form>

    <h3>Recovery code</h3>
    <form class="card account-form" id="recovery-form" novalidate>
      <p>${ME.recovery ? `Your account has a recovery code: it resets your password if you forget it. If you've
        lost the code, make a new one here. The old one stops working.`
        : `<b>Your account has no recovery code yet.</b> Make one now: it is the only way to reset your
        password if you forget it.`}</p>
      ${who}
      ${current("r-current")}
      <p class="form-error" role="alert"></p>
      <button type="submit">Make a new recovery code</button>
    </form>

    <h3>Signing out</h3>
    <div class="card">
      <p>On a shared computer, sign out when you're done. If you think someone else has got into your
        account, change your password: that signs them out too.</p>
      <div class="row">
        <button data-sign-out>Sign out</button>
        <button class="ghost" data-sign-out="all">Sign out of every browser</button>
      </div>
    </div>

    <h3>Delete your account</h3>
    <div class="card">
      <p>This removes your account and everything saved in it, for good. An account that isn't used for
        12 months is deleted on its own.</p>
      ${remove.button}
      ${remove.form}
    </div>`;

  wireName(profile);
  wireForm($("#username-form"), {
    username: v => !v.trim() ? "Enter the new username." : USERNAME_OK.test(v.trim()) ? ""
      : "Use 3 to 20 letters, numbers or _ (no spaces).",
    current: CURRENT_RULE
  }, async data => {
    const r = await api("/auth/username", { method: "POST", body: { username: data.username, password: data.current } });
    ME.username = r.username;
    profile();
    toast(`You now sign in as ${r.username}`);
  });
  const passwords = $("#password-form");
  wireForm(passwords, {
    current: CURRENT_RULE,
    new: v => !v ? "Choose a new password." : v.length < 8 ? "Use at least 8 characters." : ""
  }, async data => {
    await api("/auth/password", { method: "POST", body: data });
    passwords.reset();
    passwords.querySelectorAll("[data-pw]").forEach(i => { i.type = "password"; });
    toast("Password changed. Other browsers were signed out.");
  });
  wireForm($("#recovery-form"), { current: CURRENT_RULE }, async data => {
    const r = await api("/auth/recovery", { method: "POST", body: { password: data.current } });
    ME.recovery = true;
    recoveryView(r.recovery, "This is your new recovery code. Any code you had before no longer works.", profile);
  });
  wireDelete();
}

// ---------- Formula sheet ----------
function formulas() {
  if (!LESSONS.length) return serverMissing();
  V.innerHTML = `
    <h2>Formula sheet</h2>
    <p>Every key formula from your course, week by week. Click a topic name to open its full lesson.</p>
    <div class="row no-print">
      <input id="fq" type="search" placeholder="Filter, e.g. chain, series, polar, gradient">
      <button class="ghost" id="print">Print / save as PDF</button>
    </div>
    <div id="flist"></div>`;
  const draw = () => {
    const f = $("#fq").value.trim().toLowerCase();
    const html = units().map(u => {
      const list = u.lessons.filter(l =>
        (l.name + " " + l.keywords + " " + l.formulas.map(x => x[0]).join(" ")).toLowerCase().includes(f));
      return list.length ? `<h3>${esc(u.label)}: ${esc(u.title)}</h3>` + list.map(l => `
        <div class="card fcard">
          <a href="#/learn/${l.id}"><b>${esc(l.name)}</b></a>
          ${l.formulas.map(([label, tex]) => `<div class="formula"><small>${label}</small>\\[${tex}\\]</div>`).join("")}
        </div>`).join("") : "";
    }).join("");
    $("#flist").innerHTML = html || `<p class="muted">No formulas match "${esc(f)}".</p>`;
    math($("#flist"));
  };
  $("#fq").oninput = debounce(draw, 200);
  $("#print").onclick = () => window.print();
  draw();
}

// ---------- Practice (#/practice/<week>): extra questions for each week, with worked solutions ----------
let PRACTICE = null;

async function practicePage(arg) {
  if (!LESSONS.length) return serverMissing();
  if (!PRACTICE) {
    try { PRACTICE = await api("/practice"); }
    catch (e) { V.innerHTML = `<h2>Practice</h2><p class="bad">${esc(e.message)}</p>`; return; }
  }
  // No week in the address: open the week of the lesson the learner looked at last.
  const set = PRACTICE.find(p => p.week === +arg) || PRACTICE.find(p => p.week === BY_ID[ME.last_topic]?.week) || PRACTICE[0];
  const i = PRACTICE.indexOf(set);
  const prev = PRACTICE[i - 1], next = PRACTICE[i + 1];
  const count = set.sets.reduce((n, s) => n + s.questions.length, 0);
  const kinds = new Set(set.sets.flatMap(s => s.questions.map(q => q.kind))).size;
  let n = 0;

  V.innerHTML = `
    <h2>Practice</h2>
    <p>Questions for every week of the course, sorted by type, each with a worked solution. A set starts with
      quick questions and builds up to midterm level, and every week ends with long exam-style questions.
      Give each one an honest try on paper before you open the answer.</p>
    <nav class="chips week-tabs" aria-label="Weeks">
      ${PRACTICE.map(p => `<a class="chip ${p === set ? "on" : ""}" href="#/practice/${p.week}"
        ${p === set ? 'aria-current="page"' : ""}>Week ${p.week}</a>`).join("")}
    </nav>
    <h3 class="practice-week">Week ${set.week}: ${esc(set.title)}</h3>
    <p class="muted">${plural(count, "question")} covering ${plural(kinds, "type")} of question, grouped by lesson.</p>
    <nav class="jump" aria-label="Question sets">
      ${set.sets.map((s, i) => `<button data-jump="set-${i}"><span>${i + 1}</span>${esc(s.title)}</button>`).join("")}
    </nav>
    <div id="practice-sets">
      ${set.sets.map((s, i) => `
        <section class="card practice-set" id="set-${i}">
          <div class="row between">
            <h3>${esc(s.title)}</h3>
            ${BY_ID[s.lesson] ? `<a href="#/learn/${s.lesson}">Open the lesson</a>` : ""}
          </div>
          ${s.questions.map(q => `
            <div class="prob">
              <div class="prob-kind">${esc(q.kind)}${q.mins ? `<span class="badge">About ${q.mins} min</span>` : ""}</div>
              <p><b>${++n}.</b> ${q.q}</p>
              <div class="row">
                <button class="ghost small" data-toggle="ans" aria-expanded="false">Show answer</button>
                <button class="ghost small" data-toggle="sol" aria-expanded="false">Show steps</button>
              </div>
              <div class="box ans" hidden><b>Answer:</b> ${q.a}</div>
              <div class="box sol" hidden><ol class="steps">${q.steps.map(step => `<li>${step}</li>`).join("")}</ol></div>
            </div>`).join("")}
        </section>`).join("")}
    </div>
    <div class="pager">
      ${prev ? `<a class="prev" href="#/practice/${prev.week}"><small>Previous week</small>Week ${prev.week}: ${esc(prev.title)}</a>` : ""}
      ${next ? `<a class="next" href="#/practice/${next.week}"><small>Next week</small>Week ${next.week}: ${esc(next.title)}</a>` : ""}
    </div>`;

  V.querySelector(".jump").onclick = e => {
    const b = e.target.closest("[data-jump]");
    if (b) document.getElementById(b.dataset.jump).scrollIntoView({ behavior: "smooth" });
  };

  const LABELS = { ans: "answer", sol: "steps" };
  $("#practice-sets").onclick = e => {
    const b = e.target.closest("[data-toggle]");
    if (!b) return;
    const box = b.closest(".prob").querySelector(".box." + b.dataset.toggle);
    box.hidden = !box.hidden;
    b.setAttribute("aria-expanded", !box.hidden);
    b.textContent = (box.hidden ? "Show " : "Hide ") + LABELS[b.dataset.toggle];
  };
}

// ---------- Forum ----------
async function forum(_, params) {
  if (!LESSONS.length) return serverMissing();
  const topic = params.get("topic") || "";

  V.innerHTML = `
    <h2>Q&amp;A Forum</h2>
    <p>Stuck? Ask the community. Math questions, study tips, follow-up questions and a quick thanks are all
      welcome. Posts are checked automatically so the forum stays kind and about math.
      You can type math like <code>\\( x^2 \\)</code> and it will display nicely.</p>
    <p><small>Posts are public, so please don't share personal details such as full names, contact details or
      your school. Under 13? Ask a parent or guardian before you post. See the
      <a href="terms.html">rules</a>.</small></p>

    <div class="card" id="ask-card">
      <h3>Ask a question</h3>
      <small>Posting as <b>${esc(ME.name || "Anonymous learner")}</b> · <a href="#/dashboard">change name</a></small>
      <input id="nq" maxlength="200" placeholder="Your question in one sentence, e.g. How do I know when to use the ratio test?">
      <textarea id="nb" rows="3" placeholder="Details (optional): what have you tried, and where did you get stuck?"></textarea>
      <div class="row"><select id="nt" aria-label="Topic">${topicOptions(topic, "No specific topic")}</select>
        <button id="ask">Post question</button></div>
      <p id="ask-msg" class="bad" role="alert"></p>
    </div>

    <div class="row filters">
      <select id="ft" aria-label="Filter by topic">${topicOptions(topic, "All topics")}</select>
      <input id="fs" type="search" placeholder="Search questions" aria-label="Search questions">
      <label class="sort" for="fo">Sort by
        <select id="fo">
          <option value="liked">Most liked</option>
          <option value="new">Newest</option>
          <option value="old">Oldest</option>
          <option value="replies">Most replies</option>
          <option value="unanswered">No replies yet</option>
        </select>
      </label>
    </div>
    <div id="qs"><p class="muted">Loading…</p></div>`;

  if (topic) $("#nq").focus();

  // `show` is the id of a question to scroll to (the one just posted).
  const load = async show => {
    const p = new URLSearchParams({ topic: $("#ft").value, q: $("#fs").value, sort: $("#fo").value });
    let qs;
    try { qs = await api("/questions?" + p); }
    catch (e) { $("#qs").innerHTML = `<p class="bad">${esc(e.message)}</p>`; return; }
    const filtered = $("#ft").value || $("#fs").value || $("#fo").value === "unanswered";
    $("#qs").innerHTML = qs.length ? qs.map(renderQuestion).join("")
      : `<div class="empty">${filtered ? "No questions match. Try a different topic, search or sort."
        : "No questions here yet. Be the first to ask! Someone else is probably wondering the same thing."}</div>`;
    math($("#qs"));
    const card = show && $("#q" + show);
    if (card) {
      card.classList.add("hl");
      card.scrollIntoView({ block: "center" });
    }
  };

  $("#ask").onclick = async () => {
    $("#ask-msg").textContent = "";
    $("#ask").disabled = true;  // the check can take a few seconds
    try {
      const r = await api("/questions", { method: "POST", body: { title: $("#nq").value, body: $("#nb").value, topic: $("#nt").value } });
      $("#nq").value = $("#nb").value = "";
      toast("Question posted!");
      load(r.id);
    } catch (e) { $("#ask-msg").textContent = e.message; }
    $("#ask").disabled = false;
  };

  $("#ft").onchange = () => load();
  $("#fo").onchange = () => load();
  $("#fs").oninput = debounce(() => load(), 300);

  $("#qs").onclick = async e => {
    const t = e.target.closest("button");
    if (!t) return;
    try {
      if (t.dataset.vote) {
        // The counts change in place: re-sorting the list on every like would make it jump around.
        const r = await api("/vote", { method: "POST", body: { kind: t.dataset.vote, id: +t.dataset.id, value: +t.dataset.value } });
        const group = t.closest(".votes"), foot = group.parentElement;
        group.outerHTML = voteButtons(t.dataset.vote, { id: t.dataset.id, ...r });
        foot.querySelector(`.vote[data-value="${t.dataset.value}"]`).focus();
        return;
      } else if (t.dataset.del) {
        if (!confirm("Delete this question and its replies?")) return;
        await api("/questions/" + t.dataset.del, { method: "DELETE" });
        toast("Question deleted");
      } else if (t.dataset.delAnswer) {
        if (!confirm("Delete this reply?")) return;
        await api("/answers/" + t.dataset.delAnswer, { method: "DELETE" });
        toast("Reply deleted");
      } else if (t.dataset.block) {
        if (!confirm("Block this person? They are locked out and everything they posted is deleted.")) return;
        await api("/admin/block", { method: "POST", body: { kind: t.dataset.block, id: +t.dataset.id } });
        toast("Blocked, and their posts deleted");
      } else if (t.dataset.report) {
        if (!confirm("Report this post to the moderators?")) return;
        await api("/report", { method: "POST", body: { kind: t.dataset.report, id: +t.dataset.id } });
        toast("Reported. Thanks, a moderator will take a look.");
        return;
      } else if (t.dataset.reply) {
        const id = t.dataset.reply;
        const msg = $("#m" + id);
        msg.textContent = "";
        t.disabled = true;
        try {
          await api(`/questions/${id}/answers`, { method: "POST", body: { body: $("#a" + id).value } });
          toast("Reply posted");
        } catch (err) { msg.textContent = err.message; t.disabled = false; return; }
      } else return;
      load();
    } catch (err) { toast(err.message); }
  };

  await load();
}

const THUMB = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
  stroke-linejoin="round" aria-hidden="true"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/></svg>`;

// Like and dislike buttons for a question ("q") or reply ("a"). Pressing your own vote again takes it back.
function voteButtons(kind, p) {
  const button = (value, word, count) => `<button class="vote ${value < 0 ? "down" : ""} ${p.my_vote === value ? "on" : ""}"
    data-vote="${kind}" data-id="${p.id}" data-value="${value}" aria-pressed="${p.my_vote === value}"
    aria-label="${word} (${count})" ${p.mine ? `disabled title="You can't vote on your own post"` : `title="${word}"`}>${THUMB}<span>${count}</span></button>`;
  return `<div class="votes" role="group" aria-label="Likes and dislikes">${button(1, "Like", p.likes)}${button(-1, "Dislike", p.dislikes)}</div>`;
}

// Moderators see the 1-10 score the automatic check gave a post.
const scoreBadge = p => ME.admin && p.score ? ` · <span class="badge" title="Automatic check: 1 (doesn't belong) to 10 (great)">${p.score}/10</span>` : "";

function renderQuestion(q) {
  const topic = q.topic_id && BY_ID[q.topic_id];
  return `<div class="card q" id="q${q.id}">
    <b class="q-title">${esc(q.title)}</b>
    ${q.body ? `<p class="post-text">${esc(q.body)}</p>` : ""}
    <div class="post-foot">
      ${voteButtons("q", q)}
      <div class="meta">
        ${topic ? `<a class="chip" href="#/learn/${topic.id}">${esc(topic.name)}</a>` : ""}
        ${esc(q.author)} · ${timeAgo(q.created)} · ${q.answer_count} ${q.answer_count === 1 ? "reply" : "replies"}${scoreBadge(q)}
        ${q.mine || ME.admin ? ` · <button class="link" data-del="${q.id}">Delete</button>` : ""}
        ${ME.admin && !q.mine ? ` · <button class="link" data-block="q" data-id="${q.id}">Block author</button>` : ""}
        ${q.mine ? "" : ` · <button class="link" data-report="q" data-id="${q.id}">Report</button>`}
      </div>
    </div>
    <div class="answers">${q.answers.map(renderAnswer).join("")}</div>
    <div class="row reply">
      <textarea id="a${q.id}" rows="1" placeholder="Write a reply" aria-label="Write a reply"></textarea>
      <button data-reply="${q.id}">Reply</button>
    </div>
    <p class="bad" id="m${q.id}" role="alert"></p>
  </div>`;
}

function renderAnswer(a) {
  return `<div class="answer">
    <p class="post-text">${esc(a.body)}</p>
    <div class="post-foot">
      ${voteButtons("a", a)}
      <div class="meta">
        ${esc(a.author)} · ${timeAgo(a.created)}${scoreBadge(a)}
        ${a.mine || ME.admin ? ` · <button class="link" data-del-answer="${a.id}">Delete</button>` : ""}
        ${ME.admin && !a.mine ? ` · <button class="link" data-block="a" data-id="${a.id}">Block author</button>` : ""}
        ${a.mine ? "" : ` · <button class="link" data-report="a" data-id="${a.id}">Report</button>`}
      </div>
    </div>
  </div>`;
}

// ---------- Upload ----------
async function upload() {
  if (!LESSONS.length) return serverMissing();
  const savedStyle = +(store("style") || 0);

  V.innerHTML = `
    <h2>Upload your notes</h2>
    <p>Upload class notes, homework or a practice sheet. PDFs become a <b>video lesson</b>: short animated episodes with
      voiceover and practice questions. You also get a study plan for the topics it covers.</p>
    <div class="card">
      <label class="drop" id="drop">
        <input type="file" id="f" accept=".pdf,.docx,.txt,.doc">
        <b>Drop a file here</b> or click to choose
        <small>PDF, Word (.docx) or text, up to 10 MB</small>
        <span id="fname"></span>
      </label>
      <h3>How do you like to learn?</h3>
      <div class="styles">${STYLES.map((s, i) => `
        <label class="style"><input type="radio" name="style" value="${i}" ${i === savedStyle ? "checked" : ""}>
          <b>${s[0]}</b><small>${s[1]}</small></label>`).join("")}</div>
      <p><small>Before you upload: a PDF may be sent to an AI service (Anthropic, in the United States) to
        build its lesson. Don't upload files that contain personal information, and only upload notes you're
        allowed to share. <a href="privacy.html">How we handle uploads</a></small></p>
      <button id="go">Upload &amp; build my lesson</button>
      <div id="out" role="status"></div>
    </div>
    <small>Note: research on matching lessons to a single "learning style" is weak, so mixing methods works best.
      Use your favourite as a starting point.</small>
    <h3>Your past uploads</h3>
    <div id="past"><p class="muted">Loading…</p></div>`;

  const input = $("#f"), drop = $("#drop");
  const showName = () => { $("#fname").textContent = input.files[0] ? "Selected: " + input.files[0].name : ""; };
  input.onchange = showName;
  drop.ondragover = e => { e.preventDefault(); drop.classList.add("over"); };
  drop.ondragleave = () => drop.classList.remove("over");
  drop.ondrop = e => {
    e.preventDefault();
    drop.classList.remove("over");
    input.files = e.dataTransfer.files;
    showName();
  };

  $("#go").onclick = async () => {
    const file = input.files[0];
    const style = +V.querySelector("input[name=style]:checked").value;
    store("style", style);
    if (!file) { $("#out").innerHTML = `<p class="bad">Choose a file first.</p>`; return; }
    const fd = new FormData();
    fd.append("file", file);
    fd.append("style", style);
    $("#out").innerHTML = `<p class="muted">Reading your file…</p>`;
    try {
      const r = await api("/upload", { method: "POST", body: fd });
      const isPdf = /\.pdf$/i.test(r.filename);
      $("#out").innerHTML = (r.video ? renderVideoResult(r.video, r.style)
        : isPdf && !r.ai_available ? `<div class="plan"><b>🎬 Want this PDF as animated video episodes?</b>
            <p class="muted">Turning new PDFs into videos uses Claude, so it needs an Anthropic API key.
            Set <code>ANTHROPIC_API_KEY</code>, restart <code>python server.py</code> and upload again.
            Meanwhile, here's a study plan:</p></div>` : "")
        + (r.video ? `<details class="plan-details"><summary>Show the study plan too</summary>${renderPlan(r)}</details>` : renderPlan(r));
      math($("#out"));
      loadPast();
    } catch (e) { $("#out").innerHTML = `<p class="bad">${esc(e.message)}</p>`; }
  };

  const loadPast = async () => {
    try {
      const items = await api("/uploads");
      $("#past").innerHTML = items.length ? items.map(i => `<div class="card slim">
        <div class="row between"><div><b>${esc(i.filename)}</b> <small>· ${STYLES[i.style]?.[0] || ""} · ${timeAgo(i.created)}</small></div>
          ${i.video ? `<a class="btn small" href="#/watch/${i.video.id}">${i.video.status === "ready" ? "Open lesson" : i.video.status === "failed" ? "⚠ Lesson failed" : "⏳ Building lesson…"}</a>` : ""}</div>
        <div class="chips">${i.topics.filter(t => BY_ID[t]).map(t => `<a class="chip" href="#/learn/${t}">${esc(BY_ID[t].name)}</a>`).join("") || "<small>No topics detected</small>"}</div>
      </div>`).join("") : `<p class="muted">Nothing yet.</p>`;
    } catch (e) { $("#past").innerHTML = ""; }
  };
  loadPast();
}

function renderVideoResult(v, style = learnerStyle()) {
  if (v.status !== "ready") {
    return `<div class="video-ready">
      <div class="big-emoji">${v.status === "failed" ? "⚠️" : "⏳"}</div>
      <div><h3>${v.status === "failed" ? "The lesson couldn't be built" : "Building your lesson…"}</h3>
      <p class="muted">${esc(v.message || "This takes a few minutes. You can leave this page; it keeps going.")}</p>
      <a class="btn" href="#/watch/${v.id}">Open lesson page</a></div></div>`;
  }
  const watchMin = Math.round(v.episodes.reduce((s, e) => s + e.seconds, 0) / 60);
  const readMin = v.episodes.reduce((s, e) => s + (e.read_minutes || 0), 0);
  const mode = STYLE_MODES[style];
  const cta = { practice: "✏️ Start with the practice questions", read: "📖 Read episode 1", watch: "▶ Watch episode 1" }[mode];
  return `<div class="video-ready">
    <div class="big-emoji">${mode === "watch" ? "🎬" : mode === "read" ? "📖" : "✏️"}</div>
    <div><h3>Your lesson is ready!</h3>
    <p><b>${esc(v.title)}</b> · ${plural(v.episodes.length, "episode")}.
      Watch them (about ${watchMin} min)${readMin ? `, read them (about ${readMin} min)` : ""} or go straight to practice.</p>
    <ol class="ep-list">${v.episodes.map(e => `<li>${esc(e.title)} <small>🎬 ${fmtSecs(e.seconds)}${e.read_minutes ? ` · 📖 ${e.read_minutes} min` : ""}</small></li>`).join("")}</ol>
    <a class="btn" href="#/watch/${v.id}?mode=${mode}">${cta}</a>
    <p class="muted"><small>Starting with ${mode} because you picked "${STYLES[style][0]}". You can switch any time.</small></p></div></div>`;
}

const fmtSecs = s => Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");

// ---------- Video lessons ----------
let pollTimer;
const LEVELS = [["easy", "Easy", 5], ["intermediate", "Intermediate", 5], ["advanced", "Advanced", 5], ["expert", "Expert", 3]];

// An episode counts as done once it's been watched or read.
function epDone(progress, i) { return !!(progress?.[i]?.watched || progress?.[i]?.read); }

// How each learning style (same order as STYLES) uses a lesson: the tab it opens on, and a tip.
const STYLE_MODES = ["practice", "read", "watch", "read", "read"];

function learnerStyle() {
  const s = store("style");
  return s === null ? 2 : Math.min(4, Math.max(0, +s || 0));
}

function startMode(style, epProgress) {
  // Spaced-repetition learners coming back to an episode go straight to review.
  if (style === 4 && (epProgress.watched || epProgress.read)) return "practice";
  return STYLE_MODES[style];
}

function reviewDates() {
  const fmt = d => new Date(Date.now() + d * 86400000).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  return [1, 3, 7, 14].map(fmt).join(" · ");
}

function styleTip(style) {
  return [
    "✏️ Practice first: try the questions, then read or watch only the parts you got wrong.",
    "🧩 Worked examples: the Read tab reveals each example one step at a time. Predict the next step before you click.",
    "🎬 Visual: watch the episode, then lock it in with the practice questions.",
    "📖 Reading: a written version of every episode, with figures, worked examples and space for your own notes.",
    `🧠 Spaced repetition: learn it today, then redo the practice on ${reviewDates()}. Coming back is what makes it stick.`
  ][style];
}

async function videosView() {
  let data;
  try { data = await api("/videos"); }
  catch (e) { V.innerHTML = `<h2>Video lessons</h2><p class="bad">${esc(e.message)}</p>`; return; }
  V.innerHTML = `
    <h2>Your lessons</h2>
    <p>Your PDFs turned into episodes, one subtopic each. Watch them as animated videos, read them as text, or jump straight to the 18 practice questions.
      Each lesson opens in the format that matches your learning style.</p>
    ${data.videos.length ? data.videos.map(v => {
      if (v.status !== "ready") return `<div class="card">
        <b>${esc(v.filename)}</b>
        <p class="${v.status === "failed" ? "bad" : "muted"}">${v.status === "failed" ? "⚠ " : "⏳ "}${esc(v.message || "Building…")}</p>
        <a class="btn small" href="#/watch/${v.id}">Open</a></div>`;
      const watched = v.episodes.filter((_, i) => epDone(v.progress, i)).length;
      const next = v.episodes.findIndex((_, i) => !epDone(v.progress, i));
      return `<div class="card">
        <div class="row between"><div><small>${esc(v.source || v.filename)}</small><h3>${esc(v.title)}</h3></div>
          <a class="btn" href="#/watch/${v.id}${next > 0 ? "?ep=" + (next + 1) : ""}">${watched === 0 ? "▶ Start" : next === -1 ? "↺ Review" : "▶ Continue"}</a></div>
        <div class="bar" role="progressbar" aria-valuenow="${watched}" aria-valuemax="${v.episodes.length}" aria-label="Episodes done"><i style="width:${100 * watched / v.episodes.length}%"></i></div>
        <div class="chips">${v.episodes.map((e, i) => `<a class="chip ${epDone(v.progress, i) ? "done" : ""}" href="#/watch/${v.id}?ep=${i + 1}">
          ${epDone(v.progress, i) ? "✓ " : ""}${i + 1}. ${esc(e.title)} · ${fmtSecs(e.seconds)}</a>`).join("")}</div>
      </div>`;
    }).join("") : `<div class="empty">No video lessons yet. <a href="#/upload">Upload a PDF</a> of your class notes to get one.</div>`}`;
  if (data.videos.some(v => v.status === "generating")) {
    pollTimer = setTimeout(() => location.hash === "#/videos" && route(), 5000);
  }
}

async function watch(id, params) {
  let data;
  try { data = await api("/videos/" + encodeURIComponent(id)); }
  catch (e) { V.innerHTML = `<h2>Video lesson</h2><p class="bad">${esc(e.message)}</p><a href="#/videos">← All video lessons</a>`; return; }

  if (data.status !== "ready") {
    const failed = data.status === "failed";
    V.innerHTML = `<div class="crumbs"><a href="#/videos">Video lessons</a></div>
      <div class="card video-ready">
        <div class="big-emoji ${failed ? "" : "spin"}">${failed ? "⚠️" : "⏳"}</div>
        <div><h3>${failed ? "This lesson couldn't be built" : "Building your video lesson…"}</h3>
        <p>${esc(data.message || "Starting…")}</p>
        ${failed ? `<button id="retry">Retry</button>` : `<small>This usually takes a few minutes. This page updates by itself.</small>`}</div>
      </div>`;
    if (failed) {
      $("#retry").onclick = async () => {
        try { await api(`/videos/${id}/retry`, { method: "POST" }); route(); } catch (e) { toast(e.message); }
      };
    } else {
      const here = location.hash;
      pollTimer = setTimeout(() => location.hash === here && route(), 4000);
    }
    return;
  }

  const lesson = data.lesson;
  let progress = data.progress || {};
  const n = lesson.episodes.length;
  const epIdx = Math.min(n, Math.max(1, +params.get("ep") || 1)) - 1;
  const ep = lesson.episodes[epIdx];
  const secs = VideoPlayer.episodeSeconds(ep);
  const article = ep.article || Reader.fromScenes(ep);
  const readMin = Reader.minutes(article);
  const questionCount = LEVELS.reduce((s, [k]) => s + (ep.questions[k] || []).length, 0);
  const epProgress = () => progress[epIdx] || {};
  let style = learnerStyle();
  let mode = ["watch", "read", "practice"].includes(params.get("mode")) ? params.get("mode") : startMode(style, epProgress());
  const epHref = (i, m = mode) => `#/watch/${id}?ep=${i + 1}&mode=${m}`;
  const hasNext = epIdx + 1 < n;

  V.innerHTML = `
    <div class="crumbs"><a href="#/videos">Lessons</a>${lesson.source ? " · " + esc(lesson.source) : ""}</div>
    <h2>${esc(lesson.title)}</h2>
    <div class="style-bar">
      <label>I learn best by
        <select id="style-sel">${STYLES.map((s, i) => `<option value="${i}" ${i === style ? "selected" : ""}>${s[0].replace(/ learner$/, "")}</option>`).join("")}</select>
      </label>
      <span class="style-tip"></span>
    </div>
    <nav class="episodes" aria-label="Episodes">${lesson.episodes.map((e, i) => `
      <a href="${epHref(i)}" class="ep ${i === epIdx ? "on" : ""} ${epDone(progress, i) ? "done" : ""}" ${i === epIdx ? 'aria-current="page"' : ""}>
        <span class="n">${epDone(progress, i) ? "✓" : i + 1}</span><span class="t">${esc(e.title)}</span><small>${fmtSecs(VideoPlayer.episodeSeconds(e))}</small></a>`).join("")}
    </nav>
    <div class="ep-head">
      <h3>Episode ${epIdx + 1} of ${n}: ${esc(ep.title)}</h3>
      <p class="muted">${esc(ep.hook || "")}</p>
    </div>
    <div class="modes" role="tablist" aria-label="How to learn this episode">
      <button role="tab" data-mode="watch">🎬 Watch <small>${fmtSecs(secs)}</small></button>
      <button role="tab" data-mode="read">📖 Read <small>${readMin} min</small></button>
      <button role="tab" data-mode="practice">✏️ Practice <small>${questionCount} questions</small></button>
    </div>
    <div id="mode-body"></div>`;

  const body = $("#mode-body");
  const save = async (level, score, total) => {
    try {
      progress = (await api(`/videos/${id}/progress`, { method: "POST", body: { episode: epIdx, level, score, total } })).progress;
    } catch (e) { toast("Couldn't save: " + e.message); }
  };
  const markDone = () => {
    const chip = V.querySelectorAll(".episodes .ep")[epIdx];
    chip.classList.add("done");
    chip.querySelector(".n").textContent = "✓";
  };

  const showWatch = () => {
    body.innerHTML = `<div id="player"></div>
      <p class="player-tips"><small>🔊 Turn your sound on for the voiceover · <kbd>space</kbd> play/pause · <kbd>←</kbd> <kbd>→</kbd> skip scenes · speed button for 1.25× to 2×</small></p>`;
    new VideoPlayer.Player($("#player"), ep, {
      hasNext,
      onNext: () => { location.hash = epHref(epIdx + 1, "watch"); },
      onPractice: () => setMode("practice"),
      onEnd: async () => { await save("watched", 1, 1); markDone(); }
    });
  };

  const showRead = () => {
    const read = !!epProgress().read;
    body.innerHTML = `<article class="reader">
      <p class="reader-meta">📖 ${readMin} min read${style === 1 ? " · worked examples reveal one step at a time" : ""}</p>
      ${Reader.render(article, { stepByStep: style === 1 })}
      <div class="row reader-end">
        <button id="mark-read" class="${read ? "ghost" : ""}">${read ? "✓ Read" : "✓ Mark as read"}</button>
        <button class="ghost" data-goto="practice">✏️ Practice now</button>
        ${hasNext ? `<a class="btn ghost" href="${epHref(epIdx + 1, "read")}">Next episode →</a>` : ""}
      </div>
      <section class="card notes-card">
        <h3>📝 My notes</h3>
        <p class="muted">${style === 3 ? "Rewrite the big ideas in your own words. For readers, that's the single best way to make it stick."
          : "Jot down anything you want to remember."}</p>
        <textarea id="vnote" rows="5" placeholder="Saved automatically"></textarea>
        <small id="vnote-status"></small>
      </section>
    </article>`;
    Reader.hydrate(body, ep);
    $("#mark-read").onclick = async () => {
      await save("read", 1, 1);
      markDone();
      $("#mark-read").textContent = "✓ Read";
      $("#mark-read").classList.add("ghost");
      toast(hasNext ? "Nice! On to the next episode when you're ready." : "You finished the last episode! 🎉");
    };
    const note = $("#vnote"), status = $("#vnote-status");
    api(`/videos/${id}/notes/${epIdx}`).then(r => { note.value = r.body; }).catch(() => {});
    note.oninput = debounce(async () => {
      status.textContent = "Saving…";
      try {
        await api(`/videos/${id}/notes/${epIdx}`, { method: "PUT", body: { body: note.value } });
        status.textContent = "Saved ✓";
      } catch (e) { status.textContent = e.message; }
    }, 700);
  };

  const showPractice = () => {
    body.innerHTML = `
      ${style === 0 ? `<div class="callout">✏️ Try these first. Got one wrong? <button class="link" data-goto="read">Read the lesson</button>
        or <button class="link" data-goto="watch">watch the episode</button>, then come back and retry.</div>` : ""}
      ${style === 4 ? `<div class="callout">🧠 Redo this practice on ${reviewDates()} to move it into long-term memory.</div>` : ""}
      <section class="card practice" id="practice"></section>`;
    renderPractice($("#practice"), ep, epProgress, save, hasNext ? epHref(epIdx + 1, STYLE_MODES[style]) : null);
  };

  function setMode(m) {
    mode = m;
    VideoPlayer.stopAll();
    V.querySelectorAll(".modes [data-mode]").forEach(b => {
      b.classList.toggle("on", b.dataset.mode === m);
      b.setAttribute("aria-selected", b.dataset.mode === m);
    });
    V.querySelectorAll(".episodes .ep").forEach((a, i) => { a.href = epHref(i); });
    history.replaceState(null, "", epHref(epIdx));
    ({ watch: showWatch, read: showRead, practice: showPractice })[m]();
  }

  V.querySelector(".modes").onclick = e => {
    const b = e.target.closest("[data-mode]");
    if (b && b.dataset.mode !== mode) setMode(b.dataset.mode);
  };
  body.addEventListener("click", e => {
    const g = e.target.closest("[data-goto]");
    if (g) { setMode(g.dataset.goto); V.querySelector(".modes").scrollIntoView({ behavior: "smooth" }); }
  });
  const tip = V.querySelector(".style-tip");
  tip.textContent = styleTip(style);
  $("#style-sel").onchange = e => {
    style = +e.target.value;
    store("style", style);
    tip.textContent = styleTip(style);
    setMode(startMode(style, epProgress()));
  };
  setMode(mode);
}

function renderPractice(box, ep, getProgress, save, nextHref) {
  const rich = VideoPlayer.rich;
  let level = (LEVELS.find(([k]) => !getProgress()[k]) || LEVELS[0])[0];
  let combo = 0;

  const paint = () => {
    const prog = getProgress();
    box.innerHTML = `
      <h3>Practice: prove you've got it 💪</h3>
      <p class="muted">5 easy, 5 intermediate, 5 advanced, then 3 expert problems where you really have to think.</p>
      <div class="levels" role="tablist">${LEVELS.map(([k, name, count]) => {
        const p = prog[k];
        return `<button role="tab" class="lvl lvl-${k} ${k === level ? "on" : ""}" aria-selected="${k === level}" data-level="${k}">
          ${name}<small>${p ? `best ${p.score}/${p.total}` : `${count} questions`}</small></button>`;
      }).join("")}</div>
      <div class="combo" aria-live="polite"></div>
      <div class="lvl-body"></div>`;
    box.querySelector(".levels").onclick = e => {
      const b = e.target.closest("[data-level]");
      if (b) { level = b.dataset.level; combo = 0; paint(); }
    };
    level === "expert" ? expertLevel() : mcLevel();
  };

  const nextLevel = () => {
    const i = LEVELS.findIndex(([k]) => k === level);
    return LEVELS[i + 1]?.[0];
  };

  const finishBar = (score, total) => {
    const pct = Math.round(100 * score / total);
    const nl = nextLevel();
    const msg = pct === 100 ? "Perfect! 🔥" : pct >= 60 ? "Nice work!" : "Good effort. Review the lesson (Read or Watch above) and try again.";
    return `<div class="result ${pct >= 60 ? "good" : ""}"><div class="score">${score}/${total}</div><div><b>${pct}%</b> · ${msg}</div></div>
      <div class="row"><button class="ghost retry-lvl">Retry this level</button>
      ${nl ? `<button class="next-lvl">Next: ${LEVELS.find(([k]) => k === nl)[1]} →</button>`
           : nextHref ? `<a class="btn" href="${nextHref}">Next episode ▶</a>` : `<a class="btn" href="#/videos">Back to video lessons</a>`}</div>`;
  };

  const wireFinish = el => {
    el.querySelector(".retry-lvl").onclick = () => { combo = 0; paint(); };
    const nl = el.querySelector(".next-lvl");
    if (nl) nl.onclick = () => { level = nextLevel(); combo = 0; paint(); box.scrollIntoView({ behavior: "smooth" }); };
  };

  function mcLevel() {
    const qs = ep.questions[level] || [];
    const body = box.querySelector(".lvl-body");
    let answered = 0, correct = 0;
    body.innerHTML = qs.map((q, i) => `
      <div class="qq" data-i="${i}">
        <p><b>${i + 1}.</b> ${rich(q.q)}</p>
        <div class="choices">${q.choices.map((c, j) => `<button class="choice" data-j="${j}">${rich(c)}</button>`).join("")}</div>
        <p class="why" hidden></p>
      </div>`).join("") + `<div class="lvl-result"></div>`;
    body.onclick = async e => {
      const btn = e.target.closest(".choice");
      if (!btn) return;
      const qq = btn.closest(".qq");
      if (qq.dataset.answered) return;
      qq.dataset.answered = "1";
      const q = qs[qq.dataset.i];
      const right = +btn.dataset.j === q.answer;
      answered++;
      if (right) { correct++; combo++; } else combo = 0;
      qq.querySelectorAll(".choice").forEach((b, k) => { b.disabled = true; if (k === q.answer) b.classList.add("right"); });
      if (!right) btn.classList.add("wrong");
      const why = qq.querySelector(".why");
      why.hidden = false;
      why.innerHTML = `<b class="${right ? "ok" : "bad"}">${right ? "Correct!" : "Not quite."}</b> ${rich(q.why)}`;
      const comboEl = box.querySelector(".combo");
      comboEl.textContent = combo >= 2 ? `🔥 ${combo} in a row!` : "";
      if (combo >= 2 && window.anime) anime({ targets: comboEl, scale: [1.3, 1], duration: 400, easing: "easeOutBack" });
      if (answered === qs.length) {
        const res = body.querySelector(".lvl-result");
        res.innerHTML = finishBar(correct, qs.length);
        wireFinish(res);
        if (correct === qs.length) VideoPlayer.confetti(box);
        await save(level, correct, qs.length);
        box.querySelector(`.lvl-${level} small`).textContent = `best ${getProgress()[level]?.score ?? correct}/${qs.length}`;
      }
    };
  }

  function expertLevel() {
    const qs = ep.questions.expert || [];
    const body = box.querySelector(".lvl-body");
    let marked = 0, got = 0;
    body.innerHTML = `<p class="muted">🧠 Expert problems: grab paper and work each one out fully before you peek. Then mark yourself honestly.</p>` +
      qs.map((q, i) => `
      <div class="qq expert" data-i="${i}">
        <p><b>${i + 1}.</b> ${rich(q.q)}</p>
        <div class="row"><button class="ghost small" data-act="hint">💡 Hint</button><button class="ghost small" data-act="sol">Show solution</button></div>
        <div class="box hint" hidden>${rich(q.hint)}</div>
        <div class="box ans" hidden>
          <ol>${q.steps.map(s => `<li>${rich(s)}</li>`).join("")}</ol>
          <p><b>Answer:</b> ${rich(q.answer)}</p>
          <div class="row self"><span>Did you get it?</span>
            <button class="small" data-act="yes">✅ I got it</button><button class="ghost small" data-act="no">Not yet</button></div>
        </div>
      </div>`).join("") + `<div class="lvl-result"></div>`;
    body.onclick = async e => {
      const b = e.target.closest("[data-act]");
      if (!b) return;
      const qq = b.closest(".qq");
      const a = b.dataset.act;
      if (a === "hint") qq.querySelector(".hint").hidden = !qq.querySelector(".hint").hidden;
      if (a === "sol") { qq.querySelector(".ans").hidden = false; b.remove(); }
      if ((a === "yes" || a === "no") && !qq.dataset.marked) {
        qq.dataset.marked = a;
        marked++;
        if (a === "yes") got++;
        qq.querySelector(".self").innerHTML = a === "yes" ? `<b class="ok">✅ Nice, expert-level work!</b>` : `<b class="bad">No stress. Read the steps and try it again tomorrow.</b>`;
        if (marked === qs.length) {
          const res = body.querySelector(".lvl-result");
          res.innerHTML = finishBar(got, qs.length);
          wireFinish(res);
          if (got === qs.length) VideoPlayer.confetti(box);
          await save("expert", got, qs.length);
          box.querySelector(".lvl-expert small").textContent = `best ${getProgress().expert?.score ?? got}/${qs.length}`;
        }
      }
    };
  }

  paint();
}

function renderPlan(r) {
  const [name, , steps] = STYLES[r.style] || STYLES[0];
  const topics = r.topics.filter(t => BY_ID[t]);
  let dates = "";
  if (r.style === 4) {
    const fmt = d => new Date(Date.now() + d * 86400000).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
    dates = `<p><b>Review dates:</b> ${[1, 3, 7, 14].map(fmt).join(" → ")}</p>`;
  }
  return `<div class="plan">
    <h3>Study plan for ${esc(r.filename)}</h3>
    ${topics.length ? `<p>It looks like this covers:</p>
      <ol>${topics.map(t => `<li><a href="#/learn/${t}">${esc(BY_ID[t].name)}</a> <small>${esc(unitLabel(BY_ID[t]))}${isDone(t) ? " · ✓ already understood" : ""}</small></li>`).join("")}</ol>`
      : `<p>We couldn't spot specific topics${r.read_text ? "" : " (we couldn't read any text from this file, which happens with scanned PDFs)"}.
         Pick the topics yourself from the <a href="#/learn">Learn</a> page.</p>`}
    <p><b>For each topic (${name}):</b></p>
    <ol>${steps.map(s => `<li>${s}</li>`).join("")}</ol>
    ${dates}
  </div>`;
}

// ---------- Moderation (#/admin, not linked from the menu) ----------
async function admin() {
  if (!ME.admin) {
    V.innerHTML = `
      <h2>Moderation</h2>
      <p>Enter the moderator passcode to see reported posts and to delete or block from this browser.</p>
      <form class="card" id="unlock" novalidate>
        <div class="field">
          <label for="admin-key">Passcode</label>
          <input id="admin-key" type="password" autocomplete="off" required>
        </div>
        <p class="form-error" role="alert"></p>
        <button type="submit">Unlock moderation</button>
      </form>`;
    $("#unlock").onsubmit = async e => {
      e.preventDefault();
      try {
        await api("/admin/unlock", { method: "POST", body: { key: $("#admin-key").value } });
        ME.admin = true;
        admin();
      } catch (err) { $("#unlock .form-error").textContent = err.message; }
    };
    return;
  }

  let items = [];
  try { items = await api("/admin/reports"); } catch (e) { toast(e.message); }
  V.innerHTML = `
    <h2>Moderation</h2>
    <p>This browser can delete any forum post and block its author. Reported posts are listed here; the same
      Delete and Block links also show on every post in the <a href="#/forum">forum</a>.</p>
    <div id="reports">${items.length ? items.map(p => `<div class="card">
      <small>${plural(p.reports, "report")} · ${p.kind === "q" ? "Question" : "Reply"} by ${esc(p.author)}</small>
      <p><b>${esc(p.title)}</b></p>
      ${p.body ? `<p class="post-text">${esc(p.body)}</p>` : ""}
      <div class="row">
        <button class="small danger" data-remove="${p.kind}" data-id="${p.id}">Delete post</button>
        <button class="small ghost danger" data-block="${p.kind}" data-id="${p.id}">Block author</button>
        <button class="small ghost" data-dismiss="${p.kind}" data-id="${p.id}">Keep post</button>
      </div>
    </div>`).join("") : `<div class="empty">No reported posts.</div>`}</div>
    <p><button class="ghost small" id="admin-lock">Stop moderating on this browser</button></p>`;
  math(V);

  $("#reports").onclick = async e => {
    const t = e.target.closest("button");
    if (!t) return;
    const post = { kind: t.dataset.remove || t.dataset.block || t.dataset.dismiss, id: +t.dataset.id };
    try {
      if (t.dataset.remove) {
        if (!confirm("Delete this post?")) return;
        await api((post.kind === "q" ? "/questions/" : "/answers/") + post.id, { method: "DELETE" });
      } else if (t.dataset.block) {
        if (!confirm("Block this person? They are locked out and everything they posted is deleted.")) return;
        await api("/admin/block", { method: "POST", body: post });
      } else if (t.dataset.dismiss) {
        await api("/admin/reports/dismiss", { method: "POST", body: post });
      } else return;
      admin();
    } catch (err) { toast(err.message); }
  };
  $("#admin-lock").onclick = async () => {
    try { await api("/admin/lock", { method: "POST" }); } catch (err) { toast(err.message); return; }
    ME.admin = false;
    admin();
  };
}

// ---------- Feedback ----------
async function feedback() {
  let count = 0;
  try { count = (await api("/feedback")).count; } catch (e) { /* offline */ }
  V.innerHTML = `
    <h2>Feedback</h2>
    <p>Help make CalcLearners better. Answer as many or as few questions as you like.</p>
    <div class="card">
      <p><b>How easy is CalcLearners to use?</b></p>
      <div class="rating" role="radiogroup" aria-label="Ease of use">
        ${[1, 2, 3, 4, 5].map(n => `<button class="ghost" role="radio" aria-checked="false" data-r="${n}">${n}</button>`).join("")}
        <small>1 = confusing, 5 = super easy</small>
      </div>
      ${FEEDBACK_QUESTIONS.map((q, i) => `<label>${q}<textarea id="fb${i}" rows="2"></textarea></label>`).join("")}
      <button id="send">Send feedback</button>
      <p id="fb-msg" class="bad" role="alert"></p>
    </div>
    ${count ? `<small>You've sent ${plural(count, "piece")} of feedback. Thank you!</small>` : ""}`;

  let rating = "";
  V.querySelector(".rating").onclick = e => {
    const b = e.target.closest("[data-r]");
    if (!b) return;
    rating = b.dataset.r;
    $$(".rating button").forEach(x => {
      x.classList.toggle("ghost", x !== b);
      x.setAttribute("aria-checked", x === b);
    });
  };

  $("#send").onclick = async () => {
    const answers = [["How easy is CalcLearners to use? (1-5)", rating],
      ...FEEDBACK_QUESTIONS.map((q, i) => [q, $("#fb" + i).value])];
    try {
      await api("/feedback", { method: "POST", body: { answers } });
      toast("Thanks for the feedback! 💛");
      feedback();
    } catch (e) { $("#fb-msg").textContent = e.message; }
  };
}

// ---------- Theme (light / dark) ----------
function syncTheme() {
  const dark = document.documentElement.dataset.theme === "dark";
  const label = dark ? "Switch to light mode" : "Switch to dark mode";
  $$(".theme-toggle").forEach(b => {
    const text = b.querySelector(".theme-label");
    if (text) text.textContent = label;
    else b.setAttribute("aria-label", label);
  });
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = dark ? "#0F1729" : "#F4F6F9";
}
$$(".theme-toggle").forEach(b => b.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  store("theme", next);
  syncTheme();
}));
syncTheme();

// ==================================================
// HOME PAGE: hero graph, topic search, course map
// ==================================================
const CHEV = `<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"
  stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>`;
const openWeeks = new Set();   // weeks the learner opened by hand
let weeksTouched = false;      // until they do, the week they're on starts open

// The big button: the last lesson visited if it isn't understood yet, otherwise the recommended next one.
function heroLesson() {
  const last = BY_ID[ME.last_topic];
  if (last && !isDone(last.id)) return { lesson: last, resume: true };
  const next = recommendNext();
  return next ? { lesson: next, resume: false } : null;
}

function renderLanding() {
  const cta = $("#cta-main"), note = $("#resume-note");
  if (!LESSONS.length) {
    cta.href = "#/learn";
    cta.textContent = "Browse the course";
    note.textContent = "No sign-up needed. Your progress saves in this browser.";
    return;
  }
  const course = courseLessons();
  const weekCount = new Set(course.map(l => l.week)).size;
  $(".lede").textContent = `${course.length} short lessons across your ${weekCount}-week course, from precalc review to tangent planes. ` +
    "Pick up where you stopped, or jump to the exact topic you're stuck on.";

  const done = course.filter(l => isDone(l.id)).length;
  const pick = heroLesson();
  if (pick) {
    const l = pick.lesson;
    cta.href = "#/learn/" + l.id;
    cta.innerHTML = `${pick.resume ? "Continue" : done ? "Up next" : "Start"}: ${esc(l.name)}
      <small>${l.unit === "Extra" ? "Extra topic" : esc(l.unit)}</small>`;
    note.innerHTML = done
      ? `You've understood <b>${done} of ${course.length}</b> lessons. This one takes about ${l.minutes} minutes.`
      : ME.username ? `Signed in as <b>${esc(ME.username)}</b>. This lesson takes about ${l.minutes} minutes.`
      : `No sign-up needed, and your progress saves in this browser. This lesson takes about ${l.minutes} minutes.`;
  } else {
    cta.href = "#/formulas";
    cta.textContent = "Review the formula sheet";
    note.innerHTML = `You've understood all <b>${course.length}</b> course lessons. Retake a quiz now and then to keep it fresh.`;
  }
  renderWeeks(pick?.lesson);
}

function renderWeeks(current) {
  $("#weeks").innerHTML = units().map(u => {
    const extra = u.label === "Extra topics";
    const total = u.lessons.length;
    const done = u.lessons.filter(l => isDone(l.id)).length;
    const here = !!current && current.week === u.week;
    const state = done === total ? "done" : here ? "current" : "";
    const label = done === total ? "Done" : here ? "You're here" : done ? `${done} of ${total} done`
      : extra ? "Optional" : "Not started";
    const open = weeksTouched ? openWeeks.has(u.week) : here;
    const lessons = u.lessons.map(l => {
      const cls = isDone(l.id) ? "l-done" : current && l.id === current.id ? "l-next" : "";
      const doneText = isDone(l.id) ? `<span class="sr-only"> (understood)</span>` : "";
      const tag = cls === "l-next" ? `<span class="tag">Up next</span>` : "";
      return `<li><a class="${cls}" href="#/learn/${l.id}"><span class="dot" aria-hidden="true"></span>${esc(l.name)}${doneText}${tag}</a></li>`;
    }).join("");
    return `<li class="week ${state} ${open ? "open" : ""}" data-week="${u.week}">
      <button class="week-toggle" type="button" aria-expanded="${open}" aria-controls="wk-${u.week}">
        <span class="w-num" aria-hidden="true">${extra ? "+" : String(u.week).padStart(2, "0")}</span>
        <span class="w-title">${esc(u.title)}<span class="w-sub">${esc(u.label)}, ${plural(total, "lesson")}</span></span>
        <span class="w-state">${label}</span>
        ${CHEV}
      </button>
      <div class="week-lessons" id="wk-${u.week}"><ul>${lessons}</ul></div>
    </li>`;
  }).join("");
}

$("#weeks").addEventListener("click", e => {
  const b = e.target.closest(".week-toggle");
  if (!b) return;
  if (!weeksTouched) {
    weeksTouched = true;
    $$("#weeks .week.open").forEach(w => openWeeks.add(+w.dataset.week));
  }
  const li = b.closest(".week");
  const open = li.classList.toggle("open");
  b.setAttribute("aria-expanded", open);
  if (open) openWeeks.add(+li.dataset.week); else openWeeks.delete(+li.dataset.week);
});

// ---------- "What are you stuck on?" search ----------
const findInput = $("#find"), findList = $("#find-results");

function searchLessons(query) {
  const q = query.trim().toLowerCase();
  const words = q.split(/\s+/).filter(Boolean);
  if (!words.length) return [];
  return LESSONS.map(l => {
    const name = l.name.toLowerCase();
    const hay = (l.name + " " + l.keywords + " " + l.unit_title).toLowerCase();
    if (!words.every(w => hay.includes(w))) return null;
    return { l, rank: name.startsWith(q) ? 0 : name.includes(q) ? 1 : 2 };
  }).filter(Boolean).sort((a, b) => a.rank - b.rank).slice(0, 6).map(x => x.l);
}

function showResults() {
  const q = findInput.value.trim();
  if (!q) { findList.hidden = true; findList.innerHTML = ""; return; }
  if (!LESSONS.length) {
    findList.innerHTML = `<li class="none">Lessons load from the server. Start it with <code>python server.py</code>, then refresh.</li>`;
  } else {
    const hits = searchLessons(q);
    findList.innerHTML = hits.length
      ? hits.map(l => `<li><a href="#/learn/${l.id}">${esc(l.name)}<small>${esc(unitLabel(l))}</small></a></li>`).join("")
      : `<li class="none">No lesson matches "${esc(q)}". Try a shorter word, like "limit", "integral" or "series".</li>`;
  }
  findList.hidden = false;
}

function goFirstResult() {
  showResults();
  const a = findList.querySelector("a");
  if (a) location.hash = a.getAttribute("href");
  else findInput.focus();
}

findInput.addEventListener("input", showResults);
findInput.addEventListener("keydown", e => {
  if (e.key === "Enter") { e.preventDefault(); goFirstResult(); }
  if (e.key === "ArrowDown") {
    const a = findList.querySelector("a");
    if (a) { e.preventDefault(); a.focus(); }
  }
});
findList.addEventListener("keydown", e => {
  const links = [...findList.querySelectorAll("a")];
  const i = links.indexOf(document.activeElement);
  if (i < 0) return;
  if (e.key === "ArrowDown") { e.preventDefault(); links[Math.min(i + 1, links.length - 1)].focus(); }
  if (e.key === "ArrowUp") { e.preventDefault(); (i ? links[i - 1] : findInput).focus(); }
});
$("#find-go").addEventListener("click", goFirstResult);

// ---------- Hero graph: a tangent line that follows your pointer ----------
function startGraph() {
  const svg = $("#graph");
  const W = 640, H = 380, X0 = -1, X1 = 9, Y0 = -1.5, Y1 = 6;
  const f = x => Math.sin(x) + x / 2, df = x => Math.cos(x) + 0.5;
  const sx = x => (x - X0) / (X1 - X0) * W, sy = y => H - (y - Y0) / (Y1 - Y0) * H;
  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, cls, attrs = {}) => {
    const e = document.createElementNS(NS, tag);
    e.setAttribute("class", cls);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    svg.appendChild(e);
    return e;
  };

  for (let x = Math.ceil(X0); x <= X1; x++) el("line", "g-grid", { x1: sx(x), x2: sx(x), y1: 0, y2: H });
  for (let y = Math.ceil(Y0); y <= Y1; y++) el("line", "g-grid", { x1: 0, x2: W, y1: sy(y), y2: sy(y) });
  el("line", "g-axis", { x1: sx(0), x2: sx(0), y1: 0, y2: H });
  el("line", "g-axis", { x1: 0, x2: W, y1: sy(0), y2: sy(0) });
  let d = "";
  for (let i = 0; i <= 400; i++) {
    const x = X0 + (X1 - X0) * i / 400;
    d += (i ? "L" : "M") + sx(x).toFixed(1) + " " + sy(f(x)).toFixed(1);
  }
  el("path", "g-curve", { d });
  const rise = el("path", "g-rise");
  const tan = el("line", "g-tan");
  const dot = el("circle", "g-dot", { r: 7 });

  const xv = $("#xv"), mv = $("#mv");
  let cur = 2, touched = false;
  function setX(x) {
    cur = Math.max(X0 + 0.3, Math.min(X1 - 0.3, x));
    const y = f(cur), m = df(cur), L = 1.6;
    tan.setAttribute("x1", sx(cur - L)); tan.setAttribute("y1", sy(y - m * L));
    tan.setAttribute("x2", sx(cur + L)); tan.setAttribute("y2", sy(y + m * L));
    rise.setAttribute("d", `M${sx(cur)} ${sy(y)} H${sx(cur + 1)} V${sy(y + m)}`);
    dot.setAttribute("cx", sx(cur)); dot.setAttribute("cy", sy(y));
    xv.textContent = "x = " + cur.toFixed(2);
    mv.textContent = (m < -0.005 ? "−" : "") + Math.abs(m).toFixed(2);
  }
  const fromEvent = e => {
    const r = svg.getBoundingClientRect();
    touched = true;
    setX(X0 + (e.clientX - r.left) / r.width * (X1 - X0));
  };
  // Vertical swipes still scroll the page on phones (touch-action: pan-y); taps and sideways drags move the line.
  svg.addEventListener("pointerdown", fromEvent);
  svg.addEventListener("pointermove", e => { if (e.pointerType === "mouse" || e.pressure > 0) fromEvent(e); });
  svg.addEventListener("keydown", e => {
    const step = { ArrowRight: 0.1, ArrowUp: 0.1, ArrowLeft: -0.1, ArrowDown: -0.1 }[e.key];
    if (step === undefined) return;
    e.preventDefault();
    touched = true;
    setX(cur + step);
  });
  if (matchMedia("(pointer: coarse)").matches) $("#graph-hint").textContent = "Tap or drag along the graph";

  if (window.katex) {
    try {
      katex.render("f(x) = \\sin x + \\tfrac{x}{2}", $("#fx-label"), { throwOnError: false });
      katex.render("\\tfrac{d}{dx}f(g(x)) = f'(g(x))\\,g'(x)", $("#tool-formula"), { throwOnError: false });
    } catch (e) { /* the plain-text versions stay */ }
  }

  // The one orchestrated moment: on load the tangent rides along the curve once.
  if ($("#landing").hidden || matchMedia("(prefers-reduced-motion: reduce)").matches) { setX(2); return; }
  const t0 = performance.now(), dur = 2600;
  (function step(t) {
    if (touched) return;
    const p = Math.min(1, (t - t0) / dur), ease = 1 - Math.pow(1 - p, 3);
    setX(ease * 6.6);
    if (p < 1) requestAnimationFrame(step);
  })(t0);
}

// ---------- Start ----------
(async function init() {
  await useLocalServer();
  try {
    ME = await api("/me");
    // The server now holds our ID in its cookie, so the old copy can go.
    if (LEGACY_UID) { try { localStorage.removeItem("uid"); } catch (e) { /* blocked */ } LEGACY_UID = null; }
    LESSONS = await api("/lessons");
    BY_ID = Object.fromEntries(LESSONS.map(l => [l.id, l]));
  } catch (e) {
    if (e.status === 403) $("#banner").textContent = e.message;  // this browser was blocked
    offline();
  }
  updateProgress();
  updateAccountLinks();
  route();
  startGraph();
  // A message left by restart() just before the page reloaded.
  try {
    const flash = sessionStorage.getItem("flash");
    if (flash) { sessionStorage.removeItem("flash"); toast(flash); }
  } catch (e) { /* private window */ }
})();
