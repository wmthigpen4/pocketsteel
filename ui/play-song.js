(function (global) {
  "use strict";

  const songTools = global.STEEL_RAG_SONG_PROJECTS;
  const practiceTools = global.STEEL_RAG_PRACTICE;
  const ACCOUNT_COPEDENT_STARTUP_BUDGET_MS = 1500;
  const DEFAULT_PLAY_ALONG_COPEDENT = Object.freeze({ profileId: "emmons-e9-basic" });
  const app = document.querySelector("#play-app");
  const errorPanel = document.querySelector("#play-error");
  const errorCopy = document.querySelector("#play-error-copy");
  const audio = document.querySelector("#play-audio");
  const elements = {
    title: document.querySelector("#play-title"), key: document.querySelector("#play-key"), keyJourney: document.querySelector("#play-key-journey"), meta: document.querySelector("#play-meta"), attribution: document.querySelector("#play-attribution"), bar: document.querySelector("#play-bar"),
    objective: document.querySelector("#play-objective"), currentCard: document.querySelector(".play-cue.is-current"), currentKeyChange: document.querySelector("#current-key-change"), currentChord: document.querySelector("#current-chord"), currentGrip: document.querySelector("#current-grip"), currentMelody: document.querySelector("#current-melody"), currentMove: document.querySelector("#current-move"),
    nextLabel: document.querySelector("#next-chord-label"), nextKeyChange: document.querySelector("#next-key-change"), nextDirection: document.querySelector("#next-direction"), nextDirectionArrow: document.querySelector("#next-direction-arrow"), nextDirectionText: document.querySelector("#next-direction-text"), nextChord: document.querySelector("#next-chord"), nextGrip: document.querySelector("#next-grip"), nextMelody: document.querySelector("#next-melody"),
    fretboard: document.querySelector("#play-fretboard"), lyric: document.querySelector("#play-lyric"), toggle: document.querySelector("#play-toggle"), restart: document.querySelector("#play-restart"),
    scrub: document.querySelector("#play-scrub"), time: document.querySelector("#play-time"), speed: document.querySelector("#play-speed"), route: document.querySelector("#play-route"), loop: document.querySelector("#play-loop"), volume: document.querySelector("#play-volume"),
    checkpoints: Array.from(document.querySelectorAll("[data-checkpoint]")), nextCard: document.querySelector(".play-cue.is-next"),
    chordDisplay: document.querySelector("#chord-display"), openSongMap: document.querySelector("#open-song-map"), songMapDialog: document.querySelector("#song-map-dialog"), songMap: document.querySelector("#song-map"), songMapLoop: document.querySelector("#song-map-loop"), closeSongMap: document.querySelector("#close-song-map"),
    countIn: document.querySelector("#play-count-in"), metronome: document.querySelector("#play-metronome"),
    why: document.querySelector("#play-why"), whyTitle: document.querySelector("#play-why-title"), whyCopy: document.querySelector("#play-why-copy"), whyMovement: document.querySelector("#play-why-movement"),
    whyMelody: document.querySelector("#play-why-melody"), whyDegree: document.querySelector("#play-why-degree"), whyRole: document.querySelector("#play-why-role"), whySupport: document.querySelector("#play-why-support"), whyPosition: document.querySelector("#play-why-position"),
    whyAlternatives: document.querySelector("#play-why-alternatives"), whyAlternativeList: document.querySelector("#play-why-alternative-list")
  };
  const startupControls = [elements.toggle, elements.restart, elements.scrub, elements.speed, elements.route, elements.loop, elements.chordDisplay, elements.openSongMap, elements.countIn, elements.metronome, ...elements.checkpoints];
  const projectId = decodeURIComponent(global.location.pathname.split("/").filter(Boolean).at(-1) || "");
  let track = null;
  let plan = null;
  let chart = null;
  let session = null;
  let renderedState = "";
  let frame = 0;
  let loopRange = null;
  let assistanceReduced = false;
  let practiceMode = "full";
  let practiceSession = null;
  let transport = null;
  let localAudioUrl = "";
  let practiceBars = [];
  let loopSelection = [];
  let sessionSaveTimer = 0;
  let lastSessionPositionSave = 0;
  let selectedLessonId = "";
  let lessons = [];
  let playAlongCopedentContext = DEFAULT_PLAY_ALONG_COPEDENT;
  const lessonPlans = new Map();

  function showError(message) {
    cancelAnimationFrame(frame);
    app.hidden = true;
    errorPanel.hidden = false;
    errorCopy.textContent = message;
  }

  function setPlayerReady(ready) {
    startupControls.forEach((control) => { control.disabled = !ready; });
  }

  function showLoadingState() {
    setPlayerReady(false);
    app.hidden = false;
    elements.objective.textContent = "Preparing the reviewed melody route…";
    elements.currentChord.textContent = "…";
    elements.currentMove.textContent = "Loading the synchronized fretboard guidance.";
    elements.nextChord.textContent = "…";
  }

  function formatTime(seconds) {
    const safe = Math.max(0, Number(seconds || 0));
    return `${Math.floor(safe / 60)}:${String(Math.floor(safe % 60)).padStart(2, "0")}`;
  }

  function keyContextForBar(bar) {
    return practiceTools?.keyForBar(track, bar) || { key: track?.key, keyMode: track?.keyMode || "major" };
  }

  function displayedChord(symbol, bar) {
    return practiceTools?.chordForDisplay(symbol, keyContextForBar(bar).key, practiceSession?.chordDisplay || "letters") || symbol;
  }

  function keyDisplayName(context) {
    return `${context?.key || "—"} ${context?.keyMode === "minor" ? "minor" : "major"}`;
  }

  function setKeyChangeCue(element, card, message, context, visible) {
    element.hidden = !visible;
    element.textContent = visible ? `${message} · ${keyDisplayName(context)}` : "";
    card?.classList.toggle("has-key-change", visible);
  }

  function queueSessionSave(force = false) {
    if (!practiceSession || !track) return;
    const write = () => {
      practiceSession = { ...practiceSession, mode: practiceMode, speed: Number(elements.speed.value), volume: Number(elements.volume.value), loopStartBar: loopRange?.startBar ?? null, loopEndBar: loopRange?.endBar ?? null, countIn: elements.countIn.checked, metronome: elements.metronome.checked, lastPositionMs: Math.round(audio.currentTime * 1000), updatedAt: new Date().toISOString() };
      practiceTools.saveSession(practiceSession).catch((error) => global.console?.warn?.("Practice settings could not be saved.", error));
    };
    global.clearTimeout(sessionSaveTimer);
    if (force) write(); else sessionSaveTimer = global.setTimeout(write, 180);
  }

  function accessHeaders(json = false) {
    const headers = { Accept: "application/json" };
    if (json) headers["Content-Type"] = "application/json";
    if (["beta_user", "admin"].includes(session?.role)) headers["X-Steel-Rag-Dev-Access-Role"] = session.role;
    else if (["127.0.0.1", "localhost"].includes(global.location.hostname)) headers["X-Steel-Rag-Dev-Access-Role"] = "beta_user";
    return headers;
  }

  function activeLesson() {
    return lessons.find((lesson) => lesson.id === selectedLessonId) || lessons[0] || null;
  }

  function isMelodyLesson() {
    return activeLesson()?.kind === "melody";
  }

  function compactControlToken(value) {
    const text = practiceTools?.controlLabelForDisplay(value) || String(value || "").trim();
    const token = text.toLowerCase();
    if (/^a(?:\s+pedal|\s*\(p1\))?$/.test(token)) return "A";
    if (/^b(?:\s+pedal|\s*\(p2\))?$/.test(token)) return "B";
    if (/^c(?:\s+pedal|\s*\(p3\))?$/.test(token)) return "C";
    if (token.includes("e-lower") || token.includes("e lower")) return "E";
    if (token === "f" || token.includes("f lever") || token.includes("e-raise")) return "F";
    return text.replace(/\s+(?:pedal|lever).*$/i, "");
  }

  function displayControlLabels(values) {
    return practiceTools?.controlLabelsForDisplay(values)
      || Array.from(new Set((Array.isArray(values) ? values : []).map(compactControlToken).filter(Boolean)));
  }

  function noteControlLabel(note) {
    const changes = Array.isArray(note?.changes) && note.changes.length ? note.changes : (note?.changeLabels || []);
    return Array.from(new Set(changes.map(compactControlToken).filter(Boolean))).join("+");
  }

  function stringControlMap(position) {
    return new Map((position?.notes || []).map((note) => [Number(note.string), noteControlLabel(note)]));
  }

  function gripMarkup(position, showStrings = true) {
    if (!position) return "";
    if (!showStrings) return `<span class="play-grip__fret">Fret ${position.fret}</span>`;
    const controlsByString = stringControlMap(position);
    const strings = (position.strings || []).map((string) => {
      const control = controlsByString.get(Number(string));
      return `<span class="play-string">${string}${control ? ` ${control}` : ""}</span>`;
    }).join("");
    return `<span class="play-grip__fret">Fret ${position.fret}</span><span class="play-grip__strings" aria-label="Strings ${(position.strings || []).join(", ")}">${strings}</span>`;
  }

  function movementIndicator(current, next) {
    const fromFret = Number(current?.position?.fret);
    const toFret = Number(next?.position?.fret);
    if (!Number.isFinite(toFret)) return null;
    if (!Number.isFinite(fromFret)) {
      return { direction: "same", symbol: "●", label: `Start fret ${toFret}`, accessible: `Start at fret ${toFret}` };
    }
    const change = toFret - fromFret;
    if (change === 0) {
      return { direction: "same", symbol: "●", label: "Same fret", accessible: `Stay at fret ${toFret}` };
    }
    const direction = change > 0 ? "up" : "down";
    const distance = Math.abs(change);
    const fretLabel = distance === 1 ? "fret" : "frets";
    return {
      direction,
      symbol: change > 0 ? "↑" : "↓",
      label: `${direction} ${distance} ${fretLabel}`,
      accessible: `Move ${direction} ${distance} ${fretLabel}, from fret ${fromFret} to fret ${toFret}`
    };
  }

  function renderMovementIndicator(current, next) {
    const indicator = movementIndicator(current, next);
    elements.nextDirection.hidden = assistanceReduced || !indicator;
    if (!indicator) return;
    elements.nextDirection.className = `play-direction is-${indicator.direction}`;
    elements.nextDirection.setAttribute("aria-label", indicator.accessible);
    elements.nextDirectionArrow.textContent = indicator.symbol;
    elements.nextDirectionText.textContent = indicator.label;
  }

  function currentInstruction(current) {
    const position = current?.position;
    if (noChordEvent(current)) return "Rest · keep your place and listen.";
    if (!position) return "Listen for the count-in.";
    const strings = position.strings || [];
    const instruction = strings.length === 1 ? `Pick string ${strings[0]}` : `Play strings ${strings.join(" · ")}`;
    const controls = new Set((position.controls || []).map(compactControlToken));
    const stringFive = (position.notes || []).find((note) => Number(note.string) === 5);
    const stringTen = (position.notes || []).find((note) => Number(note.string) === 10);
    const cRaisesFive = (stringFive?.changes || []).map(compactControlToken).includes("C");
    const tenStaysOpen = stringTen && !(stringTen.changes || []).length;
    if (position.quality === "minor7" && controls.has("C") && !controls.has("A") && cRaisesFive && tenStaysOpen) {
      return `${instruction}. C is intentional: it raises string 5 while leaving string 10 at the ♭7.`;
    }
    return instruction;
  }

  function melodyCueText(event) {
    const position = event?.position;
    if (!position?.melodyPitchLabel) return "";
    return `★ Melody ${position.melodyPitchLabel} on top`;
  }

  function beatLengthMs(event) {
    const authoredBar = Number(event?.bar);
    const measureIndex = Number.isFinite(authoredBar) && authoredBar > 0
      ? authoredBar - 1
      : chart?.measures?.findIndex((measure) => measure.id === event?.measureId) ?? -1;
    const starts = track?.barStartsMs || [];
    if (measureIndex < 0 || !Number.isFinite(starts[measureIndex])) return 500;
    const barEnd = Number(starts[measureIndex + 1] ?? track.durationMs);
    const beats = Math.max(1, Number(String(track.meter || "4/4").split("/")[0]) || 4);
    return Math.max(1, (barEnd - starts[measureIndex]) / beats);
  }

  function beatCountdown(current, next, timeMs) {
    const target = current?.endMs ?? next?.startMs;
    if (!Number.isFinite(target)) return "";
    if (isMelodyLesson()) {
      const remaining = Math.max(0, (target - timeMs) / beatLengthMs(current || next));
      return Math.ceil(remaining * 2) / 2;
    }
    const authoredBeats = Array.isArray(track?.beatTimesMs) ? track.beatTimesMs : [];
    if (authoredBeats.length) {
      return authoredBeats.filter((beat) => beat > timeMs + 1 && beat <= target + 1).length;
    }
    const reference = current || next;
    return Math.max(0, Math.ceil((target - timeMs) / beatLengthMs(reference)));
  }

  function barNumber(event) {
    if (Number.isFinite(Number(event?.bar))) return Number(event.bar);
    const index = chart?.measures?.findIndex((measure) => measure.id === event?.measureId) ?? -1;
    return index >= 0 ? index + 1 : 0;
  }

  function beatLabel(beats) {
    if (!beats) return "";
    if (beats === 0.5) return "½ beat";
    return `${beats} beat${beats === 1 ? "" : "s"}`;
  }

  function lyricAt(timeMs) {
    const cues = track?.lyricCues || [];
    const cue = cues.find((item) => timeMs >= item.startMs && timeMs < item.endMs);
    return cue?.text || (timeMs < Number(track?.barStartsMs?.[0] || 0) ? "Count in…" : "");
  }

  function positionDisplay(event, id, role, sortOrder) {
    const position = event?.position;
    if (!position) return null;
    const controlsByString = stringControlMap(position);
    const notes = Object.fromEntries((position.notes || []).map((note) => [String(note.string), note.note]));
    const intervals = Object.fromEntries((position.notes || []).map((note) => [String(note.string), "chord tone"]));
    return {
      id, label: event.chord, root: position.root, quality: position.quality, positionKind: "song_practice",
      fret: position.fret, strings: position.strings, grip: position.grip, pedals: position.pedals || [], levers: position.levers || [],
      colorRole: role === "current" ? position.controls?.length ? undefined : "open" : "advanced", role, family: "song_practice", tier: "starter",
      visibleByDefault: true, sortOrder, notes, intervals, explanationShort: position.instruction, validationStatus: "pitch_validated",
      stringActionLabels: Object.fromEntries((position.strings || []).map((string) => [
        String(string),
        [String(string), controlsByString.get(Number(string))].filter(Boolean).join(" ")
      ]))
    };
  }

  function noChordEvent(event) {
    return Boolean(event && (event.isRest || event.status === "rest" || event.role === "rest" || !event.chord));
  }

  function fretboardAnchorEvent(current, next, timeMs) {
    if (current?.position) return current;
    const events = plan?.events || [];
    const previous = events.filter((event) => event?.position && Number(event.startMs) <= timeMs).at(-1);
    if (previous) return previous;
    if (next?.position) return next;
    return events.find((event) => event?.position && Number(event.startMs) >= timeMs) || null;
  }

  function leftAlignSvgStringLabels(id) {
    const group = elements.fretboard.querySelector(`[data-highlight-id="${id}"]`);
    if (!group) return;
    group.querySelectorAll(".pedal-steel-fretboard__string-action-label").forEach((label) => {
      const string = label.getAttribute("data-string-action-label-string");
      const dot = group.querySelector(`[data-highlight-dot][data-highlight-string="${string}"]`);
      if (!dot) return;
      const dotX = Number(dot.getAttribute("x"));
      label.textContent = String(label.textContent || "").replace(/^(\d+)(?=\D)/, "$1 ");
      label.setAttribute("x", String(dotX + 7));
      label.setAttribute("text-anchor", "start");
    });
  }

  function addMelodyVoiceTag(id, position, role, forceLeft = false) {
    if (assistanceReduced || !position?.melodyString || !position?.melodyPitchLabel) return;
    const group = elements.fretboard.querySelector(`[data-highlight-id="${id}"]`);
    const dot = group?.querySelector(`[data-highlight-dot][data-highlight-string="${position.melodyString}"]`);
    if (!group || !dot) return;
    const dotX = Number(dot.getAttribute("x"));
    const dotY = Number(dot.getAttribute("y"));
    const dotWidth = Number(dot.getAttribute("width"));
    const tagWidth = 112;
    const tagHeight = 22;
    const placeLeft = forceLeft || dotX > 1010;
    const tagX = placeLeft ? dotX - tagWidth - 6 : dotX + dotWidth + 6;
    const tag = document.createElementNS("http://www.w3.org/2000/svg", "g");
    tag.setAttribute("class", `play-melody-tag is-${role}`);
    tag.setAttribute("data-melody-string", String(position.melodyString));
    tag.setAttribute("aria-label", `${role === "next" ? "Upcoming" : "Current"} melody ${position.melodyPitchLabel} on string ${position.melodyString}`);
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", String(tagX));
    rect.setAttribute("y", String(dotY + 1));
    rect.setAttribute("width", String(tagWidth));
    rect.setAttribute("height", String(tagHeight));
    rect.setAttribute("rx", "11");
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", String(tagX + (tagWidth / 2)));
    label.setAttribute("y", String(dotY + 16));
    label.setAttribute("text-anchor", "middle");
    label.textContent = `★ MELODY ${position.melodyPitchLabel}`;
    tag.append(rect, label);
    group.append(tag);
    group.setAttribute("aria-label", `${group.getAttribute("aria-label") || "Fretboard position"}. Melody ${position.melodyPitchLabel} is on string ${position.melodyString}.`);
  }

  function sameFret(left, right) {
    return Boolean(left && right && left.fret === right.fret);
  }

  function samePosition(left, right) {
    if (!sameFret(left, right)) return false;
    const signature = (position) => JSON.stringify({
      strings: (position?.strings || []).map(Number),
      controls: displayControlLabels(position?.controlLabels || position?.controls || []).sort()
    });
    return signature(left) === signature(right);
  }

  function renderOffsetX(group) {
    return Number(group?.getAttribute("data-highlight-render-offset-x")) || 0;
  }

  function centerSameFretCurrentGrip() {
    const group = elements.fretboard.querySelector('[data-highlight-id="play-current"]');
    if (!group) return;
    group.setAttribute("transform", `translate(${-renderOffsetX(group)} 0)`);
  }

  function separateSameFretNextGrip(position) {
    const group = elements.fretboard.querySelector('[data-highlight-id="play-next"]');
    const firstDot = group?.querySelector("[data-highlight-dot]");
    if (!group || !firstDot) return;
    const dotX = Number(firstDot.getAttribute("x"));
    const dotY = Number(firstDot.getAttribute("y"));
    const dotWidth = Number(firstDot.getAttribute("width"));
    const sideOffset = dotX > 1050 ? -76 : 76;
    const offset = sideOffset - renderOffsetX(group);
    group.classList.add("is-same-fret-next");
    group.setAttribute("transform", `translate(${offset} 0)`);
    group.setAttribute("aria-label", `Upcoming grip at the same fret ${position?.fret}`);
    const caption = document.createElementNS("http://www.w3.org/2000/svg", "text");
    caption.setAttribute("class", "play-next-grip-caption");
    caption.setAttribute("x", String(dotX + (dotWidth / 2)));
    caption.setAttribute("y", String(dotY - 6));
    caption.setAttribute("text-anchor", "middle");
    caption.textContent = "NEXT · SAME FRET";
    group.append(caption);
  }

  function addFretMovementArrow(currentPosition, nextPosition) {
    const fromFret = Number(currentPosition?.fret);
    const toFret = Number(nextPosition?.fret);
    if (!Number.isFinite(fromFret) || !Number.isFinite(toFret) || fromFret === toFret) return;
    const svg = elements.fretboard.querySelector("svg");
    const currentGroup = elements.fretboard.querySelector('[data-highlight-id="play-current"]');
    const nextGroup = elements.fretboard.querySelector('[data-highlight-id="play-next"]');
    const fromX = Number(currentGroup?.getAttribute("data-highlight-fret-x"));
    const toX = Number(nextGroup?.getAttribute("data-highlight-fret-x"));
    if (!svg || !Number.isFinite(fromX) || !Number.isFinite(toX)) return;

    const direction = toX > fromX ? 1 : -1;
    const distance = Math.abs(toFret - fromFret);
    const gap = Math.abs(toX - fromX);
    const inset = Math.min(24, Math.max(7, gap * 0.18));
    const startX = fromX + (direction * inset);
    const endX = toX - (direction * inset);
    const head = Math.min(13, Math.max(8, gap * 0.12));
    const y = 37;
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("class", `play-fret-move-arrow${distance >= 4 ? " is-large" : " is-slide"}`);
    group.setAttribute("data-fret-move-from", String(fromFret));
    group.setAttribute("data-fret-move-to", String(toFret));
    group.setAttribute("data-fret-move-distance", String(distance));
    group.setAttribute("aria-label", `Move from fret ${fromFret} to fret ${toFret}, ${distance} fret${distance === 1 ? "" : "s"}`);

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("class", "play-fret-move-arrow__line");
    line.setAttribute("x1", String(startX));
    line.setAttribute("y1", String(y));
    line.setAttribute("x2", String(endX - (direction * head * 0.7)));
    line.setAttribute("y2", String(y));

    const arrowHead = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    arrowHead.setAttribute("class", "play-fret-move-arrow__head");
    arrowHead.setAttribute("points", [
      `${endX},${y}`,
      `${endX - (direction * head)},${y - head * 0.7}`,
      `${endX - (direction * head)},${y + head * 0.7}`
    ].join(" "));

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("class", "play-fret-move-arrow__label");
    label.setAttribute("x", String((startX + endX) / 2));
    label.setAttribute("y", "25");
    label.setAttribute("text-anchor", "middle");
    label.textContent = distance >= 4 ? `MOVE ${distance}` : `SLIDE ${distance}`;
    group.append(line, arrowHead, label);
    svg.append(group);
  }

  function renderFretboard(current, next, timeMs) {
    if (!global.STEEL_RAG_FRETBOARD?.mountPedalSteelFretboard) return;
    const displayedCurrent = fretboardAnchorEvent(current, next, timeMs);
    const visibleNext = assistanceReduced || displayedCurrent === next || samePosition(displayedCurrent?.position, next?.position) ? null : next;
    const sharedFret = sameFret(displayedCurrent?.position, visibleNext?.position);
    const positions = [positionDisplay(displayedCurrent, "play-current", "current", 1), positionDisplay(visibleNext, "play-next", "next", 2)].filter(Boolean);
    if (!positions.length) { elements.fretboard.innerHTML = ""; return; }
    global.STEEL_RAG_FRETBOARD.mountPedalSteelFretboard(elements.fretboard, {
      title: "Play Along route", maxFret: 24, stringCount: 10, positions,
      selectedPositionId: positions[0].id, hidePositionTools: true, hideFilterControls: true, hideLegend: true,
      showHighlightLabels: false, showStringActionLabels: true, highlightStyle: "prominent", query: { key: track.key }
    });
    leftAlignSvgStringLabels("play-current");
    leftAlignSvgStringLabels("play-next");
    if (sharedFret) {
      centerSameFretCurrentGrip();
      separateSameFretNextGrip(visibleNext?.position);
    }
    addFretMovementArrow(displayedCurrent?.position, visibleNext?.position);
    addMelodyVoiceTag("play-current", displayedCurrent?.position, "current", sharedFret);
    addMelodyVoiceTag("play-next", visibleNext?.position, "next");
  }

  function readableRole(event) {
    const role = String(event?.harmonyFunction || event?.arrangementRole || "melody voice").replaceAll("_", " ");
    const chord = event?.chord ? ` of ${event.chord}` : "";
    return `${role.replace(/^./, (letter) => letter.toUpperCase())}${chord}`;
  }

  function alternativeTradeoff(alternative, current) {
    const fret = Number(alternative?.fret);
    const controls = displayControlLabels(alternative?.controlLabels || alternative?.controls || []);
    const distance = Number.isFinite(fret) && Number.isFinite(Number(current?.position?.fret))
      ? Math.abs(fret - Number(current.position.fret))
      : 0;
    if (distance >= 5) return `${distance}-fret move; same melody pitch`;
    if (controls.length) return `${controls.join("+")} control posture; same melody pitch`;
    return "Another mechanically valid place for the same melody pitch";
  }

  function renderWhyDetails(current) {
    const position = current?.position;
    if (!position?.melodyPitchLabel) return;
    const strings = position.strings || [];
    const positionName = strings.length > 1 ? `grip ${strings.join("–")}` : `string ${strings[0]}`;
    elements.whyTitle.textContent = `Why ${positionName} here?`;
    elements.whyCopy.textContent = current.selectionReason || `This position keeps ${position.melodyPitchLabel} above the supporting voices.`;
    elements.whyMovement.textContent = current.movement ? `From the previous note: ${current.movement}` : "Start here and listen for the melody on top.";
    elements.whyMelody.textContent = `${position.melodyPitchLabel} · string ${position.melodyString}`;
    elements.whyDegree.textContent = current.scaleDegree ? `Degree ${current.scaleDegree} in ${track.key}` : "—";
    elements.whyRole.textContent = readableRole(current);
    elements.whySupport.textContent = (current.supportingPitches || []).join(" · ") || "No supporting note on this event";
    const controlsByString = stringControlMap(position);
    const stringPosture = strings.map((string) => `${string}${controlsByString.get(Number(string)) ? ` ${controlsByString.get(Number(string))}` : " open"}`).join(" · ");
    elements.whyPosition.textContent = `Fret ${position.fret} · grip ${strings.join("–")} · ${stringPosture}`;
    const alternatives = (current.alternatives || []).slice(0, 2);
    elements.whyAlternativeList.replaceChildren(...alternatives.map((alternative) => {
      const card = document.createElement("div");
      card.className = "play-why-alternative";
      const stringsForAlternative = alternative.strings || (alternative.notes || []).map((note) => note.string);
      const controls = displayControlLabels(alternative.controlLabels || alternative.controls || []);
      const title = document.createElement("strong");
      title.textContent = `Fret ${alternative.fret} · strings ${stringsForAlternative.join("–")}${controls.length ? ` · ${controls.join("+")}` : " · open"} · top ${position.melodyPitchLabel}`;
      const tradeoff = document.createElement("span");
      tradeoff.textContent = alternativeTradeoff(alternative, current);
      card.append(title, tradeoff);
      return card;
    }));
    elements.whyAlternatives.hidden = alternatives.length === 0;
  }

  function renderState(timeMs, force = false) {
    const events = plan?.events || [];
    if (!events.length) return;
    const timeline = songTools.activeTimelineState(events, timeMs);
    const pickupStartMs = Number(track?.lyricCues?.[0]?.startMs);
    const isPickup = !timeline.current && timeline.next === events[0] && Number.isFinite(pickupStartMs) && timeMs >= pickupStartMs;
    const next = isPickup ? events[1] || null : timeline.next || (!timeline.current ? events[0] : null);
    const current = isPickup
      ? { ...events[0], startMs: pickupStartMs, isPickup: true }
      : timeline.current || restEventAt(timeMs, next);
    const currentBar = barNumber(current || next);
    const nextBar = barNumber(next || current);
    const stateKey = `${current?.id || "count-in"}:${next?.id || "end"}:${isPickup ? "pickup" : "bar"}:${assistanceReduced}:${keyContextForBar(currentBar).key}`;
    const beats = beatCountdown(current, next, timeMs);
    if (force || stateKey !== renderedState) {
      renderedState = stateKey;
      elements.currentChord.textContent = noChordEvent(current) ? "N.C." : displayedChord(current?.chord || "—", currentBar);
      elements.currentGrip.innerHTML = assistanceReduced ? "" : gripMarkup(current?.position, false);
      elements.currentMelody.textContent = assistanceReduced ? "" : melodyCueText(current);
      elements.currentMelody.hidden = !elements.currentMelody.textContent;
      elements.currentMove.textContent = assistanceReduced ? "Listen and make the change." : currentInstruction(current);
      elements.nextChord.textContent = next ? displayedChord(next.chord, nextBar) : "End";
      elements.nextGrip.innerHTML = assistanceReduced ? "" : gripMarkup(next?.position);
      elements.nextMelody.textContent = assistanceReduced ? "" : melodyCueText(next);
      elements.nextMelody.hidden = !elements.nextMelody.textContent;
      renderMovementIndicator(current, next);
      const activeKey = keyContextForBar(currentBar);
      const upcomingKey = next ? keyContextForBar(nextBar) : null;
      const currentStartsNewKey = Boolean(current && currentBar > 1 && activeKey.region?.startBar === currentBar);
      const nextCrossesKey = Boolean(next && nextBar !== currentBar && upcomingKey && (activeKey.key !== upcomingKey.key || activeKey.keyMode !== upcomingKey.keyMode));
      setKeyChangeCue(elements.currentKeyChange, elements.currentCard, "Key change", activeKey, currentStartsNewKey);
      setKeyChangeCue(elements.nextKeyChange, elements.nextCard, "Key change ahead", upcomingKey, nextCrossesKey);
      elements.key.textContent = `${activeKey.key}${activeKey.keyMode === "minor" ? " minor" : ""}`;
      elements.bar.textContent = current?.isPickup ? `Pickup · Bar 1 of ${chart.measures.length}` : current ? `Bar ${currentBar} of ${chart.measures.length}` : "Count-in";
      renderFretboard(current, next, timeMs);
      renderWhyDetails(current);
      renderSongMapActive(currentBar);
    }
    elements.nextLabel.textContent = next ? `Next${beats ? ` · ${beatLabel(beats)}` : ""}` : "End";
    elements.nextCard.classList.toggle("is-imminent", Boolean(next && beats <= 2));
    elements.lyric.textContent = assistanceReduced ? "" : lyricAt(timeMs);
    elements.why.hidden = !(audio.paused && isMelodyLesson() && current?.position?.melodyPitchLabel && !assistanceReduced);
  }

  function currentBarIndex(timeMs = audio.currentTime * 1000) {
    return Math.max(0, (track?.barStartsMs || []).findLastIndex((start) => start <= timeMs));
  }

  function ensureLoopRange() {
    if (loopRange) return loopRange;
    const index = currentBarIndex();
    loopRange = practiceTools.barsToLoopRange(track, index + 1, Math.min((track.barStartsMs || []).length, index + 2));
    transport?.setLoop(loopRange, true);
    return loopRange;
  }

  function renderSongMapActive(barNumberValue) {
    elements.songMap?.querySelectorAll("[data-map-bar]").forEach((button) => {
      const active = Number(button.dataset.mapBar) === Number(barNumberValue);
      button.classList.toggle("is-active", active);
      if (active && elements.songMapDialog?.open) button.scrollIntoView({ block: "nearest", inline: "nearest" });
    });
  }

  function renderSongMap() {
    if (!elements.songMap) return;
    practiceBars = practiceTools.projectBars(track, plan);
    elements.songMap.replaceChildren(...practiceBars.map((bar) => {
      const button = document.createElement("button");
      button.type = "button"; button.className = "song-map-bar"; button.dataset.mapBar = String(bar.barNumber);
      if (loopRange && bar.barNumber >= loopRange.startBar && bar.barNumber <= loopRange.endBar) button.classList.add("is-looped");
      const keyContext = keyContextForBar(bar.barNumber);
      const keyChange = keyContext.region?.startBar === bar.barNumber && bar.barNumber > 1;
      if (keyChange) button.classList.add("has-key-change");
      const chordMarkup = bar.chords.length ? bar.chords.map((chord) => `<span style="--start:${chord.startFraction};--length:${chord.durationFraction}">${displayedChord(chord.symbol, bar.barNumber)}</span>`).join("") : "<span>N.C.</span>";
      const move = bar.firstMove ? `Fret ${bar.firstMove.fret}${bar.firstMove.controls?.length ? ` · ${bar.firstMove.controls.join("+")}` : ""}` : "Listen";
      button.innerHTML = `${keyChange ? `<i>New key · ${keyContext.key} ${keyContext.keyMode}</i>` : ""}<small>Bar ${bar.barNumber}</small><strong>${chordMarkup}</strong><em>${move}</em>`;
      button.setAttribute("aria-label", `Bar ${bar.barNumber}, ${bar.chords.map((item) => displayedChord(item.symbol, bar.barNumber)).join(", ") || "no chord"}${keyChange ? `, new key ${keyContext.key} ${keyContext.keyMode}` : ""}. Seek without autoplay.`);
      button.onclick = () => {
        if (elements.songMapLoop.dataset.selecting === "true") {
          loopSelection.push(bar.barNumber);
          if (loopSelection.length === 1) { elements.songMapLoop.textContent = `Choose end (starts ${bar.barNumber})`; button.classList.add("is-loop-anchor"); }
          else { loopRange = practiceTools.barsToLoopRange(track, Math.min(...loopSelection), Math.max(...loopSelection)); elements.loop.checked = true; practiceMode = "loop"; transport.setLoop(loopRange, true); elements.songMapLoop.dataset.selecting = "false"; elements.songMapLoop.textContent = "Set Loop"; loopSelection = []; updateModeButtons(); renderSongMap(); queueSessionSave(); }
        } else { transport.pause(); transport.seek(bar.startMs); renderState(bar.startMs, true); }
      };
      return button;
    }));
    renderSongMapActive(currentBarIndex() + 1);
  }

  function restEventAt(timeMs, next) {
    if (!next || timeMs < Number(track?.barStartsMs?.[0] || 0)) return null;
    const starts = track?.barStartsMs || [];
    const barIndex = Math.max(0, starts.findLastIndex((start) => start <= timeMs));
    const measure = chart?.measures?.[barIndex];
    return {
      id: `rest-${barIndex + 1}-${next.id}`, chord: measure?.resolvedChords?.[0] || next.chord,
      bar: barIndex + 1, startMs: starts[barIndex], endMs: next.startMs, isRest: true, position: null
    };
  }

  function tick() {
    const timeMs = transport ? transport.update() : audio.currentTime * 1000;
    renderState(timeMs);
    if (!elements.scrub.matches(":active")) elements.scrub.value = String(audio.currentTime || 0);
    elements.time.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration || track?.durationMs / 1000)}`;
    elements.toggle.textContent = audio.paused ? "▶ Play" : "Pause";
    if (practiceSession && timeMs - lastSessionPositionSave > 5000) { lastSessionPositionSave = timeMs; queueSessionSave(); }
    frame = requestAnimationFrame(tick);
  }

  function activeCopedentContext() {
    return { ...playAlongCopedentContext };
  }

  async function configurePlayAlongCopedent() {
    const configureAccount = global.STEEL_RAG_COPEDENTS?.configureAccount;
    if (typeof configureAccount !== "function") return;
    let timeoutId = 0;
    const startupBudget = new Promise((resolve) => {
      timeoutId = global.setTimeout(resolve, ACCOUNT_COPEDENT_STARTUP_BUDGET_MS);
    });
    try {
      await Promise.race([
        configureAccount(session, {
          accessRole: ["beta_user", "admin"].includes(session?.role) ? session.role : ""
        }),
        startupBudget
      ]);
    } catch (error) {
      global.console?.warn?.("Account copedent sync is unavailable; Play Along will use standard E9 for this session.", error);
    } finally {
      global.clearTimeout(timeoutId);
    }
    const requestContext = global.STEEL_RAG_COPEDENTS?.requestContext?.();
    playAlongCopedentContext = session?.features?.accountCopedents && requestContext?.profileId
      ? { ...requestContext }
      : DEFAULT_PLAY_ALONG_COPEDENT;
  }

  function selectedChordRoute(lesson = activeLesson()) {
    const options = Array.isArray(track?.routeOptions) ? track.routeOptions : [];
    return options.find((option) => option.id === lesson?.routeId) || null;
  }

  function updateLessonDescription() {
    const lesson = activeLesson();
    elements.route.title = lesson?.description || "Choose what this Play Along lesson teaches.";
    elements.objective.textContent = lesson?.objective || "Follow the reviewed E9 route.";
  }

  function updateModeButtons() {
    elements.checkpoints.forEach((button) => button.classList.toggle("is-active", button.dataset.checkpoint === practiceMode));
    document.querySelector("#preview-step-controls").hidden = practiceMode !== "preview";
    elements.loop.checked = practiceMode === "loop" && Boolean(loopRange);
    transport?.setLoop(loopRange, elements.loop.checked);
  }

  function stepGrip(direction) {
    const events = plan?.events || [];
    if (!events.length) return;
    const currentIndex = Math.max(0, events.findLastIndex((event) => Number(event.startMs) <= audio.currentTime * 1000 + 1));
    const nextIndex = Math.max(0, Math.min(events.length - 1, currentIndex + direction));
    transport.pause(); transport.seek(events[nextIndex].startMs); renderState(events[nextIndex].startMs, true); queueSessionSave();
  }

  async function arrangeMelodyLessons() {
    const melody = Array.isArray(track?.melodyTimeline) ? track.melodyTimeline : [];
    if (!melody.length || !session?.features?.melodyExercise) return;
    const request = {
      kind: "song_arrangement_lesson", key: track.key, meter: track.meter, pickupBeats: 1,
      wholeSong: true, texture: "both", sourceProvided: true, accuracy: "exact", accuracyConfidence: "high",
      accuracyNote: "Reviewed public-domain melody aligned to the confirmed Play Along beat grid.",
      responseMode: "play_along_lessons",
      playAlongTimeline: melody,
      playAlongOpeningChordMelodyEvents: 3,
      melody: melody.map((event) => ({
        token: event.pitch, pitch: event.pitch, pitchValue: event.pitchValue, durationBeats: event.durationBeats,
        measure: event.measure, beat: event.beat, chord: event.chord, origin: event.origin
      })),
      copedentContext: activeCopedentContext()
    };
    const response = await fetch("/api/amazing-tablature/arrange", { method: "POST", headers: accessHeaders(true), body: JSON.stringify(request) });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "The melody route could not be prepared.");
    const lessonPayload = payload?.playAlongLessons;
    if (lessonPayload?.schemaVersion !== "play_along_melody_lessons_v1") throw new Error("The synchronized melody lesson contract is unavailable.");
    (lessonPayload.lessons || []).forEach((lesson) => {
      if (!Array.isArray(lesson.events) || lesson.events.length !== melody.length) throw new Error(`${lesson.id || "Melody lesson"} did not preserve all reviewed melody events.`);
      lessonPlans.set(lesson.id, lesson);
    });
  }

  async function arrangeChordLesson(lesson) {
    chart = songTools.parseSongChart(track.chart, { mode: "letter", key: track.key, meter: track.meter });
    if (chart.errors.length) throw new Error(chart.errors.join(" "));
    if (Array.isArray(track.timelineChords)) {
      chart.measures.forEach((measure, measureIndex) => {
        const events = track.timelineChords.filter((event) => Number(event.bar) === measureIndex + 1).sort((left, right) => Number(left.startFraction || 0) - Number(right.startFraction || 0));
        if (events.length === measure.resolvedChords.length) measure.chordFractions = events.map((event) => Number(event.startFraction || 0));
      });
    }
    const route = selectedChordRoute(lesson);
    const practiceProject = {
      key: track.key, meter: track.meter, style: "classic_country", sections: chart.sections, measures: chart.measures,
      barStartsMs: track.barStartsMs, durationMs: track.durationMs, audioRef: { kind: "bundled", durationMs: track.durationMs },
      authoredRoute: route?.positions || track.authoredRoute || [], syncOffsetMs: 0
    };
    const request = songTools.buildArrangePayload(practiceProject, activeCopedentContext());
    const response = await fetch("/api/song-practice/arrange", { method: "POST", headers: accessHeaders(true), body: JSON.stringify(request) });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "The E9 route could not be prepared.");
    return payload;
  }

  async function loadActiveLessonPlan() {
    const lesson = activeLesson();
    if (!lesson) throw new Error("No Play Along lesson is available.");
    if (!lessonPlans.has(lesson.id)) lessonPlans.set(lesson.id, await arrangeChordLesson(lesson));
    plan = lessonPlans.get(lesson.id);
  }

  async function localProject(id) {
    return practiceTools.loadProject(id);
  }

  async function trackFromLocalProject(project) {
    const timeline = project.timeline || {};
    const chords = Array.isArray(timeline.chords) ? timeline.chords : [];
    if (!chords.length || !Array.isArray(timeline.barStartsMs) || !timeline.barStartsMs.length) throw new Error(`${project.title} still needs chord and timing review.`);
    const file = await practiceTools.readAudio(project.audio?.opfsPath || `${project.id}.audio`).catch(() => null);
    if (!file) throw new Error("The local recording is missing. Return to Songs and relink the original file with the same fingerprint.");
    localAudioUrl = URL.createObjectURL(file);
    const timelineChords = chords.map((chord, index) => ({ ...chord, bar: Number(chord.bar || index + 1), startFraction: Number(chord.startFraction || 0) }));
    const chartBars = timeline.barStartsMs.map((_start, index) => {
      const symbols = timelineChords.filter((chord) => chord.bar === index + 1).sort((left, right) => left.startFraction - right.startFraction).map((chord) => chord.symbol || "N.C.");
      return symbols.length ? symbols.join(" ") : "N.C.";
    });
    return {
      id: project.id, projectId: project.id, title: project.title, performer: "On-device recording", key: timeline.key || "G", keyMode: timeline.keyMode || "major", meter: timeline.meter || "4/4", tempo: Number(timeline.tempo || 100),
      durationMs: Number(project.audio.durationMs), barStartsMs: timeline.barStartsMs.map(Number), beatTimesMs: (timeline.beatTimesMs || []).map(Number),
      chart: `[Detected song] | ${chartBars.join(" | ")} |`, timelineChords, keyRegions: timeline.keyRegions || [], audioUrl: localAudioUrl, playAlongReady: true,
      routeOptions: [{ id: "movement", label: "Move the Bar", description: "Follow a practical E9 chord route generated from your reviewed chart." }], defaultRouteId: "movement",
      recordingCredit: "Stored and analyzed only on this device", authoredCountIn: Boolean(timeline.authoredCountIn), localProject: true
    };
  }

  function prepareTrackShell() {
    elements.title.textContent = track.title;
    elements.key.textContent = track.key ? `${track.key}${track.keyMode === "minor" ? " minor" : ""}` : "—";
    elements.keyJourney.textContent = `Key journey: ${practiceTools.keyJourneyLabel(track)}`;
    elements.meta.textContent = [track.performer, track.meter, track.tempo ? `${track.tempo} BPM` : ""].filter(Boolean).join(" · ");
    elements.attribution.replaceChildren(document.createTextNode(track.recordingCredit || ""));
    if (track.rightsUrl) {
      elements.attribution.append(document.createTextNode(" · "));
      const sourceLink = document.createElement("a");
      sourceLink.href = track.rightsUrl;
      sourceLink.target = "_blank";
      sourceLink.rel = "noreferrer";
      sourceLink.textContent = "Source";
      elements.attribution.append(sourceLink);
    }
    if (track.licenseUrl) {
      elements.attribution.append(document.createTextNode(" · "));
      const licenseLink = document.createElement("a");
      licenseLink.href = track.licenseUrl;
      licenseLink.target = "_blank";
      licenseLink.rel = "noreferrer";
      licenseLink.textContent = track.license || "License";
      elements.attribution.append(licenseLink);
    }
    transport = global.usePracticeTransport({ audio, track });
    transport.load(track.audioUrl, track);
    transport.setVolume(Number(elements.volume.value));
    transport.setRate(Number(elements.speed.value));
    audio.addEventListener("loadedmetadata", () => { elements.scrub.max = String(audio.duration); }, { once: true });
  }

  async function initialize() {
    if (!songTools || !practiceTools || !global.usePracticeTransport) throw new Error("The song timeline could not load.");
    session = await fetch("/api/session", { headers: accessHeaders() }).then((response) => response.json());
    const catalogRequest = fetch("/api/song-practice/catalog", { headers: accessHeaders() });
    if (projectId.startsWith("local-")) await configurePlayAlongCopedent();
    const response = await catalogRequest;
    const catalog = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(catalog.error || "The guided song catalog could not load.");
    track = (catalog.tracks || []).find((item) => (item.projectId || item.id) === projectId);
    if (!track && projectId.startsWith("local-")) {
      const local = await localProject(projectId);
      if (!local) throw new Error("That device-only track is no longer stored in this browser.");
      track = await trackFromLocalProject(local);
    }
    if (!track || track.playAlongReady !== true) {
      throw new Error(track?.availabilityReason || "That guided song is still in recording and synchronization review.");
    }
    chart = songTools.parseSongChart(track.chart, { mode: "letter", key: track.key, meter: track.meter });
    if (chart.errors.length) throw new Error(chart.errors.join(" "));
    prepareTrackShell();
    practiceSession = { ...practiceTools.sessionDefaults(projectId), ...(await practiceTools.loadSession(projectId) || {}) };
    if (practiceSession.lastPositionMs >= track.durationMs - 1000) practiceSession.lastPositionMs = 0;
    elements.speed.value = String(practiceSession.speed || 1);
    elements.volume.value = String(Number.isFinite(Number(practiceSession.volume)) ? practiceSession.volume : 0.9);
    elements.countIn.checked = Boolean(practiceSession.countIn);
    elements.metronome.checked = Boolean(practiceSession.metronome);
    elements.chordDisplay.textContent = practiceSession.chordDisplay === "nns" ? "Chords" : "NNS";
    elements.chordDisplay.setAttribute("aria-pressed", String(practiceSession.chordDisplay === "nns"));
    practiceMode = ["preview", "loop", "full", "less"].includes(practiceSession.mode) ? practiceSession.mode : "full";
    assistanceReduced = practiceMode === "less";
    transport.setRate(elements.speed.value); transport.setVolume(elements.volume.value); transport.setCountIn(elements.countIn.checked); transport.setMetronome(elements.metronome.checked);
    if (practiceSession.loopStartBar && practiceSession.loopEndBar) { loopRange = practiceTools.barsToLoopRange(track, practiceSession.loopStartBar, practiceSession.loopEndBar); }
    elements.loop.checked = practiceMode === "loop" && Boolean(loopRange);
    transport.setLoop(loopRange, elements.loop.checked);
    try {
      await arrangeMelodyLessons();
    } catch (error) {
      global.console?.warn?.("Melody lessons are unavailable; chord foundation remains available.", error);
    }
    const routeOptions = Array.isArray(track.routeOptions) ? track.routeOptions : [];
    lessons = [];
    if (lessonPlans.has("follow-melody")) lessons.push({
      id: "follow-melody", kind: "melody", label: "Follow the Melody", description: "Amazing Tablature keeps the exact reviewed melody as the highest voice.",
      objective: "Keep the melody as the highest note."
    });
    routeOptions.forEach((routeOption) => lessons.push({
      id: `chord-${routeOption.id}`, kind: "chord", routeId: routeOption.id,
      label: routeOption.id === "movement" ? "Chord Foundation · Move the Bar" : routeOption.id === "same-fret" ? "Chord Foundation · Stay Near Fret 3" : `Chord Foundation · ${routeOption.label}`,
      description: routeOption.description || "Practice the chord progression as accompaniment.",
      objective: routeOption.id === "same-fret"
        ? "Accompany the chords near fret 3; the top note is not necessarily the melody."
        : "Accompany the chords through common pockets; the top note is not necessarily the melody."
    }));
    if (lessonPlans.has("full-chord-melody")) lessons.push({
      id: "full-chord-melody", kind: "melody", label: "Full Chord Melody · Advanced",
      description: "Play each reviewed melody event with a validated three-voice position.", objective: "Keep the complete melody on top of three-voice harmony."
    });
    selectedLessonId = lessonPlans.has("follow-melody")
      ? "follow-melody"
      : `chord-${track.defaultRouteId || routeOptions[0]?.id || "movement"}`;
    elements.route.replaceChildren(...lessons.map((lesson) => {
      const option = document.createElement("option");
      option.value = lesson.id;
      option.textContent = lesson.label;
      return option;
    }));
    elements.route.value = selectedLessonId;
    elements.route.parentElement.hidden = lessons.length < 2;
    updateLessonDescription();
    await loadActiveLessonPlan();
    renderSongMap();
    updateModeButtons();
    setPlayerReady(true);
    transport.seek(practiceSession.lastPositionMs || 0);
    renderState(practiceSession.lastPositionMs || 0, true);
    frame = requestAnimationFrame(tick);
  }

  elements.toggle.addEventListener("click", async () => { if (audio.paused && !transport.pendingCountIn) await transport.play(); else transport.pause(); });
  elements.restart.addEventListener("click", () => { transport.pause(); transport.seek(0); renderState(0, true); queueSessionSave(); });
  elements.scrub.addEventListener("input", () => { transport.seek(Number(elements.scrub.value) * 1000); renderState(audio.currentTime * 1000, true); queueSessionSave(); });
  elements.speed.addEventListener("change", () => { transport.setRate(elements.speed.value); queueSessionSave(); });
  elements.route.addEventListener("change", async () => {
    transport.pause();
    selectedLessonId = elements.route.value;
    updateLessonDescription();
    elements.route.disabled = true;
    try {
      await loadActiveLessonPlan();
      renderedState = "";
      renderState(audio.currentTime * 1000, true);
      renderSongMap();
    } catch (error) {
      showError(error.message || "That Play Along lesson could not be prepared.");
    } finally {
      elements.route.disabled = false;
    }
  });
  elements.volume.addEventListener("input", () => { transport.setVolume(elements.volume.value); queueSessionSave(); });
  elements.countIn.addEventListener("change", () => { transport.setCountIn(elements.countIn.checked); queueSessionSave(); });
  elements.metronome.addEventListener("change", () => { transport.setMetronome(elements.metronome.checked); queueSessionSave(); });
  elements.loop.addEventListener("change", () => {
    if (elements.loop.checked) { ensureLoopRange(); practiceMode = "loop"; }
    else if (practiceMode === "loop") practiceMode = "full";
    updateModeButtons(); renderSongMap(); queueSessionSave();
  });
  elements.chordDisplay.addEventListener("click", () => {
    const nns = practiceSession.chordDisplay !== "nns";
    practiceSession.chordDisplay = nns ? "nns" : "letters";
    elements.chordDisplay.textContent = nns ? "Chords" : "NNS";
    elements.chordDisplay.setAttribute("aria-pressed", String(nns));
    renderedState = ""; renderState(audio.currentTime * 1000, true); renderSongMap(); queueSessionSave();
  });
  elements.openSongMap.addEventListener("click", () => { renderSongMap(); elements.songMapDialog.showModal(); });
  elements.closeSongMap.addEventListener("click", () => elements.songMapDialog.close());
  elements.songMapLoop.addEventListener("click", () => { loopSelection = []; elements.songMapLoop.dataset.selecting = "true"; elements.songMapLoop.textContent = "Choose start bar"; });
  document.querySelector("#previous-grip").addEventListener("click", () => stepGrip(-1));
  document.querySelector("#next-grip-step").addEventListener("click", () => stepGrip(1));
  elements.checkpoints.forEach((button) => button.addEventListener("click", () => {
    const value = button.dataset.checkpoint;
    transport.cancelPending(); practiceMode = value;
    if (value === "preview") { transport.pause(); transport.seek(Number(plan?.events?.[0]?.startMs || track?.barStartsMs?.[0] || 0)); assistanceReduced = false; }
    else if (value === "loop") { ensureLoopRange(); assistanceReduced = false; transport.seek(loopRange.startMs); }
    else if (value === "less") assistanceReduced = true;
    else assistanceReduced = false;
    updateModeButtons(); renderSongMap(); queueSessionSave();
    renderedState = "";
    renderState(audio.currentTime * 1000, true);
  }));

  global.addEventListener("beforeunload", () => { queueSessionSave(true); transport?.destroy(); if (localAudioUrl) URL.revokeObjectURL(localAudioUrl); });

  showLoadingState();
  initialize().catch((error) => showError(error.message || "Play Along could not start."));
})(window);
