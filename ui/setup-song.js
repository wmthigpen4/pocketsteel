(function (global) {
  "use strict";
  const tools = global.STEEL_RAG_PRACTICE;
  const analysisClient = global.STEEL_RAG_ANALYSIS_CLIENT;
  const referenceValidation = global.STEEL_RAG_REFERENCE_VALIDATION;
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
  const referencePanel = document.querySelector("#reference-panel");
  const referenceStatus = document.querySelector("#reference-status");
  let project = null;
  let audioFile = null;
  let objectUrl = "";
  let saveTimer = 0;
  let selectedBar = 0;
  let pendingAnalysis = null;
  let showingPreview = false;
  let analysisRunning = false;

  function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]); }
  function reviewMapElement() { return document.querySelector("#review-song-map"); }
  function reviewEditorElement() { return document.querySelector("#review-editor"); }
  function formatTime(ms) { const seconds = Math.max(0, Number(ms || 0) / 1000); return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}.${String(Math.floor((seconds % 1) * 10))}`; }
  function percent(value) { return Number.isFinite(Number(value)) ? `${Math.round(Number(value) * 100)}%` : "—"; }
  function showError(message) { app.hidden = true; errorPanel.hidden = false; errorCopy.textContent = message; }
  function controls() { return { key: document.querySelector("#setup-key"), keyMode: document.querySelector("#setup-key-mode"), tempo: document.querySelector("#setup-tempo"), meter: document.querySelector("#setup-meter") }; }
  function activeTimeline() { return showingPreview && pendingAnalysis ? pendingAnalysis : project.timeline; }
  function legacyTimeline() { return Number(activeTimeline()?.analysisVersion || 1) < 2; }
  function barCount() { const timeline = activeTimeline(); return timeline?.barStartsMs?.length || Math.max(0, ...(timeline?.chords || []).map((chord) => Number(chord.bar || 0))); }
  function eventsForBar(bar) { return (activeTimeline()?.chords || []).filter((chord) => Number(chord.bar) === bar).sort((left, right) => Number(left.startFraction || 0) - Number(right.startFraction || 0)); }
  function eventNeedsAttention(event) { return Boolean(event.needsAttention ?? (!event.reviewed || Number(event.confidence) < 0.68)); }
  function barNeedsAttention(bar) { if (legacyTimeline()) return false; const events = eventsForBar(bar); return !events.length || events.some(eventNeedsAttention); }
  function allReviewed() { return Array.from({ length: barCount() }, (_item, index) => index + 1).every((bar) => !barNeedsAttention(bar)); }

  function updateConfirmation() {
    const attention = Array.from({ length: barCount() }, (_item, index) => index + 1).filter(barNeedsAttention).length;
    if (showingPreview) {
      confirmButton.hidden = true;
      status.textContent = `${attention} preview bar${attention === 1 ? "" : "s"} need attention. This preview has not replaced your saved map.`;
      return;
    }
    if (legacyTimeline()) {
      confirmButton.hidden = true;
      status.textContent = "Legacy chord map shown. Run the improved analysis to create confidence-based review results.";
      return;
    }
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
    return Array.from(new Set((activeTimeline().chords || []).filter((event) => event.repeatedSectionGroup === group && Number(event.bar) !== excludingBar).map((event) => Number(event.bar))));
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

  function barExternalState(bar) {
    const results = eventsForBar(bar).map((event) => event.externalValidation?.result).filter(Boolean);
    if (results.includes("close-audio-alternative")) return "Reference-resolved";
    if (results.includes("bar-agreement")) return "Reference-confirmed";
    return "";
  }

  function mapButtonForBar(bar) {
    const events = eventsForBar(bar);
    const legacy = legacyTimeline();
    const needsAttention = barNeedsAttention(bar);
    const symbols = events.map((event) => event.symbol || "N.C.").join(" · ") || "N.C.";
    const externalState = barExternalState(bar);
    const stateLabel = legacy ? "Legacy detection" : needsAttention ? "Needs attention" : externalState || "Accepted";
    const button = document.createElement("button");
    button.type = "button";
    button.className = `review-map-bar ${legacy ? "is-legacy" : needsAttention ? "needs-attention" : "is-accepted"}${bar === selectedBar ? " is-selected" : ""}`;
    button.dataset.bar = String(bar);
    button.setAttribute("aria-pressed", String(bar === selectedBar));
    button.setAttribute("aria-label", `Bar ${bar}, ${symbols}, ${stateLabel}. Select to review without autoplay.`);
    button.innerHTML = `<span>Bar ${bar}</span><strong>${escapeHtml(symbols)}</strong><small>${legacy ? stateLabel : `${percent(barConfidence(bar))} · ${stateLabel}`}</small>`;
    button.onclick = () => {
      selectedBar = bar;
      audio.pause();
      audio.currentTime = Number(activeTimeline().barStartsMs?.[bar - 1] || events[0]?.startMs || 0) / 1000;
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
    const timeline = activeTimeline();
    const legacy = legacyTimeline();
    const editable = !showingPreview;
    const startMs = Number(timeline.barStartsMs?.[bar - 1] || events[0]?.startMs || 0);
    const needsAttention = barNeedsAttention(bar);
    const reasons = Array.from(new Set(events.flatMap((event) => event.reviewReasons || [])));
    const matches = matchingBarsFor(events[0]?.repeatedSectionGroup, bar);
    const externalState = barExternalState(bar);
    const stateLabel = showingPreview ? (needsAttention ? "Preview · Needs attention" : externalState ? `Preview · ${externalState}` : "Preview · Auto-accepted") : legacy ? "Legacy detection" : needsAttention ? "Needs attention" : externalState || "Accepted";
    editor.innerHTML = `
      <div class="review-editor__head">
        <div><p class="songs-kicker">Selected measure</p><h3>Bar ${bar}</h3></div>
        <span class="review-editor__status ${legacy ? "is-legacy" : needsAttention ? "needs-attention" : "is-accepted"}">${legacy ? stateLabel : `${percent(barConfidence(bar))} confidence · ${stateLabel}`}</span>
      </div>
      <div class="review-editor__fields">
        <label>Chord${events.length === 2 ? "s" : ""}<input data-chord type="text" value="${escapeHtml(events.map((event) => event.symbol || "N.C.").join(" "))}" aria-label="Chord${events.length === 2 ? "s" : ""} for bar ${bar}"${editable ? "" : " disabled"}><small>${editable ? "Enter one chord, or two chords separated by a space." : "Accept the preview before making corrections."}</small></label>
        <label>Bar downbeat<input data-time type="number" min="0" max="${project.audio.durationMs}" step="10" value="${Math.round(startMs)}" aria-label="Downbeat milliseconds for bar ${bar}"${editable ? "" : " disabled"}><small>${formatTime(startMs)} into the recording</small></label>
      </div>
      <p class="review-editor__reason">${escapeHtml(legacy ? "This bar came from the earlier extractor and has no v2 confidence decision." : reasons.join(" ") || "Strong audio and song-context agreement.")}</p>
      <div class="review-editor__actions">
        <button class="songs-button" data-play-bar type="button">Play from bar ${bar}</button>
        ${editable && !legacy ? `<button class="songs-button is-primary" data-accept-bar type="button">${needsAttention ? "Accept this bar" : "Mark for review"}</button>` : ""}
        ${editable && !legacy && matches.length ? `<button class="songs-button is-quiet" data-apply-repeat type="button">Apply chord to ${matches.length} matching bar${matches.length === 1 ? "" : "s"}</button>` : ""}
      </div>`;
    editor.querySelector("[data-play-bar]").onclick = () => {
      audio.currentTime = Number(timeline.barStartsMs?.[bar - 1] || 0) / 1000;
      audio.play().catch(() => {});
    };
    if (editable) editor.querySelector("[data-chord]").onchange = (event) => {
      replaceBarChords(bar, event.target.value.split(/\s+/)); renderReview(); updateConfirmation(); queueSave();
    };
    if (editable) editor.querySelector("[data-time]").onchange = (event) => {
      const starts = project.timeline.barStartsMs;
      const lower = bar > 1 ? Number(starts[bar - 2]) + 25 : 0;
      const upper = bar < starts.length ? Number(starts[bar]) - 25 : Number(project.audio.durationMs);
      starts[bar - 1] = Math.round(Math.max(lower, Math.min(upper, Number(event.target.value))));
      acceptBar(bar); rebuildEventTimes(); rebuildBeatTimes(); renderReview(); updateConfirmation(); queueSave();
    };
    if (editor.querySelector("[data-accept-bar]")) editor.querySelector("[data-accept-bar]").onclick = () => {
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
    const heading = document.querySelector("#review-heading");
    const description = document.querySelector("#review-description");
    const reviewAll = document.querySelector("#review-all");
    if (showingPreview) {
      heading.textContent = "Improved Analysis Preview";
      description.textContent = "This is the new key-aware map. Coral bars need review; amber bars were accepted automatically. Nothing is saved until you choose Use this analysis.";
    } else if (legacyTimeline()) {
      heading.textContent = "Legacy Song Map";
      description.textContent = "This map came from the earlier extractor. Run the improved analysis above to see confidence-based results before replacing it.";
    } else {
      heading.textContent = "Song Map";
      description.textContent = "See the whole progression at once. Amber bars are accepted; coral bars need attention. Select any bar to hear and correct it.";
    }
    reviewAll.hidden = showingPreview || legacyTimeline();
    referencePanel.hidden = legacyTimeline();
    map.replaceChildren(...Array.from({ length: count }, (_item, index) => mapButtonForBar(index + 1)));
    renderEditor();
  }

  function normalizedSourceUrl(urlValue) {
    if (!urlValue) return "";
    try {
      const url = new URL(urlValue);
      if (!/^https?:$/.test(url.protocol)) throw new Error();
      url.username = ""; url.password = ""; url.search = ""; url.hash = "";
      return url.href;
    } catch (_error) {
      throw new Error("Enter a complete http or https source URL, or leave it blank.");
    }
  }

  function sourceLabelFor(urlValue) {
    if (!urlValue) return "User-supplied chart";
    const host = new URL(urlValue).hostname.replace(/^www\./, "");
    return host === "ultimate-guitar.com" || host.endsWith(".ultimate-guitar.com") ? "Ultimate Guitar reference" : `${host} reference`;
  }

  function previewSummary(timeline) {
    const attention = new Set((timeline.chords || []).filter(eventNeedsAttention).map((event) => event.bar)).size;
    const chordCounts = new Map();
    (timeline.chords || []).forEach((event) => chordCounts.set(event.symbol, (chordCounts.get(event.symbol) || 0) + 1));
    const commonChords = [...chordCounts.entries()].sort((left, right) => right[1] - left[1]).slice(0, 7).map(([symbol, count]) => `${symbol} (${count})`).join(", ");
    return `Preview: ${timeline.key} ${timeline.keyMode} · ${timeline.meter} · ${timeline.tempo} BPM · ${attention} attention bar${attention === 1 ? "" : "s"}. Common chords: ${commonChords || "N.C."}.`;
  }

  async function applyReferenceValidation() {
    if (!referenceValidation) throw new Error("External chord validation is unavailable. Reload the page and try again.");
    if (legacyTimeline()) throw new Error("Run the improved local analysis before adding an external reference.");
    if (!document.querySelector("#reference-permission").checked) throw new Error("Confirm that you have permission to use this reference.");
    const chartField = document.querySelector("#reference-chart");
    const sourceUrl = normalizedSourceUrl(document.querySelector("#reference-url").value.trim());
    const sourceLabel = sourceLabelFor(sourceUrl);
    const loaded = await referenceValidation.loadProviderReference("user-supplied", { text: chartField.value, sourceLabel, sourceUrl });
    const reference = loaded.reference;
    const result = referenceValidation.validateTimeline(activeTimeline(), reference, { sourceLabel, sourceUrl });
    if (showingPreview) pendingAnalysis = result.timeline;
    else { project.timeline = result.timeline; queueSave(); }
    chartField.value = "";
    document.querySelector("#reference-permission").checked = false;
    selectedBar = 0;
    renderReview(); updateConfirmation();
    if (showingPreview) document.querySelector("#reanalyze-preview-copy").textContent = previewSummary(pendingAnalysis);
    const resolved = result.summary.agreements + result.summary.corrections;
    referenceStatus.textContent = result.summary.alignment === "vocabulary-only"
      ? `Found ${reference.vocabulary.length} chord symbol${reference.vocabulary.length === 1 ? "" : "s"}, but no reliable measure alignment. No bars were auto-accepted.`
      : `${resolved} uncertain event${resolved === 1 ? "" : "s"} resolved (${result.summary.agreements} confirmed, ${result.summary.corrections} changed); ${result.summary.disagreements} disagreement${result.summary.disagreements === 1 ? "" : "s"} remain for review.`;
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
    analysisRunning = true; pendingAnalysis = null; showingPreview = false; reanalyzePreview.hidden = true;
    reanalyzeButton.disabled = true; previewRhythmButton.disabled = true;
    try {
      const fields = controls();
      const legacy = Number(project.timeline?.analysisVersion || 1) < 2;
      const options = previewRhythmButton.hidden
        ? (legacy ? { tempoHint: Number(project.timeline.tempo), keyHint: project.timeline.key, keyModeHint: project.timeline.keyMode || "major" } : {})
        : { tempo: Number(fields.tempo.value), meter: fields.meter.value, keyHint: fields.key.value, keyModeHint: fields.keyMode.value };
      const result = await analysisClient.analyzeFile(audioFile, options, (stage, detail) => { reanalyzeStatus.textContent = `${stage}: ${detail}`; });
      pendingAnalysis = result.analysis;
      document.querySelector("#reanalyze-preview-copy").textContent = previewSummary(pendingAnalysis);
      reanalyzePreview.hidden = false;
      showingPreview = true; selectedBar = 0; renderReview(); updateConfirmation();
      reanalyzeStatus.textContent = "Preview ready below. Your saved map is unchanged.";
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
    pendingAnalysis = null; showingPreview = false;
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
    document.querySelector("#setup-title").textContent = "Review Song";
    document.querySelector("#setup-track-name").textContent = project.title;
    document.querySelector("#setup-song-title").value = project.title;
    document.querySelector("#start-play").href = `/play/${encodeURIComponent(project.id)}`;
    setControlsFromTimeline(); analysisBadges(); configureReanalysis();
    document.querySelector("#setup-song-title").addEventListener("input", (event) => {
      document.querySelector("#setup-track-name").textContent = event.target.value.trim() || "Untitled song";
      queueSave();
    });
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
    document.querySelector("#discard-reanalysis").onclick = () => { pendingAnalysis = null; showingPreview = false; selectedBar = 0; reanalyzePreview.hidden = true; reanalyzeStatus.textContent = "Current map kept."; setControlsFromTimeline(); configureReanalysis(); renderReview(); updateConfirmation(); };
    document.querySelector("#validate-reference").onclick = async () => { try { await applyReferenceValidation(); } catch (error) { referenceStatus.textContent = error.message; } };
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
