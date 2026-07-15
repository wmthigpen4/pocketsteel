(function (global) {
  "use strict";

  const DURATIONS = {
    whole: 4,
    half: 2,
    dotted_half: 3,
    quarter: 1,
    dotted_quarter: 1.5,
    eighth: 0.5
  };
  const PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const MAX_EVENTS = 128;
  const MAX_MEASURES = 64;

  function pitchLabel(value) {
    const pitch = Number(value);
    return `${PITCH_NAMES[((pitch % 12) + 12) % 12]}${Math.floor(pitch / 12) - 1}`;
  }

  function createDraft(options = {}) {
    return {
      schemaVersion: "score_draft_v1",
      source: {
        type: options.sourceType || "composed_in_studio",
        title: options.title || "My Melody Studio score",
        url: options.url || null,
        rightsLabel: options.rightsLabel || "user_created",
        retained: false
      },
      score: {
        sourceKey: options.key || "G",
        arrangementKey: options.key || "G",
        meter: options.meter || "4/4",
        pickupBeats: Number(options.pickupBeats || 0),
        melody: [],
        harmony: []
      },
      review: { status: options.reviewStatus || "confirmed", warnings: [] }
    };
  }

  function cloneDraft(draft) {
    return JSON.parse(JSON.stringify(draft));
  }

  function beatsPerMeasure(draft) {
    return String(draft?.score?.meter || "4/4").startsWith("3/") ? 3 : 4;
  }

  function reflowDraft(draft) {
    const next = cloneDraft(draft);
    const beats = beatsPerMeasure(next);
    const pickup = Math.max(0, Number(next.score.pickupBeats || 0));
    const preserveReviewedMeasures = Array.isArray(next.score.sections) && next.score.sections.length > 0;
    let measure = 1;
    let beat = pickup ? beats - pickup + 1 : 1;
    next.score.melody = (next.score.melody || []).slice(0, MAX_EVENTS).map((raw, index) => {
      const event = { ...raw };
      const duration = Math.max(0.5, Number(event.durationBeats || 1));
      if (!preserveReviewedMeasures && beat >= beats + 1 - 0.001) {
        measure += 1;
        beat = 1;
      }
      event.id = event.id || `score-event-${index + 1}`;
      event.measure = preserveReviewedMeasures
        ? Math.max(1, Math.min(MAX_MEASURES, Number(event.measure || 1)))
        : Math.min(MAX_MEASURES, measure);
      event.beat = preserveReviewedMeasures ? Math.max(1, Number(event.beat || 1)) : Number(beat.toFixed(3));
      event.durationBeats = duration;
      event.origin = event.origin || (next.source.type === "composed_in_studio" ? "user_edit" : "source");
      event.confidence = Number.isFinite(Number(event.confidence)) ? Number(event.confidence) : 1;
      event.articulation = ["accent", "tenuto", "staccato"].includes(event.articulation) ? event.articulation : "";
      if (!event.rest && Number.isFinite(Number(event.pitchValue))) {
        event.pitchValue = Number(event.pitchValue);
        event.pitch = pitchLabel(event.pitchValue);
        if (Array.isArray(event.pitches)) {
          const pitches = event.pitches.map(Number).filter(Number.isFinite);
          event.pitches = Array.from(new Set([...pitches, event.pitchValue])).sort((a, b) => a - b);
        }
      }
      if (!preserveReviewedMeasures) beat += duration;
      return event;
    });
    next.score.harmony = (next.score.harmony || []).filter((item) => item.symbol).slice(0, 64);
    return next;
  }

  function addEvent(draft, event) {
    if ((draft?.score?.melody || []).length >= MAX_EVENTS) return cloneDraft(draft);
    const next = cloneDraft(draft);
    next.score.melody.push({
      id: `score-event-${Date.now()}-${next.score.melody.length + 1}`,
      durationBeats: 1,
      pitchValue: 67,
      pitch: "G4",
      origin: next.source.type === "composed_in_studio" ? "user_edit" : "source",
      confidence: 1,
      ...event
    });
    return reflowDraft(next);
  }

  function updateEvent(draft, index, changes) {
    const next = cloneDraft(draft);
    if (!next.score.melody[index]) return next;
    next.score.melody[index] = { ...next.score.melody[index], ...changes, origin: "user_edit", confidence: 1 };
    return reflowDraft(next);
  }

  function removeEvent(draft, index) {
    const next = cloneDraft(draft);
    next.score.melody.splice(index, 1);
    return reflowDraft(next);
  }

  function clearMeasure(draft, measure) {
    const next = cloneDraft(draft);
    next.score.melody = next.score.melody.filter((event) => Number(event.measure) !== Number(measure));
    next.score.harmony = next.score.harmony.filter((event) => Number(event.measure) !== Number(measure));
    return reflowDraft(next);
  }

  function duplicatePhrase(draft) {
    const next = cloneDraft(draft);
    const room = MAX_EVENTS - next.score.melody.length;
    next.score.melody.push(...next.score.melody.slice(0, room).map((event, index) => ({ ...event, id: `${event.id}-copy-${index + 1}`, origin: "user_edit" })));
    return reflowDraft(next);
  }

  function transposeDraft(draft, semitones) {
    const next = cloneDraft(draft);
    next.score.melody = next.score.melody.map((event) => event.rest ? event : {
      ...event,
      pitchValue: Number(event.pitchValue) + Number(semitones),
      pitch: pitchLabel(Number(event.pitchValue) + Number(semitones)),
      ...(Array.isArray(event.pitches) ? {pitches: event.pitches.map((value) => Number(value) + Number(semitones))} : {}),
      origin: "user_edit"
    });
    return reflowDraft(next);
  }

  function setChordAtEvent(draft, index, symbol) {
    const next = cloneDraft(draft);
    const event = next.score.melody[index];
    if (!event) return next;
    next.score.harmony = next.score.harmony.filter((item) => !(Number(item.measure) === Number(event.measure) && Number(item.beat) === Number(event.beat)));
    if (String(symbol || "").trim()) {
      next.score.harmony.push({
        measure: event.measure,
        beat: event.beat,
        symbol: String(symbol).trim().slice(0, 24),
        basis: "user",
        confidence: 1
      });
    }
    return next;
  }

  function chordForEvent(draft, event) {
    const harmony = [...(draft?.score?.harmony || [])]
      .filter((item) => Number(item.measure) < Number(event.measure) || (Number(item.measure) === Number(event.measure) && Number(item.beat) <= Number(event.beat)))
      .sort((a, b) => Number(a.measure) - Number(b.measure) || Number(a.beat) - Number(b.beat));
    return harmony.at(-1)?.symbol || "";
  }

  function chordChangeAtEvent(draft, event) {
    return (draft?.score?.harmony || []).find((item) =>
      Number(item.measure) === Number(event.measure) && Number(item.beat) === Number(event.beat)
    )?.symbol || "";
  }

  function arrangementEvents(draft) {
    return (draft?.score?.melody || []).filter((event) => !event.rest).map((event) => ({
      token: event.pitch,
      pitch: event.pitch,
      pitchValue: event.pitchValue,
      measure: event.measure,
      beat: event.beat,
      durationBeats: event.durationBeats,
      origin: event.origin || "user_edit",
      confidence: Number.isFinite(Number(event.confidence)) ? Number(event.confidence) : 1,
      tie: event.tie || "",
      lyric: event.lyric || "",
      articulation: event.articulation || "",
      chord: chordForEvent(draft, event)
    }));
  }

  function draftWarnings(draft) {
    const score = reflowDraft(draft).score;
    const beats = beatsPerMeasure(draft);
    const warnings = [];
    const totals = new Map();
    score.melody.forEach((event) => totals.set(event.measure, (totals.get(event.measure) || 0) + Number(event.durationBeats || 0)));
    totals.forEach((total, measure) => {
      const capacity = measure === 1 && Number(score.pickupBeats) > 0 ? Number(score.pickupBeats) : beats;
      if (total > capacity + 0.001) warnings.push(`Measure ${measure} has ${total} beats but allows ${capacity}. Shorten a note or add a tie.`);
    });
    score.melody.forEach((event, index) => {
      if (event.tie === "start") {
        const next = score.melody[index + 1];
        if (!next || next.rest || Number(next.pitchValue) !== Number(event.pitchValue)) warnings.push(`Tie after event ${index + 1} needs the same pitch next.`);
      }
    });
    return warnings;
  }

  function durationName(beats) {
    return Object.keys(DURATIONS).find((key) => DURATIONS[key] === Number(beats)) || "quarter";
  }

  function musicXmlForDraft(draft) {
    const score = reflowDraft(draft).score;
    const beats = beatsPerMeasure(draft);
    const divisions = 8;
    const byMeasure = new Map();
    score.melody.forEach((event) => {
      const list = byMeasure.get(event.measure) || [];
      list.push(event);
      byMeasure.set(event.measure, list);
    });
    const escape = (value) => String(value || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    const measures = Array.from({ length: Math.max(1, ...byMeasure.keys()) }, (_, offset) => {
      const measure = offset + 1;
      const notes = byMeasure.get(measure) || [];
      const attributes = measure === 1 ? `<attributes><divisions>${divisions}</divisions><key><fifths>${score.arrangementKey === "G" ? 1 : 0}</fifths></key><time><beats>${beats}</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>` : "";
      const harmony = score.harmony.filter((item) => Number(item.measure) === measure).map((item) => `<direction><direction-type><words>${escape(item.symbol)}</words></direction-type></direction>`).join("");
      const body = notes.map((event) => {
        const duration = Math.max(1, Math.round(Number(event.durationBeats) * divisions));
        const rest = event.rest ? "<rest/>" : (() => {
          const match = String(event.pitch).match(/^([A-G])([#b]?)(-?\d+)$/);
          const alter = match?.[2] === "#" ? "<alter>1</alter>" : match?.[2] === "b" ? "<alter>-1</alter>" : "";
          return `<pitch><step>${match?.[1] || "C"}</step>${alter}<octave>${match?.[3] || "4"}</octave></pitch>`;
        })();
        const lyric = event.lyric ? `<lyric><text>${escape(event.lyric)}</text></lyric>` : "";
        const tie = event.tie ? `<tie type="${escape(event.tie)}"/>` : "";
        const dot = [1.5, 3].includes(Number(event.durationBeats)) ? "<dot/>" : "";
        const articulation = event.articulation ? `<notations><articulations><${escape(event.articulation)}/></articulations></notations>` : "";
        return `<note>${rest}<duration>${duration}</duration><voice>1</voice><type>${durationName(event.durationBeats).replace("dotted_", "")}</type>${dot}${tie}${articulation}${lyric}</note>`;
      }).join("");
      return `<measure number="${measure}">${attributes}${harmony}${body}</measure>`;
    }).join("");
    return `<?xml version="1.0" encoding="UTF-8"?><score-partwise version="4.0"><work><work-title>${escape(draft.source.title)}</work-title></work><part-list><score-part id="P1"><part-name>Melody</part-name></score-part></part-list><part id="P1">${measures}</part></score-partwise>`;
  }

  function staffStep(pitchValue) {
    const label = pitchLabel(pitchValue);
    const match = label.match(/^([A-G])[#b]?(-?\d+)$/);
    const order = { C: 0, D: 1, E: 2, F: 3, G: 4, A: 5, B: 6 };
    return (Number(match?.[2] || 4) - 4) * 7 + order[match?.[1] || "C"];
  }

  function vexDuration(event) {
    const duration = Number(event.durationBeats || 1);
    const base = duration === 4 ? "w" : duration >= 2 ? "h" : duration <= 0.5 ? "8" : "q";
    return `${base}${event.rest ? "r" : ""}`;
  }

  function scoreSystemLayout(measureCount, containerWidth) {
    const width = Math.max(320, Math.floor(Number(containerWidth) || 760) - 16);
    const columns = Math.max(2, Math.min(4, Math.floor((width - 24) / 180)));
    const systems = Math.max(1, Math.ceil(Math.max(1, Number(measureCount) || 1) / columns));
    return { width, columns, systems, systemHeight: 190, height: systems * 190 + 24 };
  }

  function transitionScoreVoices(event) {
    const voices = event?.transitionFromPrevious?.scoreVoices;
    return Array.isArray(voices) ? voices.filter((voice) =>
      Number.isFinite(Number(voice?.fromPitchValue)) && Number.isFinite(Number(voice?.toPitchValue))) : [];
  }

  function nearestPitchIndex(event, pitchValue) {
    const pitches = event?.pitches?.length ? event.pitches : [event?.pitchValue];
    let bestIndex = 0;
    let bestDistance = Infinity;
    pitches.forEach((value, index) => {
      const distance = Math.abs(Number(value) - Number(pitchValue));
      if (distance < bestDistance) {
        bestIndex = index;
        bestDistance = distance;
      }
    });
    return bestIndex;
  }

  function vexVoiceY(rendered, pitchValue, box) {
    const ys = typeof rendered?.note?.getYs === "function" ? rendered.note.getYs() : [];
    const index = nearestPitchIndex(rendered?.event, pitchValue);
    return Number.isFinite(Number(ys?.[index])) ? Number(ys[index]) : box.y + box.height * 0.42;
  }

  function renderWithVexFlow(container, draft, selectedIndex = -1, onSelect) {
    const VF = global.VexFlow;
    if (!VF?.Renderer || !VF?.Stave || !VF?.StaveNote || !VF?.Voice || !VF?.Formatter) return false;
    container.replaceChildren();
    const score = reflowDraft(draft).score;
    const measureCount = Math.max(1, ...score.melody.map((event) => Number(event.measure) || 1));
    const layout = scoreSystemLayout(measureCount, container.clientWidth);
    const measureWidth = (layout.width - 24) / layout.columns;
    const renderer = new VF.Renderer(container, VF.Renderer.Backends.SVG);
    renderer.resize(layout.width, layout.height);
    const context = renderer.getContext();
    const renderedNotes = [];
    const beams = [];
    for (let measure = 1; measure <= measureCount; measure += 1) {
      const column = (measure - 1) % layout.columns;
      const system = Math.floor((measure - 1) / layout.columns);
      const systemStart = column === 0;
      const x = 12 + column * measureWidth;
      const stave = new VF.Stave(x, 42 + system * layout.systemHeight, measureWidth);
      if (systemStart) {
        stave.addClef("treble");
        if (typeof stave.addKeySignature === "function") stave.addKeySignature(score.arrangementKey || "C");
        if (measure === 1) stave.addTimeSignature(score.meter);
      }
      stave.setContext(context).draw();
      const sourceEvents = score.melody.map((event, index) => ({ event, index })).filter((item) => Number(item.event.measure) === measure);
      if (!sourceEvents.length) continue;
      const notes = sourceEvents.map(({ event, index }) => {
        const pitchValues = event.rest ? [] : (event.pitches?.length ? event.pitches : [event.pitchValue]);
        const pitchMatches = pitchValues.map((value) => pitchLabel(value).match(/^([A-G])([#b]?)(-?\d+)$/));
        const keys = event.rest ? ["b/4"] : pitchMatches.map((match) => `${(match?.[1] || "B").toLowerCase()}/${match?.[3] || "4"}`);
        const note = new VF.StaveNote({ clef: "treble", keys, duration: vexDuration(event) });
        if (!event.rest && VF.Accidental) {
          pitchMatches.forEach((match, pitchIndex) => {
            if (match?.[2]) note.addModifier(new VF.Accidental(match[2]), pitchIndex);
          });
        }
        if ([1.5, 3].includes(Number(event.durationBeats)) && VF.Dot?.buildAndAttach) VF.Dot.buildAndAttach([note], { all: true });
        const chord = chordChangeAtEvent(draft, event);
        if (chord && VF.Annotation) note.addModifier(new VF.Annotation(chord).setVerticalJustification(VF.Annotation.VerticalJustify.TOP), 0);
        if (event.lyric && VF.Annotation) note.addModifier(new VF.Annotation(event.lyric).setVerticalJustification(VF.Annotation.VerticalJustify.BOTTOM), 0);
        const articulationCode = { accent: "a>", tenuto: "a-", staccato: "a." }[event.articulation];
        if (articulationCode && VF.Articulation) note.addModifier(new VF.Articulation(articulationCode), 0);
        renderedNotes.push({ note, event, index });
        return note;
      });
      const capacity = measure === 1 && Number(score.pickupBeats) > 0 ? Number(score.pickupBeats) : beatsPerMeasure(draft);
      const voice = new VF.Voice({ numBeats: capacity, beatValue: 4 });
      if (VF.Voice.Mode?.SOFT !== undefined) voice.setMode(VF.Voice.Mode.SOFT);
      voice.addTickables(notes);
      new VF.Formatter().joinVoices([voice]).format([voice], measureWidth - (systemStart ? (measure === 1 ? 104 : 84) : 34));
      voice.draw(context, stave);
      if (VF.Beam?.generateBeams) beams.push(...VF.Beam.generateBeams(notes));
    }
    beams.forEach((beam) => beam.setContext(context).draw());
    renderedNotes.forEach(({ note, event, index }) => {
      const element = typeof note.getSVGElement === "function" ? note.getSVGElement() : null;
      if (!element) return;
      element.classList.add("score-event");
      if (index === selectedIndex) {
        element.classList.add("is-selected");
        element.setAttribute("aria-current", "true");
      }
      element.dataset.origin = event.origin || "source";
      element.setAttribute("role", "button");
      element.setAttribute("tabindex", "0");
      const pitchNames = (event.pitches?.length ? event.pitches : [event.pitchValue]).map(pitchLabel).join(", ");
      element.setAttribute("aria-label", event.rest ? `Rest ${index + 1}` : `${pitchNames}, note ${index + 1}`);
      const select = () => typeof onSelect === "function" && onSelect(index);
      element.addEventListener("click", select);
      element.addEventListener("keydown", (keyboardEvent) => {
        if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") select();
      });
    });
    if (VF.StaveTie) {
      renderedNotes.forEach((item, index) => {
        const next = renderedNotes[index + 1];
        if (item.event.tie === "start" && next && Number(next.event.pitchValue) === Number(item.event.pitchValue)) {
          new VF.StaveTie({ first_note: item.note, last_note: next.note, first_indices: [0], last_indices: [0] }).setContext(context).draw();
        }
      });
    }
    const svg = container.querySelector("svg");
    if (svg) {
      svg.classList.add("score-svg");
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-label", `${draft.source.title} melody staff`);
      renderedNotes.forEach((target, index) => {
        const transition = target.event.transitionFromPrevious;
        const source = renderedNotes[index - 1];
        if (!transition || !source) return;
        const sourceElement = source.note.getSVGElement?.();
        const targetElement = target.note.getSVGElement?.();
        if (!sourceElement || !targetElement || typeof sourceElement.getBBox !== "function") return;
        const sourceBox = sourceElement.getBBox();
        const targetBox = targetElement.getBBox();
        const voices = transitionScoreVoices(target.event);
        if (!voices.length) return;
        const sameSystem = Math.floor((Number(source.event.measure) - 1) / layout.columns) === Math.floor((Number(target.event.measure) - 1) / layout.columns);
        if (sameSystem) {
          voices.forEach((voice) => {
            const overlay = global.document.createElementNS("http://www.w3.org/2000/svg", "line");
            overlay.setAttribute("class", "score-gliss");
            overlay.setAttribute("data-transition-string", String(voice.string || ""));
            overlay.setAttribute("x1", String(sourceBox.x + sourceBox.width));
            overlay.setAttribute("y1", String(vexVoiceY(source, voice.fromPitchValue, sourceBox)));
            overlay.setAttribute("x2", String(targetBox.x));
            overlay.setAttribute("y2", String(vexVoiceY(target, voice.toPitchValue, targetBox)));
            svg.appendChild(overlay);
          });
        } else {
          const overlay = global.document.createElementNS("http://www.w3.org/2000/svg", "text");
          overlay.setAttribute("class", "score-gliss-label");
          overlay.setAttribute("x", String(targetBox.x));
          overlay.setAttribute("y", String(Math.max(12, targetBox.y - 5)));
          overlay.textContent = "gliss.";
          svg.appendChild(overlay);
        }
        if (transition.controlAnnotation) {
          const annotation = global.document.createElementNS("http://www.w3.org/2000/svg", "text");
          annotation.setAttribute("class", "score-control-annotation");
          annotation.setAttribute("x", String(targetBox.x));
          annotation.setAttribute("y", String(Math.max(12, targetBox.y - 18)));
          annotation.textContent = transition.controlAnnotation;
          svg.appendChild(annotation);
        }
      });
    }
    container.dataset.scoreRenderer = "vexflow-5.0.0";
    return true;
  }

  function renderFallback(container, draft, selectedIndex = -1, onSelect) {
    if (!container || typeof document === "undefined") return;
    container.replaceChildren();
    const score = reflowDraft(draft).score;
    const measures = Math.max(1, ...score.melody.map((event) => Number(event.measure) || 1));
    const layout = scoreSystemLayout(measures, container.clientWidth);
    const measureWidth = (layout.width - 24) / layout.columns;
    const width = layout.width;
    const height = layout.height;
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", `${draft.source.title} melody staff`);
    svg.classList.add("score-svg");
    const make = (name, attrs = {}) => {
      const node = document.createElementNS("http://www.w3.org/2000/svg", name);
      Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
      return node;
    };
    for (let system = 0; system < layout.systems; system += 1) {
      const y = 70 + system * layout.systemHeight;
      for (let line = 0; line < 5; line += 1) svg.appendChild(make("line", { x1: 18, y1: y + line * 14, x2: width - 18, y2: y + line * 14, class: "staff-line" }));
      const clef = make("text", { x: 28, y: y + 49, class: "score-clef" });
      clef.textContent = "𝄞";
      svg.appendChild(clef);
    }
    for (let measure = 1; measure <= measures; measure += 1) {
      const column = (measure - 1) % layout.columns;
      const system = Math.floor((measure - 1) / layout.columns);
      const y = 70 + system * layout.systemHeight;
      svg.appendChild(make("line", { x1: 24 + column * measureWidth, y1: y, x2: 24 + column * measureWidth, y2: y + 56, class: "bar-line" }));
      if (column === layout.columns - 1 || measure === measures) svg.appendChild(make("line", { x1: 24 + (column + 1) * measureWidth, y1: y, x2: 24 + (column + 1) * measureWidth, y2: y + 56, class: "bar-line" }));
    }
    score.harmony.forEach((item) => {
      const beats = beatsPerMeasure(draft);
      const measureIndex = Number(item.measure) - 1;
      const column = measureIndex % layout.columns;
      const system = Math.floor(measureIndex / layout.columns);
      const x = 55 + column * measureWidth + ((Number(item.beat) - 1) / beats) * (measureWidth - 40);
      const text = make("text", { x, y: 45 + system * layout.systemHeight, class: "chord-symbol" });
      text.textContent = item.symbol;
      svg.appendChild(text);
    });
    const fallbackPoints = [];
    score.melody.forEach((event, index) => {
      const beats = beatsPerMeasure(draft);
      const measureIndex = Number(event.measure) - 1;
      const column = measureIndex % layout.columns;
      const system = Math.floor(measureIndex / layout.columns);
      const x = 55 + column * measureWidth + ((Number(event.beat) - 1) / beats) * (measureWidth - 40);
      const group = make("g", { class: `score-event${index === selectedIndex ? " is-selected" : ""}`, tabindex: "0", role: "button", "aria-label": event.rest ? `Rest ${index + 1}` : `${event.pitch}, note ${index + 1}` });
      group.dataset.origin = event.origin || "source";
      if (event.rest) {
        const rest = make("text", { x: x - 8, y: 104 + system * layout.systemHeight, class: "rest-mark" });
        rest.textContent = "𝄽";
        group.appendChild(rest);
      } else {
        const pitchValues = event.pitches?.length ? event.pitches : [event.pitchValue];
        const noteYs = pitchValues.map((value) => 126 + system * layout.systemHeight - (staffStep(value) + 2) * 7);
        noteYs.forEach((y, pitchIndex) => {
          group.appendChild(make("ellipse", { cx: x, cy: y, rx: 9, ry: 6.5, transform: `rotate(-18 ${x} ${y})`, class: "note-head" }));
          const pitch = pitchLabel(pitchValues[pitchIndex]);
          if (pitch.includes("#") || pitch.includes("b")) {
            const accidental = make("text", { x: x - 24, y: y + 5, class: "accidental" });
            accidental.textContent = pitch.includes("#") ? "♯" : "♭";
            group.appendChild(accidental);
          }
        });
        const stemY = Math.min(...noteYs);
        if (Number(event.durationBeats) < 4) group.appendChild(make("line", { x1: x + 8, y1: Math.max(...noteYs), x2: x + 8, y2: stemY - 38, class: "note-stem" }));
      }
      const duration = make("text", { x: x - 14, y: 160 + system * layout.systemHeight, class: "duration-label" });
      duration.textContent = durationName(event.durationBeats).replaceAll("_", " ");
      group.appendChild(duration);
      if (event.lyric) {
        const lyric = make("text", { x: x - 12, y: 180 + system * layout.systemHeight, class: "lyric-label" });
        lyric.textContent = event.lyric;
        group.appendChild(lyric);
      }
      if (event.articulation) {
        const articulation = make("text", { x: x - 5, y: 53 + system * layout.systemHeight, class: "articulation-label" });
        articulation.textContent = ({ accent: ">", tenuto: "—", staccato: "•" })[event.articulation] || "";
        group.appendChild(articulation);
      }
      const select = () => typeof onSelect === "function" && onSelect(index);
      group.addEventListener("click", select);
      group.addEventListener("keydown", (eventObject) => {
        if (eventObject.key === "Enter" || eventObject.key === " ") select();
      });
      svg.appendChild(group);
      const pitchValues = event.pitches?.length ? event.pitches : [event.pitchValue];
      const pitchYs = Object.fromEntries(pitchValues.map((value) => [String(value), 126 + system * layout.systemHeight - (staffStep(value) + 2) * 7]));
      fallbackPoints.push({ x, y: event.rest ? 104 + system * layout.systemHeight : pitchYs[String(event.pitchValue)], pitchYs, system, event });
    });
    fallbackPoints.forEach((target, index) => {
      const source = fallbackPoints[index - 1];
      const transition = target.event.transitionFromPrevious;
      const voices = transitionScoreVoices(target.event);
      if (!transition || !source || !voices.length) return;
      if (source.system === target.system) {
        voices.forEach((voice) => {
          const fromY = source.pitchYs[String(voice.fromPitchValue)] ?? source.y;
          const toY = target.pitchYs[String(voice.toPitchValue)] ?? target.y;
          svg.appendChild(make("line", { x1: source.x + 10, y1: fromY, x2: target.x - 10, y2: toY, class: "score-gliss", "data-transition-string": voice.string || "" }));
        });
      } else {
        const label = make("text", { x: target.x - 5, y: target.y - 14, class: "score-gliss-label" });
        label.textContent = "gliss.";
        svg.appendChild(label);
      }
      if (transition.controlAnnotation) {
        const annotation = make("text", { x: target.x - 5, y: target.y - 28, class: "score-control-annotation" });
        annotation.textContent = transition.controlAnnotation;
        svg.appendChild(annotation);
      }
    });
    container.appendChild(svg);
    container.dataset.scoreRenderer = "fallback-svg";
  }

  function render(container, draft, selectedIndex = -1, onSelect) {
    if (!container || typeof document === "undefined") return;
    try {
      if (renderWithVexFlow(container, draft, selectedIndex, onSelect)) return;
    } catch (_error) {
      container.replaceChildren();
    }
    renderFallback(container, draft, selectedIndex, onSelect);
  }

  function renderPreview(container) {
    if (!container || !global.document?.createElement) return false;
    try {
      container.replaceChildren();
      const image = global.document.createElement("img");
      image.classList.add("home-melody-score-image");
      image.src = "assets/landing/melody-score.png?v=updated-score-artwork-20260714-1";
      image.alt = "";
      image.width = 1452;
      image.height = 484;
      image.decoding = "async";
      image.draggable = false;
      image.dataset.previewKind = "approved-melody-score-png";
      container.appendChild(image);
      container.dataset.scoreRenderer = "static-png-preview";
      return true;
    } catch (_error) {
      container.replaceChildren();
      delete container.dataset.scoreRenderer;
      return false;
    }
  }

  const api = {
    DURATIONS,
    MAX_EVENTS,
    MAX_MEASURES,
    scoreSystemLayout,
    pitchLabel,
    createDraft,
    cloneDraft,
    beatsPerMeasure,
    reflowDraft,
    addEvent,
    updateEvent,
    removeEvent,
    clearMeasure,
    duplicatePhrase,
    transposeDraft,
    setChordAtEvent,
    chordForEvent,
    chordChangeAtEvent,
    arrangementEvents,
    draftWarnings,
    durationName,
    musicXmlForDraft,
    render,
    renderPreview
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  global.STEEL_RAG_MELODY_SCORE = api;
})(typeof window !== "undefined" ? window : globalThis);
