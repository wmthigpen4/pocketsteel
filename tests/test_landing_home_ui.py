from __future__ import annotations

import subprocess
from pathlib import Path


HTML_PATH = Path("ui/steel-guitar-rag-mock.html")
CSS_PATH = Path("ui/workspace-shell.css")
SCRIPT_PATH = Path("ui/landing-home.js")


def _home_markup() -> str:
    html = HTML_PATH.read_text(encoding="utf-8")
    return html.split('<div class="home-overview">', 1)[1].split(
        '<section class="answer-workspace"', 1
    )[0]


def test_landing_home_has_product_first_hierarchy_and_copy() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    home = _home_markup()

    assert '<a class="skip-link" href="#main-content">Skip to main content</a>' in html
    assert '<nav class="header-actions app-shell-nav" aria-label="Primary navigation">' in html
    assert 'href="workspace-shell.css?v=landing-preview-canvas-20260714-1"' in html
    assert '<main id="main-content">' in html
    assert "A connected pedal-steel learning studio" in home
    assert "See the neck. Understand the music. Play with confidence." in home
    assert (
        "Explore E9 positions. Build and practice melodies. Follow guided lessons. "
        "Get source-backed help from the Steel Guitar Brain."
    ) in home
    assert "home-hero-actions" not in home
    assert "Open Fretboard Explorer" not in home
    assert home.index("home-hero") < home.index("home-explorer-panel")
    assert home.index("home-explorer-panel") < home.index("home-product-grid")
    assert "home-backstage-strip" not in home


def test_landing_home_exposes_all_four_workspaces_and_neutral_backstage() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    home = _home_markup()

    expected_links = {
        "/ui/e9-fretboard-explorer.html": "Fretboard Explorer",
        "/ui/melody-workbench.html": "Melody Studio",
        "/ui/lesson-workbench.html": "Lessons",
    }
    for href, label in expected_links.items():
        assert home.count(f'href="{href}"') == 1
        assert label in home

    assert 'id="ask-the-brain"' in home
    assert "Visualize E9 positions, grips, intervals, scales, harmony, and movement across the neck." in home
    assert "Build, edit, play back, and practice melodies while connecting each note to a playable E9 position." in home
    assert "Follow reviewed learning paths or build a focused lesson for the topic, level, and time you have." in home
    assert "Get teacher-first, source-backed help with technique, tone, setup, gear, copedents, theory, and troubleshooting." in home
    assert "Manage your setup, copedent, account, access, feedback, and preferences." not in home
    assert "Open Backstage" not in home
    assert "Go Backstage" in html
    assert home.count("backstage-trigger") == 0
    assert html.count('class="header-action-button backstage-trigger"') == 1
    assert 'window.location.hash === "#backstage"' in html
    assert "activeBackstageTrigger = backstageTriggers[0] || null;" in html
    assert "openBackstageForAccessState();" in html
    assert "Last Updated" not in home
    assert "Not connected" not in home


def test_landing_workspace_cards_include_compact_tool_previews() -> None:
    home = _home_markup()
    css = CSS_PATH.read_text(encoding="utf-8")

    fretboard_preview = home.split(
        '<div class="home-card-preview home-fretboard-mini"', 1
    )[1].split('<a class="home-card-link"', 1)[0]
    assert fretboard_preview.count('class="mini-string-line"') == 6
    assert fretboard_preview.count('class="mini-fret-anchor') == 11
    assert fretboard_preview.count('class="mini-grip-dot"') == 9
    assert fretboard_preview.count('mini-fret-anchor is-amber') == 1
    assert fretboard_preview.count('mini-fret-anchor is-blue') == 1
    assert fretboard_preview.count('mini-fret-anchor is-pink') == 1
    assert "<svg" not in fretboard_preview
    assert "preserveAspectRatio" not in fretboard_preview
    assert 'class="home-card-preview home-score-preview" id="home-melody-preview"' in home
    assert 'aria-label="A short melody written in standard notation"' in home
    score_preview = home.split(
        '<div class="home-card-preview home-score-preview"', 1
    )[1].split('<a class="home-card-link"', 1)[0]
    assert "<svg" not in score_preview
    assert 'class="home-card-preview home-lesson-mini"' in home
    assert "Finding the I–IV–V in G" in home
    assert "saved lesson progress" not in home.casefold()
    assert "Start composing" in home
    assert ".home-score-preview .score-canvas" in css
    score_script = Path("ui/melody-score.js").read_text(encoding="utf-8")
    preview_renderer = score_script.split("function renderPreview(container)", 1)[1].split(
        "const api =", 1
    )[0]
    assert "home-real-score-canvas" in preview_renderer
    assert "VexFlow" not in preview_renderer
    assert "getContext(\"2d\")" in preview_renderer
    assert "context.bezierCurveTo" in preview_renderer
    assert "drawPreviewNote(context, note)" in preview_renderer
    assert "drawPreviewBeam(context, notes[1], notes[2])" in preview_renderer
    assert "drawPreviewBeam(context, notes[4], notes[5])" in preview_renderer
    assert "const width = 300;" in score_script
    assert "const height = 86;" in preview_renderer
    assert "canvas.width = Math.round(width * pixelRatio);" in preview_renderer
    assert "canvas.height = Math.round(height * pixelRatio);" in preview_renderer
    assert "context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);" in preview_renderer
    assert 'canvas.style.width = "100%";' not in preview_renderer
    assert 'canvas.style.height = "86px";' not in preview_renderer
    assert 'canvas.setAttribute("aria-hidden", "true")' in preview_renderer
    assert 'canvas.dataset.previewKind = "simple-musical-score"' in preview_renderer
    assert 'container.dataset.scoreRenderer = "simple-canvas-preview"' in preview_renderer
    assert "aspect-ratio: 150 / 43;" in css
    assert "width: 300px;" in css
    assert "max-width: 100%;" in css
    assert "height: auto !important;" in css
    assert "overflow: hidden;" in css
    assert "mountMelodyPreview" in SCRIPT_PATH.read_text(encoding="utf-8")
    assert 'src="vendor/vexflow-5.0.0.js?v=5.0.0"' in HTML_PATH.read_text(encoding="utf-8")
    assert 'src="melody-score.js?v=simple-score-canvas-20260714-1"' in HTML_PATH.read_text(encoding="utf-8")
    assert ".home-fretboard-mini" in css
    assert "grid-template-columns: repeat(12, minmax(0, 1fr));" in css
    assert ".mini-string-line" in css
    assert ".mini-fret-anchor" in css
    assert "grid-column: var(--fret-line);" in css
    assert ".mini-grip-dot" in css
    assert "left: 50%;" in css
    assert "transform: translate(-50%, -50%);" in css
    assert ".home-lesson-mini" in css


def test_landing_home_uses_compact_functional_ask_card_without_voice_control() -> None:
    home = _home_markup()

    assert 'id="ask-the-brain"' in home
    assert 'id="question"' in home
    assert '<button class="send" type="button">Ask a question</button>' in home
    assert 'id="suggested-prompts"' in home
    assert 'aria-label="Voice question"' not in home
    assert 'const visiblePrompts = Array.from({ length: Math.min(1, promptPool.length)' in HTML_PATH.read_text(
        encoding="utf-8"
    )


def test_landing_home_restores_source_aware_ai_shimmer_and_claim_boundaries() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    home = _home_markup()

    assert "Validated E9 positions" not in html
    assert "Source-backed guidance when evidence is available" not in html
    assert "Built deep for pedal steel." in html
    assert "Powered by source-aware AI underneath." in html
    assert 'class="footer-trigger footer-shimmer"' in html
    assert 'data-text="Powered by source-aware AI underneath."' not in html
    assert ".footer-shimmer::after" not in html
    assert ".home-ai-footer .footer-trigger.footer-shimmer {" in html
    assert "-webkit-background-clip: text;" in html
    assert "animation: footer-shimmer-sweep 3.2s ease-in-out infinite;" in html
    assert ".home-ai-footer .footer-trigger.footer-shimmer:hover," in html
    assert html.count("text-decoration: none;") >= 2
    assert "How the workbench supports you" not in html
    assert 'title: "What’s underneath?"' in html
    assert '“RAG” stands for retrieval-augmented generation' in html
    assert "searches organized knowledge before responding" in html
    assert "searches by meaning instead of exact wording" in html
    assert "grounded responses tied back to real discussions" in html
    assert 'class="tech-popover-rag-flow"' in html
    assert "Retrieve" in html and "Augment" in html and "Generate" in html
    assert 'aria-modal="true"' in html
    assert "techPopoverClose.focus();" in html
    assert "Open the full Explorer" not in home
    assert "One chord. Three positions. A whole neck opens up." in home
    assert "E9 · G major · strings 4-5-6" in home
    assert "validated positions" not in home.casefold()
    prohibited = (
        "YouTube transcription",
        "audio transcription",
        "full-song tab",
        "saved lesson progress",
        "completed lessons",
        "backing tracks",
        "personalized for you",
    )
    for claim in prohibited:
        assert claim.casefold() not in home.casefold()


def test_landing_shell_has_responsive_and_accessibility_contract() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")
    html = HTML_PATH.read_text(encoding="utf-8")

    assert "--shell-max: 1180px;" in css
    assert "outline: 2px solid var(--focus-ring) !important;" in css
    assert "@media (max-width: 1099px)" in css
    assert "@media (max-width: 699px)" in css
    assert "@media (max-width: 360px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "left: calc((100vw - 100%) / -2 - 12px);" in css
    assert "width: clamp(330px, 24vw, 350px);" in css
    assert "justify-items: start;" in css
    assert "min-height: 44px;" in css
    assert ".home-explorer-stage [data-string-label]," in css
    assert ".home-explorer-stage [data-tuning-label] {\n  display: none;\n}" in css
    assert ".page:not(.is-answering) .app-shell-nav {" in css
    assert "position: absolute;\n  top: 18px;\n  right: 0;" in css
    assert ".page:not(.is-answering) .app-shell-nav > :not(.backstage-trigger)" in css
    assert '--font-nav: "Gill Sans", "Gill Sans MT", "Avenir Next"' in css
    assert "font: 600 14px/1.15 var(--font-nav);" in css
    assert ".page:not(.is-answering) .app-shell-header .app-shell-nav {" in css
    assert "position: static;" in css
    assert 'role="dialog" aria-modal="true"' in html
    assert 'event.key === "Tab" && !backstage.hidden' in html
    assert "activeBackstageTrigger?.focus();" in html


def test_landing_preview_mounts_validated_demo_with_simplified_options() -> None:
    script = r"""
const assert = require("node:assert/strict");
const landing = require("./ui/landing-home.js");
let receivedOptions = null;
const interactive = [{ tabIndex: 0 }, { tabIndex: 2 }];
const figure = { classList: { add(name) { this.name = name; } } };
const container = {
  textContent: "",
  classList: { add() {}, remove() {} },
  querySelectorAll() { return interactive; }
};
const api = {
  DEMO_POSITIONS: [{ id: "g-3", fret: 3 }, { id: "g-6", fret: 6 }, { id: "g-10", fret: 10 }],
  mountPedalSteelFretboard(target, options) {
    assert.equal(target, container);
    receivedOptions = options;
    return figure;
  }
};
assert.equal(landing.mountExplorerPreview(container, api), figure);
assert.notEqual(receivedOptions.positions, api.DEMO_POSITIONS);
assert.deepEqual(receivedOptions.positions.map((position) => position.label), [
  "No pedals",
  "A + F lever",
  "A + B pedals"
]);
assert.deepEqual(receivedOptions.positions[0].stringActionLabels, {4: "4", 5: "5", 6: "6"});
assert.deepEqual(receivedOptions.positions[1].stringActionLabels, {4: "4F", 5: "5A", 6: "6"});
assert.deepEqual(receivedOptions.positions[2].stringActionLabels, {4: "4", 5: "5A", 6: "6B"});
assert.equal(receivedOptions.hideFilterControls, true);
assert.equal(receivedOptions.hidePositionTools, true);
assert.equal(receivedOptions.hideLegend, true);
assert.equal(receivedOptions.showHighlightLabels, true);
assert.equal(receivedOptions.showStringActionLabels, false);
assert.equal(receivedOptions.emphasizeVisibleHighlights, true);
assert.deepEqual(interactive.map((item) => item.tabIndex), [-1, -1]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_landing_preview_fails_gracefully_without_renderer() -> None:
    script = r"""
const assert = require("node:assert/strict");
const landing = require("./ui/landing-home.js");
const classes = [];
const container = {
  textContent: "",
  classList: { add(name) { classes.push(name); }, remove() {} },
  querySelectorAll() { return []; }
};
assert.equal(landing.mountExplorerPreview(container, null), null);
assert.equal(container.textContent, landing.UNAVAILABLE_MESSAGE);
assert.deepEqual(classes, ["is-unavailable"]);

classes.length = 0;
container.textContent = "";
assert.equal(landing.mountMelodyPreview(container, {renderPreview() { return false; }}), false);
assert.equal(container.textContent, landing.SCORE_UNAVAILABLE_MESSAGE);
assert.deepEqual(classes, ["is-unavailable"]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_simple_score_preview_draws_on_one_scaled_canvas_without_vexflow() -> None:
    script = r"""
const assert = require("node:assert/strict");
global.devicePixelRatio = 2;
const calls = [];
const context = new Proxy({}, {
  get(target, property) {
    if (property in target) return target[property];
    return (...args) => calls.push([property, ...args]);
  },
  set(target, property, value) {
    target[property] = value;
    calls.push([`set:${property}`, value]);
    return true;
  }
});
const canvas = {
  width: 0,
  height: 0,
  dataset: {},
  classList: { values: [], add(...names) { this.values.push(...names); } },
  attributes: {},
  setAttribute(name, value) { this.attributes[name] = value; },
  getContext(kind) { assert.equal(kind, "2d"); return context; }
};
global.document = { createElement(tag) { assert.equal(tag, "canvas"); return canvas; } };
const score = require("./ui/melody-score.js");
const container = {
  children: [],
  dataset: {},
  replaceChildren() { this.children = []; },
  appendChild(child) { this.children.push(child); }
};
assert.equal(score.renderPreview(container), true);
assert.deepEqual(container.children, [canvas]);
assert.equal(canvas.width, 600);
assert.equal(canvas.height, 172);
assert.equal(canvas.dataset.logicalWidth, "300");
assert.equal(canvas.dataset.logicalHeight, "86");
assert.equal(canvas.dataset.pixelRatio, "2");
assert.equal(canvas.dataset.previewKind, "simple-musical-score");
assert.equal(container.dataset.scoreRenderer, "simple-canvas-preview");
assert.equal(canvas.attributes["aria-hidden"], "true");
assert.ok(calls.some((call) => call[0] === "setTransform" && call[1] === 2 && call[4] === 2));
assert.equal(calls.filter((call) => call[0] === "ellipse").length, 6);
assert.ok(calls.filter((call) => call[0] === "bezierCurveTo").length >= 6);
assert.ok(calls.filter((call) => call[0] === "fillText" && call[1] === "4").length === 2);
assert.ok(calls.filter((call) => call[0] === "lineTo").length >= 15);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
