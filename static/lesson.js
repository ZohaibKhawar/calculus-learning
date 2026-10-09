// Render the \( inline \) and \[ display \] math on the /lessons pages with KaTeX.
// Kept out of the HTML so the Content-Security-Policy can forbid inline scripts.
(function () {
  const main = document.getElementById("main");
  // Formulas are split into parts that stack on a narrow screen (see formula.js).
  if (window.Formula) {
    main.querySelectorAll(".formula[data-tex]").forEach(f => {
      f.querySelector(".f-row").outerHTML = Formula.row(f.dataset.tex);
    });
  }
  // The pictures in the explanation (plot.js).
  if (window.Plot) Plot.hydrate(main);
  if (!window.renderMathInElement) return;
  renderMathInElement(main, {
    delimiters: [
      { left: "\\[", right: "\\]", display: true },
      { left: "\\(", right: "\\)", display: false }
    ],
    throwOnError: false
  });
  if (!window.Formula) return;
  Formula.fit(main);
  let timer;
  window.addEventListener("resize", () => { clearTimeout(timer); timer = setTimeout(() => Formula.fit(main), 150); });
})();