(function ownerChordReaderTest() {
  "use strict";

  const API = "/api/owner-chord-test";
  const byId = (id) => document.getElementById(id);
  const KEY_NAMES = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];
  const PITCH_CLASSES = { C: 0, "B#": 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, Fb: 4, "E#": 5, F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11, Cb: 11 };
  const NNS_INTERVALS = ["1", "b2", "2", "b3", "3", "4", "#4", "5", "b6", "6", "b7", "7"];
  const percent = (value) => `${(Number(value || 0) * 100).toFixed(0)}%`;
  const clock = (seconds) => {
    const total = Math.max(0, Math.floor(Number(seconds) || 0));
    return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
  };
  const preciseClock = (seconds) => {
    const value = Math.max(0, Number(seconds) || 0);
    const minutes = Math.floor(value / 60);
    return `${minutes}:${String((value % 60).toFixed(1)).padStart(4, "0")}`;
  };
  let tracks = [];
  let selected = null;
  let timeline = { mode: "exact-model-transitions", items: [] };
  let activeItemId = "";
  let activeChordIndex = -1;
  let displayMode = "nns";
  let selectedKey = "C";

  function status(message, state = "") {
    const node = byId("analysis-status");
    node.textContent = message;
    node.dataset.state = state;
  }

  function chordToNns(symbol) {
    const value = String(symbol || "").trim();
    if (/^(N\.?C\.?|N)$/i.test(value)) return "N.C.";
    const match = value.match(/^([A-G](?:#|b)?)([^/]*)(?:\/([A-G](?:#|b)?))?$/);
    if (!match) return value;
    const tonic = PITCH_CLASSES[selectedKey];
    const root = PITCH_CLASSES[match[1]];
    if (tonic === undefined || root === undefined) return value;
    const quality = (match[2] || "")
      .replace(/^(min)(?!aj)/i, "m")
      .replace(/^dim/i, "°")
      .replace(/^aug/i, "+");
    const bassPitch = PITCH_CLASSES[match[3]];
    const bass = bassPitch === undefined ? "" : `/${NNS_INTERVALS[(bassPitch - tonic + 12) % 12]}`;
    return `${NNS_INTERVALS[(root - tonic + 12) % 12]}${quality}${bass}`;
  }

  function shownChord(symbol) {
    return displayMode === "nns" ? chordToNns(symbol) : symbol;
  }

  function timelineName(mode, plural = false) {
    if (mode === "beat-aligned-bars") return plural ? "bars" : "bar";
    return plural ? "changes" : "change";
  }

  function renderSongList() {
    const list = byId("song-list");
    list.replaceChildren();
    tracks.forEach((track) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = track.id === selected?.id ? "active" : "";
      const title = document.createElement("strong");
      title.textContent = track.title;
      const meta = document.createElement("span");
      const trackTimeline = OwnerChordTiming.itemsForTrack(track);
      meta.textContent = `${clock(track.durationSeconds)} · ${trackTimeline.items.length} ${timelineName(trackTimeline.mode, true)}`;
      button.append(title, meta);
      button.addEventListener("click", () => selectTrack(track.id));
      list.append(button);
    });
  }

  async function seek(seconds) {
    const audio = byId("audio");
    if (audio.readyState === 0) {
      await new Promise((resolve) => audio.addEventListener("loadedmetadata", resolve, { once: true }));
    }
    audio.currentTime = Number(seconds);
    updatePlayback();
    await audio.play();
  }

  function renderBars() {
    const grid = byId("bar-grid");
    grid.replaceChildren();
    timeline.items.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `bar-card${Number(item.confidence) >= 0.9 ? " high-confidence" : ""}${item.splitUncertain ? " uncertain" : ""}`;
      button.dataset.itemId = item.id;
      const number = document.createElement("span");
      number.className = "bar-number";
      number.textContent = `${timelineName(timeline.mode).toUpperCase()} ${item.position} · ${preciseClock(item.start)}`;
      const chord = document.createElement("strong");
      (item.chordSymbols || ["N.C."]).forEach((symbol, index) => {
        const part = document.createElement("span");
        part.dataset.chordPart = String(index);
        part.textContent = shownChord(symbol);
        chord.append(part);
      });
      const confidence = document.createElement("span");
      confidence.textContent = `${percent(item.confidence)} confidence${item.splitUncertain ? " · verify split" : ""}`;
      button.append(number, chord, confidence);
      button.addEventListener("click", () => seek(item.start).catch(() => {}));
      grid.append(button);
    });
  }

  function syncTransport() {
    const audio = byId("audio");
    const button = byId("transport-toggle");
    const playing = !audio.paused && !audio.ended;
    button.firstChild.textContent = playing ? "❚❚ " : "▶ ";
    button.querySelector("span").textContent = playing ? "Pause" : "Play";
    button.setAttribute("aria-label", playing ? "Pause song" : "Play song");
    byId("transport-bar").textContent = byId("current-bar").textContent;
    byId("transport-chord").textContent = byId("current-chord").textContent;
    const currentIndex = timeline.items.findIndex((item) => item.id === activeItemId);
    const current = timeline.items[currentIndex];
    const nextChord = current?.chordSymbols?.[activeChordIndex + 1]
      || timeline.items[currentIndex + 1]?.chordSymbols?.[0];
    byId("transport-next-chord").textContent = nextChord ? shownChord(nextChord) : "—";
    byId("transport-time").textContent = clock(audio.currentTime);
  }

  function keepUpcomingChangesVisible(active) {
    if (!active) return;
    const grid = byId("bar-grid");
    const gridTop = grid.getBoundingClientRect().top;
    const activeTop = active.getBoundingClientRect().top;
    grid.scrollTo({
      top: Math.max(0, grid.scrollTop + activeTop - gridTop - 2),
      behavior: "smooth",
    });
  }

  function updatePlayback() {
    if (!selected) return;
    const time = byId("audio").currentTime;
    const item = OwnerChordTiming.itemAt(timeline.items, time);
    const chordIndex = item ? OwnerChordTiming.chordIndexAt(item, time) : -1;
    if ((item?.id || "") === activeItemId && chordIndex === activeChordIndex) {
      syncTransport();
      return;
    }
    activeItemId = item?.id || "";
    activeChordIndex = chordIndex;
    document.querySelectorAll(".bar-card.active").forEach((card) => {
      card.classList.remove("active");
      card.removeAttribute("aria-current");
    });
    document.querySelectorAll(".bar-card .active-part").forEach((part) => part.classList.remove("active-part"));
    byId("current-bar").textContent = item?.position || "—";
    byId("current-chord").textContent = item ? shownChord(OwnerChordTiming.chordAt(item, time)) : "N.C.";
    byId("current-confidence").textContent = item ? percent(item.confidence) : "—";
    syncTransport();
    const active = document.querySelector(`.bar-card[data-item-id="${activeItemId}"]`);
    active?.classList.add("active");
    active?.setAttribute("aria-current", "true");
    active?.querySelector(`[data-chord-part="${chordIndex}"]`)?.classList.add("active-part");
    keepUpcomingChangesVisible(active);
  }

  function renderSelected() {
    byId("workspace").hidden = false;
    byId("selected-title").textContent = selected.title;
    const rhythm = selected.rhythm || {};
    timeline = OwnerChordTiming.itemsForTrack(selected);
    const positionName = timelineName(timeline.mode);
    const positionPlural = timelineName(timeline.mode, true);
    byId("transport-position-label").textContent = positionName;
    byId("current-position-label").textContent = positionName;
    byId("seek-legend").textContent = `Click any ${positionName} to seek.`;
    byId("bar-grid").setAttribute("aria-label", `Predicted chord ${positionPlural}`);
    const timingMode = byId("timing-mode");
    timingMode.dataset.mode = timeline.mode;
    timingMode.textContent = timeline.mode === "beat-aligned-bars"
      ? "Beat-aligned bars · downbeat phase passed validation. Split chords switch at the bar midpoint."
      : "Exact model timing · downbeat phase was unresolved, so boxes follow the engine's raw chord-change timestamps instead of a guessed bar grid.";
    selectedKey = KEY_NAMES.includes(rhythm.key) ? rhythm.key : "C";
    const key = byId("song-key");
    key.replaceChildren(...KEY_NAMES.map((name) => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      option.selected = name === selectedKey;
      return option;
    }));
    byId("selected-meta").textContent = [
      clock(selected.durationSeconds),
      rhythm.key ? `${rhythm.key} ${rhythm.keyMode || ""}`.trim() : null,
      rhythm.meter,
      rhythm.tempoBpm ? `${Math.round(rhythm.tempoBpm)} BPM` : null,
      `${timeline.items.length} ${positionPlural}`,
    ].filter(Boolean).join(" · ");
    byId("mean-confidence").textContent = percent(selected.summary.meanConfidence);
    byId("disclosure").textContent = `${selected.disclosure} Engine: ${selected.engine.label}. Downbeat phase: ${rhythm.phase?.status || "unresolved"}. Display timing: ${timeline.mode}.`;
    const audio = byId("audio");
    audio.pause();
    audio.src = selected.audioUrl;
    audio.load();
    activeItemId = "";
    activeChordIndex = -1;
    renderSongList();
    renderBars();
    updatePlayback();
    syncTransport();
  }

  function selectTrack(id) {
    selected = tracks.find((track) => track.id === id) || tracks[0];
    if (selected) renderSelected();
  }

  async function loadTracks(preferredId = "") {
    const response = await fetch(`${API}/tracks`, { cache: "no-store" });
    if (!response.ok) throw new Error("The local test library could not load.");
    const library = await response.json();
    tracks = library.tracks || [];
    if (tracks.length) selectTrack(preferredId || tracks[0].id);
  }

  async function analyze(file) {
    if (!file) return;
    const title = byId("song-title-input").value.trim();
    status(`Analyzing ${file.name}. This full-engine pass can take several minutes…`, "working");
    byId("drop-zone").disabled = true;
    try {
      const response = await fetch(`${API}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": file.type || "application/octet-stream",
          "X-File-Name": encodeURIComponent(file.name),
          "X-Song-Title": encodeURIComponent(title),
        },
        body: file,
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "The song could not be analyzed.");
      await loadTracks(result.id);
      byId("song-title-input").value = "";
      byId("file-input").value = "";
      const resultTimeline = OwnerChordTiming.itemsForTrack(result);
      status(`${result.title} is ready: ${resultTimeline.items.length} predicted ${timelineName(resultTimeline.mode, true)}.`, "success");
    } catch (error) {
      status(error instanceof Error ? error.message : String(error), "error");
    } finally {
      byId("drop-zone").disabled = false;
    }
  }

  function installDropZone() {
    const zone = byId("drop-zone");
    const input = byId("file-input");
    zone.addEventListener("click", () => input.click());
    input.addEventListener("change", () => analyze(input.files?.[0]));
    ["dragenter", "dragover"].forEach((name) => zone.addEventListener(name, (event) => {
      event.preventDefault();
      zone.classList.add("dragging");
    }));
    ["dragleave", "drop"].forEach((name) => zone.addEventListener(name, (event) => {
      event.preventDefault();
      zone.classList.remove("dragging");
    }));
    zone.addEventListener("drop", (event) => analyze(event.dataTransfer?.files?.[0]));
  }

  installDropZone();
  byId("transport-toggle").addEventListener("click", () => {
    const audio = byId("audio");
    if (audio.paused) audio.play().catch(() => {});
    else audio.pause();
  });
  byId("song-key").addEventListener("change", (event) => {
    selectedKey = event.target.value;
    activeItemId = "";
    activeChordIndex = -1;
    renderBars();
    updatePlayback();
  });
  document.querySelectorAll("[data-notation]").forEach((button) => button.addEventListener("click", () => {
    displayMode = button.dataset.notation;
    document.querySelectorAll("[data-notation]").forEach((item) => {
      const active = item === button;
      item.classList.toggle("active", active);
      item.setAttribute("aria-pressed", String(active));
    });
    activeItemId = "";
    activeChordIndex = -1;
    renderBars();
    updatePlayback();
  }));
  byId("audio").addEventListener("timeupdate", updatePlayback);
  byId("audio").addEventListener("seeked", updatePlayback);
  byId("audio").addEventListener("play", syncTransport);
  byId("audio").addEventListener("pause", syncTransport);
  byId("audio").addEventListener("ended", syncTransport);
  loadTracks().catch((error) => status(error.message, "error"));
})();
