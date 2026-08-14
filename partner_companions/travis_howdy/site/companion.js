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
    frameId: null,
    previousFrameTime: null,
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
  const currentPhrase = () => state.data.phrases.find((item) => item.id === state.selectedPhraseId) || state.data.phrases[0];
  const eventAt = (milliseconds) => {
    const events = state.data.events;
    return events.find((item) => milliseconds >= item.startMs && milliseconds < item.endMs) || events[events.length - 1];
  };
  const chordFor = (event) => state.data.chordTimeline.find((item) => item.id === event.chordEventId);
  const eventIndex = (event) => state.data.events.findIndex((item) => item.id === event.id);
  const nextEvent = (event) => state.data.events[Math.min(state.data.events.length - 1, eventIndex(event) + 1)];

  function validateCompanion(data) {
    if (!data || data.schemaVersion !== "lesson_companion_v1") throw new Error("Unsupported companion artifact.");
    if (data.runtimeMode !== "published_deterministic" || data.modelCallsAllowed !== false) {
      throw new Error("This preview accepts only a deterministic published artifact.");
    }
    if (!Array.isArray(data.events) || !data.events.length || !Array.isArray(data.phrases)) {
      throw new Error("The companion artifact is incomplete.");
    }
    const eventIds = new Set(data.events.map((item) => item.id));
    if (eventIds.size !== data.events.length) throw new Error("Companion event IDs must be unique.");
    data.phrases.forEach((phrase) => phrase.eventIds.forEach((id) => {
      if (!eventIds.has(id)) throw new Error(`Phrase references missing event ${id}.`);
    }));
  }

  function renderPreviewMarker() {
    const marker = q("[data-preview-marker]");
    if (!marker) return;
    const sha = String(state.data.buildSha || "local").slice(0, 12);
    marker.textContent = `${state.data.release.previewLabel} · ${state.data.revision} · ${sha}`;
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
      button.append(node("strong", "", layer.label), node("span", "", layer.description));
      button.addEventListener("click", () => {
        state.selectedLayer = layer.id;
        renderLayerTabs();
        const note = q("[data-transport-note]");
        if (note) note.textContent = layer.description;
      });
      container.append(button);
    });
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
        state.selectedMode = mode.id;
        renderModes();
        updateFrame();
      });
      container.append(button);
    });
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
        let className = "fret-cell";
        let label = "";
        if (currentNote && Number(currentNote.fret) === fret) {
          className += " is-current";
          label = (currentNote.controls || []).join("");
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
    const controls = (note.controls || []).join("");
    const technique = note.technique === "slide-in" ? "↗" : note.technique === "release" ? "~" : "";
    return `${technique}${note.fret}${controls}`;
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
    const current = eventAt(state.timeMs);
    const upcoming = nextEvent(current);
    const phrase = state.data.phrases.find((item) => item.id === current.phraseId) || currentPhrase();
    const chord = chordFor(current);
    if (state.selectedPhraseId !== phrase.id && !state.loop) {
      state.selectedPhraseId = phrase.id;
      renderPhraseMap();
      if (presentation === "embed-demo") renderTab();
    }
    const seek = q("[data-seek]");
    if (seek) seek.value = String(Math.round(state.timeMs));
    const time = q("[data-current-time]");
    if (time) time.textContent = formatTime(state.timeMs);
    const bar = q("[data-current-bar]");
    if (bar) bar.textContent = `Bar ${current.bar} · beat ${current.beat}`;
    const chordLabel = q("[data-current-chord]");
    if (chordLabel) {
      chordLabel.textContent = chord && chord.verified && chord.symbol
        ? `${chord.symbol}${chord.nns ? ` · ${chord.nns}` : ""}`
        : "Chord pending Travis review";
    }
    const currentInstruction = q("[data-current-instruction]");
    const technique = q("[data-current-technique]");
    const nextInstruction = q("[data-next-instruction]");
    const chordModeBlocked = state.selectedMode === "chord-foundation" && !state.data.approvals.chords;
    if (currentInstruction) currentInstruction.textContent = chordModeBlocked ? "Reviewed chord chart not attached yet." : current.instruction;
    if (technique) technique.textContent = chordModeBlocked
      ? "This guardrail prevents the draft from showing a plausible-looking but wrong chord."
      : `${current.notationPitch} · ${controlsLabel(current.tabNotes)} · ${current.movement.replaceAll("-", " ")}`;
    if (nextInstruction) nextInstruction.textContent = chordModeBlocked ? "Travis approval unlocks this mode." : upcoming.instruction;
    const position = q("[data-position-label]");
    if (position) position.textContent = `Fret ${current.tabNotes[0].fret} · ${controlsLabel(current.tabNotes)}`;
    const phraseTitle = q("[data-phrase-title]");
    const phraseNote = q("[data-phrase-note]");
    const phraseBars = q("[data-phrase-bars]");
    const phraseMove = q("[data-phrase-move]");
    const status = q("[data-review-status]");
    if (phraseTitle) phraseTitle.textContent = phrase.label;
    if (phraseNote) phraseNote.textContent = phrase.lessonNote;
    if (phraseBars) phraseBars.textContent = `${phrase.barStart}–${phrase.barEnd}`;
    if (phraseMove) phraseMove.textContent = current.movement.replaceAll("-", " ");
    if (status) status.textContent = state.data.approvals.musical ? "Travis approved" : "Draft · review required";
    renderFretboard(current, upcoming);
    updateTabHighlight(current, upcoming);
  }

  function seekTo(milliseconds) {
    const duration = Number(state.data.media.durationMs);
    state.timeMs = clamp(Number(milliseconds || 0), 0, duration);
    const audio = q("[data-audio]");
    if (audio && audio.src) audio.currentTime = state.timeMs / 1000;
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
    if (audio && audio.src) {
      state.timeMs = audio.currentTime * 1000;
    } else {
      if (state.previousFrameTime !== null) state.timeMs += (frameTime - state.previousFrameTime) * state.speed;
      state.previousFrameTime = frameTime;
    }
    const phrase = currentPhrase();
    const limit = state.loop ? phrase.endMs : state.data.media.durationMs;
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
    state.playing = true;
    const audio = q("[data-audio]");
    if (audio && audio.src) {
      audio.playbackRate = state.speed;
      audio.preservesPitch = true;
      audio.play().catch(() => pausePlayback());
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
    const duration = q("[data-duration]");
    const note = q("[data-transport-note]");
    if (seek) {
      seek.max = String(state.data.media.durationMs);
      seek.addEventListener("input", () => seekTo(Number(seek.value)));
    }
    if (duration) duration.textContent = formatTime(state.data.media.durationMs);
    if (note) {
      note.textContent = state.data.media.audioUrl
        ? "Same-origin reviewed backing track loaded."
        : "Draft clock only · reviewed audio is added by the private release packager.";
    }
    const audio = q("[data-audio]");
    if (audio && state.data.media.audioUrl) {
      const mediaUrl = new URL(state.data.media.audioUrl, window.location.origin);
      if (mediaUrl.origin !== window.location.origin) throw new Error("Backing audio must be same-origin.");
      audio.src = mediaUrl.href;
      audio.addEventListener("timeupdate", () => {
        if (state.playing) {
          state.timeMs = audio.currentTime * 1000;
          updateFrame();
        }
      });
      audio.addEventListener("ended", () => pausePlayback());
    }
    const play = q('[data-action="play"]');
    if (play) play.addEventListener("click", () => state.playing ? pausePlayback() : playPlayback());
    qa("[data-speed]").forEach((button) => button.addEventListener("click", () => {
      state.speed = Number(button.dataset.speed);
      qa("[data-speed]").forEach((item) => item.classList.toggle("is-active", item === button));
      if (audio && audio.src) audio.playbackRate = state.speed;
    }));
    const loop = q('[data-action="loop"]');
    if (loop) loop.addEventListener("click", () => {
      state.loop = !state.loop;
      loop.setAttribute("aria-pressed", state.loop ? "true" : "false");
      if (state.loop) {
        const phrase = currentPhrase();
        if (state.timeMs < phrase.startMs || state.timeMs >= phrase.endMs) seekTo(phrase.startMs);
      }
    });
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
    state.data.phrases.forEach((phrase) => {
      const section = node("section", "print-phrase");
      section.append(node("h2", "", `Bars ${phrase.barStart}–${phrase.barEnd} · ${phrase.label}`), node("p", "", phrase.lessonNote));
      const ids = new Set(phrase.eventIds);
      section.append(buildTabTable(state.data.events.filter((event) => ids.has(event.id)), "print-tab"));
      root.append(section);
    });
    const controls = state.data.copedent.controls.map((item) => `${item.code} = ${item.label} (strings ${item.strings.join(", ")})`).join(" · ");
    root.append(node("footer", "print-legend", `${controls}. ${state.data.print.footer}. Source copedent: ${state.data.copedent.label}.`));
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
    renderLayerTabs();
    renderModes();
    renderPhraseMap();
    renderTab();
    configureTransport();
    configureFeedback();
    const attribution = q("[data-source-attribution]");
    if (attribution) attribution.textContent = data.lesson.sourceAttribution;
    updateFrame();
  }

  initialize().catch((error) => {
    const panel = q("[data-error]") || root;
    panel.hidden = false;
    panel.textContent = `Companion unavailable: ${error.message}`;
  });
})();
