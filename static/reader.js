/* CalcLearners reader: the text version of a video episode.
 *
 * Articles use a small, safe markup (all text is HTML-escaped):
 *   ## Heading          section heading
 *   - item / 1. item    lists
 *   **bold**  *italic*  bold, italic
 *   > text              tip / common-mistake callout
 *   \( x \)  \[ x \]    inline / display math (KaTeX)
 *   ::: example Title   worked example: numbered steps, then "Answer: ..."
 *   ::: figure N        still picture of scene N of the episode, then a caption
 *   ::: try Question    try-it question; the body is the hidden answer
 *   :::                 ends a block
 */
window.Reader = (function () {
  "use strict";
  const { tex } = window.VideoPlayer;

  const esc = s => String(s ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // Text with inline/display math, **bold** and *italic*. A lone star, as in "2 * 3", is left alone:
  // italics must hug their words and start after a space or bracket.
  function inline(s) {
    return String(s ?? "").split(/(\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\))/).map((part, i) => {
      if (i % 2) return tex(part.slice(2, -2), part.startsWith("\\["));
      return esc(part).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
        .replace(/(^|[\s(;>])\*(?!\s)([^*\n]+?)\*(?=[\s).,!?:;&<]|$)/g,
          (all, lead, words) => /\s$/.test(words) ? all : `${lead}<i>${words}</i>`);
    }).join("");
  }

  function example(title, body, stepByStep) {
    const steps = [], intro = [];
    let answer = "";
    for (const line of body) {
      const step = line.match(/^\d+\.\s+(.*)/);
      if (step) steps.push(step[1]);
      else if (/^Answer:/i.test(line)) answer = line.replace(/^Answer:\s*/i, "");
      else if (line.trim()) intro.push(line);
    }
    const hide = stepByStep && steps.length ? " hidden" : "";
    return `<div class="ex-block${stepByStep ? " step-mode" : ""}">
      <div class="ex-title">✍️ ${inline(title)}</div>
      ${intro.length ? `<p>${inline(intro.join(" "))}</p>` : ""}
      <ol class="ex-steps">${steps.map(s => `<li${hide}>${inline(s)}</li>`).join("")}</ol>
      ${answer ? `<p class="ex-answer"${hide}><b>Answer:</b> ${inline(answer)}</p>` : ""}
      ${hide ? `<div class="row"><button class="small ex-next">Show step 1 of ${steps.length}</button>
        <button class="ghost small ex-all">Show all</button></div>
        <small class="muted">Try to predict each step before you reveal it.</small>` : ""}
    </div>`;
  }

  function render(src, opts = {}) {
    const lines = String(src ?? "").replace(/\r/g, "").split("\n");
    const out = [];
    let para = [], list = null;
    const flush = () => {
      if (para.length) { out.push(`<p>${inline(para.join(" "))}</p>`); para = []; }
      if (list) { out.push(`<${list.tag}>${list.items.map(i => `<li>${inline(i)}</li>`).join("")}</${list.tag}>`); list = null; }
    };
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      const block = line.match(/^:::\s*(example|figure|try)\b\s*(.*)$/);
      if (block) {
        flush();
        const body = [];
        while (++i < lines.length && lines[i].trim() !== ":::") body.push(lines[i].trim());
        const [, kind, arg] = block;
        if (kind === "example") out.push(example(arg, body, opts.stepByStep));
        if (kind === "figure") out.push(`<figure class="fig" data-scene="${parseInt(arg, 10)}">
          <div class="fig-stage"></div>${body.join(" ").trim() ? `<figcaption>${inline(body.join(" "))}</figcaption>` : ""}</figure>`);
        if (kind === "try") out.push(`<details class="try"><summary><b>✏️ Try it:</b> ${inline(arg)}</summary>
          <div>${inline(body.join(" "))}</div></details>`);
        continue;
      }
      if (!line) { flush(); continue; }
      const h = line.match(/^(#{2,3})\s+(.*)/);
      if (h) { flush(); out.push(`<h${h[1].length + 1} class="ar-h">${inline(h[2])}</h${h[1].length + 1}>`); continue; }
      if (line.startsWith("> ")) { flush(); out.push(`<div class="callout">${inline(line.slice(2))}</div>`); continue; }
      const li = line.match(/^(-|\d+\.)\s+(.*)/);
      if (li) {
        const tag = li[1] === "-" ? "ul" : "ol";
        if (para.length || (list && list.tag !== tag)) flush();
        list = list || { tag, items: [] };
        list.items.push(li[2]);
        continue;
      }
      if (list) flush();
      para.push(line);
    }
    flush();
    return out.join("\n");
  }

  // Bring a rendered article to life: still figures and step-by-step examples.
  function hydrate(root, episode) {
    root.querySelectorAll(".fig").forEach(fig => {
      const scene = episode.scenes[+fig.dataset.scene];
      if (scene) window.VideoPlayer.staticScene(scene, fig.querySelector(".fig-stage"));
      else fig.remove();
    });
    root.querySelectorAll(".ex-block.step-mode").forEach(ex => {
      const steps = [...ex.querySelectorAll(".ex-steps li")];
      const next = ex.querySelector(".ex-next"), all = ex.querySelector(".ex-all");
      if (!next) return;
      let shown = 0;
      const upTo = n => {
        while (shown < n && shown < steps.length) steps[shown++].hidden = false;
        if (shown >= steps.length) {
          const ans = ex.querySelector(".ex-answer");
          if (ans) ans.hidden = false;
          next.parentElement.remove();
          ex.querySelector("small.muted")?.remove();
        } else next.textContent = `Show step ${shown + 1} of ${steps.length}`;
      };
      next.onclick = () => upTo(shown + 1);
      all.onclick = () => upTo(steps.length);
    });
  }

  // Fallback for lessons without a written article: build one from the scenes.
  function fromScenes(ep) {
    const md = [];
    ep.scenes.forEach((s, i) => {
      if (s.type === "title") return;
      if (s.heading) md.push("## " + s.heading);
      const say = s.beats.map(b => b.say).join(" ");
      if (s.type === "equation") md.push(say, "", ...s.lines.map(l => `\\[${l}\\]`));
      else if (s.type === "cards") md.push(...s.items.map(c => `- **${c.title}:** ${c.text}`));
      else if (s.type === "compare") md.push(say, "", `\\[${s.left.lines.join(" ")}\\]`, "", `\\[${s.right.lines.join(" ")}\\]`);
      else if (s.type === "pause") md.push(`::: try \\(${s.question}\\)`, `\\(${s.answer}\\)`, ":::");
      else md.push(say, "", `::: figure ${i}`, ":::");
      md.push("");
    });
    return md.join("\n");
  }

  // Reading time: 200 words a minute plus about 4 seconds per formula
  // (keep in sync with read_minutes in videos/__init__.py).
  function minutes(src) {
    const math = /\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)/g;
    const s = String(src ?? "");
    const formulas = (s.match(math) || []).length;
    const words = s.replace(math, " ").split(/\s+/).filter(Boolean).length;
    return Math.max(1, Math.round(words / 200 + formulas * 4 / 60));
  }

  return { render, hydrate, fromScenes, minutes };
})();
