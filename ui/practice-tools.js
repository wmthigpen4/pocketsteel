(function (global) {
  "use strict";

  const DB_NAME = "steel-guitar-rag-practice";
  const DB_VERSION = 2;
  const PROJECT_STORE = "practiceProjects";
  const SESSION_STORE = "practiceSessions";
  const AUDIO_DIR = "practice-audio";
  const SESSION_SCHEMA_VERSION = 1;
  const CHART_REFERENCE_PROVIDER_VERSION = 1;
  const NOTE_PCS = {
    C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4,
    F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9,
    "A#": 10, Bb: 10, B: 11
  };
  const NASHVILLE_DEGREES = ["1", "b2", "2", "b3", "3", "4", "#4", "5", "b6", "6", "b7", "7"];

  function requestResult(request, fallback) {
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error(fallback));
    });
  }

  function openDatabase(indexedDb = global.indexedDB) {
    return new Promise((resolve, reject) => {
      if (!indexedDb) return reject(new Error("IndexedDB is unavailable in this browser."));
      const request = indexedDb.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const database = request.result;
        if (!database.objectStoreNames.contains(PROJECT_STORE)) database.createObjectStore(PROJECT_STORE, { keyPath: "id" });
        if (!database.objectStoreNames.contains(SESSION_STORE)) database.createObjectStore(SESSION_STORE, { keyPath: "projectId" });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Local song storage could not open."));
    });
  }

  async function withStore(storeName, mode, callback) {
    const database = await openDatabase();
    try {
      const transaction = database.transaction(storeName, mode);
      return await requestResult(callback(transaction.objectStore(storeName)), "Local song storage failed.");
    } finally {
      database.close();
    }
  }

  function listProjects() {
    return withStore(PROJECT_STORE, "readonly", (store) => store.getAll()).then((projects) =>
      (projects || []).sort((left, right) => String(right.updatedAt || "").localeCompare(String(left.updatedAt || "")))
    );
  }

  function loadProject(id) {
    return withStore(PROJECT_STORE, "readonly", (store) => store.get(id));
  }

  function saveProject(project) {
    return withStore(PROJECT_STORE, "readwrite", (store) => store.put(project));
  }

  async function deleteProject(project) {
    if (project?.audio?.kind === "local") {
      try {
        const directory = await audioDirectory();
        await directory.removeEntry(project.audio.opfsPath || `${project.id}.audio`);
      } catch (_error) {
        // The browser may already have evicted the local audio file.
      }
    }
    const database = await openDatabase();
    try {
      await new Promise((resolve, reject) => {
        const transaction = database.transaction([PROJECT_STORE, SESSION_STORE], "readwrite");
        transaction.objectStore(PROJECT_STORE).delete(project.id);
        transaction.objectStore(SESSION_STORE).delete(project.id);
        transaction.oncomplete = resolve;
        transaction.onerror = () => reject(transaction.error || new Error("The song could not be removed."));
      });
    } finally {
      database.close();
    }
  }

  function loadSession(projectId) {
    return withStore(SESSION_STORE, "readonly", (store) => store.get(projectId));
  }

  function saveSession(session) {
    return withStore(SESSION_STORE, "readwrite", (store) => store.put(session));
  }

  function sessionDefaults(projectId) {
    return {
      schemaVersion: SESSION_SCHEMA_VERSION,
      projectId,
      mode: "full",
      speed: 1,
      volume: 0.9,
      loopStartBar: null,
      loopEndBar: null,
      countIn: false,
      metronome: false,
      chordDisplay: "letters",
      lastPositionMs: 0,
      updatedAt: new Date().toISOString()
    };
  }

  async function audioDirectory() {
    if (!global.navigator?.storage?.getDirectory) throw new Error("This browser cannot keep audio on this device yet.");
    const root = await global.navigator.storage.getDirectory();
    return root.getDirectoryHandle(AUDIO_DIR, { create: true });
  }

  async function writeAudio(id, file, signal) {
    const directory = await audioDirectory();
    const path = `${id}.audio`;
    const handle = await directory.getFileHandle(path, { create: true });
    const writer = await handle.createWritable();
    try {
      await file.stream().pipeTo(writer, signal ? { signal } : undefined);
    } catch (error) {
      try { await directory.removeEntry(path); } catch (_removeError) { /* ignore partial cleanup */ }
      throw error;
    }
    return path;
  }

  async function readAudio(path) {
    const directory = await audioDirectory();
    const handle = await directory.getFileHandle(path);
    return handle.getFile();
  }

  async function removeAudio(path) {
    const directory = await audioDirectory();
    try { await directory.removeEntry(path); } catch (error) { if (error?.name !== "NotFoundError") throw error; }
  }

  async function hasAudio(path) {
    try { await readAudio(path); return true; } catch (_error) { return false; }
  }

  async function fingerprintFile(file) {
    const chunkSize = Math.min(1024 * 1024, file.size);
    const first = new Uint8Array(await file.slice(0, chunkSize).arrayBuffer());
    const last = new Uint8Array(await file.slice(Math.max(0, file.size - chunkSize)).arrayBuffer());
    // The fingerprint identifies the recording, not the filename. Renaming an
    // otherwise identical file must still find the existing reviewed project.
    const metadata = new TextEncoder().encode(`${file.size}`);
    const combined = new Uint8Array(metadata.length + first.length + last.length);
    combined.set(metadata, 0);
    combined.set(first, metadata.length);
    combined.set(last, metadata.length + first.length);
    const digest = await global.crypto.subtle.digest("SHA-256", combined);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  async function findProjectByFingerprint(fingerprint) {
    const projects = await listProjects();
    return projects.find((project) => project?.audio?.fingerprint === fingerprint) || null;
  }

  function nashvilleSuffix(suffix) {
    return String(suffix || "").replaceAll("13", "¹³").replaceAll("11", "¹¹").replaceAll("9", "⁹").replaceAll("7", "⁷");
  }

  function musicalAccidentals(value) {
    return String(value || "").replace(/^b(?=[1-7])/, "♭").replace(/^#(?=[1-7])/, "♯");
  }

  function chordForDisplay(symbol, key, display = "letters") {
    const chord = String(symbol || "N.C.").trim();
    if (/^(?:N\.?C\.?|NO\s+CHORD|REST)$/i.test(chord)) return "No chord";
    if (display !== "nns") return chord;
    if (/^[b#♭♯]?[1-7]/.test(chord)) return musicalAccidentals(nashvilleSuffix(chord));
    const chordMatch = /^([A-G])([#b]?)(.*)$/.exec(chord);
    const keyMatch = /^([A-G])([#b]?)/.exec(String(key || "C"));
    if (!chordMatch || !keyMatch) return chord;
    const chordPitch = NOTE_PCS[`${chordMatch[1]}${chordMatch[2]}`];
    const keyPitch = NOTE_PCS[`${keyMatch[1]}${keyMatch[2]}`];
    if (!Number.isInteger(chordPitch) || !Number.isInteger(keyPitch)) return chord;
    return `${musicalAccidentals(NASHVILLE_DEGREES[(chordPitch - keyPitch + 12) % 12])}${nashvilleSuffix(chordMatch[3])}`;
  }

  function normalizeKeyRegions(regions, barCount, fallbackKey = "C", fallbackMode = "major") {
    const count = Math.max(1, Number(barCount || 1));
    const clean = (Array.isArray(regions) ? regions : []).map((region) => ({
      startBar: Math.max(1, Math.min(count, Math.round(Number(region.startBar) || 1))),
      key: Object.hasOwn(NOTE_PCS, region.key) ? region.key : fallbackKey,
      keyMode: region.keyMode === "minor" ? "minor" : "major",
      confidence: Number.isFinite(Number(region.confidence)) ? Number(region.confidence) : 1,
      source: region.source === "manual" ? "manual" : "detected"
    })).sort((left, right) => left.startBar - right.startBar).filter((region, index, items) => !index || region.startBar !== items[index - 1].startBar);
    if (!clean.length || clean[0].startBar !== 1) clean.unshift({ startBar: 1, key: fallbackKey, keyMode: fallbackMode === "minor" ? "minor" : "major", confidence: 1, source: "detected" });
    return clean.map((region, index) => ({ ...region, endBar: (clean[index + 1]?.startBar || count + 1) - 1 }));
  }

  function keyRegionForBar(timeline, bar) {
    const count = timeline?.barStartsMs?.length || Math.max(1, Number(bar || 1));
    const regions = normalizeKeyRegions(timeline?.keyRegions, count, timeline?.key || "C", timeline?.keyMode || "major");
    return regions.find((region) => Number(bar) >= region.startBar && Number(bar) <= region.endBar) || regions[0];
  }

  function keyForBar(timeline, bar) {
    const region = keyRegionForBar(timeline, bar);
    return { key: region.key, keyMode: region.keyMode, region };
  }

  function keyJourneyLabel(timeline) {
    const count = timeline?.barStartsMs?.length || 1;
    return normalizeKeyRegions(timeline?.keyRegions, count, timeline?.key || "C", timeline?.keyMode || "major")
      .map((region) => `${region.key} ${region.keyMode}`)
      .join(" → ");
  }

  function chartReferenceProvider(adapter) {
    if (!adapter || typeof adapter.lookup !== "function" || !String(adapter.id || "").trim()) {
      throw new Error("A chart reference provider needs an id and a permitted lookup function.");
    }
    return Object.freeze({
      schemaVersion: CHART_REFERENCE_PROVIDER_VERSION,
      id: String(adapter.id),
      attribution: String(adapter.attribution || adapter.id),
      lookup: adapter.lookup
    });
  }

  function controlLabelForDisplay(value) {
    const label = String(value || "").trim().replace(
      /\s*\((?:p(?:edal)?\s*\d+|[lr]k[lrv]\d*(?:\.(?:half|full))?)\)/gi,
      ""
    ).replace(/\s{2,}/g, " ").trim();
    const standardPedal = /^([abc])(?:\s+pedal)?$/i.exec(label);
    return standardPedal ? standardPedal[1].toUpperCase() : label;
  }

  function controlLabelsForDisplay(values) {
    return Array.from(new Set((Array.isArray(values) ? values : []).map(controlLabelForDisplay).filter(Boolean)));
  }

  function meterBeats(track) {
    return Math.max(1, Number(String(track?.meter || "4/4").split("/")[0]) || 4);
  }

  function projectBars(track, plan) {
    const starts = Array.isArray(track?.barStartsMs) ? track.barStartsMs : [];
    const events = Array.isArray(plan?.events) ? plan.events : [];
    return starts.map((startMs, index) => {
      const endMs = Number(starts[index + 1] ?? track.durationMs);
      const chords = events.filter((event) => Number(event.startMs) < endMs && Number(event.endMs) > startMs).map((event) => ({
        id: event.id,
        symbol: event.chord || "N.C.",
        startFraction: Math.max(0, (Number(event.startMs) - startMs) / Math.max(1, endMs - startMs)),
        durationFraction: Math.min(1, (Math.min(endMs, Number(event.endMs)) - Math.max(startMs, Number(event.startMs))) / Math.max(1, endMs - startMs))
      }));
      const firstPosition = events.find((event) => Number(event.startMs) < endMs && Number(event.endMs) > startMs)?.position;
      const firstControls = firstPosition?.controlLabels || firstPosition?.controls || [];
      return {
        barNumber: index + 1,
        startTick: index * meterBeats(track) * 960,
        endTick: (index + 1) * meterBeats(track) * 960,
        startMs,
        endMs,
        chords,
        firstMove: firstPosition ? {
          fret: firstPosition.fret,
          strings: firstPosition.strings || [],
          controls: controlLabelsForDisplay(firstControls)
        } : null
      };
    });
  }

  function barsToLoopRange(track, startBar, endBar) {
    const starts = Array.isArray(track?.barStartsMs) ? track.barStartsMs : [];
    const finalBar = Math.max(1, starts.length);
    const boundedStart = Math.max(1, Math.min(finalBar, Math.round(Number(startBar) || 1)));
    const boundedEnd = Math.max(boundedStart, Math.min(finalBar, Math.round(Number(endBar) || boundedStart)));
    return {
      startBar: boundedStart,
      endBar: boundedEnd,
      startMs: Number(starts[boundedStart - 1] || 0),
      endMs: Number(starts[boundedEnd] ?? track.durationMs)
    };
  }

  function countBasedLoopRange(track, currentMs, barCount = 4) {
    const starts = Array.isArray(track?.barStartsMs) ? track.barStartsMs : [];
    const current = Math.max(0, starts.findLastIndex((start) => Number(start) <= Number(currentMs || 0)));
    const count = Math.max(1, Math.round(Number(barCount) || 1));
    const groupStart = Math.floor(current / count) * count;
    return barsToLoopRange(track, groupStart + 1, Math.min(starts.length, groupStart + count));
  }

  function beatTimesForTrack(track) {
    if (Array.isArray(track?.beatTimesMs) && track.beatTimesMs.length) return track.beatTimesMs;
    const beatsPerBar = meterBeats(track);
    const starts = Array.isArray(track?.barStartsMs) ? track.barStartsMs : [];
    return starts.flatMap((start, barIndex) => {
      const end = Number(starts[barIndex + 1] ?? track.durationMs);
      return Array.from({ length: beatsPerBar }, (_item, beatIndex) => Math.round(start + ((end - start) * beatIndex / beatsPerBar)));
    });
  }

  const api = {
    DB_NAME, DB_VERSION, PROJECT_STORE, SESSION_STORE, SESSION_SCHEMA_VERSION, CHART_REFERENCE_PROVIDER_VERSION,
    openDatabase, listProjects, loadProject, saveProject, deleteProject,
    loadSession, saveSession, sessionDefaults,
    writeAudio, readAudio, removeAudio, hasAudio, fingerprintFile, findProjectByFingerprint,
    chordForDisplay, normalizeKeyRegions, keyRegionForBar, keyForBar, keyJourneyLabel, chartReferenceProvider, controlLabelForDisplay, controlLabelsForDisplay,
    projectBars, barsToLoopRange, countBasedLoopRange, beatTimesForTrack, meterBeats
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  global.STEEL_RAG_PRACTICE = api;
})(typeof window !== "undefined" ? window : globalThis);
