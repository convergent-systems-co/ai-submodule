// Initialize Mermaid.js for MkDocs Material
// fence_div_format outputs <div class="mermaid"><code>...</code></div>
// Mermaid.js expects <div class="mermaid">raw text</div> (no <code> wrapper)
// This script strips the <code> wrapper before Mermaid processes the elements
function initMermaid() {
  var elements = document.querySelectorAll("div.mermaid");
  if (!elements.length) return;

  // Strip <code> wrappers that fence_div_format may insert
  elements.forEach(function (el) {
    var code = el.querySelector("code");
    if (code) {
      el.textContent = code.textContent;
    }
    // Mark as unprocessed so Mermaid picks it up on re-runs
    el.removeAttribute("data-processed");
  });

  mermaid.initialize({
    startOnLoad: false,
    theme: "base",
    themeVariables: {
      darkMode: true,
      background: "#252A33",
      primaryColor: "#5E81AC",
      primaryTextColor: "#ECEFF4",
      primaryBorderColor: "#4C566A",
      secondaryColor: "#363D4B",
      secondaryTextColor: "#D8DEE9",
      secondaryBorderColor: "#4C566A",
      tertiaryColor: "#2F3542",
      tertiaryTextColor: "#D8DEE9",
      tertiaryBorderColor: "#4C566A",
      lineColor: "#81A1C1",
      textColor: "#ECEFF4",
      mainBkg: "#2F3542",
      nodeBorder: "#81A1C1",
      clusterBkg: "#2F3542",
      clusterBorder: "#4C566A",
      titleColor: "#88C0D0",
      edgeLabelBackground: "#2F3542",
      nodeTextColor: "#ECEFF4"
    }
  });
  mermaid.run();
}

if (typeof document$ !== "undefined") {
  document$.subscribe(initMermaid);
} else {
  document.addEventListener("DOMContentLoaded", initMermaid);
}
