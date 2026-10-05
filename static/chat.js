/* CalcBot: the study helper chat in the corner of every page.
 *
 * The conversation lives in this tab only (session storage); the server keeps none of it.
 * Replies use the same safe markup as the reading lessons (see reader.js), plus
 * [text](#/page) links to pages of this site.
 */
(function () {
  "use strict";
  const panel = $("#chat"), log = $("#chat-log"), chips = $("#chat-chips");
  const input = $("#chat-input"), fab = $("#chat-open");
  const KEEP = 40;   // messages remembered in this tab
  const SEND = 16;   // how many of them go along with a new message, for context
  const phone = matchMedia("(max-width: 640px)");
  let turns = [];    // [{ role: "user" | "assistant", content }]
  let busy = false;

  try { turns = JSON.parse(sessionStorage.getItem("chat")) || []; } catch (e) { /* blocked or empty */ }
  if (!Array.isArray(turns)) turns = [];
  const save = () => {
    try { sessionStorage.setItem("chat", JSON.stringify(turns.slice(-KEEP))); } catch (e) { /* private window */ }
  };

  // Reader.render escapes everything; links are added afterwards and may only point inside the site.
  const LINK = /\[([^\]<]+)\]\((#\/[\w\-/?=&.%]*)\)/g;
  const render = text => window.Reader.render(text).replace(LINK, '<a href="$2">$1</a>');

  function add(role, html) {
    const el = document.createElement("div");
    el.className = "chat-msg " + (role === "user" ? "me" : "bot");
    el.innerHTML = html;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
    return el;
  }
  const show = t => add(t.role, t.role === "user" ? esc(t.content) : render(t.content));

  function welcome() {
    add("assistant", render("Hi! I'm **CalcBot**. Ask me a math question, how to study for a test, or how this site works."));
    const lesson = BY_ID[currentTopicId()];
    const ideas = [lesson ? `Explain ${lesson.name} simply` : "What is the chain rule?",
      "How do I prepare for a calculus test?", "How does this site work?"];
    chips.innerHTML = ideas.map(q => `<button type="button">${esc(q)}</button>`).join("");
    chips.hidden = false;
  }

  // The box grows with the message, up to a few lines.
  function grow() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight + 2, 120) + "px";
  }

  async function send(text) {
    text = text.trim();
    if (!text || busy) return;
    busy = true;
    chips.hidden = true;
    turns.push({ role: "user", content: text });
    show(turns[turns.length - 1]);
    input.value = "";
    grow();
    const reply = add("assistant", `<span class="typing" role="img" aria-label="CalcBot is thinking"><i></i><i></i><i></i></span>`);
    try {
      const r = await api("/chat", { method: "POST", body: {
        messages: turns.slice(-SEND), lesson: currentTopicId() || "", page: parseHash().view || "home" } });
      turns.push({ role: "assistant", content: r.reply });
      reply.innerHTML = render(r.reply);
    } catch (e) {
      // The message stays in the chat, so the next one sent carries it along.
      reply.classList.add("err");
      reply.textContent = e.message;
    }
    save();
    busy = false;
    log.scrollTop = reply.offsetTop - 12;  // show the start of the answer, not its end
  }

  // Phones: keep the panel inside the part of the screen the keyboard leaves free.
  function fit() {
    const vv = window.visualViewport;
    const on = vv && !panel.hidden && phone.matches;
    panel.style.top = on ? vv.offsetTop + "px" : "";
    panel.style.height = on ? vv.height + "px" : "";
  }

  function open() {
    panel.hidden = false;
    fab.setAttribute("aria-expanded", "true");
    document.body.classList.add("chat-open");
    if (!log.children.length) {
      if (turns.length) turns.forEach(show); else welcome();
    }
    fit();
    log.scrollTop = log.scrollHeight;
    input.focus();
  }

  function close(restoreFocus) {
    panel.hidden = true;
    fab.setAttribute("aria-expanded", "false");
    document.body.classList.remove("chat-open");
    if (restoreFocus) fab.focus();
  }

  fab.addEventListener("click", open);
  $("#chat-close").addEventListener("click", () => close(true));
  $("#chat-new").addEventListener("click", () => {
    if (busy) return;
    turns = [];
    save();
    log.innerHTML = "";
    welcome();
    input.focus();
  });
  $("#chat-form").addEventListener("submit", e => { e.preventDefault(); send(input.value); });
  input.addEventListener("input", grow);
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });
  chips.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (b) send(b.textContent);
  });
  // On a phone the chat covers the page, so following a link closes it.
  log.addEventListener("click", e => { if (e.target.closest("a") && phone.matches) close(false); });
  panel.addEventListener("keydown", e => { if (e.key === "Escape") { e.stopPropagation(); close(true); } });
  window.visualViewport?.addEventListener("resize", fit);
  window.visualViewport?.addEventListener("scroll", fit);
  phone.addEventListener?.("change", fit);
})();
