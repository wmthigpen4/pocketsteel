from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPONENT = Path("ui/pedal-steel-fretboard.js")
STYLES = Path("ui/pedal-steel-fretboard-styles.js")
DEMO = Path("ui/pedal-steel-fretboard-demo.html")


def run_node(script: str) -> str:
    result = subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def component_eval_script(assertions: str) -> str:
    return f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const sandbox = {{ window: {{}} }};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("{STYLES}", "utf8"), sandbox);
const code = fs.readFileSync("{COMPONENT}", "utf8");
vm.runInContext(code, sandbox);
const fretboard = vm.runInContext("window.STEEL_RAG_FRETBOARD", sandbox);

{assertions}
"""


def test_normalized_fret_positions_use_equal_temperament_math() -> None:
    script = component_eval_script(
        """
assert.equal(fretboard.normalizedFretPosition(0, 24), 0);
assert.ok(Math.abs(fretboard.normalizedFretPosition(12, 24) - 0.5) < 0.000001);
assert.ok(Math.abs(fretboard.normalizedFretPosition(24, 24) - 0.75) < 0.000001);

const fret12 = fretboard.normalizedFretPosition(12, 24);
const expected12 = 1 - Math.pow(2, -12 / 12);
assert.ok(Math.abs(fret12 - expected12) < 0.000001);
const fret24 = fretboard.normalizedFretPosition(24, 24);
const expected24 = 1 - Math.pow(2, -24 / 12);
assert.ok(Math.abs(fret24 - expected24) < 0.000001);

const fret1 = fretboard.normalizedFretPosition(1, 24);
const fret2 = fretboard.normalizedFretPosition(2, 24);
const fret3 = fretboard.normalizedFretPosition(3, 24);
assert.ok(fret1 > 0);
assert.ok(fret2 > fret1);
assert.ok(fret3 > fret2);
assert.ok((fret2 - fret1) > (fret3 - fret2));
"""
    )

    run_node(script)


def test_default_model_has_10_e9_strings_and_24_frets_plus_nut() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel();
assert.equal(model.maxFret, 24);
assert.equal(model.stringCount, 10);
assert.equal(JSON.stringify(model.tuningLabels), JSON.stringify(["F#", "D#", "G#", "E", "B", "G#", "F#", "E", "D", "B"]));
assert.equal(model.strings.length, 10);
assert.equal(model.fretPositions.length, 25);
assert.equal(model.fretPositions[0].fret, 0);
assert.equal(model.fretPositions[24].fret, 24);
assert.equal(model.fretPositions[0].x, model.layout.nutX);
assert.equal(model.layout.scalePx, model.layout.bridgeX - model.layout.nutX);
assert.equal(model.height - model.layout.top - model.layout.bottom, 200);
assert.ok(model.layout.scalePx / (model.height - model.layout.top - model.layout.bottom) >= 5);
assert.ok(Math.abs(model.fretPositions[12].x - (model.layout.nutX + model.layout.scalePx / 2)) < 0.001);
assert.ok(Math.abs(model.fretPositions[24].x - (model.layout.nutX + model.layout.scalePx * 0.75)) < 0.001);
assert.ok(model.layout.stringEndX > model.layout.pickupStartX);
assert.ok(model.fretPositions[24].x < model.layout.pickupStartX - model.layout.hardwareGapPx);
const gap = model.layout.pickupStartX - model.fretPositions[24].x;
assert.ok(gap >= 55 && gap <= 75);
assert.ok(Math.abs(gap - 65) < 0.001);
assert.ok(Math.abs(model.markerY - ((model.strings[4].y + model.strings[5].y) / 2)) < 0.001);
assert.ok(model.markerY > model.strings[4].y);
assert.ok(model.markerY < model.strings[5].y);
assert.ok(model.fretPositions[1].x - model.fretPositions[0].x > model.fretPositions[24].x - model.fretPositions[23].x);
assert.equal(JSON.stringify(model.markers), JSON.stringify([3, 5, 7, 9, 12, 15, 17, 19, 21, 24]));
"""
    )

    run_node(script)


def test_scientific_octave_overlay_is_opt_in_string_aware_and_marker_aware() -> None:
    script = component_eval_script(
        """
const position = {
  id: "melody-event-1",
  label: "D4",
  fret: 3,
  strings: [5, 6],
  scientificOctavesByString: { 5: 4, 6: 3 }
};
const hiddenHtml = fretboard.renderPedalSteelFretboard({ positions: [position] });
assert.doesNotMatch(hiddenHtml, /data-scientific-octave-overlay/);

const model = fretboard.buildFretboardModel({
  positions: [position],
  showScientificOctaveOverlay: true
});
assert.equal(model.showScientificOctaveOverlay, true);
assert.equal(model.allHighlights[0].scientificOctavesByString["5"], 4);
assert.equal(model.allHighlights[0].scientificOctavesByString["6"], 3);
const zones = fretboard.scientificOctaveZones(model);
assert.ok(zones.length > 10);
assert.ok(zones.some((zone) => zone.string === 10 && zone.octave === 2 && zone.fretStart === 0 && zone.fretEnd === 0));
assert.ok(zones.some((zone) => zone.string === 4 && zone.octave === 4 && zone.fretStart === 0));

const html = fretboard.renderPedalSteelFretboard({
  positions: [position],
  showScientificOctaveOverlay: true
});
assert.match(html, /data-scientific-octave-overlay/);
assert.match(html, /data-scientific-octave-zone[^>]*data-scientific-octave="2"[^>]*data-octave-string="10"/);
assert.match(html, /data-highlight-dot[^>]*data-highlight-string="5"[^>]*data-scientific-octave="4"/);
assert.match(html, /data-highlight-dot[^>]*data-highlight-string="6"[^>]*data-scientific-octave="3"/);
assert.doesNotMatch(html, /\\[object Object\\]/);
"""
    )

    run_node(script)


def test_every_fret_gap_follows_equal_temperament_ratio() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel();
const expectedRatio = Math.pow(2, -1 / 12);
const gaps = [];
for (let fret = 1; fret <= 24; fret += 1) {
  gaps.push(model.fretPositions[fret].x - model.fretPositions[fret - 1].x);
}
assert.equal(gaps.length, 24);
for (let index = 1; index < gaps.length; index += 1) {
  assert.ok(gaps[index] < gaps[index - 1], `gap ${index + 1} should be smaller than previous gap`);
  assert.ok(Math.abs((gaps[index] / gaps[index - 1]) - expectedRatio) < 0.000001);
}
"""
    )

    run_node(script)


def test_playable_scale_stops_before_pickup_and_changer_hardware() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel({ highlights: fretboard.DEMO_HIGHLIGHTS });
const fret24 = model.fretPositions[24].x;
const marker24 = model.fretPositions[model.markers.at(-1)].x;
const gap = model.layout.pickupStartX - fret24;
assert.equal(model.markers.at(-1), 24);
assert.equal(fret24, marker24);
assert.ok(Math.abs(fret24 - (model.layout.nutX + model.layout.scalePx * 0.75)) < 0.001);
assert.ok(fret24 < model.layout.pickupStartX - model.layout.hardwareGapPx);
assert.ok(gap >= 55 && gap <= 75);
assert.ok(Math.abs(gap - 65) < 0.001);
assert.ok(model.layout.bridgeX > model.layout.pickupStartX);
assert.ok(model.layout.pickupStartX < model.layout.stringEndX);
assert.ok(model.layout.stringEndX < model.width);
assert.equal(model.layout.hardwareGapPx, 48);
assert.equal(model.highlights.find((item) => item.id === "g-major-af-6").fret, 6);
assert.equal(model.highlights.find((item) => item.id === "g-major-ab-10").fret, 10);
"""
    )

    run_node(script)


def test_rendered_svg_has_strings_frets_markers_and_demo_highlights() -> None:
    script = component_eval_script(
        """
const html = fretboard.renderPedalSteelFretboard({ highlights: fretboard.DEMO_HIGHLIGHTS });
assert.match(html, /data-component="PedalSteelFretboard"/);
assert.match(html, /data-string-count="10"/);
assert.match(html, /data-max-fret="24"/);
assert.match(html, /data-spacing="equal-temperament"/);
assert.equal((html.match(/data-fretboard-string="/g) || []).length, 10);
assert.equal((html.match(/data-fret-line="/g) || []).length, 25);
assert.equal((html.match(/data-fret-marker="/g) || []).length, 10);
const fretLines = Array.from(html.matchAll(/data-fret-line="(\\d+)"/g)).map((match) => Number(match[1]));
assert.equal(fretLines.filter((fret) => fret > 0).length, 24);
assert.equal(fretLines[0], 0);
assert.equal(fretLines.at(-1), 24);
const markerFrets = Array.from(html.matchAll(/data-fret-marker="(\\d+)"/g)).map((match) => Number(match[1]));
assert.deepEqual(markerFrets, [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]);
assert.equal((html.match(/data-fret-marker-emphasis="true"/g) || []).length, 2);
assert.equal((html.match(/data-fret-marker-placement="space"/g) || []).length, 10);
assert.equal((html.match(/data-fret-marker-position="between-strings-5-6"/g) || []).length, 10);
assert.equal((html.match(/data-fret-marker-style="printed-diamond"/g) || []).length, 10);
assert.equal((html.match(/data-fret-marker-diamond="/g) || []).length, 14);
assert.equal((html.match(/data-fret-marker-diamond="12"/g) || []).length, 3);
assert.equal((html.match(/data-fret-marker-diamond="24"/g) || []).length, 3);
assert.match(html, /data-highlight-id="g-major-open-3"/);
assert.match(html, /data-highlight-id="g-major-af-6"/);
assert.match(html, /data-highlight-id="g-major-ab-10"/);
assert.match(html, /data-highlight-fret="3"/);
assert.match(html, /data-highlight-fret="6"/);
assert.match(html, /data-highlight-fret="10"/);
assert.match(html, /data-highlight-strings="4,5,6"/);
assert.match(html, /A\\+B position/);
assert.match(html, /E raise\\/F lever/);
assert.match(html, /A\\+F position/);
assert.doesNotMatch(html, /E9 PEDAL STEEL/);
"""
    )

    run_node(script)


def test_high_fret_number_labels_are_compact_without_moving_frets() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel();
const html = fretboard.renderPedalSteelFretboard({ highlights: fretboard.DEMO_HIGHLIGHTS });
const compactLabels = Array.from(html.matchAll(/data-fret-number="(\\d+)" data-fret-number-density="compact" x="([^"]+)" y="([^"]+)"[^>]*font-size="(\\d+)"/g));
assert.equal(compactLabels.length, 5);
assert.deepEqual(compactLabels.map((match) => Number(match[1])), [15, 17, 19, 21, 24]);
for (const match of compactLabels) {
  const fret = Number(match[1]);
  const x = Number(match[2]);
  const y = Number(match[3]);
  const fontSize = Number(match[4]);
  assert.ok(Math.abs(x - model.fretPositions[fret].x) < 0.001);
  assert.equal(fontSize, 16);
  assert.equal(y, model.height - 38);
}
const visibleLabels = Array.from(html.matchAll(/data-fret-number="(\\d+)"/g)).map((match) => Number(match[1]));
assert.deepEqual(visibleLabels, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 17, 19, 21, 24]);
assert.equal((html.match(/data-fret-number-density="standard"/g) || []).length, 12);
assert.match(html, /paint-order="stroke fill"/);
"""
    )

    run_node(script)


def test_printed_fret_markers_are_centered_in_fret_spaces_and_playable_region() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel();
const html = fretboard.renderPedalSteelFretboard({ highlights: fretboard.DEMO_HIGHLIGHTS });
const markerGroups = Array.from(html.matchAll(/data-fret-marker="(\\d+)"[^>]*data-fret-marker-y="([^"]+)"/g));
assert.equal(markerGroups.length, 10);
for (const match of markerGroups) {
  const fret = Number(match[1]);
  const markerY = Number(match[2]);
  assert.ok(Math.abs(markerY - model.markerY) < 0.001);
  assert.ok(markerY > model.strings[4].y, `marker ${fret} should be below string 5`);
  assert.ok(markerY < model.strings[5].y, `marker ${fret} should be above string 6`);
  assert.ok(markerY < model.strings[9].y, `marker ${fret} should not sit below string 10`);
}
const markers = Array.from(html.matchAll(/data-fret-marker-diamond="(\\d+)"[^>]*points="([^"]+)"/g));
assert.equal(markers.length, 14);
for (const match of markers) {
  const fret = Number(match[1]);
  const centerX = Number(match[2].split(" ")[0].split(",")[0]);
  const previousFretX = model.fretPositions[fret - 1].x;
  const fretX = model.fretPositions[fret].x;
  const expectedCenter = (previousFretX + fretX) / 2;
  assert.ok(centerX > previousFretX, `marker ${fret} should be after fret line ${fret - 1}`);
  assert.ok(centerX < fretX, `marker ${fret} should be before fret line ${fret}`);
  assert.ok(Math.abs(centerX - expectedCenter) < 0.001);
}
assert.equal(markers.filter((match) => Number(match[1]) === 12).length, 3);
assert.equal(markers.filter((match) => Number(match[1]) === 24).length, 3);
"""
    )

    run_node(script)


def test_explorer_selected_group_renders_localized_markers_without_string_lanes() -> None:
    script = component_eval_script(
        """
const positions = [
  {
    id: "g-568-fret-3",
    label: "G at fret 3",
    fret: 3,
    strings: [5, 6, 8],
    grip: "5-6-8",
    visibleByDefault: true,
    colorRole: "open"
  },
  {
    id: "g-568-fret-8",
    label: "C at fret 8",
    fret: 8,
    strings: [5, 6, 8],
    grip: "5-6-8",
    visibleByDefault: true,
    colorRole: "open"
  }
];
const model = fretboard.buildFretboardModel({
  positions,
  hideFilterControls: true,
  hidePositionTools: true,
  hideLegend: true,
  showHighlightLabels: false,
  emphasizeVisibleHighlights: true
});
assert.equal(model.highlights.length, 2);
assert.equal(model.highlightStyle, "standard");
assert.equal(Object.prototype.hasOwnProperty.call(model, "emphasizeStringGroups"), false);
assert.equal(Object.prototype.hasOwnProperty.call(model, "emphasizedStrings"), false);
assert.equal(Object.prototype.hasOwnProperty.call(model, "emphasizedStringGroups"), false);
const html = fretboard.renderPedalSteelFretboard({
  positions,
  hideFilterControls: true,
  hidePositionTools: true,
  hideLegend: true,
  showHighlightLabels: false,
  emphasizeVisibleHighlights: true
});
assert.doesNotMatch(html, /data-selected-string-group-lanes/);
assert.doesNotMatch(html, /data-selected-strings=/);
assert.doesNotMatch(html, /data-selected-string-groups=/);
assert.equal((html.match(/data-selected-string-row="/g) || []).length, 0);
assert.equal((html.match(/data-highlight-dot/g) || []).length, 6);
assert.equal((html.match(/data-highlight-band/g) || []).length, 2);
assert.equal((html.match(/data-highlight-cluster-style="standard"/g) || []).length, 10);
assert.equal((html.match(/data-highlight-halo/g) || []).length, 0);
assert.equal((html.match(/data-highlight-strings="5,6,8"/g) || []).length >= 2, true);
assert.equal((html.match(/data-highlight-string="5"/g) || []).length, 2);
assert.equal((html.match(/data-highlight-string="6"/g) || []).length, 2);
assert.equal((html.match(/data-highlight-string="8"/g) || []).length, 2);
assert.equal((html.match(/data-emphasized-visible="true"/g) || []).length, 2);
assert.equal((html.match(/is-emphasized-visible/g) || []).length >= 2, true);
assert.equal(html.indexOf("data-fretboard-string=\\"1\\"") < html.indexOf("data-highlight-id=\\"g-568-fret-3\\""), true);
assert.doesNotMatch(html, /\\[object Object\\]/);
assert.doesNotMatch(html, /five_eight_branch/);

const prominentModel = fretboard.buildFretboardModel({
  positions,
  hideFilterControls: true,
  hidePositionTools: true,
  hideLegend: true,
  showHighlightLabels: false,
  emphasizeVisibleHighlights: true,
  highlightStyle: "prominent"
});
assert.equal(prominentModel.highlightStyle, "prominent");
const prominentHtml = fretboard.renderPedalSteelFretboard({
  positions,
  hideFilterControls: true,
  hidePositionTools: true,
  hideLegend: true,
  showHighlightLabels: false,
  emphasizeVisibleHighlights: true,
  highlightStyle: "prominent"
});
assert.doesNotMatch(prominentHtml, /data-selected-string-group-lanes/);
assert.doesNotMatch(prominentHtml, /data-selected-string-row="/);
assert.equal((prominentHtml.match(/data-highlight-dot/g) || []).length, 6);
assert.equal((prominentHtml.match(/data-highlight-halo/g) || []).length, 6);
assert.equal((prominentHtml.match(/data-highlight-band/g) || []).length, 2);
assert.equal((prominentHtml.match(/data-highlight-cluster-style="prominent"/g) || []).length, 16);
assert.equal((prominentHtml.match(/is-prominent-cluster/g) || []).length, 2);
assert.match(prominentHtml, /data-highlight-dot[^>]*width="42" height="24"/);
assert.match(prominentHtml, /data-highlight-band[^>]*width="52"/);
assert.equal((prominentHtml.match(/data-filter-visible="true"/g) || []).length, 2);
assert.equal((prominentHtml.match(/data-filter-visible="false"/g) || []).length, 0);
assert.doesNotMatch(prominentHtml, /is-filter-hidden/);
assert.equal((prominentHtml.match(/data-highlight-strings="5,6,8"/g) || []).length >= 2, true);
assert.doesNotMatch(prominentHtml, /data-highlight-label="g-568-fret-3"/);
assert.doesNotMatch(prominentHtml, /\\[object Object\\]/);
assert.doesNotMatch(prominentHtml, /five_eight_branch/);
	"""
    )

    run_node(script)


def test_same_fret_full_grips_are_staggered_without_changing_fret_math() -> None:
    script = component_eval_script(
        """
const positions = [
  {
    id: "path-g-fret-3-6810",
    label: "G",
    fret: 3,
    strings: [6, 8, 10],
    grip: "6-8-10",
    visibleByDefault: true,
    colorRole: "open"
  },
  {
    id: "path-am-fret-3-6710",
    label: "Am",
    fret: 3,
    strings: [6, 7, 10],
    grip: "6-7-10",
    visibleByDefault: true,
    colorRole: "a-b"
  }
];
const model = fretboard.buildFretboardModel({
  positions,
  hideFilterControls: true,
  hidePositionTools: true,
  hideLegend: true,
  showHighlightLabels: true,
  emphasizeVisibleHighlights: true
});
assert.equal(model.highlights.length, 2);
assert.equal(model.highlights[0].fret, 3);
assert.equal(model.highlights[1].fret, 3);
assert.equal(model.highlights[0].x, model.highlights[1].x);
assert.notEqual(model.highlights[0].renderX, model.highlights[1].renderX);
assert.equal(model.highlights[0].renderOffsetX, -9);
assert.equal(model.highlights[1].renderOffsetX, 9);
assert.equal(model.highlights[0].overlapLaneCount, 2);
assert.equal(model.highlights[1].overlapLaneCount, 2);
assert.equal(JSON.stringify(model.highlights.map((item) => item.strings.join(","))), JSON.stringify(["6,8,10", "6,7,10"]));
const html = fretboard.renderPedalSteelFretboard({
  positions,
  hideFilterControls: true,
  hidePositionTools: true,
  hideLegend: true,
  showHighlightLabels: true,
  emphasizeVisibleHighlights: true
});
assert.match(html, /data-highlight-id="path-g-fret-3-6810"[^>]*data-highlight-fret-x="[^"]+"[^>]*data-highlight-render-offset-x="-9\\.000"/);
assert.match(html, /data-highlight-id="path-am-fret-3-6710"[^>]*data-highlight-fret-x="[^"]+"[^>]*data-highlight-render-offset-x="9\\.000"/);
assert.match(html, /data-highlight-id="path-g-fret-3-6810"[^>]*data-highlight-strings="6,8,10"/);
assert.match(html, /data-highlight-id="path-am-fret-3-6710"[^>]*data-highlight-strings="6,7,10"/);
assert.doesNotMatch(html, /\\[object Object\\]/);
"""
    )

    run_node(script)


def test_same_fret_same_string_groups_are_staggered_as_whole_grips() -> None:
    script = component_eval_script(
        """
const positions = [
  {
    id: "same-fret-b-345",
    label: "B",
    fret: 3,
    strings: [3, 4, 5],
    grip: "3-4-5",
    visibleByDefault: true,
    colorRole: "open"
  },
  {
    id: "same-fret-c-345",
    label: "C",
    fret: 3,
    strings: [3, 4, 5],
    grip: "3-4-5",
    visibleByDefault: true,
    colorRole: "a-b"
  }
];
const model = fretboard.buildFretboardModel({
  positions,
  hideFilterControls: true,
  hidePositionTools: true,
  hideLegend: true,
  showHighlightLabels: true,
  emphasizeVisibleHighlights: true
});
assert.equal(model.highlights.length, 2);
assert.equal(model.highlights[0].fret, 3);
assert.equal(model.highlights[1].fret, 3);
assert.equal(model.highlights[0].x, model.highlights[1].x);
assert.notEqual(model.highlights[0].renderX, model.highlights[1].renderX);
assert.equal(model.highlights[0].renderOffsetX, -9);
assert.equal(model.highlights[1].renderOffsetX, 9);
assert.equal(model.highlights[0].overlapLaneCount, 2);
assert.equal(model.highlights[1].overlapLaneCount, 2);
assert.equal(JSON.stringify(model.highlights.map((item) => item.strings.join(","))), JSON.stringify(["3,4,5", "3,4,5"]));
const html = fretboard.renderPedalSteelFretboard({
  positions,
  hideFilterControls: true,
  hidePositionTools: true,
  hideLegend: true,
  showHighlightLabels: true,
  emphasizeVisibleHighlights: true
});
assert.match(html, /data-highlight-id="same-fret-b-345"[^>]*data-highlight-fret-x="[^"]+"[^>]*data-highlight-render-offset-x="-9\\.000"/);
assert.match(html, /data-highlight-id="same-fret-c-345"[^>]*data-highlight-fret-x="[^"]+"[^>]*data-highlight-render-offset-x="9\\.000"/);
assert.match(html, /data-highlight-id="same-fret-b-345"[^>]*data-highlight-strings="3,4,5"/);
assert.match(html, /data-highlight-id="same-fret-c-345"[^>]*data-highlight-strings="3,4,5"/);
assert.doesNotMatch(html, /\\[object Object\\]/);
"""
    )

    run_node(script)


def test_optional_string_action_marker_labels_are_compact_and_off_by_default() -> None:
    script = component_eval_script(
        """
const positions = [
  {
    id: "bc-pedal-grip",
    label: "B+C grip",
    fret: 5,
    strings: [3, 4, 5],
    grip: "3-4-5",
    pedals: ["B", "C"],
    per_string_changes: {
      3: { open_at_fret: "B", final_note: "C", controls: "B pedal", marker_label: "3B" },
      4: { open_at_fret: "E", final_note: "F#", controls: "C pedal", marker_label: "4C" },
      5: { open_at_fret: "B", final_note: "C#", controls: "C pedal", marker_label: "5C" }
    }
  },
  {
    id: "lever-grip",
    label: "Lever grip",
    fret: 8,
    strings: [2, 4, 6, 8],
    grip: "2-4-6-8",
    per_string_changes: {
      2: { open_at_fret: "D#", final_note: "D", controls: "D lower half-stop" },
      4: { open_at_fret: "E", final_note: "F", controls: "E-raise lever" },
      6: { open_at_fret: "G#", final_note: "G", controls: "G lever" },
      8: { open_at_fret: "E", final_note: "Eb", controls: "E-lower lever" }
    }
  },
  {
    id: "vertical-grip",
    label: "Vertical grip",
    fret: 3,
    strings: [5, 6],
    grip: "5-6",
    per_string_changes: {
      5: { open_at_fret: "B", final_note: "Bb", controls: "B-to-Bb vertical" },
      6: { open_at_fret: "G#", final_note: "G#", controls: "no change" }
    }
  }
];
const cleanHtml = fretboard.renderPedalSteelFretboard({
  positions,
  hideFilterControls: true,
  hidePositionTools: true,
  hideLegend: true,
  showStringActionLabels: false
});
assert.doesNotMatch(cleanHtml, /data-string-action-label=/);
assert.doesNotMatch(cleanHtml, />3B</);

const labeledHtml = fretboard.renderPedalSteelFretboard({
  positions,
  hideFilterControls: true,
  hidePositionTools: true,
  hideLegend: true,
  showStringActionLabels: true,
  stringActionLabelMode: "selected"
});
for (const expected of ["3B", "4C", "5C", "2D", "4F", "6G", "8E", "5V", "6"]) {
  assert.match(labeledHtml, new RegExp(`data-string-action-label="${expected}"`));
  assert.match(labeledHtml, new RegExp(`>${expected}<`));
}
for (const invalid of ["S3", "String 3", "3 B", "E-raise", "E-lower", "E↑", "E↓", "B pedal", "C pedal"]) {
  assert.equal(labeledHtml.includes(invalid), false);
}
assert.match(labeledHtml, /data-string-action-label-mode="selected"/);
assert.doesNotMatch(labeledHtml, /\\[object Object\\]/);
"""
    )

    run_node(script)


def test_programmatic_selection_works_when_position_tools_are_hidden() -> None:
    script = component_eval_script(
        """
const targetId = "melody-event-2";
const classNames = new Set();
const highlight = {
  hidden: false,
  style: {},
  dataset: { filterVisible: "true" },
  getAttribute(name) {
    return name === "data-highlight-id" ? targetId : null;
  },
  classList: {
    toggle(name, enabled) {
      if (enabled) classNames.add(name);
      else classNames.delete(name);
    }
  }
};
const figure = {
  dataset: {},
  matches(selector) {
    return selector === "[data-component='PedalSteelFretboard']";
  },
  querySelector(selector) {
    if (selector === `[data-highlight-id="${targetId}"]`) return highlight;
    return null;
  },
  querySelectorAll(selector) {
    return selector === ".pedal-steel-fretboard__highlight" ? [highlight] : [];
  }
};
assert.equal(fretboard.selectPedalSteelFretboardPosition(figure, targetId), true);
assert.equal(figure.dataset.selectedPositionId, targetId);
assert.equal(classNames.has("is-selected"), true);
assert.equal(fretboard.selectPedalSteelFretboardPosition(figure, "missing"), false);
"""
    )

    run_node(script)


def test_rendered_svg_uses_decorative_background_underlay() -> None:
    script = component_eval_script(
        """
const html = fretboard.renderPedalSteelFretboard({ highlights: fretboard.DEMO_HIGHLIGHTS });
const backgroundHref = '/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f';
const backgroundIndex = html.indexOf(`href="${backgroundHref}"`);
const panelIndex = html.indexOf('width="1164" height="306"');
const fretIndex = html.indexOf('data-fret-line="0"');
const markerIndex = html.indexOf('data-fret-marker="3"');
const stringIndex = html.indexOf('data-fretboard-string="1"');
const highlightIndex = html.indexOf('data-highlight-id="g-major-open-3"');
assert.ok(backgroundIndex > -1);
assert.match(html, /class="pedal-steel-background"/);
assert.match(html, /x="-139"/);
assert.match(html, /y="-65"/);
assert.match(html, /width="1493"/);
assert.match(html, /height="442"/);
assert.match(html, /opacity="0.68"/);
assert.match(html, /preserveAspectRatio="none"/);
assert.match(html, /pointer-events="none"/);
assert.ok(backgroundIndex < panelIndex);
assert.ok(panelIndex < fretIndex);
assert.ok(fretIndex < markerIndex);
assert.ok(markerIndex < stringIndex);
assert.ok(stringIndex < highlightIndex);
assert.equal((html.match(/href="\\/brand\\/pedal-steel-fretboard-background\\.svg\\?v=keyhead-vshape-bce771f"/g) || []).length, 1);
assert.equal((html.match(/href="\\/brand\\/pedal-steel-fretboard-background\\.svg"/g) || []).length, 0);
"""
    )

    run_node(script)


def test_selectorless_mount_keeps_explorer_highlights_visible() -> None:
    component = (REPO_ROOT / COMPONENT).read_text(encoding="utf-8")

    assert 'const hasPositionSelectors = Boolean(figure.querySelector("[data-position-selector]"));' in component
    assert "if (hasPositionSelectors) {" in component
    assert "updatePositionFilter(figure);" in component
    assert "selectPosition(figure, figure.dataset.selectedPositionId);" in component


def test_position_dots_use_distinct_explained_color_roles() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel({ positions: fretboard.DEMO_POSITIONS });
assert.equal(JSON.stringify(model.highlights.map((item) => item.colorRole)), JSON.stringify(["open", "a-f", "a-b"]));
const html = fretboard.renderPedalSteelFretboard({ positions: fretboard.DEMO_POSITIONS });
assert.equal((html.match(/data-color-role="open"/g) || []).length > 0, true);
assert.equal((html.match(/data-color-role="a-f"/g) || []).length > 0, true);
assert.equal((html.match(/data-color-role="a-b"/g) || []).length > 0, true);
assert.equal((html.match(/data-color-role="warning"/g) || []).length, 0);
assert.equal((html.match(/data-color-role="primary"/g) || []).length, 0);
assert.equal((html.match(/data-color-role="secondary"/g) || []).length, 0);
assert.equal((html.match(/data-color-role="alternate"/g) || []).length, 0);
assert.match(html, /#f0bf69/);
assert.match(html, /#8fd5ff/);
assert.match(html, /#8de391/);
"""
    )

    run_node(script)


def test_multiple_highlight_positions_have_distinct_coordinates() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel({ highlights: fretboard.DEMO_HIGHLIGHTS });
assert.equal(model.highlights.length, 3);
assert.equal(JSON.stringify(model.highlights.map((item) => item.fret)), JSON.stringify([3, 6, 10]));
assert.equal(model.highlights[1].id, "g-major-af-6");
assert.equal(model.highlights[1].role, "A+F position");
assert.equal(JSON.stringify(model.highlights[1].pedals), JSON.stringify(["A"]));
assert.equal(JSON.stringify(model.highlights[1].levers), JSON.stringify(["E raise/F lever"]));
assert.equal(model.highlights[2].id, "g-major-ab-10");
assert.equal(model.highlights[2].role, "A+B position");
assert.equal(JSON.stringify(model.highlights[2].pedals), JSON.stringify(["A", "B"]));
assert.equal(JSON.stringify(model.highlights[2].levers), JSON.stringify([]));
assert.equal(JSON.stringify(model.highlights.map((item) => item.strings.join("-"))), JSON.stringify(["4-5-6", "4-5-6", "4-5-6"]));
assert.ok(model.highlights[0].x < model.highlights[1].x);
assert.ok(model.highlights[1].x < model.highlights[2].x);
for (const highlight of model.highlights) {
  assert.equal(highlight.stringYs.length, 3);
  assert.ok(highlight.stringYs[0] < highlight.stringYs[1]);
  assert.ok(highlight.stringYs[1] < highlight.stringYs[2]);
}
"""
    )

    run_node(script)


def test_contract_positions_are_primary_over_legacy_highlights() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel({
  positions: fretboard.DEMO_POSITIONS,
  highlights: [{
    id: "wrong-legacy-ab-6",
    label: "Wrong legacy A+B",
    fret: 6,
    strings: [4, 5, 6],
    pedals: ["A", "B"]
  }]
});
assert.equal(model.highlights.length, 3);
assert.equal(JSON.stringify(model.highlights.map((item) => item.id)), JSON.stringify([
  "g-position-open-3",
  "g-position-af-6",
  "g-position-ab-10"
]));
assert.equal(JSON.stringify(model.highlights.map((item) => item.fret)), JSON.stringify([3, 6, 10]));
assert.equal(model.highlights[1].id, "g-position-af-6");
assert.equal(model.highlights[1].role, "A+F position");
assert.equal(JSON.stringify(model.highlights[1].pedals), JSON.stringify(["A"]));
assert.equal(JSON.stringify(model.highlights[1].levers), JSON.stringify(["E raise/F lever"]));
assert.equal(model.highlights[1].grip, "4-5-6");
assert.equal(model.highlights[1].explanation, "A pedal plus the E raise makes the G pocket at fret 6.");
assert.equal(model.highlights[2].id, "g-position-ab-10");
assert.equal(model.highlights[2].role, "A+B position");
assert.equal(JSON.stringify(model.highlights[2].pedals), JSON.stringify(["A", "B"]));
assert.equal(JSON.stringify(model.highlights[2].levers), JSON.stringify([]));
assert.equal(model.highlights[2].fret, 10);
assert.ok(model.highlights.every((item) => item.sourceType === "position"));
assert.equal(JSON.stringify(model.highlights.map((item) => item.strings.join("-"))), JSON.stringify(["4-5-6", "4-5-6", "4-5-6"]));
assert.ok(model.highlights[0].x < model.highlights[1].x);
assert.ok(model.highlights[1].x < model.highlights[2].x);
"""
    )

    run_node(script)


def test_committed_contract_positions_render_with_stable_g_major_facts() -> None:
    script = component_eval_script(
        """
const committedPositions = [
  {
    id: "g-open-3",
    label: "G major",
    fret: 3,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: [],
    levers: [],
    color: "primary",
    role: "Open position"
  },
  {
    id: "g-af-6",
    label: "G major",
    fret: 6,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: ["A"],
    levers: ["F"],
    color: "secondary",
    role: "A+F position"
  },
  {
    id: "g-ab-10",
    label: "G major",
    fret: 10,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: ["A", "B"],
    levers: [],
    color: "alternate",
    role: "A+B position"
  }
];
const staleHighlights = [
  {
    id: "wrong-legacy-af-10",
    label: "Wrong legacy A+F",
    fret: 10,
    strings: [4, 5, 6],
    pedals: ["A"],
    levers: ["F"],
    role: "Wrong A+F"
  },
  {
    id: "wrong-legacy-ab-6",
    label: "Wrong legacy A+B",
    fret: 6,
    strings: [4, 5, 6],
    pedals: ["A", "B"],
    role: "Wrong A+B"
  }
];
const model = fretboard.buildFretboardModel({ positions: committedPositions, highlights: staleHighlights });
const byId = Object.fromEntries(model.highlights.map((item) => [item.id, item]));
assert.deepEqual(model.highlights.map((item) => item.id), ["g-open-3", "g-af-6", "g-ab-10"]);
assert.equal(byId["g-open-3"].fret, 3);
assert.equal(JSON.stringify(byId["g-open-3"].strings), JSON.stringify([4, 5, 6]));
assert.equal(JSON.stringify(byId["g-open-3"].pedals), JSON.stringify([]));
assert.equal(JSON.stringify(byId["g-open-3"].levers), JSON.stringify([]));
assert.equal(byId["g-af-6"].fret, 6);
assert.equal(JSON.stringify(byId["g-af-6"].strings), JSON.stringify([4, 5, 6]));
assert.equal(JSON.stringify(byId["g-af-6"].pedals), JSON.stringify(["A"]));
assert.equal(JSON.stringify(byId["g-af-6"].levers), JSON.stringify(["F"]));
assert.equal(byId["g-ab-10"].fret, 10);
assert.equal(JSON.stringify(byId["g-ab-10"].strings), JSON.stringify([4, 5, 6]));
assert.equal(JSON.stringify(byId["g-ab-10"].pedals), JSON.stringify(["A", "B"]));
assert.equal(JSON.stringify(byId["g-ab-10"].levers), JSON.stringify([]));
assert.ok(model.highlights.every((item) => item.sourceType === "position"));
assert.equal(model.highlights.some((item) => item.id.startsWith("wrong-legacy")), false);
assert.equal(byId["g-af-6"].fret === 10, false);
assert.equal(byId["g-ab-10"].fret === 6, false);

const html = fretboard.renderPedalSteelFretboard({ positions: committedPositions, highlights: staleHighlights });
assert.match(html, /data-highlight-id="g-open-3"/);
assert.match(html, /data-highlight-id="g-af-6"/);
assert.match(html, /data-highlight-fret="6"/);
assert.match(html, /data-highlight-id="g-ab-10"/);
assert.match(html, /data-highlight-fret="10"/);
assert.match(html, /data-highlight-strings="4,5,6"/);
assert.match(html, /A\\+F position/);
assert.match(html, /A\\+B position/);
assert.doesNotMatch(html, /wrong-legacy/);
assert.doesNotMatch(html, /data-highlight-fret="10"[^>]*data-highlight-id="g-af-6"/);
assert.doesNotMatch(html, /data-highlight-fret="6"[^>]*data-highlight-id="g-ab-10"/);
"""
    )

    run_node(script)


def test_legacy_highlights_still_render_when_positions_are_absent() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel({ highlights: fretboard.DEMO_HIGHLIGHTS });
assert.equal(model.highlights.length, 3);
assert.equal(JSON.stringify(model.highlights.map((item) => item.id)), JSON.stringify([
  "g-major-open-3",
  "g-major-af-6",
  "g-major-ab-10"
]));
assert.equal(JSON.stringify(model.highlights.map((item) => item.fret)), JSON.stringify([3, 6, 10]));
assert.ok(model.highlights.every((item) => item.sourceType === "highlight"));
assert.equal(model.highlights[1].role, "A+F position");
assert.equal(model.highlights[2].role, "A+B position");
"""
    )

    run_node(script)


def test_unsupported_or_empty_contract_payload_does_not_invent_positions() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel({
  positions: [
    {
      id: "unsupported-full-solo",
      label: "Unsupported full solo",
      fret: "not-a-fret",
      strings: [99],
      pedals: ["made-up"],
      levers: ["made-up"]
    }
  ]
});
assert.equal(model.highlights.length, 0);
const html = fretboard.renderPedalSteelFretboard({
  positions: [
    {
      id: "unsupported-full-solo",
      label: "Unsupported full solo",
      fret: "not-a-fret",
      strings: [99],
      pedals: ["made-up"],
      levers: ["made-up"]
    }
  ]
});
assert.doesNotMatch(html, /unsupported-full-solo/);
assert.doesNotMatch(html, /made-up/);
"""
    )

    run_node(script)


def test_rendered_svg_uses_positions_contract_fields_in_legend() -> None:
    script = component_eval_script(
        """
const html = fretboard.renderPedalSteelFretboard({ positions: fretboard.DEMO_POSITIONS });
assert.match(html, /data-highlight-id="g-position-af-6"/);
assert.match(html, /data-highlight-fret="6"/);
assert.match(html, /data-highlight-id="g-position-ab-10"/);
assert.match(html, /data-highlight-fret="10"/);
assert.match(html, /grip 4-5-6/);
assert.match(html, /intervals 1; 3; 5/);
assert.match(html, /Open G pocket/);
assert.match(html, /A pedal plus the E raise makes the G pocket at fret 6\\./);
assert.match(html, /Pedals-down G position at fret 10\\./);
assert.doesNotMatch(html, /wrong-legacy/);
"""
    )

    run_node(script)


def test_position_selector_renders_three_positions_and_default_detail() -> None:
    script = component_eval_script(
        """
const csharpPositions = [
  {
    id: "csharp-open-9",
    label: "C# major",
    fret: 9,
    strings: [4, 5, 6],
    grip: "4-5-6",
    root: "C#",
    quality: "major",
    pedals: [],
    levers: [],
    role: "Open position",
    notes: {"4": "C#", "5": "G#", "6": "E#"},
    intervals: {"4": "1", "5": "5", "6": "3"},
    explanation: "No-pedal C# at fret 9."
  },
  {
    id: "csharp-af-12",
    label: "C# major",
    fret: 12,
    strings: [4, 5, 6],
    grip: "4-5-6",
    root: "C#",
    quality: "major",
    pedals: ["A"],
    levers: ["F"],
    role: "A+F position",
    notes: {"4": "E#", "5": "C#", "6": "G#"},
    intervals: {"4": "3", "5": "1", "6": "5"},
    explanation: "A+F C# at fret 12."
  },
  {
    id: "csharp-ab-16",
    label: "C# major",
    fret: 16,
    strings: [4, 5, 6],
    grip: "4-5-6",
    root: "C#",
    quality: "major",
    pedals: ["A", "B"],
    levers: [],
    role: "A+B position",
    notes: {"4": "E#", "5": "C#", "6": "G#"},
    intervals: {"4": "3", "5": "1", "6": "5"},
    explanation: "A+B C# at fret 16."
  }
];
const html = fretboard.renderPedalSteelFretboard({ positions: csharpPositions, query: { key: "C#", quality: "major" } });
assert.equal((html.match(/data-position-selector="/g) || []).length, 3);
assert.match(html, /data-position-selector="csharp-open-9"/);
assert.match(html, />\\s*<span class="pedal-steel-fretboard__selector-main">9 open<\\/span>/);
assert.match(html, />\\s*<span class="pedal-steel-fretboard__selector-main">12 A\\+F<\\/span>/);
assert.match(html, />\\s*<span class="pedal-steel-fretboard__selector-main">16 A\\+B<\\/span>/);
assert.match(html, /data-selected-position-id="csharp-open-9"/);
assert.match(html, /data-position-detail="csharp-open-9"[^>]*aria-live="polite">/);
assert.match(html, /data-position-detail="csharp-af-12"[^>]*aria-live="polite" hidden>/);
assert.match(html, /data-learning-summary/);
assert.match(html, /Start here/);
assert.match(html, /<strong>Fret 9 · 4-5-6 · open<\\/strong>/);
assert.match(html, /data-chord-tone-chip="4"[^>]*>\\s*<span class="pedal-steel-fretboard__tone-string">S4<\\/span><strong>C#<\\/strong><span class="pedal-steel-fretboard__tone-interval">1<\\/span>/);
assert.match(html, /data-chord-tone-chip="5"[^>]*>\\s*<span class="pedal-steel-fretboard__tone-string">S5<\\/span><strong>G#<\\/strong><span class="pedal-steel-fretboard__tone-interval">5<\\/span>/);
assert.match(html, /<strong>Why this works:<\\/strong> No-pedal C# at fret 9\\./);
assert.match(html, /Compare starter positions/);
assert.equal((html.match(/data-position-compare="/g) || []).length, 9);
assert.match(html, /data-position-compare="csharp-open-9"[^>]*aria-pressed="true"/);
assert.match(html, /data-position-compare="csharp-af-12"[^>]*>\\s*<span class="pedal-steel-fretboard__starter-row-main">Fret 12 · A\\+F<\\/span>/);
assert.match(html, /<strong>Try this next:<\\/strong> Play this 4-5-6 once, block cleanly, then compare the other starter positions\\./);
assert.match(html, /data-explorer-handoff="position" href="\\/ui\\/e9-fretboard-explorer.html\\?mode=single&amp;source=answer&amp;key=Db&amp;fret=9&amp;strings=4-5-6&amp;grip=4-5-6"/);
assert.match(html, />Explore this position<\\/a>/);
assert.match(html, /data-explorer-handoff="compare" href="\\/ui\\/e9-fretboard-explorer.html\\?mode=chord&amp;root=Db&amp;quality=major&amp;source=answer"/);
assert.match(html, />Compare in Explorer<\\/a>/);
const htmlWithoutQuery = fretboard.renderPedalSteelFretboard({ positions: csharpPositions });
assert.match(htmlWithoutQuery, /data-explorer-handoff="position"/);
assert.match(htmlWithoutQuery, /data-explorer-handoff="compare" href="\\/ui\\/e9-fretboard-explorer.html\\?mode=chord&amp;root=Db&amp;quality=major&amp;source=answer"/);
assert.match(htmlWithoutQuery, />Compare in Explorer<\\/a>/);
const labelOnlyHtml = fretboard.renderPedalSteelFretboard({
  positions: [
    { id: "g-open-3", label: "G major", fret: 3, strings: [4, 5, 6], grip: "4-5-6", pedals: [], levers: [] },
    { id: "g-ab-10", label: "G major", fret: 10, strings: [4, 5, 6], grip: "4-5-6", pedals: ["A", "B"], levers: [] }
  ]
});
assert.match(labelOnlyHtml, /data-explorer-handoff="position" href="\\/ui\\/e9-fretboard-explorer.html\\?mode=single&amp;source=answer&amp;fret=3&amp;strings=4-5-6&amp;grip=4-5-6"/);
assert.match(labelOnlyHtml, /data-explorer-handoff="compare" href="\\/ui\\/e9-fretboard-explorer.html\\?mode=chord&amp;root=G&amp;quality=major&amp;source=answer"/);
assert.match(labelOnlyHtml, />Compare in Explorer<\\/a>/);
const singleLabelOnlyHtml = fretboard.renderPedalSteelFretboard({
  positions: [
    { id: "g-single-open-3", label: "G major", fret: 3, strings: [4, 5, 6], grip: "4-5-6", pedals: [], levers: [] }
  ]
});
assert.match(singleLabelOnlyHtml, /data-explorer-handoff="position"/);
assert.match(singleLabelOnlyHtml, /data-explorer-handoff="compare" href="\\/ui\\/e9-fretboard-explorer.html\\?mode=chord&amp;root=G&amp;quality=major&amp;source=answer"/);
assert.match(singleLabelOnlyHtml, />Compare in Explorer<\\/a>/);
assert.match(html, /<span class="pedal-steel-fretboard__detail-label">Fret<\\/span>\\s*<span class="pedal-steel-fretboard__detail-value">9<\\/span>/);
assert.match(html, /<span class="pedal-steel-fretboard__detail-label">Grip<\\/span>\\s*<span class="pedal-steel-fretboard__detail-value">4-5-6<\\/span>/);
assert.doesNotMatch(html, /<span class="pedal-steel-fretboard__detail-label">Pedals<\\/span>\\s*<span class="pedal-steel-fretboard__detail-value">none<\\/span>/);
assert.doesNotMatch(html, /<span class="pedal-steel-fretboard__detail-label">Levers<\\/span>\\s*<span class="pedal-steel-fretboard__detail-value">none<\\/span>/);
assert.match(html, /String 4: C#/);
assert.match(html, /String 5: G#/);
assert.match(html, /String 6: E#/);
assert.match(html, /String 4: 1/);
assert.match(html, /No-pedal C# at fret 9\\./);
assert.doesNotMatch(html, /\\[object Object\\]/);
const nestedHtml = fretboard.renderPedalSteelFretboard({
  positions: [{
    id: "nested-detail",
    label: "Nested detail",
    fret: 3,
    strings: [4, 5, 6],
    grip: "4-5-6",
    notes: {"4": {note: "G", interval: "1"}, "5": {note: "D", interval: "5"}},
    intervals: {"4": {value: "1"}, "5": {value: "5"}},
    explanation: "Nested details should render cleanly."
  }]
});
assert.match(nestedHtml, /String 4: G \\/ 1/);
assert.match(nestedHtml, /String 5: D \\/ 5/);
assert.match(nestedHtml, /data-chord-tone-chip="4"[^>]*>\\s*<span class="pedal-steel-fretboard__tone-string">S4<\\/span><strong>G<\\/strong><span class="pedal-steel-fretboard__tone-interval">1<\\/span>/);
assert.doesNotMatch(nestedHtml, /Compare starter positions/);
assert.doesNotMatch(nestedHtml, /\\[object Object\\]/);
"""
    )

    run_node(script)


def test_csharp_and_b_payloads_render_expected_selector_frets() -> None:
    script = component_eval_script(
        """
const csharpModel = fretboard.buildFretboardModel({
  positions: [
    { id: "csharp-open-9", label: "C# major", fret: 9, strings: [4, 5, 6], grip: "4-5-6", pedals: [], levers: [] },
    { id: "csharp-af-12", label: "C# major", fret: 12, strings: [4, 5, 6], grip: "4-5-6", pedals: ["A"], levers: ["F"] },
    { id: "csharp-ab-16", label: "C# major", fret: 16, strings: [4, 5, 6], grip: "4-5-6", pedals: ["A", "B"], levers: [] }
  ]
});
assert.deepEqual(csharpModel.highlights.map((item) => item.fret), [9, 12, 16]);
const csharpHtml = fretboard.renderPedalSteelFretboard({
  positions: csharpModel.highlights.map((item) => ({
    id: item.id,
    label: item.label,
    fret: item.fret,
    strings: item.strings,
    grip: item.grip,
    pedals: item.pedals,
    levers: item.levers
  }))
});
assert.match(csharpHtml, /9 open/);
assert.match(csharpHtml, /12 A\\+F/);
assert.match(csharpHtml, /16 A\\+B/);

const bModel = fretboard.buildFretboardModel({
  positions: [
    { id: "b-open-7", label: "B major", fret: 7, strings: [4, 5, 6], grip: "4-5-6", pedals: [], levers: [] },
    { id: "b-af-10", label: "B major", fret: 10, strings: [4, 5, 6], grip: "4-5-6", pedals: ["A"], levers: ["F"] },
    { id: "b-ab-14", label: "B major", fret: 14, strings: [4, 5, 6], grip: "4-5-6", pedals: ["A", "B"], levers: [] }
  ]
});
assert.deepEqual(bModel.highlights.map((item) => item.fret), [7, 10, 14]);
const bHtml = fretboard.renderPedalSteelFretboard({
  positions: bModel.highlights.map((item) => ({
    id: item.id,
    label: item.label,
    fret: item.fret,
    strings: item.strings,
    grip: item.grip,
    pedals: item.pedals,
    levers: item.levers
  }))
});
assert.match(bHtml, /7 open/);
assert.match(bHtml, /10 A\\+F/);
assert.match(bHtml, /14 A\\+B/);
"""
    )

    run_node(script)


def test_b_payload_filters_reveal_hidden_fret_two_alternate_without_object_text() -> None:
    script = component_eval_script(
        """
const bPositions = [
  {
    id: "b-open-7",
    label: "B major",
    fret: 7,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: [],
    levers: [],
    role: "Open position",
    family: "major_triad",
    tier: "beginner",
    colorRole: "primary",
    visibleByDefault: true,
    sortOrder: 10,
    notes: {"4": "B", "5": "F#", "6": "D#"},
    intervals: {"4": "1", "5": "5", "6": "3"},
    explanation: "No-pedal B at fret 7."
  },
  {
    id: "b-af-10",
    label: "B major",
    fret: 10,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: ["A"],
    levers: ["F"],
    role: "A+F position",
    family: "major_triad",
    tier: "beginner",
    colorRole: "secondary",
    visibleByDefault: true,
    sortOrder: 20,
    notes: {"4": {note: "D#", interval: "3"}, "5": {note: "B", interval: "1"}, "6": {note: "F#", interval: "5"}},
    intervals: {"4": {value: "3"}, "5": {value: "1"}, "6": {value: "5"}},
    explanation: "A+F B at fret 10."
  },
  {
    id: "b-ab-14",
    label: "B major",
    fret: 14,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: ["A", "B"],
    levers: [],
    role: "A+B position",
    family: "major_triad",
    tier: "beginner",
    colorRole: "alternate",
    visibleByDefault: true,
    sortOrder: 30,
    notes: {"4": "D#", "5": "B", "6": "F#"},
    intervals: {"4": "3", "5": "1", "6": "5"},
    explanation: "A+B B at fret 14."
  },
  {
    id: "b-ab-2-lower-octave",
    label: "B major",
    fret: 2,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: ["A", "B"],
    levers: [],
    role: "A+B lower-octave alternate",
    family: "major_triad",
    tier: "alternate",
    colorRole: "alternate",
    visibleByDefault: false,
    sortOrder: 40,
    notes: {"4": "D#", "5": "B", "6": "F#"},
    intervals: {"4": "3", "5": "1", "6": "5"},
    explanation: "A+B B at fret 2."
  }
];
const coreModel = fretboard.buildFretboardModel({ positions: bPositions });
assert.deepEqual(coreModel.highlights.map((item) => item.id), ["b-open-7", "b-af-10", "b-ab-14"]);
assert.equal(coreModel.allHighlights.length, 4);
assert.equal(coreModel.allHighlights.find((item) => item.id === "b-ab-2-lower-octave").fret, 2);
assert.equal(coreModel.hasFilters, true);
assert.equal(coreModel.voicingFilter, "recommended");

const allModel = fretboard.buildFretboardModel({ positions: bPositions, voicingFilter: "all" });
assert.deepEqual(allModel.highlights.map((item) => item.id), ["b-open-7", "b-af-10", "b-ab-14", "b-ab-2-lower-octave"]);

const html = fretboard.renderPedalSteelFretboard({
  positions: bPositions,
  legend: [
    { id: "primary", label: "Open/no-pedal position", color: "primary", description: "Straight-bar position." },
    { id: "secondary", label: "A+F position", color: "secondary", description: "A pedal plus F lever." },
    { id: "alternate", label: "A+B position", color: "alternate", description: "A and B pedals together." }
  ]
});
assert.doesNotMatch(html, /data-position-tab="/);
assert.doesNotMatch(html, /pedal-steel-fretboard__tab/);
assert.doesNotMatch(html, /data-include-levers/);
assert.doesNotMatch(html, /Include lever positions/);
assert.doesNotMatch(html, /data-has-tabs=/);
assert.match(html, /data-fretboard-filter-panel/);
assert.match(html, /data-voicing-filter="recommended" aria-pressed="true"/);
assert.match(html, /data-voicing-filter="all"[^>]*>All positions<\\/button>/);
assert.match(html, /data-position-selector="b-ab-2-lower-octave"/);
assert.match(html, /data-position-selector="b-ab-2-lower-octave"[^>]*hidden/);
assert.match(html, /data-highlight-id="b-ab-2-lower-octave"[^>]*data-visible-by-default="false"/);
assert.match(html, /data-highlight-id="b-ab-2-lower-octave"[^>]*hidden/);
assert.match(html, /2 A\\+B/);
assert.doesNotMatch(html, /\\[object Object\\]/);
assert.match(html, /String 4: D# \\/ 3/);
assert.match(html, /String 5: B \\/ 1/);
assert.match(html, /String 6: F# \\/ 5/);
assert.match(html, /data-position-selector="b-open-7"[^>]*data-color-role="open"/);
assert.match(html, /data-position-selector="b-af-10"[^>]*data-color-role="a-f"/);
assert.match(html, /data-position-selector="b-ab-14"[^>]*data-color-role="a-b"/);
assert.match(html, /data-position-selector="b-af-10"[^>]*style="[^"]*--fretboard-swatch: #8fd5ff/);
assert.match(html, /data-position-selector="b-ab-14"[^>]*style="[^"]*--fretboard-swatch: #8de391/);
assert.match(html, /data-position-detail="b-af-10"[^>]*data-color-role="a-f"/);
assert.match(html, /data-highlight-id="b-af-10"[^>]*data-color-role="a-f"/);
assert.match(html, /data-legend-id="secondary" data-color-role="a-f"/);
assert.match(html, /Straight-bar position\\./);
assert.match(html, /A pedal plus F lever\\./);
"""
    )

    run_node(script)


def test_pitch_engine_tabs_render_dominant_partial_rootless_and_linked_colors() -> None:
    script = component_eval_script(
        """
const positions = [
  {
    id: "g-open-3",
    label: "G major",
    fret: 3,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: [],
    levers: [],
    family: "open_no_pedals",
    tier: "beginner",
    positionKind: "starter_position",
    colorRole: "open",
    visibleByDefault: true,
    validationStatus: "pitch_validated",
    intervals: {"4": "1", "5": "5", "6": "3"},
    tierReason: "straight-bar reference",
    whenToUse: "Use as the home-base pocket before reaching for pedals.",
    soundCharacter: "stable major triad",
    forumEvidenceStatus: "deterministic pitch-engine result; forum usage not checked"
  },
  {
    id: "a-v-dominant-3",
    label: "E7 pocket",
    fret: 3,
    strings: [5, 7, 8],
    grip: "5-7-8",
    pedals: [],
    levers: ["E lower"],
    family: "dominant_pocket",
    tier: "common",
    positionKind: "dominant_pocket",
    colorRole: "dominant",
    visibleByDefault: false,
    validationStatus: "pitch_validated",
    notes: {"5": {note: "B", interval: "5"}, "7": {note: "F#", interval: "9"}, "8": {note: "D", interval: "b7"}},
    intervals: {"5": "5", "7": "9", "8": "b7"},
    omittedIntervals: ["1", "3"],
    caveats: [{label: "No root in this grip", detail: {reason: "rootless dominant color"}}],
    tierReason: "resolves to I",
    whenToUse: "Use it before resolving back to the I chord.",
    resolutionUse: "resolves to I",
    forumEvidenceStatus: {status: "not linked", note: "needs SGF evidence"}
  },
  {
    id: "a-v-rootless-5",
    label: "E9 rootless",
    fret: 5,
    strings: [5, 6, 8],
    grip: "5-6-8",
    pedals: ["A"],
    levers: [],
    family: "dominant_rootless_partial",
    tier: "common",
    positionKind: "rootless_partial",
    colorRole: "partial-rootless",
    visibleByDefault: false,
    isPartial: true,
    isRootless: true,
    validationStatus: "pitch_validated",
    omittedIntervals: ["1"],
    explanation: {summary: "Useful passing dominant color", context: {resolution: "A"}},
    tierReason: {summary: "partial E-lower color"},
    whenToUse: "Use as a passing dominant color when the band covers the root.",
    explanationShort: "partial E-lower color",
    explanationLong: {summary: "Works as a compact color grip", movement: {to: "A"}},
    forumEvidenceStatus: "not yet linked"
  },
  {
    id: "advanced-e-lower-10",
    label: "E-lower color",
    fret: 10,
    strings: [5, 7, 8],
    grip: "5-7-8",
    pedals: [],
    levers: ["E lower"],
    family: "e_lower_578",
    tier: "advanced",
    positionKind: "advanced_reference",
    colorRole: "e-lower",
    visibleByDefault: false,
    validationStatus: "pitch_validated",
    tierReason: "partial E-lower color",
    whenToUse: "Use when you want a thinner color tone instead of a full grip.",
    soundCharacter: "tense E-lower color",
    forumEvidenceStatus: "computed only"
  }
];
const defaultModel = fretboard.buildFretboardModel({ positions });
assert.deepEqual(defaultModel.highlights.map((item) => item.id), ["g-open-3"]);
assert.equal(defaultModel.voicingFilter, "recommended");

const grip578Model = fretboard.buildFretboardModel({ positions, voicingFilter: "all", gripFilter: "5-7-8" });
assert.deepEqual(grip578Model.highlights.map((item) => item.id), ["a-v-dominant-3", "advanced-e-lower-10"]);
assert.deepEqual(grip578Model.highlights.map((item) => item.colorRole), ["dominant", "e-lower"]);

const grip568Model = fretboard.buildFretboardModel({ positions, voicingFilter: "all", gripFilter: "5-6-8" });
assert.deepEqual(grip568Model.highlights.map((item) => item.id), ["a-v-rootless-5"]);
assert.equal(grip568Model.highlights[0].colorRole, "partial-rootless");

const html = fretboard.renderPedalSteelFretboard({ positions });
assert.doesNotMatch(html, /data-position-tab="/);
assert.match(html, /data-voicing-filter="recommended" aria-pressed="true"/);
assert.match(html, /Dominant pockets/);
assert.match(html, /data-voicing-filter="all"[^>]*>All positions<\\/button>/);
assert.match(html, /data-grip-filter="5-7-8"/);
assert.match(html, /data-grip-filter="5-6-8"/);
assert.match(html, /data-position-selector="a-v-dominant-3"[^>]*data-color-role="dominant"[^>]*hidden/);
assert.match(html, /data-position-detail="a-v-dominant-3"[^>]*data-color-role="dominant"/);
assert.match(html, /data-highlight-id="a-v-dominant-3"[^>]*data-color-role="dominant"[^>]*hidden/);
assert.match(html, /data-position-selector="a-v-rootless-5"[^>]*data-color-role="partial-rootless"[^>]*hidden/);
assert.match(html, /data-position-detail="a-v-rootless-5"[^>]*data-color-role="partial-rootless"/);
assert.match(html, /data-highlight-id="a-v-rootless-5"[^>]*data-color-role="partial-rootless"[^>]*hidden/);
assert.match(html, /data-position-selector="advanced-e-lower-10"[^>]*data-color-role="e-lower"[^>]*hidden/);
assert.match(html, /Technical details/);
assert.match(html, /Position kind/);
assert.match(html, /Validation status/);
assert.match(html, /Omitted intervals/);
assert.match(html, /Why classified/);
assert.match(html, /When to use/);
assert.match(html, /What is omitted/);
assert.match(html, /Forum usage evidence/);
assert.match(html, /Sound character/);
assert.match(html, /Resolution use/);
assert.match(html, /Extended explanation/);
assert.match(html, /starter: straight-bar reference/);
assert.match(html, /dominant pocket: resolves to I/);
assert.match(html, /advanced: partial E-lower color/);
assert.match(html, /Use as the home-base pocket before reaching for pedals\\./);
assert.match(html, /needs SGF evidence \\/ status: not linked/);
assert.match(html, /Works as a compact color grip \\/ movement: to: A/);
assert.match(html, /partial · rootless/);
assert.match(html, /pitch_validated/);
assert.match(html, /No root in this grip \\/ detail: reason: rootless dominant color/);
assert.match(html, /Short explanation/);
assert.match(html, /partial E-lower color/);
assert.doesNotMatch(html, /\\[object Object\\]/);
"""
    )

    run_node(script)


def test_five_eight_branch_internal_label_is_hidden_from_fretboard_cards() -> None:
    script = component_eval_script(
        """
const positions = [{
  id: "g-five-eight-branch-6",
  label: "G on strings 5-8",
  fret: 6,
  strings: [5, 8],
  grip: "5-8",
  pedals: ["A"],
  levers: ["E-raise"],
  notes: ["G", "B"],
  intervals: ["1", "3"],
  tier: "advanced",
  tierReason: "five_eight_branch",
  positionKind: "five_eight_branch",
  visibleByDefault: true,
  colorRole: "alternate"
}];
const html = fretboard.renderPedalSteelFretboard({ positions });
assert.match(html, /5&amp;8 branch/);
assert.match(html, /advanced: 5&amp;8 branch/);
assert.doesNotMatch(html, /five_eight_branch/);
assert.doesNotMatch(html, />[^<]*five_eight_branch[^<]*</);
"""
    )

    run_node(script)


def test_advanced_filter_and_safe_nested_values_render_without_object_text() -> None:
    script = component_eval_script(
        """
const positions = [
  {
    id: "starter-open",
    label: "Starter",
    fret: 7,
    strings: [4, 5, 6],
    grip: "4-5-6",
    tier: "beginner",
    visibleByDefault: true,
    colorRole: "primary",
    pedals: [],
    levers: []
  },
  {
    id: "advanced-pass",
    label: "Advanced",
    fret: 19,
    strings: [4, 5, 6],
    grip: "4-5-6",
    tier: "advanced",
    visibleByDefault: false,
    colorRole: "warning",
    pedals: ["A", "B"],
    levers: ["E lower"],
    notes: { "4": { note: "D#", confidence: { level: "draft" } } },
    intervals: { "4": { value: "3", source: { type: "computed" } } },
    caveats: [{ label: "Watch intonation", detail: { reason: "high fret" } }],
    explanation: { summary: "Use sparingly", context: { lane: "advanced" } }
  }
];
const defaultModel = fretboard.buildFretboardModel({ positions });
assert.deepEqual(defaultModel.highlights.map((item) => item.id), ["starter-open"]);
const allModel = fretboard.buildFretboardModel({ positions, voicingFilter: "all" });
assert.deepEqual(allModel.highlights.map((item) => item.id), ["starter-open", "advanced-pass"]);
const html = fretboard.renderPedalSteelFretboard({ positions });
assert.match(html, /data-position-selector="advanced-pass"[^>]*data-position-tier="advanced"[^>]*data-visible-by-default="false"[^>]*data-has-levers="true"/);
assert.match(html, /data-position-selector="advanced-pass"[^>]*hidden/);
assert.match(html, /data-color-role="e-lower"/);
assert.match(html, /#c7a5ff/);
assert.match(html, /String 4: D# \\/ confidence: level: draft/);
assert.match(html, /Use sparingly \\/ context: lane: advanced/);
assert.match(html, /Watch intonation \\/ detail: reason: high fret/);
assert.doesNotMatch(html, /\\[object Object\\]/);
"""
    )

    run_node(script)


def test_filter_interaction_source_resets_hidden_selection_to_first_visible() -> None:
    source = (REPO_ROOT / COMPONENT).read_text(encoding="utf-8")

    assert "function updatePositionFilter(figure, changedVoicingFilter, changedGripFilter, changedPedalLeverFilter)" in source
    assert "function setPositionElementFilterVisibility(element, isVisible)" in source
    assert "function syncPositionElementVisibility(figure, visibleIds)" in source
    assert 'figure.querySelectorAll("[data-position-selector]").forEach((selector)' in source
    assert 'figure.querySelectorAll("[data-position-detail]").forEach((detail)' in source
    assert 'figure.querySelectorAll(".pedal-steel-fretboard__highlight").forEach((highlight)' in source
    assert 'figure.querySelectorAll("[data-legend-id]").forEach((legend)' in source
    assert 'element.style.display = isVisible ? "" : "none";' in source
    assert "const visibleIds = new Set();" in source
    assert "visibleIds.add(item.getAttribute(\"data-position-selector\"));" in source
    assert "syncPositionElementVisibility(figure, visibleIds);" in source
    assert 'if (changedVoicingFilter === "all" && !changedGripFilter)' in source
    assert 'updateSelectedGripFilterButtons(figure, "all");' in source
    assert 'const firstVisible = figure.querySelector("[data-position-selector]:not([hidden])");' in source
    assert "selectPosition(figure, firstVisible.getAttribute(\"data-position-selector\"));" in source
    assert "if (selector?.hidden) return;" in source
    assert ".pedal-steel-fretboard__selector[hidden]" in (REPO_ROOT / STYLES).read_text(encoding="utf-8")
    assert "data-position-empty" in source
    assert "function positionElementMatchesTab(element, tabMode)" not in source
    assert "function positionElementMatchesVoicing(element, voicingFilter)" in source
    assert "function positionElementMatchesGrip(element, gripFilter)" in source
    assert "function positionElementMatchesPedalLever(element, pedalLeverFilters)" in source
    assert "function readActiveGripFilters(figure)" in source
    assert "function readActivePedalLeverFilters(figure)" in source
    assert "function updateSelectedGripFilterButtons(figure, changedGripFilter)" in source
    assert "function updateSelectedPedalLeverFilterButtons(figure, changedPedalLeverFilter)" in source
    assert 'if (changedGripFilter === "all")' in source
    assert 'if (changedPedalLeverFilter === "all")' in source
    assert "const nextSelected = !changedButton.classList.contains(\"is-selected\");" in source
    assert "const hasSelectedGrip = gripButtons.some((button) => button.classList.contains(\"is-selected\"));" in source
    assert "const hasSelectedPedalLever = pedalLeverButtons.some((button) => button.classList.contains(\"is-selected\"));" in source
    assert "figure.dataset.activeGripFilters = gripFilters.join(\",\");" in source
    assert "figure.dataset.activePedalLeverFilters = pedalLeverFilters.join(\",\");" in source
    assert 'voicingFilter === "recommended"' in source
    assert 'data-visible-by-default") === "true"' in source
    assert 'voicingFilter === "starter"' in source
    assert 'data-is-starter") === "true"' in source
    assert 'voicingFilter === "full-chord"' in source
    assert 'data-is-full-chord") === "true"' in source
    assert 'voicingFilter === "dominant"' in source
    assert 'data-is-dominant") === "true"' in source
    assert 'data-is-starter="${isStarterPosition(highlight) ? "true" : "false"}"' in source
    assert 'data-is-full-chord="${isFullChordPosition(highlight) ? "true" : "false"}"' in source
    assert "No positions match these filters. Try All grips, All pedals/levers, or All positions." in source
    assert "data-position-tab" not in source
    assert "data-include-levers" not in source
    assert "Include lever positions" not in source


def test_direct_diagnostic_payload_hides_tabs_but_keeps_focused_position_visible() -> None:
    script = component_eval_script(
        """
const positions = [
  {
    id: "d-e-lower-578-3",
    label: "D E-lower grip",
    fret: 3,
    strings: [5, 7, 8],
    grip: "5-7-8",
    pedals: [],
    levers: ["E lower"],
    family: "e_lower_578",
    tier: "advanced",
    positionKind: "grip_diagnostic",
    colorRole: "e-lower",
    visibleByDefault: false,
    validationStatus: "pitch_validated",
    notes: {"5": "B", "7": "F#", "8": "D"},
    intervals: {"5": "6/13", "7": "3", "8": "1"},
    omittedIntervals: ["5"],
    caveats: [{label: "Not a full triad", detail: {reason: "fifth omitted"}}],
    explanation: {summary: "This is a D color with E lowered at fret 3."}
  }
];
const model = fretboard.buildFretboardModel({ positions });
assert.equal(model.hasFilters, false);
assert.equal(model.tabMode, "all");
assert.deepEqual(model.highlights.map((item) => item.id), ["d-e-lower-578-3"]);
assert.equal(model.highlights[0].colorRole, "e-lower");

const html = fretboard.renderPedalSteelFretboard({ positions });
assert.doesNotMatch(html, /data-has-tabs=/);
assert.doesNotMatch(html, /data-position-tab="/);
assert.doesNotMatch(html, /Starter/);
assert.doesNotMatch(html, /Dominant pockets/);
assert.match(html, /data-position-selector="d-e-lower-578-3"/);
assert.doesNotMatch(html, /data-position-selector="d-e-lower-578-3"[^>]*hidden/);
assert.match(html, /data-highlight-id="d-e-lower-578-3"[^>]*data-color-role="e-lower"/);
assert.doesNotMatch(html, /data-highlight-id="d-e-lower-578-3"[^>]*hidden/);
assert.match(html, /data-position-detail="d-e-lower-578-3"[^>]*data-color-role="e-lower"/);
assert.match(html, /#c7a5ff/);
assert.match(html, /String 5: B/);
assert.match(html, /String 7: F#/);
assert.match(html, /String 8: D/);
assert.match(html, /String 5: 6\\/13/);
assert.match(html, /Omitted intervals/);
assert.match(html, /5/);
assert.match(html, /Not a full triad \\/ detail: reason: fifth omitted/);
assert.doesNotMatch(html, /\\[object Object\\]/);
"""
    )

    run_node(script)


def test_explorer_payload_uses_key_aware_display_fields_for_learner_text() -> None:
    script = component_eval_script(
        """
const explorerPositions = [
  {
    id: "g-natural-minor-core-456",
    key: "G",
    scale_type: "natural_minor",
    harmony_type: "three_string_diatonic",
    scale_degree: 3,
    chord_function: "III",
    chord_name: "Bb",
    chord_quality: "major",
    fret: 6,
    string_group: "4-5-6",
    strings: [4, 5, 6],
    notes: {"4": "A#", "5": "F", "6": "D"},
    display_notes: {"4": "Bb", "5": "F", "6": "D"},
    intervals: {"4": "1", "5": "5", "6": "3"},
    top_voice: {"string": 4, "note": "A#", "interval": "1"},
    display_top_voice: {"string": 4, "note": "Bb", "interval": "1"},
    display_summary: "Bb on strings 4-5-6 at fret 6: Bb, F, D.",
    position_family: "no_pedals_no_levers",
    difficulty_tier: "starter",
    pitch_validated: true
  },
  {
    id: "g-natural-minor-e-lower-578",
    key: "G",
    scale_type: "natural_minor",
    harmony_type: "advanced_pocket",
    scale_degree: 6,
    chord_function: "VI",
    chord_name: "Eb",
    chord_quality: "major",
    fret: 11,
    string_group: "5-7-8",
    strings: [5, 7, 8],
    levers: ["E-lower"],
    notes: {"5": "A#", "7": "F", "8": "D#"},
    display_notes: {"5": "Bb", "7": "F", "8": "Eb"},
    intervals: {"5": "5", "7": "2/9", "8": "1"},
    top_voice: {"string": 5, "note": "A#", "interval": "5"},
    display_top_voice: {"string": 5, "note": "Bb", "interval": "5"},
    display_summary: "Eb on strings 5-7-8 at fret 11: Bb, F, Eb.",
    position_family: "e_lower_pocket",
    difficulty_tier: "advanced",
    per_string_changes: {"8": {"from": "E", "to": "Eb/D#", "controls": "E-lower"}},
    warnings: ["This is an advanced E-lower pocket; check the missing chord tones before treating it as a full grip."],
    omitted_intervals: ["3"],
    pitch_validated: true
  }
];
const query = {
  key: "G",
  display_scale_notes: {
    major: ["G", "A", "B", "C", "D", "E", "F#"],
    natural_minor: ["G", "A", "Bb", "C", "D", "Eb", "F"]
  }
};

const model = fretboard.buildFretboardModel({ positions: explorerPositions, query, voicingFilter: "all" });
assert.equal(model.displayScaleNotes.find((item) => item.scaleType === "natural minor").notes.join(" "), "G A Bb C D Eb F");
assert.equal(model.allHighlights.find((item) => item.id === "g-natural-minor-core-456").notes.join("; "), "String 4: Bb; String 5: F; String 6: D");
assert.equal(model.allHighlights.find((item) => item.id === "g-natural-minor-core-456").topVoice, "Bb / 1 / string: 4");
assert.equal(model.allHighlights.find((item) => item.id === "g-natural-minor-core-456").displaySummary, "Bb on strings 4-5-6 at fret 6: Bb, F, D.");
assert.equal(model.allHighlights.find((item) => item.id === "g-natural-minor-e-lower-578").grip, "5-7-8");
assert.equal(model.allHighlights.find((item) => item.id === "g-natural-minor-e-lower-578").tier, "advanced");
assert.equal(model.allHighlights.find((item) => item.id === "g-natural-minor-e-lower-578").colorRole, "partial-rootless");
assert.equal(JSON.stringify(model.gripOptions), JSON.stringify(["4-5-6", "5-7-8"]));

const html = fretboard.renderPedalSteelFretboard({ positions: explorerPositions, query, voicingFilter: "all" });
assert.match(html, /natural minor<\\/span>: G A Bb C D Eb F/);
assert.doesNotMatch(html, /G A A# C D D# F/);
assert.match(html, /String 4: Bb/);
assert.match(html, /String 5: Bb/);
assert.match(html, /String 8: Eb/);
assert.doesNotMatch(html, /String 4: A#/);
assert.doesNotMatch(html, /String 5: A#/);
assert.doesNotMatch(html, /String 8: D#/);
assert.match(html, /Top voice/);
assert.match(html, /Bb \\/ 1 \\/ string: 4/);
assert.match(html, /Bb \\/ 5 \\/ string: 5/);
assert.doesNotMatch(html, /A# \\/ 1 \\/ string: 4/);
assert.match(html, /Bb on strings 4-5-6 at fret 6: Bb, F, D\\./);
assert.match(html, /Eb on strings 5-7-8 at fret 11: Bb, F, Eb\\./);
assert.match(html, /String changes/);
assert.match(html, /String 8: controls: E-lower \\/ from: E \\/ to: Eb\\/D#/);
assert.match(html, /Warnings/);
assert.match(html, /advanced E-lower pocket/);
assert.match(html, /data-position-selector="g-natural-minor-core-456"[^>]*data-position-family="no_pedals_no_levers"[^>]*data-position-tier="starter"/);
assert.match(html, /data-position-selector="g-natural-minor-e-lower-578"[^>]*data-position-family="e_lower_pocket"[^>]*data-position-tier="advanced"[^>]*data-position-grip="5-7-8"/);
assert.match(html, /data-position-selector="g-natural-minor-e-lower-578"[^>]*data-color-role="partial-rootless"/);
assert.doesNotMatch(html, /RAG generated/);
assert.doesNotMatch(html, /\\[object Object\\]/);
"""
    )

    run_node(script)


def test_missing_or_partial_fretboard_payload_omits_selector_cleanly() -> None:
    script = component_eval_script(
        """
const emptyHtml = fretboard.renderPedalSteelFretboard({ positions: [] });
assert.doesNotMatch(emptyHtml, /data-position-selector="/);
assert.doesNotMatch(emptyHtml, /data-position-detail="/);

const partialHtml = fretboard.renderPedalSteelFretboard({
  positions: [
    { id: "missing-strings", label: "Missing strings", fret: 4 },
    { id: "bad-strings", label: "Bad strings", fret: 5, strings: [99] }
  ]
});
assert.doesNotMatch(partialHtml, /data-position-selector="/);
assert.doesNotMatch(partialHtml, /missing-strings/);
assert.doesNotMatch(partialHtml, /bad-strings/);
"""
    )

    run_node(script)


def test_voicing_type_and_grip_filters_render_only_when_payload_supports_them() -> None:
    script = component_eval_script(
        """
const positions = [
  {
    id: "c-root-8",
    label: "C major",
    fret: 8,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: [],
    levers: [],
    tier: "beginner",
    visibleByDefault: true,
    voicingType: "root_position",
    isRootPosition: true,
    notes: {"4": "C", "5": "G", "6": "E"}
  },
  {
    id: "c-first-11",
    label: "C major",
    fret: 11,
    strings: [3, 4, 5],
    grip: "3-4-5",
    pedals: ["A"],
    levers: ["F"],
    tier: "beginner",
    visibleByDefault: true,
    voicingType: "first_inversion",
    isInversion: true,
    inversionLabel: "1st inversion",
    notes: {"3": "E", "4": "C", "5": "G"}
  },
  {
    id: "c-second-15",
    label: "C major",
    fret: 15,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: ["A", "B"],
    levers: [],
    tier: "beginner",
    visibleByDefault: true,
    voicingType: "second_inversion",
    isInversion: true,
    inversionLabel: "2nd inversion",
    notes: {"4": "E", "5": "C", "6": "G"}
  },
  {
    id: "c-rootless-5",
    label: "C rootless",
    fret: 5,
    strings: [5, 7, 8],
    grip: "5-7-8",
    pedals: ["A"],
    levers: ["E lower"],
    tier: "beginner",
    visibleByDefault: true,
    voicingType: "rootless",
    isRootless: true,
    isPartialVoicing: true,
    omittedIntervals: ["1"],
    notes: {"5": "E", "7": "D", "8": "Bb"}
  }
];

const rootModel = fretboard.buildFretboardModel({ positions, voicingFilter: "root-position" });
assert.deepEqual(rootModel.highlights.map((item) => item.id), ["c-root-8"]);

const inversionModel = fretboard.buildFretboardModel({ positions, voicingFilter: "inversions" });
assert.deepEqual(inversionModel.highlights.map((item) => item.id), ["c-first-11", "c-second-15"]);

const partialModel = fretboard.buildFretboardModel({ positions, voicingFilter: "partial-rootless" });
assert.deepEqual(partialModel.highlights.map((item) => item.id), ["c-rootless-5"]);

const gripModel = fretboard.buildFretboardModel({ positions, gripFilter: "3-4-5" });
assert.deepEqual(gripModel.highlights.map((item) => item.id), ["c-first-11"]);
assert.equal(gripModel.selectedPositionId, "c-first-11");

const recommendedModel = fretboard.buildFretboardModel({ positions });
assert.equal(recommendedModel.voicingFilter, "recommended");
assert.ok(recommendedModel.highlights.length > 0);
assert.deepEqual(recommendedModel.highlights.map((item) => item.id), ["c-root-8", "c-first-11", "c-second-15", "c-rootless-5"]);

const starterModel = fretboard.buildFretboardModel({ positions, voicingFilter: "starter" });
assert.deepEqual(starterModel.highlights.map((item) => item.id), ["c-root-8", "c-first-11", "c-second-15", "c-rootless-5"]);

const fullChordModel = fretboard.buildFretboardModel({ positions, voicingFilter: "full-chord" });
assert.deepEqual(fullChordModel.highlights.map((item) => item.id), ["c-root-8", "c-first-11", "c-second-15"]);

const fullChordGripModel = fretboard.buildFretboardModel({ positions, voicingFilter: "full-chord", gripFilter: "4-5-6" });
assert.deepEqual(fullChordGripModel.highlights.map((item) => item.id), ["c-root-8", "c-second-15"]);

const noPedalModel = fretboard.buildFretboardModel({ positions, pedalLeverFilter: "none" });
assert.deepEqual(noPedalModel.highlights.map((item) => item.id), ["c-root-8"]);

const afModel = fretboard.buildFretboardModel({ positions, pedalLeverFilter: "a+f" });
assert.deepEqual(afModel.highlights.map((item) => item.id), ["c-first-11"]);

const abModel = fretboard.buildFretboardModel({ positions, pedalLeverFilter: "a+b" });
assert.deepEqual(abModel.highlights.map((item) => item.id), ["c-second-15"]);

const eLowerModel = fretboard.buildFretboardModel({ positions, pedalLeverFilter: "a+e-lower" });
assert.deepEqual(eLowerModel.highlights.map((item) => item.id), ["c-rootless-5"]);

const gripAndPedalModel = fretboard.buildFretboardModel({ positions, gripFilter: "4-5-6", pedalLeverFilter: "a+b" });
assert.deepEqual(gripAndPedalModel.highlights.map((item) => item.id), ["c-second-15"]);

const voicingGripAndPedalModel = fretboard.buildFretboardModel({ positions, voicingFilter: "full-chord", gripFilter: "4-5-6", pedalLeverFilter: "a+b" });
assert.deepEqual(voicingGripAndPedalModel.highlights.map((item) => item.id), ["c-second-15"]);

const noMatchModel = fretboard.buildFretboardModel({ positions, voicingFilter: "root-position", gripFilter: "3-4-5" });
assert.deepEqual(noMatchModel.highlights.map((item) => item.id), []);
assert.equal(noMatchModel.selectedPositionId, "");

const html = fretboard.renderPedalSteelFretboard({ positions });
assert.match(html, /data-fretboard-filter-panel/);
assert.match(html, /data-voicing-filter="recommended" aria-pressed="true"/);
assert.match(html, /data-voicing-filter="all"[^>]*>All positions<\\/button>/);
assert.match(html, /data-voicing-filter="starter"/);
assert.match(html, /data-voicing-filter="full-chord"/);
assert.match(html, /data-voicing-filter="root-position"/);
assert.match(html, /data-voicing-filter="inversions"/);
assert.match(html, /data-voicing-filter="partial-rootless"/);
assert.match(html, /data-grip-filter="all"/);
assert.match(html, /data-grip-filter="3-4-5"/);
assert.match(html, /data-grip-filter="4-5-6"/);
assert.match(html, /data-grip-filter="5-7-8"/);
assert.match(html, /data-has-pedal-lever-filters="true"/);
assert.match(html, /data-pedal-lever-filter="all" aria-pressed="true"/);
assert.match(html, /data-pedal-lever-filter="none"/);
assert.match(html, /data-pedal-lever-filter="a\\+b"/);
assert.match(html, /data-pedal-lever-filter="a\\+f"/);
assert.match(html, /data-pedal-lever-filter="a\\+e-lower"/);
assert.match(html, />No pedals\\/levers<\\/button>/);
assert.match(html, />A\\+B<\\/button>/);
assert.match(html, />A\\+F<\\/button>/);
assert.match(html, /data-position-selector="c-root-8"[^>]*data-voicing-category="root-position"[^>]*data-is-starter="true"[^>]*data-is-full-chord="true"/);
assert.match(html, /data-position-selector="c-first-11"[^>]*data-voicing-category="inversions"[^>]*data-is-starter="true"[^>]*data-is-full-chord="true"/);
assert.match(html, /data-position-selector="c-rootless-5"[^>]*data-voicing-category="partial-rootless"[^>]*data-is-starter="true"[^>]*data-is-full-chord="false"/);
assert.match(html, /data-position-selector="c-root-8"[^>]*data-position-pedal-lever-key="none"[^>]*data-filter-visible="true"/);
assert.match(html, /data-position-selector="c-first-11"[^>]*data-position-pedal-lever-key="a\\+f"[^>]*data-filter-visible="true"/);
assert.match(html, /data-position-selector="c-second-15"[^>]*data-position-pedal-lever-key="a\\+b"[^>]*data-filter-visible="true"/);
assert.match(html, /data-position-selector="c-rootless-5"[^>]*data-position-pedal-lever-key="a\\+e-lower"[^>]*data-filter-visible="true"/);
assert.match(html, /data-highlight-id="c-first-11"[^>]*data-position-grip="3-4-5"/);
assert.match(html, /Root position: root in the bass/);
assert.match(html, /1st inversion: 3rd in the bass/);
assert.match(html, /2nd inversion: 5th in the bass/);
assert.match(html, /Rootless: root is omitted/);
assert.doesNotMatch(html, /\\[object Object\\]/);

const gripFilteredHtml = fretboard.renderPedalSteelFretboard({ positions, gripFilter: "4-5-6" });
assert.match(gripFilteredHtml, /data-grip-filter="4-5-6" aria-pressed="true"/);
assert.match(gripFilteredHtml, /data-position-selector="c-root-8"/);
assert.match(gripFilteredHtml, /data-position-selector="c-second-15"/);
assert.match(gripFilteredHtml, /data-position-selector="c-first-11"[^>]*hidden/);
assert.match(gripFilteredHtml, /data-position-selector="c-rootless-5"[^>]*hidden/);
assert.match(gripFilteredHtml, /data-position-detail="c-first-11"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(gripFilteredHtml, /data-highlight-id="c-first-11"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(gripFilteredHtml, /data-highlight-id="c-rootless-5"[^>]*data-filter-visible="false"[^>]*hidden/);

const combinedFilteredHtml = fretboard.renderPedalSteelFretboard({
  positions,
  voicingFilter: "inversions",
  gripFilter: "4-5-6"
});
assert.match(combinedFilteredHtml, /data-voicing-filter="inversions" aria-pressed="true"/);
assert.match(combinedFilteredHtml, /data-grip-filter="4-5-6" aria-pressed="true"/);
assert.match(combinedFilteredHtml, /data-position-selector="c-second-15"/);
assert.doesNotMatch(combinedFilteredHtml, /data-position-selector="c-second-15"[^>]*hidden/);
assert.match(combinedFilteredHtml, /data-position-selector="c-root-8"[^>]*hidden/);
assert.match(combinedFilteredHtml, /data-position-selector="c-first-11"[^>]*hidden/);
assert.match(combinedFilteredHtml, /data-position-selector="c-rootless-5"[^>]*hidden/);
assert.match(combinedFilteredHtml, /data-highlight-id="c-second-15"[^>]*data-filter-visible="true"/);
assert.match(combinedFilteredHtml, /data-highlight-id="c-root-8"[^>]*data-filter-visible="false"[^>]*hidden/);

const fullChordGripHtml = fretboard.renderPedalSteelFretboard({
  positions,
  voicingFilter: "full-chord",
  gripFilter: "4-5-6"
});
assert.match(fullChordGripHtml, /data-voicing-filter="full-chord" aria-pressed="true"/);
assert.match(fullChordGripHtml, /data-grip-filter="4-5-6" aria-pressed="true"/);
assert.match(fullChordGripHtml, /data-position-selector="c-root-8"/);
assert.doesNotMatch(fullChordGripHtml, /data-position-selector="c-root-8"[^>]*hidden/);
assert.match(fullChordGripHtml, /data-position-selector="c-second-15"/);
assert.doesNotMatch(fullChordGripHtml, /data-position-selector="c-second-15"[^>]*hidden/);
assert.match(fullChordGripHtml, /data-position-selector="c-first-11"[^>]*hidden/);
assert.match(fullChordGripHtml, /data-position-selector="c-rootless-5"[^>]*hidden/);
assert.match(fullChordGripHtml, /data-position-detail="c-root-8"[^>]*aria-live="polite"/);

const pedalFilteredHtml = fretboard.renderPedalSteelFretboard({ positions, pedalLeverFilter: "a+b" });
assert.match(pedalFilteredHtml, /data-active-pedal-lever-filters="a\\+b"/);
assert.match(pedalFilteredHtml, /data-pedal-lever-filter="a\\+b" aria-pressed="true"/);
assert.match(pedalFilteredHtml, /data-position-selector="c-second-15"[^>]*data-filter-visible="true"/);
assert.doesNotMatch(pedalFilteredHtml, /data-position-selector="c-second-15"[^>]*hidden/);
assert.match(pedalFilteredHtml, /data-position-selector="c-root-8"[^>]*data-filter-visible="false"[^>]*style="[^"]*display: none;[^"]*"[^>]*hidden/);
assert.match(pedalFilteredHtml, /data-position-selector="c-first-11"[^>]*data-filter-visible="false"[^>]*style="[^"]*display: none;[^"]*"[^>]*hidden/);
assert.match(pedalFilteredHtml, /data-position-detail="c-root-8"[^>]*data-filter-visible="false"[^>]*style="[^"]*display: none;[^"]*"[^>]*hidden/);
assert.match(pedalFilteredHtml, /data-highlight-id="c-root-8"[^>]*data-filter-visible="false"[^>]*style="[^"]*display: none;[^"]*"[^>]*hidden/);

const combinedGripPedalHtml = fretboard.renderPedalSteelFretboard({
  positions,
  gripFilter: "4-5-6",
  pedalLeverFilter: "a+b"
});
assert.match(combinedGripPedalHtml, /data-grip-filter="4-5-6" aria-pressed="true"/);
assert.match(combinedGripPedalHtml, /data-pedal-lever-filter="a\\+b" aria-pressed="true"/);
assert.match(combinedGripPedalHtml, /data-position-selector="c-second-15"[^>]*data-filter-visible="true"/);
assert.match(combinedGripPedalHtml, /data-position-selector="c-root-8"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(combinedGripPedalHtml, /data-position-selector="c-first-11"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(combinedGripPedalHtml, /data-position-selector="c-rootless-5"[^>]*data-filter-visible="false"[^>]*hidden/);

const noMatchHtml = fretboard.renderPedalSteelFretboard({
  positions,
  voicingFilter: "root-position",
  gripFilter: "3-4-5"
});
assert.match(noMatchHtml, /data-voicing-filter="root-position" aria-pressed="true"/);
assert.match(noMatchHtml, /data-grip-filter="3-4-5" aria-pressed="true"/);
assert.match(noMatchHtml, /<p class="pedal-steel-fretboard__empty" data-position-empty>No positions match these filters\\. Try All grips, All pedals\\/levers, or All positions\\.<\\/p>/);
assert.match(noMatchHtml, /data-position-detail="c-root-8"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(noMatchHtml, /data-position-detail="c-first-11"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(noMatchHtml, /data-highlight-id="c-root-8"[^>]*data-filter-visible="false"[^>]*hidden/);

const oldPayloadHtml = fretboard.renderPedalSteelFretboard({ positions: fretboard.DEMO_POSITIONS });
assert.doesNotMatch(oldPayloadHtml, /data-fretboard-filter-panel/);
assert.doesNotMatch(oldPayloadHtml, /data-voicing-filter=/);
assert.doesNotMatch(oldPayloadHtml, /data-grip-filter=/);
assert.doesNotMatch(oldPayloadHtml, /data-pedal-lever-filter=/);
"""
    )

    run_node(script)


def test_grip_filters_support_multi_select_and_filter_all_visible_outputs() -> None:
    script = component_eval_script(
        """
const positions = [
  { id: "g-root-345", label: "G root grip", fret: 3, strings: [3, 4, 5], grip: "3-4-5", pedals: [], levers: [], tier: "beginner", visibleByDefault: true, voicingType: "root_position", isRootPosition: true, notes: {"3": "G", "4": "B", "5": "D"} },
  { id: "g-root-456", label: "G root grip", fret: 3, strings: [4, 5, 6], grip: "4-5-6", pedals: [], levers: [], tier: "beginner", visibleByDefault: true, voicingType: "root_position", isRootPosition: true, notes: {"4": "G", "5": "D", "6": "B"} },
  { id: "g-first-345", label: "G first inversion", fret: 6, strings: [3, 4, 5], grip: "3-4-5", pedals: ["A"], levers: ["F"], tier: "beginner", visibleByDefault: true, voicingType: "first_inversion", isInversion: true, notes: {"3": "B", "4": "G", "5": "D"} },
  { id: "g-second-456", label: "G second inversion", fret: 10, strings: [4, 5, 6], grip: "4-5-6", pedals: ["A", "B"], levers: [], tier: "beginner", visibleByDefault: true, voicingType: "second_inversion", isInversion: true, notes: {"4": "B", "5": "G", "6": "D"} },
  { id: "g-elower-578", label: "G E-lower color", fret: 8, strings: [5, 7, 8], grip: "5-7-8", pedals: [], levers: ["E lower"], tier: "advanced", visibleByDefault: false, voicingType: "rootless", isRootless: true, isPartialVoicing: true, omittedIntervals: ["1"], notes: {"5": "D", "7": "A", "8": "F"} }
];

const root345Model = fretboard.buildFretboardModel({ positions, voicingFilter: "root-position", gripFilter: "3-4-5" });
assert.deepEqual(root345Model.highlights.map((item) => item.id), ["g-root-345"]);
assert.equal(root345Model.selectedPositionId, "g-root-345");

const full456Model = fretboard.buildFretboardModel({ positions, voicingFilter: "full-chord", gripFilter: "4-5-6" });
assert.deepEqual(full456Model.highlights.map((item) => item.id), ["g-root-456", "g-second-456"]);
assert.equal(full456Model.selectedPositionId, "g-root-456");

const multiGripModel = fretboard.buildFretboardModel({ positions, voicingFilter: "all", gripFilters: ["3-4-5", "4-5-6"] });
assert.deepEqual(Array.from(multiGripModel.gripFilters), ["3-4-5", "4-5-6"]);
assert.deepEqual(multiGripModel.highlights.map((item) => item.id), ["g-root-345", "g-root-456", "g-first-345", "g-second-456"]);

const afOnlyModel = fretboard.buildFretboardModel({ positions, pedalLeverFilter: "a+f" });
assert.deepEqual(afOnlyModel.highlights.map((item) => item.id), ["g-first-345"]);

const abOnlyModel = fretboard.buildFretboardModel({ positions, pedalLeverFilter: "a+b" });
assert.deepEqual(abOnlyModel.highlights.map((item) => item.id), ["g-second-456"]);

const eLowerOnlyModel = fretboard.buildFretboardModel({ positions, voicingFilter: "all", pedalLeverFilter: "e-lower" });
assert.deepEqual(eLowerOnlyModel.highlights.map((item) => item.id), ["g-elower-578"]);

const noPedalsOnlyModel = fretboard.buildFretboardModel({ positions, pedalLeverFilter: "none" });
assert.deepEqual(noPedalsOnlyModel.highlights.map((item) => item.id), ["g-root-345", "g-root-456"]);

const multiPedalModel = fretboard.buildFretboardModel({ positions, voicingFilter: "all", pedalLeverFilters: ["a+f", "a+b"] });
assert.deepEqual(Array.from(multiPedalModel.pedalLeverFilters), ["a+f", "a+b"]);
assert.deepEqual(multiPedalModel.highlights.map((item) => item.id), ["g-first-345", "g-second-456"]);

const multiGripHtml = fretboard.renderPedalSteelFretboard({ positions, voicingFilter: "all", gripFilters: ["3-4-5", "4-5-6"] });
assert.match(multiGripHtml, /data-active-grip-filters="3-4-5,4-5-6"/);
assert.match(multiGripHtml, /data-grip-filter="all" aria-pressed="false"/);
assert.match(multiGripHtml, /data-grip-filter="3-4-5" aria-pressed="true"/);
assert.match(multiGripHtml, /data-grip-filter="4-5-6" aria-pressed="true"/);
assert.match(multiGripHtml, /data-position-selector="g-root-345"/);
assert.match(multiGripHtml, /data-position-selector="g-root-456"/);
assert.match(multiGripHtml, /data-position-selector="g-first-345"/);
assert.match(multiGripHtml, /data-position-selector="g-second-456"/);
assert.match(multiGripHtml, /data-position-selector="g-elower-578"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(multiGripHtml, /data-position-detail="g-elower-578"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(multiGripHtml, /data-highlight-id="g-elower-578"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(multiGripHtml, /data-pedal-lever-filter="none"[^>]*>No pedals\\/levers<\\/button>/);
assert.match(multiGripHtml, /data-pedal-lever-filter="a\\+b"[^>]*>A\\+B<\\/button>/);
assert.match(multiGripHtml, /data-pedal-lever-filter="a\\+f"[^>]*>A\\+F<\\/button>/);
assert.match(multiGripHtml, /data-pedal-lever-filter="e-lower"[^>]*>E-lower<\\/button>/);

const root345Html = fretboard.renderPedalSteelFretboard({ positions, voicingFilter: "root-position", gripFilter: "3-4-5" });
assert.match(root345Html, /data-position-selector="g-root-345"/);
assert.doesNotMatch(root345Html, /data-position-selector="g-root-345"[^>]*hidden/);
assert.match(root345Html, /data-position-selector="g-root-456"[^>]*hidden/);
assert.match(root345Html, /data-position-selector="g-first-345"[^>]*hidden/);
assert.match(root345Html, /data-position-selector="g-second-456"[^>]*hidden/);
assert.match(root345Html, /data-position-selector="g-elower-578"[^>]*hidden/);
assert.match(root345Html, /data-position-detail="g-root-345"[^>]*aria-live="polite"/);
assert.match(root345Html, /data-position-detail="g-root-456"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(root345Html, /data-position-detail="g-first-345"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(root345Html, /data-position-detail="g-second-456"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(root345Html, /data-position-detail="g-elower-578"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(root345Html, /data-highlight-id="g-root-345"[^>]*data-filter-visible="true"/);
assert.match(root345Html, /data-highlight-id="g-root-456"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(root345Html, /data-highlight-id="g-first-345"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(root345Html, /data-highlight-id="g-second-456"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(root345Html, /data-highlight-id="g-elower-578"[^>]*data-filter-visible="false"[^>]*hidden/);

const grip456Html = fretboard.renderPedalSteelFretboard({ positions, gripFilter: "4-5-6" });
assert.match(grip456Html, /data-grip-filter="4-5-6" aria-pressed="true"/);
assert.match(grip456Html, /data-position-selector="g-root-456"/);
assert.match(grip456Html, /data-position-selector="g-second-456"/);
assert.match(grip456Html, /data-position-selector="g-root-345"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(grip456Html, /data-position-selector="g-first-345"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(grip456Html, /data-position-selector="g-elower-578"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(grip456Html, /data-position-detail="g-root-345"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(grip456Html, /data-highlight-id="g-root-345"[^>]*data-filter-visible="false"[^>]*hidden/);

const pedalFilteredHtml = fretboard.renderPedalSteelFretboard({ positions, pedalLeverFilter: "a+f" });
assert.match(pedalFilteredHtml, /data-active-pedal-lever-filters="a\\+f"/);
assert.match(pedalFilteredHtml, /data-pedal-lever-filter="a\\+f" aria-pressed="true"/);
assert.match(pedalFilteredHtml, /data-position-selector="g-first-345"[^>]*data-position-pedal-lever-key="a\\+f"[^>]*data-filter-visible="true"/);
assert.doesNotMatch(pedalFilteredHtml, /data-position-selector="g-first-345"[^>]*hidden/);
assert.match(pedalFilteredHtml, /data-position-selector="g-root-345"[^>]*data-position-pedal-lever-key="none"[^>]*data-filter-visible="false"[^>]*style="[^"]*display: none;[^"]*"[^>]*hidden/);
assert.match(pedalFilteredHtml, /data-position-selector="g-second-456"[^>]*data-position-pedal-lever-key="a\\+b"[^>]*data-filter-visible="false"[^>]*style="[^"]*display: none;[^"]*"[^>]*hidden/);
assert.match(pedalFilteredHtml, /data-position-detail="g-root-345"[^>]*data-filter-visible="false"[^>]*style="[^"]*display: none;[^"]*"[^>]*hidden/);
assert.match(pedalFilteredHtml, /data-highlight-id="g-root-345"[^>]*data-filter-visible="false"[^>]*style="[^"]*display: none;[^"]*"[^>]*hidden/);

const gripAndPedalHtml = fretboard.renderPedalSteelFretboard({ positions, voicingFilter: "all", gripFilter: "3-4-5", pedalLeverFilter: "a+f" });
assert.match(gripAndPedalHtml, /data-grip-filter="3-4-5" aria-pressed="true"/);
assert.match(gripAndPedalHtml, /data-pedal-lever-filter="a\\+f" aria-pressed="true"/);
assert.match(gripAndPedalHtml, /data-position-selector="g-first-345"[^>]*data-filter-visible="true"/);
assert.match(gripAndPedalHtml, /data-position-selector="g-root-345"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(gripAndPedalHtml, /data-position-selector="g-root-456"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(gripAndPedalHtml, /data-position-selector="g-second-456"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(gripAndPedalHtml, /data-position-selector="g-elower-578"[^>]*data-filter-visible="false"[^>]*hidden/);

const multiPedalHtml = fretboard.renderPedalSteelFretboard({ positions, voicingFilter: "all", pedalLeverFilters: ["a+f", "a+b"] });
assert.match(multiPedalHtml, /data-active-pedal-lever-filters="a\\+f,a\\+b"/);
assert.match(multiPedalHtml, /data-pedal-lever-filter="all" aria-pressed="false"/);
assert.match(multiPedalHtml, /data-pedal-lever-filter="a\\+f" aria-pressed="true"/);
assert.match(multiPedalHtml, /data-pedal-lever-filter="a\\+b" aria-pressed="true"/);
assert.match(multiPedalHtml, /data-position-selector="g-first-345"[^>]*data-filter-visible="true"/);
assert.match(multiPedalHtml, /data-position-selector="g-second-456"[^>]*data-filter-visible="true"/);
assert.match(multiPedalHtml, /data-position-selector="g-root-345"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(multiPedalHtml, /data-position-selector="g-root-456"[^>]*data-filter-visible="false"[^>]*hidden/);

const noMatchHtml = fretboard.renderPedalSteelFretboard({ positions, voicingFilter: "root-position", gripFilter: "5-7-8" });
assert.match(noMatchHtml, /No positions match these filters\\. Try All grips, All pedals\\/levers, or All positions\\./);
assert.match(noMatchHtml, /data-position-detail="g-root-345"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.match(noMatchHtml, /data-highlight-id="g-root-345"[^>]*data-filter-visible="false"[^>]*hidden/);
assert.doesNotMatch(noMatchHtml, /\\[object Object\\]/);
"""
    )

    run_node(script)


def test_large_position_payload_starts_with_recommended_set_and_can_show_all() -> None:
    script = component_eval_script(
        """
const positions = Array.from({ length: 7 }, (_, index) => ({
  id: `g-option-${index + 1}`,
  label: "G major",
  fret: index + 3,
  strings: [4, 5, 6],
  grip: index < 5 ? "4-5-6" : "3-4-5",
  pedals: index % 3 === 0 ? [] : index % 3 === 1 ? ["A"] : ["A", "B"],
  levers: index % 3 === 1 ? ["F"] : [],
  tier: index < 5 ? "starter" : "alternate",
  visibleByDefault: true,
  voicingType: index < 5 ? "root_position" : "first_inversion",
  isRootPosition: index < 5,
  isInversion: index >= 5,
  sortOrder: index + 1
}));

const model = fretboard.buildFretboardModel({ positions });
assert.equal(model.allHighlights.length, 7);
assert.equal(model.highlights.length, 5);
assert.equal(model.hasRecommendedLimit, true);
assert.deepEqual(model.highlights.map((item) => item.id), [
  "g-option-1",
  "g-option-2",
  "g-option-3",
  "g-option-4",
  "g-option-5"
]);
assert.equal(model.recommendedHiddenIds.has("g-option-6"), true);
assert.equal(model.recommendedHiddenIds.has("g-option-7"), true);

const html = fretboard.renderPedalSteelFretboard({ positions });
assert.match(html, /data-recommended-limited="true"/);
assert.match(html, /Showing 5 recommended positions first/);
assert.match(html, /data-show-all-positions/);
assert.match(html, /data-position-selector="g-option-6"[^>]*data-recommended-extra="true"[^>]*hidden/);
assert.match(html, /data-position-selector="g-option-7"[^>]*data-recommended-extra="true"[^>]*hidden/);
assert.match(html, /data-highlight-id="g-option-6"[^>]*data-recommended-extra="true"[^>]*hidden/);
assert.match(html, /data-highlight-id="g-option-7"[^>]*data-recommended-extra="true"[^>]*hidden/);

const inversionModel = fretboard.buildFretboardModel({ positions, voicingFilter: "inversions" });
assert.equal(inversionModel.hasRecommendedLimit, false);
assert.deepEqual(inversionModel.highlights.map((item) => item.id), ["g-option-6", "g-option-7"]);
"""
    )

    run_node(script)


def test_component_can_hide_internal_filters_for_explorer_surface() -> None:
    script = component_eval_script(
        """
const positions = [
  {
    id: "explorer-g-345",
    label: "G major",
    fret: 3,
    strings: [3, 4, 5],
    grip: "3-4-5",
    pedals: [],
    voicingType: "root_position",
    isRootPosition: true
  },
  {
    id: "explorer-g-456",
    label: "G major",
    fret: 3,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: [],
    voicingType: "root_position",
    isRootPosition: true
  }
];

const html = fretboard.renderPedalSteelFretboard({ positions, hideFilterControls: true });
assert.match(html, /data-highlight-id="explorer-g-345"/);
assert.match(html, /data-highlight-id="explorer-g-456"/);
assert.match(html, /data-has-voicing-filters="false"/);
assert.match(html, /data-has-grip-filters="false"/);
assert.doesNotMatch(html, /pedal-steel-fretboard__filters/);
assert.doesNotMatch(html, /\\[object Object\\]/);

const markerOnlyHtml = fretboard.renderPedalSteelFretboard({
  positions,
  hideFilterControls: true,
  showHighlightLabels: false
});
assert.match(markerOnlyHtml, /data-highlight-dot/);
assert.match(markerOnlyHtml, /data-highlight-id="explorer-g-345"/);
assert.doesNotMatch(markerOnlyHtml, /data-highlight-label="explorer-g-345"/);
assert.doesNotMatch(markerOnlyHtml, />G major<\\/text>/);

const multiValueLabelHtml = fretboard.renderPedalSteelFretboard({
  positions: [{
    id: "explorer-multi-label",
    label: "3-, 4",
    labelValues: ["3-", "4", "5"],
    labelOverflowCount: 1,
    fret: 3,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: []
  }],
  hideFilterControls: true
});
assert.match(multiValueLabelHtml, /data-highlight-label-values="3-,4,5"/);
assert.match(multiValueLabelHtml, /data-highlight-label-overflow-count="1"/);
assert.match(multiValueLabelHtml, /<tspan data-highlight-label-main>3-, 4<\\/tspan>/);
assert.match(multiValueLabelHtml, /<tspan data-highlight-label-overflow[^>]*>\\+1<\\/tspan>/);
assert.doesNotMatch(multiValueLabelHtml, />3\\+<\\/text>/);
"""
    )

    run_node(script)


def test_component_escapes_user_supplied_highlight_text() -> None:
    script = component_eval_script(
        r"""
const html = fretboard.renderPedalSteelFretboard({
  highlights: [{
    id: "unsafe",
    label: "<img src=x onerror=alert(1)>",
    fret: 3,
    strings: [4],
    pedals: ["A<bad>"],
    role: "role & detail"
  }]
});
assert.doesNotMatch(html, /<img src=x/);
assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt;/);
assert.match(html, /A&lt;bad&gt;/);
assert.match(html, /role &amp; detail/);
"""
    )

    run_node(script)


def test_component_renders_internal_position_labels_as_readable_text() -> None:
    script = component_eval_script(
        r"""
const html = fretboard.renderPedalSteelFretboard({
  positions: [{
    id: "g-open-3",
    label: "G major",
    fret: 3,
    strings: [4, 5, 6],
    grip: "4-5-6",
    pedals: [],
    levers: [],
    family: "open_no_pedals",
    tier: "beginner",
    role: "starter_home_position",
    positionKind: "full_chord_position",
    visibleByDefault: true
  }]
});
const visibleText = html.replace(/<[^>]+>/g, " ");
assert.match(visibleText, /Full chord position/);
assert.match(visibleText, /Open no pedals/);
assert.doesNotMatch(visibleText, /full_chord_position/);
assert.doesNotMatch(visibleText, /open_no_pedals/);
"""
    )

    run_node(script)


def test_component_honors_caller_grip_contract_and_order() -> None:
    script = component_eval_script(
        r"""
const grips = ["1-4-5", "3-4-5", "4-5-6", "4-5-7", "5-6-8", "5-7-8", "6-8-10", "7-8-10"];
const approvedGrips = ["3-4-5", "4-5-6", "5-6-8", "5-7-8", "6-8-10"];
const positions = grips.map((grip, index) => ({
  id: `position-${index}`,
  label: `Position ${index}`,
  fret: index + 1,
  strings: grip.split("-").map(Number),
  grip,
  pedals: [],
  levers: [],
  family: "open_no_pedals",
  tier: "beginner",
  role: "starter_home_position",
  positionKind: "full_chord_position",
  visibleByDefault: true
}));
const model = fretboard.buildFretboardModel({positions, gripOptions: approvedGrips});
assert.equal(JSON.stringify(model.gripOptions), JSON.stringify(approvedGrips));
const html = fretboard.renderPedalSteelFretboard({positions, gripOptions: approvedGrips});
const renderedGrips = Array.from(html.matchAll(/data-grip-filter="([^"]+)"/g)).map((match) => match[1]);
assert.equal(JSON.stringify(renderedGrips), JSON.stringify(["all", ...approvedGrips]));
assert.doesNotMatch(html, /data-grip-filter="1-4-5"/);
assert.doesNotMatch(html, /data-grip-filter="4-5-7"/);
assert.doesNotMatch(html, /data-grip-filter="7-8-10"/);
"""
    )

    run_node(script)


def test_demo_page_mounts_the_component_without_touching_landing_pages() -> None:
    if not (REPO_ROOT / DEMO).exists():
        return
    html = (REPO_ROOT / DEMO).read_text(encoding="utf-8")

    assert '<script src="pedal-steel-fretboard.js"></script>' in html
    assert "mountPedalSteelFretboard" in html
    assert "DEMO_HIGHLIGHTS" in html
    assert "PedalSteelFretboard" in html
    assert "steel-guitar-rag-landing.html" not in html
    assert "steel-guitar-rag-mock.html" not in html


def test_component_source_contains_no_eyeballed_fret_spacing_formula() -> None:
    source = (REPO_ROOT / COMPONENT).read_text(encoding="utf-8")
    styles = (REPO_ROOT / STYLES).read_text(encoding="utf-8")

    assert 'const DECORATIVE_BACKGROUND_HREF = "/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f";' in source
    assert "Decorative underlay only." in source
    assert ".answer-fretboard-mount" in styles
    assert "grid-template-columns: minmax(0, 1fr);" in styles
    assert "overflow-x: auto;" in styles
    assert "1 - Math.pow(2, -safeFret / 12)" in source
    assert "rawMax" not in source
    assert "safeFret / safeMax" not in source
    assert "fret / maxFret" not in source
    assert "const APPROVED_FRET_24_PICKUP_GAP_PX = 65;" in source
    assert "const PLAYABLE_BRIDGE_X = PLAYABLE_NUT_X + ((PICKUP_START_X - APPROVED_FRET_24_PICKUP_GAP_PX - PLAYABLE_NUT_X) / 0.75);" in source
    assert "const PICKUP_START_X = 1055;" in source
    assert "LAYOUT.nutX + normalizedFretPosition(fret, maxFret) * fretboardWidth" in source
    assert "data-spacing=\"equal-temperament\"" in source
    assert re.search(r"COMMON_FRET_MARKERS\s*=\s*\[3, 5, 7, 9, 12, 15, 17, 19, 21, 24\]", source)


def test_resting_highlight_bubbles_remain_visible_without_flattening_selection_hierarchy() -> None:
    styles = (REPO_ROOT / STYLES).read_text(encoding="utf-8")

    assert re.search(
        r"\.pedal-steel-fretboard__highlight\s*\{\s*opacity:\s*0\.78;",
        styles,
    )
    assert re.search(
        r"\.pedal-steel-fretboard__highlight\.is-emphasized-visible\s*\{\s*opacity:\s*0\.9;",
        styles,
    )
    assert re.search(
        r"\.pedal-steel-fretboard__highlight\.is-selected\s*\{\s*opacity:\s*1;",
        styles,
    )
