(function (global) {
  "use strict";

  const accountActivity = global.STEEL_RAG_ACCOUNT_ACTIVITY;

  const MAX_EVENTS_PER_SECTION = 16;
  const TASKS = {
    artist_solo_lesson: {
      title: "Learn an artist’s solo",
      shortTitle: "Artist solo",
      question: "Teach this artist solo as an E9 lesson.",
      renderingMode: "transcription",
      needsMaterial: true
    },
    song_arrangement_lesson: {
      title: "Build a song arrangement",
      shortTitle: "Song arrangement",
      question: "Build this song section as an E9 teaching arrangement.",
      renderingMode: "e9_adaptation",
      needsMaterial: true
    },
    user_melody: {
      title: "Map my own melody",
      shortTitle: "My melody",
      question: "Map my melody into a playable E9 lesson.",
      renderingMode: "e9_adaptation",
      needsMaterial: false
    },
    original_exercise: {
      title: "Make a practice phrase",
      shortTitle: "Practice phrase",
      question: "Build an original E9 practice phrase.",
      renderingMode: "teaching_simplification",
      needsMaterial: false
    }
  };
  const STARTING_POINTS = {
    song: "song_practice",
    phrase: "user_melody",
    score: "user_melody",
    import: "user_melody",
    microphone: "user_melody",
    recording: "song_arrangement_lesson",
    catalog: "song_arrangement_lesson",
    exercise: "original_exercise"
  };
  const KEY_NOTES = {
    C: ["C", "D", "E", "F", "G", "A", "B"],
    Db: ["Db", "Eb", "F", "Gb", "Ab", "Bb", "C"],
    D: ["D", "E", "F#", "G", "A", "B", "C#"],
    Eb: ["Eb", "F", "G", "Ab", "Bb", "C", "D"],
    E: ["E", "F#", "G#", "A", "B", "C#", "D#"],
    F: ["F", "G", "A", "Bb", "C", "D", "E"],
    "F#": ["F#", "G#", "A#", "B", "C#", "D#", "E#"],
    G: ["G", "A", "B", "C", "D", "E", "F#"],
    Ab: ["Ab", "Bb", "C", "Db", "Eb", "F", "G"],
    A: ["A", "B", "C#", "D", "E", "F#", "G#"],
    Bb: ["Bb", "C", "D", "Eb", "F", "G", "A"],
    B: ["B", "C#", "D#", "E", "F#", "G#", "A#"]
  };
  const E9_OPEN_NOTES = {
    1: "F#", 2: "D#", 3: "G#", 4: "E", 5: "B",
    6: "G#", 7: "F#", 8: "E", 9: "D", 10: "B"
  };
  const E9_OPEN_PITCHES = { 1: 66, 2: 63, 3: 68, 4: 64, 5: 59, 6: 56, 7: 54, 8: 52, 9: 50, 10: 47 };
  const E9_CHANGE_DELTAS = {
    A: { 5: 2, 10: 2 }, B: { 3: 1, 6: 1 }, C: { 4: 2, 5: 2 },
    E: { 4: -1, 8: -1 }, F: { 4: 1, 8: 1 }, V: { 5: -1, 10: -1 },
    G: { 1: 1, 6: -1 }, D: { 2: -2, 9: -1 }
  };
  const COPEDENT_STORAGE_KEY = "steel-guitar-rag.copedentProfile.v1";
  const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const CHROMATIC_SHARPS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const PRESETS = {
    "1-2-3-5": ["1", "2", "3", "5"],
    "1-3-5-3": ["1", "3", "5", "3"],
    "5-6-5-3": ["5", "6", "5", "3"]
  };

  function savedE9TargetCopedent(storage = global.localStorage) {
    const active = global.STEEL_RAG_COPEDENTS?.activeContext?.(storage);
    if (active && !active.blocked) {
      return active.profileSnapshot || null;
    }
    try {
      const profile = JSON.parse(storage?.getItem?.(COPEDENT_STORAGE_KEY) || "null");
      if (!profile || String(profile.tuningFamily || "").toUpperCase() !== "E9") return null;
      if (Number(profile.stringCount || profile.strings?.length) !== 10 || !Array.isArray(profile.strings)) return null;
      return {
        id: profile.id || "saved-user-e9",
        name: profile.name || "My saved E9",
        tuningFamily: "E9",
        stringCount: 10,
        strings: profile.strings.map((item) => ({
          stringNumber: Number(item.stringNumber),
          openNote: String(item.openNote || "")
        })),
        controls: (profile.controls || []).map((control) => ({
          id: String(control.id || control.label || ""),
          label: String(control.label || control.id || ""),
          type: String(control.type || "lever"),
          changes: (control.changes || []).map((change) => ({
            stringNumber: Number(change.stringNumber),
            fromNote: String(change.fromNote || ""),
            toNote: String(change.toNote || "")
          }))
        }))
      };
    } catch (_error) {
      return null;
    }
  }

  function normalizeToken(value) {
    const raw = String(value || "").trim().replace(/♯/g, "#").replace(/♭/g, "b");
    if (/^[1-7]$/.test(raw)) return raw;
    const match = raw.match(/^([A-Ga-g])([#b]?)$/);
    return match ? `${match[1].toUpperCase()}${match[2]}` : raw;
  }

  function semitoneForNote(note) {
    const normalized = normalizeToken(note);
    const flats = { Db: "C#", Eb: "D#", Gb: "F#", Ab: "G#", Bb: "A#" };
    return CHROMATIC_SHARPS.indexOf(flats[normalized] || normalized);
  }

  function noteAtFret(stringNumber, fret) {
    const openNote = E9_OPEN_NOTES[Number(stringNumber)];
    const openSemitone = semitoneForNote(openNote);
    if (!openNote || openSemitone < 0 || !Number.isInteger(Number(fret)) || Number(fret) < 0 || Number(fret) > 24) {
      return "";
    }
    return CHROMATIC_SHARPS[(openSemitone + Number(fret)) % 12];
  }

  function parseSimpleTab(value) {
    const match = String(value || "").match(/(?:^|\n)\s*(?:S|string\s*)\s*(\d{1,2})\s*:\s*([^\n]+)/i);
    if (!match) return [];
    return (match[2].match(/\d{1,2}/g) || [])
      .map((fret) => noteAtFret(Number(match[1]), Number(fret)))
      .filter(Boolean);
  }

  function parseSimpleTabEvents(value) {
    const compact = Array.from(String(value || "").matchAll(/S(\d{1,2}):(\d{1,2})([A-Za-z](?:\+[A-Za-z])*)?/gi));
    if (compact.length) {
      return compact.map((match) => ({
        token: match[0].toUpperCase(),
        string: Number(match[1]),
        fret: Number(match[2]),
        changes: match[3] ? match[3].split("+").filter(Boolean).map((item) => item.toUpperCase()) : [],
        direction: "auto",
        octaveShift: 0
      }));
    }
    const match = String(value || "").match(/(?:^|\n)\s*(?:S|string\s*)\s*(\d{1,2})\s*:\s*([^\n]+)/i);
    if (!match) return [];
    const string = Number(match[1]);
    return (match[2].match(/\d{1,2}(?:[A-Za-z](?:\+[A-Za-z])*)?/g) || []).map((entry) => {
      const tokenMatch = entry.match(/^(\d{1,2})(.*)$/);
      const fret = Number(tokenMatch[1]);
      const changes = tokenMatch[2] ? tokenMatch[2].split("+").filter(Boolean).map((item) => item.toUpperCase()) : [];
      return { token: `S${string}:${fret}${changes.join("+")}`, string, fret, changes, direction: "auto", octaveShift: 0 };
    });
  }

  function phraseItem(value) {
    if (value && typeof value === "object") return { direction: "auto", octaveShift: 0, ...value };
    return { token: normalizeToken(value), direction: "auto", octaveShift: 0 };
  }

  function phraseItemLabel(value) {
    const item = phraseItem(value);
    return String(item.token || (item.string ? `S${item.string}:${item.fret}` : ""));
  }

  function parsePhraseEvents(value) {
    const literal = parseSimpleTabEvents(value);
    if (literal.length) return literal;
    return parsePhraseInput(value).map(phraseItem);
  }

  function pitchLabel(value) {
    return `${NOTE_NAMES[((value % 12) + 12) % 12]}${Math.floor(value / 12) - 1}`;
  }

  function resolvePhrasePreview(items, key, contourMode = "closest_playable") {
    const notes = KEY_NOTES[key] || [];
    const anchor = 67;
    const result = [];
    let previousBase = null;
    (items || []).forEach((raw) => {
      const item = phraseItem(raw);
      let basePitch;
      if (Number.isInteger(item.string) && Number.isInteger(item.fret)) {
        const changeDelta = (item.changes || []).reduce((sum, change) => sum + (E9_CHANGE_DELTAS[String(change).toUpperCase()]?.[item.string] || 0), 0);
        basePitch = (E9_OPEN_PITCHES[item.string] ?? 64) + item.fret + changeDelta;
      } else {
        const token = normalizeToken(item.token);
        const note = /^[1-7]$/.test(token) ? notes[Number(token) - 1] : token;
        const pitchClass = semitoneForNote(note);
        const options = Array.from({ length: 48 }, (_, offset) => 47 + offset).filter((value) => value % 12 === pitchClass);
        if (previousBase === null) basePitch = options.sort((a, b) => Math.abs(a - anchor) - Math.abs(b - anchor) || a - b)[0];
        else {
          const direction = item.direction !== "auto" ? item.direction : contourMode === "ascending" ? "up" : contourMode === "descending" ? "down" : "nearest";
          const directed = options.filter((value) => direction === "up" ? value >= previousBase : direction === "down" ? value <= previousBase : true);
          basePitch = (directed.length ? directed : options).sort((a, b) => Math.abs(a - previousBase) - Math.abs(b - previousBase) || a - b)[0];
        }
      }
      const pitch = basePitch + (Number.isInteger(item.string) ? 0 : Number(item.octaveShift || 0) * 12);
      result.push({ ...item, pitchValue: pitch, pitch: pitchLabel(pitch) });
      previousBase = basePitch;
    });
    return result;
  }

  function parsePhraseInput(value) {
    const tabNotes = parseSimpleTab(value);
    if (tabNotes.length) return tabNotes;
    return String(value || "")
      .split(/[\s,|]+/)
      .map(normalizeToken)
      .filter(Boolean);
  }

  function sectionCount(tokens) {
    return Math.max(1, Math.ceil((tokens?.length || 0) / MAX_EVENTS_PER_SECTION));
  }

  function validateTokens(tokens, key) {
    const allowedNotes = new Set(KEY_NOTES[key] || []);
    const invalid = (tokens || []).filter((raw) => {
      const item = phraseItem(raw);
      if (Number.isInteger(item.string) && Number.isInteger(item.fret)) return item.string < 1 || item.string > 10 || item.fret < 0 || item.fret > 24;
      if (Number.isFinite(Number(item.pitchValue)) || /^[A-Ga-g](?:#|b)?-?\d+$/.test(String(item.pitch || ""))) return false;
      const token = normalizeToken(item.token);
      return !/^[1-7]$/.test(token) && !allowedNotes.has(token);
    });
    if (!tokens?.length) return { ok: false, message: "Add at least one note, scale degree, or simple tab position." };
    if (invalid.length) {
      return { ok: false, message: `${invalid.map(phraseItemLabel).join(", ")} ${invalid.length === 1 ? "is" : "are"} outside ${key} major or the supported E9 tab range.` };
    }
    return { ok: true, message: "" };
  }

  function reorderToken(tokens, index, direction) {
    const next = [...(tokens || [])];
    const target = index + direction;
    if (index < 0 || target < 0 || index >= next.length || target >= next.length) return next;
    [next[index], next[target]] = [next[target], next[index]];
    return next;
  }

  function buildMelodyRequest(state) {
    const task = TASKS[state.kind];
    const request = {
      kind: state.kind,
      key: state.key,
      tuning: "E9",
      renderingMode: task.renderingMode,
      sectionNumber: state.sectionNumber || 1,
      contourMode: state.contourMode || "closest_playable",
      voiceMode: state.voiceMode || "mixed",
      movementMode: state.movementMode || "best_fit"
    };
    if (state.targetCopedent) {
      request.targetCopedent = state.targetCopedent;
      request.targetCopedentId = `saved:${state.targetCopedent.id || "saved-user-e9"}`;
    } else if (state.targetCopedentId) {
      request.targetCopedentId = state.targetCopedentId;
    }
    if (state.sourceCopedentId) request.sourceCopedentId = state.sourceCopedentId;
    if (state.tokens?.length) request.melody = [...state.tokens];
    const sections = state.scoreDraft?.score?.sections;
    const score = state.scoreDraft?.score;
    if (score?.meter) request.meter = score.meter;
    if (Number.isFinite(Number(score?.pickupBeats))) request.pickupBeats = Number(score.pickupBeats);
    if (Array.isArray(sections) && sections.length) {
      request.sections = sections.map((section) => ({ ...section }));
      request.wholeSong = true;
    }
    const transcription = state.scoreDraft?.transcription;
    if (transcription) {
      request.accuracy = "approximate";
      request.accuracyConfidence = transcription.confidenceLabel || "low";
      request.accuracyNote = "Pitch and rhythm came from on-device audio estimation and were opened for manual review before E9 arrangement.";
      request.sourceProvided = true;
      request.transcription = {
        engine: transcription.engine,
        confidence: transcription.confidence,
        confidenceLabel: transcription.confidenceLabel,
        audioRetained: false
      };
    }
    if (task.needsMaterial) {
      const hasReviewedSections = Array.isArray(sections) && sections.length > 0;
      request.material = {
        artist: state.artist || "",
        song: state.song || "",
        recording: state.recording || "",
        section: state.section || (hasReviewedSections ? "" : `Section ${state.sectionNumber || 1}`),
        sourceUrl: state.sourceUrl || ""
      };
    }
    return request;
  }

  function startingPointForKind(kind) {
    if (kind === "artist_solo_lesson" || kind === "song_arrangement_lesson") return "recording";
    if (kind === "original_exercise") return "exercise";
    return "phrase";
  }

  function entryChoicePresentation(target, { replacing = false, catalogCount = 0 } = {}) {
    const choices = {
      song: {
        label: "Learn a song",
        defaultHelp: "Chord Karaoke",
        replacementHelp: "Start a Song Project"
      },
      catalog: {
        label: "Browse songbook",
        defaultHelp: catalogCount ? `${catalogCount} reviewed songs` : "Reviewed melody examples",
        replacementHelp: "Choose a different reviewed song"
      },
      phrase: {
        label: "Type or tap notes",
        defaultHelp: "Notes or scale numbers",
        replacementHelp: "Enter a different melody"
      },
      microphone: {
        label: "Record or upload audio",
        defaultHelp: "Choose a short passage",
        replacementHelp: "Use a different recording"
      },
      score: {
        label: "Staff editor",
        defaultHelp: "Write notes on a staff",
        replacementHelp: "Edit a different melody on the staff"
      },
      import: {
        label: "Import music",
        defaultHelp: "Photo, MusicXML, or MIDI",
        replacementHelp: "Import a different file"
      }
    };
    const choice = choices[target] || choices.phrase;
    return {
      label: choice.label,
      help: replacing ? choice.replacementHelp : choice.defaultHelp
    };
  }

  function createInitialState(kind = "user_melody") {
    const safeKind = TASKS[kind] ? kind : "user_melody";
    return {
      kind: safeKind,
      inputMethod: "phrase",
      workflowPhase: "add",
      showSourceDetails: safeKind === "artist_solo_lesson" || safeKind === "song_arrangement_lesson",
      pendingReplacement: "",
      key: "G",
      paletteMode: "degrees",
      tokens: [],
      contourMode: "closest_playable",
      voiceMode: "mixed",
      movementMode: "best_fit",
      selectedHarmonyType: "mixed_arrangement",
      sourceCopedentId: "",
      targetCopedentId: "emmons-e9-basic",
      targetCopedent: null,
      selectedPhraseIndex: 0,
      artist: "",
      song: "",
      recording: "",
      section: "",
      sourceUrl: "",
      sectionNumber: 1,
      activeEventIndex: 0,
      showOctaveMap: false,
      showOctaveLabels: false,
      showStringLabels: false,
      response: null,
      exploredTabEventIndex: null,
      scoreDraft: null,
      scoreEditingEnabled: true,
      scoreSelectedIndex: -1,
      scoreHistory: [],
      scoreFuture: [],
      sourceImageUrl: "",
      sourceAudioUrl: "",
      microphoneCapture: null,
      tapTimes: [],
      importParts: [],
      importSelectedPart: "",
      practiceStatus: "stopped",
      practiceTimers: [],
      practiceContext: null,
      practiceRun: 0,
      loopMode: "off",
      loopStart: null,
      loopEnd: null
    };
  }

  function youtubeVideoId(value) {
    try {
      const url = new URL(String(value || "").trim());
      if (url.hostname === "youtu.be") return url.pathname.split("/").filter(Boolean)[0] || "";
      if (!/(^|\.)youtube\.com$/.test(url.hostname)) return "";
      if (url.pathname === "/watch") return url.searchParams.get("v") || "";
      const parts = url.pathname.split("/").filter(Boolean);
      return ["embed", "shorts", "live"].includes(parts[0]) ? parts[1] || "" : "";
    } catch (_error) {
      return "";
    }
  }

  function referenceEmbedUrl(value, start = 0, end = 0) {
    const id = youtubeVideoId(value);
    if (!id) return "";
    const query = new URLSearchParams({ rel: "0", playsinline: "1" });
    if (Number(start) > 0) query.set("start", String(Math.floor(Number(start))));
    if (Number(end) > Number(start)) query.set("end", String(Math.floor(Number(end))));
    return `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?${query.toString()}`;
  }

  function fileSourceType(file) {
    const name = String(file?.name || "").toLowerCase();
    const type = String(file?.type || "").toLowerCase();
    if (type.startsWith("image/") || /\.(jpe?g|png|webp)$/.test(name)) return "image";
    if (/\.(mxl)$/.test(name)) return "mxl";
    if (/\.(mid|midi)$/.test(name) || type.includes("midi")) return "midi";
    if (/\.(xml|musicxml)$/.test(name) || type.includes("xml")) return "musicxml";
    return "";
  }

  function parseAudioTimecode(value) {
    const text = String(value ?? "").trim();
    if (!text) return 0;
    if (/^\d+(?:\.\d+)?$/.test(text)) return Number(text);
    const parts = text.split(":");
    if (parts.length !== 2 || !/^\d+$/.test(parts[0]) || !/^\d+(?:\.\d+)?$/.test(parts[1])) return null;
    const seconds = Number(parts[1]);
    return seconds < 60 ? Number(parts[0]) * 60 + seconds : null;
  }

  function formatAudioTimecode(value) {
    const seconds = Math.max(0, Number(value) || 0);
    const minutes = Math.floor(seconds / 60);
    const remainder = seconds - minutes * 60;
    return `${minutes}:${remainder.toFixed(remainder % 1 ? 1 : 0).padStart(2, "0")}`;
  }

  function audioWindowBounds(audioDuration, startValue, lengthValue) {
    const duration = Number(audioDuration);
    const start = parseAudioTimecode(startValue);
    const length = Math.max(5, Math.min(15, Number(lengthValue) || 15));
    if (!Number.isFinite(duration) || duration <= 0 || start === null || start < 0 || start >= duration) return null;
    const end = Math.min(duration, start + length);
    return end - start >= 0.25 ? { start, end, duration: end - start } : null;
  }

  function frequencyToMidi(frequency) {
    const value = Number(frequency);
    return value > 0 ? Math.round(69 + 12 * Math.log2(value / 440)) : null;
  }

  function frequencyToMidiFloat(frequency) {
    const value = Number(frequency);
    return value > 0 ? 69 + 12 * Math.log2(value / 440) : null;
  }

  function autoCorrelate(buffer, sampleRate) {
    if (!buffer?.length || !sampleRate) return -1;
    let rms = 0;
    for (let index = 0; index < buffer.length; index += 1) rms += buffer[index] * buffer[index];
    rms = Math.sqrt(rms / buffer.length);
    if (rms < 0.012) return -1;
    const minOffset = Math.max(2, Math.floor(sampleRate / 1000));
    const maxOffset = Math.min(buffer.length - 2, Math.floor(sampleRate / 70));
    let bestOffset = -1;
    let bestCorrelation = 0;
    for (let offset = minOffset; offset <= maxOffset; offset += 1) {
      let correlation = 0;
      for (let index = 0; index < buffer.length - offset; index += 1) correlation += buffer[index] * buffer[index + offset];
      if (correlation > bestCorrelation) {
        bestCorrelation = correlation;
        bestOffset = offset;
      }
    }
    return bestOffset > 0 ? sampleRate / bestOffset : -1;
  }

  function median(values) {
    const sorted = (values || []).filter(Number.isFinite).sort((a, b) => a - b);
    if (!sorted.length) return null;
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  }

  function quantizeTranscriptionBeats(seconds, bpm = 80) {
    const raw = Math.max(0.05, Number(seconds) || 0) * Math.max(40, Math.min(200, Number(bpm) || 80)) / 60;
    return [0.5, 1, 1.5, 2, 3, 4].sort((a, b) => Math.abs(a - raw) - Math.abs(b - raw) || a - b)[0];
  }

  function transcribePitchSamples(rawSamples, options = {}) {
    const bpm = Math.max(40, Math.min(200, Number(options.bpm) || 80));
    const samples = (rawSamples || []).map((raw) => ({
      time: Number(raw.time),
      midiFloat: Number.isFinite(Number(raw.midiFloat)) ? Number(raw.midiFloat) : Number.isFinite(Number(raw.midi)) ? Number(raw.midi) : null
    })).filter((sample) => Number.isFinite(sample.time)).sort((a, b) => a.time - b.time);
    if (!samples.length) return { events: [], confidence: 0, confidenceLabel: "low", warnings: ["No usable audio frames were detected."] };

    const smoothed = samples.map((sample, index) => {
      if (!Number.isFinite(sample.midiFloat)) return { ...sample, midi: null, deviation: null };
      const neighbors = samples.slice(Math.max(0, index - 2), index + 3)
        .filter((candidate) => Number.isFinite(candidate.midiFloat) && Math.abs(candidate.time - sample.time) <= 0.14)
        .map((candidate) => candidate.midiFloat);
      const stable = median(neighbors) ?? sample.midiFloat;
      const midi = Math.round(stable);
      return { ...sample, midi, deviation: Math.abs(stable - midi) };
    });
    const voicedTimes = smoothed.filter((sample) => sample.midi !== null).map((sample) => sample.time);
    const frameSeconds = Math.max(0.02, Math.min(0.12, median(voicedTimes.slice(1).map((time, index) => time - voicedTimes[index])) || 0.05));
    const preliminary = [];
    smoothed.forEach((sample) => {
      if (sample.midi === null || sample.midi < 36 || sample.midi > 96) return;
      const last = preliminary.at(-1);
      if (last && last.midi === sample.midi && sample.time - last.lastTime <= Math.max(0.2, frameSeconds * 3)) {
        last.lastTime = sample.time;
        last.frames += 1;
        last.deviations.push(sample.deviation);
      } else {
        preliminary.push({ midi: sample.midi, startTime: sample.time, lastTime: sample.time, frames: 1, deviations: [sample.deviation] });
      }
    });
    const stableRuns = preliminary.filter((run) => run.frames >= 2 && run.lastTime - run.startTime + frameSeconds >= 0.11);
    const merged = [];
    stableRuns.forEach((run) => {
      const last = merged.at(-1);
      if (last && last.midi === run.midi && run.startTime - (last.lastTime + frameSeconds) < 0.18) {
        last.lastTime = run.lastTime;
        last.frames += run.frames;
        last.deviations.push(...run.deviations);
      } else merged.push({ ...run, deviations: [...run.deviations] });
    });

    const events = [];
    let previousEnd = null;
    merged.slice(0, 64).forEach((run, index) => {
      const endTime = run.lastTime + frameSeconds;
      if (previousEnd !== null && run.startTime - previousEnd >= 0.3) {
        events.push({
          id: `audio-rest-${index + 1}`,
          rest: true,
          pitch: null,
          pitchValue: null,
          durationBeats: quantizeTranscriptionBeats(run.startTime - previousEnd, bpm),
          origin: "audio_estimate",
          confidence: 0.9
        });
      }
      const durationSeconds = Math.max(frameSeconds, endTime - run.startTime);
      const averageDeviation = run.deviations.reduce((sum, value) => sum + value, 0) / Math.max(1, run.deviations.length);
      const confidence = Math.max(0.35, Math.min(0.98,
        0.48 + Math.min(0.28, run.frames * 0.025) + Math.min(0.16, durationSeconds * 0.12) - Math.min(0.25, averageDeviation * 0.65)
      ));
      events.push({
        id: `audio-note-${index + 1}`,
        pitchValue: run.midi,
        pitch: pitchLabel(run.midi),
        durationBeats: quantizeTranscriptionBeats(durationSeconds, bpm),
        origin: "audio_estimate",
        confidence: Number(confidence.toFixed(3)),
        sourceStartSeconds: Number(run.startTime.toFixed(3)),
        sourceEndSeconds: Number(endTime.toFixed(3))
      });
      previousEnd = endTime;
    });
    const notes = events.filter((event) => !event.rest);
    const confidence = notes.length ? notes.reduce((sum, event) => sum + event.confidence, 0) / notes.length : 0;
    const confidenceLabel = confidence >= 0.85 ? "high" : confidence >= 0.68 ? "medium" : "low";
    const lowConfidenceCount = notes.filter((event) => event.confidence < 0.68).length;
    const warnings = ["Pitch and rhythm were estimated on this device; confirm every note before arranging."];
    if (lowConfidenceCount) warnings.push(`${lowConfidenceCount} note${lowConfidenceCount === 1 ? "" : "s"} need${lowConfidenceCount === 1 ? "s" : ""} extra review.`);
    return { events, confidence: Number(confidence.toFixed(3)), confidenceLabel, lowConfidenceCount, warnings };
  }

  function pitchSamplesFromPcm(channelData, sampleRate, options = {}) {
    const source = channelData || [];
    const sourceRate = Number(sampleRate);
    if (!source.length || !Number.isFinite(sourceRate) || sourceRate <= 0) return [];
    const targetRate = Math.min(8000, sourceRate);
    const ratio = sourceRate / targetRate;
    const downsampled = new Float32Array(Math.max(1, Math.floor(source.length / ratio)));
    for (let index = 0; index < downsampled.length; index += 1) {
      const start = Math.floor(index * ratio);
      const end = Math.max(start + 1, Math.min(source.length, Math.floor((index + 1) * ratio)));
      let sum = 0;
      for (let cursor = start; cursor < end; cursor += 1) sum += source[cursor];
      downsampled[index] = sum / (end - start);
    }
    const frameSize = 1024;
    const hopSize = 512;
    const limit = Math.min(downsampled.length, Math.floor((Number(options.maxSeconds) || 15) * targetRate));
    const samples = [];
    for (let start = 0; start + frameSize <= limit; start += hopSize) {
      const frame = downsampled.subarray(start, start + frameSize);
      const frequency = autoCorrelate(frame, targetRate);
      samples.push({ time: start / targetRate, midiFloat: frequencyToMidiFloat(frequency) });
    }
    return samples;
  }

  function createAudioTranscriptionDraft(samples, options = {}) {
    const bpm = Math.max(40, Math.min(200, Number(options.bpm) || 80));
    const transcription = transcribePitchSamples(samples, { bpm });
    const sourceStartSeconds = Math.max(0, Number(options.sourceStartSeconds) || 0);
    const sourceEndSeconds = Number.isFinite(Number(options.sourceEndSeconds)) ? Number(options.sourceEndSeconds) : null;
    return {
      schemaVersion: "score_draft_v1",
      source: {
        type: options.sourceType || "microphone",
        title: options.title || "Recorded melody",
        url: null,
        rightsLabel: "user_provided",
        retained: false
      },
      score: {
        sourceKey: options.key || "G",
        arrangementKey: options.key || "G",
        meter: options.meter || "4/4",
        pickupBeats: 0,
        melody: transcription.events.map((event) => ({
          ...event,
          ...(Number.isFinite(Number(event.sourceStartSeconds)) ? { sourceStartSeconds: Number((event.sourceStartSeconds + sourceStartSeconds).toFixed(3)) } : {}),
          ...(Number.isFinite(Number(event.sourceEndSeconds)) ? { sourceEndSeconds: Number((event.sourceEndSeconds + sourceStartSeconds).toFixed(3)) } : {})
        })),
        harmony: []
      },
      review: { status: "needs_review", warnings: transcription.warnings },
      transcription: {
        engine: "on_device_monophonic_v1",
        tempoBpm: bpm,
        confidence: transcription.confidence,
        confidenceLabel: transcription.confidenceLabel,
        lowConfidenceCount: transcription.lowConfidenceCount || 0,
        audioRetained: false,
        sourceStartSeconds,
        sourceEndSeconds
      }
    };
  }

  function controlLabel(change) {
    return ({ A: "A pedal", B: "B pedal", C: "C pedal", E: "E-lower lever", F: "F lever", V: "vertical lever", G: "G lever", D: "D lever" })[change] || change;
  }

  function eventStepPresentation(event) {
    const notes = event?.notes || [];
    const strings = notes.map((note) => note.string);
    const frets = Array.from(new Set(notes.map((note) => note.fret)));
    const controls = Array.isArray(event?.performanceControlLabels) && event.performanceControlLabels.length
      ? event.performanceControlLabels
      : Array.from(new Set(notes.flatMap((note) => note.changes || []))).map(controlLabel);
    const positionParts = [
      `${strings.length === 1 ? "String" : "Strings"} ${strings.join(" + ")}`,
      `${frets.length === 1 ? "Fret" : "Frets"} ${frets.join(" + ")}`,
      controls.length ? controls.join(" + ") : "Open"
    ];
    return {
      note: `${event?.step}. ${event?.resolvedPitch || event?.resolvedNote || "Note"}`,
      position: positionParts.join(" · ")
    };
  }

  function eventStepCompactPresentation(event) {
    const notes = event?.notes || [];
    const strings = notes.map((note) => note.string);
    const frets = Array.from(new Set(notes.map((note) => note.fret)));
    const controls = Array.from(new Set(notes.flatMap((note) => note.changes || [])));
    return {
      note: event?.resolvedPitch || event?.resolvedNote || "Note",
      position: [
        `S${strings.join("+")}`,
        `F${frets.join("+")}`,
        controls.length ? controls.join("+") : "Open"
      ].join(" · ")
    };
  }

  function humanList(values) {
    const items = Array.from(new Set(values.filter((value) => value !== null && value !== undefined && value !== "")));
    if (items.length < 2) return String(items[0] ?? "");
    if (items.length === 2) return `${items[0]} & ${items[1]}`;
    return `${items.slice(0, -1).join(", ")} & ${items.at(-1)}`;
  }

  function readableEventPosition(event) {
    const notes = event?.notes || [];
    const strings = notes.map((note) => Number(note.string)).filter(Number.isInteger).sort((a, b) => a - b);
    const frets = notes.map((note) => Number(note.fret)).filter(Number.isInteger);
    const controls = eventPerformanceControlLabels(event);
    const stringLabel = `${strings.length === 1 ? "String" : "Strings"} ${humanList(strings)}`;
    const fretLabel = frets.length ? `Fret ${humanList(Array.from(new Set(frets)))}` : "";
    return [stringLabel, fretLabel, controls.length ? controls.join("+") : "Open"].filter(Boolean).join(" · ");
  }

  function fretboardPlayingContext(event) {
    const chord = String(event?.harmonySymbol || event?.chord || "").trim();
    const strings = eventStrings(event);
    const controls = eventPerformanceControlLabels(event);
    const article = /^[AEF]/i.test(chord) ? "AN" : "A";
    return {
      chord: chord ? `PLAYING OVER ${article} ${chord.toUpperCase()} CHORD` : "",
      action: strings.length
        ? `${strings.length === 1 ? "string" : "strings"} ${strings.join("–")} · ${controls.length ? controls.join("+") : "no pedals"}`
        : ""
    };
  }

  function hasChordContext(events) {
    return (events || []).some((event) => String(event?.harmonySymbol || event?.chord || "").trim());
  }

  function routeButtonLabel(route) {
    return route?.label || (route?.recommended ? "Recommended harmony" : "Arrangement");
  }

  function arrangementEngineStatus(modelMetadata = {}) {
    if (modelMetadata.privateBeta === true && modelMetadata.rankerEnabled === true) {
      const modelId = String(modelMetadata.modelId || "unknown model");
      const exampleCount = Number(modelMetadata.exampleCount || 0);
      const changed = Number(modelMetadata.comparisonChangedEvents);
      const total = Number(modelMetadata.comparisonEventCount);
      const comparison = Number.isInteger(changed) && Number.isInteger(total) && total > 0
        ? ` It changed ${changed} of ${total} positions compared with the deterministic route.`
        : "";
      const examples = exampleCount > 0 ? ` · ${exampleCount} reviewed choices` : "";
      return `Private learned beta · ${modelId}${examples}.${comparison} Pitch, register, and mechanics still pass the verified E9 rules. Score-image reading remains a separate reviewed step.`;
    }
    if (modelMetadata.rankerEnabled === true) {
      return "Arrangement method: trained Amazing Tablature ranker with verified E9 rules.";
    }
    return "Arrangement method: verified E9 rules. Imported score images are reviewed before arranging.";
  }

  function arrangementPolicySummary(exercise = {}) {
    const contract = exercise.arrangementContract || {};
    const request = contract.request || {};
    const route = (exercise.routes || []).find((item) => item.id === contract.recommendedRouteId)
      || (exercise.routes || []).find((item) => item.recommended)
      || (exercise.routes || [])[0];
    if (!route) return "";
    const voiceLabels = {
      single: "single note",
      two_voice: "two note",
      three_voice: "three note",
      mixed: "mixed voice"
    };
    const movementLabels = {
      best_fit: "best fit",
      slides: "slides",
      pedal_lever: "pedal & lever movement",
      compact_pocket: "a compact pocket",
      clean_repick: "clean repicks"
    };
    const requestedVoice = voiceLabels[request.voiceMode] || request.voiceMode || "mixed voice";
    const realizedVoice = voiceLabels[route.voiceMode] || route.voiceMode || requestedVoice;
    const movement = movementLabels[request.movementMode] || request.movementMode || "best fit";
    const fallback = contract.requestedVoiceModeAvailable === false
      ? ` Requested ${requestedVoice}; the closest validated result is ${realizedVoice}.`
      : "";
    const alternatives = Array.isArray(contract.alternatives) ? contract.alternatives.length : 0;
    return `Recommended: ${realizedVoice} with ${movement}. ${alternatives} materially different ${alternatives === 1 ? "alternative" : "alternatives"}.${fallback}`;
  }

  function numberList(value) {
    return Array.from(new Set((Array.isArray(value) ? value : [])
      .map(Number)
      .filter((item) => Number.isInteger(item) && item >= 1 && item <= 10)))
      .sort((a, b) => a - b);
  }

  function eventStrings(event) {
    return numberList((event?.notes || []).map((note) => note.string));
  }

  function eventFret(event, fallback = null) {
    const fret = Number(event?.notes?.[0]?.fret ?? fallback);
    return Number.isInteger(fret) ? fret : null;
  }

  function eventPerformanceControls(event, fallback = []) {
    const explicit = Array.isArray(event?.performanceControls) ? event.performanceControls : [];
    const controls = explicit.length
      ? explicit
      : [...fallback, ...(event?.notes || []).flatMap((note) => note.changes || [])];
    const controlOrder = ["A", "B", "C", "E", "F", "V", "G", "D"];
    return Array.from(new Set(controls.map((control) => String(control || "").trim().toUpperCase()).filter(Boolean)))
      .sort((a, b) => {
        const aIndex = controlOrder.indexOf(a);
        const bIndex = controlOrder.indexOf(b);
        return (aIndex < 0 ? 99 : aIndex) - (bIndex < 0 ? 99 : bIndex) || a.localeCompare(b);
      });
  }

  function eventPerformanceControlLabels(event) {
    const explicit = Array.isArray(event?.performanceControlLabels) ? event.performanceControlLabels : [];
    return explicit.length ? explicit.map(String) : eventPerformanceControls(event);
  }

  function compactGripDescription(event, options = {}) {
    const strings = numberList(options.strings?.length ? options.strings : eventStrings(event));
    const fret = eventFret(event, options.fret);
    const hasControlOverride = Object.prototype.hasOwnProperty.call(options, "controls");
    const controls = hasControlOverride
      ? Array.from(new Set((options.controls || []).map(String).filter(Boolean)))
      : eventPerformanceControlLabels(event);
    const stringText = strings.length ? `${strings.length === 1 ? "string" : "strings"} ${humanList(strings)}` : "the shown strings";
    const fretText = fret === null ? "the shown fret" : `fret ${fret}`;
    return `${stringText} at ${fretText}${controls.length ? ` with ${controls.join("+")}` : " open"}`;
  }

  function transitionVoiceActions(transition) {
    const actions = Array.isArray(transition?.voiceActions) ? transition.voiceActions : [];
    return actions.flatMap((item) => {
      const string = Number(item?.string);
      const action = String(item?.action || "").trim().toLowerCase();
      return Number.isInteger(string) && action ? [{ string, action }] : [];
    });
  }

  function transitionSustainedStrings(transition) {
    const explicit = numberList(transition?.sustainedStrings);
    if (explicit.length) return explicit;
    const sustainedActions = new Set(["bar_slide", "pedal_glide", "lever_glide", "hold"]);
    const fromActions = numberList(transitionVoiceActions(transition)
      .filter((item) => sustainedActions.has(item.action))
      .map((item) => item.string));
    return fromActions.length ? fromActions : numberList(transition?.strings);
  }

  function transitionGlidingStrings(transition) {
    const glidingActions = new Set(["bar_slide", "pedal_glide", "lever_glide"]);
    const explicit = numberList(transitionVoiceActions(transition)
      .filter((item) => glidingActions.has(item.action))
      .map((item) => item.string));
    if (explicit.length) return explicit;
    return transitionSustainedStrings(transition);
  }

  function transitionControlAnnotation(transition) {
    const before = new Set(transition?.controlLabelsBefore || transition?.controlsBefore || []);
    const after = new Set(transition?.controlLabelsAfter || transition?.controlsAfter || []);
    const pressed = [...after].filter((control) => !before.has(control));
    const released = [...before].filter((control) => !after.has(control));
    const parts = [];
    if (pressed.length) parts.push(`press ${pressed.join("+")}`);
    if (released.length) parts.push(`release ${released.join("+")}`);
    return parts.join("; ");
  }

  function transitionScoreVoices(transition, sourceEvent, targetEvent) {
    const slidingStrings = numberList(transitionVoiceActions(transition)
      .filter((item) => item.action === "bar_slide")
      .map((item) => item.string));
    const strings = slidingStrings.length
      ? slidingStrings
      : (String(transition?.kind || "").toLowerCase() === "bar_slide" ? transitionSustainedStrings(transition) : []);
    return strings.flatMap((string) => {
      const sourceNote = (sourceEvent?.notes || []).find((note) => Number(note.string) === string);
      const targetNote = (targetEvent?.notes || []).find((note) => Number(note.string) === string);
      const fromPitchValue = mechanicalPitchForString(sourceEvent, string, sourceNote);
      const toPitchValue = mechanicalPitchForString(targetEvent, string, targetNote);
      if (!Number.isFinite(fromPitchValue) || !Number.isFinite(toPitchValue)) return [];
      const action = transitionVoiceActions(transition).find((item) => item.string === string)?.action || transition?.kind || "bar_slide";
      return [{ string, action, fromPitchValue, toPitchValue }];
    });
  }

  function transitionArrivalInstruction(transition) {
    const repicked = numberList(transition?.repickedStrings);
    const released = numberList(transition?.releasedStrings);
    const fromStrings = numberList(transition?.fromStrings);
    const toStrings = numberList(transition?.toStrings);
    const added = toStrings.filter((string) => !fromStrings.includes(string) && !repicked.includes(string));
    const melodyOnly = String(transition?.scope || "").toLowerCase() === "melody_voice";
    const parts = [];
    if (released.length) {
      const strings = `${released.length === 1 ? "string" : "strings"} ${humanList(released)}`;
      parts.push(melodyOnly ? `block and release ${strings} before the slide` : `release ${strings} at the arrival`);
    }
    if (added.length) parts.push(`add ${added.length === 1 ? "string" : "strings"} ${humanList(added)} at the arrival`);
    if (repicked.length) parts.push(`repick ${repicked.length === 1 ? "string" : "strings"} ${humanList(repicked)} at the arrival`);
    return parts.join("; ");
  }

  function transitionChoreography(transition, sourceEvent, targetEvent) {
    if (!transition) return "";
    const fromStrings = numberList(transition.fromStrings?.length ? transition.fromStrings : eventStrings(sourceEvent));
    const toStrings = numberList(transition.toStrings?.length ? transition.toStrings : eventStrings(targetEvent));
    const source = compactGripDescription(sourceEvent, {
      strings: fromStrings,
      fret: transition.fromFret,
      controls: transition.controlLabelsBefore || transition.controlsBefore
    });
    const destination = compactGripDescription(targetEvent, {
      strings: toStrings,
      fret: transition.toFret,
      controls: transition.controlLabelsAfter || transition.controlsAfter
    });
    const sustained = transitionSustainedStrings(transition);
    const arrival = transitionArrivalInstruction(transition);
    const kind = String(transition.kind || "").toLowerCase();
    const scope = String(transition.scope || "").toLowerCase();
    const controlAction = transitionControlAnnotation(transition);
    let movement = "";
    if (kind === "bar_slide") {
      const fromFret = Number.isInteger(Number(transition.fromFret)) ? Number(transition.fromFret) : eventFret(sourceEvent) ?? "the starting fret";
      const toFret = Number.isInteger(Number(transition.toFret)) ? Number(transition.toFret) : eventFret(targetEvent) ?? "the destination fret";
      if (scope === "full_grip" && sustained.length >= 2) {
        const ringing = sustained.length === 2 ? "keep both strings ringing" : `keep all ${sustained.length === 3 ? "three" : sustained.length} strings ringing`;
        movement = `Attack the full grip: ${source}; ${ringing}; slide the grip from fret ${fromFret} to fret ${toFret}${controlAction ? `; ${controlAction} at the arrival` : ""}; land on ${destination}`;
      } else {
        const subject = sustained.length ? `${sustained.length === 1 ? "string" : "strings"} ${humanList(sustained)}` : "the melody voice";
        movement = `Pick ${source}; slide ${subject} from fret ${fromFret} to fret ${toFret}${controlAction ? `; ${controlAction} at the arrival` : ""}; land on ${destination}`;
      }
    } else if (kind === "pedal_glide" || kind === "lever_glide") {
      movement = `Pick ${source}; hold fret ${Number.isInteger(Number(transition.toFret)) ? Number(transition.toFret) : eventFret(targetEvent) ?? "in place"}${controlAction ? ` and ${controlAction}` : " for the control change"}; land on ${destination}`;
    } else {
      movement = `Pick ${source}; move to ${destination}`;
    }
    return `${movement}${arrival ? `; ${arrival}` : ""}.`;
  }

  function eventPlaybackVoices(event) {
    const topPitch = Number(event?.pitchValue);
    const voices = (event?.notes || []).flatMap((note) => {
      const string = Number(note?.string);
      const pitchValue = mechanicalPitchForString(event, string, note);
      if (!Number.isInteger(string) || !Number.isFinite(pitchValue)) return [];
      return [{ string, pitchValue, topVoice: Number.isFinite(topPitch) && pitchValue === topPitch }];
    });
    if (voices.length) return voices;
    return Number.isFinite(topPitch) ? [{ string: null, pitchValue: topPitch, topVoice: true }] : [];
  }

  function transitionPlaybackPlan(event, nextEvent, outgoingTransition = null, incomingTransition = null) {
    const incomingStrings = new Set(transitionSustainedStrings(incomingTransition));
    const outgoingStrings = new Set(transitionSustainedStrings(outgoingTransition));
    const targetByString = new Map(eventPlaybackVoices(nextEvent)
      .filter((voice) => Number.isInteger(voice.string))
      .map((voice) => [voice.string, voice]));
    return eventPlaybackVoices(event).map((voice) => {
      if (Number.isInteger(voice.string) && incomingStrings.has(voice.string)) {
        return { ...voice, action: "continue" };
      }
      const target = Number.isInteger(voice.string) && outgoingStrings.has(voice.string)
        ? targetByString.get(voice.string)
        : null;
      if (target) {
        return {
          ...voice,
          action: target.pitchValue === voice.pitchValue ? "sustain" : "glide",
          toPitchValue: target.pitchValue
        };
      }
      return { ...voice, action: "attack" };
    });
  }

  function gripRationale(event) {
    if (!event) return null;
    const selectionReason = String(event.selectionReason || "").trim();
    const patternFamily = String(event.patternFamily || "").trim();
    const canonicalGrip = String(event.canonicalGrip || "").trim();
    const chord = String(event.harmonySymbol || event.chord || "").trim();
    if (!selectionReason && !patternFamily && !canonicalGrip) return null;
    return {
      reason: selectionReason || "This position keeps the melody in the current harmonic pocket with practical string and control movement.",
      pocket: patternFamily,
      grip: canonicalGrip,
      chord
    };
  }

  function supportedScientificOctave(value) {
    const octave = Number(value);
    return Number.isInteger(octave) && octave >= 2 && octave <= 6 ? octave : null;
  }

  function scientificOctaveForEvent(event) {
    const resolvedPitch = typeof event?.resolvedPitch === "string" ? event.resolvedPitch.trim() : "";
    const match = resolvedPitch.match(/^[A-Ga-g](?:#|b)?(-?\d+)$/);
    if (match) return supportedScientificOctave(match[1]);
    const pitchValue = Number(event?.pitchValue);
    if (!Number.isFinite(pitchValue)) return null;
    return supportedScientificOctave(Math.floor(pitchValue / 12) - 1);
  }

  function scientificOctaveLabel(octave) {
    const supported = supportedScientificOctave(octave);
    return supported === null ? "" : `Octave ${supported} — C${supported} through B${supported}`;
  }

  function scientificOctaveForTabNote(note) {
    const pitchValue = pitchValueForTabNote(note);
    if (!Number.isFinite(pitchValue)) return null;
    return supportedScientificOctave(Math.floor(pitchValue / 12) - 1);
  }

  function pitchValueForTabNote(note) {
    const stringNumber = Number(note?.string);
    const fret = Number(note?.fret);
    const openPitch = E9_OPEN_PITCHES[stringNumber];
    if (!Number.isInteger(stringNumber) || !Number.isInteger(fret) || !Number.isFinite(openPitch)) return null;
    const changeDelta = (note?.changes || []).reduce(
      (sum, change) => sum + (E9_CHANGE_DELTAS[String(change).toUpperCase()]?.[stringNumber] || 0),
      0
    );
    return openPitch + fret + changeDelta;
  }

  function mechanicalPitchForString(event, stringNumber, fallbackNote = null) {
    const explicit = Number(event?.mechanicalPitchesByString?.[String(stringNumber)]);
    return Number.isFinite(explicit) ? explicit : pitchValueForTabNote(fallbackNote);
  }

  function scorePitchesForEvent(event) {
    const mechanicalPitches = (event?.notes || [])
      .map((note) => mechanicalPitchForString(event, Number(note.string), note))
      .filter(Number.isFinite);
    const melodyPitch = Number(event?.pitchValue);
    const pitches = mechanicalPitches.length ? mechanicalPitches : (Number.isFinite(melodyPitch) ? [melodyPitch] : []);
    if (Number.isFinite(melodyPitch) && !pitches.includes(melodyPitch)) pitches.push(melodyPitch);
    return Array.from(new Set(pitches)).sort((a, b) => a - b);
  }

  function positionsWithScientificOctaves(positions, events) {
    const eventByPosition = new Map((events || []).map((event) => [event.renderablePositionId, event]));
    return (positions || []).map((position) => {
      const event = eventByPosition.get(position.id);
      if (!event) return position;
      const scientificOctavesByString = Object.fromEntries((event.notes || []).flatMap((note) => {
        const pitchValue = mechanicalPitchForString(event, Number(note.string), note);
        const octave = Number.isFinite(pitchValue) ? supportedScientificOctave(Math.floor(pitchValue / 12) - 1) : null;
        return octave === null ? [] : [[String(note.string), octave]];
      }));
      const melodyLabel = String(event.resolvedPitch || event.resolvedNote || "").trim();
      const stringActionLabels = (event.notes || []).map((note) => ({
        string: note.string,
        label: `${note.string}${Array.from(new Set((note.changeLabels || note.changes || []).map(String))).join("+")}`
      }));
      return {
        ...position,
        ...(melodyLabel ? { label: melodyLabel, role: `Melody note ${event.step || ""}`.trim() } : {}),
        scientificOctavesByString,
        stringActionLabels
      };
    });
  }

  function melodyFretboardOptions(fretboard, events, activeEventIndex = 0, displayOptions = {}) {
    const positioned = positionsWithScientificOctaves(fretboard.positions, events);
    const activeEvent = (events || [])[Math.max(0, Math.min(Number(activeEventIndex) || 0, Math.max(0, (events || []).length - 1)))];
    const activePositionId = activeEvent?.renderablePositionId;
    const activePositions = activePositionId
      ? positioned.filter((position) => position.id === activePositionId)
      : positioned.slice(0, 1);
    return {
      maxFret: fretboard.maxFret,
      stringCount: fretboard.stringCount,
      tuningLabels: fretboard.tuningLabels,
      openPitchValues: fretboard.openPitchValues || E9_OPEN_PITCHES,
      positions: activePositions,
      highlights: fretboard.highlights || [],
      legend: fretboard.legend,
      query: fretboard.query,
      hideFilterControls: true,
      hidePositionTools: true,
      hideLegend: true,
      showHighlightLabels: displayOptions.showOctaveLabels === true,
      showStringActionLabels: displayOptions.showStringLabels === true,
      stringActionLabelMode: "all",
      showScientificOctaveOverlay: true
    };
  }

  function printableLessonTitle(exercise) {
    const materialTitle = String(exercise?.material?.song || "").trim();
    const lessonTitle = String(exercise?.title || "").trim();
    const title = materialTitle || lessonTitle || "E9 tablature";
    return title
      .replace(/\s+[—-]\s+(?:Complete|Section\s+\d+)\s+E9\s+lesson$/i, "")
      .trim() || "E9 tablature";
  }

  function preferredStudioRoute(exercise, preferredHarmonyType = "") {
    const routes = exercise?.routes || [];
    return routes.find((route) => route.harmonyType === preferredHarmonyType)
      || routes.find((route) => route.harmonyType === "mixed_arrangement")
      || routes.find((route) => route.id === exercise?.selectedRouteId)
      || routes[0]
      || null;
  }

  function tabPositionSignature(event = {}) {
    if (event.rest) return "rest";
    return JSON.stringify((event.notes || []).map((note) => [
      Number(note.string),
      Number(note.fret),
      [...(note.changes || [])].map(String).sort()
    ]));
  }

  function changedTabPositionCount(previousRoute, nextRoute) {
    const previous = previousRoute?.events || [];
    const next = nextRoute?.events || [];
    const total = Math.max(previous.length, next.length);
    let changed = 0;
    for (let index = 0; index < total; index += 1) {
      if (tabPositionSignature(previous[index]) !== tabPositionSignature(next[index])) changed += 1;
    }
    return { changed, total };
  }

  function styleImpactSummary(previousRoute, nextRoute, styleLabel = "This style") {
    const { changed, total } = changedTabPositionCount(previousRoute, nextRoute);
    if (!total) return "";
    if (!changed) return `${styleLabel} uses the same Recommended tab for this melody.`;
    return `${styleLabel} changed ${changed} of ${total} Recommended tab positions.`;
  }

  const api = {
    MAX_EVENTS_PER_SECTION,
    TASKS,
    STARTING_POINTS,
    KEY_NOTES,
    PRESETS,
    savedE9TargetCopedent,
    createInitialState,
    startingPointForKind,
    entryChoicePresentation,
    parsePhraseInput,
    parseSimpleTab,
    parseSimpleTabEvents,
    parsePhraseEvents,
    resolvePhrasePreview,
    noteAtFret,
    sectionCount,
    validateTokens,
    reorderToken,
    buildMelodyRequest,
    youtubeVideoId,
    referenceEmbedUrl,
    fileSourceType,
    parseAudioTimecode,
    formatAudioTimecode,
    audioWindowBounds,
    frequencyToMidi,
    frequencyToMidiFloat,
    autoCorrelate,
    quantizeTranscriptionBeats,
    transcribePitchSamples,
    pitchSamplesFromPcm,
    createAudioTranscriptionDraft,
    chordPitchValues,
    eventStepPresentation,
    eventStepCompactPresentation,
    readableEventPosition,
    fretboardPlayingContext,
    hasChordContext,
    routeButtonLabel,
    arrangementEngineStatus,
    eventPerformanceControls,
    transitionSustainedStrings,
    transitionGlidingStrings,
    transitionControlAnnotation,
    transitionScoreVoices,
    transitionChoreography,
    eventPlaybackVoices,
    transitionPlaybackPlan,
    gripRationale,
    scientificOctaveForEvent,
    scientificOctaveLabel,
    scientificOctaveForTabNote,
    pitchValueForTabNote,
    scorePitchesForEvent,
    positionsWithScientificOctaves,
    melodyFretboardOptions,
    printableLessonTitle,
    preferredStudioRoute,
    tabPositionSignature,
    changedTabPositionCount,
    styleImpactSummary,
    arrangementPolicySummary
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  global.STEEL_RAG_MELODY_STUDIO = api;

  if (!global.document) return;

  const doc = global.document;
  const $ = (selector) => doc.querySelector(selector);
  const answerUi = typeof STEEL_RAG_ANSWER_UI !== "undefined"
    ? STEEL_RAG_ANSWER_UI
    : global.STEEL_RAG_ANSWER_UI;
  const scoreUi = global.STEEL_RAG_MELODY_SCORE;
  const studioParams = new URLSearchParams(global.location.search);
  let state = createInitialState(studioParams.get("kind") || "user_melody");
  const activeCopedentContext = global.STEEL_RAG_COPEDENTS?.activeContext?.();
  state.targetCopedentId = studioParams.get("copedent") || activeCopedentContext?.profileId || state.targetCopedentId;
  state.voiceMode = studioParams.get("voice") || state.voiceMode;
  const legacyMovementByStyle = {
    vocal_steel: "slides",
    lever_driven: "pedal_lever",
    fixed_pocket: "compact_pocket",
    single_note_run: "clean_repick"
  };
  state.movementMode = studioParams.get("movement")
    || legacyMovementByStyle[studioParams.get("style")]
    || state.movementMode;
  if (studioParams.get("key")) {
    const requestedKey = studioParams.get("key");
    const normalizedKey = requestedKey.slice(0, 1).toUpperCase() + requestedKey.slice(1);
    if (KEY_NOTES[normalizedKey]) state.key = normalizedKey;
  }
  if (studioParams.get("notes")) {
    const chord = studioParams.get("chord") || "";
    state.tokens = parsePhraseEvents(studioParams.get("notes")).map((item) => (
      chord ? {...phraseItem(item), chord} : item
    ));
    state.workflowPhase = "review";
  }
  state.targetCopedent = studioParams.get("copedent") ? null : (activeCopedentContext?.profileSnapshot || savedE9TargetCopedent());
  let session = null;
  let catalogSongs = [];

  const elements = {
    hero: $(".studio-hero"),
    unavailable: $("#studio-unavailable"),
    unavailableTitle: $("#studio-unavailable-title"),
    unavailableCopy: $("#studio-unavailable-copy"),
    workflow: $("#studio-workflow"),
    phaseLabel: $("#studio-phase-label"),
    entryGuidance: $("#studio-entry-guidance"),
    replaceConfirmation: $("#studio-replace-confirmation"),
    replaceMessage: $("#studio-replace-message"),
    confirmReplace: $("#studio-confirm-replace"),
    keepMelody: $("#studio-keep-melody"),
    startChoices: Array.from(doc.querySelectorAll("[data-studio-start]")),
    inputPanels: Array.from(doc.querySelectorAll("[data-input-panel]")),
    sourceTreatmentButtons: Array.from(doc.querySelectorAll("[data-source-treatment]")),
    editor: $("#studio-editor"),
    materialFields: $("#studio-material-fields"),
    closeMaterial: $("#studio-close-material"),
    artist: $("#studio-artist"),
    song: $("#studio-song"),
    recording: $("#studio-recording"),
    section: $("#studio-section"),
    sourceUrl: $("#studio-source-url"),
    loopStart: $("#studio-loop-start"),
    loopEnd: $("#studio-loop-end"),
    loadReference: $("#studio-load-reference"),
    repeatReference: $("#studio-repeat-reference"),
    tapTempo: $("#studio-tap-tempo"),
    tempo: $("#studio-tempo"),
    youtubeFrame: $("#studio-youtube-frame"),
    externalReference: $("#studio-external-reference"),
    key: $("#studio-key"),
    contour: $("#studio-contour"),
    phraseInput: $("#studio-phrase-input"),
    sequence: $("#studio-sequence"),
    noteEditor: $("#studio-note-editor"),
    selectedNote: $("#studio-selected-note"),
    selectedPitch: $("#studio-selected-pitch"),
    registerValue: $("#studio-register-value"),
    octaveDown: $("#studio-octave-down"),
    octaveAuto: $("#studio-octave-auto"),
    octaveUp: $("#studio-octave-up"),
    noteEarlier: $("#studio-note-earlier"),
    noteLater: $("#studio-note-later"),
    noteRemove: $("#studio-note-remove"),
    sectionCount: $("#studio-section-count"),
    palette: $("#studio-palette"),
    presets: $("#studio-presets"),
    useExercise: $("#studio-use-exercise"),
    addRecording: $("#studio-add-recording"),
    paletteModeButtons: Array.from(doc.querySelectorAll("[data-palette-mode]")),
    presetButtons: Array.from(doc.querySelectorAll("[data-preset]")),
    error: $("#studio-error"),
    build: $("#studio-build"),
    scoreMeter: $("#studio-score-meter"),
    scorePickup: $("#studio-score-pickup"),
    scoreDuration: $("#studio-score-duration"),
    scorePartField: $("#studio-score-part-field"),
    scorePart: $("#studio-score-part"),
    insertRest: $("#studio-insert-rest"),
    addMeasure: $("#studio-add-measure"),
    removeMeasure: $("#studio-remove-measure"),
    scoreUndo: $("#studio-score-undo"),
    scoreRedo: $("#studio-score-redo"),
    scoreKeyboard: $("#studio-score-keyboard"),
    scoreCanvas: $("#studio-score-canvas"),
    scoreSelection: $("#studio-score-selection"),
    scoreSelectionSummary: $("#studio-score-selection-summary"),
    scoreDeleteSelected: $("#studio-score-delete-selected"),
    scorePreviousNote: $("#studio-score-previous-note"),
    scoreNextNote: $("#studio-score-next-note"),
    scoreStatus: $("#studio-score-status"),
    scoreEventEditor: $("#studio-score-event-editor"),
    scorePitch: $("#studio-score-pitch"),
    scoreConfidence: $("#studio-score-confidence"),
    eventDuration: $("#studio-event-duration"),
    scoreChord: $("#studio-score-chord"),
    scoreLyric: $("#studio-score-lyric"),
    scoreTie: $("#studio-score-tie"),
    scoreArticulation: $("#studio-score-articulation"),
    scoreRemove: $("#studio-score-remove-note"),
    scoreClearMeasure: $("#studio-score-clear-measure"),
    scoreDuplicate: $("#studio-score-duplicate"),
    scoreTransposeDown: $("#studio-score-transpose-down"),
    scoreTransposeUp: $("#studio-score-transpose-up"),
    scoreOctaveDown: $("#studio-score-octave-down"),
    scoreOctaveUp: $("#studio-score-octave-up"),
    scorePlay: $("#studio-score-play"),
    scoreDownload: $("#studio-score-download"),
    scoreArrange: $("#studio-score-arrange"),
    scoreArrangeStatus: $("#studio-score-arrange-status"),
    scorePanel: $("#studio-score-panel"),
    scoreHeading: $("#studio-score-heading"),
    scoreGuidance: $("#studio-score-guidance"),
    scoreActionTitle: $("#studio-score-action-title"),
    scoreActionHelp: $("#studio-score-action-help"),
    scoreEditToggle: $("#studio-score-edit-toggle"),
    scoreWarnings: $("#studio-score-warnings"),
    scoreSource: $("#studio-score-source"),
    scoreSourceImage: $("#studio-score-source-image"),
    importFile: $("#studio-import-file"),
    importButton: $("#studio-import-button"),
    importStatus: $("#studio-import-status"),
    importPreview: $("#studio-import-preview"),
    microphoneStart: $("#studio-microphone-start"),
    microphoneStop: $("#studio-microphone-stop"),
    microphoneStatus: $("#studio-microphone-status"),
    audioFile: $("#studio-audio-file"),
    audioFileControls: $("#studio-audio-file-controls"),
    audioAnalyze: $("#studio-audio-analyze"),
    audioPreview: $("#studio-audio-preview"),
    audioStart: $("#studio-audio-start"),
    audioLength: $("#studio-audio-length"),
    audioUsePlayhead: $("#studio-audio-use-playhead"),
    transcriptionTempo: $("#studio-transcription-tempo"),
    catalogGrid: $("#studio-catalog-grid"),
    catalogStatus: $("#studio-catalog-status"),
    catalogSearch: $("#studio-catalog-search"),
    catalogDifficulty: $("#studio-catalog-difficulty"),
    catalogMeter: $("#studio-catalog-meter"),
    catalogFeel: $("#studio-catalog-feel"),
    result: $("#studio-result"),
    resultTitle: $("#studio-result-title"),
    resultSource: $("#studio-result-source"),
    engineStatus: $("#studio-engine-status"),
    resultScoreStage: $("#studio-result-score-stage"),
    resultScore: $("#studio-result-score"),
    scoreLyricCue: $("#studio-score-lyric-cue"),
    scoreLyricText: $("#studio-score-lyric-text"),
    sectionNavigation: $("#studio-section-navigation"),
    sectionPrevious: $("#studio-section-previous"),
    sectionStatus: $("#studio-section-status"),
    sectionNext: $("#studio-section-next"),
    practice: $("#studio-practice"),
    practicePlay: $("#studio-practice-play"),
    practiceStop: $("#studio-practice-stop"),
    practiceTempo: $("#studio-practice-tempo"),
    practiceTempoValue: $("#studio-practice-tempo-value"),
    practiceCountIn: $("#studio-practice-count-in"),
    practiceChords: $("#studio-practice-chords"),
    practiceChordOption: $("#studio-practice-chord-option"),
    practiceLoopPanel: $("#studio-practice-loop-panel"),
    practiceLoopMeasure: $("#studio-practice-loop-measure"),
    practiceLoopStart: $("#studio-practice-loop-start"),
    practiceLoopEnd: $("#studio-practice-loop-end"),
    practiceLoopClear: $("#studio-practice-loop-clear"),
    practiceLoopStatus: $("#studio-practice-loop-status"),
    printTab: $("#studio-print-tab"),
    printTitle: $("#studio-print-title"),
    printRoute: $("#studio-print-route"),
    arrangementChoices: $("#studio-arrangement-choices"),
    routeTabs: $("#studio-route-tabs"),
    voiceMode: $("#studio-voice-mode"),
    movementMode: $("#studio-movement-mode"),
    arrangementPolicySummary: $("#studio-arrangement-policy-summary"),
    sourceNeeded: $("#studio-source-needed"),
    fretboard: $("#studio-fretboard"),
    fretboardPlayingContext: $("#studio-fretboard-playing-context"),
    fretboardChordContext: $("#studio-fretboard-chord-context"),
    fretboardActionContext: $("#studio-fretboard-action-context"),
    octaveMapControls: $("#studio-octave-map-controls"),
    octaveToggle: $("#studio-octave-toggle"),
    stringLabelToggle: $("#studio-string-label-toggle"),
    octaveLabelToggle: $("#studio-octave-label-toggle"),
    octaveGuide: $("#studio-octave-guide"),
    transport: $("#studio-transport"),
    previous: $("#studio-previous"),
    next: $("#studio-next"),
    eventStrip: $("#studio-event-strip"),
    gripRationale: $("#studio-grip-rationale"),
    gripReason: $("#studio-grip-reason"),
    gripFacts: $("#studio-grip-facts"),
    tab: $("#studio-tab"),
    tabCode: $("#studio-tab-code"),
    tabAlternatives: $("#studio-tab-alternatives"),
    tabAlternativesHeading: $("#studio-tab-alternatives-heading"),
    tabAlternativesSummary: $("#studio-tab-alternatives-summary"),
    tabAlternativesList: $("#studio-tab-alternatives-list"),
    tabAlternativesNote: $("#studio-tab-alternatives-note"),
    tabAlternativesClose: $("#studio-tab-alternatives-close"),
    transitionKey: $("#studio-transition-key"),
    wholeSongTab: $("#studio-whole-song-tab"),
    wholeSongTabCode: $("#studio-whole-song-tab-code"),
    continueButton: $("#studio-continue"),
    editTop: $("#studio-edit-top"),
    edit: $("#studio-edit"),
  };

  function currentTask() {
    return TASKS[state.kind] || null;
  }

  function readAccessRole() {
    return answerUi.normalizeAccessRole(new URLSearchParams(global.location.search).get("access"));
  }

  function clearMaterial() {
    state.artist = "";
    state.song = "";
    state.recording = "";
    state.section = "";
    state.sourceUrl = "";
    [elements.artist, elements.song, elements.recording, elements.section, elements.sourceUrl].forEach((input) => {
      input.value = "";
    });
  }

  function entryPathForMethod(method) {
    return ["song", "phrase", "score", "microphone", "import", "catalog"].includes(method) ? method : "phrase";
  }

  function hasMelodyContent() {
    return Boolean(
      state.tokens.length
      || state.scoreDraft?.score?.melody?.length
      || state.sourceAudioUrl
      || elements.importFile?.files?.length
    );
  }

  function hasMaterialDetails() {
    return [elements.artist, elements.song, elements.recording, elements.section, elements.sourceUrl]
      .some((input) => Boolean(input?.value?.trim()));
  }

  function clearMelodyDraft() {
    clearTransientDraft();
    state.tokens = [];
    state.selectedPhraseIndex = 0;
    state.scoreDraft = null;
    state.scoreEditingEnabled = true;
    state.scoreSelectedIndex = -1;
    state.scoreHistory = [];
    state.scoreFuture = [];
    state.importParts = [];
    state.importSelectedPart = "";
    elements.phraseInput.value = "";
    elements.importFile.value = "";
    elements.importStatus.textContent = "";
    elements.microphoneStatus.textContent = "Ready for up to 15 seconds.";
    elements.audioFileControls.hidden = true;
    showError("");
  }

  function syncStateFromFields() {
    state.key = elements.key.value;
    state.contourMode = elements.contour.value;
    const parsed = parsePhraseEvents(elements.phraseInput.value);
    const previous = state.tokens;
    state.tokens = parsed.map((item, index) => ({
      ...item,
      direction: previous[index]?.direction || item.direction || "auto",
      octaveShift: previous[index]?.octaveShift || item.octaveShift || 0
    }));
    if (currentTask()?.needsMaterial) {
      state.artist = elements.artist.value.trim();
      state.song = elements.song.value.trim();
      state.recording = elements.recording.value.trim();
      state.section = elements.section.value.trim();
      state.sourceUrl = elements.sourceUrl.value.trim();
    } else {
      clearMaterial();
    }
  }

  function setTokens(tokens) {
    state.tokens = (tokens || []).map(phraseItem).filter((item) => phraseItemLabel(item));
    state.selectedPhraseIndex = Math.max(0, Math.min(state.selectedPhraseIndex || 0, state.tokens.length - 1));
    elements.phraseInput.value = state.tokens.some((item) => Number.isInteger(item.string))
      ? state.tokens.map(phraseItemLabel).join("\n")
      : state.tokens.map(phraseItemLabel).join(" ");
    renderPhraseBuilder();
    renderStartingPoint();
  }

  function renderPalette() {
    const values = state.paletteMode === "notes" ? KEY_NOTES[state.key] : ["1", "2", "3", "4", "5", "6", "7"];
    elements.palette.replaceChildren();
    values.forEach((value) => {
      const button = doc.createElement("button");
      button.type = "button";
      button.className = "palette-note";
      button.textContent = value;
      button.setAttribute("aria-label", `Add ${value} to phrase`);
      button.addEventListener("click", () => setTokens([...state.tokens, phraseItem(value)]));
      elements.palette.appendChild(button);
    });
    elements.paletteModeButtons.forEach((button) => {
      const selected = button.dataset.paletteMode === state.paletteMode;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
  }

  function renderPhraseBuilder() {
    elements.sequence.replaceChildren();
    if (!state.tokens.length) {
      const empty = doc.createElement("p");
      empty.className = "sequence-empty";
      empty.textContent = "Your phrase will appear here as you type or choose notes.";
      elements.sequence.appendChild(empty);
    }
    const previews = resolvePhrasePreview(state.tokens, state.key, state.contourMode);
    state.tokens.forEach((raw, index) => {
      const token = phraseItem(raw);
      const tokenLabel = phraseItemLabel(token);
      const chip = doc.createElement("button");
      chip.type = "button";
      chip.className = "sequence-chip";
      chip.classList.toggle("is-selected", index === state.selectedPhraseIndex);
      chip.setAttribute("aria-pressed", String(index === state.selectedPhraseIndex));
      chip.setAttribute("aria-label", `Select ${tokenLabel}, ${previews[index]?.pitch || "unresolved pitch"}`);
      chip.dataset.sequenceIndex = String(index);
      const label = doc.createElement("strong");
      label.textContent = tokenLabel;
      const pitch = doc.createElement("span");
      pitch.className = "sequence-pitch";
      pitch.textContent = previews[index]?.pitch || "";
      chip.addEventListener("click", () => {
        state.selectedPhraseIndex = index;
        renderPhraseBuilder();
      });
      chip.append(label, pitch);
      elements.sequence.appendChild(chip);
    });
    const selected = state.tokens[state.selectedPhraseIndex];
    elements.noteEditor.hidden = !selected;
    if (selected) {
      const selectedItem = phraseItem(selected);
      elements.selectedNote.textContent = `Selected: ${phraseItemLabel(selectedItem)}`;
      elements.selectedPitch.textContent = previews[state.selectedPhraseIndex]?.pitch || "";
      const literal = Number.isInteger(selectedItem.string) && Number.isInteger(selectedItem.fret);
      const preview = previews[state.selectedPhraseIndex];
      const shift = Number(selectedItem.octaveShift || 0);
      const octave = scientificOctaveForEvent({ resolvedPitch: preview?.pitch, pitchValue: preview?.pitchValue });
      const shiftLabel = shift === 0 ? "Automatic" : shift > 0 ? `+${shift} octave${shift === 1 ? "" : "s"}` : `${shift} octave${shift === -1 ? "" : "s"}`;
      elements.registerValue.textContent = octave === null ? shiftLabel : `Octave ${octave} · ${shiftLabel}`;
      elements.octaveDown.disabled = literal || shift <= -2;
      elements.octaveAuto.disabled = literal || shift === 0;
      elements.octaveUp.disabled = literal || shift >= 2;
      const lowerPitch = Number.isFinite(preview?.pitchValue) ? pitchLabel(preview.pitchValue - 12) : "a lower octave";
      const upperPitch = Number.isFinite(preview?.pitchValue) ? pitchLabel(preview.pitchValue + 12) : "a higher octave";
      elements.octaveDown.setAttribute("aria-label", `Lower selected note from ${preview?.pitch || "its current pitch"} to ${lowerPitch}`);
      elements.octaveUp.setAttribute("aria-label", `Raise selected note from ${preview?.pitch || "its current pitch"} to ${upperPitch}`);
      elements.noteEarlier.disabled = state.selectedPhraseIndex === 0;
      elements.noteLater.disabled = state.selectedPhraseIndex === state.tokens.length - 1;
    }
    const count = sectionCount(state.tokens);
    elements.sectionCount.textContent = state.tokens.length
      ? `${state.tokens.length} notes · ${count} ${count === 1 ? "section" : "sections"}`
      : "Complete songbook melodies appear as one continuous score and tab.";
  }

  function renderEntryChoices(startingPoint = state.inputMethod || "phrase") {
    const entryPath = entryPathForMethod(startingPoint);
    const hasDraft = hasMelodyContent();
    elements.startChoices.forEach((button) => {
      const target = button.dataset.studioStart;
      const selected = target === entryPath;
      const replacing = hasDraft && target !== startingPoint;
      const presentation = entryChoicePresentation(target, {
        replacing,
        catalogCount: catalogSongs.length
      });
      const strong = button.querySelector("strong");
      const small = button.querySelector("small");
      if (strong) strong.textContent = presentation.label;
      if (small) small.textContent = presentation.help;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    elements.addRecording.textContent = state.showSourceDetails ? "Edit recording details" : "Add recording details";
  }

  function renderStartingPoint() {
    const startingPoint = state.inputMethod || startingPointForKind(state.kind);
    const entryPath = entryPathForMethod(startingPoint);
    const phaseLabels = { add: "Add melody", review: "Review melody", result: "E9 arrangement" };
    elements.phaseLabel.textContent = phaseLabels[state.workflowPhase] || phaseLabels.add;
    elements.entryGuidance.textContent = state.workflowPhase === "review"
      ? "Check the melody, make any corrections, then arrange it for E9."
      : entryPath === "microphone"
        ? "Record or choose a short, clear melody passage."
        : entryPath === "import"
          ? "Import music, then review the notes before arranging."
          : "Enter a short melody, then arrange it for E9.";
    renderEntryChoices(startingPoint);
    const replacementLabels = { song: "a Song Project", phrase: "typed notes", score: "the staff editor", microphone: "recorded or uploaded audio", import: "imported music", catalog: "an example song" };
    elements.replaceConfirmation.hidden = !state.pendingReplacement;
    elements.replaceMessage.textContent = state.pendingReplacement
      ? `Replace the current melody with ${replacementLabels[state.pendingReplacement] || "a different melody"}?`
      : "";
    elements.sourceTreatmentButtons.forEach((button) => {
      const selected = button.dataset.sourceTreatment === state.kind;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    elements.inputPanels.forEach((panel) => {
      const methods = String(panel.dataset.inputPanel || "").split(/\s+/).filter(Boolean);
      panel.hidden = !methods.includes(startingPoint);
    });
    elements.materialFields.hidden = !state.showSourceDetails || !["phrase", "score"].includes(startingPoint);
    elements.presets.hidden = state.kind !== "original_exercise";
    if (startingPoint === "score") renderScoreBuilder();
    if (startingPoint === "catalog" && !elements.catalogGrid.childElementCount) loadCatalog();
  }

  function selectStartingPoint(startingPoint, options = {}) {
    const previousStartingPoint = state.inputMethod || startingPointForKind(state.kind);
    if (!options.confirmed && hasMelodyContent() && startingPoint !== previousStartingPoint) {
      state.pendingReplacement = startingPoint;
      renderStartingPoint();
      elements.replaceConfirmation.scrollIntoView({ behavior: "smooth", block: "nearest" });
      return;
    }
    if (startingPoint === "song") {
      state.pendingReplacement = "";
      renderStartingPoint();
      global.STEEL_RAG_SONG_PROJECTS?.open?.();
      return;
    }
    if (startingPoint !== previousStartingPoint) clearMelodyDraft();
    state.pendingReplacement = "";
    const nextKind = STARTING_POINTS[startingPoint] || "user_melody";
    state.inputMethod = startingPoint;
    state.kind = state.showSourceDetails && hasMaterialDetails() && currentTask()?.needsMaterial ? state.kind : nextKind;
    state.workflowPhase = "add";
    if (startingPoint === "score") ensureScoreDraft();
    state.sectionNumber = 1;
    state.response = null;
    elements.result.hidden = true;
    elements.editor.hidden = false;
    renderStartingPoint();
    renderPalette();
    renderPhraseBuilder();
  }

  function selectSourceTreatment(kind) {
    if (!TASKS[kind]?.needsMaterial) return;
    state.kind = kind;
    state.showSourceDetails = true;
    state.sectionNumber = 1;
    state.response = null;
    elements.result.hidden = true;
    renderStartingPoint();
  }

  function questionForState() {
    const subject = [state.artist, state.song].filter(Boolean).join(" — ");
    return subject ? `${currentTask().question} Source: ${subject}.` : currentTask().question;
  }

  function showError(message) {
    elements.error.textContent = message || "";
    elements.error.hidden = !message;
  }

  function accessHeaders(json = false) {
    const headers = { Accept: "application/json" };
    if (json) headers["Content-Type"] = "application/json";
    const role = session?.role || readAccessRole();
    if (["beta_user", "admin"].includes(role)) headers["X-Steel-Rag-Dev-Access-Role"] = role;
    return headers;
  }

  function ensureScoreDraft() {
    if (!state.scoreDraft) state.scoreDraft = scoreUi.createDraft({ key: state.key, meter: elements.scoreMeter?.value || "4/4" });
    return state.scoreDraft;
  }

  function commitScoreDraft(next, selectedIndex = state.scoreSelectedIndex) {
    if (state.scoreDraft) state.scoreHistory.push(scoreUi.cloneDraft(state.scoreDraft));
    state.scoreHistory = state.scoreHistory.slice(-50);
    state.scoreFuture = [];
    state.scoreDraft = scoreUi.reflowDraft(next);
    state.scoreSelectedIndex = Math.max(-1, Math.min(selectedIndex, state.scoreDraft.score.melody.length - 1));
    state.workflowPhase = state.scoreDraft.score.melody.length ? "review" : "add";
    elements.phaseLabel.textContent = state.workflowPhase === "review" ? "Review melody" : "Add melody";
    elements.entryGuidance.textContent = state.workflowPhase === "review"
      ? "Check the melody, make any corrections, then arrange it for E9."
      : "Add notes to the staff, then arrange them for E9.";
    renderEntryChoices("score");
    renderScoreBuilder();
    accountActivity?.track("melody.edited", { dedupeKey: `score:${state.kind || "melody"}` });
  }

  function selectedScoreEvent() {
    return state.scoreDraft?.score?.melody?.[state.scoreSelectedIndex] || null;
  }

  function selectScoreEvent(index) {
    const events = state.scoreDraft?.score?.melody || [];
    if (!events.length) return;
    state.scoreSelectedIndex = Math.max(0, Math.min(Number(index) || 0, events.length - 1));
    renderScoreBuilder();
  }

  function removeSelectedScoreEvent() {
    if (!selectedScoreEvent()) return;
    const nextSelectedIndex = Math.max(0, state.scoreSelectedIndex - 1);
    commitScoreDraft(scoreUi.removeEvent(state.scoreDraft, state.scoreSelectedIndex), nextSelectedIndex);
  }

  function transposeWholeScore(semitones, message) {
    commitScoreDraft(scoreUi.transposeDraft(ensureScoreDraft(), semitones), state.scoreSelectedIndex);
    elements.scoreArrangeStatus.textContent = message;
  }

  function renderScoreKeyboard() {
    if (elements.scoreKeyboard.childElementCount) return;
    [60, 62, 64, 65, 67, 69, 71, 72].forEach((pitchValue) => {
      const button = doc.createElement("button");
      button.type = "button";
      button.className = "score-key";
      button.textContent = scoreUi.pitchLabel(pitchValue);
      button.setAttribute("aria-label", `Add ${scoreUi.pitchLabel(pitchValue)}`);
      button.addEventListener("click", () => addScoreEvent({ pitchValue, pitch: scoreUi.pitchLabel(pitchValue) }));
      elements.scoreKeyboard.appendChild(button);
    });
  }

  function renderScoreBuilder() {
    if (!scoreUi || !elements.scoreCanvas) return;
    const draft = ensureScoreDraft();
    const isCatalog = draft.source.type === "catalog";
    const isReviewOnly = isCatalog && !state.scoreEditingEnabled;
    elements.scorePanel.classList.toggle("is-review-only", isReviewOnly);
    elements.scoreHeading.textContent = isCatalog ? "Review songbook melody" : "Staff editor";
    elements.scoreGuidance.textContent = isCatalog
      ? "This reviewed melody is ready to arrange. Editing is available only when you choose it."
      : "Add and review one melody voice. Open the details only when you need them.";
    elements.scoreActionTitle.textContent = isCatalog ? `${draft.source.title || "Songbook melody"} is ready` : "Melody ready";
    elements.scoreActionHelp.textContent = isCatalog
      ? "Create the E9 arrangement now, or open note editing if the teaching melody needs a correction."
      : "Review the staff, then create your E9 arrangement.";
    elements.scoreEditToggle.hidden = !isCatalog;
    elements.scoreEditToggle.textContent = isReviewOnly ? "Edit melody notes" : "Done editing";
    elements.scoreEditToggle.setAttribute("aria-pressed", String(!isReviewOnly));
    renderScoreKeyboard();
    scoreUi.render(elements.scoreCanvas, draft, state.scoreSelectedIndex, selectScoreEvent);
    const event = selectedScoreEvent();
    elements.scoreEventEditor.hidden = !event;
    elements.scoreSelection.hidden = !event;
    if (event) {
      const selectedNumber = state.scoreSelectedIndex + 1;
      const eventName = event.rest ? "Rest" : event.pitch;
      elements.scoreSelectionSummary.textContent = `Selected ${event.rest ? "rest" : "note"} ${selectedNumber} of ${draft.score.melody.length} · ${eventName} · measure ${event.measure}, beat ${event.beat}`;
      elements.scoreDeleteSelected.textContent = `Delete selected ${event.rest ? "rest" : "note"}`;
      elements.scorePreviousNote.disabled = state.scoreSelectedIndex <= 0;
      elements.scoreNextNote.disabled = state.scoreSelectedIndex >= draft.score.melody.length - 1;
      elements.scorePitch.value = event.rest ? "Rest" : event.pitch;
      elements.scorePitch.disabled = Boolean(event.rest);
      elements.scoreConfidence.textContent = event.rest
        ? "Estimated rest — adjust or remove it if the silence was intentional phrasing rather than a rest."
        : event.origin === "user_edit"
          ? "Confirmed by your edit."
          : `Estimated confidence: ${Math.round(Number(event.confidence || 0) * 100)}% — verify this pitch and duration.`;
      elements.eventDuration.value = String(event.durationBeats);
      elements.scoreChord.value = scoreUi.chordForEvent(draft, event);
      elements.scoreLyric.value = event.lyric || "";
      elements.scoreTie.value = event.tie || "";
      elements.scoreArticulation.value = event.articulation || "";
    } else {
      elements.scoreConfidence.textContent = "";
      elements.scoreSelectionSummary.textContent = "";
    }
    elements.scoreMeter.value = draft.score.meter;
    elements.scorePickup.value = String(draft.score.pickupBeats || 0);
    elements.scoreUndo.disabled = !state.scoreHistory.length;
    elements.scoreRedo.disabled = !state.scoreFuture.length;
    elements.scorePartField.hidden = !state.importParts.length;
    if (state.importParts.length) {
      elements.scorePart.replaceChildren(...state.importParts.map((part) => {
        const option = doc.createElement("option");
        option.value = String(part.id);
        option.textContent = `${part.name} (${part.eventCount} events)`;
        option.selected = String(part.id) === String(state.importSelectedPart);
        return option;
      }));
    }
    elements.scoreStatus.textContent = draft.score.melody.length
      ? `${draft.score.melody.length} of ${scoreUi.MAX_EVENTS} events · ${Math.max(...draft.score.melody.map((item) => item.measure), 1)} of ${scoreUi.MAX_MEASURES} measures · the amber note and selection bar show exactly what you are editing.`
      : "Choose a pitch, click the staff, or press A–G to add the first note.";
    const structureWarnings = scoreUi.draftWarnings(draft);
    const warnings = [...(draft.review?.warnings || []), ...structureWarnings];
    const unsupportedKey = !KEY_NOTES[draft.score.arrangementKey];
    elements.scoreWarnings.textContent = [...warnings, ...(unsupportedKey ? ["Choose a supported major key before arranging."] : [])].join(" ");
    elements.scoreWarnings.hidden = !elements.scoreWarnings.textContent;
    elements.scoreArrange.disabled = !draft.score.melody.some((item) => !item.rest) || unsupportedKey;
    elements.scoreArrange.textContent = draft.review.status === "confirmed" ? "Arrange for E9" : "Confirm and arrange for E9";
    elements.scoreSource.textContent = draft.source.type === "composed_in_studio" ? "User-created score" : `${draft.source.title || "Imported score"} · ${draft.review.status === "confirmed" ? "confirmed" : "review before arranging"}`;
    elements.scoreSourceImage.hidden = !state.sourceImageUrl;
    if (state.sourceImageUrl) elements.scoreSourceImage.src = state.sourceImageUrl;
  }

  function addScoreEvent(changes = {}) {
    const durationBeats = Number(elements.scoreDuration.value || 1);
    const draft = scoreUi.addEvent(ensureScoreDraft(), { durationBeats, ...changes });
    commitScoreDraft(draft, draft.score.melody.length - 1);
  }

  function updateSelectedScoreEvent(changes) {
    if (!selectedScoreEvent()) return;
    commitScoreDraft(scoreUi.updateEvent(state.scoreDraft, state.scoreSelectedIndex, changes), state.scoreSelectedIndex);
  }

  function restoreScoreHistory(direction) {
    const from = direction < 0 ? state.scoreHistory : state.scoreFuture;
    const to = direction < 0 ? state.scoreFuture : state.scoreHistory;
    if (!from.length) return;
    to.push(scoreUi.cloneDraft(state.scoreDraft));
    state.scoreDraft = from.pop();
    state.scoreSelectedIndex = Math.min(state.scoreSelectedIndex, state.scoreDraft.score.melody.length - 1);
    renderScoreBuilder();
  }

  function hydrateScoreDraft(draft, imageUrl = "") {
    if (!draft?.score?.melody) throw new Error("The import did not contain a readable melody.");
    state.scoreHistory = [];
    state.scoreFuture = [];
    state.scoreDraft = scoreUi.reflowDraft(draft);
    state.scoreEditingEnabled = draft.source?.type !== "catalog";
    state.importParts = Array.isArray(draft.parts) && draft.parts.length > 1 ? draft.parts : [];
    state.importSelectedPart = String(draft.selectedPartId ?? draft.selectedTrackIndex ?? state.importSelectedPart ?? "");
    state.scoreSelectedIndex = state.scoreDraft.score.melody.length ? 0 : -1;
    state.inputMethod = "score";
    state.workflowPhase = "review";
    state.kind = draft.source?.type === "catalog"
      ? "song_arrangement_lesson"
      : state.showSourceDetails && hasMaterialDetails() && currentTask()?.needsMaterial
        ? state.kind
        : "user_melody";
    state.key = KEY_NOTES[draft.score.arrangementKey] ? draft.score.arrangementKey : elements.key.value;
    elements.key.value = state.key;
    if (imageUrl) state.sourceImageUrl = imageUrl;
    renderStartingPoint();
    renderScoreBuilder();
  }

  function scoreDraftFromExercise(exercise) {
    const draft = scoreUi.createDraft({
      key: state.key,
      title: exercise?.title || "Melody lesson",
      sourceType: "manual_phrase",
      rightsLabel: "user_provided"
    });
    draft.score.melody = (exercise?.events || []).map((event, index) => ({
      id: event.id || `result-${index + 1}`,
      measure: event.measure || Math.floor(index / MAX_EVENTS_PER_SECTION) + 1,
      beat: event.beat || index % MAX_EVENTS_PER_SECTION + 1,
      durationBeats: event.durationBeats || 1,
      pitch: event.resolvedPitch || event.resolvedNote,
      pitchValue: event.pitchValue,
      pitches: scorePitchesForEvent(event),
      origin: event.origin || "source",
      tie: event.tie || "",
      lyric: event.lyric || "",
      articulation: event.articulation || ""
    })).filter((event) => Number.isFinite(Number(event.pitchValue)));
    let previousChord = "";
    (exercise?.events || []).forEach((event, index) => {
      const chord = String(event.harmonySymbol || event.chord || "").trim();
      if (chord && chord !== previousChord) {
        draft.score.harmony.push({ measure: event.measure || 1, beat: event.beat || index + 1, symbol: chord, basis: "source", confidence: 1 });
      }
      if (chord) previousChord = chord;
    });
    return draft;
  }

  function renderResultScore(exercise, route = null) {
    if (!scoreUi || !exercise?.events?.length) {
      elements.resultScoreStage.hidden = true;
      return;
    }
    elements.resultScoreStage.hidden = false;
    const eventStart = Number(exercise?.section?.eventStart || 0);
    const hasWholeScore = (state.scoreDraft?.score?.melody?.length || 0) > (exercise.events?.length || 0);
    const draft = hasWholeScore ? scoreUi.cloneDraft(state.scoreDraft) : scoreDraftFromExercise(exercise);
    const reviewedSections = state.scoreDraft?.score?.sections || [];
    if (!draft.score.sections?.length && reviewedSections.length) draft.score.sections = reviewedSections.map((section) => ({ ...section }));
    if (hasWholeScore) {
      (exercise.events || []).forEach((event, index) => {
        const target = draft.score.melody[eventStart + index];
        if (!target) return;
        target.pitch = event.resolvedPitch || event.resolvedNote || target.pitch;
        target.pitchValue = event.pitchValue ?? target.pitchValue;
        target.pitches = scorePitchesForEvent(event);
      });
    }
    const transitionByTarget = new Map((route?.transitions || []).map((transition) => [transition.toEventId, transition]));
    (exercise.events || []).forEach((event, index) => {
      const target = draft.score.melody[eventStart + index];
      const transition = transitionByTarget.get(event.id);
      if (target) target.transitionFromPrevious = transition ? {
        ...transition,
        scoreVoices: transitionScoreVoices(transition, exercise.events[index - 1], event),
        controlAnnotation: transitionControlAnnotation(transition)
      } : null;
    });
    (draft.score.sections || []).forEach((section) => {
      const label = String(section.label || "").trim();
      if (!label) return;
      const firstEvent = draft.score.melody.find((event) => !event.rest && Number(event.measure) >= Number(section.startMeasure) && Number(event.measure) <= Number(section.endMeasure));
      if (firstEvent && !firstEvent.lyric) firstEvent.lyric = label;
    });
    const activeEvent = exercise.events[state.activeEventIndex];
    const activeMeasure = Number(activeEvent?.measure || 0);
    const activeSection = (draft.score.sections || []).find((section) => activeMeasure >= Number(section.startMeasure) && activeMeasure <= Number(section.endMeasure));
    elements.scoreLyricText.textContent = activeSection?.label || "";
    elements.scoreLyricCue.hidden = !activeSection?.label;
    scoreUi.render(elements.resultScore, draft, eventStart + state.activeEventIndex, (index) => {
      if (index >= eventStart && index < eventStart + exercise.events.length) selectEvent(index - eventStart);
    });
  }

  function updatePracticeControls() {
    const status = state.practiceStatus;
    elements.practicePlay.textContent = status === "playing" ? "Pause" : status === "paused" ? "Resume" : "Play";
    elements.practicePlay.setAttribute("aria-pressed", String(status === "playing"));
    elements.practiceTempoValue.textContent = `${elements.practiceTempo.value} BPM`;
    let loopText = "Loop off";
    if (state.loopMode === "measure") {
      const event = state.response?.melodyExercise?.events?.[state.activeEventIndex];
      loopText = `Looping measure ${event?.measure || 1}`;
    } else if (state.loopMode === "selection" && state.loopStart !== null && state.loopEnd !== null) {
      loopText = `Looping notes ${Math.min(state.loopStart, state.loopEnd) + 1}–${Math.max(state.loopStart, state.loopEnd) + 1}`;
    } else if (state.loopStart !== null) {
      loopText = `Loop starts at note ${state.loopStart + 1}; choose an end`;
    }
    elements.practiceLoopStatus.textContent = loopText;
    elements.practiceLoopMeasure.classList.toggle("is-selected", state.loopMode === "measure");
  }

  function clearPracticeAudio() {
    state.practiceTimers.forEach((timer) => global.clearTimeout(timer));
    state.practiceTimers = [];
    if (state.practiceContext) state.practiceContext.close().catch(() => {});
    state.practiceContext = null;
    state.practiceRun += 1;
  }

  function stopPractice() {
    clearPracticeAudio();
    state.practiceStatus = "stopped";
    updatePracticeControls();
  }

  function pausePractice() {
    clearPracticeAudio();
    state.practiceStatus = "paused";
    updatePracticeControls();
  }

  function schedulePitch(context, pitchValue, when, duration, gainValue = 0.11, type = "triangle", glideToPitch = null, glideFraction = 0) {
    if (!Number.isFinite(Number(pitchValue))) return;
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = type;
    oscillator.frequency.value = 440 * 2 ** ((Number(pitchValue) - 69) / 12);
    if (Number.isFinite(Number(glideToPitch)) && Number(glideFraction) > 0) {
      const glideStart = when + duration * Math.max(0.5, 1 - Number(glideFraction));
      oscillator.frequency.setValueAtTime(oscillator.frequency.value, glideStart);
      oscillator.frequency.exponentialRampToValueAtTime(440 * 2 ** ((Number(glideToPitch) - 69) / 12), when + duration);
    }
    gain.gain.setValueAtTime(0.0001, when);
    gain.gain.exponentialRampToValueAtTime(gainValue, when + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, Math.max(when + 0.03, when + duration - 0.02));
    oscillator.connect(gain).connect(context.destination);
    oscillator.start(when);
    oscillator.stop(when + duration);
  }

  function scheduleSustainedTransitionPitch(
    context,
    fromPitchValue,
    toPitchValue,
    when,
    sourceDuration,
    targetDuration,
    gainValue = 0.11,
    type = "triangle",
    glideFraction = 0.35
  ) {
    if (!Number.isFinite(Number(fromPitchValue)) || !Number.isFinite(Number(toPitchValue))) return;
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    const fromFrequency = 440 * 2 ** ((Number(fromPitchValue) - 69) / 12);
    const toFrequency = 440 * 2 ** ((Number(toPitchValue) - 69) / 12);
    const sourceLength = Math.max(0.08, Number(sourceDuration) || 0.08);
    const targetLength = Math.max(0.08, Number(targetDuration) || 0.08);
    const glideEnd = when + sourceLength;
    const stopAt = glideEnd + targetLength;
    oscillator.type = type;
    oscillator.frequency.value = fromFrequency;
    if (Math.abs(fromFrequency - toFrequency) > 0.001) {
      const glideStart = when + sourceLength * Math.max(0.5, 1 - Number(glideFraction || 0.35));
      oscillator.frequency.setValueAtTime(fromFrequency, glideStart);
      oscillator.frequency.exponentialRampToValueAtTime(toFrequency, glideEnd);
    }
    gain.gain.setValueAtTime(0.0001, when);
    gain.gain.exponentialRampToValueAtTime(gainValue, when + 0.015);
    gain.gain.setValueAtTime(gainValue, Math.max(when + 0.016, stopAt - 0.03));
    gain.gain.exponentialRampToValueAtTime(0.0001, stopAt - 0.005);
    oscillator.connect(gain).connect(context.destination);
    oscillator.start(when);
    oscillator.stop(stopAt);
  }

  function chordPitchValues(symbol) {
    const match = String(symbol || "").trim().match(/^([A-Ga-g])([#b]?)([^/]*)/);
    if (!match) return [];
    const root = semitoneForNote(`${match[1].toUpperCase()}${match[2]}`);
    const quality = match[3].toLowerCase();
    let intervals = quality.includes("dim") ? [0, 3, 6] : quality.includes("aug") ? [0, 4, 8] : quality.startsWith("m") && !quality.startsWith("maj") ? [0, 3, 7] : [0, 4, 7];
    if (quality.includes("maj7")) intervals = [...intervals, 11];
    else if (quality.includes("7")) intervals = [...intervals, 10];
    return intervals.map((interval) => 48 + root + interval);
  }

  function activeChord(events, index) {
    for (let cursor = index; cursor >= 0; cursor -= 1) {
      const chord = String(events[cursor]?.harmonySymbol || events[cursor]?.chord || "").trim();
      if (chord) return chord;
    }
    return "";
  }

  function practiceRange(events) {
    if (state.loopMode === "measure") {
      const measure = events[state.activeEventIndex]?.measure || 1;
      const indexes = events.map((event, index) => Number(event.measure || 1) === Number(measure) ? index : -1).filter((index) => index >= 0);
      if (indexes.length) return { start: indexes[0], end: indexes.at(-1) };
    }
    if (state.loopMode === "selection" && state.loopStart !== null && state.loopEnd !== null) {
      return { start: Math.min(state.loopStart, state.loopEnd), end: Math.max(state.loopStart, state.loopEnd) };
    }
    return { start: state.activeEventIndex, end: events.length - 1 };
  }

  function runPractice({ countIn = true } = {}) {
    const events = state.response?.melodyExercise?.events || [];
    if (!events.length) return;
    clearPracticeAudio();
    const AudioContext = global.AudioContext || global.webkitAudioContext;
    if (!AudioContext) return showError("This browser does not support score playback.");
    const context = new AudioContext();
    state.practiceContext = context;
    state.practiceStatus = "playing";
    const run = state.practiceRun;
    const secondsPerBeat = 60 / Number(elements.practiceTempo.value || 80);
    const range = practiceRange(events);
    const meterBeats = String(state.scoreDraft?.score?.meter || "4/4").startsWith("3/") ? 3 : 4;
    const countBeats = countIn && elements.practiceCountIn.checked ? meterBeats : 0;
    let cursor = context.currentTime + 0.08 + countBeats * secondsPerBeat;
    for (let beat = 0; beat < countBeats; beat += 1) {
      schedulePitch(context, beat === countBeats - 1 ? 84 : 79, context.currentTime + 0.08 + beat * secondsPerBeat, 0.055, 0.055, "square");
    }
    const activeRoute = state.response?.melodyExercise?.routes?.find((route) => route.id === state.response?.melodyExercise?.selectedRouteId);
    for (let index = range.start; index <= range.end; index += 1) {
      const event = events[index];
      const duration = Math.max(0.08, Number(event.durationBeats || 1) * secondsPerBeat);
      const delay = Math.max(0, (cursor - context.currentTime) * 1000);
      state.practiceTimers.push(global.setTimeout(() => {
        if (run === state.practiceRun) selectEvent(index);
      }, delay));
      const nextEvent = index < range.end ? events[index + 1] : null;
      const previousEvent = index > range.start ? events[index - 1] : null;
      const outgoingTransition = (activeRoute?.transitions || []).find((item) => item.fromEventId === event.id && item.toEventId === nextEvent?.id);
      const incomingTransition = (activeRoute?.transitions || []).find((item) => item.fromEventId === previousEvent?.id && item.toEventId === event.id);
      if (!event.rest) {
        const targetDuration = nextEvent
          ? Math.max(0.08, Number(nextEvent.durationBeats || 1) * secondsPerBeat)
          : 0;
        transitionPlaybackPlan(event, nextEvent, outgoingTransition, incomingTransition).forEach((voice) => {
          if (voice.action === "continue") return;
          const gainValue = voice.topVoice ? 0.11 : 0.035;
          const type = voice.topVoice ? "triangle" : "sine";
          if (voice.action === "glide" || voice.action === "sustain") {
            scheduleSustainedTransitionPitch(
              context,
              voice.pitchValue,
              voice.toPitchValue,
              cursor,
              duration,
              targetDuration,
              gainValue,
              type,
              outgoingTransition?.playbackGlideFraction || 0.35
            );
          } else {
            schedulePitch(context, voice.pitchValue, cursor, duration, gainValue, type);
          }
        });
      }
      if (elements.practiceChords.checked) {
        chordPitchValues(activeChord(events, index)).forEach((pitch) => schedulePitch(context, pitch, cursor, duration, 0.025, "sine"));
      }
      cursor += duration;
    }
    state.practiceTimers.push(global.setTimeout(() => {
      if (run !== state.practiceRun) return;
      if (state.loopMode !== "off") {
        state.activeEventIndex = range.start;
        runPractice({ countIn: false });
      } else {
        accountActivity?.track("melody.playback_completed", {
          dedupeKey: `practice:${state.kind || "melody"}:${state.sectionNumber || 1}`
        });
        clearPracticeAudio();
        state.practiceStatus = "stopped";
        updatePracticeControls();
      }
    }, Math.max(0, (cursor - context.currentTime + 0.08) * 1000)));
    updatePracticeControls();
  }

  function togglePractice() {
    if (state.practiceStatus === "playing") pausePractice();
    else runPractice({ countIn: state.practiceStatus !== "paused" });
  }

  function loopCurrentMeasure() {
    state.loopMode = state.loopMode === "measure" ? "off" : "measure";
    state.loopStart = null;
    state.loopEnd = null;
    updatePracticeControls();
  }

  function setLoopBoundary(which) {
    if (which === "start") {
      state.loopStart = state.activeEventIndex;
      state.loopEnd = null;
      state.loopMode = "off";
    } else {
      state.loopStart = state.loopStart === null ? state.activeEventIndex : state.loopStart;
      state.loopEnd = state.activeEventIndex;
      state.loopMode = "selection";
    }
    updatePracticeControls();
  }

  function clearLoop() {
    state.loopMode = "off";
    state.loopStart = null;
    state.loopEnd = null;
    updatePracticeControls();
  }

  function playScoreDraft() {
    const events = ensureScoreDraft().score.melody;
    if (!events.length) return;
    const AudioContext = global.AudioContext || global.webkitAudioContext;
    if (!AudioContext) return showError("This browser does not support score playback.");
    const context = new AudioContext();
    let cursor = context.currentTime + 0.05;
    const secondsPerBeat = 0.5;
    events.forEach((event) => {
      const duration = Math.max(0.08, Number(event.durationBeats || 1) * secondsPerBeat);
      if (!event.rest) {
        const oscillator = context.createOscillator();
        const gain = context.createGain();
        oscillator.type = "triangle";
        oscillator.frequency.value = 440 * 2 ** ((Number(event.pitchValue) - 69) / 12);
        gain.gain.setValueAtTime(0.0001, cursor);
        gain.gain.exponentialRampToValueAtTime(0.14, cursor + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, cursor + duration - 0.02);
        oscillator.connect(gain).connect(context.destination);
        oscillator.start(cursor);
        oscillator.stop(cursor + duration);
      }
      cursor += duration;
    });
    global.setTimeout(() => {
      context.close();
      accountActivity?.track("melody.playback_completed", { dedupeKey: "score-playback" });
    }, Math.max(500, (cursor - context.currentTime + 0.2) * 1000));
  }

  function downloadScoreDraft() {
    const blob = new Blob([scoreUi.musicXmlForDraft(ensureScoreDraft())], { type: "application/vnd.recordare.musicxml+xml" });
    const url = URL.createObjectURL(blob);
    const link = doc.createElement("a");
    link.href = url;
    link.download = `${String(state.scoreDraft.source.title || "melody-studio-score").replace(/[^a-z0-9]+/gi, "-").toLowerCase()}.musicxml`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function importPayload(payload) {
    const isCatalog = String(payload?.sourceType || "").toLowerCase() === "catalog";
    if (isCatalog && !session?.features?.melodyCatalog) throw new Error("The built-in songbook is not enabled on this preview.");
    if (!isCatalog && !session?.features?.melodyImport) throw new Error("Temporary imports are not enabled on this preview.");
    const response = await global.fetch("/api/melody/import", {
      method: "POST",
      credentials: "same-origin",
      headers: accessHeaders(true),
      body: JSON.stringify(payload),
      cache: "no-store"
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error || `Import failed with ${response.status}.`);
    return body.scoreDraft || body.score_draft || body;
  }

  function readFileAsDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(new Error("The file could not be read."));
      reader.readAsDataURL(file);
    });
  }

  async function imageFileDataUrl(file) {
    if (!global.createImageBitmap) return readFileAsDataUrl(file);
    const bitmap = await global.createImageBitmap(file);
    const scale = Math.min(1, 1800 / Math.max(bitmap.width, bitmap.height));
    const canvas = doc.createElement("canvas");
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();
    return canvas.toDataURL(file.type === "image/png" ? "image/png" : "image/webp", 0.88);
  }

  async function importSelectedFile() {
    const file = elements.importFile.files?.[0];
    if (!file) return elements.importStatus.textContent = "Choose an image, MusicXML, MXL, or MIDI file first.";
    const sourceType = fileSourceType(file);
    if (!sourceType) return elements.importStatus.textContent = "Use JPG, PNG, WebP, MusicXML, MXL, or MIDI. For PDF, upload a screenshot.";
    if (state.sourceImageUrl) URL.revokeObjectURL(state.sourceImageUrl);
    state.sourceImageUrl = sourceType === "image" ? URL.createObjectURL(file) : "";
    elements.importPreview.hidden = !state.sourceImageUrl;
    if (state.sourceImageUrl) elements.importPreview.src = state.sourceImageUrl;
    elements.importButton.disabled = true;
    elements.importStatus.textContent = sourceType === "image" ? "Reading the page locally. You will review every note before arranging…" : "Reading the music file in memory…";
    try {
      const dataUrl = sourceType === "image" ? await imageFileDataUrl(file) : await readFileAsDataUrl(file);
      const request = {
        sourceType,
        filename: file.name,
        mimeType: sourceType === "image" ? dataUrl.slice(5, dataUrl.indexOf(";")) : file.type,
        contentBase64: dataUrl.split(",")[1] || ""
      };
      if (state.importSelectedPart) {
        if (sourceType === "midi") request.trackIndex = Number(state.importSelectedPart);
        else request.partId = state.importSelectedPart;
      }
      const draft = await importPayload(request);
      draft.review = draft.review || { status: "needs_review", warnings: [] };
      draft.review.status = "needs_review";
      hydrateScoreDraft(draft, state.sourceImageUrl);
    } catch (error) {
      elements.importStatus.textContent = error.message || "The score could not be read.";
    } finally {
      elements.importButton.disabled = false;
    }
  }

  function populateCatalogFilter(select, values) {
    const current = select.value;
    Array.from(select.options).slice(1).forEach((option) => option.remove());
    [...new Set(values.filter(Boolean))].sort().forEach((value) => {
      const option = doc.createElement("option");
      option.value = value;
      option.textContent = value.replace(/\b\w/g, (letter) => letter.toUpperCase());
      select.appendChild(option);
    });
    select.value = current;
  }

  function renderCatalog() {
    const query = elements.catalogSearch.value.trim().toLowerCase();
    const difficulty = elements.catalogDifficulty.value;
    const meter = elements.catalogMeter.value;
    const feel = elements.catalogFeel.value;
    const visibleSongs = catalogSongs.filter((song) => {
      const searchable = [song.title, song.subtitle, song.attribution].filter(Boolean).join(" ").toLowerCase();
      return (!query || searchable.includes(query))
        && (!difficulty || song.difficulty === difficulty)
        && (!meter || song.meter === meter)
        && (!feel || song.feel === feel);
    });
    elements.catalogGrid.replaceChildren();
    visibleSongs.forEach((song) => {
      const card = doc.createElement("article");
      card.className = "catalog-card";
      const title = doc.createElement("h4");
      title.textContent = song.title;
      const subtitle = doc.createElement("p");
      subtitle.textContent = song.subtitle || "Reviewed public-domain teaching version";
      const facts = doc.createElement("div");
      facts.className = "catalog-card__facts";
      [song.formLabel, song.key, song.meter, song.difficulty, song.feel, `${song.eventCount} notes`, `${song.measureCount} measures`, `${song.sectionCount} ${song.sectionCount === 1 ? "phrase" : "phrases"}`].filter(Boolean).forEach((value) => {
        const fact = doc.createElement("span");
        fact.textContent = value;
        facts.appendChild(fact);
      });
      const attribution = doc.createElement("p");
      attribution.textContent = song.attribution || "Reviewed public-domain source";
      const button = doc.createElement("button");
      button.type = "button";
      button.className = "primary-action";
      button.textContent = "Review melody";
      button.addEventListener("click", async () => {
        elements.catalogStatus.textContent = `Opening the complete melody for ${song.title}…`;
        try {
          hydrateScoreDraft(await importPayload({ sourceType: "catalog", catalogId: song.id }));
        } catch (error) {
          elements.catalogStatus.textContent = error.message;
        }
      });
      card.append(title, subtitle, facts, attribution, button);
      elements.catalogGrid.appendChild(card);
    });
    elements.catalogStatus.textContent = visibleSongs.length
      ? `${visibleSongs.length} of ${catalogSongs.length} reviewed songs shown. Source links identify the teaching version; they are not automatically transcribed.`
      : "No songs match those filters.";
  }

  async function loadCatalog() {
    elements.catalogStatus.textContent = "Loading reviewed songs…";
    if (!session?.features?.melodyCatalog) {
      elements.catalogStatus.textContent = "The built-in songbook is not enabled on this preview.";
      return;
    }
    try {
      const response = await global.fetch("/api/melody/catalog", { credentials: "same-origin", headers: accessHeaders(), cache: "no-store" });
      if (!response.ok) throw new Error(`Catalog failed with ${response.status}.`);
      const payload = await response.json();
      catalogSongs = payload.songs || payload.catalog || [];
      populateCatalogFilter(elements.catalogDifficulty, catalogSongs.map((song) => song.difficulty));
      populateCatalogFilter(elements.catalogMeter, catalogSongs.map((song) => song.meter));
      populateCatalogFilter(elements.catalogFeel, catalogSongs.map((song) => song.feel));
      renderCatalog();
      renderEntryChoices("catalog");
    } catch (error) {
      elements.catalogStatus.textContent = error.message;
    }
  }

  function loadReference() {
    const value = elements.sourceUrl.value.trim();
    const embed = referenceEmbedUrl(value, elements.loopStart.value, elements.loopEnd.value);
    if (embed) {
      elements.youtubeFrame.src = embed;
      elements.youtubeFrame.hidden = false;
      elements.externalReference.hidden = true;
      return;
    }
    try {
      const url = new URL(value);
      if (!/^https?:$/.test(url.protocol)) throw new Error("protocol");
      elements.youtubeFrame.hidden = true;
      elements.externalReference.href = url.href;
      elements.externalReference.hidden = false;
    } catch (_error) {
      showError("Use a complete YouTube, Ultimate Guitar, or attribution link.");
    }
  }

  function recordTapTempo() {
    const now = performance.now();
    state.tapTimes = [...state.tapTimes.filter((time) => now - time < 5000), now].slice(-5);
    if (state.tapTimes.length < 2) return elements.tempo.value = "Keep tapping…";
    const intervals = state.tapTimes.slice(1).map((time, index) => time - state.tapTimes[index]);
    elements.tempo.value = `${Math.round(60000 / (intervals.reduce((sum, item) => sum + item, 0) / intervals.length))} BPM`;
  }

  function transcriptionTempo() {
    return Math.max(40, Math.min(200, Number(elements.transcriptionTempo.value) || 80));
  }

  function hydrateAudioTranscription(samples, options = {}) {
    const draft = createAudioTranscriptionDraft(samples, {
      bpm: transcriptionTempo(),
      key: state.key,
      sourceType: options.sourceType,
      title: options.title,
      sourceStartSeconds: options.sourceStartSeconds,
      sourceEndSeconds: options.sourceEndSeconds
    });
    const notes = draft.score.melody.filter((event) => !event.rest);
    if (!notes.length) {
      elements.microphoneStatus.textContent = "No stable single-note phrase was detected. Try one note at a time in a quieter recording.";
      return false;
    }
    elements.microphoneStatus.textContent = `${notes.length} note${notes.length === 1 ? "" : "s"} detected · ${draft.transcription.confidenceLabel} confidence · review opened.`;
    hydrateScoreDraft(draft);
    return true;
  }

  function monoPcmFromAudioBuffer(audioBuffer) {
    const mono = new Float32Array(audioBuffer.length);
    for (let channel = 0; channel < audioBuffer.numberOfChannels; channel += 1) {
      const data = audioBuffer.getChannelData(channel);
      for (let index = 0; index < mono.length; index += 1) mono[index] += data[index] / audioBuffer.numberOfChannels;
    }
    return mono;
  }

  async function analyzeAudioFile() {
    const file = elements.audioFile.files?.[0];
    if (!file) return elements.microphoneStatus.textContent = "Choose a WAV, MP3, M4A, AAC, or OGG file first.";
    if (file.size > 75 * 1024 * 1024) return elements.microphoneStatus.textContent = "Choose an audio file smaller than 75 MB.";
    const AudioContext = global.AudioContext || global.webkitAudioContext;
    if (!AudioContext) return elements.microphoneStatus.textContent = "Audio-file transcription is unavailable in this browser.";
    elements.audioAnalyze.disabled = true;
    elements.microphoneStart.disabled = true;
    elements.microphoneStatus.textContent = "Decoding and analyzing on this device…";
    const context = new AudioContext();
    try {
      const audioBuffer = await context.decodeAudioData(await file.arrayBuffer());
      const windowBounds = audioWindowBounds(audioBuffer.duration, elements.audioStart.value, elements.audioLength.value);
      if (!windowBounds) throw new Error(`Choose a valid start before ${formatAudioTimecode(audioBuffer.duration)}.`);
      const mono = monoPcmFromAudioBuffer(audioBuffer);
      const startFrame = Math.floor(windowBounds.start * audioBuffer.sampleRate);
      const endFrame = Math.min(mono.length, Math.ceil(windowBounds.end * audioBuffer.sampleRate));
      const samples = pitchSamplesFromPcm(mono.subarray(startFrame, endFrame), audioBuffer.sampleRate, { maxSeconds: windowBounds.duration });
      elements.microphoneStatus.textContent = `Analyzing ${formatAudioTimecode(windowBounds.start)}–${formatAudioTimecode(windowBounds.end)} on this device…`;
      hydrateAudioTranscription(samples, {
        sourceType: "audio_file",
        title: file.name.replace(/\.[^.]+$/, "") || "Uploaded melody",
        sourceStartSeconds: windowBounds.start,
        sourceEndSeconds: windowBounds.end
      });
    } catch (error) {
      elements.microphoneStatus.textContent = error.message || "This audio file could not be decoded.";
    } finally {
      await context.close();
      elements.audioAnalyze.disabled = false;
      elements.microphoneStart.disabled = false;
    }
  }

  async function startMicrophoneCapture() {
    if (!navigator.mediaDevices?.getUserMedia) return elements.microphoneStatus.textContent = "Microphone capture is unavailable in this browser.";
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
      const AudioContext = global.AudioContext || global.webkitAudioContext;
      const context = new AudioContext();
      const analyser = context.createAnalyser();
      analyser.fftSize = 2048;
      context.createMediaStreamSource(stream).connect(analyser);
      const buffer = new Float32Array(analyser.fftSize);
      const capture = { stream, context, analyser, buffer, samples: [], startedAt: performance.now(), lastAnalyzedAt: 0, frame: 0, timer: 0 };
      state.microphoneCapture = capture;
      const sample = () => {
        if (state.microphoneCapture !== capture) return;
        const now = performance.now();
        if (now - capture.lastAnalyzedAt >= 50) {
          capture.lastAnalyzedAt = now;
          analyser.getFloatTimeDomainData(buffer);
          const frequency = autoCorrelate(buffer, context.sampleRate);
          const midiFloat = frequencyToMidiFloat(frequency);
          capture.samples.push({ midiFloat: midiFloat !== null && midiFloat >= 36 && midiFloat <= 96 ? midiFloat : null, time: (now - capture.startedAt) / 1000 });
          const heard = midiFloat !== null && midiFloat >= 36 && midiFloat <= 96 ? ` · ${pitchLabel(Math.round(midiFloat))}` : "";
          elements.microphoneStatus.textContent = `Listening… ${Math.min(15, Math.ceil((now - capture.startedAt) / 1000))} seconds${heard}`;
        }
        capture.frame = global.requestAnimationFrame(sample);
      };
      sample();
      capture.timer = global.setTimeout(stopMicrophoneCapture, 15000);
      elements.microphoneStart.disabled = true;
      elements.microphoneStop.disabled = false;
    } catch (_error) {
      elements.microphoneStatus.textContent = "Microphone permission was not granted.";
    }
  }

  async function stopMicrophoneCapture() {
    const capture = state.microphoneCapture;
    if (!capture) return;
    state.microphoneCapture = null;
    global.cancelAnimationFrame(capture.frame);
    global.clearTimeout(capture.timer);
    capture.stream.getTracks().forEach((track) => track.stop());
    await capture.context.close();
    elements.microphoneStart.disabled = false;
    elements.microphoneStop.disabled = true;
    hydrateAudioTranscription(capture.samples, { sourceType: "microphone", title: "Played or hummed phrase" });
  }

  function clearTransientDraft() {
    stopPractice();
    if (state.microphoneCapture) stopMicrophoneCapture();
    if (state.sourceImageUrl) URL.revokeObjectURL(state.sourceImageUrl);
    state.sourceImageUrl = "";
    if (state.sourceAudioUrl) URL.revokeObjectURL(state.sourceAudioUrl);
    state.sourceAudioUrl = "";
    if (elements.audioPreview) {
      elements.audioPreview.pause();
      elements.audioPreview.removeAttribute("src");
      elements.audioPreview.hidden = true;
    }
    if (elements.audioFile) elements.audioFile.value = "";
    elements.youtubeFrame.removeAttribute("src");
  }

  function materialLabel(material) {
    return [material?.artist, material?.song, material?.recording, material?.section].filter(Boolean).join(" · ");
  }

  function renderActiveFretboard() {
    const exercise = state.response?.melodyExercise;
    const activeRoute = exercise?.routes?.find((item) => item.id === exercise.selectedRouteId);
    const fretboard = activeRoute?.fretboard || state.response?.fretboard;
    if (!exercise?.events?.length || !fretboard) return;
    const playingContext = fretboardPlayingContext(exercise.events[state.activeEventIndex]);
    elements.fretboardPlayingContext.hidden = !playingContext.chord && !playingContext.action;
    elements.fretboardChordContext.textContent = playingContext.chord;
    elements.fretboardActionContext.textContent = playingContext.action;
    global.STEEL_RAG_FRETBOARD.mountPedalSteelFretboard(
      elements.fretboard,
      melodyFretboardOptions(fretboard, exercise.events, state.activeEventIndex, {
        showOctaveLabels: state.showOctaveLabels,
        showStringLabels: state.showStringLabels
      })
    );
    const transition = (activeRoute?.transitions || []).find((item) => item.toEventId === exercise.events[state.activeEventIndex]?.id);
    if (transition && !global.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches) {
      const sourceLine = elements.fretboard.querySelector(`[data-fret-line="${transition.fromFret}"]`);
      const sourceX = Number(sourceLine?.getAttribute("x1"));
      const sustainedStrings = new Set(transitionSustainedStrings(transition).map(String));
      elements.fretboard.querySelectorAll("[data-highlight-dot][data-highlight-string]").forEach((marker) => {
        if (!sustainedStrings.has(String(marker.dataset.highlightString))) return;
        const targetX = Number(marker.dataset.highlightRenderX);
        if (Number.isFinite(sourceX) && Number.isFinite(targetX) && typeof marker.animate === "function") {
          marker.animate([{ transform: `translateX(${sourceX - targetX}px)`, opacity: 0.45 }, { transform: "translateX(0)", opacity: 1 }], { duration: 320, easing: "ease-out" });
        }
      });
    }
  }

  function selectEvent(index) {
    const exercise = state.response?.melodyExercise;
    const events = exercise?.events || [];
    if (!events.length) return;
    state.activeEventIndex = Math.max(0, Math.min(index, events.length - 1));
    renderEvents(exercise);
    elements.previous.disabled = state.activeEventIndex === 0;
    elements.next.disabled = state.activeEventIndex === events.length - 1;
    renderActiveFretboard();
    const activeRoute = exercise.routes?.find((item) => item.id === exercise.selectedRouteId) || null;
    renderResultScore(exercise, activeRoute);
    updatePracticeControls();
  }

  function renderEvents(exercise) {
    elements.eventStrip.replaceChildren();
    const events = exercise.events || [];
    const event = events[state.activeEventIndex];
    if (!event) return;
    const activeRoute = exercise.routes?.find((item) => item.id === exercise.selectedRouteId);
    const transition = (activeRoute?.transitions || []).find((item) => item.toEventId === event.id);
    const previousEvent = state.activeEventIndex > 0 ? events[state.activeEventIndex - 1] : null;
    const card = doc.createElement("div");
    card.className = "event-step";
    card.setAttribute("role", "status");
    const scientificOctave = scientificOctaveForEvent(event);
    if (scientificOctave !== null) card.dataset.scientificOctave = String(scientificOctave);
    const progress = doc.createElement("span");
    progress.className = "event-step__progress";
    progress.textContent = `Note ${state.activeEventIndex + 1} of ${events.length}`;
    const noteLabel = doc.createElement("strong");
    noteLabel.textContent = event.resolvedPitch || event.resolvedNote || "Note";
    const positionLabel = doc.createElement("span");
    positionLabel.className = "event-step__position";
    positionLabel.textContent = readableEventPosition(event);
    card.append(progress, noteLabel, positionLabel);
    const movementText = transitionChoreography(transition, previousEvent, event) || event.movement;
    if (movementText) {
      const movement = doc.createElement("span");
      movement.className = "event-step__movement";
      movement.textContent = movementText;
      card.appendChild(movement);
    }
    elements.eventStrip.appendChild(card);
    const rationale = activeRoute?.harmonyType === "mixed_arrangement" ? gripRationale(event) : null;
    elements.gripRationale.hidden = !rationale;
    elements.gripRationale.open = false;
    elements.gripReason.textContent = rationale?.reason || "";
    elements.gripFacts.replaceChildren();
    if (rationale) {
      [
        rationale.pocket ? `Pocket: ${rationale.pocket}` : "",
        rationale.grip ? `Grip: ${rationale.grip}` : "",
        rationale.chord ? `Chord: ${rationale.chord}` : ""
      ].filter(Boolean).forEach((label) => {
        const fact = doc.createElement("span");
        fact.textContent = label;
        elements.gripFacts.appendChild(fact);
      });
      elements.gripFacts.hidden = !elements.gripFacts.childElementCount;
    } else {
      elements.gripFacts.hidden = true;
    }
  }

  function tabNoteToken(note) {
    const labels = (note?.changeLabels || []).map(String).filter(Boolean);
    const changes = (note?.changes || []).map(String).filter(Boolean);
    return `${Number(note?.fret)}${labels.length ? labels.join("+") : changes.join("")}`;
  }

  function tabConnectorTokens(transition) {
    if (!transition) return {};
    const tokens = {};
    (transition.voiceActions || []).forEach((item) => {
      const string = Number(item?.string);
      const action = String(item?.action || "");
      if (!Number.isInteger(string)) return;
      if (["bar_slide", "pedal_glide", "lever_glide"].includes(action)) tokens[string] = "~~~~~";
      else if (action === "hold") tokens[string] = "-----";
    });
    (transition.sustainedStrings || []).forEach((value) => {
      const string = Number(value);
      if (!Number.isInteger(string) || tokens[string]) return;
      if (["bar_slide", "pedal_glide", "lever_glide"].includes(String(transition.kind || ""))) tokens[string] = "~~~~~";
      else if (String(transition.kind || "") === "hold") tokens[string] = "-----";
    });
    return tokens;
  }

  function interactiveTabColumns(route) {
    const transitions = new Map((route?.transitions || []).map((item) => [item.toEventId, item]));
    let previousChord = "";
    return (route?.events || []).flatMap((event, eventIndex) => {
      const columns = [];
      const transition = eventIndex > 0 ? transitions.get(event.id) : null;
      if (transition) {
        const tokens = tabConnectorTokens(transition);
        const width = Math.max(5, ...Object.values(tokens).map((token) => String(token).length)) + 2;
        columns.push({ kind: "connector", tokens, width });
      }
      const chord = event.chord && event.chord !== previousChord ? event.chord : "";
      if (event.chord) previousChord = event.chord;
      const tokens = (event.notes || []).map(tabNoteToken);
      const width = Math.max(4, chord.length, ...tokens.map((token) => token.length)) + 2;
      columns.push({ kind: "event", event, eventIndex, chord, width });
      return columns;
    });
  }

  function highlightTabPosition(eventIndex = state.exploredTabEventIndex) {
    elements.tabCode.querySelectorAll("[data-tab-event-index]").forEach((button) => {
      button.classList.toggle("is-related", eventIndex !== null && Number(button.dataset.tabEventIndex) === Number(eventIndex));
    });
  }

  function renderTabAlternatives(route, eventIndex) {
    const event = route?.events?.[eventIndex];
    if (!event) return;
    state.exploredTabEventIndex = eventIndex;
    selectEvent(eventIndex);
    highlightTabPosition(eventIndex);
    const pitchLabels = scorePitchesForEvent(event).map((pitch) => scoreUi.pitchLabel(pitch));
    elements.tabAlternativesHeading.textContent = pitchLabels.length
      ? `Other ways to play ${pitchLabels.join(" + ")}`
      : "Other ways to play this position";
    elements.tabAlternativesSummary.textContent = `Selected position: ${compactGripDescription(event)}.`;
    elements.tabAlternativesList.replaceChildren();
    const alternatives = event.alternatePositions || [];
    alternatives.forEach((position, index) => {
      const card = doc.createElement("article");
      card.className = "tab-alternative";
      const title = doc.createElement("strong");
      title.textContent = `Option ${index + 1}`;
      const positionText = doc.createElement("span");
      positionText.textContent = compactGripDescription(event, {
        strings: position.strings,
        fret: position.fret,
        controls: position.controlLabels
      });
      const pitches = doc.createElement("span");
      pitches.textContent = `Same pitches: ${(position.pitchLabels || pitchLabels).join(" + ")}`;
      card.append(title, positionText, pitches);
      elements.tabAlternativesList.appendChild(card);
    });
    elements.tabAlternativesNote.textContent = alternatives.length
      ? `${event.selectionReason || "The arrangement chose the highlighted grip for its fit with the surrounding notes."} Every option shown passes the active copedent's pitch and mechanical checks.`
      : "No other exact-pitch grip passed the active copedent's pitch and mechanical checks. Compare another Arrangement choice to hear a different texture.";
    elements.tabAlternatives.hidden = false;
    elements.tabAlternativesHeading.focus({ preventScroll: true });
  }

  function renderInteractiveTab(route) {
    elements.tabCode.replaceChildren();
    state.exploredTabEventIndex = null;
    elements.tabAlternatives.hidden = true;
    const columns = interactiveTabColumns(route);
    if (!columns.length) {
      elements.tabCode.textContent = route?.tab?.tabText || "";
      return;
    }
    const rows = [
      ...(columns.some((column) => column.kind === "event" && column.chord) ? [{ label: "Ch |", string: null }] : []),
      ...Array.from({ length: 10 }, (_, index) => ({ label: `${String(index + 1).padStart(2, " ")} |`, string: index + 1 }))
    ];
    rows.forEach((row, rowIndex) => {
      elements.tabCode.append(doc.createTextNode(row.label));
      columns.forEach((column) => {
        let token = "";
        if (column.kind === "connector") token = row.string === null ? "" : String(column.tokens[row.string] || "");
        else if (row.string === null) token = column.chord;
        else {
          const note = (column.event.notes || []).find((item) => Number(item.string) === row.string);
          token = note ? tabNoteToken(note) : "";
          if (token) {
            const button = doc.createElement("button");
            button.type = "button";
            button.className = "tab-position";
            button.dataset.tabEventIndex = String(column.eventIndex);
            button.textContent = token;
            button.setAttribute("aria-label", `Explore note ${column.eventIndex + 1}, string ${row.string}, ${token}`);
            button.addEventListener("mouseenter", () => highlightTabPosition(column.eventIndex));
            button.addEventListener("mouseleave", () => highlightTabPosition());
            button.addEventListener("focus", () => highlightTabPosition(column.eventIndex));
            button.addEventListener("click", () => renderTabAlternatives(route, column.eventIndex));
            elements.tabCode.appendChild(button);
          }
        }
        if (!(column.kind === "event" && row.string !== null && token)) {
          elements.tabCode.append(doc.createTextNode(token));
        }
        elements.tabCode.append(doc.createTextNode(" ".repeat(Math.max(0, column.width - token.length))));
      });
      if (rowIndex < rows.length - 1) elements.tabCode.append(doc.createTextNode("\n"));
    });
  }

  function activateRoute(routeId) {
    const exercise = state.response?.melodyExercise;
    const route = (exercise?.routes || []).find((item) => item.id === routeId);
    if (!route) return;
    stopPractice();
    exercise.events = route.events;
    exercise.selectedRouteId = route.id;
    state.selectedHarmonyType = route.harmonyType;
    state.activeEventIndex = 0;
    elements.routeTabs.querySelectorAll("[data-route-id]").forEach((button) => {
      const selected = button.dataset.routeId === route.id;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    elements.printRoute.textContent = `E9 tablature · ${routeButtonLabel(route)} · Arranged for ${route.arrangedFor || exercise.arrangedFor || "E9"}`;
    elements.practiceChordOption.hidden = !hasChordContext(exercise.events);
    if (elements.practiceChordOption.hidden) elements.practiceChords.checked = false;
    renderResultScore(exercise, route);
    elements.transitionKey.hidden = !(route.transitions || []).length;
    renderInteractiveTab(route);
    selectEvent(0);
  }

  function renderRoutes(exercise) {
    elements.routeTabs.replaceChildren();
    const routes = exercise?.routes || [];
    elements.arrangementChoices.hidden = !routes.length;
    routes.forEach((route) => {
      const button = doc.createElement("button");
      button.type = "button";
      button.className = "route-tab";
      button.dataset.routeId = route.id;
      button.textContent = routeButtonLabel(route);
      button.addEventListener("click", () => activateRoute(route.id));
      elements.routeTabs.appendChild(button);
    });
    const request = exercise?.arrangementContract?.request || {};
    elements.voiceMode.value = request.voiceMode || state.voiceMode || "mixed";
    elements.movementMode.value = request.movementMode || state.movementMode || "best_fit";
    elements.arrangementPolicySummary.textContent = arrangementPolicySummary(exercise);
  }

  function updateOctaveMapVisibility() {
    const visible = Boolean(state.showOctaveMap);
    elements.result.classList.toggle("is-octave-map-visible", visible);
    elements.octaveToggle.setAttribute("aria-pressed", String(visible));
    elements.octaveToggle.setAttribute("aria-label", `${visible ? "Hide" : "Show"} octave colors`);
    elements.octaveGuide.hidden = !visible;
  }

  function updateFretboardLabelToggles() {
    elements.stringLabelToggle.setAttribute("aria-pressed", String(state.showStringLabels));
    elements.octaveLabelToggle.setAttribute("aria-pressed", String(state.showOctaveLabels));
  }

  function renderResult(response) {
    state.response = response;
    state.workflowPhase = "result";
    state.activeEventIndex = 0;
    const exercise = response.melodyExercise;
    elements.hero.hidden = true;
    elements.editor.hidden = true;
    elements.result.hidden = false;
    elements.resultTitle.textContent = exercise?.title || "Melody lesson";
    elements.printTitle.textContent = printableLessonTitle(exercise);
    const section = exercise?.section || {};
    const needsSource = exercise?.status === "needs_source";
    elements.sectionNavigation.hidden = needsSource || Number(section.total || 0) <= 1;
    elements.sectionPrevious.hidden = !section.previousSection;
    elements.sectionPrevious.dataset.section = String(section.previousSection || "");
    elements.sectionStatus.textContent = `${section.label || `Phrase ${section.number || 1}`} · ${section.number || 1} of ${section.total || 1}`;
    elements.sectionNext.hidden = !section.nextSection;
    elements.sectionNext.dataset.section = String(section.nextSection || "");
    const sourceLabel = materialLabel(exercise?.material);
    const arrangedFor = String(exercise?.arrangedFor || exercise?.targetCopedentLabel || "").trim();
    elements.resultSource.replaceChildren();
    if (arrangedFor) elements.resultSource.append(doc.createTextNode(`Arranged for ${arrangedFor}`));
    if (sourceLabel) {
      if (arrangedFor) elements.resultSource.append(" · ");
      elements.resultSource.append(doc.createTextNode(sourceLabel));
      if (exercise.material.sourceUrl) {
        const link = doc.createElement("a");
        link.href = exercise.material.sourceUrl;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Open attribution source";
        elements.resultSource.append(" · ", link);
      }
      elements.resultSource.hidden = false;
    } else {
      elements.resultSource.hidden = !arrangedFor;
    }
    const modelMetadata = exercise?.decisionRules?.modelMetadata || {};
    elements.engineStatus.textContent = arrangementEngineStatus(modelMetadata);
    elements.engineStatus.hidden = false;
    elements.sourceNeeded.hidden = !needsSource;
    elements.sourceNeeded.querySelector("p").textContent = needsSource
      ? "The recording identity is saved, but Melody Studio does not listen to the link yet. Paste notes, scale degrees, or simple one-string tab—or build the passage with the note palette—to render playable E9 positions."
      : "";
    elements.fretboard.hidden = needsSource || !response.fretboard;
    elements.octaveMapControls.hidden = needsSource || !exercise?.events?.length;
    elements.transport.hidden = needsSource || !exercise?.events?.length;
    elements.tab.hidden = needsSource || !response.tabs?.length;
    elements.resultScoreStage.hidden = needsSource;
    elements.practice.hidden = needsSource || !exercise?.events?.length;
    elements.practiceLoopPanel.hidden = needsSource || (exercise?.events?.length || 0) < 8;
    if (elements.practiceLoopPanel.hidden) elements.practiceLoopPanel.open = false;
    elements.arrangementChoices.hidden = needsSource;
    elements.practiceChordOption.hidden = needsSource || !hasChordContext(exercise?.events);
    if (elements.practiceChordOption.hidden) elements.practiceChords.checked = false;
    updateOctaveMapVisibility();
    updateFretboardLabelToggles();
    if (!needsSource && response.fretboard) {
      renderEvents(exercise);
      renderResultScore(exercise);
      renderRoutes(exercise);
      elements.tabCode.textContent = response.tabs[0]?.tabText || "";
      const selectedRoute = preferredStudioRoute(exercise, state.selectedHarmonyType);
      if (selectedRoute) activateRoute(selectedRoute.id);
      else selectEvent(0);
      updatePracticeControls();
    }
    elements.continueButton.hidden = !section.hasMore;
    elements.continueButton.textContent = section.nextSection ? `Continue to Section ${section.nextSection}` : "Continue";
    elements.continueButton.dataset.nextSection = String(section.nextSection || "");
    elements.result.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function submitLesson(sectionNumber = 1, options = {}) {
    const fail = (message) => {
      showError(message);
      if (options.statusElement) options.statusElement.textContent = message;
      return false;
    };
    if (!options.preserveStructuredEvents) syncStateFromFields();
    const task = currentTask();
    if (!task) return fail("Choose what you want to learn first.");
    const validation = validateTokens(state.tokens, state.key);
    if (!validation.ok && (!task.needsMaterial || state.tokens.length)) return fail(validation.message);
    if (state.sourceUrl) {
      try {
        const url = new URL(state.sourceUrl);
        if (!/^https?:$/.test(url.protocol)) throw new Error("protocol");
      } catch (_error) {
        return fail("Use a complete http:// or https:// attribution link.");
      }
    }
    showError("");
    state.sectionNumber = sectionNumber;
    elements.build.disabled = true;
    elements.build.textContent = "Arranging for E9…";
    try {
      const response = await answerUi.requestAnswer(questionForState(), {
        accessRole: session?.role || readAccessRole(),
        retryTransientOnce: Boolean(options.retryTransientOnce),
        requestPayload: {
          melodyRequest: buildMelodyRequest(state),
          ...(global.STEEL_RAG_COPEDENTS?.requestContext?.() ? { copedentContext: global.STEEL_RAG_COPEDENTS.requestContext() } : {})
        }
      });
      renderResult(response);
      accountActivity?.track("melody.session_started", {
        dedupeKey: `${state.kind || "melody"}:section:${sectionNumber}`
      });
      return true;
    } catch (error) {
      return fail(error.message || "Melody Studio could not build this lesson.");
    } finally {
      elements.build.disabled = false;
      elements.build.textContent = "Arrange for E9";
    }
  }

  function submitSection(sectionNumber) {
    return submitLesson(sectionNumber, { preserveStructuredEvents: Boolean(state.scoreDraft) });
  }

  async function printWholeSong() {
    const exercise = state.response?.melodyExercise;
    const total = Number(exercise?.section?.total || 1);
    const selected = exercise?.routes?.find((route) => route.id === exercise.selectedRouteId);
    const harmonyType = selected?.harmonyType;
    const originalLabel = elements.printTab.textContent;
    elements.printTab.disabled = true;
    elements.printTab.textContent = total > 1 ? "Preparing full song…" : "Preparing…";
    try {
      const sections = [];
      for (let number = 1; number <= total; number += 1) {
        let response = number === Number(exercise.section.number) ? state.response : null;
        if (!response) {
          state.sectionNumber = number;
          response = await answerUi.requestAnswer(questionForState(), {
            accessRole: session?.role || readAccessRole(),
            requestPayload: {
              melodyRequest: buildMelodyRequest(state),
              ...(global.STEEL_RAG_COPEDENTS?.requestContext?.() ? { copedentContext: global.STEEL_RAG_COPEDENTS.requestContext() } : {})
            }
          });
        }
        const route = response.melodyExercise?.routes?.find((item) => item.harmonyType === harmonyType)
          || response.melodyExercise?.routes?.[0];
        const sectionLabel = total > 1 ? (response.melodyExercise?.section?.label || `Phrase ${number}`) : "";
        const tabText = route?.tab?.printTabText || route?.tab?.tabText || response.tabs?.[0]?.printTabText || response.tabs?.[0]?.tabText || "";
        sections.push([sectionLabel, tabText].filter(Boolean).join("\n"));
      }
      elements.wholeSongTabCode.textContent = sections.join("\n\n");
      elements.wholeSongTab.hidden = false;
      global.print();
    } catch (error) {
      showError(error.message || "The complete tablature could not be prepared for printing.");
    } finally {
      state.sectionNumber = Number(exercise?.section?.number || 1);
      elements.printTab.disabled = false;
      elements.printTab.textContent = originalLabel;
    }
  }

  async function arrangeScoreDraft() {
    const draft = ensureScoreDraft();
    elements.scoreArrangeStatus.textContent = "";
    if (!KEY_NOTES[draft.score.arrangementKey]) {
      elements.scoreArrangeStatus.textContent = "Choose a supported major key before arranging.";
      return false;
    }
    state.tokens = scoreUi.arrangementEvents(draft);
    if (!state.tokens.length) {
      elements.scoreArrangeStatus.textContent = "Add at least one note before arranging.";
      return false;
    }
    state.key = draft.score.arrangementKey;
    state.kind = draft.source.type === "catalog" ? "song_arrangement_lesson" : "user_melody";
    state.song = draft.source.title || "";
    state.sourceUrl = draft.source.url || "";
    const previousReviewStatus = state.scoreDraft.review.status;
    state.scoreDraft.review.status = "confirmed";
    elements.scoreArrange.disabled = true;
    elements.scoreArrange.textContent = "Arranging for E9…";
    elements.scoreArrangeStatus.textContent = "Checking the notes and finding playable E9 routes…";
    const startedAt = Date.now();
    const progressTimer = global.setInterval(() => {
      const elapsed = Math.max(1, Math.round((Date.now() - startedAt) / 1000));
      elements.scoreArrangeStatus.textContent = `Finding the best playable E9 route… ${elapsed}s`;
    }, 1000);
    const success = await submitLesson(1, {
      preserveStructuredEvents: true,
      retryTransientOnce: true,
      statusElement: elements.scoreArrangeStatus
    });
    global.clearInterval(progressTimer);
    if (success) {
      elements.scoreArrangeStatus.textContent = "";
    } else {
      state.scoreDraft.review.status = previousReviewStatus;
      renderScoreBuilder();
    }
    return success;
  }

  function editPhrase() {
    stopPractice();
    state.workflowPhase = hasMelodyContent() ? "review" : "add";
    elements.hero.hidden = false;
    elements.result.hidden = true;
    elements.editor.hidden = false;
    renderStartingPoint();
    elements.editor.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function startOver() {
    clearTransientDraft();
    state = createInitialState();
    clearMaterial();
    elements.key.value = "G";
    elements.contour.value = "closest_playable";
    elements.phraseInput.value = "";
    elements.audioStart.value = "0:00";
    elements.audioLength.value = "15";
    elements.microphoneStatus.textContent = "Ready for audio.";
    elements.scoreArrangeStatus.textContent = "";
    elements.audioFileControls.hidden = true;
    elements.editor.hidden = false;
    elements.result.hidden = true;
    elements.hero.hidden = false;
    renderStartingPoint();
    renderPalette();
    renderPhraseBuilder();
    showError("");
    elements.editor.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function bootstrap() {
    try {
      session = await answerUi.requestSession({ accessRole: readAccessRole() });
      await global.STEEL_RAG_COPEDENTS?.configureAccount?.(session, { accessRole: readAccessRole() });
      global.STEEL_RAG_COPEDENTS?.renderStatus?.(elements.hero?.querySelector?.("[data-active-copedent]"));
      const profileState = global.STEEL_RAG_COPEDENTS?.activeContext?.();
      if (profileState?.blocked) {
        elements.unavailableTitle.textContent = "Your copedent needs review.";
        elements.unavailableCopy.textContent = "Backstage preserved the older setup without guessing at missing RKL or travel states. Review and validate it before arranging.";
        elements.unavailable.hidden = false;
        elements.workflow.hidden = true;
        return;
      }
      const enabled = Boolean(session.features?.melodyExercise);
      elements.unavailable.hidden = enabled;
      elements.workflow.hidden = !enabled;
      if (!enabled) {
        elements.unavailableTitle.textContent = "Melody Studio is temporarily unavailable.";
        elements.unavailableCopy.textContent = "This preview did not enable Melody Studio. This is not a mobile limitation: Melody Studio supports phones, tablets, and desktop browsers. Return home, then try again after the preview is updated.";
        return;
      }
      const importEnabled = Boolean(session.features?.melodyImport);
      const catalogEnabled = Boolean(session.features?.melodyCatalog);
      const songPracticeEnabled = Boolean(session.features?.songPractice);
      const importChoice = elements.startChoices.find((button) => button.dataset.studioStart === "import");
      const catalogChoice = elements.startChoices.find((button) => button.dataset.studioStart === "catalog");
      const songChoice = elements.startChoices.find((button) => button.dataset.studioStart === "song");
      if (importChoice) importChoice.hidden = !importEnabled;
      if (catalogChoice) catalogChoice.hidden = !catalogEnabled;
      if (songChoice) songChoice.hidden = !songPracticeEnabled;
      if (songPracticeEnabled) {
        try {
          await global.STEEL_RAG_SONG_PROJECTS?.configure?.({ session, enabled: true });
        } catch (songPracticeError) {
          if (songChoice) {
            songChoice.disabled = true;
            songChoice.dataset.songPracticeError = String(songPracticeError?.message || "Song Practice initialization failed");
            const help = songChoice.querySelector("small");
            if (help) help.textContent = "Temporarily unavailable";
          }
        }
      }
      // Preserve Explorer, Q&A, and Song Practice handoffs as visible,
      // editable input. Without this synchronization the parsed deep-link
      // state could disagree with the controls and be erased on submit.
      elements.key.value = state.key;
      elements.voiceMode.value = state.voiceMode;
      elements.movementMode.value = state.movementMode;
      if (state.tokens.length) {
        elements.phraseInput.value = state.tokens.some((item) => Number.isInteger(item.string))
          ? state.tokens.map(phraseItemLabel).join("\n")
          : state.tokens.map(phraseItemLabel).join(" ");
      }
      elements.editor.hidden = false;
      renderStartingPoint();
      renderPalette();
      renderPhraseBuilder();
    } catch (_error) {
      elements.unavailableTitle.textContent = "Melody Studio could not verify access.";
      elements.unavailableCopy.textContent = "The availability check did not complete. This is not a mobile limitation. Check the connection, reload the page, or return home and try again.";
      elements.unavailable.hidden = false;
      elements.workflow.hidden = true;
    }
  }

  elements.startChoices.forEach((button) => button.addEventListener("click", () => selectStartingPoint(button.dataset.studioStart)));
  elements.confirmReplace.addEventListener("click", () => {
    const nextMethod = state.pendingReplacement;
    if (nextMethod) selectStartingPoint(nextMethod, { confirmed: true });
  });
  elements.keepMelody.addEventListener("click", () => {
    state.pendingReplacement = "";
    renderStartingPoint();
  });
  elements.sourceTreatmentButtons.forEach((button) => button.addEventListener("click", () => selectSourceTreatment(button.dataset.sourceTreatment)));
  elements.addRecording.addEventListener("click", () => {
    state.showSourceDetails = !state.showSourceDetails;
    if (state.showSourceDetails && !currentTask()?.needsMaterial) state.kind = "song_arrangement_lesson";
    renderStartingPoint();
    if (state.showSourceDetails) elements.materialFields.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
  elements.closeMaterial.addEventListener("click", () => {
    state.showSourceDetails = false;
    renderStartingPoint();
  });
  [elements.catalogSearch, elements.catalogDifficulty, elements.catalogMeter, elements.catalogFeel].forEach((control) => control.addEventListener("input", renderCatalog));
  elements.octaveDown.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.tokens[index] = { ...phraseItem(state.tokens[index]), octaveShift: Math.max(-2, Number(state.tokens[index]?.octaveShift || 0) - 1) };
    renderPhraseBuilder();
  });
  elements.octaveAuto.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.tokens[index] = { ...phraseItem(state.tokens[index]), direction: "auto", octaveShift: 0 };
    renderPhraseBuilder();
  });
  elements.octaveUp.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.tokens[index] = { ...phraseItem(state.tokens[index]), octaveShift: Math.min(2, Number(state.tokens[index]?.octaveShift || 0) + 1) };
    renderPhraseBuilder();
  });
  elements.noteEarlier.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.selectedPhraseIndex = Math.max(0, index - 1);
    setTokens(reorderToken(state.tokens, index, -1));
  });
  elements.noteLater.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.selectedPhraseIndex = Math.min(state.tokens.length - 1, index + 1);
    setTokens(reorderToken(state.tokens, index, 1));
  });
  elements.noteRemove.addEventListener("click", () => {
    const index = state.selectedPhraseIndex;
    state.tokens = state.tokens.filter((_item, itemIndex) => itemIndex !== index);
    state.selectedPhraseIndex = Math.max(0, Math.min(index, state.tokens.length - 1));
    setTokens(state.tokens);
  });
  elements.key.addEventListener("change", () => {
    const nextKey = elements.key.value;
    if (state.inputMethod === "score" && state.scoreDraft) {
      const roots = { C: 0, G: 7, D: 2, A: 9, E: 4, B: 11, F: 5, "F#": 6, Bb: 10, Eb: 3, Ab: 8, Db: 1 };
      const source = state.scoreDraft.score.arrangementKey || state.scoreDraft.score.sourceKey;
      let shift = (roots[nextKey] ?? 0) - (roots[source] ?? 0);
      if (shift > 6) shift -= 12;
      if (shift < -6) shift += 12;
      const transposed = scoreUi.transposeDraft(state.scoreDraft, shift);
      transposed.score.arrangementKey = nextKey;
      commitScoreDraft(transposed, state.scoreSelectedIndex);
    }
    state.key = nextKey;
    renderPalette();
    renderPhraseBuilder();
  });
  elements.contour.addEventListener("change", () => {
    state.contourMode = elements.contour.value;
    renderPhraseBuilder();
  });
  async function rebuildArrangementPolicy() {
    const previousVoiceMode = state.voiceMode;
    const previousMovementMode = state.movementMode;
    const previousHarmonyType = state.selectedHarmonyType;
    state.voiceMode = elements.voiceMode.value || "mixed";
    state.movementMode = elements.movementMode.value || "best_fit";
    state.selectedHarmonyType = {
      single: "single_note",
      two_voice: "automatic_harmony",
      three_voice: "chord_melody",
      mixed: "mixed_arrangement"
    }[state.voiceMode] || "mixed_arrangement";
    elements.voiceMode.disabled = true;
    elements.movementMode.disabled = true;
    elements.arrangementPolicySummary.textContent = "Rebuilding validated tab, movement, and alternatives…";
    const sectionNumber = Number(state.response?.melodyExercise?.section?.number || state.sectionNumber || 1);
    const success = await submitSection(sectionNumber);
    if (!success) {
      state.voiceMode = previousVoiceMode;
      state.movementMode = previousMovementMode;
      state.selectedHarmonyType = previousHarmonyType;
      elements.voiceMode.value = previousVoiceMode;
      elements.movementMode.value = previousMovementMode;
    }
    elements.voiceMode.disabled = false;
    elements.movementMode.disabled = false;
  }
  elements.voiceMode.addEventListener("change", rebuildArrangementPolicy);
  elements.movementMode.addEventListener("change", rebuildArrangementPolicy);
  elements.phraseInput.addEventListener("input", () => {
    state.tokens = parsePhraseEvents(elements.phraseInput.value);
    renderPhraseBuilder();
    renderStartingPoint();
  });
  elements.paletteModeButtons.forEach((button) => button.addEventListener("click", () => {
    state.paletteMode = button.dataset.paletteMode;
    renderPalette();
  }));
  elements.presetButtons.forEach((button) => button.addEventListener("click", () => setTokens(PRESETS[button.dataset.preset] || [])));
  elements.useExercise.addEventListener("click", () => {
    clearMaterial();
    state.showSourceDetails = false;
    state.kind = "original_exercise";
    state.inputMethod = "phrase";
    setTokens(PRESETS["1-2-3-5"]);
    renderStartingPoint();
  });
  elements.scoreMeter.addEventListener("change", () => {
    const next = scoreUi.cloneDraft(ensureScoreDraft());
    next.score.meter = elements.scoreMeter.value;
    commitScoreDraft(next);
  });
  elements.scorePickup.addEventListener("change", () => {
    const next = scoreUi.cloneDraft(ensureScoreDraft());
    next.score.pickupBeats = Number(elements.scorePickup.value);
    commitScoreDraft(next);
  });
  elements.scorePart.addEventListener("change", () => {
    state.importSelectedPart = elements.scorePart.value;
    importSelectedFile();
  });
  elements.insertRest.addEventListener("click", () => addScoreEvent({ rest: true, pitch: null, pitchValue: null }));
  elements.addMeasure.addEventListener("click", () => {
    const beats = scoreUi.beatsPerMeasure(ensureScoreDraft());
    addScoreEvent({ rest: true, pitch: null, pitchValue: null, durationBeats: beats });
  });
  elements.removeMeasure.addEventListener("click", () => {
    const draft = ensureScoreDraft();
    const lastMeasure = Math.max(...draft.score.melody.map((event) => event.measure), 1);
    commitScoreDraft(scoreUi.clearMeasure(draft, lastMeasure), -1);
  });
  elements.scoreUndo.addEventListener("click", () => restoreScoreHistory(-1));
  elements.scoreRedo.addEventListener("click", () => restoreScoreHistory(1));
  elements.scorePitch.addEventListener("change", () => {
    const match = elements.scorePitch.value.trim().replace(/♯/g, "#").replace(/♭/g, "b").match(/^([A-Ga-g])([#b]?)(-?\d)$/);
    if (!match) return showError("Use a scientific pitch such as G4, F#4, or Bb3.");
    const note = `${match[1].toUpperCase()}${match[2]}`;
    const pitchClass = semitoneForNote(note);
    const pitchValue = (Number(match[3]) + 1) * 12 + pitchClass;
    updateSelectedScoreEvent({ pitchValue, pitch: scoreUi.pitchLabel(pitchValue) });
  });
  elements.eventDuration.addEventListener("change", () => updateSelectedScoreEvent({ durationBeats: Number(elements.eventDuration.value) }));
  elements.scoreLyric.addEventListener("change", () => updateSelectedScoreEvent({ lyric: elements.scoreLyric.value.trim() }));
  elements.scoreTie.addEventListener("change", () => updateSelectedScoreEvent({ tie: elements.scoreTie.value }));
  elements.scoreArticulation.addEventListener("change", () => updateSelectedScoreEvent({ articulation: elements.scoreArticulation.value }));
  elements.scoreChord.addEventListener("input", () => commitScoreDraft(scoreUi.setChordAtEvent(state.scoreDraft, state.scoreSelectedIndex, elements.scoreChord.value), state.scoreSelectedIndex));
  elements.scoreRemove.addEventListener("click", removeSelectedScoreEvent);
  elements.scoreDeleteSelected.addEventListener("click", removeSelectedScoreEvent);
  elements.scoreClearMeasure.addEventListener("click", () => {
    const event = selectedScoreEvent();
    if (event) commitScoreDraft(scoreUi.clearMeasure(state.scoreDraft, event.measure), -1);
  });
  elements.scoreDuplicate.addEventListener("click", () => commitScoreDraft(scoreUi.duplicatePhrase(ensureScoreDraft()), -1));
  elements.scoreTransposeDown.addEventListener("click", () => transposeWholeScore(-1, "Moved every note down one semitone."));
  elements.scoreTransposeUp.addEventListener("click", () => transposeWholeScore(1, "Moved every note up one semitone."));
  elements.scoreOctaveDown.addEventListener("click", () => transposeWholeScore(-12, "Moved every note down one octave."));
  elements.scoreOctaveUp.addEventListener("click", () => transposeWholeScore(12, "Moved every note up one octave."));
  elements.scorePlay.addEventListener("click", playScoreDraft);
  elements.scoreDownload.addEventListener("click", downloadScoreDraft);
  elements.scoreArrange.addEventListener("click", arrangeScoreDraft);
  elements.scoreEditToggle.addEventListener("click", () => {
    state.scoreEditingEnabled = !state.scoreEditingEnabled;
    renderScoreBuilder();
  });
  elements.scorePreviousNote.addEventListener("click", () => selectScoreEvent(state.scoreSelectedIndex - 1));
  elements.scoreNextNote.addEventListener("click", () => selectScoreEvent(state.scoreSelectedIndex + 1));
  elements.scoreCanvas.addEventListener("click", (event) => {
    if (event.target.closest?.(".score-event")) return;
    if (state.scoreDraft?.source?.type === "catalog" && !state.scoreEditingEnabled) return;
    const rect = elements.scoreCanvas.getBoundingClientRect();
    const relative = Math.max(0, Math.min(1, (event.clientY - rect.top) / Math.max(1, rect.height)));
    const pitchValue = Math.max(48, Math.min(84, Math.round(79 - relative * 24)));
    addScoreEvent({ pitchValue, pitch: scoreUi.pitchLabel(pitchValue) });
  });
  elements.importButton.addEventListener("click", importSelectedFile);
  elements.importFile.addEventListener("change", () => {
    const file = elements.importFile.files?.[0];
    elements.importStatus.textContent = file ? `${file.name} is ready to read.` : "";
    renderStartingPoint();
  });
  elements.microphoneStart.addEventListener("click", startMicrophoneCapture);
  elements.microphoneStop.addEventListener("click", stopMicrophoneCapture);
  elements.audioAnalyze.addEventListener("click", analyzeAudioFile);
  elements.audioFile.addEventListener("change", () => {
    const file = elements.audioFile.files?.[0];
    if (state.sourceAudioUrl) URL.revokeObjectURL(state.sourceAudioUrl);
    state.sourceAudioUrl = file ? URL.createObjectURL(file) : "";
    elements.audioPreview.hidden = !state.sourceAudioUrl;
    elements.audioFileControls.hidden = !state.sourceAudioUrl;
    if (state.sourceAudioUrl) elements.audioPreview.src = state.sourceAudioUrl;
    else elements.audioPreview.removeAttribute("src");
    elements.microphoneStatus.textContent = file ? `${file.name} is ready. Play it, choose a 5–15 second window, then transcribe.` : "Ready for audio.";
    renderStartingPoint();
  });
  elements.audioPreview.addEventListener("loadedmetadata", () => {
    elements.microphoneStatus.textContent = `Recording length ${formatAudioTimecode(elements.audioPreview.duration)}. Choose the passage you want to transcribe.`;
  });
  elements.audioUsePlayhead.addEventListener("click", () => {
    elements.audioStart.value = formatAudioTimecode(elements.audioPreview.currentTime || 0);
    elements.microphoneStatus.textContent = `Window will start at ${elements.audioStart.value}.`;
  });
  elements.transcriptionTempo.addEventListener("change", () => {
    elements.transcriptionTempo.value = String(transcriptionTempo());
  });
  elements.loadReference.addEventListener("click", loadReference);
  elements.repeatReference.addEventListener("click", () => {
    if (!elements.youtubeFrame.hidden) {
      const source = elements.youtubeFrame.src;
      elements.youtubeFrame.src = "about:blank";
      global.setTimeout(() => { elements.youtubeFrame.src = source; }, 0);
    } else loadReference();
  });
  elements.tapTempo.addEventListener("click", recordTapTempo);
  elements.build.addEventListener("click", () => submitLesson(1));
  elements.previous.addEventListener("click", () => selectEvent(state.activeEventIndex - 1));
  elements.next.addEventListener("click", () => selectEvent(state.activeEventIndex + 1));
  elements.practicePlay.addEventListener("click", togglePractice);
  elements.practiceStop.addEventListener("click", stopPractice);
  elements.practiceTempo.addEventListener("input", updatePracticeControls);
  elements.practiceLoopMeasure.addEventListener("click", loopCurrentMeasure);
  elements.practiceLoopStart.addEventListener("click", () => setLoopBoundary("start"));
  elements.practiceLoopEnd.addEventListener("click", () => setLoopBoundary("end"));
  elements.practiceLoopClear.addEventListener("click", clearLoop);
  elements.printTab.addEventListener("click", printWholeSong);
  elements.tabAlternativesClose.addEventListener("click", () => {
    const eventIndex = state.exploredTabEventIndex;
    state.exploredTabEventIndex = null;
    elements.tabAlternatives.hidden = true;
    highlightTabPosition();
    elements.tabCode.querySelector(`[data-tab-event-index="${eventIndex}"]`)?.focus();
  });
  elements.octaveToggle.addEventListener("click", () => {
    state.showOctaveMap = !state.showOctaveMap;
    updateOctaveMapVisibility();
  });
  elements.stringLabelToggle.addEventListener("click", () => {
    state.showStringLabels = !state.showStringLabels;
    updateFretboardLabelToggles();
    renderActiveFretboard();
  });
  elements.octaveLabelToggle.addEventListener("click", () => {
    state.showOctaveLabels = !state.showOctaveLabels;
    updateFretboardLabelToggles();
    renderActiveFretboard();
  });
  elements.continueButton.addEventListener("click", () => submitSection(Number(elements.continueButton.dataset.nextSection) || state.sectionNumber + 1));
  elements.sectionPrevious.addEventListener("click", () => submitSection(Number(elements.sectionPrevious.dataset.section)));
  elements.sectionNext.addEventListener("click", () => submitSection(Number(elements.sectionNext.dataset.section)));
  elements.editTop.addEventListener("click", editPhrase);
  elements.edit.addEventListener("click", editPhrase);
  elements.sourceNeeded.querySelector("[data-edit-source]").addEventListener("click", editPhrase);
  elements.result.querySelector("[data-start-over]").addEventListener("click", startOver);

  doc.addEventListener("keydown", (event) => {
    if (state.inputMethod !== "score" || event.metaKey || event.ctrlKey || event.altKey) return;
    if (state.scoreDraft?.source?.type === "catalog" && !state.scoreEditingEnabled) return;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(doc.activeElement?.tagName)) return;
    if (["Delete", "Backspace"].includes(event.key)) {
      event.preventDefault();
      removeSelectedScoreEvent();
      return;
    }
    const durationShortcuts = { "1": "0.5", "2": "1", "3": "1.5", "4": "2", "5": "3", "6": "4" };
    if (durationShortcuts[event.key]) {
      event.preventDefault();
      elements.scoreDuration.value = durationShortcuts[event.key];
      elements.scoreStatus.textContent = `Note length: ${elements.scoreDuration.options[elements.scoreDuration.selectedIndex].text}. Press A–G to add a pitch.`;
      return;
    }
    const note = event.key.toUpperCase();
    if (!/^[A-G]$/.test(note)) return;
    event.preventDefault();
    const pitchValue = 60 + semitoneForNote(note);
    addScoreEvent({ pitchValue, pitch: scoreUi.pitchLabel(pitchValue) });
  });
  global.addEventListener("pagehide", clearTransientDraft);

  bootstrap();
})(typeof window !== "undefined" ? window : globalThis);
