/* The roadmap (#/path), the skip test (#/skip/<week>) and the Start here page (#/start).
 *
 * The roadmap lays the course out as one winding path, a unit per week. A lesson unlocks when
 * everything it builds on is complete, the way letters come before words: the lessons'
 * "prereqs" decide that, so the path can't drift out of step with them. Completing a lesson
 * means passing its quiz (or marking it as understood). Nothing is ever truly closed: a locked
 * lesson says what it is waiting for and can still be opened, because some people arrive
 * needing one topic for class tomorrow.
 *
 * Each week ends in a checkpoint. Someone who already knows the week can take its skip test
 * there: two quiz questions from every lesson, and 80% completes the whole week.
 *
 * CalcBot's mascot (the drawing in index.html) stands beside the lesson you're on.
 * Loaded before app.js; everything here runs later, from its router.
 */

// How far each stop in a week sits to the left or right of the middle: one swing of the path.
const PATH_WAVE = [0, 0.72, 1, 0.72, 0, -0.72, -1, -0.72];

const pathIcon = d => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;
const PATH_ICONS = {
  passed: pathIcon(`<path fill="currentColor" d="M12 3.2l2.7 5.5 6 .9-4.4 4.2 1.1 6-5.4-2.9-5.4 2.9 1.1-6-4.4-4.2 6-.9z"/>`),
  done: pathIcon(`<path fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" d="M5 12.5l4.5 4.5L19 7.5"/>`),
  open: pathIcon(`<path fill="currentColor" d="M9 6.2v11.6l9.4-5.8z"/>`),
  locked: pathIcon(`<g fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="5.5" y="11" width="13" height="9" rx="2"/><path d="M8.5 11V8a3.5 3.5 0 0 1 7 0v3"/></g>`),
  flag: pathIcon(`<path fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" d="M6 21V4h11l-2.2 4 2.2 4H6"/>`)
};
PATH_ICONS.started = PATH_ICONS.open;

// Where a lesson stands for this learner.
function lessonState(l) {
  if (isDone(l.id)) return passedQuiz(l.id) ? "passed" : "done";
  if (!l.prereqs.every(isDone)) return "locked";
  return ME.quiz[l.id] || ME.last_topic === l.id ? "started" : "open";
}
const STATE_WORDS = { passed: "Quiz passed", done: "Marked as understood", started: "In progress", open: "Ready to start", locked: "Locked" };

function pathView() {
  if (!LESSONS.length) return serverMissing();
  const course = courseLessons();
  const done = course.filter(l => isDone(l.id)).length;
  const stars = course.filter(l => isDone(l.id) && passedQuiz(l.id)).length;
  const here = heroLesson()?.lesson || null;
  const showExtra = store("path-extra") === "1" || (here && here.unit === "Extra");

  const node = (l, i) => {
    const state = lessonState(l), cur = here && l.id === here.id;
    return `<li class="stop ${state} ${cur ? "here" : ""}" style="--k:${PATH_WAVE[i % PATH_WAVE.length]}">
      <button class="node" type="button" data-lesson="${l.id}" aria-haspopup="dialog"
        aria-label="${esc(l.name)}: ${STATE_WORDS[state]}${cur ? ". You are here" : ""}">${PATH_ICONS[state]}</button>
      <span class="stop-name" aria-hidden="true">${esc(l.name)}</span>
    </li>`;
  };
  const unit = u => {
    const extra = u.label === "Extra topics";
    const total = u.lessons.length, count = u.lessons.filter(l => isDone(l.id)).length;
    const head = `<header class="unit-head ${count === total ? "complete" : ""}">
        <div><small>${esc(u.label)}</small><h3>${esc(u.title)}</h3></div>
        <span class="unit-count">${count === total ? "Complete" : `${count} of ${total} done`}</span>
        <div class="bar" role="progressbar" aria-valuenow="${count}" aria-valuemax="${total}" aria-label="${esc(u.label)} progress"><i style="width:${100 * count / total}%"></i></div>
      </header>`;
    if (extra && !showExtra) {
      return `<section class="unit">${head}
        <p class="unit-note">${total} optional topics from later courses: more integration, series, vectors and vector calculus.
          <button class="link" type="button" id="path-extra">Show them on the roadmap</button></p></section>`;
    }
    const check = extra ? "" : `<li class="stop check ${count === total ? "complete" : ""}" style="--k:${PATH_WAVE[total % PATH_WAVE.length]}">
        <button class="node" type="button" data-check="${u.week}" aria-haspopup="dialog"
          aria-label="${esc(u.label)} checkpoint${count === total ? ": complete" : ""}">${PATH_ICONS.flag}</button>
        <span class="stop-name" aria-hidden="true">${esc(u.label)} checkpoint</span>
      </li>`;
    return `<section class="unit">${head}
      <svg class="path-line" aria-hidden="true"></svg>
      <ol class="stops">${u.lessons.map(node).join("")}${check}</ol></section>`;
  };

  V.innerHTML = `
    <h2>Roadmap</h2>
    <p class="path-intro">Calculus builds like a language: letters before words, words before sentences. Each lesson
      unlocks the ones that build on it, so the path always shows what you're ready for. Pass a lesson's quiz to
      complete it.</p>
    <p class="path-stats"><b>${done} of ${course.length}</b> lessons complete${stars ? `, <b>${stars}</b> with the quiz passed` : ""}${
      ME.streak > 1 ? `. <b>${ME.streak}</b> days in a row` : ""}.
      ${here ? `<button class="link" type="button" id="path-jump">Go to my place</button>` : ""}</p>
    <div class="legend path-legend" aria-hidden="true">
      <span><i class="lg-done"></i>Complete</span><span><i class="lg-now"></i>You're here</span>
      <span><i class="lg-open"></i>Ready</span><span><i class="lg-lock"></i>Locked</span>
    </div>
    <div class="path" id="path">
      ${units().map(unit).join("")}
      <div class="path-pop" id="path-pop" role="dialog" aria-label="Lesson details" tabindex="-1" hidden></div>
    </div>
    <p class="path-foot"><a href="#/learn">See every lesson as a list</a> · New here? <a href="#/start">Start here</a></p>`;

  const path = $("#path"), pop = $("#path-pop");
  let opener = null;  // the stop whose details are showing

  // The line through a week's stops: an S-curve from each one to the next, solid as far as you've got.
  const drawLines = () => {
    path.querySelectorAll(".unit").forEach(section => {
      const svg = section.querySelector(".path-line");
      if (!svg) return;
      const box = section.getBoundingClientRect();
      const stops = [...section.querySelectorAll(".stop")];
      const pts = stops.map(s => {
        const r = s.querySelector(".node").getBoundingClientRect();
        return [r.left + r.width / 2 - box.left, r.top + r.height / 2 - box.top];
      });
      svg.innerHTML = pts.slice(1).map(([x, y], i) => {
        const [px, py] = pts[i], mid = (py + y) / 2;
        const walked = stops[i].matches(".passed, .done");
        return `<path class="${walked ? "walked" : ""}" d="M${px.toFixed(1)} ${py.toFixed(1)}C${px.toFixed(1)} ${mid.toFixed(1)} ${x.toFixed(1)} ${mid.toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)}"/>`;
      }).join("");
    });
  };

  const closePop = refocus => {
    if (pop.hidden) return;
    pop.hidden = true;
    if (refocus && opener) opener.querySelector(".node").focus();
    opener = null;
  };
  // Shows the details card under a stop, with its arrow pointing at the stop.
  const openPop = (stop, html) => {
    opener = stop;
    pop.innerHTML = html + `<button class="icon-btn pop-close" type="button" aria-label="Close">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button>`;
    pop.hidden = false;
    math(pop);
    const box = path.getBoundingClientRect(), r = stop.querySelector(".node").getBoundingClientRect();
    const cx = r.left + r.width / 2 - box.left;
    const left = Math.max(4, Math.min(cx - pop.offsetWidth / 2, box.width - pop.offsetWidth - 4));
    pop.style.left = left + "px";
    pop.style.top = stop.querySelector(".stop-name").getBoundingClientRect().bottom - box.top + 14 + "px";
    pop.style.setProperty("--ax", cx - left + "px");
    pop.focus({ preventScroll: true });
    pop.scrollIntoView({ block: "nearest", behavior: "smooth" });
  };

  const lessonCard = l => {
    const state = lessonState(l), q = ME.quiz[l.id];
    const missing = l.prereqs.filter(p => !isDone(p)).map(p => BY_ID[p]);
    const unlocks = LESSONS.filter(x => x.prereqs.includes(l.id) && x.unit !== "Extra").slice(0, 3);
    const status = {
      passed: `Quiz passed, best score ${q?.best}%. This lesson is complete.`,
      done: "You marked this as understood. Pass its quiz to earn the star.",
      started: q ? `In progress. Your best quiz score so far is ${q.best}%.` : "You've opened this one. Pass its quiz to complete it.",
      open: l.prereqs.length ? "Ready: you've finished everything it builds on." : "Ready: it needs nothing before it.",
      locked: `Locked. It builds on ${plural(missing.length, "lesson")} you haven't finished:`
    }[state];
    return `
      <small>${esc(unitLabel(l))}</small>
      <h4>${esc(l.name)}</h4>
      <p class="pop-meta">${badge(l.level)} About ${l.minutes} min</p>
      <p>${status}</p>
      ${state === "locked" ? `<ul class="pop-needs">${missing.map(m => `<li><a href="#/learn/${m.id}">${esc(m.name)}</a></li>`).join("")}</ul>
        <div class="row"><a class="btn" href="#/learn/${missing[0].id}">Start with ${esc(missing[0].name)}</a></div>
        <p class="pop-alt">Need this one for class today? <a href="#/learn/${l.id}">Open it anyway</a></p>`
      : `${unlocks.length && state !== "passed" && state !== "done" ? `<p class="pop-unlocks">Finishing it unlocks ${unlocks.map(x => esc(x.name)).join(", ")}.</p>` : ""}
        <div class="row"><a class="btn" href="#/learn/${l.id}">${{ passed: "Review lesson", done: "Take the quiz", started: "Continue lesson", open: "Start lesson" }[state]}</a></div>`}`;
  };

  const checkCard = week => {
    const u = units().find(x => x.week === week);
    const left = u.lessons.filter(l => !isDone(l.id)).length;
    return `
      <small>${esc(u.label)} checkpoint</small>
      <h4>${esc(u.title)}</h4>
      ${left ? `<p>${plural(left, "lesson")} to go in this week.</p>
        <p>Know this week already? The skip test takes two questions from each lesson. Get 80% and the whole week is
          marked complete.</p>
        <div class="row"><a class="btn" href="#/skip/${week}">Take the skip test</a>
          <a class="btn ghost" href="#/practice/${week}">Practice questions</a></div>`
      : `<p>Week complete. Keep it sharp with the practice set: questions from quick checks to exam level, each with a
          worked solution.</p>
        <div class="row"><a class="btn" href="#/practice/${week}">Open ${esc(u.label)} practice</a></div>`}`;
  };

  path.onclick = e => {
    if (e.target.closest(".pop-close")) return closePop(true);
    if (e.target.closest("#path-extra")) { store("path-extra", "1"); return route(); }
    const bot = e.target.closest(".bot-btn");
    const btn = bot ? path.querySelector(".stop.here .node") : e.target.closest(".node");
    if (!btn) { if (!e.target.closest(".path-pop")) closePop(false); return; }
    const stop = btn.closest(".stop");
    if (stop === opener) return closePop(false);
    openPop(stop, btn.dataset.lesson ? lessonCard(BY_ID[btn.dataset.lesson]) : checkCard(+btn.dataset.check));
  };
  path.onkeydown = e => { if (e.key === "Escape" && !pop.hidden) { e.stopPropagation(); closePop(true); } };

  // CalcBot's mascot beside the stop you're on, with the lesson you just finished celebrated first.
  const hereStop = path.querySelector(".stop.here");
  const seen = new Set((sessionRead("path-done") || "").split(",").filter(Boolean));
  const fresh = sessionRead("path-done") === null ? [] : ME.done.filter(id => !seen.has(id));
  sessionWrite("path-done", ME.done.join(","));
  if (hereStop && $("#mascot svg")) {
    const k = +hereStop.style.getPropertyValue("--k");
    const say = fresh.length ? "Nice work! This one's next." : !ME.done.length && !Object.keys(ME.quiz).length ? "Start here!" : "You're here. Keep going!";
    hereStop.insertAdjacentHTML("beforeend", `<div class="path-bot ${k > 0 ? "left" : "right"}">
      <span class="bot-say">${say}</span>
      <button class="bot-btn" type="button" aria-label="CalcBot says: ${say} Show this lesson."><span class="mascot in ${fresh.length ? "idea" : "wave"}"></span></button>
    </div>`);
    const bot = hereStop.querySelector(".mascot");
    bot.appendChild($("#mascot svg").cloneNode(true));
    setTimeout(() => bot.classList.remove("wave", "idea"), 3200);  // then he stands still
  }
  for (const id of fresh) path.querySelector(`[data-lesson="${id}"]`)?.closest(".stop").classList.add("just-done");
  if (fresh.length && window.VideoPlayer && !matchMedia("(prefers-reduced-motion: reduce)").matches) VideoPlayer.confetti(path);

  const toHere = smooth => hereStop?.scrollIntoView({ block: "center", behavior: smooth ? "smooth" : "auto" });
  const jump = $("#path-jump");
  if (jump) jump.onclick = () => { toHere(true); hereStop.querySelector(".node").focus({ preventScroll: true }); };

  drawLines();
  // Fonts and the mascot can shift the stops a little after the first draw.
  requestAnimationFrame(() => { drawLines(); if (ME.done.length || ME.last_topic) toHere(false); });
  pathView.redraw = () => { if (document.body.contains(path)) { closePop(false); drawLines(); } };
}
window.addEventListener("resize", () => pathView.redraw && pathView.redraw());

// sessionStorage that never throws (private windows can block it).
function sessionRead(key) { try { return sessionStorage.getItem(key); } catch (e) { return null; } }
function sessionWrite(key, value) { try { sessionStorage.setItem(key, value); } catch (e) { /* blocked */ } }

// ---------- Skip test (#/skip/<week>) ----------
function skipTest(arg) {
  if (!LESSONS.length) return serverMissing();
  const u = units().find(x => x.week === +arg && x.label !== "Extra topics");
  if (!u) return pathView();
  // Two questions from each lesson, different ones each time.
  const pick = (list, n) => choiceOrder(list.map(() => "")).slice(0, n).map(i => list[i]);
  const qs = u.lessons.flatMap(l => pick(l.quiz, 2).map(q => ({ q, lesson: l })));
  const need = Math.ceil(qs.length * 0.8);
  let answered = 0, correct = 0;
  const missed = new Set();

  V.innerHTML = `
    <div class="crumbs"><a href="#/path">Roadmap</a><span>${esc(u.label)}</span></div>
    <h2>Skip test: ${esc(u.title)}</h2>
    <p>Already know this week? Get at least <b>${need} of ${qs.length}</b> right and every lesson in ${esc(u.label)} is
      marked complete, which unlocks what comes after. If you fall short nothing is lost: you'll see which lessons
      to read first.</p>
    <div class="card" id="skip-quiz">
      ${qs.map(({ q }, i) => `<div class="qq" data-i="${i}">
        <p><b>${i + 1}.</b> ${q.q}</p>
        <div class="choices">${choiceOrder(q.choices).map(j => `<button class="choice" data-j="${j}">${asMath(q.choices[j])}</button>`).join("")}</div>
        <p class="why" hidden></p>
      </div>`).join("")}
      <div id="skip-result"></div>
    </div>`;

  $("#skip-quiz").onclick = async e => {
    const btn = e.target.closest(".choice");
    const qq = btn?.closest(".qq");
    if (!btn || qq.dataset.answered) return;
    qq.dataset.answered = "1";
    const { q, lesson } = qs[qq.dataset.i];
    const right = +btn.dataset.j === q.answer;
    answered++;
    if (right) correct++; else missed.add(lesson);
    qq.querySelectorAll(".choice").forEach(b => {
      b.disabled = true;
      if (+b.dataset.j === q.answer) b.classList.add("right");
    });
    if (!right) btn.classList.add("wrong");
    const why = qq.querySelector(".why");
    why.hidden = false;
    why.innerHTML = `<b class="${right ? "ok" : "bad"}">${right ? "Correct!" : "Not quite."}</b> ${q.why}`;
    math(why);
    if (answered < qs.length) return;

    const passed = correct >= need, res = $("#skip-result");
    if (passed) {
      try {
        for (const l of u.lessons) if (!isDone(l.id)) await setDone(l.id, true);
      } catch (err) { toast("Couldn't save your progress: " + err.message); return; }
    }
    res.innerHTML = `
      <div class="result ${passed ? "good" : ""}">
        <div class="score">${correct}/${qs.length}</div>
        <div>${passed ? `<b>You passed.</b> ${esc(u.label)} is complete, and the lessons that build on it are unlocked.`
          : `<b>Not this time.</b> You needed ${need}. These lessons had a question you missed, so start with them:`}</div>
      </div>
      ${passed ? "" : `<div class="chips">${[...missed].map(l => `<a class="chip" href="#/learn/${l.id}">${esc(l.name)}</a>`).join("")}</div>`}
      <div class="row">
        <a class="btn" href="#/path">Back to the roadmap</a>
        ${passed ? "" : `<button class="ghost" type="button" id="skip-again">Try again with new questions</button>`}
      </div>`;
    const again = $("#skip-again");
    if (again) again.onclick = () => { skipTest(arg); math(V); window.scrollTo(0, 0); };
    res.scrollIntoView({ block: "nearest", behavior: "smooth" });
  };
}

// ---------- Start here (#/start) ----------
function startPage() {
  if (!LESSONS.length) return serverMissing();
  const course = courseLessons();
  const first = recommendNext() || course[0];
  const week1 = course.filter(l => l.week === 1);
  const speed = { view: [0, 6, 0, 20], alt: "Distance against time for a car that is speeding up, with a tangent line you can slide along it",
    curves: [{ f: "0.5*x^2" }], tool: { type: "tangent", start: 2, read: "After {x} s the car has gone {y} m and is doing {m} m/s." } };
  const area = { view: [0, 5, 0, 6], alt: "Rectangles under a speed curve, adding up to the distance travelled",
    curves: [{ f: "0.2*x^2+1" }], tool: { type: "riemann", dom: [0, 4], start: 4, max: 40 } };

  V.innerHTML = `
    <h2>Start here</h2>
    <p class="path-intro">Never done calculus? Good. This page says what it is, what you need before you begin, and how
      to use the site. It takes about five minutes.</p>

    <section class="card">
      <h3>What calculus is</h3>
      <p>Calculus answers two questions about anything that changes.</p>
      <div class="learn-block">
        <h4>How fast is it changing right now?</h4>
        <p>A car's speedometer answers this for distance. On a graph, "how fast" is how steep the curve is at one
          point: the slope of the line that just touches it there. Finding that slope is called taking a
          <b>derivative</b>.</p>
        ${Plot.figure(speed, "Distance against time for a car that keeps speeding up. Slide the point: the steeper the curve, the faster the car.")}
      </div>
      <div class="learn-block">
        <h4>How much has built up in total?</h4>
        <p>If you know the speed at every moment, how far did the car go? On a graph that total is the area under the
          curve, and you can get at it by adding up thin rectangles. Finding it exactly is called taking an
          <b>integral</b>.</p>
        ${Plot.figure(area, "Speed against time. The rectangles add up to roughly the distance travelled. More rectangles, better answer.")}
      </div>
      <div class="learn-block">
        <h4>The idea that makes both work</h4>
        <p>Both pictures rely on the same trick: get closer and closer to something you can't compute directly (a slope
          at one single point, an area under a curve) and see what your answers are heading for. That target is a
          <b>limit</b>, and it is the first thing the course teaches.</p>
      </div>
    </section>

    <section class="card">
      <h3>What you need first</h3>
      <p>Calculus itself is a handful of ideas. Most mistakes in it are algebra mistakes, so the course opens with a
        review week:</p>
      <div class="chips">${week1.map(l => `<a class="chip ${isDone(l.id) ? "done" : ""}" href="#/learn/${l.id}">${isDone(l.id) ? "✓ " : ""}${esc(l.name)}</a>`).join("")}</div>
      <p class="start-skip">Comfortable with all of that? <a href="#/skip/1">Take the Week 1 skip test</a>: ten
        questions, and 80% moves you straight on to limits.</p>
    </section>

    <section class="card">
      <h3>How a lesson works</h3>
      <ol class="start-steps">
        <li><b>Read the big idea.</b> The first lessons explain everything from zero, with graphs you can drag.</li>
        <li><b>Step through the worked examples.</b> Guess each step before you reveal it.</li>
        <li><b>Do the practice on paper.</b> Hints first, then the answer, then the worked steps.</li>
        <li><b>Pass the quiz.</b> That completes the lesson and unlocks the ones that build on it.</li>
      </ol>
      <p>${course.length} lessons at about 20 to 30 minutes each. Three or four a week gets you through in a term.
        Stuck on something? Ask CalcBot (the button in the corner) or post on the <a href="#/forum">Q&amp;A forum</a>.</p>
    </section>

    <div class="row start-go">
      <a class="btn btn-lg" href="#/path">Open the roadmap</a>
      ${first ? `<a class="btn btn-lg ghost" href="#/learn/${first.id}">Go to ${esc(first.name)}</a>` : ""}
    </div>`;
  Plot.hydrate(V);
}