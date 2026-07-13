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
    assert '<main id="main-content">' in html
    assert "A connected pedal-steel learning studio" in home
    assert "See the neck. Understand the music. Play with confidence." in home
    assert (
        "Explore E9 positions. Build and practice melodies. Follow guided lessons. "
        "Get source-backed help from the Steel Guitar Brain."
    ) in home
    assert "Open Fretboard Explorer" in home
    assert "Open Melody Studio" in home
    assert home.index("home-hero") < home.index("home-explorer-panel")
    assert home.index("home-explorer-panel") < home.index("home-product-grid")
    assert home.index("home-product-grid") < home.index("home-backstage-strip")


def test_landing_home_exposes_all_four_workspaces_and_neutral_backstage() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    home = _home_markup()

    expected_links = {
        "/ui/e9-fretboard-explorer.html": "Fretboard Explorer",
        "/ui/melody-workbench.html": "Melody Studio",
        "/ui/lesson-workbench.html": "Lessons",
        "#ask-the-brain": "Ask the Brain",
    }
    for href, label in expected_links.items():
        assert f'href="{href}"' in html
        assert label in html

    assert "Visualize E9 positions, grips, intervals, scales, harmony, and movement across the neck." in home
    assert "Build, edit, play back, and practice melodies while connecting each note to a playable E9 position." in home
    assert "Follow reviewed learning paths or build a focused lesson for the topic, level, and time you have." in home
    assert "Get teacher-first, source-backed help with technique, tone, setup, gear, copedents, theory, and troubleshooting." in home
    assert "Manage your setup, copedent, account, access, feedback, and preferences." in home
    assert "Open Backstage" in home
    assert "Last Updated" not in home
    assert "Not connected" not in home


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


def test_landing_home_trust_copy_and_claim_boundaries() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    home = _home_markup()

    assert "Validated E9 positions" in html
    assert "Source-backed guidance when evidence is available" in html
    assert ">How it works</button>" in html
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
    assert "justify-self: start;" in css
    assert "justify-items: start;" in css
    assert "min-height: 44px;" in css
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
  DEMO_POSITIONS: [{ id: "g-3" }, { id: "g-6" }, { id: "g-10" }],
  mountPedalSteelFretboard(target, options) {
    assert.equal(target, container);
    receivedOptions = options;
    return figure;
  }
};
assert.equal(landing.mountExplorerPreview(container, api), figure);
assert.equal(receivedOptions.positions, api.DEMO_POSITIONS);
assert.equal(receivedOptions.hideFilterControls, true);
assert.equal(receivedOptions.hidePositionTools, true);
assert.equal(receivedOptions.hideLegend, true);
assert.equal(receivedOptions.showHighlightLabels, true);
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
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
