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
  const setupSummary = document.querySelector(".setup-summary");
  const analysisSummary = document.querySelector("#analysis-summary");
  const reviewPanel = document.querySelector(".review-panel");
  const startPlayButton = document.querySelector("#start-play");
  const showChordsButton = document.querySelector("#review-show-chords");
  const showNnsButton = document.querySelector("#review-show-nns");
  let project = null;
  let practiceSession = null;
  let audioFile = null;
  let objectUrl = "";
  let saveTimer = 0;
  let selectedBar = 0;
  let pendingAnalysis = null;
  let showingPreview = false;
  let analysisRunning = false;
  let reviewChordDisplay = "letters";
  let keyChangeRequest = 0;

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
  function keyContextForBar(bar, timeline = activeTimeline()) { return tools.keyForBar(timeline, bar); }
  function chordForReview(symbol, bar) { return tools.chordForDisplay(symbol || "N.C.", keyContextForBar(bar).key, reviewChordDisplay); }
  function noChord(symbol) { return /^(?:N\.?C\.?|NO\s+CHORD|REST)$/i.test(String(symbol || "").trim()); }
  function explorerTargetForChord(symbol, bar) {
    const match = /^([A-G])([#b]?)(.*)$/i.exec(String(symbol || "").trim());
    if (!match || noChord(symbol)) return null;
    const suffix = match[3].toLowerCase();
    const quality = /^m7/.test(suffix) ? "minor7" : /^m(?!aj)/.test(suffix) ? "minor" : /^(?:7|dom7)/.test(suffix) ? "dominant7" : /^maj7/.test(suffix) ? "major7" : "major";
    const root = `${match[1].toUpperCase()}${match[2]}`;
    const key = keyContextForBar(bar).key;
    return {
      root,
      url: `/ui/e9-fretboard-explorer.html?mode=chord&key=${encodeURIComponent(key)}&root=${encodeURIComponent(root)}&quality=${quality}&source=song-review`
    };
  }
  function selectedChordTeaching(events, displayedChords, bar) {
    const symbols = events.map((event) => event.symbol || "N.C.");
    if (symbols.some(noChord)) {
      return "No chord means there is no sustained harmony to play in this measure. Listen for silence, spoken audio, or pickup notes before the band enters.";
    }
    if (reviewChordDisplay !== "nns" || events.length !== 1) return "";
    const key = keyContextForBar(bar).key || "the section key";
    if (/^♭7/.test(displayedChords)) {
      return `${displayedChords} is ${symbols[0]} in the key of ${key}. The flat-seven chord sits one whole step below the 1 chord and is a common country and rock color.`;
    }
    return `${displayedChords} is ${symbols[0]} in the key of ${key}.`;
  }
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

  function preserveManualChordEdits(updatedTimeline, previousTimeline) {
    const manual = (previousTimeline.chords || []).filter((chord) => String(chord.id || "").startsWith("reviewed-chord-"));
    if (!manual.length) return updatedTimeline;
    const manualBars = new Set(manual.map((chord) => Number(chord.bar)));
    return {
      ...updatedTimeline,
      chords: (updatedTimeline.chords || []).filter((chord) => !manualBars.has(Number(chord.bar))).concat(manual)
        .sort((left, right) => Number(left.bar) - Number(right.bar) || Number(left.startFraction || 0) - Number(right.startFraction || 0))
    };
  }

  function analysisBadges() {
    const timeline = project.timeline || {};
    const mode = timeline.keyMode === "minor" ? "minor" : "major";
    const version = Number(timeline.analysisVersion || 1);
    const journey = tools.keyJourneyLabel(timeline);
    document.querySelector("#analysis-summary").innerHTML = `
      <span><strong>${escapeHtml(timeline.key || "—")} ${mode}</strong><small>Starting key · ${escapeHtml(journey)}</small></span>
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

  function seventhEvidenceTeaching(events) {
    const event = events.find((item) => /(?:m7|7)$/.test(String(item.symbol || "")) && Number.isFinite(Number(item.seventhCoreRatio)));
    if (!event) return "";
    const ratio = Math.round(Number(event.seventhCoreRatio) * 100);
    return `Audio ♭7 evidence is ${ratio}% as strong as the core chord tones. A seventh label is kept only when that note has direct audio support.`;
  }

  function renderNotationToggle() {
    const nns = reviewChordDisplay === "nns";
    showChordsButton.setAttribute("aria-pressed", String(!nns));
    showNnsButton.setAttribute("aria-pressed", String(nns));
  }

  async function setReviewChordDisplay(display) {
    reviewChordDisplay = display === "nns" ? "nns" : "letters";
    practiceSession = { ...practiceSession, chordDisplay: reviewChordDisplay, updatedAt: new Date().toISOString() };
    renderReview();
    await tools.saveSession(practiceSession);
  }

  function mapButtonForBar(bar) {
    const events = eventsForBar(bar);
    const needsAttention = barNeedsAttention(bar);
    const keyContext = keyContextForBar(bar);
    const keyChange = keyContext.region.startBar === bar && bar > 1;
    const symbols = events.map((event) => chordForReview(event.symbol, bar)).join(" · ") || "No chord";
    const externalState = barExternalState(bar);
    const confidenceLabel = percent(barConfidence(bar));
    const stateLabel = needsAttention ? `${confidenceLabel} confidence · Needs attention` : `${confidenceLabel} confident${externalState ? ` · ${externalState}` : ""}`;
    const button = document.createElement("button");
    button.type = "button";
    button.className = `review-map-bar ${needsAttention ? "needs-attention" : "is-accepted"}${bar === selectedBar ? " is-selected" : ""}${keyChange ? " has-key-change" : ""}`;
    button.dataset.bar = String(bar);
    button.setAttribute("aria-pressed", String(bar === selectedBar));
    button.setAttribute("aria-label", `Bar ${bar}, ${symbols}, ${stateLabel}. Select to review without autoplay.`);
    button.innerHTML = `${keyChange ? `<em class="review-map-bar__key">New key · ${escapeHtml(keyContext.key)} ${escapeHtml(keyContext.keyMode)}</em>` : ""}<span>Bar ${bar}</span><strong>${escapeHtml(symbols)}</strong><small>${escapeHtml(stateLabel)}</small>`;
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
    const editable = !showingPreview;
    const startMs = Number(timeline.barStartsMs?.[bar - 1] || events[0]?.startMs || 0);
    const needsAttention = barNeedsAttention(bar);
    const reasons = Array.from(new Set(events.flatMap((event) => event.reviewReasons || [])));
    const matches = matchingBarsFor(events[0]?.repeatedSectionGroup, bar);
    const chordNames = events.map((event) => event.symbol === "N.C." ? "No chord" : event.symbol || "No chord").join(" ");
    const keyContext = keyContextForBar(bar, timeline);
    const displayedChords = events.map((event) => chordForReview(event.symbol, bar)).join(" · ") || "No chord";
    const teaching = selectedChordTeaching(events, displayedChords, bar);
    const seventhTeaching = seventhEvidenceTeaching(events);
    const explorerTargets = events.map((event) => explorerTargetForChord(event.symbol, bar)).filter(Boolean);
    const keyOptions = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"].map((key) => `<option${key === keyContext.key ? " selected" : ""}>${key}</option>`).join("");
    const startsKeyRegion = keyContext.region.startBar === bar;
    const externalState = barExternalState(bar);
    const confidenceLabel = percent(barConfidence(bar));
    const stateLabel = showingPreview
      ? needsAttention ? `${confidenceLabel} confidence · Preview needs attention` : `${confidenceLabel} confident · Preview${externalState ? ` · ${externalState}` : ""}`
      : needsAttention ? `${confidenceLabel} confidence · Needs attention` : `${confidenceLabel} confident${externalState ? ` · ${externalState}` : ""}`;
    editor.innerHTML = `
      <div class="review-editor__head">
        <div><p class="songs-kicker">Selected measure</p><h3>Bar ${bar}</h3></div>
        <span class="review-editor__status ${needsAttention ? "needs-attention" : "is-accepted"}">${escapeHtml(stateLabel)}</span>
      </div>
      ${reviewChordDisplay === "nns" ? `<p class="review-editor__notation"><span>Nashville number${events.length === 2 ? "s" : ""}</span><strong>${escapeHtml(displayedChords)}</strong></p>` : ""}
      <div class="review-editor__fields">
        <label>${reviewChordDisplay === "nns" ? "Chord names (editing)" : `Chord${events.length === 2 ? "s" : ""}`}<input data-chord type="text" value="${escapeHtml(chordNames)}" aria-label="Chord${events.length === 2 ? "s" : ""} for bar ${bar}"${editable ? "" : " disabled"}><small>${editable ? "Enter one chord, or two chords separated by a space." : "Accept the preview before making corrections."}</small></label>
        <label>Bar downbeat<input data-time type="number" min="0" max="${project.audio.durationMs}" step="10" value="${Math.round(startMs)}" aria-label="Downbeat milliseconds for bar ${bar}"${editable ? "" : " disabled"}><small>${formatTime(startMs)} into the recording</small></label>
        <label>Section key<select data-section-key aria-label="Section key for bar ${bar}"${editable ? "" : " disabled"}>${keyOptions}</select><small>NNS is measured from this key until the next marker.</small></label>
        <label>Section mode<select data-section-mode aria-label="Section mode for bar ${bar}"${editable ? "" : " disabled"}><option value="major"${keyContext.keyMode === "major" ? " selected" : ""}>Major</option><option value="minor"${keyContext.keyMode === "minor" ? " selected" : ""}>Minor</option></select><small>${startsKeyRegion ? `This section starts at bar ${keyContext.region.startBar}.` : `Current section starts at bar ${keyContext.region.startBar}.`}</small></label>
      </div>
      ${teaching ? `<p class="review-editor__teaching">${escapeHtml(teaching)}</p>` : ""}
      ${seventhTeaching ? `<p class="review-editor__teaching" data-seventh-evidence>${escapeHtml(seventhTeaching)}</p>` : ""}
      <p class="review-editor__reason">${escapeHtml(reasons.join(" ") || "Strong audio and song-context agreement.")}</p>
      <div class="review-editor__actions">
        <button class="songs-button" data-play-bar type="button">Play from bar ${bar}</button>
        ${explorerTargets.length === 1 ? `<a class="songs-button is-quiet" href="${escapeHtml(explorerTargets[0].url)}" target="_blank" rel="noopener">Explore ${escapeHtml(explorerTargets[0].root)}${reviewChordDisplay === "nns" ? ` (${escapeHtml(displayedChords)})` : ""} on the fretboard</a>` : ""}
        ${editable ? `<button class="songs-button is-primary" data-accept-bar type="button">${needsAttention ? "Accept this bar" : "Mark for review"}</button>` : ""}
        ${editable && matches.length ? `<button class="songs-button is-quiet" data-apply-repeat type="button">Apply chord to ${matches.length} matching bar${matches.length === 1 ? "" : "s"}</button>` : ""}
        ${editable ? `<button class="songs-button is-quiet" data-key-boundary type="button">${startsKeyRegion && bar > 1 ? "Remove key change here" : startsKeyRegion ? "Starting key" : `Start a key change at bar ${bar}`}</button>` : ""}
      </div>`;
    editor.querySelector("[data-play-bar]").onclick = () => {
      audio.currentTime = Number(timeline.barStartsMs?.[bar - 1] || 0) / 1000;
      audio.play().catch(() => {});
    };
    if (editable) {
      const chordField = editor.querySelector("[data-chord]");
      const commitChordField = () => {
        const value = chordField.value.trim();
        replaceBarChords(bar, /^(?:N\.?C\.?|NO\s+CHORD|REST)$/i.test(value) ? ["N.C."] : value.split(/\s+/)); renderReview(); updateConfirmation(); queueSave();
      };
      chordField.onchange = commitChordField;
      chordField.onkeydown = (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        commitChordField();
      };
      const commitSectionKey = () => updateSectionKey(bar, editor.querySelector("[data-section-key]").value, editor.querySelector("[data-section-mode]").value).catch((error) => { status.textContent = error.message; });
      editor.querySelector("[data-section-key]").onchange = commitSectionKey;
      editor.querySelector("[data-section-mode]").onchange = commitSectionKey;
    }
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
    editor.querySelector("[data-key-boundary]")?.addEventListener("click", () => toggleKeyBoundary(bar).catch((error) => { status.textContent = error.message; }));
  }

  async function applyKeyRegions(regions, message) {
    const request = ++keyChangeRequest;
    const previousTimeline = project.timeline;
    const normalized = tools.normalizeKeyRegions(regions, barCount(), previousTimeline.key, previousTimeline.keyMode);
    project.timeline = { ...previousTimeline, key: normalized[0].key, keyMode: normalized[0].keyMode, keyRegions: normalized };
    analysisBadges(); renderReview(); updateConfirmation();
    if (!project.timeline.analysisState) { queueSave(); return; }
    try {
      reanalyzePanel.hidden = false;
      reanalyzeStatus.textContent = message;
      const updated = await analysisClient.redecodeRegions(previousTimeline, normalized, (_stage, detail) => { if (request === keyChangeRequest) reanalyzeStatus.textContent = detail; });
      if (request !== keyChangeRequest) return;
      project.timeline = { ...preserveManualChordEdits(updated, previousTimeline), confirmationState: "detected" };
      analysisBadges(); renderReview(); updateConfirmation(); await persist();
      reanalyzeStatus.textContent = `Key journey updated: ${tools.keyJourneyLabel(project.timeline)}. The audio was not transposed.`;
    } catch (error) {
      if (request !== keyChangeRequest) return;
      project.timeline = previousTimeline; analysisBadges(); renderReview(); updateConfirmation(); reanalyzeStatus.textContent = error.message;
    }
  }

  function updateSectionKey(bar, key, keyMode) {
    const timeline = project.timeline;
    const regions = tools.normalizeKeyRegions(timeline.keyRegions, barCount(), timeline.key, timeline.keyMode);
    const active = regions.find((region) => bar >= region.startBar && bar <= region.endBar) || regions[0];
    const updated = regions.map((region) => region.startBar === active.startBar ? { ...region, key, keyMode, confidence: 1, source: "manual" } : region);
    return applyKeyRegions(updated, `Rechecking the section from bar ${active.startBar} in ${key} ${keyMode}…`);
  }

  function toggleKeyBoundary(bar) {
    if (bar <= 1) return;
    const timeline = project.timeline;
    const regions = tools.normalizeKeyRegions(timeline.keyRegions, barCount(), timeline.key, timeline.keyMode);
    const existing = regions.find((region) => region.startBar === bar);
    const updated = existing
      ? regions.filter((region) => region.startBar !== bar)
      : [...regions, { startBar: bar, key: keyContextForBar(bar, timeline).key, keyMode: keyContextForBar(bar, timeline).keyMode, confidence: 1, source: "manual" }];
    return applyKeyRegions(updated, existing ? `Removing the key change at bar ${bar}…` : `Adding a key change at bar ${bar}…`);
  }

  function renderReview() {
    const map = reviewMapElement();
    if (!map) throw new Error("The visual song map is unavailable. Reload the page and try again.");
    const count = barCount();
    if (!selectedBar || selectedBar > count) selectedBar = Array.from({ length: count }, (_item, index) => index + 1).find(barNeedsAttention) || 1;
    const heading = document.querySelector("#review-heading");
    const description = document.querySelector("#review-description");
    const reviewAll = document.querySelector("#review-all");
    const journey = document.querySelector("#review-key-journey");
    if (showingPreview) {
      heading.textContent = "Improved Analysis Preview";
      description.textContent = "This is the new key-aware map. Coral bars need review; amber bars were accepted automatically. Nothing is saved until you choose Use this analysis.";
    } else {
      heading.textContent = "Song Map";
      description.textContent = "See the whole progression at once. Amber bars are accepted; coral bars need attention. Select any bar to hear and correct it.";
    }
    reviewAll.hidden = showingPreview;
    journey.textContent = `Key journey: ${tools.keyJourneyLabel(activeTimeline())}`;
    // The paste-a-chart workflow is intentionally dormant. Keep the provider
    // boundary available for a future permitted integration without asking the
    // player to copy a public chart into Review.
    referencePanel.hidden = true;
    renderNotationToggle();
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
    const commonChords = [...chordCounts.entries()].sort((left, right) => right[1] - left[1]).slice(0, 7).map(([symbol, count]) => `${symbol === "N.C." ? "No chord" : symbol} (${count})`).join(", ");
    return `Preview: ${timeline.key} ${timeline.keyMode} · ${timeline.meter} · ${timeline.tempo} BPM · ${attention} attention bar${attention === 1 ? "" : "s"}. Common chords: ${commonChords || "No chord"}.`;
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
    reanalyzePanel.hidden = true;
    reanalyzeButton.hidden = true;
    previewRhythmButton.hidden = true;
    reanalyzePreview.hidden = true;
  }

  function setUpgradeVisibility(upgrading) {
    setupSummary.hidden = upgrading;
    analysisSummary.hidden = upgrading;
    audio.hidden = upgrading;
    reviewPanel.hidden = upgrading;
    referencePanel.hidden = true;
    startPlayButton.hidden = upgrading;
    confirmButton.hidden = true;
  }

  async function upgradeLegacyAnalysis(useExistingKeyHint = true) {
    if (analysisRunning) return;
    analysisRunning = true; pendingAnalysis = null; showingPreview = false;
    setUpgradeVisibility(true);
    reanalyzePanel.hidden = false;
    reanalyzeButton.hidden = true;
    previewRhythmButton.hidden = true;
    reanalyzePreview.hidden = true;
    document.querySelector("#reanalyze-title").textContent = "Updating Song Map";
    document.querySelector("#reanalyze-copy").textContent = "Replacing the earlier chord analysis with the current key-aware method. Your audio stays on this device.";
    reanalyzeStatus.textContent = "Preparing the local recording…";
    try {
      const result = await analysisClient.analyzeFile(audioFile, {
        tempoHint: Number(project.timeline.tempo),
        ...(useExistingKeyHint ? { keyHint: project.timeline.key, keyModeHint: project.timeline.keyMode || "major" } : {})
      }, (stage, detail) => { reanalyzeStatus.textContent = `${stage}: ${detail}`; });
      project.timeline = { ...result.analysis, confirmationState: "detected" };
      selectedBar = 0;
      await persist();
      setControlsFromTimeline(); analysisBadges(); configureReanalysis();
      setUpgradeVisibility(false); renderReview(); updateConfirmation();
      status.textContent = "Song Map updated with the current local analysis method. Review the highlighted bars before playing.";
    } catch (error) {
      document.querySelector("#reanalyze-title").textContent = "Song Map update did not finish";
      document.querySelector("#reanalyze-copy").textContent = "The older map is not offered as an alternative. Try the current local analysis again.";
      reanalyzeStatus.textContent = error.message || "The current local analysis could not be completed.";
      reanalyzeButton.textContent = "Try update again";
      reanalyzeButton.hidden = false;
    } finally {
      analysisRunning = false;
      reanalyzeButton.disabled = false;
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
      const options = { tempo: Number(fields.tempo.value), meter: fields.meter.value, keyHint: fields.key.value, keyModeHint: fields.keyMode.value };
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
    const requestedKey = fields.key.value;
    const requestedMode = fields.keyMode.value;
    if (Number(project.timeline.analysisVersion || 1) < 2 || !project.timeline.analysisState) {
      project.timeline.key = requestedKey; project.timeline.keyMode = requestedMode; queueSave(); analysisBadges(); renderReview(); return;
    }
    const request = ++keyChangeRequest;
    const previousTimeline = project.timeline;
    const immediateRegions = tools.normalizeKeyRegions(previousTimeline.keyRegions, barCount(), previousTimeline.key, previousTimeline.keyMode)
      .map((region, index) => index ? region : { ...region, key: requestedKey, keyMode: requestedMode, confidence: 1, source: "manual" });
    project.timeline = { ...previousTimeline, key: requestedKey, keyMode: requestedMode, keyRegions: immediateRegions };
    analysisBadges(); renderReview(); updateConfirmation();
    try {
      reanalyzePanel.hidden = false;
      reanalyzeStatus.textContent = `Song Map is now shown in ${requestedKey} ${requestedMode}. Rechecking chord choices…`;
      const manualLaterRegions = immediateRegions.slice(1).some((region) => region.source === "manual");
      const updated = manualLaterRegions
        ? await analysisClient.redecodeRegions(previousTimeline, immediateRegions, (_stage, detail) => { if (request === keyChangeRequest) reanalyzeStatus.textContent = detail; })
        : await analysisClient.redecode(previousTimeline, requestedKey, requestedMode, (_stage, detail) => { if (request === keyChangeRequest) reanalyzeStatus.textContent = detail; });
      if (request !== keyChangeRequest) return;
      project.timeline = { ...preserveManualChordEdits(updated, previousTimeline), confirmationState: "detected" };
      selectedBar = 0; analysisBadges(); renderReview(); updateConfirmation(); await persist();
      reanalyzeStatus.textContent = `Song Map updated for ${requestedKey} ${requestedMode}. The audio was not transposed.`;
    } catch (error) {
      if (request !== keyChangeRequest) return;
      project.timeline = previousTimeline; reanalyzeStatus.textContent = error.message; setControlsFromTimeline(); analysisBadges(); renderReview(); updateConfirmation();
    }
  }

  async function initialize() {
    project = await tools.loadProject(projectId);
    if (!project) throw new Error("That local song is no longer stored in this browser.");
    audioFile = await tools.readAudio(project.audio?.opfsPath || `${project.id}.audio`).catch(() => null);
    if (!audioFile) throw new Error("The local recording is missing. Return to Songs and relink the original file with the same fingerprint.");
    if (!analysisClient) throw new Error("Local analysis controls are unavailable. Reload the page and try again.");
    practiceSession = { ...tools.sessionDefaults(projectId), ...(await tools.loadSession(projectId) || {}) };
    reviewChordDisplay = practiceSession.chordDisplay === "nns" ? "nns" : "letters";
    objectUrl = URL.createObjectURL(audioFile); audio.src = objectUrl;
    document.querySelector("#setup-title").textContent = "Review Song";
    document.querySelector("#setup-track-name").textContent = project.title;
    document.querySelector("#setup-song-title").value = project.title;
    document.querySelector("#start-play").href = `/play/${encodeURIComponent(project.id)}`;
    const needsUpgrade = Number(project.timeline?.analysisVersion || 1) < 2;
    setControlsFromTimeline();
    if (!needsUpgrade) analysisBadges();
    configureReanalysis();
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
    reanalyzeButton.onclick = () => upgradeLegacyAnalysis(needsUpgrade);
    previewRhythmButton.onclick = runFreshAnalysis;
    document.querySelector("#accept-reanalysis").onclick = acceptReanalysis;
    document.querySelector("#discard-reanalysis").onclick = () => { pendingAnalysis = null; showingPreview = false; selectedBar = 0; reanalyzePreview.hidden = true; reanalyzeStatus.textContent = "Current map kept."; setControlsFromTimeline(); configureReanalysis(); renderReview(); updateConfirmation(); };
    document.querySelector("#validate-reference").onclick = async () => { try { await applyReferenceValidation(); } catch (error) { referenceStatus.textContent = error.message; } };
    showChordsButton.onclick = () => setReviewChordDisplay("letters").catch((error) => { status.textContent = error.message; });
    showNnsButton.onclick = () => setReviewChordDisplay("nns").catch((error) => { status.textContent = error.message; });
    confirmButton.onclick = async () => { project.timeline.confirmationState = "confirmed"; await persist(); global.location.assign(`/play/${encodeURIComponent(project.id)}`); };
    app.hidden = false;
    if (needsUpgrade) await upgradeLegacyAnalysis(true);
    else if (Number(project.timeline.analysisState?.qualityCalibrationVersion || 0) < 9) await upgradeLegacyAnalysis(false);
    else { renderReview(); updateConfirmation(); }
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
