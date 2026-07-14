(function initializeLandingHome(globalScope) {
  "use strict";

  const UNAVAILABLE_MESSAGE = "Fretboard preview is unavailable. Open Explorer to continue.";
  const SCORE_UNAVAILABLE_MESSAGE = "Music preview is unavailable. Open Melody Studio to continue.";

  function landingPosition(position) {
    if (Number(position.fret) === 6) {
      return {
        ...position,
        label: "A + F lever",
        stringActionLabels: { 4: "4F", 5: "5A", 6: "6" },
      };
    }
    if (Number(position.fret) === 10) {
      return {
        ...position,
        label: "A + B pedals",
        stringActionLabels: { 4: "4", 5: "5A", 6: "6B" },
      };
    }
    return {
      ...position,
      label: "No pedals",
      stringActionLabels: { 4: "4", 5: "5", 6: "6" },
    };
  }

  function mountExplorerPreview(container, fretboardApi = globalScope.STEEL_RAG_FRETBOARD) {
    if (!container) return null;
    if (!fretboardApi?.mountPedalSteelFretboard || !Array.isArray(fretboardApi.DEMO_POSITIONS)) {
      container.classList.add("is-unavailable");
      container.textContent = UNAVAILABLE_MESSAGE;
      return null;
    }

    container.classList.remove("is-unavailable");
    const figure = fretboardApi.mountPedalSteelFretboard(container, {
      title: "E9 G major positions",
      description: "G major on strings 4, 5, and 6 at frets 3, 6, and 10.",
      positions: fretboardApi.DEMO_POSITIONS.map(landingPosition),
      hideFilterControls: true,
      hidePositionTools: true,
      hideLegend: true,
      showHighlightLabels: true,
      showStringActionLabels: true,
      emphasizeVisibleHighlights: true,
      cropLeftAtNut: true,
    });

    figure?.classList.add("home-explorer-figure");
    container.querySelectorAll("a, button, input, select, textarea, [tabindex]").forEach((element) => {
      element.tabIndex = -1;
    });
    return figure;
  }

  function mountMelodyPreview(container, scoreApi = globalScope.STEEL_RAG_MELODY_SCORE) {
    if (!container) return false;
    if (!scoreApi?.renderPreview || !scoreApi.renderPreview(container)) {
      container.classList.add("is-unavailable");
      container.textContent = SCORE_UNAVAILABLE_MESSAGE;
      return false;
    }
    container.classList.remove("is-unavailable");
    container.querySelectorAll("a, button, input, select, textarea, [tabindex]").forEach((element) => {
      element.tabIndex = -1;
    });
    return true;
  }

  const api = { UNAVAILABLE_MESSAGE, SCORE_UNAVAILABLE_MESSAGE, landingPosition, mountExplorerPreview, mountMelodyPreview };
  globalScope.STEEL_RAG_LANDING = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
