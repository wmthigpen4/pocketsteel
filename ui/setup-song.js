(function (global) {
  "use strict";
  const tools = global.STEEL_RAG_PRACTICE;
  const analysisClient = global.STEEL_RAG_ANALYSIS_CLIENT;
  const projectId = decodeURIComponent(global.location.pathname.split("/").filter(Boolean).at(-1) || "");
  const app = document.querySelector("#setup-app");
  const errorPanel = document.querySelector("#setup-error");
  const errorCopy = document.querySelector("#setup-error-copy");
  const audio = document.querySelector("#setup-audio");
  const status = document.querySelector("#setup-status");
  const confirmButton = document.querySelector("#confirm-play");
  const reanalyzePanel = document.querySelector("#reanalyze-panel");
  const reanalyzeButton = document.querySelector("#reanalyze-v2");
  const previewRhythmButton = document.querySelector("#preview-rhythm");
  const reanalyzeStatus = document.querySelector("#reanalyze-status");
  const reanalyzePreview = document.querySelector("#reanalyze-preview");
  let project = null;
  let audioFile = null;
  let objectUrl = "";
  let saveTimer = 0;
  let selectedBar = 0;
  let pendingAnalysis = null;
  let analysisRunning = false;

  function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]); }
  function reviewMapElement() { return document.querySelector("#review-song-map"); }
  function reviewEditorElement() { return document.querySelector("#review-editor"); }
  function formatTime(ms) { const seconds = Math.max(0, Number(ms || 0) / 1000); return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}.${String(Math.floor((seconds % 1) * 10))}`; }
  function percent(value) { return Number.isFinite(Number(value)) ? `${Math.round(Number(value) * 100)}%` : "—"; }
  function showError(message) { app.hidden = true; errorPanel.hidden = false; errorCopy.textContent = message; }
  function controls() { return { key: document.querySelector("#setup-key"), keyMode: document.querySelector("#setup-key-mode"), tempo: document.querySelector("#setup-tempo"), meter: document.querySelector("#setup-meter") }; }
  function barCount() { return project.timeline?.barStartsMs?.length || Math.max(0, ...(project.timeline?.chords || []).map((chord) => Number(chord.bar || 0))); }
  function eventsForBar(bar) { return (project.timeline?.chords || []).filter((chord) => Number(chord.bar) === bar).sort((left, right) => Number(left.startFraction || 0) - Number(right.startFraction || 0)); }
  function eventNeedsAttention(event) { return Boolean(event.needsAttention ?? (!event.reviewed || Number(event.confidence) < 0.68)); }
  function barNeedsAttention(bar) { const events = eventsForBar(bar); return !events.length || events.some(eventNeedsAttention); }
  function allReviewed() { return Array.from({ length: barCount() }, (_item, index) => index + 1).every((bar) => !barNeedsAttention(bar)); }

  function updateConfirmation() {
    const attention = Array.from({ length: barCount() }, (_item, index) => index + 1).filter(barNeedsAttention).length;
    confirmButton.hidden = attention > 0;
    status.textContent = attention
      ? `${attention} bar${attention === 1 ? "" : "s"} need attention. You can still start Play Along with the detected map.`
      : "The detected map is ready to confirm. Play Along will use this reviewed copy.";
  }

  function rebuildEventTimes() {
    const starts = project.timeline.barStartsMs || [];
    (project.timeline.chords || []).forEach((chord) => {
      const barIndex = Math.max(0, Number(chord.bar || 1) - 1);
      const start = Number(starts[barIndex] || 0);
      const end = Number(starts[barIndex + 1] ?? project.audio.durationMs);
      const fraction = clampFraction(chord.startFraction);
      const next = eventsForBar(barIndex + 1).find((event) => Number(event.startFraction) > fraction);
      const endFraction = next ? clampFraction(next.startFraction) : 1;
      chord.startMs = Math.round(start + (end - start) * fraction);
      chord.endMs = Math.round(start + (end - start) * endFraction);
    });
  }

  function rebuildBeatTimes() {
    const starts = project.timeline.barStartsMs || [];
    const beats = Math.max(1, Number(String(project.timeline.meter || "4/4").split("/")[0]) || 4);
    project.timeline.beatTimesMs = starts.flatMap((start, index) => {
      const end = Number(starts[index + 1] ?? project.audio.durationMs);
      return Array.from({ length: beats }, (_item, beat) => Math.round(start + (end - start) * beat / beats));
    });
  }

  function clampFraction(value) { return Math.max(0, Math.min(0.999, Number(value || 0))); }

  async function persist() {
    project.title = document.querySelector("#setup-song-title").value.trim() || "My song";
    project.updatedAt = new Date().toISOString();
    await tools.saveProject(project);
  }

  function queueSave() { global.clearTimeout(saveTimer); saveTimer = global.setTimeout(() => persist().catch((error) => { status.textContent = error.message; }), 180); }

  function analysisBadges() {
    const timeline = project.timeline || {};
    const mode = timeline.keyMode === "minor" ? "minor" : "major";
    const version = Number(timeline.analysisVersion || 1);
    document.querySelector("#analysis-summary").innerHTML = `
      <span><strong>${escapeHtml(timeline.key || "—")} ${mode}</strong><small>Key confidence ${percent(timeline.keyConfidence)}</small></span>
      <span><strong>${escapeHtml(timeline.meter || "—")}</strong><small>Meter confidence ${percent(timeline.meterConfidence)}</small></span>
      <span><strong>${escapeHtml(timeline.tempo || "—")} BPM</strong><small>Tempo confidence ${percent(timeline.tempoConfidence)}</small></span>
      <span><strong>Method v${version}</strong><small>${version >= 2 ? "Key-aware sequence" : "Legacy independent bars"}</small></span>`;
  }

  function matchingBarsFor(group, excludingBar) {
    if (!group) return [];
    return Array.from(new Set((project.timeline.chords || []).filter((event) => event.repeatedSectionGroup === group && Number(event.bar) !== excludingBar).map((event) => Number(event.bar))));
  }

  function replaceBarChords(bar, symbols, sourceEvents = eventsForBar(bar)) {
    const clean = symbols.map((symbol) => symbol.trim()).filter(Boolean).slice(0, 2);
    if (!clean.length) clean.push("N.C.");
    const first = sourceEvents[0] || {};
    const starts = project.timeline.barStartsMs || [];
    const start = Number(starts[bar - 1] || 0), end = Number(starts[bar] ?? project.audio.durationMs);
    const replacements = clean.map((symbol, index) => {
      const startFraction = clean.length === 2 ? index * 0.5 : 0;
      const endFraction = clean.length === 2 ? (index + 1) * 0.5 : 1;
      return {
        ...first, id: `reviewed-chord-${bar}-${index + 1}`, bar, startFraction,
        startMs: Math.round(start + (end - start) * startFraction), endMs: Math.round(start + (end - start) * endFraction),
        symbol, finalSymbol: symbol, confidence: 1, contextualAdjusted: false,
        reviewReasons: ["Corrected during Review."], reviewed: true, needsAttention: false
      };
    });
    project.timeline.chords = (project.timeline.chords || []).filter((event) => Number(event.bar) !== bar).concat(replacements).sort((left, right) => Number(left.bar) - Number(right.bar) || Number(left.startFraction || 0) - Number(right.startFraction || 0));
  }

  function acceptBar(bar) {
    if (!eventsForBar(bar).length) replaceBarChords(bar, ["N.C."]);
    eventsForBar(bar).forEach((event) => { event.reviewed = true; event.needsAttention = false; });
  }

  function applyToMatchingBars(bar) {
    const source = eventsForBar(bar);
    const group = source[0]?.repeatedSectionGroup;
    const symbols = source.map((event) => event.symbol);
    matchingBarsFor(group, bar).forEach((matchingBar) => replaceBarChords(matchingBar, symbols, eventsForBar(matchingBar)));
    renderReview(); updateConfirmation(); queueSave();
  }

  function barConfidence(bar) {
    const events = eventsForBar(bar);
    return events.length ? Math.min(...events.map((event) => Number(event.confidence || 0))) : 0;
  }

  function mapButtonForBar(bar) {
    const events = eventsForBar(bar);
    const needsAttention = barNeedsAttention(bar);
    const symbols = events.map((event) => event.symbol || "N.C.").join(" · ") || "N.C.";
    const button = document.createElement("button");
    button.type = "button";
    button.className = `review-map-bar ${needsAttention ? "needs-attention" : "is-accepted"}${bar === selectedBar ? " is-selected" : ""}`;
    button.dataset.bar = String(bar);
    button.setAttribute("aria-pressed", String(bar === selectedBar));
    button.setAttribute("aria-label", `Bar ${bar}, ${symbols}, ${needsAttention ? "needs attention" : "accepted"}. Select to review without autoplay.`);
    button.innerHTML = `<span>Bar ${bar}</span><strong>${escapeHtml(symbols)}</strong><small>${percent(barConfidence(bar))} · ${needsAttention ? "Needs attention" : "Accepted"}</small>`;
    button.onclick = () => {
      selectedBar = bar;
      audio.pause();
      audio.currentTime = Number(project.timeline.barStartsMs?.[bar - 1] || events[0]?.startMs || 0) / 1000;
      renderReview();
      reviewEditorElement()?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    };
    return button;
  }

  function renderEditor() {
    const editor = reviewEditorElement();
    if (!editor) throw new Error("The visual chord editor is unavailable. Reload the page and try again.");
    const bar = selectedBar;
    const events = eventsForBar(bar);
    const startMs = Number(project.timeline.barStartsMs?.[bar - 1] || events[0]?.startMs || 0);
    const needsAttention = barNeedsAttention(bar);
    const reasons = Array.from(new Set(events.flatMap((event) => event.reviewReasons || [])));
    const matches = matchingBarsFor(events[0]?.repeatedSectionGroup, bar);
    editor.innerHTML = `
      <div class="review-editor__head">
        <div><p class="songs-kicker">Selected measure</p><h3>Bar ${bar}</h3></div>
        <span class="review-editor__status ${needsAttention ? "needs-attention" : "is-accepted"}">${percent(barConfidence(bar))} confidence · ${needsAttention ? "Needs attention" : "Accepted"}</span>
      </div>
      <div class="review-editor__fields">
        <label>Chord${events.length === 2 ? "s" : ""}<input data-chord type="text" value="${escapeHtml(events.map((event) => event.symbol || "N.C.").join(" "))}" aria-label="Chord${events.length === 2 ? "s" : ""} for bar ${bar}"><small>Enter one chord, or two chords separated by a space.</small></label>
        <label>Bar downbeat<input data-time type="number" min="0" max="${project.audio.durationMs}" step="10" value="${Math.round(startMs)}" aria-label="Downbeat milliseconds for bar ${bar}"><small>${formatTime(startMs)} into the recording</small></label>
      </div>
      <p class="review-editor__reason">${escapeHtml(reasons.join(" ") || "No analysis concern was recorded for this bar.")}</p>
      <div class="review-editor__actions">
        <button class="songs-button" data-play-bar type="button">Play from bar ${bar}</button>
        <button class="songs-button is-primary" data-accept-bar type="button">${needsAttention ? "Accept this bar" : "Mark for review"}</button>
        ${matches.length ? `<button class="songs-button is-quiet" data-apply-repeat type="button">Apply chord to ${matches.length} matching bar${matches.length === 1 ? "" : "s"}</button>` : ""}
      </div>`;
    editor.querySelector("[data-play-bar]").onclick = () => {
      audio.currentTime = Number(project.timeline.barStartsMs?.[bar - 1] || 0) / 1000;
      audio.play().catch(() => {});
    };
    editor.querySelector("[data-chord]").onchange = (event) => {
      replaceBarChords(bar, event.target.value.split(/\s+/)); renderReview(); updateConfirmation(); queueSave();
    };
    editor.querySelector("[data-time]").onchange = (event) => {
      const starts = project.timeline.barStartsMs;
      const lower = bar > 1 ? Number(starts[bar - 2]) + 25 : 0;
      const upper = bar < starts.length ? Number(starts[bar]) - 25 : Number(project.audio.durationMs);
      starts[bar - 1] = Math.round(Math.max(lower, Math.min(upper, Number(event.target.value))));
      acceptBar(bar); rebuildEventTimes(); rebuildBeatTimes(); renderReview(); updateConfirmation(); queueSave();
    };
    editor.querySelector("[data-accept-bar]").onclick = () => {
      if (needsAttention) acceptBar(bar);
      else eventsForBar(bar).forEach((event) => { event.reviewed = false; event.needsAttention = true; });
      renderReview(); updateConfirmation(); queueSave();
    };
    editor.querySelector("[data-apply-repeat]")?.addEventListener("click", () => applyToMatchingBars(bar));
  }

  function renderReview() {
    const map = reviewMapElement();
    if (!map) throw new Error("The visual song map is unavailable. Reload the page and try again.");
    const count = barCount();
    if (!selectedBar || selectedBar > count) selectedBar = Array.from({ length: count }, (_item, index) => index + 1).find(barNeedsAttention) || 1;
    map.replaceChildren(...Array.from({ length: count }, (_item, index) => mapButtonForBar(index + 1)));
    renderEditor();
  }

  function setControlsFromTimeline() {
    const fields = controls();
    fields.key.value = project.timeline.key || "G";
    fields.keyMode.value = project.timeline.keyMode || "major";
    fields.tempo.value = String(project.timeline.tempo || 100);
    fields.meter.value = project.timeline.meter || "4/4";
  }

  function configureReanalysis() {
    const legacy = Number(project.timeline?.analysisVersion || 1) < 2;
    reanalyzePanel.hidden = !legacy;
    reanalyzeButton.hidden = !legacy;
    previewRhythmButton.hidden = true;
    reanalyzePreview.hidden = true;
    if (legacy) {
      document.querySelector("#reanalyze-title").textContent = "Improved local analysis is available.";
      document.querySelector("#reanalyze-copy").textContent = "Preview key-aware chords without overwriting your current corrections.";
    }
  }

  function markRhythmChange() {
    reanalyzePanel.hidden = false;
    previewRhythmButton.hidden = false;
    document.querySelector("#reanalyze-title").textContent = "Tempo or meter changed.";
    document.querySelector("#reanalyze-copy").textContent = "Run a fresh local preview before replacing the bar grid and chord map.";
  }

  async function runFreshAnalysis() {
    if (analysisRunning) return;
    analysisRunning = true; pendingAnalysis = null; reanalyzePreview.hidden = true;
    reanalyzeButton.disabled = true; previewRhythmButton.disabled = true;
    try {
      const fields = controls();
      const legacy = Number(project.timeline?.analysisVersion || 1) < 2;
      const options = previewRhythmButton.hidden
        ? (legacy ? { tempoHint: Number(project.timeline.tempo), keyHint: project.timeline.key, keyModeHint: project.timeline.keyMode || "major" } : {})
        : { tempo: Number(fields.tempo.value), meter: fields.meter.value, keyHint: fields.key.value, keyModeHint: fields.keyMode.value };
      const result = await analysisClient.analyzeFile(audioFile, options, (stage, detail) => { reanalyzeStatus.textContent = `${stage}: ${detail}`; });
      pendingAnalysis = result.analysis;
      const attention = new Set(pendingAnalysis.chords.filter(eventNeedsAttention).map((event) => event.bar)).size;
      const chordCounts = new Map();
      pendingAnalysis.chords.forEach((event) => chordCounts.set(event.symbol, (chordCounts.get(event.symbol) || 0) + 1));
      const commonChords = [...chordCounts.entries()].sort((left, right) => right[1] - left[1]).slice(0, 7).map(([symbol, count]) => `${symbol} (${count})`).join(", ");
      document.querySelector("#reanalyze-preview-copy").textContent = `Preview: ${pendingAnalysis.key} ${pendingAnalysis.keyMode} · ${pendingAnalysis.meter} · ${pendingAnalysis.tempo} BPM · ${attention} attention bar${attention === 1 ? "" : "s"}. Common chords: ${commonChords || "N.C."}.`;
      reanalyzePreview.hidden = false;
      reanalyzeStatus.textContent = "Preview ready. Your current map is unchanged.";
    } catch (error) {
      reanalyzeStatus.textContent = error.message || "The fresh analysis could not be completed.";
    } finally {
      analysisRunning = false; reanalyzeButton.disabled = false; previewRhythmButton.disabled = false;
    }
  }

  async function acceptReanalysis() {
    if (!pendingAnalysis) return;
    const confirmationState = "detected";
    project.timeline = { ...pendingAnalysis, confirmationState };
    pendingAnalysis = null;
    selectedBar = 0; setControlsFromTimeline(); analysisBadges(); configureReanalysis(); renderReview(); updateConfirmation(); await persist();
    reanalyzeStatus.textContent = "The improved local analysis is now this project's editable map.";
  }

  async function handleKeyChange() {
    const fields = controls();
    if (Number(project.timeline.analysisVersion || 1) < 2 || !project.timeline.analysisState) {
      project.timeline.key = fields.key.value; project.timeline.keyMode = fields.keyMode.value; queueSave(); analysisBadges(); return;
    }
    try {
      reanalyzeStatus.textContent = "Rechecking chords in the selected key…";
      const updated = await analysisClient.redecode(project.timeline, fields.key.value, fields.keyMode.value, (_stage, detail) => { reanalyzeStatus.textContent = detail; });
      project.timeline = { ...updated, confirmationState: "detected" };
      selectedBar = 0; analysisBadges(); renderReview(); updateConfirmation(); await persist();
      reanalyzeStatus.textContent = "Chord context updated from retained local candidate scores.";
      reanalyzePanel.hidden = false;
    } catch (error) { reanalyzeStatus.textContent = error.message; setControlsFromTimeline(); }
  }

  async function initialize() {
    project = await tools.loadProject(projectId);
    if (!project) throw new Error("That local song is no longer stored in this browser.");
    audioFile = await tools.readAudio(project.audio?.opfsPath || `${project.id}.audio`).catch(() => null);
    if (!audioFile) throw new Error("The local recording is missing. Return to Songs and relink the original file with the same fingerprint.");
    if (!analysisClient) throw new Error("Local analysis controls are unavailable. Reload the page and try again.");
    objectUrl = URL.createObjectURL(audioFile); audio.src = objectUrl;
    document.querySelector("#setup-title").textContent = `Review ${project.title}`;
    document.querySelector("#setup-song-title").value = project.title;
    document.querySelector("#start-play").href = `/play/${encodeURIComponent(project.id)}`;
    setControlsFromTimeline(); analysisBadges(); configureReanalysis();
    document.querySelector("#setup-song-title").addEventListener("input", queueSave);
    controls().key.addEventListener("change", handleKeyChange);
    controls().keyMode.addEventListener("change", handleKeyChange);
    controls().tempo.addEventListener("change", markRhythmChange);
    controls().meter.addEventListener("change", markRhythmChange);
    document.querySelector("#review-all").onclick = () => {
      Array.from({ length: barCount() }, (_item, index) => index + 1).filter(barNeedsAttention).forEach(acceptBar);
      renderReview(); updateConfirmation(); queueSave();
    };
    reanalyzeButton.onclick = runFreshAnalysis;
    previewRhythmButton.onclick = runFreshAnalysis;
    document.querySelector("#accept-reanalysis").onclick = acceptReanalysis;
    document.querySelector("#discard-reanalysis").onclick = () => { pendingAnalysis = null; reanalyzePreview.hidden = true; reanalyzeStatus.textContent = "Current map kept."; setControlsFromTimeline(); configureReanalysis(); };
    confirmButton.onclick = async () => { project.timeline.confirmationState = "confirmed"; await persist(); global.location.assign(`/play/${encodeURIComponent(project.id)}`); };
    renderReview(); updateConfirmation(); app.hidden = false;
  }

  global.addEventListener("beforeunload", () => { if (objectUrl) URL.revokeObjectURL(objectUrl); });
  function start() {
    initialize().catch((error) => {
      global.console.error("Song review initialization failed", error);
      showError(error.message || "This song could not be reviewed.");
    });
  }
  if (document.readyState === "loading") global.addEventListener("DOMContentLoaded", start, { once: true });
  else start();
})(window);
