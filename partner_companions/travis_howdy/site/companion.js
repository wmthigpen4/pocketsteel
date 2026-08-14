(() => {
  "use strict";

  const root = document.querySelector("[data-companion-url]");
  if (!root) return;

  const presentation = document.documentElement.dataset.presentation || "full";
  const companionUrl = new URL(root.dataset.companionUrl, window.location.origin);
  if (companionUrl.origin !== window.location.origin) {
    throw new Error("Companion data must be same-origin.");
  }

  const state = {
    data: null,
    timeMs: 0,
    speed: 1,
    playing: false,
    loop: false,
    selectedPhraseId: null,
    selectedMode: null,
    selectedLayer: null,
    searchQuery: "",
    frameId: null,
    previousFrameTime: null,
    sourceObjectUrls: {},
    sourceLoadPromises: {},
    songTimelineSegments: [],
  };

  const q = (selector) => root.querySelector(selector);
  const qa = (selector) => Array.from(root.querySelectorAll(selector));
  const node = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = String(text);
    return element;
  };
  const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));
  const formatTime = (milliseconds) => {
    const totalSeconds = Math.max(0, Math.floor(Number(milliseconds || 0) / 1000));
    return `${Math.floor(totalSeconds / 60)}:${String(totalSeconds % 60).padStart(2, "0")}`;
  };
  const formatLessonMoment = (milliseconds) => {
    const totalSeconds = Math.max(0, Math.floor(Number(milliseconds || 0) / 1000));
    return `${Math.floor(totalSeconds / 60)}:${String(totalSeconds % 60).padStart(2, "0")}`;
  };
  const currentPhrase = () => state.data.phrases.find((item) => item.id === state.selectedPhraseId) || state.data.phrases[0];
  const eventAt = (milliseconds) => {
    const events = state.data.events;
    return events.find((item) => milliseconds >= item.startMs && milliseconds < item.endMs) || events[events.length - 1];
  };
  const chordAt = (milliseconds) => state.data.chordTimeline.find(
    (item) => milliseconds >= item.startMs && milliseconds < item.endMs,
  ) || state.data.chordTimeline[state.data.chordTimeline.length - 1];
  const chordIndex = (chord) => state.data.chordTimeline.findIndex((item) => item.id === chord.id);
  const nextChord = (chord) => state.data.chordTimeline[Math.min(
    state.data.chordTimeline.length - 1,
    chordIndex(chord) + 1,
  )];
  const eventIndex = (event) => state.data.events.findIndex((item) => item.id === event.id);
  const nextEvent = (event) => state.data.events[Math.min(state.data.events.length - 1, eventIndex(event) + 1)];
  const hasChordChart = () => state.data.chordTimeline.every((item) => item.symbol && item.tabNotes?.length);
  const hasFullSongChordChart = () => (
    Array.isArray(state.data.songChordTimeline) && state.data.songChordTimeline.length > 0
  );
  const mediaScopesFor = (data) => {
    const media = data.media || {};
    const scopes = media.scopes || {};
    const fullDuration = Number(media.durationMs || 0);
    const fallback = { id: "taught-solo", label: "Taught solo", startMs: 0, endMs: fullDuration, durationMs: fullDuration };
    return {
      fullSong: scopes.fullSong || { id: "full-song", label: "Full song", startMs: 0, endMs: fullDuration, durationMs: fullDuration },
      taughtSolo: scopes.taughtSolo || fallback,
    };
  };
  const mediaScopes = () => mediaScopesFor(state.data);
  const mediaScopeForLayer = (layerId = state.selectedLayer) => (
    layerId === "play-along" ? mediaScopes().fullSong : mediaScopes().taughtSolo
  );
  const currentMediaScope = () => mediaScopeForLayer();
  const absoluteMediaTime = (scope, relativeMs) => Number(scope.startMs) + Number(relativeMs || 0);
  const relativeMediaTime = (scope, absoluteMs) => clamp(
    Number(absoluteMs || 0) - Number(scope.startMs),
    0,
    Number(scope.durationMs),
  );
  const taughtSoloTimeAt = (absoluteMs) => {
    const solo = mediaScopes().taughtSolo;
    if (absoluteMs < Number(solo.startMs) || absoluteMs >= Number(solo.endMs)) return null;
    return absoluteMs - Number(solo.startMs);
  };
  const scopeUsesSoloAudio = (scope) => (
    scope.id === mediaScopes().taughtSolo.id
    && !state.data.media.audioUrl
    && Boolean(state.data.media.soloAudioUrl)
  );
  const sourceUrlForScope = (scope) => (
    scopeUsesSoloAudio(scope) ? state.data.media.soloAudioUrl : state.data.media.audioUrl
  );
  const audioTimeForScope = (scope, relativeMs) => (
    scopeUsesSoloAudio(scope) ? Number(relativeMs || 0) : absoluteMediaTime(scope, relativeMs)
  );
  const scopeTimeFromAudio = (scope, audioMs) => (
    scopeUsesSoloAudio(scope)
      ? clamp(Number(audioMs || 0), 0, Number(scope.durationMs))
      : relativeMediaTime(scope, audioMs)
  );

  function validateCompanion(data) {
    if (!data || data.schemaVersion !== "lesson_companion_v1") throw new Error("Unsupported companion artifact.");
    if (data.runtimeMode !== "published_deterministic" || data.modelCallsAllowed !== false) {
      throw new Error("This preview accepts only a deterministic published artifact.");
    }
    if (!Array.isArray(data.events) || !data.events.length || !Array.isArray(data.phrases)) {
      throw new Error("The companion artifact is incomplete.");
    }
    const scopes = mediaScopesFor(data);
    for (const scope of [scopes.fullSong, scopes.taughtSolo]) {
      if (
        !Number.isFinite(Number(scope.startMs))
        || !Number.isFinite(Number(scope.endMs))
        || Number(scope.endMs) <= Number(scope.startMs)
        || Number(scope.durationMs) !== Number(scope.endMs) - Number(scope.startMs)
        || Number(scope.endMs) > Number(data.media.durationMs)
      ) throw new Error(`Invalid media scope ${scope.id || "unknown"}.`);
    }
    if (Number(data.events[data.events.length - 1].endMs) !== Number(scopes.taughtSolo.durationMs)) {
      throw new Error("The taught solo scope must end with the final authored event.");
    }
    const eventIds = new Set(data.events.map((item) => item.id));
    if (eventIds.size !== data.events.length) throw new Error("Companion event IDs must be unique.");
    data.phrases.forEach((phrase) => phrase.eventIds.forEach((id) => {
      if (!eventIds.has(id)) throw new Error(`Phrase references missing event ${id}.`);
    }));
    data.events.forEach((event) => {
      if (!event.coachingCue) return;
      const source = event.sourceMoment;
      if (!source || source.quoteKind !== "verbatim_excerpt" || source.excerpt !== event.coachingCue) {
        throw new Error(`Coaching cue ${event.id} must be a verbatim sourced excerpt.`);
      }
      if (!Number.isFinite(Number(source.lessonTimeMs)) || Number(source.lessonTimeMs) < 0) {
        throw new Error(`Coaching cue ${event.id} has no lesson timestamp.`);
      }
    });
    if (Array.isArray(data.songChordTimeline) && data.songChordTimeline.length) {
      let previousSongChordEnd = 0;
      data.songChordTimeline.forEach((chord) => {
        if (
          Number(chord.startMs) !== previousSongChordEnd
          || Number(chord.endMs) <= Number(chord.startMs)
          || !chord.symbol
          || !chord.nns
        ) throw new Error("The full-song chord timeline must be contiguous and fully labeled.");
        previousSongChordEnd = Number(chord.endMs);
      });
      if (previousSongChordEnd !== Number(scopes.fullSong.durationMs)) {
        throw new Error("The full-song chord timeline must cover the complete song scope.");
      }
    }
  }

  function renderPreviewMarker() {
    const marker = q("[data-preview-marker]");
    if (!marker) return;
    const sha = String(state.data.buildSha || "local").slice(0, 12);
    marker.textContent = presentation === "embed-demo"
      ? `Owner preview · ${state.data.revision} · ${sha}`
      : `${state.data.release.previewLabel} · ${state.data.revision} · ${sha}`;
    const title = q("[data-companion-title]");
    if (title && presentation === "embed-demo") title.textContent = "“Howdy” practice companion";
  }

  function renderLayerTabs() {
    const container = q("[data-layer-tabs]");
    if (!container) return;
    container.replaceChildren();
    state.data.layers.forEach((layer) => {
      const button = node("button", `layer-tab${layer.id === state.selectedLayer ? " is-active" : ""}`);
      button.type = "button";
      button.dataset.layerId = layer.id;
      button.setAttribute("aria-pressed", layer.id === state.selectedLayer ? "true" : "false");
      const compactLabels = {
        "lesson-map": "Map",
        "phrase-practice": "Solo",
        "play-along": "Full Song",
        "explore": "Explore",
      };
      const fullLabels = { "phrase-practice": "Taught Solo", "play-along": "Full Song" };
      button.append(
        node("strong", "", presentation === "embed-demo" ? compactLabels[layer.id] : (fullLabels[layer.id] || layer.label)),
        node("span", "", layer.description),
      );
      button.addEventListener("click", () => setLayer(layer.id));
      container.append(button);
    });
  }

  function setSpeed(value) {
    state.speed = Number(value);
    qa("[data-speed]").forEach((item) => item.classList.toggle("is-active", Number(item.dataset.speed) === state.speed));
    const audio = q("[data-audio]");
    if (audio?.src) audio.playbackRate = state.speed;
  }

  function setLayer(layerId, options = {}) {
    const layer = state.data.layers.find((item) => item.id === layerId);
    if (!layer) return;
    pausePlayback();
    const previousScope = currentMediaScope();
    const previousAbsoluteTime = absoluteMediaTime(previousScope, state.timeMs);
    state.selectedLayer = layer.id;
    root.dataset.activeLayer = layer.id;
    const nextScope = currentMediaScope();
    state.timeMs = options.preserveTime
      ? relativeMediaTime(nextScope, previousAbsoluteTime)
      : 0;
    const studyControls = q("[data-study-controls]");
    const explorePanel = q("[data-explore-panel]");
    if (studyControls) studyControls.hidden = layer.id !== "phrase-practice";
    if (explorePanel) explorePanel.hidden = layer.id !== "explore";
    if (layer.id === "phrase-practice") {
      state.selectedMode = "follow-solo";
      state.loop = true;
      setSpeed(0.5);
      if (!options.preserveTime) seekTo(currentPhrase().startMs);
    } else if (layer.id === "play-along") {
      state.selectedMode = hasChordChart() ? "chord-foundation" : "follow-solo";
      state.loop = false;
      setSpeed(1);
      if (!options.preserveTime) seekTo(0);
    } else {
      state.loop = false;
    }
    const loopButton = q('[data-action="loop"]');
    if (loopButton) loopButton.setAttribute("aria-pressed", state.loop ? "true" : "false");
    const layerCopy = {
      "lesson-map": ["Lesson map", "Understand the complete eight-bar route", "Select a phrase or chord bar to choose where your practice begins.", "Overview only · playback is paused"],
      "phrase-practice": ["Taught solo", "Study the exact eight-bar lesson solo", "Use Previous and Next to study the tab and fretboard. The player is scoped to the taught solo inside the full backing track.", "Solo window · 50% · phrase loop on"],
      "play-along": ["Full song", "Play against the complete backing track", "This player uses the full song. The taught solo is marked at its exact position and keeps its own tab, fretboard, and phrase loops in the Solo tab.", "Full track · 100% · no solo animation"],
      "explore": ["Explore", "Compare only positions shown in the lesson", "These are fixed lesson-demonstrated comparisons, not generated substitutes for Travis’s route.", "Playback paused · primary route unchanged"],
    }[layer.id];
    const kicker = q("[data-layer-kicker]");
    const title = q("[data-layer-title]");
    const description = q("[data-layer-description]");
    const behavior = q("[data-layer-behavior]");
    if (kicker) kicker.textContent = layerCopy[0];
    if (title) title.textContent = layerCopy[1];
    if (description) description.textContent = layerCopy[2];
    if (behavior) behavior.textContent = layerCopy[3];
    renderLayerTabs();
    renderModes();
    renderMediaScope();
    renderPhraseMap();
    renderChordChart();
    renderSongTimeline();
    updateFrame();
  }

  function renderModes() {
    const container = q("[data-mode-switcher]");
    if (!container) return;
    container.replaceChildren();
    state.data.modes.forEach((mode) => {
      const button = node("button", `mode-button${mode.id === state.selectedMode ? " is-active" : ""}`);
      button.type = "button";
      button.dataset.modeId = mode.id;
      button.setAttribute("aria-pressed", mode.id === state.selectedMode ? "true" : "false");
      button.append(node("strong", "", mode.label), node("span", "", mode.description));
      button.addEventListener("click", () => {
        if (mode.id === "chord-foundation" && hasChordChart()) {
          state.selectedMode = mode.id;
          renderModes();
          updateFrame();
          return;
        }
        state.selectedMode = mode.id;
        renderModes();
        updateFrame();
      });
      container.append(button);
    });
  }

  function renderLessonFacts() {
    const key = q("[data-key-label]");
    const meter = q("[data-meter-label]");
    const tempo = q("[data-tempo-label]");
    const chartKey = q("[data-chart-key]");
    if (key) key.textContent = `Key ${state.data.display.key}`;
    if (meter) meter.textContent = state.data.display.meter;
    if (tempo) tempo.textContent = state.data.display.tempoBpm ? `${state.data.display.tempoBpm} BPM` : "Tempo pending";
    if (chartKey) chartKey.textContent = state.data.display.key;
  }

  function selectScopeAudio(scope) {
    const audio = q("[data-audio]");
    if (!audio) return;
    const play = q('[data-action="play"]');
    const rawUrl = sourceUrlForScope(scope);
    if (!rawUrl) return;
    const mediaUrl = new URL(rawUrl, window.location.origin);
    if (mediaUrl.origin !== window.location.origin) throw new Error("Backing audio must be same-origin.");
    const sourceKey = mediaUrl.href;
    const applySource = (sourceUrl) => {
      if (audio.dataset.scopeId === scope.id && audio.src === sourceUrl) return;
      audio.dataset.scopeId = scope.id;
      audio.src = sourceUrl;
      audio.load();
    };
    const cachedObjectUrl = state.sourceObjectUrls[sourceKey];
    if (cachedObjectUrl) {
      applySource(cachedObjectUrl);
      if (play) {
        play.disabled = false;
        play.textContent = "▶";
        play.setAttribute("aria-label", "Play backing track");
      }
      return;
    }
    const note = q("[data-transport-note]");
    if (play) {
      play.disabled = true;
      play.textContent = "…";
      play.setAttribute("aria-label", `Loading ${scope.label.toLowerCase()}`);
    }
    if (note) note.textContent = `Loading ${scope.label.toLowerCase()} audio…`;
    if (!state.sourceLoadPromises[sourceKey]) {
      state.sourceLoadPromises[sourceKey] = fetch(mediaUrl.href, { credentials: "same-origin", cache: "force-cache" })
        .then((response) => {
          if (!response.ok) throw new Error(`${scope.label} audio returned ${response.status}.`);
          return response.blob();
        })
        .then((blob) => {
          state.sourceObjectUrls[sourceKey] = URL.createObjectURL(blob);
          if (currentMediaScope().id === scope.id) {
            applySource(state.sourceObjectUrls[sourceKey]);
            if (play) {
              play.disabled = false;
              play.textContent = "▶";
              play.setAttribute("aria-label", "Play backing track");
            }
            if (note) note.textContent = scope.id === mediaScopes().fullSong.id
              ? "Complete same-origin backing track loaded · audio rights approval pending."
              : `Taught solo window ${formatTime(scope.startMs)}–${formatTime(scope.endMs)} · exact excerpt from the same source track.`;
          }
        })
        .catch((error) => {
          if (play) {
            play.disabled = false;
            play.textContent = "▶";
            play.setAttribute("aria-label", `Retry ${scope.label.toLowerCase()}`);
          }
          if (note) note.textContent = `${scope.label} unavailable: ${error.message}`;
        })
        .finally(() => { delete state.sourceLoadPromises[sourceKey]; });
    }
  }

  function renderMediaScope() {
    const scopes = mediaScopes();
    const scope = currentMediaScope();
    const fullDuration = q("[data-full-song-duration]");
    const soloDuration = q("[data-taught-solo-duration]");
    if (fullDuration) fullDuration.textContent = formatTime(scopes.fullSong.durationMs);
    if (soloDuration) soloDuration.textContent = formatTime(scopes.taughtSolo.durationMs);
    const kicker = q("[data-scope-kicker]");
    const title = q("[data-scope-title]");
    const description = q("[data-scope-description]");
    const jump = q('[data-action="jump-to-solo"]');
    const isFullSong = scope.id === scopes.fullSong.id;
    if (kicker) kicker.textContent = isFullSong ? "Full song" : "Lesson solo";
    if (title) title.textContent = `${scope.label} · ${formatTime(scope.durationMs)}`;
    if (description) description.textContent = isFullSong
      ? `Complete backing track. The taught solo begins at ${formatTime(scopes.taughtSolo.startMs)}.`
      : `The eight-bar solo Travis teaches, heard from ${formatTime(scopes.taughtSolo.startMs)} to ${formatTime(scopes.taughtSolo.endMs)} inside the full song.`;
    if (jump) jump.hidden = !isFullSong;
    const seek = q("[data-seek]");
    const duration = q("[data-duration]");
    if (seek) {
      seek.max = String(scope.durationMs);
      seek.value = String(Math.round(state.timeMs));
    }
    if (duration) duration.textContent = formatTime(scope.durationMs);
    const loop = q('[data-action="loop"]');
    if (loop) loop.hidden = isFullSong;
    const note = q("[data-transport-note]");
    if (note) note.textContent = isFullSong
      ? "Complete same-origin backing track loaded · audio rights approval pending."
      : `Taught solo window ${formatTime(scopes.taughtSolo.startMs)}–${formatTime(scopes.taughtSolo.endMs)} · same source track.`;
    selectScopeAudio(scope);
  }

  function configureMediaScopeActions() {
    q('[data-action="open-full-song"]')?.addEventListener("click", () => {
      setLayer("play-along");
      seekTo(0);
    });
    q('[data-action="open-taught-solo"]')?.addEventListener("click", () => {
      setLayer("phrase-practice");
      seekTo(0);
    });
    q('[data-action="jump-to-solo"]')?.addEventListener("click", () => {
      setLayer("phrase-practice");
      seekTo(0);
    });
  }

  function normalizeSearch(value) {
    return String(value || "").toLowerCase().normalize("NFKD").replace(/[^a-z0-9#]+/g, " ").trim();
  }

  function lessonMoments() {
    if (Array.isArray(state.data.lessonMoments) && state.data.lessonMoments.length) return state.data.lessonMoments;
    return state.data.events.map((event) => ({
      id: `index-${event.id}`,
      eventId: event.id,
      lessonTimeMs: event.sourceMoment?.lessonTimeMs,
      label: event.movement.replaceAll("-", " "),
      summary: event.instruction,
      searchTerms: [event.notationPitch, controlsLabel(event.tabNotes)],
      excerpt: event.coachingCue || null,
      quoteKind: event.coachingCue ? "verbatim_excerpt" : "technical_summary",
    }));
  }

  function activateLessonMoment(moment) {
    const event = state.data.events.find((item) => item.id === moment.eventId);
    if (!event) return;
    state.selectedPhraseId = event.phraseId;
    setLayer("phrase-practice", { preserveTime: true });
    seekTo(event.startMs);
    renderPhraseMap();
    renderTab();
  }

  function renderLessonSearch() {
    const input = q("[data-lesson-search]");
    const container = q("[data-lesson-search-results]");
    const count = q("[data-search-count]");
    if (!input || !container) return;
    const moments = lessonMoments();
    if (count) count.textContent = `${moments.length} indexed moments`;
    const terms = normalizeSearch(state.searchQuery).split(" ").filter(Boolean);
    const ranked = moments.map((moment) => {
      const event = state.data.events.find((item) => item.id === moment.eventId);
      const haystack = normalizeSearch([
        moment.label,
        moment.summary,
        moment.excerpt,
        ...(moment.searchTerms || []),
        event?.instruction,
        event?.movement,
      ].join(" "));
      return { moment, event, score: terms.reduce((total, term) => total + (haystack.includes(term) ? 1 : 0), 0) };
    }).filter((item) => item.event && (!terms.length || item.score === terms.length))
      .sort((left, right) => right.score - left.score || Number(left.moment.lessonTimeMs || 0) - Number(right.moment.lessonTimeMs || 0));
    container.replaceChildren();
    if (!terms.length && presentation === "embed-demo") return;
    const visible = terms.length ? ranked.slice(0, 8) : ranked.filter((item) => item.moment.featured).slice(0, 3);
    if (!visible.length) {
      container.append(node("p", "search-empty", terms.length
        ? "No indexed technical moment matches every search word. Try a string number, fret, pedal, lever, slide, or phrase name."
        : "Search by pedal, string, fret, technique, or phrase."));
      return;
    }
    visible.forEach(({ moment, event }) => {
      const button = node("button", "search-result");
      button.type = "button";
      const sourceLabel = Number.isFinite(Number(moment.lessonTimeMs))
        ? `Lesson ${formatLessonMoment(moment.lessonTimeMs)}`
        : `Bar ${event.bar}`;
      const kind = moment.quoteKind === "verbatim_excerpt" ? "Travis · exact excerpt" : "Technical index summary";
      button.append(
        node("span", "search-result-meta", `${sourceLabel} · ${kind}`),
        node("strong", "", moment.excerpt || moment.label),
        node("span", "", moment.summary),
        node("small", "", `Go to bar ${event.bar}, beat ${event.beat} →`),
      );
      button.addEventListener("click", () => activateLessonMoment(moment));
      container.append(button);
    });
  }

  function configureLessonSearch() {
    const input = q("[data-lesson-search]");
    if (!input) return;
    input.addEventListener("input", () => {
      state.searchQuery = input.value;
      renderLessonSearch();
    });
    renderLessonSearch();
  }

  function renderChordChart() {
    const container = q("[data-chord-chart]");
    if (!container) return;
    container.replaceChildren();
    const chartAvailable = hasChordChart();
    const status = q("[data-chord-status]");
    if (status) status.textContent = chartAvailable
      ? state.data.approvals.chords ? "Travis approved" : "Solo form · audio-derived · Travis review required"
      : "Chord chart not attached";
    for (let bar = 1; bar <= Number(state.data.display.barCount); bar += 1) {
      const cell = node("button", "chord-bar");
      cell.type = "button";
      cell.dataset.bar = String(bar);
      const chords = state.data.chordTimeline.filter((item) => Number(item.barStart) <= bar && Number(item.barEnd) >= bar);
      const labels = chords.filter((item, index, items) => item.symbol && (index === 0 || item.symbol !== items[index - 1].symbol));
      cell.append(node("span", "", `Bar ${bar}`));
      if (labels.length) {
        const symbols = node("strong", "chord-symbols");
        labels.forEach((chord, index) => {
          if (index) symbols.append(node("i", "", "→"));
          const group = node("span");
          group.append(node("b", "", chord.symbol), node("small", "", chord.nns || ""));
          symbols.append(group);
        });
        cell.append(symbols);
      } else {
        cell.append(node("strong", "", "Review pending"));
      }
      const first = chords[0];
      if (first) cell.addEventListener("click", () => {
        setLayer("phrase-practice");
        state.selectedMode = chartAvailable ? "chord-foundation" : state.selectedMode;
        seekTo(first.startMs);
        renderModes();
        updateFrame();
      });
      container.append(cell);
    }
  }

  function updateChordChartHighlight(chord, currentBar, active = true) {
    qa("[data-chord-chart] [data-bar]").forEach((cell) => {
      const bar = Number(cell.dataset.bar);
      cell.classList.toggle("is-current", active && bar === Number(currentBar));
    });
  }

  function pendingSongSegments(startMs, endMs) {
    const segments = [];
    const chunkMs = 12_000;
    for (let start = startMs; start < endMs; start += chunkMs) {
      const end = Math.min(endMs, start + chunkMs);
      segments.push({
        id: `pending-${start}`,
        startMs: start,
        endMs: end,
        symbol: null,
        nns: null,
        sourceKind: "pending",
      });
    }
    return segments;
  }

  function buildSongTimelineSegments() {
    const scope = mediaScopes().fullSong;
    const solo = mediaScopes().taughtSolo;
    const authored = hasFullSongChordChart()
      ? state.data.songChordTimeline.map((chord) => ({ ...chord, sourceKind: "full-song" }))
      : state.data.chordTimeline.map((chord) => ({
        ...chord,
        id: `taught-solo-${chord.id}`,
        startMs: Number(solo.startMs) + Number(chord.startMs),
        endMs: Number(solo.startMs) + Number(chord.endMs),
        sourceKind: "taught-solo",
      }));
    const segments = [];
    let cursor = 0;
    authored.sort((left, right) => Number(left.startMs) - Number(right.startMs)).forEach((chord) => {
      const start = clamp(Number(chord.startMs), cursor, Number(scope.durationMs));
      const end = clamp(Number(chord.endMs), start, Number(scope.durationMs));
      if (start > cursor) segments.push(...pendingSongSegments(cursor, start));
      if (end > start) segments.push({ ...chord, startMs: start, endMs: end });
      cursor = Math.max(cursor, end);
    });
    if (cursor < Number(scope.durationMs)) segments.push(...pendingSongSegments(cursor, Number(scope.durationMs)));
    return segments;
  }

  function renderSongTimeline() {
    const container = q("[data-song-timeline]");
    if (!container) return;
    const chartKey = q("[data-song-chart-key]");
    if (chartKey) chartKey.textContent = state.data.display.key;
    const complete = hasFullSongChordChart();
    const status = q("[data-song-chart-status]");
    if (status) status.textContent = complete
      ? state.data.approvals.chords ? "Complete chart · Travis approved" : "Complete chart · Travis review required"
      : "Lesson solo populated · full-song chart pending";
    state.songTimelineSegments = buildSongTimelineSegments();
    container.replaceChildren();
    state.songTimelineSegments.forEach((segment) => {
      const pending = segment.sourceKind === "pending";
      const duration = Number(segment.endMs) - Number(segment.startMs);
      const width = pending
        ? clamp(Math.round(duration * 0.026), 120, 320)
        : clamp(Math.round(duration * 0.052), 88, 230);
      const button = node("button", `song-segment${pending ? " is-pending" : ""}`);
      button.type = "button";
      button.dataset.songSegmentId = segment.id;
      button.style.setProperty("--song-segment-width", `${width}px`);
      const sourceLabel = segment.sourceKind === "taught-solo"
        ? `Solo · bar ${segment.barStart}`
        : segment.sectionLabel || `Song · ${formatTime(segment.startMs)}`;
      button.append(
        node("span", "", `${formatTime(segment.startMs)} · ${formatTime(segment.endMs)}`),
        node("strong", "", pending ? "Chart pending" : segment.symbol),
        node("small", "", pending ? "No guessed chord" : `${segment.nns} · ${sourceLabel}`),
      );
      button.addEventListener("click", () => {
        if (state.selectedLayer !== "play-along") setLayer("play-along");
        seekTo(segment.startMs);
      });
      container.append(button);
    });
  }

  function updateSongTimeline(absoluteTime) {
    if (!state.songTimelineSegments.length) return;
    let index = state.songTimelineSegments.findIndex((segment) => (
      absoluteTime >= Number(segment.startMs) && absoluteTime < Number(segment.endMs)
    ));
    if (index < 0) index = state.songTimelineSegments.length - 1;
    const segment = state.songTimelineSegments[index] || state.songTimelineSegments[state.songTimelineSegments.length - 1];
    const pending = segment.sourceKind === "pending";
    const currentElement = qa("[data-song-segment-id]").find((item) => item.dataset.songSegmentId === segment.id);
    qa("[data-song-segment-id]").forEach((item) => item.classList.toggle("is-current", item === currentElement));
    const time = q("[data-song-now-time]");
    const chord = q("[data-song-now-chord]");
    const nns = q("[data-song-now-nns]");
    const note = q("[data-song-now-note]");
    if (time) time.textContent = formatTime(absoluteTime);
    if (chord) chord.textContent = pending ? "Chart pending" : segment.symbol;
    if (nns) nns.textContent = pending ? "—" : segment.nns;
    if (note) note.textContent = pending
      ? "No reviewed full-song chord is attached for this region."
      : segment.sourceKind === "taught-solo"
        ? `Taught solo · bar ${segment.barStart} · review required`
        : segment.sectionLabel || "Authored full-song chord event";
    const scroll = q("[data-song-scroll]");
    if (state.selectedLayer !== "play-along" || !scroll || !currentElement) return;
    const duration = Math.max(1, Number(segment.endMs) - Number(segment.startMs));
    const progress = clamp((absoluteTime - Number(segment.startMs)) / duration, 0, 1);
    const playheadX = currentElement.offsetLeft + currentElement.offsetWidth * progress;
    const target = clamp(playheadX - scroll.clientWidth * 0.35, 0, scroll.scrollWidth - scroll.clientWidth);
    if (Math.abs(scroll.scrollLeft - target) > 2) scroll.scrollLeft = target;
  }

  function renderAlternates() {
    const container = q("[data-alternate-grid]");
    if (!container) return;
    container.replaceChildren();
    (state.data.alternatePositions || []).forEach((alternate) => {
      const sourceEvent = state.data.events.find((item) => item.id === alternate.forEventId);
      const card = node("article", "alternate-card");
      card.append(
        node("span", "", sourceEvent ? `Bar ${sourceEvent.bar} · lesson comparison` : "Lesson comparison"),
        node("h4", "", alternate.label),
        node("p", "", alternate.tradeoff),
      );
      if (sourceEvent) {
        const button = node("button", "quiet-button", "Compare on the fretboard →");
        button.type = "button";
        button.addEventListener("click", () => activateLessonMoment({ eventId: sourceEvent.id }));
        card.append(button);
      }
      container.append(card);
    });
  }

  function stepMove(direction) {
    pausePlayback();
    const phrase = currentPhrase();
    const events = phrase.eventIds.map((id) => state.data.events.find((item) => item.id === id)).filter(Boolean);
    const current = eventAt(state.timeMs);
    const index = Math.max(0, events.findIndex((item) => item.id === current.id));
    seekTo(events[clamp(index + direction, 0, events.length - 1)].startMs);
  }

  function configureStudyControls() {
    q('[data-action="previous-move"]')?.addEventListener("click", () => stepMove(-1));
    q('[data-action="next-move"]')?.addEventListener("click", () => stepMove(1));
  }

  function renderPhraseMap() {
    const container = q("[data-phrase-map]");
    if (!container) return;
    container.replaceChildren();
    state.data.phrases.forEach((phrase) => {
      const active = phrase.id === state.selectedPhraseId;
      const button = node("button", `phrase-chip${active ? " is-active" : ""}`);
      button.type = "button";
      button.dataset.phraseId = phrase.id;
      button.setAttribute("aria-pressed", active ? "true" : "false");
      button.append(
        node("span", "", `${phrase.barStart}–${phrase.barEnd} · ${phrase.shortLabel}`),
        node("small", "", formatTime(phrase.endMs - phrase.startMs)),
      );
      button.addEventListener("click", () => {
        state.selectedPhraseId = phrase.id;
        seekTo(phrase.startMs);
        if (state.selectedLayer !== "phrase-practice") setLayer("phrase-practice", { preserveTime: true });
        renderPhraseMap();
        renderTab();
        updateFrame();
      });
      container.append(button);
    });
    const status = q("[data-map-status]");
    if (status) {
      status.textContent = state.data.approvals.musical
        ? `${state.data.phrases.length} approved phrase ranges`
        : state.data.contentStatus === "transcribed_review_required"
          ? `${state.data.phrases.length} transcript-backed ranges · Travis review required`
          : `${state.data.phrases.length} deterministic layout ranges · approval pending`;
    }
  }

  function controlsLabel(notes) {
    const labels = [];
    notes.forEach((note) => (note.controls || []).forEach((control) => {
      if (!labels.includes(control)) labels.push(control);
    }));
    return labels.length ? labels.join("+") : "open controls";
  }

  function renderFretboard(current, upcoming) {
    const container = q("[data-fretboard]");
    if (!container) return;
    const board = node("div", "fretboard");
    const numbers = node("div", "fret-numbers");
    for (let fret = 0; fret <= 12; fret += 1) numbers.append(node("span", "", fret));
    board.append(numbers);
    const currentByString = new Map(current.tabNotes.map((item) => [Number(item.string), item]));
    const upcomingByString = new Map(upcoming.tabNotes.map((item) => [Number(item.string), item]));
    state.data.copedent.stringsHighToLow.forEach((stringDefinition) => {
      const row = node("div", "fret-row");
      row.append(node("span", "string-label", `${stringDefinition.string} · ${stringDefinition.openPitch.replace(/\d+$/, "")}`));
      for (let fret = 0; fret <= 12; fret += 1) {
        const currentNote = currentByString.get(stringDefinition.string);
        const upcomingNote = upcomingByString.get(stringDefinition.string);
        const currentPath = currentNote
          ? (currentNote.fretPath || [currentNote.fret, currentNote.toFret]).filter((item) => Number.isFinite(Number(item)))
          : [];
        let className = "fret-cell";
        let label = "";
        if (currentNote && Number(currentNote.fret) === fret) {
          className += " is-current";
          label = (currentNote.controls || []).join("");
        } else if (currentNote && currentPath.slice(1).some((item) => Number(item) === fret)) {
          className += " is-path";
          label = (currentNote.toControls || currentNote.controls || []).join("");
        } else if (upcomingNote && Number(upcomingNote.fret) === fret) {
          className += " is-next";
          label = (upcomingNote.controls || []).join("");
        }
        const cell = node("span", className);
        if (label) cell.append(node("span", "", label));
        row.append(cell);
      }
      board.append(row);
    });
    container.replaceChildren(board);
  }

  function tabToken(note) {
    if (note.technique === "pedal-hammer") {
      const pedal = (note.toControls || note.controls || []).join("");
      return `${note.fret}h${pedal}`;
    }
    if (note.technique === "sustain" && note.tieFromPrevious) return "—";
    const controls = (note.controls || []).join("");
    const destinationControls = (note.toControls || note.controls || []).join("");
    const fretPath = (note.fretPath || [note.fret, note.toFret]).filter((item) => Number.isFinite(Number(item)));
    const destination = fretPath.length > 1
      ? `→${fretPath.slice(1).join("→")}${destinationControls}`
      : "";
    const technique = note.technique === "hammer-on" ? "h" : note.technique === "release" ? "~" : "";
    return `${technique}${note.fret}${controls}${destination}`;
  }

  function buildTabTable(events, className) {
    const table = node("table", className);
    const body = document.createElement("tbody");
    state.data.copedent.stringsHighToLow.forEach((stringDefinition) => {
      const row = document.createElement("tr");
      const label = node("th", "", String(stringDefinition.string));
      label.scope = "row";
      row.append(label);
      events.forEach((event) => {
        const cell = document.createElement("td");
        cell.dataset.eventId = event.id;
        const note = event.tabNotes.find((item) => Number(item.string) === Number(stringDefinition.string));
        if (note) cell.textContent = tabToken(note);
        row.append(cell);
      });
      body.append(row);
    });
    table.append(body);
    const foot = document.createElement("tfoot");
    const row = document.createElement("tr");
    row.append(node("th", "", "bar"));
    events.forEach((event) => row.append(node("td", "", `${event.bar}.${event.beat}`)));
    foot.append(row);
    table.append(foot);
    return table;
  }

  function renderTab() {
    const container = q("[data-tab]");
    if (!container) return;
    const phrase = currentPhrase();
    const phraseIds = new Set(phrase.eventIds);
    const events = presentation === "embed-demo"
      ? state.data.events.filter((event) => phraseIds.has(event.id))
      : state.data.events;
    container.replaceChildren(buildTabTable(events, "tab-table"));
  }

  function updateTabHighlight(current, upcoming) {
    qa("[data-tab] td[data-event-id]").forEach((cell) => {
      cell.classList.toggle("is-current", cell.dataset.eventId === current.id);
      cell.classList.toggle("is-next", cell.dataset.eventId === upcoming.id && upcoming.id !== current.id);
    });
  }

  function updateFrame() {
    if (!state.data) return;
    const scope = currentMediaScope();
    const absoluteTime = absoluteMediaTime(scope, state.timeMs);
    const soloTime = taughtSoloTimeAt(absoluteTime);
    const taughtSoloActive = soloTime !== null;
    updateSongTimeline(absoluteTime);
    const current = eventAt(soloTime ?? 0);
    const upcoming = nextEvent(current);
    const chord = chordAt(soloTime ?? 0);
    const upcomingChord = nextChord(chord);
    const chordFocus = taughtSoloActive && hasChordChart() && (state.selectedMode === "chord-foundation" || state.selectedLayer === "play-along");
    const visualCurrent = chordFocus ? chord : current;
    const visualUpcoming = chordFocus ? upcomingChord : upcoming;
    const phrase = state.data.phrases.find((item) => item.id === current.phraseId) || currentPhrase();
    if (taughtSoloActive && state.selectedPhraseId !== phrase.id && !state.loop) {
      state.selectedPhraseId = phrase.id;
      renderPhraseMap();
      if (presentation === "embed-demo") renderTab();
    }
    const seek = q("[data-seek]");
    if (seek) seek.value = String(Math.round(state.timeMs));
    const time = q("[data-current-time]");
    if (time) time.textContent = formatTime(state.timeMs);
    const bar = q("[data-current-bar]");
    if (bar) bar.textContent = taughtSoloActive
      ? `Bar ${current.bar} · beat ${current.beat}`
      : `Full song · ${formatTime(state.timeMs)}`;
    const chordLabel = q("[data-current-chord]");
    if (chordLabel) {
      chordLabel.textContent = !taughtSoloActive
        ? `Taught solo at ${formatTime(mediaScopes().taughtSolo.startMs)}`
        : chord?.symbol
        ? `${chord.symbol}${chord.nns ? ` · ${chord.nns}` : ""}${chord.verified ? "" : " · review"}`
        : "Chord pending Travis review";
    }
    const currentInstruction = q("[data-current-instruction]");
    const sourceMoment = q("[data-source-moment]");
    const technique = q("[data-current-technique]");
    const nextInstruction = q("[data-next-instruction]");
    const chordModeBlocked = state.selectedMode === "chord-foundation" && !hasChordChart();
    if (currentInstruction) currentInstruction.textContent = !taughtSoloActive
      ? "Play the complete backing track."
      : chordModeBlocked
      ? "Chord chart not attached yet."
      : chordFocus ? chord.instruction : (current.coachingCue || current.instruction);
    if (sourceMoment) {
      const source = taughtSoloActive && !chordFocus && current.coachingCue ? current.sourceMoment : null;
      sourceMoment.hidden = false;
      sourceMoment.textContent = !taughtSoloActive
        ? "Full song backing track"
        : chordFocus
        ? "Backing-track chord analysis · Travis review required"
        : source
          ? `Travis · lesson ${formatLessonMoment(source.lessonTimeMs)} · exact excerpt`
          : "Authored technical move from the lesson · not a direct quote";
    }
    if (technique) technique.textContent = !taughtSoloActive
      ? `The taught solo begins at ${formatTime(mediaScopes().taughtSolo.startMs)} and keeps its own tab, fretboard, and loops.`
      : chordModeBlocked
      ? "This guardrail prevents the draft from showing a plausible-looking but wrong chord."
      : chordFocus
        ? `Chord grip: ${chord.gripLabel || controlsLabel(chord.tabNotes)}. The visual holds until the harmony changes.`
        : `Literal tab: ${current.instruction} · ${current.notationPitch} · ${controlsLabel(current.tabNotes)}`;
    if (nextInstruction) nextInstruction.textContent = !taughtSoloActive
      ? `Jump to the taught solo at ${formatTime(mediaScopes().taughtSolo.startMs)}.`
      : chordModeBlocked
      ? "Travis approval unlocks this mode."
      : chordFocus
        ? upcomingChord.id === chord.id ? `Hold ${chord.symbol} through the end.` : upcomingChord.instruction
        : (upcoming.coachingCue || upcoming.instruction);
    const position = q("[data-position-label]");
    if (position) {
      const first = visualCurrent.tabNotes[0];
      const pedalHammer = !chordFocus && first.technique === "pedal-hammer";
      position.textContent = pedalHammer
        ? `Open fret · A-pedal hammer · bar stays put`
        : chordFocus
          ? (chord.gripLabel || `${Number(first.fret) === 0 ? "Open fret" : `Fret ${first.fret}`} · ${controlsLabel(chord.tabNotes)}`)
          : `${Number(first.fret) === 0 ? "Open fret" : `Fret ${first.fret}`} · ${controlsLabel(current.tabNotes)}`;
    }
    const phraseTitle = q("[data-phrase-title]");
    const phraseNote = q("[data-phrase-note]");
    const phraseBars = q("[data-phrase-bars]");
    const phraseMove = q("[data-phrase-move]");
    const status = q("[data-review-status]");
    if (phraseTitle) phraseTitle.textContent = chordFocus ? `${chord.symbol} chord` : phrase.label;
    if (phraseNote) phraseNote.textContent = chordFocus
      ? (chord.practiceNote || `Hold ${chord.symbol} until the next authored chord boundary.`)
      : phrase.lessonNote;
    if (phraseBars) phraseBars.textContent = chordFocus ? `${chord.barStart}–${chord.barEnd}` : `${phrase.barStart}–${phrase.barEnd}`;
    if (phraseMove) phraseMove.textContent = chordFocus ? chord.movement.replaceAll("-", " ") : current.movement.replaceAll("-", " ");
    if (status) status.textContent = state.data.approvals.musical
      ? "Travis approved"
      : state.data.contentStatus === "transcribed_review_required"
        ? "Transcribed · Travis review required"
        : "Draft · review required";
    renderFretboard(visualCurrent, visualUpcoming);
    updateTabHighlight(current, upcoming);
    updateChordChartHighlight(chord, current.bar, taughtSoloActive);
  }

  function seekTo(milliseconds) {
    const scope = currentMediaScope();
    const duration = Number(scope.durationMs);
    state.timeMs = clamp(Number(milliseconds || 0), 0, duration);
    const audio = q("[data-audio]");
    if (audio && audio.src) audio.currentTime = audioTimeForScope(scope, state.timeMs) / 1000;
    updateFrame();
  }

  function stopAnimation() {
    if (state.frameId !== null) cancelAnimationFrame(state.frameId);
    state.frameId = null;
    state.previousFrameTime = null;
  }

  function tick(frameTime) {
    if (!state.playing) return;
    const audio = q("[data-audio]");
    const scope = currentMediaScope();
    if (audio && audio.src) {
      state.timeMs = scopeTimeFromAudio(scope, audio.currentTime * 1000);
    } else {
      if (state.previousFrameTime !== null) state.timeMs += (frameTime - state.previousFrameTime) * state.speed;
      state.previousFrameTime = frameTime;
    }
    const phrase = currentPhrase();
    const limit = state.loop ? phrase.endMs : Number(scope.durationMs);
    if (state.timeMs >= limit) {
      if (state.loop) {
        seekTo(phrase.startMs);
        if (audio && audio.src) audio.play().catch(() => pausePlayback());
      } else {
        seekTo(0);
        pausePlayback();
        return;
      }
    }
    updateFrame();
    state.frameId = requestAnimationFrame(tick);
  }

  function pausePlayback() {
    state.playing = false;
    const audio = q("[data-audio]");
    if (audio && !audio.paused) audio.pause();
    stopAnimation();
    const button = q('[data-action="play"]');
    if (button) {
      button.textContent = "▶";
      button.setAttribute("aria-label", "Play backing track");
    }
  }

  function playPlayback() {
    const scope = currentMediaScope();
    const rawSourceUrl = sourceUrlForScope(scope);
    if (rawSourceUrl) {
      const sourceKey = new URL(rawSourceUrl, window.location.origin).href;
      if (!state.sourceObjectUrls[sourceKey]) {
        selectScopeAudio(scope);
        return;
      }
    }
    if (state.timeMs >= Number(scope.durationMs)) seekTo(0);
    state.playing = true;
    const audio = q("[data-audio]");
    if (audio && audio.src) {
      audio.playbackRate = state.speed;
      audio.preservesPitch = true;
      audio.play().catch((error) => {
        const note = q("[data-transport-note]");
        if (note) note.textContent = `Playback could not start (${error.name || "media error"}).`;
        pausePlayback();
      });
    }
    const button = q('[data-action="play"]');
    if (button) {
      button.textContent = "Ⅱ";
      button.setAttribute("aria-label", "Pause backing track");
    }
    stopAnimation();
    state.frameId = requestAnimationFrame(tick);
  }

  function configureTransport() {
    const seek = q("[data-seek]");
    if (seek) {
      seek.addEventListener("input", () => seekTo(Number(seek.value)));
    }
    const audio = q("[data-audio]");
    if (audio) {
      audio.addEventListener("loadedmetadata", () => {
        audio.currentTime = audioTimeForScope(currentMediaScope(), state.timeMs) / 1000;
      });
      audio.addEventListener("timeupdate", () => {
        if (state.playing) {
          state.timeMs = scopeTimeFromAudio(currentMediaScope(), audio.currentTime * 1000);
          updateFrame();
        }
      });
      audio.addEventListener("ended", () => pausePlayback());
    }
    const play = q('[data-action="play"]');
    if (play) play.addEventListener("click", () => state.playing ? pausePlayback() : playPlayback());
    qa("[data-speed]").forEach((button) => button.addEventListener("click", () => setSpeed(button.dataset.speed)));
    const loop = q('[data-action="loop"]');
    if (loop) loop.addEventListener("click", () => {
      state.loop = !state.loop;
      loop.setAttribute("aria-pressed", state.loop ? "true" : "false");
      if (state.loop) {
        const phrase = currentPhrase();
        if (state.timeMs < phrase.startMs || state.timeMs >= phrase.endMs) seekTo(phrase.startMs);
      }
    });
    window.addEventListener("pagehide", () => {
      Object.values(state.sourceObjectUrls).forEach((objectUrl) => URL.revokeObjectURL(objectUrl));
    }, { once: true });
  }

  function configureFeedback() {
    const button = q('[data-action="feedback"]');
    if (!button) return;
    button.addEventListener("click", async () => {
      const event = eventAt(state.timeMs);
      const phrase = state.data.phrases.find((item) => item.id === event.phraseId);
      const details = [
        `Howdy companion ${state.data.revision}`,
        `Presentation: ${presentation}`,
        `Phrase: ${phrase.label}`,
        `Bar/beat: ${event.bar}.${event.beat}`,
        `Event: ${event.id}`,
        "Feedback: ",
      ].join("\n");
      const email = state.data.release.feedbackEmail;
      if (email) {
        window.location.href = `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent(`Howdy companion feedback · ${state.data.revision}`)}&body=${encodeURIComponent(details)}`;
        return;
      }
      try {
        await navigator.clipboard.writeText(details);
        button.textContent = "Feedback details copied";
      } catch (_error) {
        button.textContent = `${event.id} · bar ${event.bar}`;
      }
      window.setTimeout(() => { button.textContent = "Send feedback on this moment"; }, 2200);
    });
  }

  function renderPrintView() {
    root.replaceChildren();
    const header = node("header", "print-header");
    const title = node("div");
    title.append(node("p", "eyebrow", "Travis Toy Tutorials lesson companion"), node("h1", "", state.data.print.title), node("p", "", `${state.data.display.key} · ${state.data.display.meter} · 10-string E9`));
    header.append(title, node("div", "print-revision", `${state.data.revision}\n${String(state.data.artifactSha256).slice(0, 16)}`));
    root.append(header);
    if (!state.data.approvals.printLayout) {
      root.append(node("div", "print-warning", "DRAFT LAYOUT PROOF - NOT MUSICAL OR PRINT APPROVED"));
    }
    if (hasChordChart()) {
      const chart = node("section", "print-chord-chart");
      chart.append(node("h2", "", `Chord chart · Key ${state.data.display.key}`));
      const bars = node("div", "print-chord-bars");
      for (let bar = 1; bar <= Number(state.data.display.barCount); bar += 1) {
        const chords = state.data.chordTimeline.filter((item) => Number(item.barStart) <= bar && Number(item.barEnd) >= bar && item.symbol);
        const labels = chords.filter((item, index, items) => index === 0 || item.symbol !== items[index - 1].symbol);
        const cell = node("div", "");
        cell.append(node("span", "", `Bar ${bar}`), node("strong", "", labels.map((item) => item.symbol).join(" → ")));
        bars.append(cell);
      }
      chart.append(bars, node("p", "", state.data.approvals.chords ? "Travis approved" : "Audio-derived review chart · Travis approval required"));
      root.append(chart);
    }
    state.data.phrases.forEach((phrase) => {
      const section = node("section", "print-phrase");
      section.append(node("h2", "", `Bars ${phrase.barStart}–${phrase.barEnd} · ${phrase.label}`), node("p", "", phrase.lessonNote));
      const ids = new Set(phrase.eventIds);
      section.append(buildTabTable(state.data.events.filter((event) => ids.has(event.id)), "print-tab"));
      root.append(section);
    });
    const controls = state.data.copedent.controls.map((item) => `${item.code} = ${item.label} (strings ${item.strings.join(", ")})`).join(" · ");
    root.append(node("footer", "print-legend", `${controls}. 0hA = hold the open fret and press A without repicking; the bar does not move. ${state.data.print.footer}. Source copedent: ${state.data.copedent.label}.`));
    const browserPrint = document.querySelector('[data-action="browser-print"]');
    if (browserPrint) browserPrint.addEventListener("click", () => window.print());
    const pdfLink = document.querySelector("[data-pdf-link]");
    if (pdfLink && !state.data.media.pdfUrl) {
      pdfLink.removeAttribute("href");
      pdfLink.setAttribute("aria-disabled", "true");
      pdfLink.textContent = "PDF added after approval";
      pdfLink.classList.remove("button-primary");
      pdfLink.classList.add("button-secondary");
    }
  }

  async function initialize() {
    const response = await fetch(companionUrl.href, { credentials: "same-origin", cache: "no-store" });
    if (!response.ok) throw new Error(`Companion data returned ${response.status}.`);
    const data = await response.json();
    validateCompanion(data);
    state.data = data;
    state.selectedPhraseId = data.phrases[0].id;
    state.selectedMode = data.display.defaultMode;
    state.selectedLayer = data.display.defaultLayer;
    if (presentation === "print") {
      renderPrintView();
      return;
    }
    renderPreviewMarker();
    const searchPanel = q("[data-lesson-search-panel]");
    if (searchPanel && presentation === "embed-demo") searchPanel.open = false;
    configureTransport();
    configureFeedback();
    configureStudyControls();
    configureMediaScopeActions();
    configureLessonSearch();
    renderLessonFacts();
    renderAlternates();
    renderTab();
    const attribution = q("[data-source-attribution]");
    if (attribution) attribution.textContent = data.lesson.sourceAttribution;
    setLayer(data.display.defaultLayer, { preserveTime: true });
  }

  initialize().catch((error) => {
    const panel = q("[data-error]") || root;
    panel.hidden = false;
    panel.textContent = `Companion unavailable: ${error.message}`;
  });
})();
