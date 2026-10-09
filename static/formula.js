/* Formulas that fit a phone.
 *
 * A "key formula" is often several formulas on one line, set apart by \quad or \qquad. Drawn
 * as one piece it is wider than a phone, and the end is cut off. Here each formula is split
 * into those parts, which sit side by side when there is room and stack when there isn't.
 * A part is drawn as inline math in display style, so a long one can also break after an
 * equals or plus sign. One that still doesn't fit is shrunk a little, and failing that the
 * formula scrolls sideways and fades at the edge to show it.
 * Used by the app (app.js) and by the lesson pages at /lessons (lesson.js).
 */
window.Formula = (function () {
  "use strict";

  // The parts of a formula: split at \quad and \qquad, but never inside { } or \left ... \right.
  function parts(tex) {
    if (/\\begin\{/.test(tex)) return [tex];  // a table of cases stays whole
    const out = [];
    let depth = 0, cur = "";
    for (let i = 0; i < tex.length; i++) {
      const at = word => tex.startsWith(word, i) && !/[a-zA-Z]/.test(tex[i + word.length] || "");
      if (tex[i] === "\\" && (tex[i + 1] === "{" || tex[i + 1] === "}")) { cur += tex[i] + tex[i + 1]; i++; continue; }
      if (tex[i] === "{" || at("\\left")) depth++;
      if (tex[i] === "}" || at("\\right")) depth--;
      const gap = depth === 0 && (at("\\qquad") ? 6 : at("\\quad") ? 5 : 0);
      if (gap) { out.push(cur); cur = ""; i += gap - 1; continue; }
      cur += tex[i];
    }
    out.push(cur);
    return out.map(p => p.trim()).filter(Boolean);
  }

  // The HTML for one formula, ready for KaTeX to draw.
  function row(tex) {
    const ps = parts(tex);
    if (ps.length === 1 && /\\begin\{/.test(tex)) return `<div class="f-row">\\[${tex}\\]</div>`;
    return `<div class="f-row">${ps.map(p => `<span class="f-part">\\(\\displaystyle ${p}\\)</span>`).join("")}</div>`;
  }

  // Once the math is drawn: shrink a formula that is a little too wide for its box, and mark
  // one that still isn't all in view, so the page can show that it scrolls.
  function fit(root) {
    (root || document).querySelectorAll(".formula").forEach(f => {
      const r = f.querySelector(".f-row");
      if (!r) return;
      r.style.fontSize = "";
      f.classList.remove("scrolls");
      if (f.scrollWidth <= f.clientWidth + 1) return;
      const k = f.clientWidth / f.scrollWidth;
      if (k >= 0.8) r.style.fontSize = (0.98 * k).toFixed(3) + "em";
      if (f.scrollWidth > f.clientWidth + 1) {
        f.classList.add("scrolls");
        f.tabIndex = 0;  // so it can be scrolled from the keyboard
      }
    });
  }

  // Math fonts can arrive after the formulas are first measured, and change their width.
  function fitWhenReady(root) {
    fit(root);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => fit(root));
  }

  return { parts, row, fit: fitWhenReady };
})();