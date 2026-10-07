/* CalcBot: the study helper chat on every page. It opens as a panel down the side of the
 * screen, or as a small window in the corner for anyone who prefers that.
 *
 * A conversation lasts until the chat is closed: opening it again starts a new one. Nothing
 * is kept of it, in the browser or on the server.
 * A message can carry one picture, when CalcBot's AI is on. A picture is shrunk here before
 * it is sent, is never stored, and stays in the chat only if CalcBot finds it is about math,
 * studying or this site.
 * Replies use the same safe markup as the reading lessons (see reader.js), plus
 * [text](#/page) links to pages of this site.
 * The mascot who pops up from behind the message bar shows what CalcBot is up to (see pose).
 */
(function () {
  "use strict";
  const panel = $("#chat"), log = $("#chat-log"), chips = $("#chat-chips");
  const input = $("#chat-input"), fab = $("#chat-open");
  const file = $("#chat-file"), attach = $("#chat-attach"), tray = $("#chat-pic");
  const sizeBtn = $("#chat-size"), bot = $("#mascot");
  const SEND = 16;   // how many messages go along with a new one, for context
  const SIDE = 1568; // the longest side of a picture once shrunk, in pixels
  const phone = matchMedia("(max-width: 640px)");
  let turns = [];    // [{ role: "user" | "assistant", content, pic: true if a picture went with it }]
  let picture = "";  // the picture waiting to be sent, as a data: URL
  let busy = false;
  let chat = 0;      // which conversation this is: a reply to one that has been closed is dropped
  let botTimer = 0;  // sends the mascot away once he has waved or had his idea

  // Earlier versions kept the conversation in session storage: clear what a tab still has.
  try { sessionStorage.removeItem("chat"); } catch (e) { /* private window */ }

  // The side panel, unless the small window was picked last time.
  function setSize(big) {
    document.body.classList.toggle("chat-big", big);
    const label = big ? "Make the chat smaller" : "Make the chat bigger";
    sizeBtn.setAttribute("aria-label", label);
    sizeBtn.title = label;
  }
  setSize(store("chat-size") !== "small");

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
  // The student's message, under the picture sent with it.
  function show(text, pic) {
    const el = add("user", esc(text));
    if (pic) {
      const img = new Image();
      img.alt = "The picture you sent";
      img.src = pic;
      el.prepend(img);
    }
    return el;
  }

  // Only CalcBot's AI can look at a picture, and the server says whether that is on.
  const canSee = () => !!ME.chat_pictures;

  // Whether it can comes with the visitor's details, which may still be on their way when
  // the chat is opened: keep checking until they arrive.
  function syncAttach() {
    attach.hidden = !canSee();
    if (!("chat_pictures" in ME) && !panel.hidden) setTimeout(syncAttach, 400);
  }

  // The mascot pops up from behind the message bar in one of four poses: "wave" when a chat
  // starts, "watch" while a message is typed, "think" while an answer is on its way, "idea"
  // when it lands. Unless he is thinking he ducks down again after a moment, so that he
  // doesn't sit on top of the messages.
  function pose(name, ms) {
    clearTimeout(botTimer);
    // The chat may have only just appeared: he starts from out of sight.
    if (!bot.classList.contains("in")) void bot.offsetWidth;
    bot.classList.remove("wave", "watch", "think", "idea");
    bot.classList.add("in", name);
    if (ms) botTimer = setTimeout(leave, ms);
  }
  function leave() {
    clearTimeout(botTimer);
    bot.classList.remove("in");
  }

  function welcome() {
    add("assistant", render("Hi! I'm **CalcBot**. Ask me a math question, how to study for a test, or how this site works."
      + (canSee() ? " You can also send a picture of a problem, your notes or this site." : "")));
    const lesson = BY_ID[currentTopicId()];
    const ideas = [lesson ? `Explain ${lesson.name} simply` : "What is the chain rule?",
      "How do I prepare for a calculus test?", "How does this site work?"];
    chips.innerHTML = ideas.map(q => `<button type="button">${esc(q)}</button>`).join("");
    chips.hidden = false;
  }

  // A new conversation: every time the chat is opened, and from its "Start a new chat" button.
  function start() {
    chat++;
    turns = [];
    busy = false;
    setPicture("");
    log.innerHTML = "";
    welcome();
    pose("wave", 3600);
  }

  // The box grows with the message, up to a few lines.
  function grow() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight + 2, 120) + "px";
  }

  // Shrink a picture and re-save it as a JPEG. That keeps the upload small, and leaves behind
  // what a photo file carries with it, such as where it was taken.
  function shrink(f) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader(), img = new Image();
      reader.onerror = img.onerror = reject;
      reader.onload = () => { img.src = reader.result; };
      img.onload = () => {
        const k = Math.min(1, SIDE / Math.max(img.naturalWidth, img.naturalHeight));
        const c = document.createElement("canvas");
        c.width = Math.max(1, Math.round(img.naturalWidth * k));
        c.height = Math.max(1, Math.round(img.naturalHeight * k));
        const g = c.getContext("2d");
        g.fillStyle = "#fff";  // JPEG has no see-through, which would come out black
        g.fillRect(0, 0, c.width, c.height);
        g.drawImage(img, 0, 0, c.width, c.height);
        resolve(c.toDataURL("image/jpeg", 0.85));
      };
      reader.readAsDataURL(f);
    });
  }

  function setPicture(url) {
    picture = url;
    tray.hidden = !url;
    if (url) $("#chat-pic-img").src = url; else $("#chat-pic-img").removeAttribute("src");
  }

  async function attachPicture(f) {
    if (!f || busy) return;
    if (!f.type.startsWith("image/")) return toast("That file isn't a picture.");
    if (f.size > 25e6) return toast("That picture is too big. Try a smaller one or a screenshot.");
    try { setPicture(await shrink(f)); }
    catch (e) { toast("That picture couldn't be opened. Try a screenshot or a photo."); }
    input.focus();
  }

  // The picture didn't stay in the chat: it couldn't be sent or read, or it wasn't about math.
  function dropPicture(turn, el) {
    delete turn.pic;
    const tag = document.createElement("span");
    tag.className = "chat-pic-tag";
    tag.textContent = "Picture removed";
    el.querySelector("img").replaceWith(tag);
  }

  async function send(text) {
    text = text.trim();
    const pic = picture;
    if ((!text && !pic) || busy) return;
    busy = true;
    chips.hidden = true;
    const id = chat;
    const turn = { role: "user", content: text || "Can you help me with this?" };
    if (pic) turn.pic = true;
    turns.push(turn);
    const mine = show(turn.content, pic);
    setPicture("");
    input.value = "";
    grow();
    const reply = add("assistant", `<span class="typing" role="img" aria-label="CalcBot is thinking"><i></i><i></i><i></i></span>`);
    pose("think");
    // Only the newest picture is sent, so earlier ones are pointed out in words.
    const messages = turns.slice(-SEND).map(t => ({ role: t.role, content: t.pic && t !== turn
      ? "[I sent a picture with this message. You can't see it any more.]\n" + t.content : t.content }));
    try {
      const r = await api("/chat", { method: "POST", body: {
        messages, image: pic || undefined, lesson: currentTopicId() || "", page: parseHash().view || "home" } });
      if (id !== chat) return;  // the chat was closed or started over while CalcBot was thinking
      turns.push({ role: "assistant", content: r.reply });
      reply.innerHTML = render(r.reply);
      if (pic && !r.picture) dropPicture(turn, mine);
      pose("idea", 2600);
    } catch (e) {
      if (id !== chat) return;
      // The message stays in the chat, so the next one sent carries it along.
      reply.classList.add("err");
      reply.textContent = e.message;
      if (pic) dropPicture(turn, mine);
      leave();
    }
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
    syncAttach();
    start();
    fit();
    log.scrollTop = log.scrollHeight;
    input.focus();
  }

  function close(restoreFocus) {
    panel.hidden = true;
    fab.setAttribute("aria-expanded", "false");
    document.body.classList.remove("chat-open");
    leave();
    if (restoreFocus) fab.focus();
  }

  fab.addEventListener("click", open);
  $("#chat-close").addEventListener("click", () => close(true));
  sizeBtn.addEventListener("click", () => {
    const big = !document.body.classList.contains("chat-big");
    setSize(big);
    store("chat-size", big ? "big" : "small");
    log.scrollTop = log.scrollHeight;
  });
  $("#chat-new").addEventListener("click", () => { start(); input.focus(); });
  attach.addEventListener("click", () => file.click());
  file.addEventListener("change", () => { attachPicture(file.files[0]); file.value = ""; });
  $("#chat-pic-remove").addEventListener("click", () => { setPicture(""); input.focus(); });
  // A screenshot is usually pasted, not saved to a file first.
  input.addEventListener("paste", e => {
    const f = canSee() && [...(e.clipboardData?.files || [])].find(x => x.type.startsWith("image/"));
    if (f) { e.preventDefault(); attachPicture(f); }
  });
  $("#chat-form").addEventListener("submit", e => { e.preventDefault(); send(input.value); });
  input.addEventListener("input", grow);
  input.addEventListener("input", () => { if (!busy) pose("watch", 1500); });
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
