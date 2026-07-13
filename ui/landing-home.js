(function initializeLandingHome(globalScope) {
  "use strict";

  const UNAVAILABLE_MESSAGE = "Fretboard preview is unavailable. Open Explorer to continue.";

  function mountExplorerPreview(container, fretboardApi = globalScope.STEEL_RAG_FRETBOARD) {
    if (!container) return null;
    if (!fretboardApi?.mountPedalSteelFretboard || !Array.isArray(fretboardApi.DEMO_POSITIONS)) {
      container.classList.add("is-unavailable");
      container.textContent = UNAVAILABLE_MESSAGE;
      return null;
    }

    container.classList.remove("is-unavailable");
    const figure = fretboardApi.mountPedalSteelFretboard(container, {
      title: "Validated E9 G major positions",
      description: "G major on strings 4, 5, and 6 at frets 3, 6, and 10.",
      positions: fretboardApi.DEMO_POSITIONS,
      hideFilterControls: true,
      hidePositionTools: true,
      hideLegend: true,
      showHighlightLabels: true,
      emphasizeVisibleHighlights: true,
    });

    figure?.classList.add("home-explorer-figure");
    container.querySelectorAll("a, button, input, select, textarea, [tabindex]").forEach((element) => {
      element.tabIndex = -1;
    });
    return figure;
  }

  const api = { UNAVAILABLE_MESSAGE, mountExplorerPreview };
  globalScope.STEEL_RAG_LANDING = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
