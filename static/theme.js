// Apply the saved theme (or the system preference) before the page paints,
// and keep the topics list folded away if that is how it was left (see app.js).
// Loaded as a blocking script in <head>; kept out of the HTML so the
// Content-Security-Policy can forbid inline scripts.
(function () {
  var t;
  try { t = localStorage.getItem("theme"); } catch (e) {}
  if (t !== "light" && t !== "dark") {
    t = window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.dataset.theme = t;
  var meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = t === "dark" ? "#0F1729" : "#F4F6F9";
  var side;
  try { side = localStorage.getItem("topics"); } catch (e) {}
  if (side === "closed") document.documentElement.dataset.side = "closed";
})();
