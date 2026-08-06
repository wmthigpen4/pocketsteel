"""Interactive E9 Explorer browser-contract regression tests."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_e9_fretboard_explorer_controls_are_mode_aware() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function makeClassList() {
  const names = new Set();
  return {
    add: (...items) => items.forEach((item) => names.add(item)),
    remove: (...items) => items.forEach((item) => names.delete(item)),
    toggle: (item, force) => {
      if (force === true) {
        names.add(item);
        return true;
      }
      if (force === false) {
        names.delete(item);
        return false;
      }
      if (names.has(item)) {
        names.delete(item);
        return false;
      }
      names.add(item);
      return true;
    },
    contains: (item) => names.has(item),
    toString: () => Array.from(names).join(" ")
  };
}

class FakeSelect {
  constructor(id, value, options) {
    this.id = id;
    this.value = value;
    this.options = options.map((item) => ({ ...item, disabled: false }));
    this.selectedIndex = Math.max(0, this.options.findIndex((item) => item.value === value));
    this.disabled = false;
    this.listeners = {};
    this._innerHTML = "";
  }
  addEventListener(type, handler) {
    this.listeners[type] = handler;
  }
  dispatchChange() {
    this.selectedIndex = Math.max(0, this.options.findIndex((item) => item.value === this.value));
    this.options.forEach((item) => {
      item.selected = item.value === this.value;
    });
    this.listeners.change();
  }
  selectValues(values) {
    const selectedValues = new Set(values);
    this.options.forEach((item) => {
      item.selected = selectedValues.has(item.value);
    });
    this.value = values[0] || this.options[0]?.value || "";
    this.selectedIndex = Math.max(0, this.options.findIndex((item) => item.value === this.value));
    this.listeners.change();
  }
  get selectedOptions() {
    return this.options.filter((item) => item.selected);
  }
  set innerHTML(value) {
    this._innerHTML = value;
    const matches = Array.from(value.matchAll(/<option value="([^"]+)"([^>]*)>([^<]+)<\/option>/g));
    this.options = matches.map((match) => ({
      value: match[1],
      selected: match[2].includes("selected"),
      text: match[3],
      disabled: false
    }));
    const selected = this.options.find((item) => item.selected);
    if (selected) {
      this.value = selected.value;
    } else if (!this.options.some((item) => item.value === this.value)) {
      this.value = this.options[0]?.value || "";
    }
    this.selectedIndex = Math.max(0, this.options.findIndex((item) => item.value === this.value));
  }
  get innerHTML() {
    return this._innerHTML;
  }
}

class FakeNode {
  constructor(id) {
    this.id = id;
    this.hidden = false;
    this.textContent = "";
    this._innerHTML = "";
    this._markers = [];
    this.attributes = {};
    this.listeners = {};
    this.style = {};
    this.className = "";
    this.classList = makeClassList();
    this._buttons = {};
  }
  set innerHTML(value) {
    this._innerHTML = value;
    this.textContent = value.replace(/<[^>]*>/g, "");
    this._markers = Array.from(value.matchAll(/data-highlight-id="([^"]+)"/g)).map((match) => new FakeMarker(match[1]));
    const noteCells = Array.from(value.matchAll(/<button[\s\S]*?data-note-cell="([^"]+)"[\s\S]*?<\/button>/g)).map((match) => {
      const rawButton = match[0];
      const button = new FakeButton(match[1], "data-note-cell");
      button.attributes["data-note-string"] = (rawButton.match(/data-note-string="([^"]+)"/) || [])[1] || "";
      button.attributes["data-note-fret"] = (rawButton.match(/data-note-fret="([^"]+)"/) || [])[1] || "";
      const result = (rawButton.match(/data-note-result="([^"]+)"/) || [])[1];
      if (result) {
        button.attributes["data-note-result"] = result;
      }
      return button;
    });
    this._buttons = {
      "[data-explorer-row]": Array.from(value.matchAll(/data-explorer-row="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-explorer-row")),
      "[data-active-result-row]": Array.from(value.matchAll(/data-active-result-row="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-active-result-row")),
      "[data-path-step]": Array.from(value.matchAll(/data-path-step="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-path-step")),
      "[data-path-display-mode]": Array.from(value.matchAll(/data-path-display-mode="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-path-display-mode")),
      "[data-path-compare-row]": Array.from(value.matchAll(/data-path-compare-row="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-path-compare-row")),
      "[data-path-prev]": value.includes("data-path-prev") ? [new FakeButton("previous", "data-path-prev")] : [],
      "[data-path-next]": value.includes("data-path-next") ? [new FakeButton("next", "data-path-next")] : [],
      "[data-control-impact-tab]": Array.from(value.matchAll(/data-control-impact-tab="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-control-impact-tab")),
      "[data-top-interval-filter]": Array.from(value.matchAll(/data-top-interval-filter="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-top-interval-filter")),
      "[data-fret-range-filter]": Array.from(value.matchAll(/data-fret-range-filter="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-fret-range-filter")),
      "[data-control-impact-clear]": value.includes("data-control-impact-clear") ? [new FakeButton("clear", "data-control-impact-clear")] : [],
          "[data-note-workflow]": Array.from(value.matchAll(/data-note-workflow="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-workflow")),
          "[data-note-target-mode]": Array.from(value.matchAll(/data-note-target-mode="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-target-mode")),
          "[data-note-control-state]": Array.from(value.matchAll(/data-note-control-state="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-control-state")),
      "[data-note-target]": Array.from(value.matchAll(/data-note-target="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-target")),
      "[data-note-string-filter]": Array.from(value.matchAll(/data-note-string-filter="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-string-filter")),
      "[data-note-cell]": noteCells,
      "[data-note-result]": Array.from(value.matchAll(/data-note-result="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-result")),
      "[data-note-result-card]": Array.from(value.matchAll(/data-note-result-card="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-result-card")),
      "[data-note-result-list]": Array.from(value.matchAll(/data-note-result-list="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-result-list")),
      "[data-note-reverse-result]": Array.from(value.matchAll(/data-note-reverse-result="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-reverse-result")),
      "[data-note-grip-target]": Array.from(value.matchAll(/data-note-grip-target="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-grip-target")),
      "[data-note-grip-vocabulary]": Array.from(value.matchAll(/data-note-grip-vocabulary="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-grip-vocabulary")),
      "[data-note-grip-role]": Array.from(value.matchAll(/data-note-grip-role="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-grip-role")),
      "[data-note-grip-card]": Array.from(value.matchAll(/data-note-grip-card="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-grip-card")),
      "[data-note-sync-event]": Array.from(value.matchAll(/data-note-sync-event="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-note-sync-event")),
      "[data-voicing-control]": Array.from(value.matchAll(/data-voicing-control="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-voicing-control")),
      "[data-voicing-control-clear]": value.includes("data-voicing-control-clear") ? [new FakeButton("clear", "data-voicing-control-clear")] : [],
      "[data-voicing-string]": Array.from(value.matchAll(/data-voicing-string="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-voicing-string")),
      "[data-chord-finder-result]": Array.from(value.matchAll(/data-chord-finder-result="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-chord-finder-result")),
      "[data-chord-map-filter-control]": Array.from(value.matchAll(/data-chord-map-filter-control="([^"]+)"/g)).map((match) => new FakeButton(match[1], "data-chord-map-filter-control"))
    };
  }
  get innerHTML() {
    return this._innerHTML;
  }
  querySelectorAll(selector) {
    if (this._buttons[selector]) {
      return this._buttons[selector] || [];
    }
    if (selector === ".pedal-steel-fretboard__highlight[data-highlight-id]") {
      return this._markers;
    }
    if (selector === ".pedal-steel-fretboard__highlight.is-explorer-hover-marker") {
      return this._markers.filter((marker) => marker.classList.contains("is-explorer-hover-marker"));
    }
    return [];
  }
  querySelector(selector) {
    const markerMatch = selector.match(/^\.pedal-steel-fretboard__highlight\[data-highlight-id="([^"]+)"\]$/);
    if (markerMatch) {
      return this._markers.find((marker) => marker.getAttribute("data-highlight-id") === markerMatch[1]) || null;
    }
    return this.querySelectorAll(selector)[0] || null;
  }
  addEventListener(type, handler) {
    this.listeners[type] = handler;
  }
  getAttribute(name) {
    return this.attributes[name] || null;
  }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
  }
  focus() {}
}

class FakeDialog extends FakeNode {
  constructor(id) {
    super(id);
    this.open = false;
  }
  showModal() {
    this.open = true;
  }
  close() {
    this.open = false;
    if (this.listeners.close) {
      this.listeners.close();
    }
  }
}

class FakeButton {
  constructor(rowId, attributeName = "data-explorer-row") {
    this.rowId = rowId;
    this.attributeName = attributeName;
    this.attributes = { [attributeName]: rowId };
    this.classList = makeClassList();
  }
  getAttribute(name) {
    return this.attributes[name] || null;
  }
  setAttribute(name, value) {
    this.attributes[name] = value;
  }
  addEventListener(type, handler) {
    this[`on${type}`] = handler;
  }
  focus() {}
}

class FakeMarker extends FakeButton {
  constructor(rowId) {
    super(rowId);
    this.attributes["data-highlight-id"] = rowId;
  }
  getBoundingClientRect() {
    return { left: 40, top: 50, width: 20, height: 20 };
  }
}

const elements = {
  "explorer-key": new FakeSelect("explorer-key", "G", [
    { value: "C", text: "C" },
    { value: "Db", text: "C# (or D♭)" },
    { value: "D", text: "D" },
    { value: "Eb", text: "D# (or E♭)" },
    { value: "E", text: "E" },
    { value: "F", text: "F" },
    { value: "Gb", text: "F# (or G♭)" },
    { value: "G", text: "G" },
    { value: "Ab", text: "G# (or A♭)" },
    { value: "A", text: "A" },
    { value: "Bb", text: "A# (or B♭)" },
    { value: "B", text: "B" }
  ]),
  "explorer-copedent": new FakeSelect("explorer-copedent", "emmons-e9-basic", [
    { value: "emmons-e9-basic", text: "Emmons E9" },
    { value: "day-e9-basic", text: "Day E9" }
  ]),
  "explorer-explore-mode": new FakeSelect("explorer-explore-mode", "single", [
    { value: "single", text: "Single grip" },
    { value: "path", text: "Harmonized scale path" },
    { value: "note", text: "Single-note finder" },
    { value: "voicing", text: "Voicing identifier" },
    { value: "chord", text: "Chord / Voicing Finder" }
  ]),
  "explorer-scale": new FakeSelect("explorer-scale", "major", [
    { value: "major", text: "G major" },
    { value: "natural_minor", text: "G natural minor" }
  ]),
  "explorer-harmony": new FakeSelect("explorer-harmony", "three_string_diatonic", [
    { value: "two_string_harmonized", text: "2-string harmonized scale" },
    { value: "three_string_diatonic", text: "3-string diatonic harmony" }
  ]),
  "explorer-harmony-control": new FakeNode("explorer-harmony-control"),
  "explorer-grip-vocabulary": new FakeSelect("explorer-grip-vocabulary", "core", [
    { value: "core", text: "Core" },
    { value: "extended", text: "Extended" },
    { value: "song_tab", text: "Song/tab vocabulary" },
    { value: "e_lower_pockets", text: "E-lower pockets" },
    { value: "two_string", text: "Two-string" },
    { value: "all", text: "All legitimate" }
  ]),
  "explorer-grip-vocabulary-control": new FakeNode("explorer-grip-vocabulary-control"),
  "explorer-string-group": new FakeSelect("explorer-string-group", "4-5-6", [
    { value: "all", text: "All 3-string groups" },
    { value: "4-5-6", text: "4-5-6", selected: true }
  ]),
  "explorer-string-group-control": new FakeNode("explorer-string-group-control"),
  "explorer-path-family": new FakeSelect("explorer-path-family", "low", [
    { value: "high", text: "High path: 3-4-5 / 4-5-6" },
    { value: "middle", text: "Middle path: 5-6-8 / 5-6-7" },
    { value: "low", text: "Low path: 6-8-10 / 6-7-10" }
  ]),
  "explorer-path-family-control": new FakeNode("explorer-path-family-control"),
  "explorer-scale-notes": new FakeNode("explorer-scale-notes"),
  "explorer-result-count": new FakeNode("explorer-result-count"),
  "explorer-top-interval-filter": new FakeNode("explorer-top-interval-filter"),
  "explorer-fret-range-filter": new FakeNode("explorer-fret-range-filter"),
  "explorer-copedent-dialog": new FakeDialog("explorer-copedent-dialog"),
  "explorer-copedent-open": new FakeButton("open", "id"),
  "explorer-copedent-close": new FakeButton("close", "id"),
  "explorer-copedent-chart": new FakeNode("explorer-copedent-chart"),
  "explorer-control-impact-preview": new FakeNode("explorer-control-impact-preview"),
  "explorer-string-action-label-toggle": new FakeButton("string-labels", "id"),
  "explorer-note-finder": new FakeNode("explorer-note-finder"),
  "explorer-voicing-identifier": new FakeNode("explorer-voicing-identifier"),
  "explorer-chord-finder": new FakeNode("explorer-chord-finder"),
  "explorer-active-results": new FakeNode("explorer-active-results"),
  "explorer-fretboard": new FakeNode("explorer-fretboard"),
  "explorer-row-list": new FakeNode("explorer-row-list"),
  "explorer-selected-detail": new FakeNode("explorer-selected-detail"),
  "explorer-empty": new FakeNode("explorer-empty"),
  "explorer-tooltip": new FakeNode("explorer-tooltip"),
  "explorer-voicing-fret": new FakeSelect("explorer-voicing-fret", "3", Array.from({ length: 10 }, (_, index) => {
    const value = String(index + 1);
    return { value, text: value };
  })),
  "explorer-chord-root": new FakeSelect("explorer-chord-root", "F", [{ value: "F", text: "F" }]),
  "explorer-chord-quality": new FakeSelect("explorer-chord-quality", "major7", [{ value: "major7", text: "Major 7" }]),
  "explorer-chord-control-scope": new FakeSelect("explorer-chord-control-scope", "common", [{ value: "common", text: "Common controls" }]),
};
let lastMount;
const notationModeButtons = [
  new FakeButton("notes", "data-explorer-notation-mode"),
  new FakeButton("nns", "data-explorer-notation-mode"),
  new FakeButton("roman", "data-explorer-notation-mode"),
  new FakeButton("numbers", "data-explorer-notation-mode")
];
const pitchRegisterButtons = [
  new FakeButton("off", "data-explorer-pitch-register"),
  new FakeButton("scientific", "data-explorer-pitch-register"),
  new FakeButton("band", "data-explorer-pitch-register")
];
const modeButtons = [
  new FakeButton("single", "data-explorer-mode-tab"),
  new FakeButton("path", "data-explorer-mode-tab"),
  new FakeButton("note", "data-explorer-mode-tab"),
  new FakeButton("voicing", "data-explorer-mode-tab"),
  new FakeButton("chord", "data-explorer-mode-tab")
];
const taskCards = [
  ["find-chord", "chord"],
  ["find-note", "note"],
  ["explore-grip", "single"],
  ["walk-harmonized-scale", "path"],
  ["study-movement-path", "path"],
  ["identify-voicing", "voicing"]
].map(([taskId, modeId]) => {
  const button = new FakeButton(taskId, "data-explorer-task-card");
  button.attributes["data-explorer-task-mode"] = modeId;
  return button;
});
const taskCard = (taskId) => taskCards.find((button) => button.getAttribute("data-explorer-task-card") === taskId);
const sandbox = {
  window: {
    innerWidth: 1280,
    innerHeight: 720,
  },
  document: {
    activeElement: null,
    getElementById: (id) => elements[id],
    querySelectorAll: (selector) => {
      if (selector === "[data-explorer-notation-mode]") {
        return notationModeButtons;
      }
      if (selector === "[data-explorer-pitch-register]") {
        return pitchRegisterButtons;
      }
      if (selector === "[data-explorer-mode-tab]") {
        return modeButtons;
      }
      if (selector === "[data-explorer-task-card]") {
        return taskCards;
      }
      return [];
    }
  },
  console
};
sandbox.window.STEEL_RAG_FRETBOARD = {
  mountPedalSteelFretboard: (container, options) => {
    lastMount = { container, options };
    container.innerHTML = options.positions.map((row) => `<g class="pedal-steel-fretboard__highlight" data-highlight-id="${row.id}"></g>`).join("");
  }
};
sandbox.window.window = sandbox.window;
sandbox.window.document = sandbox.document;
sandbox.window.console = sandbox.console;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("ui/e9-music-rules.js", "utf8"), sandbox);
vm.runInContext(fs.readFileSync("ui/e9-fretboard-explorer-data.js", "utf8"), sandbox);
vm.runInContext(fs.readFileSync("ui/e9-fretboard-explorer-config.js", "utf8"), sandbox);
vm.runInContext(fs.readFileSync("ui/e9-fretboard-explorer.js", "utf8"), sandbox);

const topFilterValues = () => elements["explorer-top-interval-filter"]
  .querySelectorAll("[data-top-interval-filter]")
  .map((button) => button.getAttribute("data-top-interval-filter"));

assert.match(elements["explorer-key"].innerHTML, /value="G" selected/);
for (const key of ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]) {
  assert.match(elements["explorer-key"].innerHTML, new RegExp(`value="${key}"`));
}
for (const key of ["C#", "D#", "F#", "G#", "A#"]) {
  assert.doesNotMatch(elements["explorer-key"].innerHTML, new RegExp(`value="${key}"`));
}
assert.match(elements["explorer-key"].innerHTML, /C# \(or D♭\)/);
assert.match(elements["explorer-key"].innerHTML, /A# \(or B♭\)/);
assert.match(elements["explorer-copedent"].innerHTML, /Emmons E9/);
assert.match(elements["explorer-copedent"].innerHTML, /Day E9/);
assert.doesNotMatch(elements["explorer-copedent"].innerHTML, /Custom E9 \(with LKV\)/);
assert.doesNotMatch(elements["explorer-copedent"].innerHTML, /My Copedent/);
assert.equal(elements["explorer-copedent"].value, "emmons-e9-basic");
assert.match(elements["explorer-string-group"].innerHTML, /All core grips/);
assert.match(elements["explorer-string-group"].innerHTML, /Core grips/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /5-6-7/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /6-7-10/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /5-7-8/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, />3-5</);
assert.equal(elements["explorer-string-group"].value, "4-5-6");
assert.equal(lastMount.options.positions.length > 0, true);
assert.equal(lastMount.options.positions.every((row) => row.grip === "4-5-6"), true);
assert.equal(elements["explorer-explore-mode"].value, "single");
assert.equal(elements["explorer-string-group-control"].hidden, false);
assert.equal(elements["explorer-path-family-control"].hidden, true);
assert.equal(elements["explorer-harmony-control"].hidden, false);
assert.equal(elements["explorer-harmony-control"].getAttribute("aria-hidden"), "false");
assert.equal(elements["explorer-harmony"].disabled, false);
assert.equal(elements["explorer-grip-vocabulary-control"].hidden, false);
assert.equal(elements["explorer-grip-vocabulary"].disabled, false);
assert.equal(taskCard("explore-grip").getAttribute("aria-pressed"), "true");
assert.equal(taskCard("find-chord").getAttribute("aria-pressed"), "false");
taskCard("find-chord").onclick();
assert.equal(elements["explorer-explore-mode"].value, "chord");
assert.equal(elements["explorer-chord-finder"].hidden, false);
assert.equal(elements["explorer-string-group-control"].hidden, true);
assert.equal(taskCard("find-chord").getAttribute("aria-pressed"), "true");
assert.equal(taskCard("explore-grip").getAttribute("aria-pressed"), "false");
elements["explorer-chord-root"].value = "F";
elements["explorer-chord-root"].dispatchChange();
elements["explorer-chord-quality"].value = "major7";
elements["explorer-chord-quality"].dispatchChange();
taskCard("find-note").onclick();
assert.equal(elements["explorer-explore-mode"].value, "note");
assert.equal(elements["explorer-note-finder"].hidden, false);
assert.equal(taskCard("find-note").getAttribute("aria-pressed"), "true");
taskCard("walk-harmonized-scale").onclick();
assert.equal(elements["explorer-explore-mode"].value, "path");
assert.equal(elements["explorer-path-family"].value, "middle");
assert.equal(taskCard("walk-harmonized-scale").getAttribute("aria-pressed"), "true");
taskCard("study-movement-path").onclick();
assert.equal(elements["explorer-explore-mode"].value, "path");
assert.equal(elements["explorer-path-family"].value, "low");
assert.equal(taskCard("study-movement-path").getAttribute("aria-pressed"), "true");
taskCard("identify-voicing").onclick();
assert.equal(elements["explorer-explore-mode"].value, "voicing");
assert.equal(elements["explorer-voicing-identifier"].hidden, false);
assert.equal(taskCard("identify-voicing").getAttribute("aria-pressed"), "true");
taskCard("explore-grip").onclick();
assert.equal(elements["explorer-explore-mode"].value, "single");
assert.equal(elements["explorer-string-group-control"].hidden, false);
assert.equal(elements["explorer-harmony-control"].hidden, false);
assert.equal(taskCard("explore-grip").getAttribute("aria-pressed"), "true");
elements["explorer-grip-vocabulary"].value = "extended";
elements["explorer-grip-vocabulary"].dispatchChange();
assert.match(elements["explorer-string-group"].innerHTML, /All extended grips/);
assert.match(elements["explorer-string-group"].innerHTML, /Path grips/);
assert.match(elements["explorer-string-group"].innerHTML, /Extended grips/);
assert.match(elements["explorer-string-group"].innerHTML, /5-6-7/);
assert.match(elements["explorer-string-group"].innerHTML, /6-7-10/);
assert.match(elements["explorer-string-group"].innerHTML, /4-6-10/);
assert.match(elements["explorer-string-group"].innerHTML, /5-6-9/);
assert.match(elements["explorer-string-group"].innerHTML, /4-6-9/);
elements["explorer-grip-vocabulary"].value = "song_tab";
elements["explorer-grip-vocabulary"].dispatchChange();
assert.match(elements["explorer-string-group"].innerHTML, /All song\/tab vocabulary grips/);
assert.match(elements["explorer-string-group"].innerHTML, /Song\/tab vocabulary grips/);
assert.match(elements["explorer-string-group"].innerHTML, /3-5-8/);
assert.match(elements["explorer-string-group"].innerHTML, /3-5-9/);
elements["explorer-grip-vocabulary"].value = "e_lower_pockets";
elements["explorer-grip-vocabulary"].dispatchChange();
assert.match(elements["explorer-string-group"].innerHTML, /All E-lower pocket grips/);
assert.match(elements["explorer-string-group"].innerHTML, /E-lower pocket grips/);
assert.match(elements["explorer-string-group"].innerHTML, /5-7-8/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /4-6-10/);
elements["explorer-grip-vocabulary"].value = "two_string";
elements["explorer-grip-vocabulary"].dispatchChange();
assert.match(elements["explorer-string-group"].innerHTML, /All two-string grips/);
assert.match(elements["explorer-string-group"].innerHTML, /Two-string grips/);
assert.match(elements["explorer-string-group"].innerHTML, /3-6/);
assert.match(elements["explorer-string-group"].innerHTML, /5-8/);
assert.match(elements["explorer-string-group"].innerHTML, /6-10/);
elements["explorer-grip-vocabulary"].value = "core";
elements["explorer-grip-vocabulary"].dispatchChange();
assert.equal(lastMount.options.showHighlightLabels, true);
assert.equal(lastMount.options.hideFilterControls, true);
assert.equal(lastMount.options.hidePositionTools, true);
assert.equal(lastMount.options.hideLegend, true);
assert.equal(lastMount.options.emphasizeVisibleHighlights, true);
assert.equal(lastMount.options.highlightStyle, "prominent");
assert.equal(lastMount.options.showStringActionLabels, false);
assert.equal(elements["explorer-string-action-label-toggle"].getAttribute("aria-pressed"), "false");
elements["explorer-string-action-label-toggle"].onclick();
assert.equal(lastMount.options.showStringActionLabels, true);
assert.equal(lastMount.options.stringActionLabelMode, "all");
assert.equal(elements["explorer-string-action-label-toggle"].getAttribute("aria-pressed"), "true");
assert.equal(elements["explorer-string-action-label-toggle"].classList.contains("is-selected"), true);
elements["explorer-string-action-label-toggle"].onclick();
assert.equal(lastMount.options.showStringActionLabels, false);
assert.equal(elements["explorer-string-action-label-toggle"].getAttribute("aria-pressed"), "false");
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "emphasizeStringGroups"), false);
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "selectedStringGroups"), false);
assert.equal(lastMount.options.positions.length > 0, true);
assert.equal(lastMount.options.positions.some((row) => /^[A-G][b#]?$/.test(row.label)), true);
assert.equal(lastMount.options.positions.every((row) => !/^[A-G][b#]?, [A-G][b#]?$/.test(row.label)), true);
assert.equal(lastMount.options.positions.every((row) => !/^[A-G][b#]?\+$/.test(row.label)), true);
const markerBy = (fret, grip, label) => lastMount.options.positions.find((row) => Number(row.fret) === fret && row.grip === grip && row.label === label);
const g345Fret3Marker = (label) => markerBy(3, "3-4-5", label);
const g345Fret10Marker = (label) => markerBy(10, "3-4-5", label);
assert.equal(g345Fret3Marker("B").label, "B");
assert.equal(g345Fret3Marker("C").label, "C");
assert.equal(JSON.stringify(Array.from(g345Fret3Marker("B").labelValues)), JSON.stringify(["B"]));
assert.equal(JSON.stringify(Array.from(g345Fret3Marker("C").labelValues)), JSON.stringify(["C"]));
assert.equal(g345Fret3Marker("B").id, "marker:3:3-4-5:3-4-5:B");
assert.equal(g345Fret3Marker("C").id, "marker:3:3-4-5:3-4-5:C");
assert.equal(g345Fret10Marker("F#").label, "F#");
assert.equal(g345Fret10Marker("G").label, "G");
assert.equal(lastMount.options.positions.every((row) => row.label !== "3, 3m"), true);
assert.equal(lastMount.options.positions.every((row) => row.label !== "3m, 4"), true);
assert.equal(lastMount.options.positions.some((row) => row.grip === "5-7-8"), true);
assert.equal(elements["explorer-top-interval-filter"].hidden, false);
assert.match(elements["explorer-top-interval-filter"].textContent, /Find top note/);
assert.match(elements["explorer-top-interval-filter"].innerHTML, /data-top-interval-filter="G"/);
assert.equal(JSON.stringify(topFilterValues()), JSON.stringify(["all", "G", "A", "B", "C", "D", "E", "F#"]));
assert.equal(elements["explorer-fret-range-filter"].hidden, false);
assert.match(elements["explorer-fret-range-filter"].textContent, /Visible fret range/);
assert.match(elements["explorer-fret-range-filter"].textContent, /Core/);
assert.match(elements["explorer-fret-range-filter"].innerHTML, /data-fret-range-filter="high"/);
assert.equal(elements["explorer-result-count"].textContent, "");
assert.doesNotMatch(elements["explorer-result-count"].textContent, /validated rows/);
assert.equal(elements["explorer-copedent-chart"].hidden, false);
assert.match(elements["explorer-copedent-chart"].textContent, /Emmons E9/);
assert.match(elements["explorer-copedent-chart"].textContent, /app-default/);
assert.match(elements["explorer-copedent-chart"].textContent, /String\s+Open[\s\S]*A pedal\s+P1[\s\S]*B pedal\s+P2[\s\S]*C pedal\s+P3/);
assert.match(elements["explorer-copedent-chart"].textContent, /D lower half-stop\s+RKR/);
assert.match(elements["explorer-copedent-chart"].textContent, /RKL G raise\/lower\s+RKL/);
assert.match(elements["explorer-copedent-chart"].textContent, /B -&gt; C#/);
assert.match(elements["explorer-copedent-chart"].textContent, /raise \+2/);
assert.doesNotMatch(elements["explorer-copedent-chart"].textContent, /B-to-Bb vertical/);
assert.doesNotMatch(elements["explorer-copedent-chart"].textContent, /\[object Object\]/);
assert.equal(elements["explorer-control-impact-preview"].hidden, false);
assert.match(elements["explorer-control-impact-preview"].textContent, /Pedal and lever impact/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /Emmons E9/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /Showing Notes notation/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /Choose one or more controls to preview changes/);
assert.match(elements["explorer-control-impact-preview"].textContent, /Pedals/);
assert.match(elements["explorer-control-impact-preview"].textContent, /Levers/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /data-control-impact-tab="A"/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /data-control-impact-tab="A"[^>]*>A<\/button>/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /data-control-impact-tab="B"[^>]*>B<\/button>/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /data-control-impact-tab="C"[^>]*>C<\/button>/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /<legend>Pedals<\/legend>[\s\S]*data-control-impact-tab="A"[\s\S]*data-control-impact-tab="B"[\s\S]*data-control-impact-tab="C"/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /<legend>Levers<\/legend>[\s\S]*data-control-impact-tab="E-raise"[^>]*>F<\/button>[\s\S]*data-control-impact-tab="E-lower"[^>]*>E<\/button>[\s\S]*data-control-impact-tab="G-lower"[^>]*>G<\/button>[\s\S]*data-control-impact-tab="D-lower"[^>]*>D<\/button>/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /String 5/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /raises 2 semitones/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /B-to-Bb vertical/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /\[object Object\]/);
let impactButtons = elements["explorer-control-impact-preview"].querySelectorAll("[data-control-impact-tab]");
impactButtons.find((button) => button.getAttribute("data-control-impact-tab") === "A").onclick();
impactButtons = elements["explorer-control-impact-preview"].querySelectorAll("[data-control-impact-tab]");
impactButtons.find((button) => button.getAttribute("data-control-impact-tab") === "B").onclick();
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /Previewing A pedal \+ B pedal/);
assert.match(elements["explorer-control-impact-preview"].textContent, /String 5/);
assert.match(elements["explorer-control-impact-preview"].textContent, /String 6/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /aria-pressed="true"[^>]*data-control-impact-tab="A"/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /aria-pressed="true"[^>]*data-control-impact-tab="B"/);
elements["explorer-control-impact-preview"].querySelector("[data-control-impact-clear]").onclick();
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /String 5/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /all 3-string groups/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /visible positions/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Cards match the SVG markers below/);
assert.match(elements["explorer-active-results"].textContent, /Top note:/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Marker \d|Marker \+\d/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Fretboard \d|Fretboard \d\+/);
assert.match(elements["explorer-active-results"].innerHTML, /data-marker-id=/);
assert.match(elements["explorer-active-results"].innerHTML, /data-marker-tone=/);
assert.equal(elements["explorer-active-results"].querySelectorAll("[data-active-result-row]").length >= lastMount.options.positions.length, true);
assert.equal(elements["explorer-fretboard"].querySelectorAll(".pedal-steel-fretboard__highlight[data-highlight-id]").length, lastMount.options.positions.length);
assert.equal(elements["explorer-fretboard"].querySelectorAll(".pedal-steel-fretboard__highlight[data-highlight-id]").filter((marker) => marker.getAttribute("data-explorer-selected-marker") === "true").length, 1);
const activeResultButtons = elements["explorer-active-results"].querySelectorAll("[data-active-result-row]");
activeResultButtons[1].onmouseenter();
assert.equal(elements["explorer-fretboard"].querySelectorAll(".pedal-steel-fretboard__highlight.is-explorer-hover-marker").length, 1);
assert.match(elements["explorer-tooltip"].textContent, /Fret/);
activeResultButtons[1].onmouseleave();
assert.equal(elements["explorer-fretboard"].querySelectorAll(".pedal-steel-fretboard__highlight.is-explorer-hover-marker").length, 0);
activeResultButtons[1].onclick();
assert.equal(elements["explorer-fretboard"].querySelectorAll(".pedal-steel-fretboard__highlight[data-highlight-id]").filter((marker) => marker.getAttribute("data-explorer-selected-marker") === "true").length, 1);
assert.match(elements["explorer-selected-detail"].textContent, /Notes/);
assert.match(elements["explorer-selected-detail"].textContent, /Chord intervals/);
assert.match(elements["explorer-selected-detail"].textContent, /Top-note focus/);
assert.match(elements["explorer-selected-detail"].textContent, /Top note/);
assert.match(elements["explorer-selected-detail"].textContent, /String actions/);
assert.match(elements["explorer-selected-detail"].textContent, /no change|B\+C|A\+B|E-raise/);
assert.match(elements["explorer-selected-detail"].textContent, /Why this position works/);
assert.match(elements["explorer-selected-detail"].textContent, /validated E9 pitch logic/);
assert.match(elements["explorer-selected-detail"].innerHTML, /explorer-teaching-note/);
assert.doesNotMatch(elements["explorer-fretboard"].textContent, /Why this position works/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /Pitch validated/);
assert.match(elements["explorer-active-results"].innerHTML, /Top note:/);
assert.match(elements["explorer-active-results"].innerHTML, /<strong>Top note: (G|B|D)/);
const intervalFilterButtons = elements["explorer-top-interval-filter"].querySelectorAll("[data-top-interval-filter]");
intervalFilterButtons.find((button) => button.getAttribute("data-top-interval-filter") === "G").onclick();
assert.match(elements["explorer-active-results"].textContent, /Top note: G/);
assert.equal(lastMount.options.positions.every((row) => row.label === "G"), true);
elements["explorer-top-interval-filter"].querySelectorAll("[data-top-interval-filter]").find((button) => button.getAttribute("data-top-interval-filter") === "all").onclick();
const rangeButtons = elements["explorer-fret-range-filter"].querySelectorAll("[data-fret-range-filter]");
const coreCount = lastMount.options.positions.length;
rangeButtons.find((button) => button.getAttribute("data-fret-range-filter") === "high").onclick();
assert.match(elements["explorer-fret-range-filter"].textContent, /Frets 10-24/);
assert.equal(lastMount.options.positions.every((row) => Number(row.fret) >= 10 && Number(row.fret) <= 24), true);
assert.equal(lastMount.options.positions.length > 0, true);
rangeButtons.find((button) => button.getAttribute("data-fret-range-filter") === "all").onclick();
assert.equal(lastMount.options.positions.length >= coreCount, true);
intervalFilterButtons.find((button) => button.getAttribute("data-top-interval-filter") === "G").onclick();
const gTop345Frets = lastMount.options.positions
  .filter((row) => row.grip === "3-4-5" && row.label === "G" && JSON.stringify(row.pedals) === JSON.stringify(["B", "C"]))
  .map((row) => Number(row.fret))
  .sort((a, b) => a - b);
assert.equal(JSON.stringify(gTop345Frets), JSON.stringify([10, 22]));

const explorerApi = sandbox.window.STEEL_RAG_E9_EXPLORER;
const fMaj7Target = explorerApi.parseChordFinderQuery("Fmaj7");
assert.equal(fMaj7Target.ok, true);
assert.equal(fMaj7Target.label, "Fmaj7");
assert.equal(fMaj7Target.quality.id, "major7");
assert.equal(JSON.stringify(fMaj7Target.toneLabels.map((tone) => tone.note)), JSON.stringify(["F", "A", "C", "E"]));
const fMajor7Target = explorerApi.parseChordFinderQuery("F major 7");
assert.equal(fMajor7Target.label, "Fmaj7");
const fDelta7Target = explorerApi.parseChordFinderQuery("FΔ7");
assert.equal(fDelta7Target.label, "Fmaj7");
const cMin9Target = explorerApi.parseChordFinderQuery("Cmin9");
assert.equal(cMin9Target.ok, true);
assert.equal(cMin9Target.label, "Cm9");
assert.equal(cMin9Target.quality.id, "minor9");
const cM9Target = explorerApi.parseChordFinderQuery("Cm9");
assert.equal(cM9Target.label, "Cm9");
const v7Target = explorerApi.parseChordFinderQuery("V7 in G");
assert.equal(v7Target.label, "D7");
assert.equal(v7Target.quality.id, "dominant7");
assert.match(v7Target.message, /resolves to D7/);
const iMaj7Target = explorerApi.parseChordFinderQuery("Imaj7 in F");
assert.equal(iMaj7Target.label, "Fmaj7");
assert.equal(iMaj7Target.quality.id, "major7");

elements["explorer-explore-mode"].value = "chord";
elements["explorer-explore-mode"].dispatchChange();
assert.equal(elements["explorer-chord-finder"].hidden, false);
assert.equal(elements["explorer-string-group-control"].hidden, true);
assert.equal(elements["explorer-harmony-control"].hidden, true);
assert.equal(elements["explorer-grip-vocabulary-control"].hidden, false);
assert.match(elements["explorer-chord-finder"].textContent, /Chord \/ Voicing Finder/);
assert.match(elements["explorer-chord-finder"].textContent, /Target: Fmaj7/);
assert.match(elements["explorer-chord-finder"].textContent, /Root/);
assert.match(elements["explorer-chord-finder"].textContent, /Quality/);
assert.doesNotMatch(elements["explorer-chord-finder"].textContent, /Target chord or function/);
assert.doesNotMatch(elements["explorer-chord-finder"].textContent, /Fmaj7, Cmin9, V7 in G/);
assert.doesNotMatch(elements["explorer-chord-finder"].textContent, /I could not read|Enter a chord|Try a chord symbol/);
assert.match(elements["explorer-active-results"].textContent, /Fmaj7/);
assert.match(elements["explorer-active-results"].textContent, /Cards and SVG markers use the same colors/);
assert.match(elements["explorer-active-results"].textContent, /Present/);
assert.match(elements["explorer-active-results"].textContent, /Omitted/);
assert.match(elements["explorer-selected-detail"].textContent, /Present chord tones/);
assert.match(elements["explorer-selected-detail"].textContent, /Omitted tones/);
assert.match(elements["explorer-selected-detail"].textContent, /Confidence/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /omitted 0/);
assert.equal(lastMount.options.positions.length > 1, true);
assert.equal(lastMount.options.showHighlightLabels, false);
assert.equal(elements["explorer-active-results"].querySelectorAll("[data-chord-finder-result]").length > 0, true);
assert.equal(elements["explorer-active-results"].querySelectorAll("[data-chord-map-filter-control]").length > 1, true);
assert.equal(lastMount.options.positions.every((row) => row.id.startsWith("marker:")), true);
const fMaj7MarkerCount = lastMount.options.positions.length;
elements["explorer-active-results"].querySelectorAll("[data-chord-map-filter-control]")
  .find((button) => button.getAttribute("data-chord-map-filter-control") === "low").onclick();
assert.equal(lastMount.options.positions.length > 0, true);
assert.equal(lastMount.options.positions.length < fMaj7MarkerCount, true);
assert.equal(lastMount.options.positions.every((row) => Number(row.fret) <= 4), true);
elements["explorer-active-results"].querySelectorAll("[data-chord-map-filter-control]")
  .find((button) => button.getAttribute("data-chord-map-filter-control") === "all").onclick();
assert.equal(lastMount.options.positions.length, fMaj7MarkerCount);
elements["explorer-chord-root"].value = "C";
elements["explorer-chord-root"].dispatchChange();
elements["explorer-chord-quality"].value = "minor9";
elements["explorer-chord-quality"].dispatchChange();
assert.match(elements["explorer-chord-finder"].textContent, /Target: Cm9/);
assert.doesNotMatch(elements["explorer-chord-finder"].textContent, /\[object Object\]/);
elements["explorer-chord-root"].value = "D";
elements["explorer-chord-root"].dispatchChange();
elements["explorer-chord-quality"].value = "major";
elements["explorer-chord-quality"].dispatchChange();
elements["explorer-grip-vocabulary"].value = "core";
elements["explorer-grip-vocabulary"].dispatchChange();
assert.match(elements["explorer-chord-finder"].textContent, /Target: D/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /5-7-8/);
assert.equal(lastMount.options.positions.some((row) => row.grip === "5-7-8" && Number(row.fret) === 3), false);
assert.match(elements["explorer-chord-finder"].textContent, /choose E-lower pockets or All legitimate/);
elements["explorer-grip-vocabulary"].value = "all";
elements["explorer-grip-vocabulary"].dispatchChange();
elements["explorer-chord-control-scope"].value = "all";
elements["explorer-chord-control-scope"].dispatchChange();
assert.match(elements["explorer-chord-finder"].textContent, /Target: D/);
assert.match(elements["explorer-active-results"].textContent, /E-lower pocket/);
assert.match(elements["explorer-active-results"].textContent, /An E-lower pocket grip/);
assert.equal(elements["explorer-row-list"].querySelectorAll("[data-chord-finder-result]").length, 0);
assert.equal(elements["explorer-row-list"].textContent.trim(), "");
const dMajorELowerPocket = lastMount.options.positions.find((row) => row.grip === "5-7-8" && Number(row.fret) === 3);
assert.ok(dMajorELowerPocket);
assert.equal(JSON.stringify(dMajorELowerPocket.strings), JSON.stringify([5, 7, 8]));
assert.equal(JSON.stringify(dMajorELowerPocket.notes), JSON.stringify(["D", "A", "F#"]));
assert.equal(JSON.stringify(dMajorELowerPocket.string_action_labels), JSON.stringify({ 5: "5", 7: "7", 8: "8E" }));
assert.match(elements["explorer-active-results"].textContent, /Presentroot \(D\), 3rd \(F#\), 5th \(A\)/);
assert.match(elements["explorer-active-results"].textContent, /Omittednone/);
elements["explorer-chord-control-scope"].value = "open";
elements["explorer-chord-control-scope"].dispatchChange();
assert.equal(lastMount.options.positions.some((row) => row.grip === "5-7-8" && Number(row.fret) === 3), false);
assert.match(elements["explorer-chord-finder"].textContent, /requires the E-lower lever/);
elements["explorer-chord-control-scope"].value = "all";
elements["explorer-chord-control-scope"].dispatchChange();
elements["explorer-chord-quality"].value = "dominant7";
elements["explorer-chord-quality"].dispatchChange();
elements["explorer-grip-vocabulary"].value = "extended";
elements["explorer-grip-vocabulary"].dispatchChange();
assert.match(elements["explorer-chord-finder"].textContent, /Target: D7/);
assert.match(elements["explorer-chord-finder"].textContent, /Where the ♭7 is/);
assert.match(elements["explorer-chord-finder"].textContent, /Dominant 7 uses the formula 1–3–5–♭7/);
assert.match(elements["explorer-chord-finder"].textContent, /C is the ♭7 \(also written b7\) above D/);
assert.match(elements["explorer-chord-finder"].textContent, /one semitone below the major 7 \(C#\)/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Fmaj7/);
assert.equal(lastMount.options.positions.length > 0, true);
assert.match(elements["explorer-active-results"].textContent, /D7/);
elements["explorer-explore-mode"].value = "voicing";
elements["explorer-explore-mode"].dispatchChange();
assert.equal(elements["explorer-voicing-identifier"].hidden, false);
assert.equal(elements["explorer-chord-finder"].hidden, true);
elements["explorer-explore-mode"].value = "single";
elements["explorer-explore-mode"].dispatchChange();

notationModeButtons[1].onclick();
assert.match(elements["explorer-scale-notes"].textContent, /1 - 2- - 3- - 4 - 5 - 6- - 7°/);
assert.equal(JSON.stringify(topFilterValues()), JSON.stringify(["all", "1", "2-", "3-", "4", "5", "6-", "7°"]));
assert.match(elements["explorer-active-results"].innerHTML, /Top note interval:/);
assert.match(elements["explorer-active-results"].textContent, /Top note interval: (1|3-|5)/);
assert.match(elements["explorer-active-results"].textContent, /Harmony/);
assert.equal(g345Fret3Marker("3-").label, "3-");
assert.equal(g345Fret3Marker("4").label, "4");
assert.equal(g345Fret10Marker("7°").label, "7°");
assert.equal(g345Fret10Marker("1").label, "1");
assert.equal(lastMount.options.positions.some((row) => /^(1|2-|3-|4|5|6-|7°)(, (1|2-|3-|4|5|6-|7°))*$/.test(row.label)), true);
assert.equal(lastMount.options.positions.every((row) => row.label !== "3+"), true);
assert.equal(lastMount.options.positions.every((row) => row.label !== "3, 3-"), true);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /Showing NNS notation/);
notationModeButtons[2].onclick();
assert.match(elements["explorer-scale-notes"].textContent, /I - ii - iii - IV - V - vi - vii°/);
assert.equal(JSON.stringify(topFilterValues()), JSON.stringify(["all", "I", "ii", "iii", "IV", "V", "vi", "vii°"]));
assert.match(elements["explorer-active-results"].textContent, /Top note interval: (I|iii|V)/);
assert.equal(g345Fret3Marker("iii").label, "iii");
assert.equal(g345Fret3Marker("IV").label, "IV");
assert.equal(g345Fret10Marker("vii°").label, "vii°");
assert.equal(g345Fret10Marker("I").label, "I");
assert.equal(lastMount.options.positions.some((row) => /^(I|ii|iii|IV|V|vi|vii°)(, (I|ii|iii|IV|V|vi|vii°))*$/.test(row.label)), true);
notationModeButtons[3].onclick();
assert.match(elements["explorer-scale-notes"].textContent, /1 - 2m - 3m - 4 - 5 - 6m - 7dim/);
assert.equal(JSON.stringify(topFilterValues()), JSON.stringify(["all", "1", "2m", "3m", "4", "5", "6m", "7dim"]));
assert.match(elements["explorer-active-results"].textContent, /Top note interval: (1|3m|5)/);
assert.equal(g345Fret3Marker("3m").label, "3m");
assert.equal(g345Fret3Marker("4").label, "4");
assert.equal(g345Fret10Marker("7dim").label, "7dim");
assert.equal(g345Fret10Marker("1").label, "1");
assert.equal(lastMount.options.positions.some((row) => /^(1|2m|3m|4|5|6m|7dim)(, (1|2m|3m|4|5|6m|7dim))*$/.test(row.label)), true);
notationModeButtons[0].onclick();
assert.equal(lastMount.options.positions.some((row) => /^[A-G][b#]?$/.test(row.label) || /^[A-G][b#]?, [A-G][b#]?$/.test(row.label)), true);
assert.equal(g345Fret3Marker("B").label, "B");
assert.equal(g345Fret3Marker("C").label, "C");
assert.match(elements["explorer-active-results"].innerHTML, /Top note:/);
assert.match(elements["explorer-active-results"].innerHTML, /<strong>Top note: (G|B|D)/);
notationModeButtons[1].onclick();
assert.equal(g345Fret3Marker("3-").label, "3-");
assert.equal(g345Fret3Marker("4").label, "4");
assert.equal(lastMount.options.positions.some((row) => /^(1|2-|3-|4|5|6-|7°)(, (1|2-|3-|4|5|6-|7°))*$/.test(row.label)), true);
assert.match(elements["explorer-active-results"].innerHTML, /Top note interval:/);
notationModeButtons[0].onclick();

elements["explorer-explore-mode"].value = "note";
elements["explorer-explore-mode"].dispatchChange();
assert.equal(elements["explorer-note-finder"].hidden, false);
assert.equal(elements["explorer-string-group-control"].hidden, true);
assert.equal(elements["explorer-string-group"].disabled, true);
assert.equal(elements["explorer-path-family-control"].hidden, true);
assert.equal(elements["explorer-harmony-control"].hidden, true);
assert.equal(elements["explorer-harmony"].disabled, true);
assert.equal(elements["explorer-control-impact-preview"].hidden, true);
assert.equal(elements["explorer-fret-range-filter"].hidden, false);
assert.match(elements["explorer-note-finder"].textContent, /Pedals and levers change the note on affected strings/);
assert.match(elements["explorer-active-results"].textContent, /Find all:/);
assert.match(elements["explorer-selected-detail"].textContent, /String 3, fret 3: B/);
assert.match(elements["explorer-selected-detail"].textContent, /Active controlsOpen/);
assert.match(elements["explorer-selected-detail"].textContent, /Open note at fretB/);
assert.match(elements["explorer-selected-detail"].textContent, /Final noteB/);
assert.match(elements["explorer-selected-detail"].textContent, /Open position: no pedals or levers are active/);
const noteWorkflowButtons = () => elements["explorer-note-finder"].querySelectorAll("[data-note-workflow]");
const noteTargetModeButtons = () => elements["explorer-note-finder"].querySelectorAll("[data-note-target-mode]");
const noteTargetButtons = () => elements["explorer-note-finder"].querySelectorAll("[data-note-target]");
const noteControlButtons = () => elements["explorer-note-finder"].querySelectorAll("[data-note-control-state]");
const noteStringFilterButtons = () => elements["explorer-note-finder"].querySelectorAll("[data-note-string-filter]");
const noteReverseButtons = () => elements["explorer-note-finder"].querySelectorAll("[data-note-reverse-result]");
const noteGripVocabularyButtons = () => elements["explorer-note-finder"].querySelectorAll("[data-note-grip-vocabulary]");
const noteGripRoleButtons = () => elements["explorer-note-finder"].querySelectorAll("[data-note-grip-role]");
const noteGripButtons = () => elements["explorer-note-finder"].querySelectorAll("[data-note-grip-card]");
const noteSyncButtons = () => elements["explorer-note-finder"].querySelectorAll("[data-note-sync-event]");
const noteCell = (stringNumber, fret) => elements["explorer-fretboard"]
  .querySelectorAll("[data-note-cell]")
  .find((button) => button.getAttribute("data-note-string") === String(stringNumber) && button.getAttribute("data-note-fret") === String(fret));
assert.deepEqual(noteWorkflowButtons().map((button) => button.getAttribute("data-note-workflow")), ["find", "reverse", "changes", "grip", "drill", "sync"]);
assert.deepEqual(noteTargetModeButtons().map((button) => button.getAttribute("data-note-target-mode")), ["scale", "intervals"]);
assert.match(elements["explorer-note-finder"].textContent, /Find all/);
assert.match(elements["explorer-note-finder"].textContent, /All strings/);
noteTargetModeButtons().find((button) => button.getAttribute("data-note-target-mode") === "intervals").onclick();
assert.match(elements["explorer-note-finder"].textContent, /Interval from G/);
assert.equal(noteTargetButtons().length, 12);
noteTargetButtons().find((button) => button.getAttribute("data-note-target") === "10").onclick();
assert.match(elements["explorer-note-finder"].textContent, /♭7 \(b7\)/);
assert.match(elements["explorer-note-finder"].textContent, /In G, the ♭7 .* is F/);
assert.match(elements["explorer-note-finder"].textContent, /10 semitones above the root/);
assert.ok(elements["explorer-fretboard"].querySelectorAll("[data-note-result]").length > 0);
assert.match(elements["explorer-selected-detail"].textContent, /Interval from G root/);
noteTargetModeButtons().find((button) => button.getAttribute("data-note-target-mode") === "scale").onclick();
noteTargetButtons().find((button) => button.getAttribute("data-note-target") === "2").onclick();
assert.equal(noteCell(3, 3).getAttribute("data-note-result"), "3:3");
noteControlButtons().find((button) => button.getAttribute("data-note-control-state") === "B").onclick();
assert.equal(noteCell(3, 3).getAttribute("data-note-result"), null);
assert.match(elements["explorer-selected-detail"].textContent, /String 3, fret 3: C/);
assert.match(elements["explorer-selected-detail"].textContent, /Open note at fretB/);
assert.match(elements["explorer-selected-detail"].textContent, /Final noteC/);
assert.match(elements["explorer-selected-detail"].textContent, /B pedal raises this string from B to C/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /C5/);
pitchRegisterButtons.find((button) => button.getAttribute("data-explorer-pitch-register") === "scientific").onclick();
assert.match(elements["explorer-selected-detail"].textContent, /String 3, fret 3: C5/);
assert.match(elements["explorer-selected-detail"].textContent, /Open note with registerB4/);
assert.match(elements["explorer-selected-detail"].textContent, /Final note with registerC5/);
pitchRegisterButtons.find((button) => button.getAttribute("data-explorer-pitch-register") === "band").onclick();
assert.match(elements["explorer-selected-detail"].textContent, /String 3, fret 3: C · upper/);
assert.match(elements["explorer-selected-detail"].textContent, /Final note with registerC · upper/);
pitchRegisterButtons.find((button) => button.getAttribute("data-explorer-pitch-register") === "off").onclick();
assert.match(elements["explorer-selected-detail"].textContent, /String 3, fret 3: C/);
noteControlButtons().find((button) => button.getAttribute("data-note-control-state") === "A").onclick();
noteCell(3, 3).onclick();
assert.match(elements["explorer-selected-detail"].textContent, /String 3, fret 3: B/);
assert.match(elements["explorer-selected-detail"].textContent, /Selected controls do not change this string; final note remains B/);
noteCell(5, 3).onclick();
assert.match(elements["explorer-selected-detail"].textContent, /String 5, fret 3: E/);
assert.match(elements["explorer-selected-detail"].textContent, /Open note at fretD/);
assert.match(elements["explorer-selected-detail"].textContent, /Final noteE/);
assert.match(elements["explorer-selected-detail"].textContent, /A pedal raises this string from D to E/);
noteControlButtons().find((button) => button.getAttribute("data-note-control-state") === "B").onclick();
noteWorkflowButtons().find((button) => button.getAttribute("data-note-workflow") === "changes").onclick();
assert.match(elements["explorer-note-finder"].textContent, /B pedal affected strings/);
assert.match(elements["explorer-note-finder"].textContent, /Affected strings: 3, 6/);
assert.match(elements["explorer-note-finder"].textContent, /G# -&gt; A/);
noteWorkflowButtons().find((button) => button.getAttribute("data-note-workflow") === "reverse").onclick();
noteStringFilterButtons().find((button) => button.getAttribute("data-note-string-filter") === "3").onclick();
assert.match(elements["explorer-note-finder"].textContent, /Reverse lookup/);
assert.match(elements["explorer-note-finder"].textContent, /How to get B/);
assert.ok(noteReverseButtons().length > 0);
assert.equal(elements["explorer-row-list"].textContent.includes("String 5,"), false);
noteWorkflowButtons().find((button) => button.getAttribute("data-note-workflow") === "grip").onclick();
noteStringFilterButtons().find((button) => button.getAttribute("data-note-string-filter") === "all").onclick();
assert.match(elements["explorer-note-finder"].textContent, /Build a grip/);
assert.match(elements["explorer-note-finder"].textContent, /The 1-3-5 chord tones/);
assert.deepEqual(noteGripVocabularyButtons().map((button) => button.getAttribute("data-note-grip-vocabulary")), ["core", "extended", "song_tab", "e_lower_pockets", "two_string", "all"]);
assert.ok(noteGripButtons().length > 0);
noteGripButtons()[0].onclick();
assert.match(elements["explorer-selected-detail"].textContent, /Single-note finder/);
noteGripVocabularyButtons().find((button) => button.getAttribute("data-note-grip-vocabulary") === "extended").onclick();
assert.match(elements["explorer-note-finder"].textContent, /Dominant 7 \/ V7/);
assert.match(elements["explorer-note-finder"].textContent, /D7|V7|5\^7|Dominant 7/);
assert.deepEqual(noteGripRoleButtons().map((button) => button.getAttribute("data-note-grip-role")), ["all", "harmonized_scale_path", "melody_harmony", "wide_voicing", "spread_voicing", "chord_shell", "pad_sustain", "chord_voicing", "dominant_color", "major_7_color", "minor_color", "bass_root_support", "passing_color", "lever_pocket", "alternate_position", "e_lower_pocket"]);
noteGripRoleButtons().find((button) => button.getAttribute("data-note-grip-role") === "dominant_color").onclick();
assert.match(elements["explorer-note-finder"].textContent, /5-6-9|4-6-9|6-9|5-9|Dominant color/);
assert.ok(noteGripButtons().length > 0);
noteGripVocabularyButtons().find((button) => button.getAttribute("data-note-grip-vocabulary") === "song_tab").onclick();
assert.match(elements["explorer-note-finder"].textContent, /3-5-8|3-5-9|Song\/tab vocabulary/);
noteGripVocabularyButtons().find((button) => button.getAttribute("data-note-grip-vocabulary") === "e_lower_pockets").onclick();
assert.match(elements["explorer-note-finder"].textContent, /5-7-8|E-lower pocket/);
noteGripVocabularyButtons().find((button) => button.getAttribute("data-note-grip-vocabulary") === "two_string").onclick();
noteGripRoleButtons().find((button) => button.getAttribute("data-note-grip-role") === "pad_sustain").onclick();
assert.match(elements["explorer-note-finder"].textContent, /Pad use|possible pad \/ sustain|Pads/);
noteGripButtons()[0].onclick();
assert.match(elements["explorer-note-finder"].textContent, /Pad use|possible pad \/ sustain|Two-string/);
assert.match(elements["explorer-note-finder"].textContent, /5-8|6-10|5-9|6-9|8-10/);
noteWorkflowButtons().find((button) => button.getAttribute("data-note-workflow") === "drill").onclick();
noteControlButtons().find((button) => button.getAttribute("data-note-control-state") === "open").onclick();
noteTargetButtons().find((button) => button.getAttribute("data-note-target") === "2").onclick();
noteCell(4, 3).onclick();
assert.match(elements["explorer-note-finder"].textContent, /Try again/);
noteCell(3, 3).onclick();
assert.match(elements["explorer-note-finder"].textContent, /Correct/);
noteWorkflowButtons().find((button) => button.getAttribute("data-note-workflow") === "sync").onclick();
assert.match(elements["explorer-note-finder"].textContent, /Deterministic event sync demo/);
noteSyncButtons().find((button) => button.getAttribute("data-note-sync-event") === "s3-f3-b").onclick();
assert.match(elements["explorer-selected-detail"].textContent, /String 3, fret 3: C/);
assert.match(elements["explorer-selected-detail"].textContent, /B pedal raises this string from B to C/);
noteCell(3, 3).onmouseenter();
assert.match(elements["explorer-selected-detail"].textContent, /String 3, fret 3: C/);
noteCell(3, 3).onmouseleave();
assert.match(elements["explorer-selected-detail"].textContent, /String 3, fret 3: C/);
notationModeButtons[1].onclick();
assert.match(elements["explorer-selected-detail"].textContent, /NNS in G major4/);
assert.doesNotMatch(elements["explorer-note-finder"].textContent, /\[object Object\]/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /\[object Object\]/);
elements["explorer-explore-mode"].value = "single";
elements["explorer-explore-mode"].dispatchChange();
notationModeButtons[0].onclick();
assert.equal(elements["explorer-note-finder"].hidden, true);
assert.equal(elements["explorer-voicing-identifier"].hidden, true);
assert.equal(elements["explorer-grip-vocabulary-control"].hidden, false);
assert.equal(elements["explorer-string-group-control"].hidden, false);
assert.equal(elements["explorer-harmony-control"].hidden, false);

elements["explorer-explore-mode"].value = "voicing";
elements["explorer-explore-mode"].dispatchChange();
assert.equal(elements["explorer-voicing-identifier"].hidden, false);
assert.equal(elements["explorer-note-finder"].hidden, true);
assert.equal(elements["explorer-string-group-control"].hidden, true);
assert.equal(elements["explorer-string-group"].disabled, true);
assert.equal(elements["explorer-path-family-control"].hidden, true);
assert.equal(elements["explorer-harmony-control"].hidden, true);
assert.equal(elements["explorer-harmony"].disabled, true);
assert.equal(elements["explorer-control-impact-preview"].hidden, true);
assert.equal(elements["explorer-top-interval-filter"].hidden, true);
assert.equal(elements["explorer-fret-range-filter"].hidden, true);
assert.match(elements["explorer-voicing-identifier"].textContent, /Choose a fret, up to four strings/);
assert.match(elements["explorer-voicing-identifier"].textContent, /G chord/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Technical name: G/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Full chord/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 3\s*B\s*=\s*3rd/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 4\s*G\s*=\s*root/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 5\s*D\s*=\s*5th/);
assert.doesNotMatch(elements["explorer-voicing-identifier"].textContent, /G chord: B, G, D/);
assert.match(elements["explorer-active-results"].textContent, /Identified G/);
assert.match(elements["explorer-selected-detail"].textContent, /Voicing identifier/);
assert.match(elements["explorer-selected-detail"].textContent, /NotesB, G, D/);
assert.match(elements["explorer-selected-detail"].textContent, /Likely functionI function in G/);
assert.match(elements["explorer-selected-detail"].textContent, /Per-string details/);
assert.match(elements["explorer-selected-detail"].textContent, /Grip typeCore grip/);
assert.equal(lastMount.options.positions.length, 1);
assert.equal(lastMount.options.positions[0].fret, 3);
assert.equal(lastMount.options.positions[0].grip, "3-4-5");
assert.equal(lastMount.options.positions[0].notes.join(","), "B,G,D");
const voicingControlButtons = () => elements["explorer-voicing-identifier"].querySelectorAll("[data-voicing-control]");
const voicingClearButtons = () => elements["explorer-voicing-identifier"].querySelectorAll("[data-voicing-control-clear]");
const voicingStringButtons = () => elements["explorer-voicing-identifier"].querySelectorAll("[data-voicing-string]");
const currentVoicingRow = () => lastMount.options.positions[0] || { strings: [], pedals: [], levers: [] };
const activeVoicingStringSet = () => new Set((currentVoicingRow().strings || []).map(Number));
const activeVoicingControlSet = () => new Set([...(currentVoicingRow().pedals || []), ...(currentVoicingRow().levers || [])]);
const setVoicingStrings = (strings) => {
  const desired = new Set(strings.map(Number));
  for (const stringNumber of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) {
    const current = activeVoicingStringSet();
    if (current.has(stringNumber) && !desired.has(stringNumber)) {
      const button = voicingStringButtons().find((item) => item.getAttribute("data-voicing-string") === String(stringNumber));
      assert.ok(button, `Missing string ${stringNumber} button`);
      button.onclick();
    }
  }
  for (const stringNumber of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) {
    const current = activeVoicingStringSet();
    if (!current.has(stringNumber) && desired.has(stringNumber)) {
      const button = voicingStringButtons().find((item) => item.getAttribute("data-voicing-string") === String(stringNumber));
      assert.ok(button, `Missing string ${stringNumber} button`);
      button.onclick();
    }
  }
  assert.deepEqual(Array.from(activeVoicingStringSet()).sort((a, b) => a - b), Array.from(desired).sort((a, b) => a - b));
};
const setVoicingControls = (controls) => {
  const desired = new Set(controls);
  for (const controlId of ["A", "B", "C", "E-raise", "E-lower", "D-lower", "G-lower"]) {
    const current = activeVoicingControlSet();
    if (current.has(controlId) !== desired.has(controlId)) {
      const button = voicingControlButtons().find((item) => item.getAttribute("data-voicing-control") === controlId);
      assert.ok(button, `Missing control ${controlId} button`);
      button.onclick();
    }
  }
  assert.deepEqual(Array.from(activeVoicingControlSet()).sort(), Array.from(desired).sort());
};
assert.deepEqual(voicingControlButtons().map((button) => button.getAttribute("data-voicing-control")), ["A", "B", "C", "E-raise", "E-lower", "D-lower", "G-lower"]);
assert.equal(voicingControlButtons().some((button) => button.getAttribute("data-voicing-control") === "AB"), false);
assert.equal(voicingControlButtons().some((button) => button.getAttribute("data-voicing-control") === "BC"), false);
setVoicingControls(["B", "C"]);
assert.match(elements["explorer-voicing-identifier"].textContent, /Am chord/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Technical name: Am/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 3\s*C\s*=\s*minor 3rd/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 4\s*A\s*=\s*root/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 5\s*E\s*=\s*5th/);
assert.match(elements["explorer-selected-detail"].textContent, /Am/);
assert.match(elements["explorer-selected-detail"].textContent, /Likely functionii function in G/);
assert.match(elements["explorer-selected-detail"].textContent, /selecting B pedal and C pedal individually/);
assert.equal(lastMount.options.positions[0].notes.join(","), "C,A,E");
setVoicingControls([]);
elements["explorer-key"].value = "F";
elements["explorer-key"].dispatchChange();
setVoicingStrings([4, 6, 10]);
setVoicingControls(["A", "B"]);
assert.match(elements["explorer-voicing-identifier"].textContent, /C chord/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Technical name: C/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 4\s*G\s*=\s*5th/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 6\s*C\s*=\s*root/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 10\s*E\s*=\s*3rd/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Card and SVG marker show the same fret\/string group/);
assert.match(elements["explorer-active-results"].textContent, /Identified C chord/);
assert.match(elements["explorer-selected-detail"].textContent, /C/);
assert.match(elements["explorer-selected-detail"].textContent, /Likely functionV function in F/);
assert.match(elements["explorer-selected-detail"].textContent, /uses string 4 instead of string 8/);
assert.equal(lastMount.options.positions[0].grip, "4-6-10");
assert.equal(lastMount.options.positions[0].notes.join(","), "G,C,E");
setVoicingControls([]);

elements["explorer-key"].value = "F";
elements["explorer-key"].dispatchChange();
elements["explorer-voicing-fret"].value = "3";
elements["explorer-voicing-fret"].dispatchChange();
setVoicingStrings([3, 5, 8]);
setVoicingControls(["B", "C"]);
assert.match(elements["explorer-voicing-identifier"].textContent, /C chord/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Technical name: C/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 3\s*C\s*=\s*root/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 5\s*E\s*=\s*3rd/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 8\s*G\s*=\s*5th/);
assert.match(elements["explorer-selected-detail"].textContent, /Grip typeSong\/tab vocabulary grip/);
assert.match(elements["explorer-selected-detail"].textContent, /Why use this gripA spread grip/);
assert.equal(lastMount.options.positions[0].grip, "3-5-8");
assert.equal(lastMount.options.positions[0].notes.join(","), "C,E,G");
setVoicingControls([]);

elements["explorer-key"].value = "G";
elements["explorer-key"].dispatchChange();
elements["explorer-voicing-fret"].value = "8";
elements["explorer-voicing-fret"].dispatchChange();
setVoicingStrings([5, 7, 8]);
setVoicingControls(["E-lower"]);
assert.match(elements["explorer-voicing-identifier"].textContent, /G chord/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Technical name: G/);
assert.match(elements["explorer-voicing-identifier"].textContent, /What notes are here/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 5\s*G\s*=\s*root/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 7\s*D\s*=\s*5th/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 8\s*B\s*=\s*3rd/);
assert.match(elements["explorer-selected-detail"].textContent, /Grip typeE-lower pocket/);
assert.match(elements["explorer-selected-detail"].textContent, /Why use this gripAn E-lower pocket grip/);
assert.equal(lastMount.options.positions[0].grip, "5-7-8");
assert.equal(lastMount.options.positions[0].notes.join(","), "G,D,B");
setVoicingControls([]);

elements["explorer-voicing-fret"].value = "3";
elements["explorer-voicing-fret"].dispatchChange();
setVoicingStrings([5, 7, 8]);
assert.match(elements["explorer-voicing-identifier"].textContent, /G color voicing — no 3rd/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Technical name: G5\/add9\(no3\)/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Confidence: Medium/);
assert.match(elements["explorer-voicing-identifier"].textContent, /What notes are here/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 5\s*D\s*=\s*5th/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 7\s*A\s*=\s*9th \/ 2nd/);
assert.match(elements["explorer-voicing-identifier"].textContent, /String 8\s*G\s*=\s*root/);
assert.match(elements["explorer-voicing-identifier"].textContent, /What is missing/);
assert.match(elements["explorer-voicing-identifier"].textContent, /3rd \(B\)/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Because there is no 3rd, this does not define major vs minor by itself/);
assert.match(elements["explorer-voicing-identifier"].textContent, /How to use it/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Use as a color\/partial voicing/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Alternate readings/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Warning \/ caution/);
assert.match(elements["explorer-voicing-identifier"].textContent, /No 3rd is present/);
assert.doesNotMatch(elements["explorer-voicing-identifier"].textContent, /G chord: D, A, G/);
assert.doesNotMatch(elements["explorer-voicing-identifier"].textContent, /G5\/add9\(no3\) voicing: D, A, G/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /G5\/add9\(no3\) chord/);
assert.match(elements["explorer-selected-detail"].textContent, /Voicing statusColor voicing \/ no 3rd/);
assert.match(elements["explorer-selected-detail"].textContent, /Present tonesroot \(G\), 9th \(A\), 5th \(D\)/);
assert.match(elements["explorer-selected-detail"].textContent, /Omitted tones3rd \(B\)/);
assert.match(elements["explorer-selected-detail"].textContent, /WarningsNo 3rd is present/);
assert.equal(lastMount.options.positions[0].grip, "5-7-8");
assert.equal(lastMount.options.positions[0].voicing_status, "color");
assert.equal(JSON.stringify(lastMount.options.positions[0].omitted_tones), JSON.stringify(["3rd (B)"]));
assert.equal(lastMount.options.positions[0].notes.join(","), "D,A,G");

elements["explorer-voicing-fret"].value = "3";
elements["explorer-voicing-fret"].dispatchChange();
setVoicingStrings([5, 6, 7]);
setVoicingControls(["B"]);
assert.match(elements["explorer-voicing-identifier"].textContent, /D7 color \/ partial V7 in G/);
assert.match(elements["explorer-selected-detail"].textContent, /Grip typePath grip/);
assert.match(elements["explorer-selected-detail"].textContent, /Why use this gripA path grip/);
assert.equal(lastMount.options.positions[0].grip, "5-6-7");
assert.equal(lastMount.options.positions[0].notes.join(","), "D,C,A");
setVoicingControls([]);

elements["explorer-voicing-fret"].value = "3";
elements["explorer-voicing-fret"].dispatchChange();
setVoicingStrings([3, 5, 9]);
assert.match(elements["explorer-voicing-identifier"].textContent, /Bdim chord/);
assert.match(elements["explorer-selected-detail"].textContent, /Grip typeSong\/tab vocabulary grip/);
assert.match(elements["explorer-selected-detail"].textContent, /Watch outThe 9th-string color is context-dependent/);
assert.equal(lastMount.options.positions[0].grip, "3-5-9");
assert.equal(lastMount.options.positions[0].notes.join(","), "B,D,F");
setVoicingControls([]);

elements["explorer-voicing-fret"].value = "10";
elements["explorer-voicing-fret"].dispatchChange();
setVoicingStrings([4, 5, 6, 9]);
assert.match(elements["explorer-voicing-identifier"].textContent, /D7/);
assert.match(elements["explorer-selected-detail"].textContent, /Likely functionV7 in G/);
assert.match(elements["explorer-selected-detail"].textContent, /Dominant 7 \/ V7 grip/);
assert.equal(lastMount.options.positions[0].grip, "4-5-6-9");
assert.equal(lastMount.options.positions[0].notes.join(","), "D,A,F#,C");
setVoicingControls([]);

elements["explorer-voicing-fret"].value = "3";
elements["explorer-voicing-fret"].dispatchChange();
setVoicingStrings([5, 6, 9]);
setVoicingControls(["A", "B"]);
assert.match(elements["explorer-voicing-identifier"].textContent, /Fmaj7\(no3\) partial voicing/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Technical name: Fmaj7\(no3\)/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Partial voicing/);
assert.match(elements["explorer-selected-detail"].textContent, /Fmaj7\(no3\)/);
assert.match(elements["explorer-selected-detail"].textContent, /partial major-7 grip/);
assert.match(elements["explorer-selected-detail"].textContent, /Voicing statusPartial voicing/);
assert.match(elements["explorer-selected-detail"].textContent, /Omitted tones3rd \(A\)/);
assert.match(elements["explorer-selected-detail"].textContent, /Confidencemedium/);
assert.match(elements["explorer-selected-detail"].textContent, /Likely functionoutside the selected scale/);
assert.match(elements["explorer-selected-detail"].textContent, /Selected-key note labels/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /Intervals against key/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /Dominant 7|V7 in G/);
assert.equal(lastMount.options.positions[0].notes.join(","), "E,C,F");

setVoicingStrings([5, 7, 9]);
assert.match(elements["explorer-voicing-identifier"].textContent, /Fmaj7\(no5\) partial voicing/);
assert.match(elements["explorer-selected-detail"].textContent, /Fmaj7\(no5\)/);
assert.match(elements["explorer-selected-detail"].textContent, /Omitted tones5th \(C\)/);
assert.match(elements["explorer-selected-detail"].textContent, /Confidencemedium-high/);
assert.match(elements["explorer-selected-detail"].textContent, /not a common musical grip/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /Dominant 7|V7 in G/);

setVoicingControls([]);
elements["explorer-key"].value = "F";
elements["explorer-key"].dispatchChange();
elements["explorer-voicing-fret"].value = "1";
elements["explorer-voicing-fret"].dispatchChange();
setVoicingStrings([3, 4, 9]);
assert.match(elements["explorer-voicing-identifier"].textContent, /F7\(no5\) partial voicing/);
assert.match(elements["explorer-selected-detail"].textContent, /F7\(no5\)/);
assert.match(elements["explorer-selected-detail"].textContent, /partial dominant-7 grip/);
assert.match(elements["explorer-selected-detail"].textContent, /Intervals in voicing3, 1, ♭7/);
assert.match(elements["explorer-selected-detail"].textContent, /Omitted tones5th \(C\)/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /Fmaj7/);

elements["explorer-key"].value = "G";
elements["explorer-key"].dispatchChange();
elements["explorer-voicing-fret"].value = "3";
elements["explorer-voicing-fret"].dispatchChange();
setVoicingStrings([1, 2, 3]);
assert.match(elements["explorer-voicing-identifier"].textContent, /strings 1-2-3/);
assert.match(elements["explorer-voicing-identifier"].textContent, /not a common musical grip/);
assert.equal(lastMount.options.positions[0].grip, "1-2-3");
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "4").onclick();
assert.equal(lastMount.options.positions[0].grip, "1-2-3-4");
const notesBeforeFifthString = lastMount.options.positions[0].notes.join(",");
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "5").onclick();
assert.match(elements["explorer-voicing-identifier"].textContent, /Choose up to 4 strings/);
assert.equal(lastMount.options.positions[0].grip, "1-2-3-4");
assert.equal(lastMount.options.positions[0].notes.join(","), notesBeforeFifthString);
assert.doesNotMatch(elements["explorer-voicing-identifier"].textContent, /\[object Object\]/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /\[object Object\]/);
elements["explorer-explore-mode"].value = "single";
elements["explorer-explore-mode"].dispatchChange();
assert.equal(elements["explorer-voicing-identifier"].hidden, true);
assert.equal(elements["explorer-string-group-control"].hidden, false);
assert.equal(elements["explorer-harmony-control"].hidden, false);

const expectedMajorScales = {
  C: "C D E F G A B",
  Db: "Db Eb F Gb Ab Bb C",
  D: "D E F# G A B C#",
  Eb: "Eb F G Ab Bb C D",
  E: "E F# G# A B C# D#",
  F: "F G A Bb C D E",
  Gb: "Gb Ab Bb Cb Db Eb F",
  G: "G A B C D E F#",
  Ab: "Ab Bb C Db Eb F G",
  A: "A B C# D E F# G#",
  Bb: "Bb C D Eb F G A",
  B: "B C# D# E F# G# A#"
};
for (const [key, scaleNotes] of Object.entries(expectedMajorScales)) {
  elements["explorer-key"].value = key;
  elements["explorer-key"].dispatchChange();
  assert.equal(elements["explorer-scale-notes"].textContent, scaleNotes.replaceAll(" ", " - "));
  assert.doesNotMatch(elements["explorer-scale-notes"].textContent, /##|B#|E#/);
  assert.equal(lastMount.options.query.key, key);
  assert.equal(lastMount.options.positions.length > 0, true);
  assert.equal(lastMount.options.positions.every((row) => row.key === key), true);
  assert.equal(elements["explorer-empty"].hidden, true);
  assert.doesNotMatch(elements["explorer-row-list"].textContent, /\[object Object\]/);
  assert.doesNotMatch(elements["explorer-active-results"].textContent, /\[object Object\]/);
  assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /\[object Object\]/);
  assert.doesNotMatch(elements["explorer-copedent-chart"].textContent, /\[object Object\]/);
  assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /\[object Object\]/);
}

elements["explorer-copedent"].value = "day-e9-basic";
elements["explorer-copedent"].dispatchChange();
assert.equal(lastMount.options.query.key, "B");
assert.match(elements["explorer-copedent-chart"].textContent, /Day E9/);
assert.match(elements["explorer-copedent-chart"].textContent, /enabled/);
assert.match(elements["explorer-copedent-chart"].textContent, /String\s+Open[\s\S]*C pedal\s+P1[\s\S]*B pedal\s+P2[\s\S]*A pedal\s+P3/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /Day E9/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /data-control-impact-tab="C"[^>]*>C<\/button>/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /data-control-impact-tab="A"[^>]*>A<\/button>/);
assert.doesNotMatch(elements["explorer-copedent-chart"].textContent, /\[object Object\]/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /\[object Object\]/);
elements["explorer-copedent"].value = "emmons-e9-basic";
elements["explorer-copedent"].dispatchChange();
assert.match(elements["explorer-copedent-chart"].textContent, /Emmons E9/);
assert.doesNotMatch(elements["explorer-copedent-chart"].textContent, /B-to-Bb vertical/);

elements["explorer-key"].value = "A";
elements["explorer-key"].dispatchChange();
elements["explorer-harmony"].value = "three_string_diatonic";
elements["explorer-harmony"].dispatchChange();
elements["explorer-string-group"].selectValues(["6-8-10"]);
assert.equal(lastMount.options.positions.length > 0, true);
assert.equal(lastMount.options.positions.every((row) => row.grip === "6-8-10"), true);
assert.equal(lastMount.options.emphasizeVisibleHighlights, true);
assert.equal(lastMount.options.highlightStyle, "prominent");
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "emphasizeStringGroups"), false);
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "selectedStringGroups"), false);
assert.match(elements["explorer-active-results"].textContent, /6-8-10/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /visible positions/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Cards match the SVG markers below/);
assert.equal(elements["explorer-active-results"].querySelectorAll("[data-active-result-row]").length >= lastMount.options.positions.length, true);
assert.equal(elements["explorer-fretboard"].querySelectorAll(".pedal-steel-fretboard__highlight[data-highlight-id]").length, lastMount.options.positions.length);
assert.match(elements["explorer-row-list"].textContent, /6-8-10/);
assert.match(elements["explorer-selected-detail"].textContent, /String group6-8-10/);
elements["explorer-string-group"].selectValues(["5-6-8"]);
assert.equal(lastMount.options.positions.length > 0, true);
assert.equal(lastMount.options.positions.every((row) => row.grip === "5-6-8"), true);
assert.equal(lastMount.options.emphasizeVisibleHighlights, true);
assert.equal(lastMount.options.highlightStyle, "prominent");
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "emphasizeStringGroups"), false);
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "selectedStringGroups"), false);
assert.match(elements["explorer-active-results"].textContent, /5-6-8/);
elements["explorer-string-group"].selectValues(["6-8-10"]);
assert.equal(lastMount.options.positions.length > 0, true);
assert.equal(lastMount.options.positions.every((row) => row.grip === "6-8-10"), true);
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "selectedStringGroups"), false);

elements["explorer-key"].value = "G";
elements["explorer-key"].dispatchChange();
assert.match(elements["explorer-scale-notes"].textContent, /G - A - B - C - D - E - F#/);

elements["explorer-string-group"].selectValues(["4-5-6", "5-6-8"]);
assert.equal(lastMount.options.positions.every((row) => ["4-5-6", "5-6-8"].includes(row.grip)), true);
assert.equal(lastMount.options.positions.some((row) => row.grip === "4-5-6"), true);
assert.equal(lastMount.options.positions.some((row) => row.grip === "5-6-8"), true);

elements["explorer-explore-mode"].value = "path";
elements["explorer-explore-mode"].dispatchChange();
assert.equal(elements["explorer-string-group-control"].hidden, true);
assert.equal(elements["explorer-string-group-control"].getAttribute("aria-hidden"), "true");
assert.equal(elements["explorer-string-group"].disabled, true);
assert.equal(elements["explorer-path-family-control"].hidden, false);
assert.equal(elements["explorer-path-family-control"].getAttribute("aria-hidden"), "false");
assert.equal(elements["explorer-path-family"].disabled, false);
assert.equal(elements["explorer-grip-vocabulary-control"].hidden, true);
assert.equal(elements["explorer-grip-vocabulary-control"].getAttribute("aria-hidden"), "true");
assert.equal(elements["explorer-grip-vocabulary"].disabled, true);
assert.equal(elements["explorer-harmony-control"].hidden, true);
assert.equal(elements["explorer-harmony-control"].getAttribute("aria-hidden"), "true");
assert.equal(elements["explorer-harmony"].value, "three_string_diatonic");
assert.equal(elements["explorer-harmony"].disabled, true);
assert.equal(elements["explorer-fret-range-filter"].hidden, true);
assert.match(elements["explorer-active-results"].textContent, /Low path \(6-8-10 \/ 6-7-10\): Scale path rail/);
assert.match(elements["explorer-active-results"].textContent, /matching full-grip marker/);
assert.match(elements["explorer-active-results"].textContent, /Same-fret grips are staggered/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Step/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Ghost all/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Compare same fret/);
const pathStepButtons = elements["explorer-active-results"].querySelectorAll("[data-path-step]");
assert.equal(pathStepButtons.length, 8);
assert.match(elements["explorer-active-results"].innerHTML, /data-path-step="[^"]+"[^>]*data-marker-tone="/);
assert.match(elements["explorer-active-results"].innerHTML, /data-path-step="[^"]+"[^>]*data-string-group="6-8-10"/);
assert.match(elements["explorer-active-results"].innerHTML, /data-path-step="[^"]+"[^>]*data-string-group="6-7-10"/);
assert.match(elements["explorer-active-results"].textContent, /G — G/);
assert.match(elements["explorer-active-results"].textContent, /A — Am/);
assert.match(elements["explorer-active-results"].textContent, /B — Bm/);
assert.match(elements["explorer-active-results"].textContent, /C — C/);
assert.match(elements["explorer-active-results"].textContent, /D — D/);
assert.match(elements["explorer-active-results"].textContent, /E — Em/);
assert.match(elements["explorer-active-results"].textContent, /F# — F# half-diminished/);
const pathCardGroups = Array.from(elements["explorer-row-list"].innerHTML.matchAll(/data-string-group="([^"]+)"/g)).map((match) => match[1]);
const pathCardIds = Array.from(elements["explorer-row-list"].innerHTML.matchAll(/data-explorer-row="([^"]+)"/g)).map((match) => match[1]);
const pathFrets = pathCardIds.map((id) => {
  const match = id.match(/-(\d+)$/);
  return match ? Number(match[1]) : null;
});
assert.equal(JSON.stringify(pathCardGroups), JSON.stringify(["6-8-10", "6-7-10", "6-7-10", "6-8-10", "6-8-10", "6-7-10", "6-8-10", "6-8-10"]));
assert.equal(JSON.stringify(pathFrets), JSON.stringify([3, 3, 5, 8, 10, 10, 13, 15]));
assert.match(elements["explorer-row-list"].textContent, /A — Am/);
assert.match(elements["explorer-row-list"].textContent, /B — Bm/);
assert.match(elements["explorer-row-list"].textContent, /F# — F# diminished|F# — F# half-diminished/);
assert.match(elements["explorer-row-list"].textContent, /String group changes/);
assert.match(elements["explorer-row-list"].textContent, /minor position uses this A\+B string group in this path/);
assert.equal(lastMount.options.positions.length, 8);
assert.equal(lastMount.options.positions.every((row) => row.strings.length >= 3), true);
assert.equal(lastMount.options.positions.some((row) => row.grip === "6-8-10" && row.strings.join(",") === "6,8,10"), true);
assert.equal(lastMount.options.positions.some((row) => row.grip === "6-7-10" && row.strings.join(",") === "6,7,10"), true);
pathStepButtons[1].onclick();
assert.match(elements["explorer-selected-detail"].textContent, /A — Am/);
assert.equal(lastMount.options.positions.length, 8);
assert.equal(lastMount.options.positions.some((row) => row.grip === "6-8-10"), true);
assert.equal(lastMount.options.positions.some((row) => row.grip === "6-7-10"), true);
pathStepButtons[4].onclick();
assert.match(elements["explorer-selected-detail"].textContent, /D — D/);
assert.equal(lastMount.options.positions.length, 8);
notationModeButtons[2].onclick();
assert.match(elements["explorer-row-list"].textContent, /I — G/);
assert.match(elements["explorer-row-list"].textContent, /ii — Am/);
assert.match(elements["explorer-row-list"].textContent, /iii — Bm/);
assert.match(elements["explorer-active-results"].textContent, /I — G/);
assert.match(elements["explorer-active-results"].textContent, /ii — Am/);
assert.match(elements["explorer-active-results"].textContent, /V — D/);
assert.match(elements["explorer-active-results"].textContent, /vi — Em/);
notationModeButtons[0].onclick();
elements["explorer-path-family"].value = "middle";
elements["explorer-path-family"].dispatchChange();
assert.equal(elements["explorer-row-list"].innerHTML.includes('data-string-group="5-6-8"'), true);
assert.equal(elements["explorer-row-list"].innerHTML.includes('data-string-group="5-6-7"'), true);
elements["explorer-path-family"].value = "high";
elements["explorer-path-family"].dispatchChange();
assert.equal(elements["explorer-row-list"].innerHTML.includes('data-string-group="3-4-5"'), true);
assert.equal(elements["explorer-row-list"].innerHTML.includes('data-string-group="4-5-6"'), true);
elements["explorer-explore-mode"].value = "single";
elements["explorer-explore-mode"].dispatchChange();
assert.equal(elements["explorer-string-group-control"].hidden, false);
assert.equal(elements["explorer-string-group-control"].getAttribute("aria-hidden"), "false");
assert.equal(elements["explorer-string-group"].disabled, false);
assert.equal(elements["explorer-path-family-control"].hidden, true);
assert.equal(elements["explorer-path-family-control"].getAttribute("aria-hidden"), "true");
assert.equal(elements["explorer-path-family"].disabled, true);
assert.equal(elements["explorer-grip-vocabulary-control"].hidden, false);
assert.equal(elements["explorer-grip-vocabulary-control"].getAttribute("aria-hidden"), "false");
assert.equal(elements["explorer-grip-vocabulary"].disabled, false);
assert.equal(elements["explorer-harmony-control"].hidden, false);
assert.equal(elements["explorer-harmony-control"].getAttribute("aria-hidden"), "false");
assert.equal(elements["explorer-harmony"].disabled, false);

elements["explorer-harmony"].value = "two_string_harmonized";
elements["explorer-harmony"].dispatchChange();
assert.equal(elements["explorer-string-group"].value, "all");
assert.match(elements["explorer-string-group"].innerHTML, /All 2-string groups/);
assert.match(elements["explorer-string-group"].innerHTML, />3-5</);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /Core grips/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /5-7-8/);
assert.equal(elements["explorer-empty"].hidden, true);
elements["explorer-string-group"].selectValues(["3-5"]);
impactButtons = elements["explorer-control-impact-preview"].querySelectorAll("[data-control-impact-tab]");
impactButtons.find((button) => button.getAttribute("data-control-impact-tab") === "E-lower").onclick();
assert.match(elements["explorer-control-impact-preview"].textContent, /No direct impact on the selected string group/);
assert.match(elements["explorer-control-impact-preview"].textContent, /strings 4, 8/);
elements["explorer-control-impact-preview"].querySelector("[data-control-impact-clear]").onclick();
impactButtons = elements["explorer-control-impact-preview"].querySelectorAll("[data-control-impact-tab]");
impactButtons.find((button) => button.getAttribute("data-control-impact-tab") === "B").onclick();
assert.match(elements["explorer-control-impact-preview"].textContent, /String 3/);
assert.match(elements["explorer-control-impact-preview"].textContent, /G# -&gt; A/);
assert.match(elements["explorer-control-impact-preview"].textContent, /B by itself may not match rows in this view that expect A\+B together/);
elements["explorer-control-impact-preview"].querySelector("[data-control-impact-clear]").onclick();

elements["explorer-scale"].value = "natural_minor";
elements["explorer-scale"].dispatchChange();
assert.equal(elements["explorer-harmony"].value, "three_string_diatonic");
assert.equal(elements["explorer-harmony"].options.find((item) => item.value === "two_string_harmonized").disabled, true);
assert.equal(elements["explorer-harmony"].options.some((item) => item.value === "five_eight_branch"), false);
assert.equal(elements["explorer-string-group"].value, "all");
assert.match(elements["explorer-scale-notes"].textContent, /G - A - Bb - C - D - Eb - F/);
assert.doesNotMatch(elements["explorer-scale-notes"].textContent, /A#|D#/);
assert.equal(elements["explorer-empty"].hidden, true);
assert.doesNotMatch(elements["explorer-row-list"].textContent, /\[object Object\]/);

elements["explorer-scale"].value = "major";
elements["explorer-scale"].dispatchChange();
assert.equal(elements["explorer-harmony"].options.some((item) => item.value === "five_eight_branch"), false);
elements["explorer-harmony"].value = "two_string_harmonized";
elements["explorer-harmony"].dispatchChange();
assert.equal(elements["explorer-string-group"].value, "all");
assert.match(elements["explorer-string-group"].innerHTML, /All 2-string groups/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /5&amp;8 branch/);
assert.match(elements["explorer-string-group"].innerHTML, />5-8</);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /Core grips/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /Advanced swaps/);
assert.match(elements["explorer-string-group"].innerHTML, />3-5</);
assert.equal(lastMount.options.positions.some((row) => row.harmony_type === "five_eight_branch"), true);
assert.match(elements["explorer-row-list"].textContent, /5&amp;8 branch/);
assert.doesNotMatch(elements["explorer-row-list"].textContent, /five_eight_branch/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /five_eight_branch/);
elements["explorer-string-group"].selectValues(["5-8"]);
assert.equal(lastMount.options.positions.length, 4);
assert.equal(lastMount.options.positions.every((row) => row.harmony_type === "five_eight_branch"), true);
assert.equal(lastMount.options.positions.every((row) => row.grip === "5-8"), true);
assert.equal(lastMount.options.emphasizeVisibleHighlights, true);
assert.equal(lastMount.options.highlightStyle, "prominent");
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "emphasizeStringGroups"), false);
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "selectedStringGroups"), false);
assert.match(elements["explorer-selected-detail"].textContent, /5&amp;8 branch/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /five_eight_branch/);

elements["explorer-harmony"].value = "three_string_diatonic";
elements["explorer-harmony"].dispatchChange();
assert.equal(elements["explorer-string-group"].value, "all");
assert.equal(lastMount.options.positions.length > 0, true);
assert.equal(lastMount.options.positions.some((row) => row.grip === "5-8"), false);
assert.equal(elements["explorer-empty"].hidden, true);
elements["explorer-grip-vocabulary"].value = "all";
elements["explorer-grip-vocabulary"].dispatchChange();
elements["explorer-string-group"].selectValues(["5-7-8"]);
assert.match(elements["explorer-selected-detail"].textContent, /Per-string changes/);
assert.match(elements["explorer-selected-detail"].textContent, /Changes used here/);
assert.match(elements["explorer-selected-detail"].textContent, /Why this position works/);
assert.match(elements["explorer-selected-detail"].textContent, /E-lower/);
assert.match(elements["explorer-selected-detail"].textContent, /lowers 1 semitone/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /E-lower\+E-lower/);
assert.doesNotMatch(elements["explorer-row-list"].textContent, /E-lower\+E-lower/);
const tooltipMarker = elements["explorer-fretboard"].querySelectorAll(".pedal-steel-fretboard__highlight[data-highlight-id]")[0];
assert.match(tooltipMarker.getAttribute("aria-label"), /Fret/);
assert.match(tooltipMarker.getAttribute("aria-label"), /Notes:/);
assert.match(tooltipMarker.getAttribute("aria-label"), /Pedals\/levers:/);
assert.doesNotMatch(tooltipMarker.getAttribute("aria-label"), /E-lower\+E-lower/);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
