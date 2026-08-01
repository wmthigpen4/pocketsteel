(function (global) {
  "use strict";

  const songTools = global.STEEL_RAG_SONG_PROJECTS;
  const app = document.querySelector("#play-app");
  const errorPanel = document.querySelector("#play-error");
  const errorCopy = document.querySelector("#play-error-copy");
  const audio = document.querySelector("#play-audio");
  const elements = {
    title: document.querySelector("#play-title"), meta: document.querySelector("#play-meta"), bar: document.querySelector("#play-bar"),
    currentChord: document.querySelector("#current-chord"), currentGrip: document.querySelector("#current-grip"), currentMove: document.querySelector("#current-move"),
    nextLabel: document.querySelector("#next-chord-label"), nextChord: document.querySelector("#next-chord"), nextGrip: document.querySelector("#next-grip"), nextMove: document.querySelector("#next-move"),
    fretboard: document.querySelector("#play-fretboard"), lyric: document.querySelector("#play-lyric"), toggle: document.querySelector("#play-toggle"), restart: document.querySelector("#play-restart"),
    scrub: document.querySelector("#play-scrub"), time: document.querySelector("#play-time"), speed: document.querySelector("#play-speed"), loop: document.querySelector("#play-loop"), volume: document.querySelector("#play-volume"),
    checkpoints: Array.from(document.querySelectorAll("[data-checkpoint]")), nextCard: document.querySelector(".play-cue.is-next")
  };
  const projectId = decodeURIComponent(global.location.pathname.split("/").filter(Boolean).at(-1) || "");
  let track = null;
  let plan = null;
  let chart = null;
  let session = null;
  let renderedState = "";
  let frame = 0;
  let loopBars = 0;
  let assistanceReduced = false;

  function showError(message) {
    cancelAnimationFrame(frame);
    app.hidden = true;
    errorPanel.hidden = false;
    errorCopy.textContent = message;
  }

  function formatTime(seconds) {
    const safe = Math.max(0, Number(seconds || 0));
    return `${Math.floor(safe / 60)}:${String(Math.floor(safe % 60)).padStart(2, "0")}`;
  }

  function accessHeaders(json = false) {
    const headers = { Accept: "application/json" };
    if (json) headers["Content-Type"] = "application/json";
    if (["beta_user", "admin"].includes(session?.role)) headers["X-Steel-Rag-Dev-Access-Role"] = session.role;
    else if (["127.0.0.1", "localhost"].includes(global.location.hostname)) headers["X-Steel-Rag-Dev-Access-Role"] = "beta_user";
    return headers;
  }

  function controlLabel(position) {
    const controls = Array.isArray(position?.controls) && position.controls.length
      ? position.controls
      : [...(position?.pedals || []), ...(position?.levers || [])];
    const compact = controls.map((value) => {
      const text = String(value || "").trim();
      const token = text.toLowerCase();
      if (/^a(?:\s+pedal|\s*\(p1\))?$/.test(token)) return "A";
      if (/^b(?:\s+pedal|\s*\(p2\))?$/.test(token)) return "B";
      if (/^c(?:\s+pedal|\s*\(p3\))?$/.test(token)) return "C";
      if (token.includes("e-lower") || token.includes("e lower")) return "E";
      if (token === "f" || token.includes("f lever") || token.includes("e-raise")) return "F";
      return text.replace(/\s+(?:pedal|lever).*$/i, "");
    }).filter(Boolean);
    return Array.from(new Set(compact)).join("+");
  }

  function gripMarkup(position, muted = false) {
    if (!position) return "";
    const strings = (position.strings || []).map((string) => `<span class="play-string">${string}</span>`).join("");
    const controls = controlLabel(position);
    return `<span>Fret ${position.fret}</span>${strings}${controls ? `<span class="play-control${muted ? " is-muted" : ""}">${controls}</span>` : ""}`;
  }

  function movementInstruction(current, next) {
    const from = current?.position;
    const to = next?.position;
    if (!from) return to ? `Get ready at fret ${to.fret}.` : "Listen for the count-in.";
    if (!to) return "Hold the ending and listen.";
    const fromControls = controlLabel(from);
    const toControls = controlLabel(to);
    const fretMove = from.fret === to.fret ? `Stay at fret ${from.fret}` : `Slide ${from.fret}→${to.fret}`;
    let controlMove = "repick";
    if (fromControls !== toControls) controlMove = toControls ? `press ${toControls}` : `release ${fromControls}`;
    else if (toControls) controlMove = `keep ${toControls}`;
    return `${fretMove} · ${controlMove}`;
  }

  function currentInstruction(current) {
    const position = current?.position;
    if (!position) return "Listen for the count-in.";
    const controls = controlLabel(position);
    return `Play strings ${(position.strings || []).join(" · ")}${controls ? ` · ${controls} down` : ""}`;
  }

  function beatLengthMs(event) {
    const measureIndex = chart?.measures?.findIndex((measure) => measure.id === event?.measureId) ?? -1;
    const starts = track?.barStartsMs || [];
    if (measureIndex < 0 || !Number.isFinite(starts[measureIndex])) return 500;
    const barEnd = Number(starts[measureIndex + 1] ?? track.durationMs);
    const beats = Math.max(1, Number(String(track.meter || "4/4").split("/")[0]) || 4);
    return Math.max(1, (barEnd - starts[measureIndex]) / beats);
  }

  function beatCountdown(current, next, timeMs) {
    const target = current?.endMs ?? next?.startMs;
    if (!Number.isFinite(target)) return "";
    const reference = current || next;
    return Math.max(0, Math.ceil((target - timeMs) / beatLengthMs(reference)));
  }

  function barNumber(event) {
    const index = chart?.measures?.findIndex((measure) => measure.id === event?.measureId) ?? -1;
    return index >= 0 ? index + 1 : 0;
  }

  function lyricAt(timeMs) {
    const cues = track?.lyricCues || [];
    const cue = cues.find((item) => timeMs >= item.startMs && timeMs < item.endMs);
    return cue?.text || (timeMs < Number(track?.barStartsMs?.[0] || 0) ? "Count in…" : "");
  }

  function positionDisplay(event, id, role, sortOrder) {
    const position = event?.position;
    if (!position) return null;
    const notes = Object.fromEntries((position.notes || []).map((note) => [String(note.string), note.note]));
    const intervals = Object.fromEntries((position.notes || []).map((note) => [String(note.string), "chord tone"]));
    return {
      id, label: event.chord, root: position.root, quality: position.quality, positionKind: "song_practice",
      fret: position.fret, strings: position.strings, grip: position.grip, pedals: position.pedals || [], levers: position.levers || [],
      colorRole: role === "current" ? position.controls?.length ? undefined : "open" : "advanced", role, family: "song_practice", tier: "starter",
      visibleByDefault: true, sortOrder, notes, intervals, explanationShort: position.instruction, validationStatus: "pitch_validated",
      stringActionLabels: Object.fromEntries((position.strings || []).map((string) => [String(string), String(string)]))
    };
  }

  function addSvgControlTag(id, label, muted) {
    if (!label) return;
    const group = elements.fretboard.querySelector(`[data-highlight-id="${id}"]`);
    const svg = group?.ownerSVGElement;
    if (!group || !svg || typeof group.getBBox !== "function") return;
    let box;
    try { box = group.getBBox(); } catch (_error) { return; }
    const namespace = "http://www.w3.org/2000/svg";
    const tag = document.createElementNS(namespace, "g");
    tag.setAttribute("class", "play-control-tag");
    tag.setAttribute("aria-label", `${muted ? "Upcoming" : "Current"} controls ${label}`);
    const width = Math.max(38, 15 + (label.length * 8));
    const x = Math.min(1154 - width, box.x + box.width + 6);
    const y = box.y + (box.height / 2) - 12;
    const rect = document.createElementNS(namespace, "rect");
    rect.setAttribute("x", String(x)); rect.setAttribute("y", String(y)); rect.setAttribute("width", String(width)); rect.setAttribute("height", "24"); rect.setAttribute("rx", "12");
    rect.setAttribute("fill", muted ? "#77756e" : "#17130d"); rect.setAttribute("stroke", muted ? "#c8c3b8" : "#fff4dc"); rect.setAttribute("stroke-opacity", muted ? "0.45" : "0.72");
    const text = document.createElementNS(namespace, "text");
    text.setAttribute("x", String(x + (width / 2))); text.setAttribute("y", String(y + 16)); text.setAttribute("text-anchor", "middle"); text.setAttribute("fill", muted ? "#eeeae1" : "#fff4dc"); text.textContent = label;
    tag.append(rect, text);
    svg.append(tag);
  }

  function renderFretboard(current, next) {
    if (!global.STEEL_RAG_FRETBOARD?.mountPedalSteelFretboard) return;
    const positions = [positionDisplay(current, "play-current", "current", 1), positionDisplay(next, "play-next", "next", 2)].filter(Boolean);
    if (!positions.length) { elements.fretboard.innerHTML = ""; return; }
    global.STEEL_RAG_FRETBOARD.mountPedalSteelFretboard(elements.fretboard, {
      title: "Play Along route", maxFret: 15, stringCount: 10, positions,
      selectedPositionId: positions[0].id, hidePositionTools: true, hideFilterControls: true, hideLegend: true,
      showHighlightLabels: false, showStringActionLabels: true, highlightStyle: "prominent", query: { key: track.key }
    });
    addSvgControlTag("play-current", controlLabel(current?.position), false);
    addSvgControlTag("play-next", controlLabel(next?.position), true);
  }

  function renderState(timeMs, force = false) {
    const events = plan?.events || [];
    if (!events.length) return;
    const timeline = songTools.activeTimelineState(events, timeMs);
    const current = timeline.current;
    const next = timeline.next || (!current ? events[0] : null);
    const stateKey = `${current?.id || "count-in"}:${next?.id || "end"}:${assistanceReduced}`;
    const beats = beatCountdown(current, next, timeMs);
    if (force || stateKey !== renderedState) {
      renderedState = stateKey;
      elements.currentChord.textContent = current?.chord || "—";
      elements.currentGrip.innerHTML = assistanceReduced ? "" : gripMarkup(current?.position);
      elements.currentMove.textContent = assistanceReduced ? "Listen and make the change." : currentInstruction(current);
      elements.nextChord.textContent = next?.chord || "End";
      elements.nextGrip.innerHTML = assistanceReduced ? "" : gripMarkup(next?.position, true);
      elements.nextMove.textContent = assistanceReduced ? "" : movementInstruction(current, next);
      const currentBar = barNumber(current || next);
      elements.bar.textContent = current ? `Bar ${currentBar} of ${chart.measures.length}` : "Count-in";
      renderFretboard(current || next, current ? next : events[1]);
    }
    elements.nextLabel.textContent = next ? `Next${controlLabel(next.position) ? `: ${controlLabel(next.position)}` : ""}${beats ? ` · ${beats} beat${beats === 1 ? "" : "s"}` : ""}` : "End";
    elements.nextCard.classList.toggle("is-imminent", Boolean(next && beats <= 2));
    elements.lyric.textContent = assistanceReduced ? "" : lyricAt(timeMs);
  }

  function loopBounds(timeMs) {
    if (!loopBars || !chart?.measures?.length) return null;
    const starts = track.barStartsMs || [];
    let index = starts.findLastIndex((start) => start <= timeMs);
    if (index < 0) index = 0;
    const groupStart = Math.floor(index / loopBars) * loopBars;
    return { startMs: starts[groupStart] || 0, endMs: starts[Math.min(starts.length, groupStart + loopBars)] || track.durationMs };
  }

  function tick() {
    const timeMs = audio.currentTime * 1000;
    renderState(timeMs);
    if (!elements.scrub.matches(":active")) elements.scrub.value = String(audio.currentTime || 0);
    elements.time.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration || track?.durationMs / 1000)}`;
    elements.toggle.textContent = audio.paused ? "▶ Play" : "Pause";
    if (elements.loop.checked) {
      const bounds = loopBounds(timeMs);
      if (bounds && timeMs >= bounds.endMs - 30) audio.currentTime = bounds.startMs / 1000;
    }
    frame = requestAnimationFrame(tick);
  }

  async function arrangeTrack() {
    chart = songTools.parseSongChart(track.chart, { mode: "letter", key: track.key, meter: track.meter });
    if (chart.errors.length) throw new Error(chart.errors.join(" "));
    const practiceProject = {
      key: track.key, meter: track.meter, style: "classic_country", sections: chart.sections, measures: chart.measures,
      barStartsMs: track.barStartsMs, durationMs: track.durationMs, audioRef: { kind: "bundled", durationMs: track.durationMs }, syncOffsetMs: 0
    };
    const activeCopedent = global.STEEL_RAG_COPEDENTS?.activeContext?.();
    const copedentContext = session?.features?.accountCopedents && activeCopedent?.profileId
      ? activeCopedent
      : { profileId: "emmons-e9-basic" };
    const request = songTools.buildArrangePayload(practiceProject, copedentContext);
    const response = await fetch("/api/song-practice/arrange", { method: "POST", headers: accessHeaders(true), body: JSON.stringify(request) });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "The E9 route could not be prepared.");
    return payload;
  }

  async function localProject(id) {
    return new Promise((resolve, reject) => {
      const request = global.indexedDB.open("steel-guitar-rag-practice", 1);
      request.onsuccess = () => {
        const database = request.result;
        if (!database.objectStoreNames.contains("practiceProjects")) { database.close(); resolve(null); return; }
        const read = database.transaction("practiceProjects", "readonly").objectStore("practiceProjects").get(id);
        read.onsuccess = () => { database.close(); resolve(read.result || null); };
        read.onerror = () => { database.close(); reject(read.error); };
      };
      request.onerror = () => reject(request.error);
    });
  }

  async function initialize() {
    if (!songTools) throw new Error("The song timeline could not load.");
    session = await fetch("/api/session", { headers: accessHeaders() }).then((response) => response.json());
    const response = await fetch("/api/song-practice/catalog", { headers: accessHeaders() });
    const catalog = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(catalog.error || "The guided song catalog could not load.");
    track = (catalog.tracks || []).find((item) => (item.projectId || item.id) === projectId);
    if (!track && projectId.startsWith("local-")) {
      const local = await localProject(projectId);
      if (!local) throw new Error("That device-only track is no longer stored in this browser.");
      throw new Error(`${local.title} is stored safely on this device. Chord and timing setup is the next step before Play Along can begin.`);
    }
    if (!track || track.publicationState === "coming_soon") throw new Error("That guided song is still in recording and synchronization review.");
    plan = await arrangeTrack();
    elements.title.textContent = track.title;
    elements.meta.textContent = [track.performer, track.key, track.meter, track.tempo ? `${track.tempo} BPM` : ""].filter(Boolean).join(" · ");
    audio.src = track.audioUrl;
    audio.volume = Number(elements.volume.value);
    audio.playbackRate = Number(elements.speed.value);
    audio.preservesPitch = true;
    audio.addEventListener("loadedmetadata", () => { elements.scrub.max = String(audio.duration); });
    app.hidden = false;
    renderState(0, true);
    frame = requestAnimationFrame(tick);
  }

  elements.toggle.addEventListener("click", async () => { if (audio.paused) await audio.play(); else audio.pause(); });
  elements.restart.addEventListener("click", () => { audio.currentTime = 0; renderState(0, true); });
  elements.scrub.addEventListener("input", () => { audio.currentTime = Number(elements.scrub.value); renderState(audio.currentTime * 1000, true); });
  elements.speed.addEventListener("change", () => { audio.playbackRate = Number(elements.speed.value); audio.preservesPitch = true; });
  elements.volume.addEventListener("input", () => { audio.volume = Number(elements.volume.value); });
  elements.loop.addEventListener("change", () => { if (elements.loop.checked && !loopBars) loopBars = 4; });
  elements.checkpoints.forEach((button) => button.addEventListener("click", () => {
    elements.checkpoints.forEach((item) => item.classList.toggle("is-active", item === button));
    const value = button.dataset.checkpoint;
    if (value === "preview") { audio.pause(); audio.currentTime = track?.barStartsMs?.[0] / 1000 || 0; loopBars = 0; assistanceReduced = false; }
    else if (value === "full") { loopBars = 0; elements.loop.checked = false; assistanceReduced = false; }
    else if (value === "less") { loopBars = 0; elements.loop.checked = false; assistanceReduced = true; }
    else { loopBars = Number(value); elements.loop.checked = true; assistanceReduced = false; }
    renderedState = "";
    renderState(audio.currentTime * 1000, true);
  }));

  initialize().catch((error) => showError(error.message || "Play Along could not start."));
})(window);
