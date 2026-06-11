from __future__ import annotations

import math
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPONENT = Path("ui/pedal-steel-fretboard.js")
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

const code = fs.readFileSync("{COMPONENT}", "utf8");
const sandbox = {{ window: {{}} }};
vm.createContext(sandbox);
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
assert.ok(model.fretPositions[1].x - model.fretPositions[0].x > model.fretPositions[24].x - model.fretPositions[23].x);
assert.equal(JSON.stringify(model.markers), JSON.stringify([3, 5, 7, 9, 12, 15, 17, 19, 21, 24]));
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
assert.equal((html.match(/data-fret-marker-style="printed-star"/g) || []).length, 10);
assert.equal((html.match(/data-fret-marker-star="/g) || []).length, 10);
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


def test_printed_fret_markers_are_centered_in_fret_spaces() -> None:
    script = component_eval_script(
        """
const model = fretboard.buildFretboardModel();
const html = fretboard.renderPedalSteelFretboard({ highlights: fretboard.DEMO_HIGHLIGHTS });
const markers = Array.from(html.matchAll(/data-fret-marker-star="(\\d+)" points="([^"]+)"/g));
assert.equal(markers.length, 10);
for (const match of markers) {
  const fret = Number(match[1]);
  const centerX = Number(match[2].split(" ")[0].split(",")[0]);
  const fretX = model.fretPositions[fret].x;
  const nextFretX = model.layout.nutX + fretboard.normalizedFretPosition(fret + 1, fret + 1) * model.layout.scalePx;
  const expectedCenter = (fretX + nextFretX) / 2;
  assert.ok(centerX > fretX, `marker ${fret} should be after its fret line`);
  assert.ok(centerX < nextFretX, `marker ${fret} should be before the next fret line`);
  assert.ok(Math.abs(centerX - expectedCenter) < 0.001);
}
"""
    )

    run_node(script)


def test_rendered_svg_uses_decorative_background_underlay() -> None:
    script = component_eval_script(
        """
const html = fretboard.renderPedalSteelFretboard({ highlights: fretboard.DEMO_HIGHLIGHTS });
const backgroundIndex = html.indexOf('href="/brand/pedal-steel-fretboard-background.svg"');
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
assert.equal((html.match(/href="\\/brand\\/pedal-steel-fretboard-background\\.svg"/g) || []).length, 1);
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
assert.match(html, /intervals 1-3-5/);
assert.match(html, /Open G pocket/);
assert.match(html, /A pedal plus the E raise makes the G pocket at fret 6\\./);
assert.match(html, /Pedals-down G position at fret 10\\./);
assert.doesNotMatch(html, /wrong-legacy/);
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


def test_demo_page_mounts_the_component_without_touching_landing_pages() -> None:
    html = (REPO_ROOT / DEMO).read_text(encoding="utf-8")

    assert '<script src="pedal-steel-fretboard.js"></script>' in html
    assert "mountPedalSteelFretboard" in html
    assert "DEMO_HIGHLIGHTS" in html
    assert "PedalSteelFretboard" in html
    assert "steel-guitar-rag-landing.html" not in html
    assert "steel-guitar-rag-mock.html" not in html


def test_component_source_contains_no_eyeballed_fret_spacing_formula() -> None:
    source = (REPO_ROOT / COMPONENT).read_text(encoding="utf-8")

    assert 'const DECORATIVE_BACKGROUND_HREF = "/brand/pedal-steel-fretboard-background.svg";' in source
    assert "Decorative underlay only." in source
    assert ".answer-fretboard-mount" in source
    assert "grid-template-columns: minmax(0, 1fr);" in source
    assert "overflow-x: auto;" in source
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
