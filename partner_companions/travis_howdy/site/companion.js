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
    selectedPhraseId: null,
    selectedMode: null,
    selectedLayer: null,
    searchQuery: "",
    frameId: null,
    previousFrameTime: null,
    sourceObjectUrls: {},
    sourceLoadPromises: {},
    songTimelineSegments: [],
    songDisplayMode: "chords",
    selectedGuideEventId: null,
    lastTabFocusId: null,
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
  const formatBpm = (value) => {
    const bpm = Number(value);
    return Number.isFinite(bpm) && bpm > 0 ? String(Math.round(bpm)) : "—";
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
  const guideEvent = () => state.data.events.find((item) => item.id === state.selectedGuideEventId) || state.data.events[0];
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
    if (Array.isArray(data.songForm) && data.songForm.length) {
      let previousSectionEnd = 0;
      data.songForm.forEach((section) => {
        if (
          Number(section.startMs) !== previousSectionEnd
          || Number(section.endMs) <= Number(section.startMs)
          || !String(section.id || "").trim()
          || !String(section.label || "").trim()
        ) throw new Error("The full-song section map must be contiguous and labeled.");
        previousSectionEnd = Number(section.endMs);
      });
      if (previousSectionEnd !== Number(scopes.fullSong.durationMs)) {
        throw new Error("The full-song section map must cover the complete song scope.");
      }
    }
    if (!Array.isArray(data.relatedLessons) || data.relatedLessons.length > 6) {
      throw new Error("The related video cards are incomplete.");
    }
    const relatedCoverage = new Map(data.phrases.map((phrase) => [phrase.id, 0]));
    const featuredLessons = data.relatedLessons.filter((lesson) => lesson.featuredForCompanion);
    if (data.relatedLessons.length && (featuredLessons.length < 1 || featuredLessons.length > 6)) {
      throw new Error("The companion needs one to six static related-video recommendations.");
    }
    data.relatedLessons.forEach((lesson) => {
      if (!/^https:\/\/travis-toy-tutorials\.teachable\.com\/courses\/[^\s]+\/lectures\/\d+$/.test(lesson.url)) {
        throw new Error(`Invalid related lesson URL for ${lesson.id}.`);
      }
      if (lesson.thumbnailUrl && new URL(lesson.thumbnailUrl, window.location.origin).origin !== window.location.origin) {
        throw new Error(`Related lesson thumbnail must be same-origin for ${lesson.id}.`);
      }
      if (!Array.isArray(lesson.matches) || !lesson.matches.length) {
        throw new Error(`Related lesson ${lesson.id} has no phrase match.`);
      }
      if (lesson.featuredForCompanion && !String(lesson.companionReason || "").trim()) {
        throw new Error(`Featured related lesson ${lesson.id} has no lesson-level reason.`);
      }
      lesson.matches.forEach((match) => {
        if (
          !relatedCoverage.has(match.phraseId)
          || !String(match.reason || "").trim()
          || !String(match.conceptId || "").trim()
          || !String(match.relation || "").trim()
          || !Array.isArray(match.sourceEventIds)
          || !match.sourceEventIds.length
          || match.sourceEventIds.some((eventId) => !data.phrases
            .find((phrase) => phrase.id === match.phraseId)?.eventIds.includes(eventId))
        ) {
          throw new Error(`Related lesson ${lesson.id} has an invalid phrase match.`);
        }
        relatedCoverage.set(match.phraseId, relatedCoverage.get(match.phraseId) + 1);
      });
    });
    if (data.relatedLessons.length && [...relatedCoverage.values()].some((count) => count < 1 || count > 2)) {
      throw new Error("Each phrase must have one or two specific related-video matches.");
    }
  }

  function renderPreviewMarker() {
    const marker = q("[data-preview-marker]");
    if (!marker) return;
    const sha = String(state.data.buildSha || "local").slice(0, 12);
    marker.textContent = presentation === "embed-demo"
      ? `Preview · ${state.data.revision} · ${sha}`
      : `${state.data.release.previewLabel} · ${state.data.revision} · ${sha}`;
    const title = q("[data-companion-title]");
    if (title) title.textContent = "Practice “Howdy”";
  }

  function renderLayerTabs() {
    const container = q("[data-layer-tabs]");
    if (!container) return;
    container.replaceChildren();
    state.data.layers.filter((layer) => ["phrase-practice", "play-along"].includes(layer.id)).forEach((layer) => {
      const button = node("button", `layer-tab${layer.id === state.selectedLayer ? " is-active" : ""}`);
      button.type = "button";
      button.dataset.layerId = layer.id;
      button.setAttribute("aria-pressed", layer.id === state.selectedLayer ? "true" : "false");
      const labels = {
        "phrase-practice": `Taught solo · ${formatTime(mediaScopes().taughtSolo.durationMs)}`,
        "play-along": `Full song · ${formatTime(mediaScopes().fullSong.durationMs)}`,
      };
      button.append(
        node("strong", "", labels[layer.id]),
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
    if (studyControls) studyControls.hidden = !["phrase-practice", "play-along"].includes(layer.id);
    if (explorePanel) explorePanel.hidden = layer.id !== "explore";
    if (layer.id === "phrase-practice") {
      state.selectedMode = "follow-solo";
      setSpeed(1);
      if (!options.preserveTime) seekTo(currentPhrase().startMs);
    } else if (layer.id === "play-along") {
      state.selectedMode = hasChordChart() ? "chord-foundation" : "follow-solo";
      setSpeed(1);
      if (!options.preserveTime) seekTo(0);
    }
    const layerCopy = {
      "phrase-practice": ["Taught solo", "Start from any phrase", "Choose a phrase, slow it down, and let the solo continue naturally.", "100% · continuous playback"],
      "play-along": ["Full song", "Follow the song form", "The current chord updates above while the chart stays still. Use the manual Travis guide below for the taught solo.", `${formatTime(mediaScopes().fullSong.durationMs)} · ${formatBpm(state.data.display.fullSongTempoBpm)} BPM`],
    }[layer.id] || ["", "", "", ""];
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
    renderLessonFacts();
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
    const songTempo = q("[data-song-tempo-label]");
    if (key) key.textContent = `Key ${state.data.display.key}`;
    if (meter) meter.textContent = state.data.display.meter;
    const fullSongActive = state.selectedLayer === "play-along";
    const tempoValue = fullSongActive
      ? state.data.display.fullSongTempoBpm
      : state.data.display.tempoBpm;
    const tempoScope = fullSongActive ? "Full song" : "Taught solo";
    if (tempo) tempo.textContent = tempoValue ? `${tempoScope} · ${formatBpm(tempoValue)} BPM` : `${tempoScope} tempo pending`;
    if (chartKey) chartKey.textContent = state.data.display.key;
    if (songTempo) songTempo.textContent = state.data.display.fullSongTempoBpm ? `${formatBpm(state.data.display.fullSongTempoBpm)} BPM` : "tempo pending";
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
            if (note) note.textContent = "";
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
      ? `Complete backing track; the taught solo begins at ${formatTime(scopes.taughtSolo.startMs)}.`
      : "The eight-bar solo from the lesson.";
    if (jump) jump.hidden = !isFullSong;
    const seek = q("[data-seek]");
    const duration = q("[data-duration]");
    if (seek) {
      seek.max = String(scope.durationMs);
      seek.value = String(Math.round(state.timeMs));
    }
    if (duration) duration.textContent = formatTime(scope.durationMs);
    const note = q("[data-transport-note]");
    if (note) note.textContent = "";
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
      ? state.data.approvals.chords ? "Travis approved" : "Draft chart"
      : "Chart unavailable";
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
        timelineKind: "pending",
      });
    }
    return segments;
  }

  function buildSongTimelineSegments() {
    const scope = mediaScopes().fullSong;
    const solo = mediaScopes().taughtSolo;
    const authored = hasFullSongChordChart()
      ? state.data.songChordTimeline.map((chord) => ({ ...chord, timelineKind: "full-song" }))
      : state.data.chordTimeline.map((chord) => ({
        ...chord,
        id: `taught-solo-${chord.id}`,
        startMs: Number(solo.startMs) + Number(chord.startMs),
        endMs: Number(solo.startMs) + Number(chord.endMs),
        timelineKind: "taught-solo",
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

  function renderSongSections() {
    const container = q("[data-song-sections]");
    if (!container) return;
    container.replaceChildren();
    const sections = Array.isArray(state.data.songForm) ? state.data.songForm : [];
    container.hidden = !sections.length;
    sections.forEach((section) => {
      const button = node("button", "song-section");
      button.type = "button";
      button.dataset.songSectionId = section.id;
      button.append(
        node("strong", "", section.label),
        node("span", "", `${formatTime(section.startMs)}–${formatTime(section.endMs)}`),
      );
      button.addEventListener("click", () => seekTo(section.startMs));
      container.append(button);
    });
  }

  function updateSongDisplayToggle() {
    qa("[data-song-display]").forEach((button) => {
      const active = button.dataset.songDisplay === state.songDisplayMode;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  function configureSongDisplayToggle() {
    qa("[data-song-display]").forEach((button) => {
      button.addEventListener("click", () => {
        const mode = button.dataset.songDisplay;
        if (!['chords', 'nns'].includes(mode) || mode === state.songDisplayMode) return;
        state.songDisplayMode = mode;
        updateSongDisplayToggle();
        renderSongTimeline();
        updateFrame();
      });
    });
    updateSongDisplayToggle();
  }

  function renderSongTimeline() {
    const container = q("[data-song-timeline]");
    if (!container) return;
    const chartKey = q("[data-song-chart-key]");
    if (chartKey) chartKey.textContent = state.data.display.key;
    const complete = hasFullSongChordChart();
    const status = q("[data-song-chart-status]");
    const sectionCount = Array.isArray(state.data.songForm) ? state.data.songForm.length : 0;
    if (status) status.textContent = complete
      ? state.data.approvals.chords ? "Travis approved" : `${sectionCount || "Draft"} sections`
      : "Full-song chart unavailable";
    const guardrail = q("[data-song-chart-guardrail]");
    if (guardrail) guardrail.textContent = complete
      ? "The current chord updates above. This chart stays still during playback; scroll it only when you want."
      : "Only source-timed chords are shown.";
    renderSongSections();
    state.songTimelineSegments = buildSongTimelineSegments();
    container.replaceChildren();
    state.songTimelineSegments.forEach((segment) => {
      const pending = segment.timelineKind === "pending";
      const duration = Number(segment.endMs) - Number(segment.startMs);
      const width = pending
        ? clamp(Math.round(duration * 0.026), 120, 320)
        : clamp(Math.round(duration * 0.052), 88, 230);
      const button = node("button", `song-segment${pending ? " is-pending" : ""}${segment.needsAttention ? " needs-attention" : ""}`);
      button.type = "button";
      button.dataset.songSegmentId = segment.id;
      button.style.setProperty("--song-segment-width", `${width}px`);
      const taughtSoloSource = segment.timelineKind === "taught-solo"
        || segment.sourceKind === "taught_solo_chord_timeline";
      const sourceLabel = segment.sectionLabel || (taughtSoloSource ? "Taught solo" : "Song form");
      const primaryLabel = state.songDisplayMode === "nns" ? segment.nns : segment.symbol;
      const secondaryLabel = state.songDisplayMode === "nns" ? segment.symbol : segment.nns;
      button.append(
        node("span", "", `${formatTime(segment.startMs)} · ${formatTime(segment.endMs)}`),
        node("strong", "", pending ? "—" : primaryLabel),
        node("small", "", pending ? "Uncharted" : `${secondaryLabel} · ${sourceLabel}`),
      );
      if (segment.needsAttention) button.title = "Draft chord timing";
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
    const pending = segment.timelineKind === "pending";
    const currentElement = qa("[data-song-segment-id]").find((item) => item.dataset.songSegmentId === segment.id);
    qa("[data-song-segment-id]").forEach((item) => item.classList.toggle("is-current", item === currentElement));
    qa("[data-song-section-id]").forEach((item) => item.classList.toggle("is-current", item.dataset.songSectionId === segment.sectionId));
    const time = q("[data-song-now-time]");
    const chord = q("[data-song-now-chord]");
    const nns = q("[data-song-now-nns]");
    const note = q("[data-song-now-note]");
    if (time) time.textContent = formatTime(absoluteTime);
    if (chord) chord.textContent = pending
      ? "—"
      : state.songDisplayMode === "nns" ? segment.nns : segment.symbol;
    if (nns) nns.textContent = pending
      ? "—"
      : state.songDisplayMode === "nns" ? segment.symbol : segment.nns;
    if (note) note.textContent = pending
      ? "Uncharted"
      : segment.timelineKind === "taught-solo" || segment.sourceKind === "taught_solo_chord_timeline"
        ? `${segment.sectionLabel || "Steel break"} · taught bar ${segment.soloBarStart || "—"}`
        : `${segment.sectionLabel || "Song form"}`;
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

  function renderRelatedLessons() {
    const container = q("[data-related-lessons]");
    if (!container) return;
    container.replaceChildren();
    const section = container.closest(".related-videos");
    const suggestions = state.data.relatedLessons.filter((lesson) => lesson.featuredForCompanion);
    if (section) section.hidden = !suggestions.length;
    const heading = q("[data-related-heading]");
    if (heading) heading.textContent = "Related Travis videos";
    container.classList.toggle("is-single", suggestions.length === 1);
    suggestions.forEach((lesson) => {
      const link = node("a", "related-video-card");
      link.href = lesson.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.setAttribute("aria-label", `Open video: ${lesson.title}, starting at ${formatLessonMoment(lesson.startMs)}`);
      const visual = node("span", "related-video-visual");
      if (lesson.thumbnailUrl) {
        const image = node("img");
        image.src = lesson.thumbnailUrl;
        image.alt = `Video thumbnail for ${lesson.title}`;
        image.loading = "lazy";
        visual.append(image);
      }
      visual.append(
        node("span", "related-play", "▶"),
        node("span", "related-time", `Start at ${formatLessonMoment(lesson.startMs)}`),
      );
      const copy = node("span", "related-video-copy");
      copy.append(
        node("span", "related-label", lesson.label),
        node("strong", "", lesson.title),
        node("span", "related-why", "Why this lesson"),
        node("span", "related-reason", lesson.companionReason),
        node("span", "related-open", "Open video ↗"),
      );
      link.append(visual, copy);
      container.append(link);
    });
  }

  function configureRelatedScroller() {
    const scroller = q("[data-related-lessons]");
    if (!scroller) return;
    qa("[data-related-scroll]").forEach((button) => {
      button.addEventListener("click", () => {
        const card = scroller.querySelector(".related-video-card");
        const distance = card ? card.getBoundingClientRect().width + 12 : scroller.clientWidth * 0.8;
        scroller.scrollBy({
          left: Number(button.dataset.relatedScroll) * distance,
          behavior: "smooth",
        });
      });
    });
  }

  function stepMove(direction) {
    const manualGuide = state.selectedLayer === "play-along";
    if (!manualGuide) pausePlayback();
    const phrase = currentPhrase();
    const events = manualGuide
      ? state.data.events
      : phrase.eventIds.map((id) => state.data.events.find((item) => item.id === id)).filter(Boolean);
    const current = manualGuide ? guideEvent() : eventAt(state.timeMs);
    const index = Math.max(0, events.findIndex((item) => item.id === current.id));
    const selected = events[clamp(index + direction, 0, events.length - 1)];
    state.selectedGuideEventId = selected.id;
    if (manualGuide) {
      state.lastTabFocusId = null;
      updateFrame();
      return;
    }
    seekTo(selected.startMs);
  }

  function configureStudyControls() {
    q('[data-action="previous-move"]')?.addEventListener("click", () => stepMove(-1));
    q('[data-action="next-move"]')?.addEventListener("click", () => stepMove(1));
  }

  function selectTabEvent(eventId) {
    const selected = state.data.events.find((item) => item.id === eventId);
    if (!selected) return;
    state.selectedGuideEventId = selected.id;
    state.lastTabFocusId = null;
    if (state.selectedLayer === "play-along") {
      updateFrame();
      return;
    }
    pausePlayback();
    seekTo(selected.startMs);
  }

  function bindTabControl(control, event) {
    control.addEventListener("click", () => selectTabEvent(event.id));
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
        ? `${state.data.phrases.length} phrases`
        : `${state.data.phrases.length} phrases`;
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
    if (note.technique === "bar-hammer") {
      const destination = note.toFret ?? (note.fretPath || [])[1];
      return `${note.fret}h${destination}`;
    }
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
    table.style.width = `${Math.max(720, 43 + events.length * 72)}px`;
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
        if (presentation === "print") {
          if (note) cell.textContent = tabToken(note);
        } else {
          const control = node("button", "tab-cell-button", note ? tabToken(note) : "");
          control.type = "button";
          control.tabIndex = -1;
          control.setAttribute("aria-label", `Select bar ${event.bar}, beat ${event.beat}: ${event.instruction}`);
          bindTabControl(control, event);
          cell.append(control);
        }
        row.append(cell);
      });
      body.append(row);
    });
    table.append(body);
    const foot = document.createElement("tfoot");
    const row = document.createElement("tr");
    row.append(node("th", "", "bar"));
    events.forEach((event) => {
      const cell = node("td");
      cell.dataset.eventId = event.id;
      if (presentation === "print") {
        cell.textContent = `${event.bar}.${event.beat}`;
      } else {
        const control = node("button", "tab-cell-button tab-beat-button", `${event.bar}.${event.beat}`);
        control.type = "button";
        control.setAttribute("aria-label", `Select bar ${event.bar}, beat ${event.beat}: ${event.instruction}`);
        bindTabControl(control, event);
        cell.append(control);
      }
      row.append(cell);
    });
    foot.append(row);
    table.append(foot);
    return table;
  }

  function renderTab() {
    const container = q("[data-tab]");
    if (!container) return;
    const phrase = currentPhrase();
    const phraseIds = new Set(phrase.eventIds);
    if (presentation === "embed-demo") {
      const events = state.data.events;
      container.replaceChildren(buildTabTable(events, "tab-table"));
      state.lastTabFocusId = null;
      return;
    }
    const systems = state.data.phrases.map((systemPhrase) => {
      const system = node("section", "tab-system");
      system.append(node("h4", "", `Bars ${systemPhrase.barStart}–${systemPhrase.barEnd} · ${systemPhrase.label}`));
      const scroll = node("div", "tab-system-scroll");
      const eventIds = new Set(systemPhrase.eventIds);
      scroll.append(buildTabTable(state.data.events.filter((event) => eventIds.has(event.id)), "tab-table"));
      system.append(scroll);
      return system;
    });
    container.replaceChildren(...systems);
  }

  function updateTabHighlight(current, upcoming) {
    qa("[data-tab] td[data-event-id]").forEach((cell) => {
      cell.classList.toggle("is-current", cell.dataset.eventId === current.id);
      cell.classList.toggle("is-next", cell.dataset.eventId === upcoming.id && upcoming.id !== current.id);
    });
  }

  function scrollTabToEvent(eventId, behavior = "smooth") {
    if (state.lastTabFocusId === eventId) return;
    const cell = q(`[data-tab] td[data-event-id="${eventId}"]`);
    if (!cell) return;
    const scroller = cell.closest(".tab-system-scroll") || q("[data-tab]");
    if (!scroller || scroller.scrollWidth <= scroller.clientWidth) {
      state.lastTabFocusId = eventId;
      return;
    }
    const target = cell.offsetLeft - (scroller.clientWidth - cell.offsetWidth) / 2;
    scroller.scrollTo({ left: Math.max(0, target), behavior });
    state.lastTabFocusId = eventId;
  }

  function updateFrame() {
    if (!state.data) return;
    const scope = currentMediaScope();
    const absoluteTime = absoluteMediaTime(scope, state.timeMs);
    const soloTime = taughtSoloTimeAt(absoluteTime);
    const taughtSoloActive = soloTime !== null;
    const manualGuide = state.selectedLayer === "play-along";
    updateSongTimeline(absoluteTime);
    const playbackEvent = eventAt(soloTime ?? 0);
    if (!manualGuide) state.selectedGuideEventId = playbackEvent.id;
    const current = manualGuide ? guideEvent() : playbackEvent;
    const upcoming = nextEvent(current);
    const guideTime = manualGuide ? Number(current.startMs) : (soloTime ?? 0);
    const guideActive = manualGuide || taughtSoloActive;
    const chord = chordAt(guideTime);
    const upcomingChord = nextChord(chord);
    const chordFocus = guideActive && !manualGuide && hasChordChart() && state.selectedMode === "chord-foundation";
    const visualCurrent = chordFocus ? chord : current;
    const visualUpcoming = chordFocus ? upcomingChord : upcoming;
    const phrase = state.data.phrases.find((item) => item.id === current.phraseId) || currentPhrase();
    if (guideActive && state.selectedPhraseId !== phrase.id) {
      state.selectedPhraseId = phrase.id;
      renderPhraseMap();
      if (presentation === "embed-demo") renderTab();
    }
    const seek = q("[data-seek]");
    if (seek) seek.value = String(Math.round(state.timeMs));
    const time = q("[data-current-time]");
    if (time) time.textContent = formatTime(state.timeMs);
    const bar = q("[data-current-bar]");
    if (bar) bar.textContent = guideActive
      ? `${manualGuide ? "Taught solo · " : ""}Bar ${current.bar} · beat ${current.beat}`
      : `Full song · ${formatTime(state.timeMs)}`;
    const chordLabel = q("[data-current-chord]");
    if (chordLabel) {
      chordLabel.textContent = !guideActive
        ? `Solo begins at ${formatTime(mediaScopes().taughtSolo.startMs)}`
        : chord?.symbol
        ? `${chord.symbol}${chord.nns ? ` · ${chord.nns}` : ""}`
        : "—";
    }
    const currentInstruction = q("[data-current-instruction]");
    const sourceMoment = q("[data-source-moment]");
    const technique = q("[data-current-technique]");
    const nextInstruction = q("[data-next-instruction]");
    const chordModeBlocked = state.selectedMode === "chord-foundation" && !hasChordChart();
    if (currentInstruction) currentInstruction.textContent = !guideActive
      ? "Play the complete backing track."
      : chordModeBlocked
      ? "Chord chart not attached yet."
      : chordFocus ? chord.instruction : current.instruction;
    if (sourceMoment) {
      const source = guideActive && !chordFocus && current.coachingCue ? current.sourceMoment : null;
      sourceMoment.hidden = !source;
      sourceMoment.textContent = !guideActive
        ? ""
        : chordFocus
        ? ""
        : source
          ? `Travis at ${formatLessonMoment(source.lessonTimeMs)}: “${current.coachingCue}”`
          : "";
    }
    if (technique) technique.textContent = !guideActive
      ? ""
      : chordModeBlocked
      ? ""
      : chordFocus
        ? `${chord.gripLabel || controlsLabel(chord.tabNotes)}`
        : `${current.notationPitch} · ${controlsLabel(current.tabNotes)}`;
    if (nextInstruction) nextInstruction.textContent = !guideActive
      ? `Solo at ${formatTime(mediaScopes().taughtSolo.startMs)}`
      : chordModeBlocked
      ? "—"
      : chordFocus
        ? upcomingChord.id === chord.id ? `Hold ${chord.symbol} through the end.` : upcomingChord.instruction
        : upcoming.instruction;
    const position = q("[data-position-label]");
    if (position) {
      const first = visualCurrent.tabNotes[0];
      const pedalHammer = !chordFocus && first.technique === "pedal-hammer";
      const barHammer = !chordFocus && first.technique === "bar-hammer";
      position.textContent = barHammer
        ? `Open fret → fret ${first.toFret ?? first.fretPath?.[1]} · bar hammer`
        : pedalHammer
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
      : "Preview transcription";
    const studyTitle = q("[data-study-title]");
    const studyProgress = q("[data-study-progress]");
    const studyEvents = manualGuide
      ? state.data.events
      : currentPhrase().eventIds.map((id) => state.data.events.find((item) => item.id === id)).filter(Boolean);
    const studyIndex = Math.max(0, studyEvents.findIndex((item) => item.id === current.id));
    if (studyTitle) studyTitle.textContent = manualGuide ? "Taught solo guide" : "Step through the tab";
    if (studyProgress) studyProgress.textContent = manualGuide
      ? `Move ${studyIndex + 1} of ${studyEvents.length} · manual — song playback will not move this guide`
      : `Move ${studyIndex + 1} of ${studyEvents.length}`;
    const previousMove = q('[data-action="previous-move"]');
    const nextMove = q('[data-action="next-move"]');
    if (previousMove) previousMove.disabled = studyIndex === 0;
    if (nextMove) nextMove.disabled = studyIndex === studyEvents.length - 1;
    renderFretboard(visualCurrent, visualUpcoming);
    updateTabHighlight(current, upcoming);
    scrollTabToEvent(current.id, manualGuide ? "smooth" : "auto");
    updateChordChartHighlight(chord, current.bar, guideActive);
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
    if (state.timeMs >= Number(scope.durationMs)) {
      seekTo(0);
      pausePlayback();
      return;
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
    window.addEventListener("pagehide", () => {
      Object.values(state.sourceObjectUrls).forEach((objectUrl) => URL.revokeObjectURL(objectUrl));
    }, { once: true });
  }

  function configureFeedback() {
    const button = q('[data-action="feedback"]');
    if (!button) return;
    button.addEventListener("click", async () => {
      const event = state.selectedLayer === "play-along" ? guideEvent() : eventAt(state.timeMs);
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
    const hasBarHammer = state.data.events.some((event) => event.tabNotes.some((note) => note.technique === "bar-hammer"));
    const hammerLegend = hasBarHammer
      ? "0h1 = hammer the bar from open to fret 1 without repicking."
      : "0hA = hold the open fret and press A without repicking; the bar does not move.";
    root.append(node("footer", "print-legend", `${controls}. ${hammerLegend} ${state.data.print.footer}. Source copedent: ${state.data.copedent.label}.`));
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
    state.selectedGuideEventId = data.events[0].id;
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
    configureSongDisplayToggle();
    configureLessonSearch();
    renderLessonFacts();
    renderAlternates();
    renderTab();
    const positionDetails = q(".position-details");
    if (positionDetails && presentation === "full") positionDetails.open = true;
    const attribution = q("[data-source-attribution]");
    if (attribution) attribution.textContent = data.lesson.sourceAttribution;
    setLayer("phrase-practice", { preserveTime: true });
    renderRelatedLessons();
    configureRelatedScroller();
  }

  initialize().catch((error) => {
    const panel = q("[data-error]") || root;
    panel.hidden = false;
    panel.textContent = `Companion unavailable: ${error.message}`;
  });
})();
