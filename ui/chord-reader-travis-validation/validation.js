(function travisValidation() {
  "use strict";

  const DATA_URL = "./local-data/proof.json";
  const FEEDBACK_URL = "/api/travis-validation/feedback";
  const REMOTE_MODE = !["127.0.0.1", "localhost"].includes(
    window.location.hostname,
  );
  const STORAGE_PREFIX = "chord-reader-travis-validation-v1";
  const STORAGE_SESSION =
    new URLSearchParams(window.location.search).get("session") || "default";
  const byId = (id) => document.getElementById(id);
  const KEY_NAMES = [
    "C",
    "Db",
    "D",
    "Eb",
    "E",
    "F",
    "F#",
    "G",
    "Ab",
    "A",
    "Bb",
    "B",
  ];
  const NOTE_PITCH_CLASSES = {
    C: 0,
    "B#": 0,
    "C#": 1,
    Db: 1,
    D: 2,
    "D#": 3,
    Eb: 3,
    E: 4,
    Fb: 4,
    "E#": 5,
    F: 5,
    "F#": 6,
    Gb: 6,
    G: 7,
    "G#": 8,
    Ab: 8,
    A: 9,
    "A#": 10,
    Bb: 10,
    B: 11,
    Cb: 11,
  };
  const NNS_INTERVALS = [
    "1",
    "b2",
    "2",
    "b3",
    "3",
    "4",
    "#4",
    "5",
    "b6",
    "6",
    "b7",
    "7",
  ];
  const pct = (value) => `${(Number(value || 0) * 100).toFixed(0)}%`;
  const clock = (seconds) => {
    const value = Math.max(0, Number(seconds) || 0);
    const minutes = Math.floor(value / 60);
    return `${minutes}:${String(Math.floor(value % 60)).padStart(2, "0")}`;
  };

  let proof;
  let selected;
  let feedback;
  let activeSegment = -1;
  let activeFilter = "all";
  let currentDisplayItems = [];
  let currentBeatGrid = null;
  let playbackFrame = 0;
  let clickTrackEnabled = false;
  let clickAudioContext = null;
  let lastClickedBeat = -1;
  const selectedBoxKeys = new Set();
  let remoteSaveSequence = Promise.resolve();
  const remoteSaveTimers = new Map();
  const clientVersions = new Map();

  function parseChord(symbol) {
    const value = String(symbol || "").trim();
    if (!value || /^(N\.?C\.?|N)$/i.test(value)) return null;
    const match = value.match(/^([A-G](?:#|b)?)([^/]*)(?:\/([A-G](?:#|b)?))?$/);
    if (!match) return null;
    return { root: match[1], quality: match[2] || "", bass: match[3] || "" };
  }

  function chordQuality(quality) {
    if (/^(m|min)(?!aj)/i.test(quality)) return "minor";
    if (/^(dim|°)/i.test(quality)) return "diminished";
    return "major";
  }

  function inferKey(track) {
    const degreeWeights = [
      2.7, -0.6, 0.8, -0.5, 0.7, 1.25, -0.7, 1.8, -0.5, 0.65, -0.4, 0.35,
    ];
    const expectedQualities = [
      "major",
      null,
      "minor",
      null,
      "minor",
      "major",
      null,
      "major",
      null,
      "minor",
      null,
      "diminished",
    ];
    let bestPitchClass = 0;
    let bestScore = -Infinity;
    KEY_NAMES.forEach((_name, tonic) => {
      let score = 0;
      (track.summary.dominantChords || []).forEach((entry) => {
        const chord = parseChord(entry.symbol);
        if (!chord) return;
        const root = NOTE_PITCH_CLASSES[chord.root];
        if (root === undefined) return;
        const interval = (root - tonic + 12) % 12;
        const expected = expectedQualities[interval];
        const qualityBonus = expected
          ? chordQuality(chord.quality) === expected
            ? 0.9
            : -0.25
          : 0;
        score +=
          Number(entry.seconds || 0) * (degreeWeights[interval] + qualityBonus);
      });
      if (score > bestScore) {
        bestScore = score;
        bestPitchClass = tonic;
      }
    });
    return KEY_NAMES[bestPitchClass];
  }

  function nnsQuality(quality) {
    if (!quality) return "";
    if (/^maj$/i.test(quality)) return "";
    return quality
      .replace(/^(min)(?!aj)/i, "m")
      .replace(/^dim/i, "°")
      .replace(/^aug/i, "+")
      .replace(/^maj7$/i, "Δ⁷")
      .replace(/13/g, "¹³")
      .replace(/11/g, "¹¹")
      .replace(/9/g, "⁹")
      .replace(/7/g, "⁷")
      .replace(/6/g, "⁶")
      .replace(/4/g, "⁴")
      .replace(/2/g, "²");
  }

  function chordToNns(symbol, key) {
    const chord = parseChord(symbol);
    if (!chord)
      return /^(N\.?C\.?|N)$/i.test(String(symbol || "").trim())
        ? "N.C."
        : symbol || "—";
    const tonic = NOTE_PITCH_CLASSES[key];
    const root = NOTE_PITCH_CLASSES[chord.root];
    if (tonic === undefined || root === undefined) return symbol;
    const degree = NNS_INTERVALS[(root - tonic + 12) % 12];
    const bassPitch = NOTE_PITCH_CLASSES[chord.bass];
    const bass =
      bassPitch === undefined
        ? ""
        : `/${NNS_INTERVALS[(bassPitch - tonic + 12) % 12]}`;
    return `${degree}${nnsQuality(chord.quality)}${bass}`;
  }

  function chordSymbol(segment) {
    return segment?.productLabel || segment?.label || "N.C.";
  }

  function displayChord(segment) {
    const symbol = chordSymbol(segment);
    const record = trackFeedback();
    return record.displayMode === "nns"
      ? chordToNns(symbol, record.songKey)
      : symbol;
  }

  function storageKey() {
    const hashes = Object.values(proof.modelSha256 || {}).join(":");
    return `${STORAGE_PREFIX}:${STORAGE_SESSION}:${hashes.slice(0, 96)}`;
  }

  function blankFeedback() {
    return {
      schemaVersion: "chord_reader_travis_feedback_v1",
      title: "Chord Reader — Travis Validation",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      modelSha256: proof.modelSha256,
      tracks: {},
    };
  }

  async function loadFeedback() {
    if (REMOTE_MODE) {
      const response = await fetch(FEEDBACK_URL, {
        credentials: "same-origin",
        cache: "no-store",
      });
      if (!response.ok)
        throw new Error(
          (await response.json()).error || "Protected feedback could not load.",
        );
      const stored = await response.json();
      return { ...blankFeedback(), ...stored, tracks: stored.tracks || {} };
    }
    try {
      return JSON.parse(localStorage.getItem(storageKey())) || blankFeedback();
    } catch (_error) {
      return blankFeedback();
    }
  }

  function trackFeedback(track = selected) {
    const id = track.track.id;
    if (!feedback.tracks[id]) {
      feedback.tracks[id] = {
        trackId: id,
        title: track.track.title,
        audioSha256: track.track.audioSha256,
        songNotes: "",
        suggestedKey: inferKey(track),
        songKey: inferKey(track),
        keySource: "suggested",
        displayMode: "chords",
        songMeter: track.track.rhythm?.meter || "4/4",
        meterSource: "detected",
        tempoBpm: Math.round(Number(track.track.rhythm?.tempoBpm) || 100),
        timingOffsetSeconds: Number(track.track.rhythm?.gridOffsetSeconds || 0),
        downbeatOffsetBeats: Number(
          track.track.rhythm?.phase?.downbeatOffsetBeats || 0,
        ),
        downbeatPhaseSource:
          track.track.rhythm?.phase?.status === "anchored"
            ? "anchored"
            : "unresolved",
        reviewComplete: false,
        reviewedAt: null,
        segments: {},
        boxMerges: [],
      };
    }
    const record = feedback.tracks[id];
    if (typeof record.reviewComplete !== "boolean")
      record.reviewComplete = false;
    if (!("reviewedAt" in record)) record.reviewedAt = null;
    if (!record.suggestedKey) record.suggestedKey = inferKey(track);
    if (!record.songKey) record.songKey = record.suggestedKey;
    if (!record.keySource) record.keySource = "suggested";
    if (!record.displayMode) record.displayMode = "chords";
    if (!record.songMeter)
      record.songMeter = track.track.rhythm?.meter || "4/4";
    if (!record.meterSource) record.meterSource = "detected";
    if (!Number.isFinite(Number(record.tempoBpm)))
      record.tempoBpm = Math.round(Number(track.track.rhythm?.tempoBpm) || 100);
    if (!Number.isFinite(Number(record.timingOffsetSeconds)))
      record.timingOffsetSeconds = Number(
        track.track.rhythm?.gridOffsetSeconds || 0,
      );
    if (!Number.isSafeInteger(Number(record.downbeatOffsetBeats)))
      record.downbeatOffsetBeats = Number(
        track.track.rhythm?.phase?.downbeatOffsetBeats || 0,
      );
    record.downbeatOffsetBeats = ChordPhaseAnchor.mod(
      Number(record.downbeatOffsetBeats),
      Number(record.songMeter.split("/")[0]) || 4,
    );
    if (!record.downbeatPhaseSource)
      record.downbeatPhaseSource =
        track.track.rhythm?.phase?.status === "anchored"
          ? "anchored"
          : "unresolved";
    if (!Array.isArray(record.boxMerges)) record.boxMerges = [];
    Object.values(record.segments).forEach((segment) => {
      if (segment.status === "unreviewed") segment.status = "assumed_correct";
      if (segment.status === "confirmed") segment.status = "assumed_correct";
    });
    return record;
  }

  function saveFeedback() {
    feedback.updatedAt = new Date().toISOString();
    if (REMOTE_MODE) {
      scheduleRemoteSave(trackFeedback().trackId);
    } else {
      localStorage.setItem(storageKey(), JSON.stringify(feedback));
      byId("save-status").textContent =
        `Saved locally at ${new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}.`;
    }
    renderProgress();
  }

  function scheduleRemoteSave(trackId) {
    const version = (clientVersions.get(trackId) || 0) + 1;
    clientVersions.set(trackId, version);
    clearTimeout(remoteSaveTimers.get(trackId));
    byId("save-status").textContent = "Saving securely…";
    remoteSaveTimers.set(
      trackId,
      setTimeout(() => {
        remoteSaveTimers.delete(trackId);
        remoteSaveSequence = remoteSaveSequence
          .then(() => saveRemoteTrack(trackId, version))
          .catch((error) => {
            byId("save-status").textContent = `Save failed: ${error.message}`;
          });
      }, 300),
    );
  }

  async function saveRemoteTrack(trackId, version) {
    const record = feedback.tracks[trackId];
    if (!record) return;
    const response = await fetch(
      `${FEEDBACK_URL}/${encodeURIComponent(trackId)}`,
      {
        method: "PUT",
        credentials: "same-origin",
        keepalive: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(record),
      },
    );
    const result = await response.json();
    if (!response.ok)
      throw new Error(result.error || "Protected feedback did not save.");
    record.serverRevision = result.revision;
    record.serverUpdatedAt = result.updatedAt;
    if (clientVersions.get(trackId) !== version) {
      scheduleRemoteSave(trackId);
      return;
    }
    byId("save-status").textContent =
      `Saved securely at ${new Date(result.updatedAt).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}.`;
  }

  function isLeadIn(segment, index) {
    return (
      index === 0 &&
      Number(segment.start) === 0 &&
      /^(N\.?C\.?|N)$/i.test(chordSymbol(segment))
    );
  }

  function isLowConfidenceTransient(segment) {
    return (
      Number(segment.end) - Number(segment.start) <= 0.25 &&
      Number(segment.confidence) < 0.5
    );
  }

  function itemConfidence(sourceIndices) {
    let weighted = 0;
    let duration = 0;
    sourceIndices.forEach((index) => {
      const segment = selected.prediction.segments[index];
      const seconds = Math.max(
        0.001,
        Number(segment.end) - Number(segment.start),
      );
      weighted += Number(segment.confidence) * seconds;
      duration += seconds;
    });
    return duration ? weighted / duration : 0;
  }

  function segmentIndexAt(seconds) {
    const index = selected.prediction.segments.findIndex(
      (segment) =>
        seconds >= Number(segment.start) && seconds < Number(segment.end),
    );
    return index >= 0 ? index : selected.prediction.segments.length - 1;
  }

  function barConfidence(sourceIndices, start, end) {
    let weighted = 0;
    let duration = 0;
    sourceIndices.forEach((index) => {
      const segment = selected.prediction.segments[index];
      const overlap = Math.max(
        0,
        Math.min(end, Number(segment.end)) -
          Math.max(start, Number(segment.start)),
      );
      weighted += Number(segment.confidence) * overlap;
      duration += overlap;
    });
    return duration ? weighted / duration : 0;
  }

  function strongestChordInWindow(sourceIndices, start, end) {
    const bySymbol = new Map();
    sourceIndices.forEach((index) => {
      const segment = selected.prediction.segments[index];
      const overlap = Math.max(
        0,
        Math.min(end, Number(segment.end)) -
          Math.max(start, Number(segment.start)),
      );
      if (!overlap) return;
      const symbol = chordSymbol(segment);
      const current = bySymbol.get(symbol) || {
        symbol,
        overlap: 0,
        weightedConfidence: 0,
      };
      current.overlap += overlap;
      current.weightedConfidence += overlap * Number(segment.confidence);
      bySymbol.set(symbol, current);
    });
    const winner = [...bySymbol.values()].sort(
      (left, right) =>
        right.weightedConfidence - left.weightedConfidence ||
        right.overlap - left.overlap,
    )[0];
    if (!winner) return null;
    return {
      ...winner,
      confidence: winner.weightedConfidence / winner.overlap,
      coverage: winner.overlap / Math.max(0.001, end - start),
    };
  }

  function chordDecisionForBar(sourceIndices, start, end) {
    const midpoint = start + (end - start) / 2;
    const full = strongestChordInWindow(sourceIndices, start, end);
    const first = strongestChordInWindow(sourceIndices, start, midpoint);
    const second = strongestChordInWindow(sourceIndices, midpoint, end);
    const supportedSplit =
      first &&
      second &&
      first.symbol !== second.symbol &&
      first.coverage >= 0.6 &&
      second.coverage >= 0.6 &&
      first.confidence >= 0.64 &&
      second.confidence >= 0.64;
    const possibleSplit =
      first &&
      second &&
      first.symbol !== second.symbol &&
      first.coverage >= 0.6 &&
      second.coverage >= 0.6 &&
      Math.max(first.confidence, second.confidence) >= 0.55 &&
      Math.min(first.confidence, second.confidence) >= 0.2;
    const rawSymbols = new Set(
      sourceIndices.map((index) =>
        chordSymbol(selected.prediction.segments[index]),
      ),
    );
    const chordSymbols = possibleSplit
      ? [first.symbol, second.symbol]
      : [full?.symbol || "N.C."];
    return {
      chordSymbols,
      splitSupported: Boolean(supportedSplit),
      splitUncertain: Boolean(possibleSplit && !supportedSplit),
      aggregationUnstable: rawSymbols.size > chordSymbols.length,
    };
  }

  function rhythmicDisplayItems() {
    currentBeatGrid = null;
    const rhythm = selected.track.rhythm;
    const record = trackFeedback();
    const offset = Number(record.timingOffsetSeconds || 0);
    const rawBeats = (rhythm?.beatTimesSeconds || [])
      .map((time) => Number(time) + offset)
      .filter((time) => time >= 0);
    if (rawBeats.length < 2) return null;
    const beatsPerBar = Number(record.songMeter.split("/")[0]) || 4;
    const completed = ChordPhaseAnchor.completeBeatGrid(
      rawBeats,
      Number(selected.track.durationSeconds),
    );
    const beats = completed.beats;
    const downbeats = ChordPhaseAnchor.downbeatTimes(
      beats,
      completed.prependedCount,
      record.downbeatOffsetBeats,
      beatsPerBar,
    );
    if (!downbeats.length) return null;
    const phaseIndex = ChordPhaseAnchor.mod(
      completed.prependedCount + Number(record.downbeatOffsetBeats),
      beatsPerBar,
    );
    const beatNumberAt = (time) => {
      const index = beats.indexOf(time);
      return ChordPhaseAnchor.mod(index - phaseIndex, beatsPerBar) + 1;
    };
    currentBeatGrid = {
      beats,
      beatNumbers: beats.map(beatNumberAt),
      prependedCount: completed.prependedCount,
      period: completed.period,
    };
    const meaningful = selected.prediction.segments.find((segment) => {
      const duration = Number(segment.end) - Number(segment.start);
      return (
        !/^(N\.?C\.?|N)$/iu.test(chordSymbol(segment)) &&
        duration >= Math.max(0.35, completed.period * 0.5) &&
        Number(segment.confidence) >= 0.2
      );
    });
    const musicStart = Number(meaningful?.start || 0);
    const firstBarStart =
      downbeats.find(
        (time) => time >= musicStart - completed.period * 0.25,
      ) || downbeats[0];
    const items = [];
    const pickupNeeded =
      firstBarStart - musicStart > completed.period * 0.25;
    const pickupStart = pickupNeeded
      ? [...beats]
          .reverse()
          .find((time) => time <= musicStart + completed.period * 0.15) ||
        musicStart
      : firstBarStart;
    const leadEnd = pickupNeeded ? pickupStart : firstBarStart;
    if (leadEnd > 0.1) {
      const leadIndex = segmentIndexAt(Math.max(0, leadEnd / 2));
      const segment = selected.prediction.segments[leadIndex];
      items.push({
        kind: "lead-in",
        sourceIndices: [leadIndex],
        boxNumbers: [],
        segment,
        start: 0,
        end: leadEnd,
        confidence: Number(segment.confidence),
      });
    }

    const windowItem = (kind, start, end, boxNumber = null) => {
      const sourceIndices = selected.prediction.segments
        .map((_segment, index) => index)
        .filter((index) => {
          const segment = selected.prediction.segments[index];
          return Number(segment.end) > start && Number(segment.start) < end;
        });
      if (!sourceIndices.length) sourceIndices.push(segmentIndexAt(start));
      const overlapByIndex = sourceIndices.map((index) => {
        const segment = selected.prediction.segments[index];
        return {
          index,
          overlap: Math.max(
            0,
            Math.min(end, Number(segment.end)) -
              Math.max(start, Number(segment.start)),
          ),
        };
      });
      const reviewIndex = overlapByIndex.sort(
        (left, right) => right.overlap - left.overlap,
      )[0].index;
      const beatTimes = beats.filter((time) => time >= start && time < end);
      return {
        kind,
        sourceIndices,
        boxNumbers: boxNumber === null ? [] : [boxNumber],
        segment: selected.prediction.segments[reviewIndex],
        reviewIndex,
        start,
        end,
        confidence: barConfidence(sourceIndices, start, end),
        beatTimes,
        beatNumbers: beatTimes.map(beatNumberAt),
        ...chordDecisionForBar(sourceIndices, start, end),
        isBar: kind === "box",
      };
    };

    if (pickupNeeded && firstBarStart - pickupStart > 0.15)
      items.push(windowItem("pickup", pickupStart, firstBarStart));

    const barStarts = downbeats.filter((time) => time >= firstBarStart - 0.001);
    barStarts.forEach((start, barIndex) => {
      const end = Math.min(
        Number(selected.track.durationSeconds),
        barStarts[barIndex + 1] || Number(selected.track.durationSeconds),
      );
      if (end - start < 0.2) return;
      items.push(windowItem("box", start, end, barIndex + 1));
    });
    return items;
  }

  function baseDisplayItems() {
    const rhythmic = rhythmicDisplayItems();
    if (rhythmic) return rhythmic;
    const items = [];
    let pendingTransientIndexes = [];
    let boxNumber = 0;
    selected.prediction.segments.forEach((segment, index) => {
      if (isLeadIn(segment, index)) {
        items.push({
          kind: "lead-in",
          sourceIndices: [index],
          boxNumbers: [],
          segment,
          start: Number(segment.start),
          end: Number(segment.end),
          confidence: Number(segment.confidence),
        });
        return;
      }
      if (isLowConfidenceTransient(segment)) {
        pendingTransientIndexes.push(index);
        return;
      }
      boxNumber += 1;
      const sourceIndices = [...pendingTransientIndexes, index];
      pendingTransientIndexes = [];
      items.push({
        kind: "box",
        sourceIndices,
        boxNumbers: [boxNumber],
        segment,
        reviewIndex: index,
        start: Number(selected.prediction.segments[sourceIndices[0]].start),
        end: Number(segment.end),
        confidence: itemConfidence(sourceIndices),
        autoGrouped: sourceIndices.length > 1,
      });
    });
    if (pendingTransientIndexes.length) {
      const previous = [...items].reverse().find((item) => item.kind === "box");
      if (previous) {
        previous.sourceIndices.push(...pendingTransientIndexes);
        previous.end = Number(
          selected.prediction.segments[pendingTransientIndexes.at(-1)].end,
        );
        previous.confidence = itemConfidence(previous.sourceIndices);
        previous.autoGrouped = true;
      }
    }
    return items;
  }

  function buildDisplayItems() {
    const baseItems = baseDisplayItems();
    const merges = [...trackFeedback().boxMerges].sort(
      (left, right) => left.startBox - right.startBox,
    );
    const items = [];
    for (let index = 0; index < baseItems.length; index += 1) {
      const item = baseItems[index];
      if (item.kind !== "box") {
        items.push(item);
        continue;
      }
      const merge = merges.find(
        (candidate) => candidate.startBox === item.boxNumbers[0],
      );
      if (!merge) {
        items.push(item);
        continue;
      }
      const grouped = [item];
      while (index + 1 < baseItems.length) {
        const next = baseItems[index + 1];
        if (next.kind !== "box") break;
        if (next.boxNumbers.at(-1) > merge.endBox) break;
        grouped.push(next);
        index += 1;
        if (next.boxNumbers.at(-1) === merge.endBox) break;
      }
      const sourceIndices = grouped.flatMap((entry) => entry.sourceIndices);
      const mergedSymbols = grouped
        .flatMap((entry) => entry.chordSymbols || [])
        .filter(
          (symbol, symbolIndex, symbols) =>
            symbolIndex === 0 || symbol !== symbols[symbolIndex - 1],
        );
      items.push({
        kind: "box",
        sourceIndices,
        boxNumbers: grouped.flatMap((entry) => entry.boxNumbers),
        segment: grouped[0].segment,
        reviewIndex: grouped[0].reviewIndex,
        start: grouped[0].start,
        end: grouped.at(-1).end,
        confidence: itemConfidence(sourceIndices),
        beatTimes: grouped.flatMap((entry) => entry.beatTimes || []),
        chordSymbols: mergedSymbols.slice(0, 2),
        splitSupported: grouped.some((entry) => entry.splitSupported),
        splitUncertain: grouped.some((entry) => entry.splitUncertain),
        aggregationUnstable:
          grouped.some((entry) => entry.aggregationUnstable) ||
          mergedSymbols.length > 2,
        isBar: grouped.every((entry) => entry.isBar),
        manualMerge: merge,
      });
    }
    return items;
  }

  function boxKey(item) {
    return `${item.boxNumbers[0]}-${item.boxNumbers.at(-1)}`;
  }

  function boxLabel(item) {
    if (item.kind === "lead-in") return "Lead-in · N.C.";
    if (item.kind === "pickup")
      return `Pickup · beats ${item.beatNumbers?.join("–") || "before Bar 1"}`;
    const first = item.boxNumbers[0];
    const last = item.boxNumbers.at(-1);
    if (item.isBar)
      return first === last
        ? `Bar ${first} · Box ${first}`
        : `Bars ${first}–${last} · Boxes ${first}–${last}`;
    return first === last ? `Box ${first}` : `Boxes ${first}–${last}`;
  }

  function itemFeedback(item) {
    return item.manualMerge || segmentFeedback(item.reviewIndex);
  }

  function displaySymbolsForItem(item) {
    if (item.kind === "lead-in") return ["N.C."];
    const symbols = item.manualMerge?.correctedChord
      ? [item.manualMerge.correctedChord]
      : item.chordSymbols?.length
        ? item.chordSymbols
        : [chordSymbol(item.segment)];
    const record = trackFeedback();
    return symbols.map((symbol) =>
      record.displayMode === "nns"
        ? chordToNns(symbol, record.songKey)
        : symbol,
    );
  }

  function displayItemChordAt(item, time) {
    const symbols = displaySymbolsForItem(item);
    if (symbols.length < 2) return symbols[0];
    return symbols[time >= item.start + (item.end - item.start) / 2 ? 1 : 0];
  }

  function segmentFeedback(index) {
    const track = trackFeedback();
    if (!track.segments[index]) {
      track.segments[index] = {
        status: "assumed_correct",
        correctedChord: "",
        note: "",
      };
    }
    return track.segments[index];
  }

  function flagCount(item) {
    const record = trackFeedback(item);
    const segmentFlags = Object.values(record.segments).filter((value) =>
      ["corrected", "timing", "unsure", "comment"].includes(value.status),
    ).length;
    return segmentFlags + record.boxMerges.length;
  }

  function renderTrackList() {
    const list = byId("track-list");
    list.replaceChildren();
    proof.tracks.forEach((item, index) => {
      const record = trackFeedback(item);
      const flags = flagCount(item);
      const button = document.createElement("button");
      button.type = "button";
      button.className =
        `${item.track.id === selected.track.id ? "active " : ""}${record.reviewComplete ? "complete" : ""}`.trim();
      button.setAttribute(
        "aria-pressed",
        String(item.track.id === selected.track.id),
      );
      const number = document.createElement("span");
      number.className = "track-number";
      number.textContent = String(index + 1).padStart(2, "0");
      const title = document.createElement("span");
      title.className = "track-title";
      title.textContent = item.track.title;
      const count = document.createElement("span");
      count.className = "track-review";
      count.textContent = `${record.reviewComplete ? "Reviewed" : "Pending"}${flags ? ` · ${flags}` : ""}`;
      button.append(number, title, count);
      button.addEventListener("click", () => selectTrack(item.track.id));
      list.append(button);
    });
  }

  function setStatus(card, item, status) {
    const record = itemFeedback(item);
    record.status =
      record.status === status ? defaultSegmentStatus(record, item) : status;
    saveFeedback();
    decorateCard(card, item);
  }

  function defaultSegmentStatus(record, item) {
    if (record.correctedChord) return "corrected";
    if (record.note) return "comment";
    if (item?.manualMerge) return "merged";
    return "assumed_correct";
  }

  function decorateCard(card, item) {
    if (item.kind === "lead-in") return;
    const record = itemFeedback(item);
    card.classList.remove("corrected", "timing", "unsure", "comment", "merged");
    if (record.status !== "assumed_correct") card.classList.add(record.status);
    card.querySelectorAll("[data-status]").forEach((button) => {
      button.classList.toggle(
        "selected",
        button.dataset.status === record.status,
      );
    });
    card.querySelector(".corrected-chord").value = record.correctedChord || "";
    card.querySelector(".segment-note").value = record.note || "";
    card.querySelector(".segment-note").placeholder =
      `Comment about ${boxLabel(item)}…`;
    card.querySelector(".review-state").textContent =
      {
        corrected: "Correction recorded",
        timing: "Timing flagged",
        unsure: "Marked unsure",
        comment: "Comment added",
        merged: "Structural correction · boxes merged",
      }[record.status] || "Assumed correct";
  }

  function shouldShow(item) {
    if (item.kind === "lead-in") return activeFilter === "all";
    const status = itemFeedback(item).status;
    if (activeFilter === "flagged")
      return ["corrected", "timing", "unsure", "comment", "merged"].includes(
        status,
      );
    return true;
  }

  function updateMergeControls() {
    const selectedItems = currentDisplayItems.filter(
      (item) => item.kind === "box" && selectedBoxKeys.has(boxKey(item)),
    );
    const numbers = selectedItems.flatMap((item) => item.boxNumbers);
    const adjacent =
      numbers.length >= 2 &&
      numbers.every(
        (number, index) => index === 0 || number === numbers[index - 1] + 1,
      );
    const mergeButton = byId("merge-selected");
    mergeButton.disabled = !adjacent;
    mergeButton.textContent = selectedItems.length
      ? `Merge ${selectedItems.length} selected ${selectedItems.length === 1 ? "box" : "boxes"}`
      : "Merge selected boxes";
    byId("clear-box-selection").hidden = selectedItems.length === 0;
    byId("merge-help").textContent = selectedItems.length
      ? adjacent
        ? "Adjacent boxes selected. Merging preserves every original model segment."
        : "Select two or more adjacent boxes to merge."
      : "Numbered boxes can be cited in comments or selected for a structural merge.";
  }

  function clearBoxSelection() {
    selectedBoxKeys.clear();
    document
      .querySelectorAll(".merge-select")
      .forEach((input) => (input.checked = false));
    document
      .querySelectorAll(".chord-card.selected-for-merge")
      .forEach((card) => card.classList.remove("selected-for-merge"));
    updateMergeControls();
  }

  function mergeSelectedBoxes() {
    const selectedItems = currentDisplayItems.filter(
      (item) => item.kind === "box" && selectedBoxKeys.has(boxKey(item)),
    );
    if (selectedItems.length < 2) return;
    const numbers = selectedItems.flatMap((item) => item.boxNumbers);
    if (
      !numbers.every(
        (number, index) => index === 0 || number === numbers[index - 1] + 1,
      )
    )
      return;
    const startBox = Math.min(...numbers);
    const endBox = Math.max(...numbers);
    const record = trackFeedback();
    record.boxMerges = record.boxMerges.filter(
      (merge) => merge.endBox < startBox || merge.startBox > endBox,
    );
    record.boxMerges.push({
      startBox,
      endBox,
      status: "merged",
      correctedChord: "",
      note: "",
      createdAt: new Date().toISOString(),
    });
    record.boxMerges.sort((left, right) => left.startBox - right.startBox);
    selectedBoxKeys.clear();
    saveFeedback();
    renderSegments();
    updatePlayback(true);
  }

  function undoMerge(item) {
    const target = item.manualMerge;
    const record = trackFeedback();
    record.boxMerges = record.boxMerges.filter((merge) => merge !== target);
    selectedBoxKeys.clear();
    saveFeedback();
    renderSegments();
    updatePlayback(true);
  }

  function renderSegments() {
    const grid = byId("chord-grid");
    const template = byId("chord-template");
    grid.replaceChildren();
    currentDisplayItems = buildDisplayItems();
    currentDisplayItems.forEach((item, viewIndex) => {
      const card = template.content.firstElementChild.cloneNode(true);
      card.dataset.index = String(viewIndex);
      card.hidden = !shouldShow(item);
      card.classList.toggle("lead-in", item.kind === "lead-in");
      card.classList.toggle("pickup", item.kind === "pickup");
      card.classList.toggle("manual-merge", Boolean(item.manualMerge));
      card.querySelector(".box-number").textContent = boxLabel(item);
      card.querySelector(".time-range").textContent =
        `${clock(item.start)}–${clock(item.end)}`;
      const predictedChord = card.querySelector(".predicted-chord");
      const displayedSymbols = displaySymbolsForItem(item);
      displayedSymbols.forEach((symbol, symbolIndex) => {
        if (symbolIndex) {
          const separator = document.createElement("span");
          separator.className = "chord-separator";
          separator.textContent = "/";
          predictedChord.append(separator);
        }
        const part = document.createElement("span");
        part.className = "chord-part";
        part.dataset.chordPart = String(symbolIndex);
        part.textContent = symbol;
        predictedChord.append(part);
      });
      predictedChord.title =
        item.kind === "lead-in" ? "Lead-in silence" : chordSymbol(item.segment);
      card.querySelector(".confidence").textContent =
        item.kind === "lead-in"
          ? "Not a chord box"
          : `${pct(item.confidence)} confidence${item.splitSupported ? " · supported half-bar split" : ""}${item.splitUncertain ? " · possible half-bar split — verify" : ""}${item.aggregationUnstable ? " · unstable raw changes collapsed" : ""}${item.autoGrouped ? " · transient grouped" : ""}`;
      const beatGrid = card.querySelector(".beat-grid");
      (item.beatTimes || []).forEach((time, beatIndex) => {
        const beatNumber = item.beatNumbers?.[beatIndex] || beatIndex + 1;
        const marker = document.createElement("span");
        marker.className = "beat-marker";
        marker.dataset.beatIndex = String(beatIndex);
        marker.title = `${clock(time)} · beat ${beatNumber}`;
        marker.textContent = String(beatNumber);
        beatGrid.append(marker);
      });
      card.querySelector(".seek-area").addEventListener("click", () => {
        byId("audio").currentTime = Number(item.start);
        byId("audio")
          .play()
          .catch(() => {});
        updatePlayback();
      });
      const mergeSelect = card.querySelector(".merge-select");
      if (item.kind === "box") {
        const key = boxKey(item);
        mergeSelect.checked = selectedBoxKeys.has(key);
        card.classList.toggle("selected-for-merge", mergeSelect.checked);
        mergeSelect.addEventListener("change", () => {
          if (mergeSelect.checked) selectedBoxKeys.add(key);
          else selectedBoxKeys.delete(key);
          card.classList.toggle("selected-for-merge", mergeSelect.checked);
          updateMergeControls();
        });
      } else {
        mergeSelect.closest(".merge-selector").hidden = true;
      }
      const unmerge = card.querySelector(".unmerge-button");
      unmerge.hidden = !item.manualMerge;
      unmerge.addEventListener("click", () => undoMerge(item));
      card.querySelectorAll("[data-status]").forEach((button) => {
        button.addEventListener("click", () =>
          setStatus(card, item, button.dataset.status),
        );
      });
      card
        .querySelector(".corrected-chord")
        .addEventListener("input", (event) => {
          const record = itemFeedback(item);
          record.correctedChord = event.target.value.trim();
          record.status = defaultSegmentStatus(record, item);
          saveFeedback();
          decorateCard(card, item);
        });
      card.querySelector(".segment-note").addEventListener("input", (event) => {
        const record = itemFeedback(item);
        record.note = event.target.value.trim();
        if (!["timing", "unsure"].includes(record.status))
          record.status = defaultSegmentStatus(record, item);
        saveFeedback();
        decorateCard(card, item);
      });
      decorateCard(card, item);
      grid.append(card);
    });
    updateMergeControls();
  }

  function renderProgress() {
    if (!selected || !feedback) return;
    const record = trackFeedback();
    byId("track-progress").textContent = record.reviewComplete
      ? "Reviewed"
      : "Pending";
    const completedTracks = proof.tracks.filter(
      (item) => trackFeedback(item).reviewComplete,
    ).length;
    byId("overall-progress").textContent =
      `${completedTracks} of ${proof.tracks.length} reviewed`;
    renderTrackList();
  }

  function renderTrack() {
    activeSegment = -1;
    lastClickedBeat = -1;
    selectedBoxKeys.clear();
    const index = proof.tracks.findIndex(
      (item) => item.track.id === selected.track.id,
    );
    const audio = byId("audio");
    audio.pause();
    audio.src = selected.track.audioUrl;
    audio.load();
    byId("song-position").textContent =
      `Song ${index + 1} of ${proof.tracks.length}`;
    byId("song-title").textContent = selected.track.title;
    const highestConfidence = Math.max(
      ...proof.tracks.map((item) => Number(item.summary.meanConfidence)),
    );
    const confidencePrefix =
      Number(selected.summary.meanConfidence) === highestConfidence
        ? "Highest-confidence starting track · "
        : "";
    const meaningfulBoxCount = baseDisplayItems().filter(
      (item) => item.kind === "box",
    ).length;
    const boxKind = selected.track.rhythm ? "beat-aligned bars" : "chord boxes";
    byId("song-summary").textContent =
      `${confidencePrefix}${clock(selected.track.durationSeconds)} · ${meaningfulBoxCount} numbered ${boxKind} · ${pct(selected.summary.meanConfidence)} mean model confidence`;
    byId("song-notes").value = trackFeedback().songNotes || "";
    renderNotationControls();
    const finish = byId("finish-track");
    finish.textContent = trackFeedback().reviewComplete
      ? "Song reviewed ✓"
      : "Finish song review";
    finish.disabled = Boolean(trackFeedback().reviewComplete);
    renderTrackList();
    renderSegments();
    renderProgress();
    updatePlayback();
  }

  function selectTrack(trackId) {
    selected =
      proof.tracks.find((item) => item.track.id === trackId) || proof.tracks[0];
    renderTrack();
  }

  function updatePlayback(force = false) {
    if (!selected) return;
    const time = byId("audio").currentTime;
    auditionBeatAt(time);
    const index = currentDisplayItems.findIndex(
      (item) => time >= item.start && time < item.end,
    );
    document
      .querySelectorAll(".beat-marker.active")
      .forEach((marker) => marker.classList.remove("active"));
    document
      .querySelectorAll(".chord-part.active")
      .forEach((part) => part.classList.remove("active"));
    const beatItem = currentDisplayItems[index];
    if (beatItem?.beatTimes?.length) {
      const beatIndex = beatItem.beatTimes.reduce(
        (current, beatTime, candidate) =>
          time >= beatTime ? candidate : current,
        0,
      );
      document
        .querySelector(
          `.chord-card[data-index="${index}"] .beat-marker[data-beat-index="${beatIndex}"]`,
        )
        ?.classList.add("active");
    }
    const item = currentDisplayItems[index];
    if (item) {
      const partIndex =
        displaySymbolsForItem(item).length > 1 &&
        time >= item.start + (item.end - item.start) / 2
          ? 1
          : 0;
      document
        .querySelector(
          `.chord-card[data-index="${index}"] .chord-part[data-chord-part="${partIndex}"]`,
        )
        ?.classList.add("active");
      byId("current-chord").textContent = displayItemChordAt(item, time);
    } else {
      byId("current-chord").textContent = "—";
    }
    if (index === activeSegment && !force) return;
    activeSegment = index;
    document
      .querySelectorAll(".chord-card.active")
      .forEach((card) => card.classList.remove("active"));
    byId("current-confidence").textContent = item
      ? item.kind === "lead-in"
        ? "Lead-in"
        : pct(item.confidence)
      : "—";
    if (index >= 0) {
      const card = document.querySelector(`.chord-card[data-index="${index}"]`);
      card?.classList.add("active");
      card?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "center",
      });
    }
  }

  function playGridClick(accent) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    clickAudioContext ||= new AudioContext();
    if (clickAudioContext.state === "suspended") clickAudioContext.resume();
    const oscillator = clickAudioContext.createOscillator();
    const gain = clickAudioContext.createGain();
    oscillator.frequency.value = accent ? 1320 : 880;
    gain.gain.setValueAtTime(0.0001, clickAudioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(
      accent ? 0.15 : 0.08,
      clickAudioContext.currentTime + 0.003,
    );
    gain.gain.exponentialRampToValueAtTime(
      0.0001,
      clickAudioContext.currentTime + 0.045,
    );
    oscillator.connect(gain).connect(clickAudioContext.destination);
    oscillator.start();
    oscillator.stop(clickAudioContext.currentTime + 0.05);
  }

  function auditionBeatAt(time) {
    if (!clickTrackEnabled || byId("audio").paused || !currentBeatGrid) return;
    const index = currentBeatGrid.beats.reduce(
      (current, beatTime, candidate) => (time >= beatTime ? candidate : current),
      -1,
    );
    if (index < 0 || index === lastClickedBeat) return;
    const distance = Math.abs(time - currentBeatGrid.beats[index]);
    if (distance > 0.12) return;
    lastClickedBeat = index;
    playGridClick(currentBeatGrid.beatNumbers[index] === 1);
  }

  function renderNotationControls() {
    const record = trackFeedback();
    byId("song-key").value = record.songKey;
    byId("key-source").textContent =
      `Song key · ${record.keySource === "reviewer" ? "reviewer selected" : "suggested"}`;
    byId("song-meter").value = record.songMeter;
    const provisional =
      selected.track.rhythm?.meterSource === "pilot-provisional-4-4";
    byId("meter-source").textContent = `Time signature · ${
      record.meterSource === "reviewer"
        ? "reviewer selected"
        : provisional
          ? "provisional — please confirm"
          : "detected"
    }`;
    byId("song-tempo").value = String(Math.round(record.tempoBpm));
    byId("grid-offset").textContent =
      `${record.timingOffsetSeconds >= 0 ? "+" : ""}${Number(record.timingOffsetSeconds).toFixed(2)}s`;
    byId("downbeat-phase").value = String(record.downbeatOffsetBeats);
    const phase = selected.track.rhythm?.phase;
    byId("phase-confidence").textContent =
      record.downbeatPhaseSource === "reviewer"
        ? "Reviewer-set bar start"
        : phase?.status === "anchored"
          ? `Backsolved from ${phase.anchorCount} sustained chord changes · ${pct(phase.confidence)} phase margin`
          : `Phase unresolved · ${phase?.anchorCount || 0} reliable anchors; use clicks and set Beat 1`;
    const rhythm = selected.track.rhythm;
    byId("rhythm-confidence").textContent = rhythm
      ? `${pct(rhythm.meterConfidence)} meter · ${pct(rhythm.tempoConfidence)} tempo confidence${provisional ? " · automatic meter guess was not decisive" : ""}`
      : "Beat grid unavailable";
    document.querySelectorAll("[data-notation]").forEach((button) => {
      const active = button.dataset.notation === record.displayMode;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }

  function populateKeyOptions() {
    const select = byId("song-key");
    KEY_NAMES.forEach((key) => {
      const option = document.createElement("option");
      option.value = key;
      option.textContent = key === "F#" ? "F# / Gb" : key;
      select.append(option);
    });
  }

  function startPlaybackTracking() {
    cancelAnimationFrame(playbackFrame);
    const tick = () => {
      updatePlayback();
      if (!byId("audio").paused && !byId("audio").ended)
        playbackFrame = requestAnimationFrame(tick);
    };
    playbackFrame = requestAnimationFrame(tick);
  }

  function finishTrack() {
    const record = trackFeedback();
    record.reviewComplete = true;
    record.reviewedAt = new Date().toISOString();
    saveFeedback();
    renderTrack();
  }

  function exportFeedback() {
    const complete = structuredClone(feedback);
    complete.exportedAt = new Date().toISOString();
    complete.source = {
      proofGeneratedAt: proof.generatedAt,
      trackCount: proof.tracks.length,
      disclosure: proof.disclosure,
    };
    complete.tracks = proof.tracks.map((item) => {
      const record = trackFeedback(item);
      return {
        ...record,
        segmentCount: item.prediction.segments.length,
        segments: item.prediction.segments.map((segment, index) => ({
          index,
          start: segment.start,
          end: segment.end,
          predictedChord: segment.productLabel || segment.label || "N.C.",
          predictedNns: chordToNns(
            segment.productLabel || segment.label || "N.C.",
            record.songKey,
          ),
          modelConfidence: segment.confidence,
          ...(record.segments[index] || {
            status: record.reviewComplete
              ? "assumed_correct"
              : "pending_assumed_correct",
            correctedChord: "",
            note: "",
          }),
        })),
      };
    });
    const blob = new Blob([`${JSON.stringify(complete, null, 2)}\n`], {
      type: "application/json",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `chord-reader-travis-feedback-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function bindControls() {
    byId("audio").addEventListener("timeupdate", updatePlayback);
    byId("audio").addEventListener("seeked", updatePlayback);
    byId("audio").addEventListener("play", startPlaybackTracking);
    byId("audio").addEventListener("pause", () =>
      cancelAnimationFrame(playbackFrame),
    );
    byId("audio").addEventListener("ended", () =>
      cancelAnimationFrame(playbackFrame),
    );
    byId("finish-track").addEventListener("click", finishTrack);
    byId("export-feedback").addEventListener("click", exportFeedback);
    byId("merge-selected").addEventListener("click", mergeSelectedBoxes);
    byId("clear-box-selection").addEventListener("click", clearBoxSelection);
    byId("song-notes").addEventListener("input", (event) => {
      trackFeedback().songNotes = event.target.value;
      saveFeedback();
    });
    byId("song-key").addEventListener("change", (event) => {
      const record = trackFeedback();
      record.songKey = event.target.value;
      record.keySource = "reviewer";
      saveFeedback();
      renderNotationControls();
      renderSegments();
      updatePlayback(true);
    });
    byId("song-meter").addEventListener("change", (event) => {
      const record = trackFeedback();
      record.songMeter = event.target.value;
      record.meterSource = "reviewer";
      record.boxMerges = [];
      record.downbeatOffsetBeats = ChordPhaseAnchor.mod(
        record.downbeatOffsetBeats,
        Number(record.songMeter.split("/")[0]) || 4,
      );
      selectedBoxKeys.clear();
      saveFeedback();
      renderNotationControls();
      renderSegments();
      updatePlayback(true);
    });
    byId("song-tempo").addEventListener("change", (event) => {
      const nextTempo = Math.max(40, Math.min(240, Number(event.target.value)));
      trackFeedback().tempoBpm = Math.round(nextTempo || 100);
      saveFeedback();
      renderNotationControls();
    });
    const nudgeGrid = (seconds) => {
      const record = trackFeedback();
      record.timingOffsetSeconds = Math.max(
        -2,
        Math.min(2, Number((record.timingOffsetSeconds + seconds).toFixed(2))),
      );
      saveFeedback();
      renderNotationControls();
      renderSegments();
      updatePlayback(true);
    };
    byId("grid-earlier").addEventListener("click", () => nudgeGrid(-0.05));
    byId("grid-later").addEventListener("click", () => nudgeGrid(0.05));
    byId("grid-reset").addEventListener("click", () => {
      trackFeedback().timingOffsetSeconds = Number(
        selected.track.rhythm?.gridOffsetSeconds || 0,
      );
      saveFeedback();
      renderNotationControls();
      renderSegments();
      updatePlayback(true);
    });
    byId("downbeat-phase").addEventListener("change", (event) => {
      const record = trackFeedback();
      record.downbeatOffsetBeats = Number(event.target.value);
      record.downbeatPhaseSource = "reviewer";
      record.boxMerges = [];
      selectedBoxKeys.clear();
      saveFeedback();
      renderNotationControls();
      renderSegments();
      updatePlayback(true);
    });
    byId("set-downbeat-here").addEventListener("click", () => {
      if (!currentBeatGrid?.beats.length) return;
      const nearest = ChordPhaseAnchor.nearestBeatIndex(
        currentBeatGrid.beats,
        byId("audio").currentTime,
      );
      if (nearest.index < 0) return;
      const beatsPerBar = Number(trackFeedback().songMeter.split("/")[0]) || 4;
      const record = trackFeedback();
      record.downbeatOffsetBeats = ChordPhaseAnchor.mod(
        nearest.index - currentBeatGrid.prependedCount,
        beatsPerBar,
      );
      record.downbeatPhaseSource = "reviewer";
      record.boxMerges = [];
      selectedBoxKeys.clear();
      saveFeedback();
      renderNotationControls();
      renderSegments();
      updatePlayback(true);
    });
    byId("click-track").addEventListener("change", (event) => {
      clickTrackEnabled = event.target.checked;
      lastClickedBeat = -1;
      if (clickTrackEnabled) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) clickAudioContext ||= new AudioContext();
        clickAudioContext?.resume();
      }
    });
    document.querySelectorAll("[data-notation]").forEach((button) => {
      button.addEventListener("click", () => {
        trackFeedback().displayMode = button.dataset.notation;
        saveFeedback();
        renderNotationControls();
        renderSegments();
        updatePlayback(true);
      });
    });
    document.querySelectorAll(".filter").forEach((button) => {
      button.addEventListener("click", () => {
        activeFilter = button.dataset.filter;
        document
          .querySelectorAll(".filter")
          .forEach((item) => item.classList.toggle("active", item === button));
        renderSegments();
      });
    });
  }

  fetch(DATA_URL, { cache: "no-store" })
    .then((response) => {
      if (!response.ok)
        throw new Error(`Prediction bundle returned ${response.status}.`);
      return response.json();
    })
    .then(async (value) => {
      if (value.schemaVersion !== "chord_reader_local_song_test_v1")
        throw new Error("Unexpected prediction bundle.");
      proof = value;
      feedback = await loadFeedback();
      byId("track-total").textContent = String(proof.tracks.length);
      if (REMOTE_MODE)
        byId("save-status").textContent =
          "Secure backend connected. Changes save automatically.";
      populateKeyOptions();
      bindControls();
      const highestConfidence = proof.tracks.reduce(
        (best, item) =>
          Number(item.summary.meanConfidence) >
          Number(best.summary.meanConfidence)
            ? item
            : best,
        proof.tracks[0],
      );
      selectTrack(highestConfidence.track.id);
    })
    .catch((error) => {
      byId("song-title").textContent = "The validation data could not load.";
      byId("song-summary").textContent =
        `${error.message} Generate the private prediction bundle first.`;
    });
})();
