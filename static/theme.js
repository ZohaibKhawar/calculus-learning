// Apply the saved theme (or the system preference) before the page paints.
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
})();
