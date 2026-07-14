(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.STEEL_RAG_COPEDENT_GRID = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const PITCH_CLASSES = Object.freeze({
    C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5,
    "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11
  });
  const SHARP_NOTES = Object.freeze(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]);
  const LEVER_ORDER = Object.freeze(["LKL", "LKV", "LKR", "RKL", "RKR"]);
  const TRAVEL_ORDER = Object.freeze({
    "half": 0, "half-stop": 0, "half_stop": 0,
    "full": 1, "full-stop": 1, "full_stop": 1,
    "vertical": 2, "split": 3, "pedal": 4
  });

  function clone(value) {
    return value == null ? value : JSON.parse(JSON.stringify(value));
  }

  function pitchClass(note) {
    const token = String(note || "").trim().match(/^[A-Ga-g](?:#|b)?/)?.[0];
    if (!token) return null;
    const normalized = token[0].toUpperCase() + token.slice(1);
    return Number.isInteger(PITCH_CLASSES[normalized]) ? PITCH_CLASSES[normalized] : null;
  }

  function semitoneDelta(fromNote, toNote, direction = "") {
    const from = pitchClass(fromNote);
    const to = pitchClass(toNote);
    if (!Number.isInteger(from) || !Number.isInteger(to)) return null;
    const delta = (((to - from + 6) % 12) + 12) % 12 - 6;
    if (delta === -6 && String(direction).toLowerCase() === "raise") return 6;
    return delta;
  }

  function destinationForDelta(fromNote, delta) {
    const start = pitchClass(fromNote);
    const amount = Number(delta);
    if (!Number.isInteger(start) || !Number.isFinite(amount)) return "";
    return SHARP_NOTES[((start + amount) % 12 + 12) % 12];
  }

  function changeDirection(delta) {
    if (Number(delta) < 0) return "lower";
    if (Number(delta) > 0) return "raise";
    return "none";
  }

  function formatCell(change) {
    if (!change) return { label: "", delta: 0, direction: "none" };
    const delta = semitoneDelta(change.fromNote, change.toNote, change.changeType || change.direction);
    if (!Number.isInteger(delta) || delta === 0) {
      return { label: String(change.toNote || ""), delta: delta || 0, direction: "none" };
    }
    return {
      label: `${change.toNote} ${delta > 0 ? "↑" : "↓"}${Math.abs(delta)}`,
      delta,
      direction: changeDirection(delta)
    };
  }

  function normalizedPosition(control) {
    return String(control?.physicalPosition || control?.physical_position || control?.label || control?.id || "Unplaced").trim() || "Unplaced";
  }

  function normalizedType(control) {
    return String(control?.type || control?.control_type || "lever").toLowerCase() === "pedal" ? "pedal" : "lever";
  }

  function travelRank(travel) {
    const key = String(travel || "full").toLowerCase();
    return Object.prototype.hasOwnProperty.call(TRAVEL_ORDER, key) ? TRAVEL_ORDER[key] : 9;
  }

  function travelLabel(control, groupSize) {
    if (normalizedType(control) === "pedal") return String(control.id || control.label || normalizedPosition(control));
    const travel = String(control.travel || "full").toLowerCase();
    if (travel === "half" || travel === "half-stop" || travel === "half_stop") return "½";
    if (travel === "full" || travel === "full-stop" || travel === "full_stop") return groupSize > 1 ? "Full" : String(control.label || "Full");
    if (travel === "vertical") return "Vertical";
    if (travel === "split") return "Split";
    return String(control.label || control.travel || "State");
  }

  function project(profile) {
    const source = clone(profile || {});
    const strings = (source.strings || []).slice().sort((a, b) => Number(a.stringNumber) - Number(b.stringNumber));
    const pedalOrder = Array.isArray(source.pedalOrder) ? source.pedalOrder.map(String) : [];
    const controls = (source.controls || []).map((control, index) => ({ ...control, _sourceIndex: index }));
    const groupMap = new Map();

    controls.forEach((control) => {
      const type = normalizedType(control);
      const physicalPosition = normalizedPosition(control);
      const key = `${type}:${physicalPosition.toUpperCase()}`;
      if (!groupMap.has(key)) {
        groupMap.set(key, { key, type, physicalPosition, controls: [], sourceIndex: control._sourceIndex });
      }
      groupMap.get(key).controls.push(control);
    });

    const groups = Array.from(groupMap.values()).map((group) => {
      group.controls.sort((a, b) => travelRank(a.travel) - travelRank(b.travel) || a._sourceIndex - b._sourceIndex);
      const orderIndexes = group.controls.map((control) => pedalOrder.indexOf(String(control.id))).filter((index) => index >= 0);
      const pedalIndex = orderIndexes.length ? Math.min(...orderIndexes) : Number.POSITIVE_INFINITY;
      const leverIndex = LEVER_ORDER.indexOf(group.physicalPosition.toUpperCase());
      return {
        ...group,
        pedalIndex,
        leverIndex: leverIndex < 0 ? LEVER_ORDER.length : leverIndex,
        states: group.controls.map((control) => ({
          id: String(control.id),
          label: String(control.label || control.id),
          type: normalizedType(control),
          physicalPosition: group.physicalPosition,
          travel: String(control.travel || (group.type === "pedal" ? "pedal" : "full")),
          headerLabel: travelLabel(control, group.controls.length),
          aliases: clone(control.aliases || []),
          notes: String(control.notes || "")
        }))
      };
    });

    groups.sort((a, b) => {
      if (a.type !== b.type) return a.type === "pedal" ? -1 : 1;
      if (a.type === "pedal") return a.pedalIndex - b.pedalIndex || a.sourceIndex - b.sourceIndex;
      return a.leverIndex - b.leverIndex || a.physicalPosition.localeCompare(b.physicalPosition) || a.sourceIndex - b.sourceIndex;
    });

    const cells = {};
    controls.forEach((control) => {
      (control.changes || []).forEach((change) => {
        const stringNumber = Number(change.stringNumber || change.string);
        cells[`${stringNumber}:${control.id}`] = {
          controlId: String(control.id),
          stringNumber,
          change: clone(change),
          ...formatCell(change)
        };
      });
    });

    return {
      profile: source,
      strings,
      groups,
      pedalGroups: groups.filter((group) => group.type === "pedal"),
      leverGroups: groups.filter((group) => group.type === "lever"),
      states: groups.flatMap((group) => group.states),
      cells
    };
  }

  function setCell(profile, controlId, stringNumber, delta) {
    const next = clone(profile || {});
    const control = (next.controls || []).find((item) => String(item.id) === String(controlId));
    if (!control) throw new Error("Control state not found.");
    const string = (next.strings || []).find((item) => Number(item.stringNumber) === Number(stringNumber));
    if (!string) throw new Error("String not found.");
    control.changes = Array.isArray(control.changes) ? control.changes : [];
    const index = control.changes.findIndex((change) => Number(change.stringNumber || change.string) === Number(stringNumber));
    const amount = Number(delta);
    if (!Number.isFinite(amount) || amount === 0) {
      if (index >= 0) control.changes.splice(index, 1);
      return next;
    }
    if (!Number.isInteger(amount) || Math.abs(amount) > 6) throw new Error("Choose a whole-number semitone change between -6 and 6.");
    const fromNote = String(string.openNote || string.open_note || "");
    const toNote = destinationForDelta(fromNote, amount);
    if (!toNote) throw new Error("Set this string's open note before adding a change.");
    const previous = index >= 0 ? control.changes[index] : {};
    const change = {
      stringNumber: Number(stringNumber),
      fromNote,
      toNote,
      changeType: changeDirection(amount),
      notes: String(previous.notes || "")
    };
    if (index >= 0) control.changes[index] = change;
    else control.changes.push(change);
    control.changes.sort((a, b) => Number(a.stringNumber || a.string) - Number(b.stringNumber || b.string));
    return next;
  }

  function scientificPitch(midiValue, fallbackNote) {
    const midi = Number(midiValue);
    if (!Number.isInteger(midi)) return { note: String(fallbackNote || ""), octave: "" };
    return { note: SHARP_NOTES[((midi % 12) + 12) % 12], octave: Math.floor(midi / 12) - 1 };
  }

  function midiForPitch(note, octave) {
    const pitch = pitchClass(note);
    const register = Number(octave);
    if (!Number.isInteger(pitch) || !Number.isInteger(register)) return null;
    return (register + 1) * 12 + pitch;
  }

  return {
    PITCH_CLASSES, SHARP_NOTES, LEVER_ORDER,
    clone, pitchClass, semitoneDelta, destinationForDelta, changeDirection,
    formatCell, project, setCell, scientificPitch, midiForPitch
  };
});
