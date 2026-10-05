const names = ["1 Axes", "2 Riemann rise", "3 The limit", "4 Integral badge", "5 Pip"];
document.getElementById("out").innerHTML = names.map((n, i) => {
  const svg = document.getElementById("m" + (i + 1)).innerHTML;
  const tile = cls => `<div class="tile ${cls}"><span class="big">${svg}</span><div><div class="lock">${svg}<span>CalcLearners</span></div><div style="margin-top:10px" class="tiny">${svg}</div></div></div>`;
  return `<h3>${n}</h3><div class="row">${tile("light")}${tile("dark")}</div>`;
}).join("");
