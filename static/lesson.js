// Render the \( inline \) and \[ display \] math on the /lessons pages with KaTeX.
// Kept out of the HTML so the Content-Security-Policy can forbid inline scripts.
if (window.renderMathInElement) {
  renderMathInElement(document.getElementById("main"), {
    delimiters: [
      { left: "\\[", right: "\\]", display: true },
      { left: "\\(", right: "\\)", display: false }
    ],
    throwOnError: false
  });
}
