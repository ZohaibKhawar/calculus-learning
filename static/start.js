/* The Start here page (#/start) and the skip test (#/skip/<week>).
 *
 * Start here is for someone who has never seen calculus: what it is, the algebra it needs and
 * how a lesson works. The skip test is for someone who already knows a week: two quiz questions
 * from every lesson, and 80% completes the whole week.
 *
 * Loaded before app.js; everything here runs later, from its router.
 */

// ---------- Skip test (#/skip/<week>) ----------
function skipTest(arg) {
  if (!LESSONS.length) return serverMissing();
  const u = units().find(x => x.week === +arg && x.label !== "Extra topics");
  if (!u) return learn();
  // Two questions from each lesson, different ones each time.
  const pick = (list, n) => choiceOrder(list.map(() => "")).slice(0, n).map(i => list[i]);
  const qs = u.lessons.flatMap(l => pick(l.quiz, 2).map(q => ({ q, lesson: l })));
  const need = Math.ceil(qs.length * 0.8);
  let answered = 0, correct = 0;
  const missed = new Set();

  V.innerHTML = `
    <div class="crumbs"><a href="#/learn">All lessons</a><span>${esc(u.label)}</span></div>
    <h2>Skip test: ${esc(u.title)}</h2>
    <p>Already know this week? Get at least <b>${need} of ${qs.length}</b> right and every lesson in ${esc(u.label)} is
      marked complete. If you fall short nothing is lost: you'll see which lessons to read first.</p>
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
        <div>${passed ? `<b>You passed.</b> ${esc(u.label)} is complete.`
          : `<b>Not this time.</b> You needed ${need}. These lessons had a question you missed, so start with them:`}</div>
      </div>
      ${passed ? "" : `<div class="chips">${[...missed].map(l => `<a class="chip" href="#/learn/${l.id}">${esc(l.name)}</a>`).join("")}</div>`}
      <div class="row">
        <a class="btn" href="#/learn">Back to all lessons</a>
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
    <p class="start-intro">Never done calculus? Good. This page says what it is, what you need before you begin, and how
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
        <li><b>Pass the quiz.</b> That completes the lesson.</li>
      </ol>
      <p>${course.length} lessons at about 20 to 30 minutes each. Three or four a week gets you through in a term.
        Stuck on something? Ask CalcBot (the button in the corner) or post on the <a href="#/forum">Q&amp;A forum</a>.</p>
    </section>

    <div class="row start-go">
      <a class="btn btn-lg" href="#/learn">See all the lessons</a>
      ${first ? `<a class="btn btn-lg ghost" href="#/learn/${first.id}">Go to ${esc(first.name)}</a>` : ""}
    </div>`;
  Plot.hydrate(V);
}