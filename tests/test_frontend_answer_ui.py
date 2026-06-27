from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def test_frontend_answer_client_posts_to_answer_api_and_normalizes_sources() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const code = fs.readFileSync("ui/answer-client.js", "utf8");
const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const answerUi = vm.runInContext("STEEL_RAG_ANSWER_UI", sandbox);

let capturedRequest;
(async () => {
  const result = await answerUi.requestAnswer("Why does my amp buzz?", {
    accessRole: "beta_user",
    fetchImpl: async (url, options) => {
      capturedRequest = { url, options };
      return {
        ok: true,
        status: 200,
        json: async () => ({
          question: "Why does my amp buzz?",
        answer: "Forum users suggest checking the ground path before replacing parts. [1]",
        sources: [
          {
              forumName: "Electronics",
              title: "Grounding a pedal steel",
              excerpt: "Check guitar ground continuity before replacing parts.",
              url: "https://bb.steelguitarforum.com/viewtopic.php?t=123"
          }
        ]
      })
      };
    }
  });

  assert.equal(capturedRequest.url, "/api/answer");
  assert.equal(capturedRequest.options.method, "POST");
  assert.equal(capturedRequest.options.credentials, "same-origin");
  assert.equal(capturedRequest.options.headers["Content-Type"], "application/json");
  assert.equal(capturedRequest.options.headers["X-Steel-Rag-Dev-Access-Role"], "beta_user");
  const legacyHeader = ["X", "Turn" + "around", "Dev", "Access", "Role"].join("-");
  assert.equal(capturedRequest.options.headers[legacyHeader], undefined);
  assert.equal(JSON.parse(capturedRequest.options.body).question, "Why does my amp buzz?");
  assert.equal(result.sections[0].body, "Forum users suggest checking the ground path before replacing parts. [1]");
  assert.equal(JSON.stringify(result.sources[0]), JSON.stringify({
    forum: "Electronics",
    title: "Grounding a pedal steel",
    excerpt: "Check guitar ground continuity before replacing parts.",
    url: "https://bb.steelguitarforum.com/viewtopic.php?t=123",
    date: ""
  }));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_frontend_answer_client_fetches_session_and_normalizes_access() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const code = fs.readFileSync("ui/answer-client.js", "utf8");
const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const answerUi = vm.runInContext("STEEL_RAG_ANSWER_UI", sandbox);

let capturedRequest;
(async () => {
  const beta = await answerUi.requestSession({
    accessRole: "beta_user",
    fetchImpl: async (url, options) => {
      capturedRequest = { url, options };
      return {
        ok: true,
        status: 200,
        json: async () => ({
          authenticated: true,
          role: "beta_user",
          email: "beta@example.test",
          authProvider: "cloudflare_access"
        })
      };
    }
  });

  assert.equal(capturedRequest.url, "/api/session");
  assert.equal(capturedRequest.options.method, "GET");
  assert.equal(capturedRequest.options.credentials, "same-origin");
  assert.equal(capturedRequest.options.headers.Accept, "application/json");
  assert.equal(capturedRequest.options.headers["X-Steel-Rag-Dev-Access-Role"], "beta_user");
  assert.equal(JSON.stringify(beta), JSON.stringify({
    authenticated: true,
    role: "beta_user",
    authProvider: "cloudflare_access"
  }));
  assert.equal("email" in beta, false);

  assert.equal(JSON.stringify(answerUi.normalizeSessionResponse({
    authenticated: false,
    role: "admin",
    email: "admin@example.test",
    authProvider: "cloudflare_access"
  })), JSON.stringify({
    authenticated: false,
    role: "anonymous",
    authProvider: "cloudflare_access"
  }));

  assert.equal(answerUi.sessionGrantsLiveAccess({
    authenticated: true,
    role: "beta_user",
    authProvider: "cloudflare_access"
  }), true);
  assert.equal(answerUi.sessionGrantsLiveAccess({
    authenticated: true,
    role: "admin",
    authProvider: "cloudflare_access"
  }), true);
  assert.equal(answerUi.sessionGrantsLiveAccess({
    authenticated: false,
    role: "anonymous",
    authProvider: "cloudflare_access"
  }), false);
  assert.equal(answerUi.sessionUsesLocalDev({ authProvider: "local_dev" }), true);
  assert.equal(answerUi.sessionUsesLocalDev({ authProvider: "cloudflare_access" }), false);
  assert.equal(answerUi.sessionUsesLocalDev({ authProvider: "cloudflare-access" }), false);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_answer_ui_uses_live_answer_client_not_mock_answer_data() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert '<script src="answer-client.js?v=e9-explorer-home-entry-20260623"></script>' in html
    assert '<script src="pedal-steel-fretboard.js?v=e9-explorer-home-entry-20260623"></script>' in html
    assert '<script src="mock-answer-data.js"></script>' not in html
    assert "STEEL_RAG_ANSWER_UI.requestAnswer" in html
    assert "STEEL_RAG_ANSWER_UI.requestSession" in html
    assert "No sources returned" in html


def test_answer_ui_includes_home_hero_hanging_sign_without_changing_answer_logo() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert 'class="hero-hanging-sign"' in html
    assert 'class="landing-sign" autoplay muted loop playsinline' in html
    assert 'poster="brand/steel-guitar-rag-landing-fallback-alpha.png?v=landing-alpha-app-20260618"' in html
    assert 'src="brand/steel-guitar-rag-landing-alpha.webm?v=landing-alpha-app-20260618"' in html
    assert 'type="video/webm"' in html
    assert 'type="video/mp4"' not in html
    assert 'class="landing-sign-fallback" src="brand/steel-guitar-rag-landing-fallback-alpha.png?v=landing-alpha-app-20260618"' in html
    assert "top: clamp(-42px, -3vw, -24px);" in html
    assert "left: -18px;" in html
    assert "width: clamp(300px, 23vw, 340px);" in html
    assert "transform: rotate(-1.5deg);" in html
    assert "padding: clamp(170px, 14vw, 220px) 0 24px;" in html
    assert "padding-top: clamp(120px, 20vw, 170px);" in html
    assert "top: 8px;" in html
    assert "padding-top: 200px;" in html
    assert "top: 8px;" in html
    assert "top: 48px;" not in html
    assert "left: -18px;" in html
    assert "width: clamp(190px, 55vw, 240px);" in html
    assert ".hero-hanging-sign.is-animated .landing-sign" in html
    assert ".hero-hanging-sign.is-animated .landing-sign-fallback" in html
    assert ".landing-sign-fallback,\n      .hero-hanging-sign.is-animated .landing-sign-fallback {\n        display: block;" in html
    assert "object-fit: contain;" in html
    assert "object-position: top left;" in html
    assert "image-rendering: auto;" in html
    assert 'prefers-reduced-motion: reduce' in html
    assert ".brand-home {\n      display: none;" in html
    assert ".page.is-answering .brand-home {\n      display: inline-flex;" in html
    assert ".page.is-answering .hero-hanging-sign" in html
    assert 'class="answer-brand-badge" autoplay muted loop playsinline' in html
    assert 'poster="brand/steel-guitar-rag-answer-badge-fallback-alpha.png?v=answer-badge-rag-artwork-3c4dedb"' in html
    assert 'src="brand/steel-guitar-rag-answer-badge-alpha.webm?v=answer-badge-rag-artwork-3c4dedb"' in html
    assert 'class="answer-brand-fallback" src="brand/steel-guitar-rag-answer-badge-fallback-alpha.png?v=answer-badge-rag-artwork-3c4dedb"' in html
    assert "width: clamp(160px, 18vw, 240px);" in html
    assert "max-height: 86px;" in html
    assert Path("ui/brand/steel-guitar-rag-landing-alpha.webm").is_file()
    assert Path("ui/brand/steel-guitar-rag-landing-fallback-alpha.png").is_file()
    assert Path("ui/brand/steel-guitar-rag-answer-badge-alpha.webm").is_file()
    assert Path("ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png").is_file()
    assert Path("public/brand/steel-guitar-rag-answer-badge-alpha.webm").is_file()
    assert Path("public/brand/steel-guitar-rag-answer-badge-fallback-alpha.png").is_file()


def test_answer_ui_links_to_e9_fretboard_explorer_surface() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert "<span>Explore Fretboard</span>" in html
    assert 'href="/ui/e9-fretboard-explorer.html"' in html
    assert 'aria-label="Explore the E9 virtual fretboard"' in html
    assert 'title="Explore the E9 virtual fretboard"' in html
    assert "explorer-header-link" in html
    assert 'class="header-action-button explorer-header-link"' in html
    assert 'class="header-action-button backstage-trigger"' in html
    assert ".header-action-button {" in html
    header_action_rule = html.split(".header-action-button {", 1)[1].split("}", 1)[0]
    assert "font-family:" not in header_action_rule
    assert "font-size:" not in header_action_rule
    assert "font-weight:" not in header_action_rule
    assert "line-height:" not in header_action_rule
    assert "var(--font-ui)" not in header_action_rule
    assert "var(--font-lesson)" not in header_action_rule
    assert "Gill Sans" not in header_action_rule
    assert "-apple-system, BlinkMacSystemFont" not in header_action_rule
    assert "letter-spacing: 0;" in html
    assert 'aria-controls="backstage"' in html
    assert 'id="backstage-cta-label">Get a Backstage Pass</span>' in html
    assert html.index('class="header-action-button explorer-header-link"') < html.index('class="header-action-button backstage-trigger"')
    assert 'class="header-action-button explorer-header-link" href="/ui/e9-fretboard-explorer.html"' in html
    assert 'class="backstage-trigger" href="/ui/e9-fretboard-explorer.html"' not in html
    assert ">Go Backstage</a>" not in html
    assert "explorer-entry-card" not in html
    assert "not corpus retrieval or RAG-generated fretboard positions" not in html
    assert "[object Object]" not in html
    assert html.index("<span>Explore Fretboard</span>") < html.index('id="question"')
    assert html.index("<span>Explore Fretboard</span>") < html.index("Get a Backstage Pass")
    assert ".explorer-header-link,\n    .backstage-trigger" not in html


def test_e9_fretboard_explorer_surface_uses_display_fields_and_validated_data() -> None:
    html = Path("ui/e9-fretboard-explorer.html").read_text(encoding="utf-8")
    script = Path("ui/e9-fretboard-explorer.js").read_text(encoding="utf-8")
    rules = Path("ui/e9-music-rules.js").read_text(encoding="utf-8")
    data = Path("ui/e9-fretboard-explorer-data.js").read_text(encoding="utf-8")
    payloads = json.loads(data.split("window.STEEL_RAG_E9_EXPLORER_PAYLOADS = ", 1)[1].split(";\nwindow.", 1)[0])
    payload = payloads["G"]

    assert "E9 Fretboard Explorer" in html
    assert "Validated Explorer data" in html
    assert "checked against tuning and pedal/lever changes" in html
    assert "These Explorer rows are deterministic teaching data, separate from source-card answers." not in html
    assert "not corpus retrieval or RAG-generated fretboard positions" not in html
    assert '<script src="pedal-steel-fretboard.js?v=explorer-harmonized-path-mode-20260626"></script>' in html
    assert "pedal-steel-fretboard.js?v=e9-explorer-explanation-ui-20260623" not in html
    assert "pedal-steel-fretboard.js?v=explorer-ui-cleanup-20260623" not in html
    assert "pedal-steel-fretboard.js?v=selected-svg-render-20260623" not in html
    assert "pedal-steel-fretboard.js?v=explorer-compact-copedent-20260625" not in html
    assert '<script src="e9-fretboard-explorer-data.js?v=explorer-harmonized-path-mode-20260626"></script>' in html
    assert "[hidden] {\n      display: none !important;\n    }" in html
    assert '<script src="e9-music-rules.js?v=shared-music-rules-20260627"></script>' in html
    assert '<script src="e9-fretboard-explorer.js?v=chord-map-view-20260627"></script>' in html
    assert html.index("e9-music-rules.js?v=shared-music-rules-20260627") < html.index("e9-fretboard-explorer.js?v=chord-map-view-20260627")
    assert "e9-fretboard-explorer.js?v=grip-vocabulary-20260627" not in html
    assert "e9-fretboard-explorer.js?v=single-note-learning-20260626" not in html
    assert "e9-fretboard-explorer.js?v=single-note-finder-20260626" not in html
    assert "explorer-top-note-marker-source-20260626" not in html
    assert "e9-fretboard-explorer.js?v=compact-controls-20260626" not in html
    assert "e9-fretboard-explorer.js?v=explorer-compact-copedent-20260625" not in html
    assert "e9-fretboard-explorer.js?v=explorer-harmonized-scale-clarity-20260626" not in html
    assert "e9-fretboard-explorer.js?v=explorer-harmonized-path-mode-20260626" not in html
    assert "e9-fretboard-explorer.js?v=top-label-chip-order-20260626" not in html
    assert "e9-fretboard-explorer.js?v=path-string-group-visibility-20260626" not in html
    expected_key_options = {
        "C": "C",
        "Db": "C# (or D♭)",
        "D": "D",
        "Eb": "D# (or E♭)",
        "E": "E",
        "F": "F",
        "Gb": "F# (or G♭)",
        "G": "G",
        "Ab": "G# (or A♭)",
        "A": "A",
        "Bb": "A# (or B♭)",
        "B": "B",
    }
    for value, label in expected_key_options.items():
        assert f'<option value="{value}"' in html
        assert label in html
        assert value in payloads
    for hidden_value in ["C#", "D#", "F#", "G#", "A#"]:
        assert f'<option value="{hidden_value}"' not in html
    assert "Enharmonic spellings are listed separately" not in html
    assert "Enharmonic keys share one selector entry" in html
    assert '<label for="explorer-copedent">Copedent</label>' in html
    assert '<label for="explorer-copedent">E9 setup</label>' not in html
    assert '<select id="explorer-copedent"' in html
    assert '<option value="emmons-e9-basic" selected>Emmons E9</option>' in html
    assert '<option value="day-e9-basic">Day E9</option>' in html
    assert '<option value="custom-e9-lkv">Custom E9 (with LKV)</option>' in html
    assert '<option value="my-copedent-e9" disabled>My Copedent (E9) - Coming soon in Backstage</option>' in html
    assert '<div class="explorer-copedent-control-row">' not in html
    mode_markup = html.split('<section class="explorer-mode-panel" aria-label="Explorer mode">', 1)[1].split("</section>", 1)[0]
    controls_markup = html.split('<section class="explorer-controls" aria-label="Explorer filters">', 1)[1].split("</section>", 1)[0]
    panel_markup = html.split('<section class="explorer-panel" aria-label="Explorer fretboard">', 1)[1].split("</section>", 1)[0]
    assert html.index('<section class="explorer-mode-panel" aria-label="Explorer mode">') < html.index('<section class="explorer-controls" aria-label="Explorer filters">')
    assert 'id="explorer-copedent-open"' not in controls_markup
    assert '<dialog class="explorer-copedent-dialog" id="explorer-copedent-dialog"' in html
    assert '<button class="explorer-inline-button" id="explorer-copedent-close" type="button">Close</button>' in html
    assert "Choose the copedent that matches your guitar" in html
    assert "Choose the E9 setup that matches your guitar" not in html
    assert "My Copedent (E9) is coming soon in Backstage" in html
    assert ".explorer-control--copedent {\n      grid-column: span 1;" in html
    assert "C6" not in html
    root_fret_classes = {
        next(row["fret"] for row in key_payload["positions"] if row["scale_type"] == "major" and row["chord_function"] == "I")
        % 12
        for key_payload in payloads.values()
    }
    assert len(root_fret_classes) == 12
    assert '<option value="major">G major</option>' in html
    assert '<option value="natural_minor">G natural minor</option>' in html
    assert '<label for="explorer-explore-mode">Explore mode</label>' in html
    assert '<label for="explorer-explore-mode">Explore mode</label>' in mode_markup
    assert '<label for="explorer-explore-mode">Explore mode</label>' not in controls_markup
    assert '<option value="single" selected>Single grip</option>' in html
    assert '<option value="path">Harmonized scale path</option>' in html
    assert '<option value="note">Single-note finder</option>' in html
    assert '<option value="voicing">Voicing identifier</option>' in html
    assert '<option value="chord">Chord / Voicing Finder</option>' in html
    assert "Single grip filters exact strings" in html
    assert "Voicing identifier explains one shape." in html
    assert "Chord / Voicing Finder searches practical shapes for a target chord." in html
    assert ".explorer-mode-panel {" in html
    assert "grid-template-columns: minmax(220px, 340px) minmax(0, 1fr);" in html
    assert "Start by choosing the kind of fretboard question you want to explore" in mode_markup
    assert 'id="explorer-note-finder"' in html
    assert 'id="explorer-voicing-identifier"' in html
    assert 'id="explorer-chord-finder"' in html
    assert ".explorer-chord-finder__controls" in html
    assert ".explorer-chord-finder__field--target" not in html
    assert ".explorer-chord-finder__input" not in html
    assert ".explorer-voicing-identifier__input" in html
    assert ".explorer-voicing-identifier__field" in html
    assert "grid-template-columns: minmax(96px, 0.25fr) minmax(210px, 0.45fr) minmax(0, 1fr);" in html
    assert "align-items: start;" in html
    assert ".explorer-note-grid" in html
    assert ".explorer-note-cell.is-result" in html
    assert '<label for="explorer-path-family">Path family</label>' in html
    assert '<option value="high">High path: 3-4-5 / 4-5-6</option>' in html
    assert '<option value="middle">Middle path: 5-6-8 / 5-6-7</option>' in html
    assert '<option value="low" selected>Low path: 6-8-10 / 6-7-10</option>' in html
    assert "This path changes string groups when the harmony requires it" in html
    assert "#explorer-path-family-control {\n      grid-column: span 2;" in html
    assert "#explorer-path-family-control,\n      .explorer-control--notation" in html
    assert '<option value="two_string_harmonized">2-string harmonized scale</option>' in html
    assert '<option value="five_eight_branch">5&amp;8 branch positions (2-string)</option>' not in html
    assert '<option value="three_string_diatonic" selected>3-string diatonic harmony</option>' in html
    assert '<div class="explorer-control" id="explorer-harmony-control">' in html
    assert '<div class="explorer-header-actions" aria-label="Explorer actions">' in html
    assert '<button class="explorer-back" id="explorer-glossary-open" type="button" aria-haspopup="dialog" aria-controls="explorer-glossary-dialog">' in html
    assert "<span>Glossary</span>" in html
    assert '<button class="explorer-back" id="explorer-copedent-open" type="button" aria-haspopup="dialog" aria-controls="explorer-copedent-dialog">' in html
    assert "<span>Copedent</span>" in html
    assert "<span>View chart</span>" not in html
    assert '<a class="explorer-back" href="steel-guitar-rag-mock.html">' in html
    assert "<span>Back to app</span>" in html
    assert ".explorer-back {" in html
    explorer_back_rule = html.split(".explorer-back {", 1)[1].split("}", 1)[0]
    for expected_style in [
        "display: inline-flex;",
        "align-items: center;",
        "gap: 9px;",
        "min-height: 42px;",
        "padding: 0 16px;",
        "border-radius: 999px;",
        "border: 1px solid rgba(240, 191, 105, 0.34);",
        "background: rgba(13, 14, 14, 0.68);",
        "color: rgba(244, 234, 214, 0.88);",
        "cursor: pointer;",
        'font-family: "Gill Sans", "Gill Sans MT", "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif;',
        "font-size: 1rem;",
        "font-weight: 400;",
        "letter-spacing: normal;",
        "text-decoration: none;",
        "box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.26), 0 18px 48px rgba(0, 0, 0, 0.24);",
    ]:
        assert expected_style in explorer_back_rule
    assert "Source Serif" not in explorer_back_rule
    assert "button.explorer-back" not in html
    explorer_back_svg_rule = html.split(".explorer-back svg {", 1)[1].split("}", 1)[0]
    for expected_style in [
        "width: 18px;",
        "height: 18px;",
        "flex: 0 0 auto;",
        "stroke: currentColor;",
        "stroke-width: 1.9;",
        "fill: none;",
        "stroke-linecap: round;",
        "stroke-linejoin: round;",
    ]:
        assert expected_style in explorer_back_svg_rule
    explorer_hover_rule = html.split(".explorer-back:hover,\n    .explorer-back:focus-visible {", 1)[1].split("}", 1)[0]
    assert "color: var(--cream);" in explorer_hover_rule
    assert "border-color: rgba(246, 190, 88, 0.62);" in explorer_hover_rule
    assert "background: rgba(240, 191, 105, 0.075);" in explorer_hover_rule
    assert "outline: none;" in explorer_hover_rule
    assert ".explorer-back {\n        min-height: 40px;\n        padding: 0 12px;" in html
    assert ".explorer-copedent-dialog__bar .explorer-inline-button {" in html
    dialog_close_rule = html.split(".explorer-copedent-dialog__bar .explorer-inline-button {", 1)[1].split("}", 1)[0]
    for expected_style in [
        "width: auto;",
        "min-width: 88px;",
        "flex: 0 0 auto;",
        "padding: 0 14px;",
    ]:
        assert expected_style in dialog_close_rule
    assert "grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));" in html
    assert "align-content: start;" in html
    assert ".explorer-control select {\n      height: 42px;" in html
    assert "height: 42px;" in html
    assert '<label for="explorer-grip-vocabulary">Grip vocabulary</label>' in html
    assert '<option value="core" selected>Core</option>' in html
    assert '<option value="extended">Extended</option>' in html
    assert '<option value="two_string">Two-string</option>' in html
    assert '<option value="all">All practical</option>' in html
    assert "Core keeps the default view clean. Extended and two-string reveal wider tab and dyad vocabulary." in html
    assert ".explorer-controls-note {" not in html
    assert "explorer-controls-note" not in html
    assert '<details class="explorer-grip-help-disclosure">' in controls_markup
    assert '<details class="explorer-grip-help-disclosure" open>' not in html
    assert "<summary>About grip vocabulary</summary>" in controls_markup
    assert "Core grips are common string sets. Extended and two-string vocabulary are opt-in" in controls_markup
    assert "5-7-8 is the advanced E-lower pocket" in controls_markup
    assert "5-8 appears in 2-string branch routes" in controls_markup
    assert '<p class="explorer-note">Core grips are common string sets.' not in html
    assert ".explorer-note {\n      grid-column: 1 / -1;" not in html
    assert "explorer-control--string-group" in html
    assert ".explorer-control--string-group {\n      grid-column: 1 / -1;" not in html
    assert '<div class="explorer-control explorer-control--string-group" id="explorer-string-group-control">' in html
    assert '<select id="explorer-string-group" aria-describedby="explorer-string-group-help">' in html
    assert '<select id="explorer-string-group" multiple' not in html
    assert 'size="4"' not in html
    assert "Select one or more groups" not in html
    assert "Choose All or one exact group. Path mode uses Path family instead." in html
    assert '<optgroup label="Core grips">' in html
    assert '<optgroup label="Advanced swaps">' in html
    assert '<option value="5-7-8">5-7-8</option>' in html
    assert '<option value="all" selected>All 3-string groups</option>' in html
    assert "Advanced swaps:</strong> less direct string combinations" not in html
    assert "5&amp;8 branch:</strong> 5-8 appears with the 2-string harmonized-scale groups" not in html
    assert "deterministic teaching data" not in html
    assert "corpus retrieval" not in html
    assert "source-card answers" not in html
    assert "RAG-generated" not in html
    assert "Explorer shorthand help" not in html
    assert "explorer-help-grid" not in html
    assert "explorer-help-card" not in html
    assert "<strong>Shorthand</strong>" not in html
    assert "<dt>m7b5</dt><dd>Means minor seven flat five." in html
    assert "<dt>ø</dt><dd>The half-diminished symbol." in html
    assert "<dt>°</dt><dd>The diminished symbol." in html
    assert "vii° means the diminished chord built on the seventh scale degree" in html
    assert "<dt>Partial row</dt><dd>A row that does not contain every chord tone by itself." in html
    assert "<dt>Core grip</dt><dd>A beginner-friendly string set" in html
    assert "<dt>Extended grip</dt><dd>A real-world tab or voicing-discovery grip" in html
    assert "<dt>Two-string grip / dyad</dt><dd>A two-note grip." in html
    assert "<dt>Pad / sustain</dt><dd>A held support sound" in html
    assert "<dt>Partial voicing</dt><dd>A useful part of a chord" in html
    assert 'id="explorer-tooltip"' in html
    assert 'id="explorer-active-results"' in html
    assert 'id="explorer-copedent-chart"' in html
    assert 'id="explorer-control-impact-preview"' in html
    assert 'id="explorer-selected-detail"' in html
    assert html.count('id="explorer-notation-control"') == 1
    assert html.count('id="explorer-notation-label"') == 1
    assert html.count('id="explorer-notation-help"') == 1
    assert "data-explorer-notation-mode" not in controls_markup
    assert '<div class="explorer-control explorer-control--notation explorer-panel-notation" id="explorer-notation-control">' in panel_markup
    assert panel_markup.index('id="explorer-notation-control"') < panel_markup.index('id="explorer-active-results"')
    assert panel_markup.index('id="explorer-notation-control"') < panel_markup.index('id="explorer-fretboard"')
    assert ".explorer-panel-notation {" in html
    assert "grid-template-columns: auto minmax(240px, 380px) minmax(0, 1fr);" in html
    active_result_track_rule = html.split(".explorer-active-results__track {", 1)[1].split("}", 1)[0]
    for expected_style in [
        "display: flex;",
        "overflow-x: auto;",
        "scroll-snap-type: x proximity;",
        "-webkit-overflow-scrolling: touch;",
    ]:
        assert expected_style in active_result_track_rule
    active_result_rule = html.split(".explorer-active-result {", 1)[1].split("}", 1)[0]
    assert "flex: 0 0 clamp(150px, 15vw, 184px);" in active_result_rule
    assert "scroll-snap-align: start;" in active_result_rule
    mobile_rule = html.split("@media (max-width: 760px) {", 1)[1].split("</style>", 1)[0]
    assert ".explorer-control-impact-tabs" in mobile_rule
    assert "flex-wrap: nowrap;" in mobile_rule
    assert "overscroll-behavior-x: contain;" in mobile_rule
    assert 'data-explorer-notation-mode="notes"' in html
    assert 'data-explorer-notation-mode="nns"' in html
    assert 'data-explorer-notation-mode="roman"' in html
    assert 'data-explorer-notation-mode="numbers"' in html
    assert '<span class="explorer-control-label" id="explorer-notation-label">Notation</span>' in html
    assert 'aria-labelledby="explorer-notation-label"' in html
    assert "Controls card, marker, and top-label display." in html
    assert ".explorer-control--notation {\n      grid-column: span 2;" in html
    assert "flex-wrap: wrap;" in html
    assert "explorer-teaching-note" in html
    assert "explorer-copedent-chart__table" in html
    assert "Pedal and lever impact" in script
    assert "STEEL_RAG_E9_MUSIC_RULES" in rules
    assert "musicRules.identifyVoicing" in script
    assert "musicRules.parseChordFinderQuery" in script
    assert "musicRules.chordFinderQualityGate" in script
    assert 'e9-fretboard-explorer.js?v=chord-map-view-20260627' in html
    assert "payloadsByCopedent" in script
    assert "renderCopedentChart" in script
    assert "openCopedentDialog" in script
    assert "closeCopedentDialog" in script
    assert "data-explorer-notation-mode" in script
    assert 'notationMode = "notes"' in script
    assert "MAJOR_SCALE_SEQUENCES" in rules
    assert '"1", "2-", "3-", "4", "5", "6-", "7°"' in rules
    assert '"I", "ii", "iii", "IV", "V", "vi", "vii°"' in rules
    assert '"1", "2m", "3m", "4", "5", "6m", "7dim"' in rules
    assert "control_impact_preview" in script
    assert "control_impacts" in script
    assert "rowControlImpactsHtml" in script
    assert "explorer-control-impact-tab" in html
    assert "explorer-control-impact-detail" in html
    assert "explorer-row-control-impacts" in html
    assert "Showing validated positions" not in html
    assert 'id="explorer-result-count"' not in html
    assert "0 validated rows" not in html
    assert "explorer-row-card" not in html

    assert "display_notes" in script
    assert "display_top_voice" in script
    assert "display_summary" in script
    assert "display_scale_notes" in script
    assert "FIVE_EIGHT_GROUPS" in script
    assert "TWO_STRING_DISPLAY_GROUPS" in script
    assert "availableStringGroups" in script
    assert "5&8 branch" in script
    assert "per_string_changes" in script
    assert "warnings" in script
    assert "explanation_summary" in script
    assert "Why this position works" in script
    assert "teachingNoteHtml" in script
    assert "STEEL_RAG_E9_EXPLORER_PAYLOADS" in data
    assert "availableKeys" in script
    assert "activePayload" in script
    assert "pitch_validated" in data
    assert "hideFilterControls: true" in script
    assert "hidePositionTools: true" in script
    assert "hideLegend: true" in script
    assert "showHighlightLabels: true" in script
    assert "emphasizeVisibleHighlights" in script
    assert 'highlightStyle: "prominent"' in script
    assert "selectedStringGroups" in script
    assert "EXPLORE_MODES" in script
    assert "PATH_FAMILIES" in script
    assert "Harmonized scale path" in script
    assert "pathRows" in script
    assert "Scale path rail" in script
    assert "data-path-step" in script
    assert "data-path-display-mode" not in script
    assert "Compare same fret" not in script
    assert "Ghost all" not in script
    assert "data-path-prev" not in script
    assert "data-path-next" not in script
    assert "Same-fret grips are staggered" in script
    assert "degreeSequenceForPath" in script
    assert "pathChangeNote" in script
    assert "this path changes string groups when the harmony requires it" in script
    assert "selectedCopedentId" in script
    component = Path("ui/pedal-steel-fretboard.js").read_text(encoding="utf-8")
    assert "data-selected-string-group-lanes" not in component
    assert "data-selected-string-row" not in component
    assert "emphasizeStringGroups" not in component
    assert "tooltipText" in script
    assert "tooltipHtmlForRows" in script
    assert "groupRowsForMarkers" in script
    assert "markerLabelForGroup" in script
    assert "renderTopIntervalFilter" in script
    assert "data-top-interval-filter" in script
    assert 'id="explorer-top-interval-filter"' in html
    assert "renderFretRangeFilter" in script
    assert "data-fret-range-filter" in script
    assert 'id="explorer-fret-range-filter"' in html
    assert "Visible fret range" in script
    assert "Core" in script and "Frets 1-15" in script
    assert "Low" in script and "Frets 0-8" in script
    assert "High" in script and "Frets 10-24" in script
    assert "All" in script and "Frets 0-24" in script
    assert "Top note interval" in html
    assert "Top note" in html
    assert "Flat symbol" in html
    assert "data-marker-id" in script
    assert "data-marker-tone" in script
    assert "explorer-marker-token" in html
    assert "data-explorer-marker-label" in script
    assert "is-explorer-selected-marker" in script
    assert "is-explorer-hover-marker" in script
    assert "Marker ${escapeHtml(markerLabel)}" not in script
    assert "Fretboard ${escapeHtml(markerLabel)}" not in script
    assert "activeTopLabelName()" in script
    assert "topVoiceExplanationHtml" in script
    assert "stringActionRowsHtml" in script
    assert "String actions" in script
    assert "String map" not in script
    assert "pos." not in script
    assert "setups" in script
    assert "Choose the E9 setup that matches your guitar" not in script
    assert "Choose the copedent that matches your guitar" in script
    assert "selectedImpactControlIds" in script
    assert "data-control-impact-clear" in script
    assert "No direct impact on the selected string group" in script
    assert "NOTE_CONTROL_STATES" in script
    assert "NOTE_WORKFLOWS" in script
    assert "identifyVoicing" in script
    assert "data-voicing-control-state" not in script
    assert "data-voicing-string-preset" not in script
    assert "data-voicing-control" in script
    assert "data-voicing-control-clear" in script
    assert "data-voicing-string" in script
    assert "Choose up to 4 strings" in script
    assert "This is not a common musical grip on E9" in script
    assert "Single-note finder" in script
    assert "Voicing identifier" in script
    assert "Find all" in script
    assert "Reverse lookup" in script
    assert "Pedal changes" in script
    assert "Build grip" in script
    assert "Drill" in script
    assert "Event sync" in script
    assert "data-note-control-state" in script
    assert "data-note-workflow" in script
    assert "data-note-string-filter" in script
    assert "data-note-reverse-result" in script
    assert "data-note-grip-card" in script
    assert "data-note-grip-vocabulary" in script
    assert "data-note-grip-role" in script
    assert "GRIP_REGISTRY" in script
    assert "GRIP_ROLE_OPTIONS" in script
    assert "pad_sustain" in script
    assert '"4-6-10"' in rules
    assert '"3-5-8"' in rules
    assert '"5-6-9"' in rules
    assert '"4-6-9"' in rules
    assert '"3-6"' in rules
    assert '"8-10"' in rules
    assert "shared-music-rules-20260627" in html
    assert "data-note-sync-event" in script
    assert "data-note-cell" in script
    assert "Dominant 7 / V7" in script
    assert "DOMINANT_9TH_GRIPS" in script
    assert "Open note at fret" in script
    assert "Final note" in script
    assert "Pedals and levers change the note on affected strings" in script
    assert "Deterministic event sync demo" in script

    g_major_three = [
        row for row in payload["positions"]
        if row["key"] == "G" and row["scale_type"] == "major" and row["harmony_type"] == "three_string_diatonic"
    ]
    g_minor_three = [
        row for row in payload["positions"]
        if row["key"] == "G" and row["scale_type"] == "natural_minor" and row["harmony_type"] == "three_string_diatonic"
    ]
    assert g_major_three
    assert g_minor_three
    for rows in (g_major_three, g_minor_three):
        assert {"3-4-5", "4-5-6", "5-6-8", "5-6-7", "6-8-10", "6-7-10"}.issubset({row["string_group"] for row in rows})
    g_major_456 = [row for row in g_major_three if row["string_group"] == "4-5-6"]
    assert [row["chord_name"] for row in g_major_456] == ["G", "A", "B", "C", "D", "E", "F#", "G"]
    assert [row["fret"] for row in g_major_456] == [3, 3, 5, 8, 10, 10, 13, 15]
    g_minor_456 = [row for row in g_minor_three if row["string_group"] == "4-5-6"]
    assert [row["chord_name"] for row in g_minor_456] == ["G", "A", "Bb", "C", "D", "Eb", "F", "G"]
    assert [row["fret"] for row in g_minor_456] == [1, 4, 6, 6, 8, 11, 13, 13]
    assert "B by itself may not match rows in this view that expect A+B together" in script
    assert "selectedRowId" in script
    assert "renderActiveResults" in script
    assert "data-active-result-row" in script
    assert "Pitch validated" not in script
    assert "validated row" not in script
    assert "Starter" not in html
    assert "Common" not in html.split("explorer-active-results", 1)[0]
    assert 'id="explorer-glossary-open"' in html
    assert 'id="explorer-glossary-dialog"' in html
    for term in [
        "Copedent",
        "Diatonic harmony",
        "Harmonized scale",
        "Diminished",
        "Half-diminished",
        "NNS / Nashville Number System",
        "Notation mode",
        "Notes",
        "NNS",
        "Roman",
        "Grips",
        "Pedals",
        "Levers",
        "Root",
        "Inversion",
        "String group",
        "Dominant 7",
        "V7",
        "9th string",
        "Flat 7 / ♭7",
    ]:
        assert f"<dt>{term}</dt>" in html
    assert "external" not in html.lower()
    assert "[object Object]" not in data
    assert "validated E9 pitch logic" in data
    assert "STEEL_RAG_E9_EXPLORER_PAYLOADS_BY_COPEDENT" in data
    assert '"selected_copedent"' in data
    assert '"emmons-e9-basic"' in data
    assert '"day-e9-basic"' in data
    assert '"custom-e9-lkv"' in data
    assert '"my-copedent-e9"' in data
    assert '"disabled_reason": "Coming soon in Backstage"' in data
    assert '"physical_position": "RKR"' in data
    assert '"physical_position": "RKL"' in data
    assert '"selected_copedent_id": "day-e9-basic"' in data
    assert payload["control_impact_preview"]["type"] == "e9-pedal-lever-impact-preview"
    assert payload["selected_copedent"]["id"] == "emmons-e9-basic"
    assert "B-to-Bb" not in [column["id"] for column in payload["selected_copedent"]["chart"]["columns"]]
    assert "B-to-Bb" not in [control["id"] for control in payload["control_impact_preview"]["controls"]]
    assert len(payload["selected_copedent"]["chart"]["rows"]) == 10
    assert payload["control_impact_preview"]["controls"][0]["string_impacts"][0]["before_note"]
    assert any(row["control_impacts"] for row in payload["positions"])
    assert "Teaching text explains the row; it does not choose the row" in data

    assert payload["query"]["display_scale_notes"]["natural_minor"] == ["G", "A", "Bb", "C", "D", "Eb", "F"]
    assert payload["query"]["display_scale_notes"]["natural_minor"] != ["G", "A", "A#", "C", "D", "D#", "F"]
    assert "five_eight_branch" in payload["query"]["harmony_types"]
    assert "five_eight_branch" in payload["filters"]["available_harmony_types"]
    assert "5-8" in payload["query"]["string_groups"]
    assert any(row["harmony_type"] == "five_eight_branch" and row["string_group"] == "5-8" for row in payload["positions"])
    assert any("validated E9 pitch logic" in row["explanation_summary"] for row in payload["positions"])
    assert any("Teaching text explains the row" in row["explanation_summary"] for row in payload["positions"])
    assert payloads["C"]["query"]["display_scale_notes"]["natural_minor"] == ["C", "D", "Eb", "F", "G", "Ab", "Bb"]
    assert payloads["Db"]["query"]["display_scale_notes"]["major"] == ["Db", "Eb", "F", "Gb", "Ab", "Bb", "C"]
    assert payloads["Bb"]["query"]["display_scale_notes"]["major"] == ["Bb", "C", "D", "Eb", "F", "G", "A"]
    assert payloads["Eb"]["query"]["display_scale_notes"]["major"] == ["Eb", "F", "G", "Ab", "Bb", "C", "D"]
    assert any(row["string_group"] == "5-7-8" and row["harmony_type"] == "advanced_pocket" for row in payload["positions"])
    assert any(row.get("warnings") for row in payload["positions"])
    assert all(row["pitch_validated"] is True for row in payload["positions"])
    assert not re.search(r"\\b\\d+\\s+(?:I|ii|iii|iv|v|vi|vii)\\b", script)


def test_e9_music_rules_boundary_covers_pitch_notation_and_voicing_contract() -> None:
    script = r"""
const assert = require("node:assert/strict");
const rules = require("./ui/e9-music-rules.js");

const gMajor = ["G", "A", "B", "C", "D", "E", "F#"];
const fMajor = ["F", "G", "A", "Bb", "C", "D", "E"];
const gContext = { key: "G", scaleType: "major", scaleNotes: gMajor, notationMode: "notes", scaleSequence: gMajor };
const fContext = { key: "F", scaleType: "major", scaleNotes: fMajor, notationMode: "notes", scaleSequence: fMajor };
const resolve = (stringNumber, fret, controls = [], scaleNotes = gMajor) => rules.resolveE9Note({ stringNumber, fret, controls, scaleNotes }).finalNote;

assert.equal(resolve(3, 3), "B");
assert.equal(resolve(3, 3, ["B"]), "C");
assert.equal(resolve(5, 3, ["A"]), "E");
assert.equal(resolve(9, 3), "F");

const cOverFNotes = [4, 6, 10].map((stringNumber) => resolve(stringNumber, 3, ["A", "B"], fMajor));
assert.deepEqual(cOverFNotes, ["G", "C", "E"]);
const cOverF = rules.identifyVoicing(cOverFNotes, fContext);
assert.equal(cOverF.label, "C");
assert.equal(cOverF.functionText, "V function in F");

const fMajNo3 = rules.identifyVoicing(["E", "C", "F"], gContext);
assert.equal(fMajNo3.label, "Fmaj7(no3)");
assert.equal(fMajNo3.quality, "partial major 7");
assert.equal(fMajNo3.confidence, "medium");
assert.equal(fMajNo3.functionText, "outside the selected scale");
assert.doesNotMatch(fMajNo3.label + fMajNo3.functionText + fMajNo3.explanation, /Dominant|V7/);

const fMajNo5 = rules.identifyVoicing(["E", "A", "F"], gContext);
assert.equal(fMajNo5.label, "Fmaj7(no5)");
assert.equal(fMajNo5.quality, "partial major 7");
assert.equal(fMajNo5.confidence, "medium-high");
assert.doesNotMatch(fMajNo5.label + fMajNo5.functionText + fMajNo5.explanation, /Dominant|V7/);

const f7No5 = rules.identifyVoicing(["F", "A", "Eb"], fContext);
assert.equal(f7No5.label, "F7(no5)");
assert.equal(f7No5.quality, "partial dominant 7");
assert.match(f7No5.explanation, /partial dominant-7 grip/);
assert.doesNotMatch(f7No5.label, /maj7/);

const d7 = rules.parseChordFinderQuery("V7 in G");
assert.equal(d7.ok, true);
assert.equal(d7.label, "D7");
assert.equal(d7.quality.id, "dominant7");
assert.match(d7.message, /resolves to D7/);

const fMaj7 = rules.parseChordFinderQuery("Imaj7 in F");
assert.equal(fMaj7.ok, true);
assert.equal(fMaj7.label, "Fmaj7");
assert.equal(fMaj7.quality.id, "major7");

const cMin9 = rules.parseChordFinderQuery("Cmin9");
assert.equal(cMin9.ok, true);
assert.equal(cMin9.label, "Cm9");
assert.equal(cMin9.quality.id, "minor9");
assert.equal(rules.chordFinderQualityGate(cMin9, [0, 3, 7]), false);
assert.equal(rules.chordFinderQualityGate(cMin9, [2, 3, 10]), true);
assert.equal(rules.chordFinderConfidence(cMin9, [2, 3, 10], [0, 7]), "medium, rootless");

assert.equal(rules.chordConfidence(rules.chordQualityById("major7"), false, [4], [0, 7, 11]), "medium");
assert.equal(rules.chordConfidence(rules.chordQualityById("major7"), false, [7], [0, 4, 11]), "medium-high");
assert.equal(rules.gripTierLabel("5-6-9"), "Extended grip");
assert.equal(rules.intervalRoleLabel(10), "flat 7");
assert.equal(rules.intervalRoleLabel(11), "major 7th");

assert.equal(rules.notationLabelForFinalNote("B", "", { notationMode: "notes", scaleNotes: gMajor, scaleSequence: gMajor }), "B");
assert.equal(rules.notationLabelForFinalNote("B", "", { notationMode: "nns", scaleNotes: gMajor, scaleSequence: rules.MAJOR_SCALE_SEQUENCES.nns }), "3-");
assert.equal(rules.notationLabelForFinalNote("B", "", { notationMode: "roman", scaleNotes: gMajor, scaleSequence: rules.MAJOR_SCALE_SEQUENCES.roman }), "iii");
assert.equal(rules.notationLabelForFinalNote("B", "", { notationMode: "numbers", scaleNotes: gMajor, scaleSequence: rules.MAJOR_SCALE_SEQUENCES.numbers }), "3m");
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


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
    { value: "day-e9-basic", text: "Day E9" },
    { value: "custom-e9-lkv", text: "Custom E9 (with LKV)" },
    { value: "my-copedent-e9", text: "My Copedent (E9) - Coming soon in Backstage" }
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
    { value: "two_string", text: "Two-string" },
    { value: "all", text: "All practical" }
  ]),
  "explorer-grip-vocabulary-control": new FakeNode("explorer-grip-vocabulary-control"),
  "explorer-string-group": new FakeSelect("explorer-string-group", "all", [{ value: "all", text: "All 3-string groups" }]),
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
assert.match(elements["explorer-copedent"].innerHTML, /Custom E9 \(with LKV\)/);
assert.match(elements["explorer-copedent"].innerHTML, /My Copedent \(E9\) - Coming soon in Backstage/);
assert.match(elements["explorer-copedent"].innerHTML, /value="my-copedent-e9"[^>]*disabled/);
assert.equal(elements["explorer-copedent"].value, "emmons-e9-basic");
assert.match(elements["explorer-string-group"].innerHTML, /All core grips/);
assert.match(elements["explorer-string-group"].innerHTML, /Core grips/);
assert.match(elements["explorer-string-group"].innerHTML, /5-6-7/);
assert.match(elements["explorer-string-group"].innerHTML, /6-7-10/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /5-7-8/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, />3-5</);
assert.equal(elements["explorer-explore-mode"].value, "single");
assert.equal(elements["explorer-string-group-control"].hidden, false);
assert.equal(elements["explorer-path-family-control"].hidden, true);
assert.equal(elements["explorer-harmony-control"].hidden, false);
assert.equal(elements["explorer-harmony-control"].getAttribute("aria-hidden"), "false");
assert.equal(elements["explorer-harmony"].disabled, false);
assert.equal(elements["explorer-grip-vocabulary-control"].hidden, false);
assert.equal(elements["explorer-grip-vocabulary"].disabled, false);
elements["explorer-grip-vocabulary"].value = "extended";
elements["explorer-grip-vocabulary"].dispatchChange();
assert.match(elements["explorer-string-group"].innerHTML, /All extended grips/);
assert.match(elements["explorer-string-group"].innerHTML, /Extended grips/);
assert.match(elements["explorer-string-group"].innerHTML, /4-6-10/);
assert.match(elements["explorer-string-group"].innerHTML, /3-5-8/);
assert.match(elements["explorer-string-group"].innerHTML, /5-6-9/);
assert.match(elements["explorer-string-group"].innerHTML, /4-6-9/);
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
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "emphasizeStringGroups"), false);
assert.equal(Object.prototype.hasOwnProperty.call(lastMount.options, "selectedStringGroups"), false);
assert.equal(lastMount.options.positions.length > 0, true);
assert.equal(lastMount.options.positions.some((row) => /^[A-G][b#]?$/.test(row.label) || /^[A-G][b#]?, [A-G][b#]?$/.test(row.label)), true);
assert.equal(lastMount.options.positions.some((row) => Array.isArray(row.labelValues) && row.labelValues.length > 1 && row.label.includes(", ")), true);
assert.equal(lastMount.options.positions.every((row) => !/^[A-G][b#]?\+$/.test(row.label)), true);
const markerPosition = (id) => lastMount.options.positions.find((row) => row.id === id);
const g345Fret3Marker = () => markerPosition("marker:3:3-4-5:3-4-5");
const g345Fret10Marker = () => markerPosition("marker:10:3-4-5:3-4-5");
assert.equal(g345Fret3Marker().label, "B, C");
assert.equal(JSON.stringify(Array.from(g345Fret3Marker().labelValues)), JSON.stringify(["B", "C"]));
assert.equal(g345Fret10Marker().label, "F#, G");
assert.equal(JSON.stringify(Array.from(g345Fret10Marker().labelValues)), JSON.stringify(["F#", "G"]));
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
assert.match(elements["explorer-control-impact-preview"].textContent, /Emmons E9/);
assert.match(elements["explorer-control-impact-preview"].textContent, /Showing Notes notation/);
assert.match(elements["explorer-control-impact-preview"].textContent, /A pedal/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /data-control-impact-tab="A"/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /String 5/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /raises 2 semitones/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /B-to-Bb vertical/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /\[object Object\]/);
assert.match(elements["explorer-control-impact-preview"].textContent, /A pedal/);
let impactButtons = elements["explorer-control-impact-preview"].querySelectorAll("[data-control-impact-tab]");
impactButtons.find((button) => button.getAttribute("data-control-impact-tab") === "A").onclick();
impactButtons = elements["explorer-control-impact-preview"].querySelectorAll("[data-control-impact-tab]");
impactButtons.find((button) => button.getAttribute("data-control-impact-tab") === "B").onclick();
assert.match(elements["explorer-control-impact-preview"].textContent, /Previewing A pedal \+ B pedal/);
assert.match(elements["explorer-control-impact-preview"].textContent, /String 5/);
assert.match(elements["explorer-control-impact-preview"].textContent, /String 6/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /aria-pressed="true"[^>]*data-control-impact-tab="A"/);
assert.match(elements["explorer-control-impact-preview"].innerHTML, /aria-pressed="true"[^>]*data-control-impact-tab="B"/);
elements["explorer-control-impact-preview"].querySelector("[data-control-impact-clear]").onclick();
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /String 5/);
assert.match(elements["explorer-active-results"].textContent, /all 3-string groups/);
assert.match(elements["explorer-active-results"].textContent, /Top note:/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Marker \d|Marker \+\d/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Fretboard \d|Fretboard \d\+/);
assert.match(elements["explorer-active-results"].innerHTML, /data-marker-id=/);
assert.match(elements["explorer-active-results"].innerHTML, /data-marker-tone=/);
assert.equal(elements["explorer-active-results"].querySelectorAll("[data-active-result-row]").length > lastMount.options.positions.length, true);
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
elements["explorer-chord-quality"].value = "dominant7";
elements["explorer-chord-quality"].dispatchChange();
assert.match(elements["explorer-chord-finder"].textContent, /Target: D7/);
assert.doesNotMatch(elements["explorer-active-results"].textContent, /Fmaj7/);
assert.equal(lastMount.options.positions.length > 1, true);
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
assert.equal(g345Fret3Marker().label, "3-, 4");
assert.equal(JSON.stringify(Array.from(g345Fret3Marker().labelValues)), JSON.stringify(["3-", "4"]));
assert.equal(g345Fret10Marker().label, "7°, 1");
assert.equal(JSON.stringify(Array.from(g345Fret10Marker().labelValues)), JSON.stringify(["7°", "1"]));
assert.equal(lastMount.options.positions.some((row) => /^(1|2-|3-|4|5|6-|7°)(, (1|2-|3-|4|5|6-|7°))*$/.test(row.label)), true);
assert.equal(lastMount.options.positions.every((row) => row.label !== "3+"), true);
assert.equal(lastMount.options.positions.every((row) => row.label !== "3, 3-"), true);
assert.match(elements["explorer-control-impact-preview"].textContent, /Showing NNS notation/);
notationModeButtons[2].onclick();
assert.match(elements["explorer-scale-notes"].textContent, /I - ii - iii - IV - V - vi - vii°/);
assert.equal(JSON.stringify(topFilterValues()), JSON.stringify(["all", "I", "ii", "iii", "IV", "V", "vi", "vii°"]));
assert.match(elements["explorer-active-results"].textContent, /Top note interval: (I|iii|V)/);
assert.equal(g345Fret3Marker().label, "iii, IV");
assert.equal(JSON.stringify(Array.from(g345Fret3Marker().labelValues)), JSON.stringify(["iii", "IV"]));
assert.equal(g345Fret10Marker().label, "vii°, I");
assert.equal(JSON.stringify(Array.from(g345Fret10Marker().labelValues)), JSON.stringify(["vii°", "I"]));
assert.equal(lastMount.options.positions.some((row) => /^(I|ii|iii|IV|V|vi|vii°)(, (I|ii|iii|IV|V|vi|vii°))*$/.test(row.label)), true);
notationModeButtons[3].onclick();
assert.match(elements["explorer-scale-notes"].textContent, /1 - 2m - 3m - 4 - 5 - 6m - 7dim/);
assert.equal(JSON.stringify(topFilterValues()), JSON.stringify(["all", "1", "2m", "3m", "4", "5", "6m", "7dim"]));
assert.match(elements["explorer-active-results"].textContent, /Top note interval: (1|3m|5)/);
assert.equal(g345Fret3Marker().label, "3m, 4");
assert.equal(JSON.stringify(Array.from(g345Fret3Marker().labelValues)), JSON.stringify(["3m", "4"]));
assert.equal(g345Fret10Marker().label, "7dim, 1");
assert.equal(JSON.stringify(Array.from(g345Fret10Marker().labelValues)), JSON.stringify(["7dim", "1"]));
assert.equal(lastMount.options.positions.some((row) => /^(1|2m|3m|4|5|6m|7dim)(, (1|2m|3m|4|5|6m|7dim))*$/.test(row.label)), true);
notationModeButtons[0].onclick();
assert.equal(lastMount.options.positions.some((row) => /^[A-G][b#]?$/.test(row.label) || /^[A-G][b#]?, [A-G][b#]?$/.test(row.label)), true);
assert.equal(g345Fret3Marker().label, "B, C");
assert.match(elements["explorer-active-results"].innerHTML, /Top note:/);
assert.match(elements["explorer-active-results"].innerHTML, /<strong>Top note: (G|B|D)/);
notationModeButtons[1].onclick();
assert.equal(g345Fret3Marker().label, "3-, 4");
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
assert.match(elements["explorer-note-finder"].textContent, /Find all/);
assert.match(elements["explorer-note-finder"].textContent, /All strings/);
noteTargetButtons().find((button) => button.getAttribute("data-note-target") === "2").onclick();
assert.equal(noteCell(3, 3).getAttribute("data-note-result"), "3:3");
noteControlButtons().find((button) => button.getAttribute("data-note-control-state") === "B").onclick();
assert.equal(noteCell(3, 3).getAttribute("data-note-result"), null);
assert.match(elements["explorer-selected-detail"].textContent, /String 3, fret 3: C/);
assert.match(elements["explorer-selected-detail"].textContent, /Open note at fretB/);
assert.match(elements["explorer-selected-detail"].textContent, /Final noteC/);
assert.match(elements["explorer-selected-detail"].textContent, /B pedal raises this string from B to C/);
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
assert.deepEqual(noteGripVocabularyButtons().map((button) => button.getAttribute("data-note-grip-vocabulary")), ["core", "extended", "two_string", "all"]);
assert.ok(noteGripButtons().length > 0);
noteGripButtons()[0].onclick();
assert.match(elements["explorer-selected-detail"].textContent, /Single-note finder/);
noteGripVocabularyButtons().find((button) => button.getAttribute("data-note-grip-vocabulary") === "extended").onclick();
assert.match(elements["explorer-note-finder"].textContent, /Dominant 7 \/ V7/);
assert.match(elements["explorer-note-finder"].textContent, /D7|V7|5\^7|Dominant 7/);
assert.deepEqual(noteGripRoleButtons().map((button) => button.getAttribute("data-note-grip-role")), ["all", "melody_harmony", "pad_sustain", "chord_voicing", "dominant_color", "bass_root_support", "passing_color"]);
noteGripRoleButtons().find((button) => button.getAttribute("data-note-grip-role") === "dominant_color").onclick();
assert.match(elements["explorer-note-finder"].textContent, /5-6-9|4-6-9|6-9|5-9|Dominant color/);
assert.ok(noteGripButtons().length > 0);
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
assert.match(elements["explorer-voicing-identifier"].textContent, /G major/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Fret 3; strings 3-4-5; Open; notes B, G, D/);
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
assert.deepEqual(voicingControlButtons().map((button) => button.getAttribute("data-voicing-control")), ["A", "B", "C", "E-raise", "E-lower", "D-lower", "G-lower"]);
assert.equal(voicingControlButtons().some((button) => button.getAttribute("data-voicing-control") === "AB"), false);
assert.equal(voicingControlButtons().some((button) => button.getAttribute("data-voicing-control") === "BC"), false);
voicingControlButtons().find((button) => button.getAttribute("data-voicing-control") === "B").onclick();
voicingControlButtons().find((button) => button.getAttribute("data-voicing-control") === "C").onclick();
assert.match(elements["explorer-voicing-identifier"].textContent, /Fret 3; strings 3-4-5; B pedal \+ C pedal; notes C, A, E/);
assert.match(elements["explorer-selected-detail"].textContent, /Am/);
assert.match(elements["explorer-selected-detail"].textContent, /Likely functionii function in G/);
assert.match(elements["explorer-selected-detail"].textContent, /selecting B pedal and C pedal individually/);
assert.equal(lastMount.options.positions[0].notes.join(","), "C,A,E");
voicingClearButtons()[0].onclick();
elements["explorer-key"].value = "F";
elements["explorer-key"].dispatchChange();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "3").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "5").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "6").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "10").onclick();
voicingControlButtons().find((button) => button.getAttribute("data-voicing-control") === "A").onclick();
voicingControlButtons().find((button) => button.getAttribute("data-voicing-control") === "B").onclick();
assert.match(elements["explorer-voicing-identifier"].textContent, /F major/);
assert.match(elements["explorer-voicing-identifier"].textContent, /Fret 3; strings 4-6-10; A pedal \+ B pedal; notes G, C, E/);
assert.match(elements["explorer-selected-detail"].textContent, /C/);
assert.match(elements["explorer-selected-detail"].textContent, /Likely functionV function in F/);
assert.equal(lastMount.options.positions[0].grip, "4-6-10");
assert.equal(lastMount.options.positions[0].notes.join(","), "G,C,E");
voicingClearButtons()[0].onclick();
elements["explorer-key"].value = "G";
elements["explorer-key"].dispatchChange();
elements["explorer-voicing-fret"].value = "10";
elements["explorer-voicing-fret"].dispatchChange();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "10").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "5").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "9").onclick();
assert.match(elements["explorer-voicing-identifier"].textContent, /D7/);
assert.match(elements["explorer-selected-detail"].textContent, /Likely functionV7 in G/);
assert.match(elements["explorer-selected-detail"].textContent, /Dominant 7 \/ V7 grip/);
assert.equal(lastMount.options.positions[0].grip, "4-5-6-9");
assert.equal(lastMount.options.positions[0].notes.join(","), "D,A,F#,C");
voicingClearButtons()[0].onclick();

elements["explorer-voicing-fret"].value = "3";
elements["explorer-voicing-fret"].dispatchChange();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "4").onclick();
voicingControlButtons().find((button) => button.getAttribute("data-voicing-control") === "A").onclick();
voicingControlButtons().find((button) => button.getAttribute("data-voicing-control") === "B").onclick();
assert.match(elements["explorer-voicing-identifier"].textContent, /Fret 3; strings 5-6-9; A pedal \+ B pedal; notes E, C, F/);
assert.match(elements["explorer-selected-detail"].textContent, /Fmaj7\(no3\)/);
assert.match(elements["explorer-selected-detail"].textContent, /partial major-7 grip/);
assert.match(elements["explorer-selected-detail"].textContent, /Omitted tones3/);
assert.match(elements["explorer-selected-detail"].textContent, /Confidencemedium/);
assert.match(elements["explorer-selected-detail"].textContent, /Likely functionoutside the selected scale/);
assert.match(elements["explorer-selected-detail"].textContent, /Selected-key note labels/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /Intervals against key/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /Dominant 7|V7 in G/);
assert.equal(lastMount.options.positions[0].notes.join(","), "E,C,F");

voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "6").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "7").onclick();
assert.match(elements["explorer-voicing-identifier"].textContent, /Fret 3; strings 5-7-9; A pedal \+ B pedal; notes E, A, F/);
assert.match(elements["explorer-selected-detail"].textContent, /Fmaj7\(no5\)/);
assert.match(elements["explorer-selected-detail"].textContent, /Omitted tones5/);
assert.match(elements["explorer-selected-detail"].textContent, /Confidencemedium-high/);
assert.match(elements["explorer-selected-detail"].textContent, /not a common musical grip/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /Dominant 7|V7 in G/);

voicingClearButtons()[0].onclick();
elements["explorer-key"].value = "F";
elements["explorer-key"].dispatchChange();
elements["explorer-voicing-fret"].value = "1";
elements["explorer-voicing-fret"].dispatchChange();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "5").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "7").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "3").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "4").onclick();
assert.match(elements["explorer-voicing-identifier"].textContent, /Fret 1; strings 3-4-9; Open; notes A, F, D#/);
assert.match(elements["explorer-selected-detail"].textContent, /F7\(no5\)/);
assert.match(elements["explorer-selected-detail"].textContent, /partial dominant-7 grip/);
assert.match(elements["explorer-selected-detail"].textContent, /Intervals in voicing3, 1, ♭7/);
assert.match(elements["explorer-selected-detail"].textContent, /Omitted tones5/);
assert.doesNotMatch(elements["explorer-selected-detail"].textContent, /Fmaj7/);

elements["explorer-key"].value = "G";
elements["explorer-key"].dispatchChange();
elements["explorer-voicing-fret"].value = "3";
elements["explorer-voicing-fret"].dispatchChange();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "3").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "4").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "9").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "1").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "2").onclick();
voicingStringButtons().find((button) => button.getAttribute("data-voicing-string") === "3").onclick();
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
assert.match(elements["explorer-control-impact-preview"].textContent, /Day E9/);
assert.match(elements["explorer-control-impact-preview"].textContent, /C pedal/);
assert.match(elements["explorer-control-impact-preview"].textContent, /A pedal/);
assert.doesNotMatch(elements["explorer-copedent-chart"].textContent, /\[object Object\]/);
assert.doesNotMatch(elements["explorer-control-impact-preview"].textContent, /\[object Object\]/);
elements["explorer-copedent"].value = "custom-e9-lkv";
elements["explorer-copedent"].dispatchChange();
assert.match(elements["explorer-copedent-chart"].textContent, /Custom E9 \(with LKV\)/);
assert.match(elements["explorer-copedent-chart"].textContent, /B-to-Bb vertical/);
assert.match(elements["explorer-control-impact-preview"].textContent, /Custom E9 \(with LKV\)/);
assert.match(elements["explorer-control-impact-preview"].textContent, /B-to-Bb vertical/);
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
assert.match(elements["explorer-active-results"].textContent, /visible positions/);
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


def test_frontend_answer_client_formats_sectioned_and_bullet_text() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const code = fs.readFileSync("ui/answer-client.js", "utf8");
const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const answerUi = vm.runInContext("STEEL_RAG_ANSWER_UI", sandbox);

const formatted = answerUi.normalizeAnswerResponse({
  answer: [
    "Direct answer: Check the ground path before replacing parts.",
    "",
    "Practical answer:",
    "1. Try a different cable.",
    "2. Bypass the volume pedal.",
    "",
    "Caveat: Do not replace the pickup from this evidence alone.",
    "- [1] current phpBB, Electronics: Raw source context should stay out of the answer panel"
  ].join("\n"),
  sources: []
});

assert.equal(formatted.sections[0].title, "Direct answer");
assert.equal(formatted.sections[0].style, "lead");
assert.equal(formatted.sections[0].body, "Check the ground path before replacing parts.");
assert.equal(formatted.sections[1].title, "Practical answer");
assert.equal(
  JSON.stringify(formatted.sections[1].bullets),
  JSON.stringify(["Try a different cable.", "Bypass the volume pedal."])
);
assert.equal(formatted.sections[1].ordered, true);
assert.equal(formatted.sections[2].title, "Caveat");
assert.equal(formatted.sections[2].style, "caveat");
assert.equal(formatted.sections[2].body, "Do not replace the pickup from this evidence alone.");
assert.equal(JSON.stringify(formatted.sections).includes("Raw source context"), false);
assert.equal(JSON.stringify(formatted.sources), JSON.stringify([]));

const sourced = answerUi.normalizeAnswerResponse({
  answer: "Direct answer: Source cards should still render below.",
  sources: [
    {
      forumName: "Electronics",
      title: "Grounding a pedal steel",
      excerpt: "Touching the changer can change the ground reference.",
      url: "https://bb.steelguitarforum.com/viewtopic.php?t=123"
    }
  ]
});

assert.equal(JSON.stringify(sourced.sources[0]), JSON.stringify({
  forum: "Electronics",
  title: "Grounding a pedal steel",
  excerpt: "Touching the changer can change the ground reference.",
  url: "https://bb.steelguitarforum.com/viewtopic.php?t=123",
  date: ""
}));
assert.equal("fretboard" in sourced, false);

const visualized = answerUi.normalizeAnswerResponse({
  question: "Show me G major positions.",
  answer: "Use a few nearby grips.",
  fretboard: {
    description: "Three common G major locations.",
    maxFret: 24,
    stringCount: 10,
    tuningLabels: ["F#", "D#", "G#", "E", "B", "G#", "F#", "E", "D", "B"],
    positions: [
      {
        id: "g-open-3",
        label: "G major",
        fret: 3,
        strings: [4, 5, 6],
        grip: [4, 5, 6],
        role: "No pedals",
        notes: "Open G pocket"
      }
    ],
    legend: [
      { id: "primary", label: "Open/no-pedal position", color: "primary" }
    ],
    query: {
      display_scale_notes: {
        natural_minor: ["G", "A", "Bb", "C", "D", "Eb", "F"]
      }
    }
  },
  sources: []
});
assert.equal(visualized.fretboard.title, "Fretboard view");
assert.equal(visualized.fretboard.description, "Three common G major locations.");
assert.equal(visualized.fretboard.maxFret, 24);
assert.equal(visualized.fretboard.stringCount, 10);
assert.equal(JSON.stringify(visualized.fretboard.tuningLabels), JSON.stringify(["F#", "D#", "G#", "E", "B", "G#", "F#", "E", "D", "B"]));
assert.equal(visualized.fretboard.positions[0].id, "g-open-3");
assert.equal(visualized.fretboard.positions[0].notes, "Open G pocket");
assert.equal(JSON.stringify(visualized.fretboard.highlights), JSON.stringify([]));
assert.equal(visualized.fretboard.legend[0].id, "primary");
assert.equal(visualized.fretboard.query.display_scale_notes.natural_minor.join(" "), "G A Bb C D Eb F");

const productionNestedVisualized = answerUi.normalizeAnswerResponse({
  question: "Where can I play a G chord?",
  answer: "Use G at frets 3, 6, and 10.",
  response: {
    fretboard: {
      title: "G major positions",
      description: "Production-like nested response payload.",
      positions: [
        {
          id: "g-open-3",
          label: "G major",
          fret: 3,
          strings: [4, 5, 6],
          grip: "4-5-6"
        }
      ]
    }
  },
  sources: []
});
assert.equal(productionNestedVisualized.fretboard.title, "G major positions");
assert.equal(productionNestedVisualized.fretboard.positions[0].id, "g-open-3");

const nestedShapes = [
  ["response", { response: { fretboard: { positions: [{ id: "from-response", fret: 3, strings: [4, 5, 6] }] } } }],
  ["data", { data: { fretboard: { positions: [{ id: "from-data", fret: 6, strings: [4, 5, 6] }] } } }],
  ["result", { result: { fretboard: { positions: [{ id: "from-result", fret: 10, strings: [4, 5, 6] }] } } }],
  ["answer", { answer: { text: "Nested object answer.", fretboard: { positions: [{ id: "from-answer", fret: 12, strings: [4, 5, 6] }] } } }]
];
for (const [name, payload] of nestedShapes) {
  const normalized = answerUi.normalizeAnswerResponse({
    question: `Nested ${name}`,
    answer_text: "Nested fretboard data should survive.",
    ...payload
  });
  assert.equal(normalized.fretboard.positions[0].id, `from-${name}`);
}

const emptyVisualized = answerUi.normalizeAnswerResponse({
  answer: "No supported fretboard data.",
  fretboard: {
    title: "Empty view",
    positions: [],
    highlights: []
  },
  sources: []
});
assert.equal("fretboard" in emptyVisualized, false);

const positionsWinVisualized = answerUi.normalizeAnswerResponse({
  question: "Where can I play a G chord?",
  answer: "Use the contract positions, not stale legacy highlights.",
  fretboard: {
    title: "G major positions on E9",
    description: "Contract positions should be primary.",
    positions: [
      {
        id: "g-open-3",
        label: "G major",
        fret: 3,
        strings: [4, 5, 6],
        grip: "4-5-6",
        pedals: [],
        levers: []
      },
      {
        id: "g-af-6",
        label: "G major",
        fret: 6,
        strings: [4, 5, 6],
        grip: "4-5-6",
        pedals: ["A"],
        levers: ["F"]
      },
      {
        id: "g-ab-10",
        label: "G major",
        fret: 10,
        strings: [4, 5, 6],
        grip: "4-5-6",
        pedals: ["A", "B"],
        levers: []
      }
    ],
    highlights: [
      {
        id: "wrong-legacy-ab-6",
        label: "Wrong legacy A+B",
        fret: 6,
        strings: [4, 5, 6],
        pedals: ["A", "B"]
      }
    ]
  },
  sources: []
});
assert.equal(positionsWinVisualized.fretboard.positions.length, 3);
assert.equal(JSON.stringify(positionsWinVisualized.fretboard.positions.map((item) => item.id)), JSON.stringify(["g-open-3", "g-af-6", "g-ab-10"]));
assert.equal(JSON.stringify(positionsWinVisualized.fretboard.positions.map((item) => item.fret)), JSON.stringify([3, 6, 10]));
assert.equal(positionsWinVisualized.fretboard.highlights[0].id, "wrong-legacy-ab-6");

const legacyVisualized = answerUi.normalizeAnswerResponse({
  question: "Show me legacy positions.",
  answer: "Legacy fallback still works.",
  fretboard: {
    highlights: [
      {
        id: "legacy-open-3",
        label: "Legacy G major",
        fret: 3,
        strings: [4, 5, 6],
        role: "Legacy no pedals"
      }
    ]
  },
  sources: []
});
assert.equal("positions" in legacyVisualized.fretboard, false);
assert.equal(legacyVisualized.fretboard.highlights[0].id, "legacy-open-3");

const vendorFormatted = answerUi.normalizeAnswerResponse({
  answer: [
    "Best places to check",
    "",
    "- Steel Guitar Shopper — https://steelguitarshopper.com/accessories/ — Steel guitar accessories.",
    "- BJS Steel Guitar Bars — https://www.bjsbars.com/ — Dedicated steel guitar bar maker.",
    "- Jim Dunlop Tonebars — https://www.jimdunlop.com/products/accessories/slides-tonebars/tonebars/ — Mainstream tonebar options.",
    "- Steel Guitar Forum Classifieds / Forum Store — https://bb.steelguitarforum.com/viewforum.php?f=9 — Used/classifieds path.",
    "",
    "What to choose",
    "",
    "- Diameter",
    "- Length",
    "- Weight",
    "- Material",
    "- Pedal steel round tone bar vs. lap/dobro slide style",
    "",
    "Check current availability before assuming anything is in stock."
  ].join("\n"),
  sources: []
});

assert.equal(vendorFormatted.sections[0].title, "Best places to check");
assert.equal(vendorFormatted.sections[0].style, "bullets");
assert.equal(vendorFormatted.sections[0].bullets.length, 4);
assert.equal(vendorFormatted.sections[1].title, "What to choose");
assert.equal(vendorFormatted.sections[1].bullets.length, 5);
assert.equal(vendorFormatted.sections[1].body, "Check current availability before assuming anything is in stock.");
assert.equal(JSON.stringify(vendorFormatted.sections).includes("Practical answer"), false);

const afFormatted = answerUi.normalizeAnswerResponse({
  answer: [
    "On standard E9, A+F means using the A pedal with the F lever to make a major-chord position three frets above the open major position.",
    "",
    "What changes",
    "",
    "- The A pedal raises the B strings to C#.",
    "- The F lever raises the E strings to F.",
    "- Together they give a major triad in the A+F position.",
    "",
    "Practical use",
    "",
    "- Use it to connect major chords smoothly without jumping straight to the A+B position.",
    "- Example: G major is available at the 6th fret with A pedal + F lever."
  ].join("\n"),
  sources: []
});

assert.equal(afFormatted.sections[0].title, "Answer");
assert.equal(afFormatted.sections[0].body, "On standard E9, A+F means using the A pedal with the F lever to make a major-chord position three frets above the open major position.");
assert.equal(afFormatted.sections[1].title, "What changes");
assert.equal(afFormatted.sections[1].bullets.length, 3);
assert.equal(afFormatted.sections[2].title, "Practical use");
assert.equal(afFormatted.sections[2].bullets.length, 2);
assert.equal(JSON.stringify(afFormatted.sections).includes("Practical answer"), false);

const bcFormatted = answerUi.normalizeAnswerResponse({
  answer: [
    "Practice plan",
    "",
    "- Start with B+C down at one fret.",
    "- Pick strings 4, 5, and 6 slowly.",
    "",
    "Diagnostic path",
    "",
    "- Listen for the C pedal raise.",
    "- Release cleanly before moving."
  ].join("\n"),
  sources: []
});

assert.equal(bcFormatted.sections[0].title, "Practice plan");
assert.equal(bcFormatted.sections[0].bullets.length, 2);
assert.equal(bcFormatted.sections[1].title, "Diagnostic path");
assert.equal(bcFormatted.sections[1].bullets.length, 2);
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_frontend_answer_client_formats_private_copedent_markdown_tables() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const code = fs.readFileSync("ui/answer-client.js", "utf8");
const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const answerUi = vm.runInContext("STEEL_RAG_ANSWER_UI", sandbox);

const formatted = answerUi.normalizeAnswerResponse({
  answer: [
    "Your private profile describes a 10-string E9 setup.",
    "",
    "Open tuning",
    "",
    "| String | Note |",
    "| --- | --- |",
    "| 1 | F# |",
    "| 2 | D# |",
    "",
    "Pedals",
    "",
    "| Pedal | Change |",
    "| --- | --- |",
    "| A | raises strings 5 and 10 B to C# |",
    "",
    "Levers",
    "",
    "| Lever | Change |",
    "| --- | --- |",
    "| F lever | raises strings 4 and 8 E to F |",
    "| E-lower | lowers strings 4 and 8 E to D# |",
    "| RKL | raises string 1 F# to G/G#, raises string 2 D# to E, lowers string 6 G# to F# |",
    "| RKR | lowers string 2 D# to D/C#, lowers string 9 D to C# |",
    "",
    "Common grips",
    "- 3-4-5",
    "- 4-5-6",
    "- 5-6-8",
    "- 6-8-10"
  ].join("\n"),
  sources: []
});

const openTuning = formatted.sections.find((section) => section.title === "Open tuning");
const pedals = formatted.sections.find((section) => section.title === "Pedals");
const levers = formatted.sections.find((section) => section.title === "Levers");
const commonGrips = formatted.sections.find((section) => section.title === "Common grips");
const sectionOrder = formatted.sections.map((section) => section.title);

assert.equal(formatted.sections[0].title, "Answer");
assert.equal(formatted.sections[0].body, "Your private profile describes a 10-string E9 setup.");
assert.equal(JSON.stringify(sectionOrder), JSON.stringify(["Answer", "Open tuning", "Pedals", "Levers", "Common grips"]));
assert.equal(JSON.stringify(sectionOrder.slice(1)), JSON.stringify(["Open tuning", "Pedals", "Levers", "Common grips"]));
assert.equal(JSON.stringify(openTuning.tables[0].headers), JSON.stringify(["String", "Note"]));
assert.equal(JSON.stringify(openTuning.tables[0].rows), JSON.stringify([["1", "F#"], ["2", "D#"]]));
assert.equal(JSON.stringify(pedals.tables[0].headers), JSON.stringify(["Pedal", "Change"]));
assert.equal(JSON.stringify(pedals.tables[0].rows), JSON.stringify([["A", "raises strings 5 and 10 B to C#"]]));
assert.equal(JSON.stringify(levers.tables[0].headers), JSON.stringify(["Lever", "Change"]));
assert.equal(JSON.stringify(levers.tables[0].rows), JSON.stringify([
  ["F lever", "raises strings 4 and 8 E to F"],
  ["E-lower", "lowers strings 4 and 8 E to D#"],
  ["RKL", "raises string 1 F# to G/G#, raises string 2 D# to E, lowers string 6 G# to F#"],
  ["RKR", "lowers string 2 D# to D/C#, lowers string 9 D to C#"]
]));
assert.equal(JSON.stringify(levers.bullets), JSON.stringify([]));
assert.equal(JSON.stringify(commonGrips.bullets), JSON.stringify(["3-4-5", "4-5-6", "5-6-8", "6-8-10"]));
assert.equal(levers.blocks[0].type, "table");
assert.equal(commonGrips.blocks[0].type, "bullets");
assert.equal(JSON.stringify(commonGrips.blocks[0].items), JSON.stringify(["3-4-5", "4-5-6", "5-6-8", "6-8-10"]));
assert.equal(JSON.stringify(levers).includes("3-4-5"), false);
assert.equal(JSON.stringify(formatted.sections).includes("| --- |"), false);

const sectionPayload = answerUi.normalizeAnswerResponse({
  sections: [
    {
      title: "Answer",
      style: "lead",
      body: [
        "Your private profile describes a 10-string E9 setup.",
        "",
        "Open tuning",
        "",
        "| String | Note |",
        "| --- | --- |",
        "| 1 | F# |",
        "| 2 | D# |"
      ].join("\n")
    }
  ],
  sources: []
});

const sectionOpenTuning = sectionPayload.sections.find((section) => section.title === "Open tuning");
assert.equal(sectionPayload.sections[0].body, "Your private profile describes a 10-string E9 setup.");
assert.equal(JSON.stringify(sectionOpenTuning.tables[0].headers), JSON.stringify(["String", "Note"]));
assert.equal(JSON.stringify(sectionOpenTuning.tables[0].rows), JSON.stringify([["1", "F#"], ["2", "D#"]]));
assert.equal(JSON.stringify(sectionPayload.sections).includes("| String | Note |"), false);
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_answer_ui_renders_private_copedent_sections_in_dom_order() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const clientCode = fs.readFileSync("ui/answer-client.js", "utf8");
const html = fs.readFileSync("ui/steel-guitar-rag-mock.html", "utf8");
const inlineScript = html.match(/<script>\n([\s\S]*)\n  <\/script>/)[1];

const COPEDENT_ANSWER = [
  "Your private profile describes a 10-string E9 setup.",
  "",
  "Open tuning",
  "| String | Note |",
  "| --- | --- |",
  "| 1 | F# |",
  "| 2 | D# |",
  "",
  "Pedals",
  "| Pedal | Change |",
  "| --- | --- |",
  "| A | raises strings 5 and 10 B to C# |",
  "",
  "Levers",
  "| Lever | Change |",
  "| --- | --- |",
  "| F lever | raises strings 4 and 8 E to F |",
  "| E-lower | lowers strings 4 and 8 E to D# |",
  "| RKL | raises string 1 F# to G/G#, raises string 2 D# to E, lowers string 6 G# to F# |",
  "| RKR | lowers string 2 D# to D/C#, lowers string 9 D to C# |",
  "",
  "Common grips",
  "- 3-4-5",
  "- 4-5-6",
  "- 5-6-8",
  "- 6-8-10"
].join("\n");

function makeClassList(element) {
  const values = new Set(String(element.className || "").split(/\s+/).filter(Boolean));
  function sync() {
    element.className = Array.from(values).join(" ");
  }
  return {
    add(...names) {
      names.forEach((name) => values.add(name));
      sync();
    },
    remove(...names) {
      names.forEach((name) => values.delete(name));
      sync();
    },
    toggle(name, force) {
      const shouldAdd = force === undefined ? !values.has(name) : Boolean(force);
      if (shouldAdd) values.add(name);
      else values.delete(name);
      sync();
      return shouldAdd;
    },
    contains(name) {
      return values.has(name);
    }
  };
}

function makeTextNode(text) {
  return { tagName: "#TEXT", textContent: String(text), children: [] };
}

function makeElement(selector = "", tagName = "div") {
  const element = {
    selector,
    tagName: tagName.toUpperCase(),
    id: selector.startsWith("#") ? selector.slice(1) : "",
    className: selector.startsWith(".") ? selector.slice(1) : "",
    value: "",
    checked: false,
    hidden: false,
    disabled: false,
    tabIndex: 0,
    dataset: {},
    attributes: {},
    children: [],
    parentNode: null,
    _textContent: "",
    set textContent(value) {
      this._textContent = String(value ?? "");
      this.children = [];
    },
    get textContent() {
      return this._textContent + this.children.map((child) => child.textContent || "").join("");
    },
    set innerHTML(_value) {
      this.children = [];
      this._textContent = "";
    },
    get innerHTML() {
      return this.textContent;
    },
    get lastChild() {
      if (!this.children.length) {
        this.appendChild(makeTextNode(""));
      }
      return this.children[this.children.length - 1];
    },
    setAttribute(name, value) {
      this.attributes[name] = String(value);
    },
    getAttribute(name) {
      return this.attributes[name] || "";
    },
    appendChild(child) {
      child.parentNode = this;
      this.children.push(child);
      return child;
    },
    append(...nodes) {
      nodes.forEach((node) => {
        this.appendChild(typeof node === "string" ? makeTextNode(node) : node);
      });
    },
    replaceChildren(...nodes) {
      this.children = [];
      this._textContent = "";
      this.append(...nodes);
    },
    querySelector(selector) {
      return findFirst(this, selector);
    },
    querySelectorAll(selector) {
      return findAll(this, selector);
    },
    closest() {
      return null;
    },
    cloneNode() {
      const clone = makeElement("", this.tagName);
      clone.textContent = this.textContent;
      return clone;
    },
    focus() {},
    addEventListener() {}
  };
  element.classList = makeClassList(element);
  return element;
}

function walk(node, callback) {
  callback(node);
  (node.children || []).forEach((child) => walk(child, callback));
}

function matchesSelector(node, selector) {
  if (!node.tagName) return false;
  if (selector === "svg") return node.tagName === "SVG";
  if (selector === "a[aria-disabled=\"true\"]") {
    return node.tagName === "A" && node.attributes["aria-disabled"] === "true";
  }
  if (selector.startsWith(".")) {
    return String(node.className || "").split(/\s+/).includes(selector.slice(1));
  }
  if (selector.startsWith("#")) return node.id === selector.slice(1);
  return node.tagName.toLowerCase() === selector.toLowerCase();
}

function findAll(root, selector) {
  const matches = [];
  walk(root, (node) => {
    if (node !== root && matchesSelector(node, selector)) matches.push(node);
  });
  return matches;
}

function findFirst(root, selector) {
  return findAll(root, selector)[0] || null;
}

const elements = new Map();
function getElement(selector) {
  if (!elements.has(selector)) {
    elements.set(selector, makeElement(selector));
  }
  return elements.get(selector);
}

const radioValues = ["anonymous", "beta_user", "admin"];
const radios = radioValues.map((value) => ({ ...makeElement(), value, checked: false }));
const tabs = ["overview", "setup", "pass", "feedback", "account"].map((name) => {
  const tab = makeElement();
  tab.dataset.backstageTab = name;
  return tab;
});
const panels = ["overview", "setup", "pass", "feedback", "account"].map((name) => {
  const panel = makeElement();
  panel.id = `backstage-panel-${name}`;
  return panel;
});
const jumps = ["setup", "pass"].map((name) => {
  const button = makeElement();
  button.dataset.backstageJump = name;
  return button;
});

const documentStub = {
  querySelector(selector) {
    return getElement(selector);
  },
  querySelectorAll(selector) {
    if (selector === ".hero, .prompt-shell, .try-asking") {
      return [getElement(".hero"), getElement(".prompt-shell"), getElement(".try-asking")];
    }
    if (selector === "input[name='mock-access-state']") return radios;
    if (selector === "[data-backstage-tab]") return tabs;
    if (selector === ".backstage-tab-panel") return panels;
    if (selector === "[data-backstage-jump]") return jumps;
    return [];
  },
  createElement(tagName) {
    return makeElement("", tagName);
  },
  createTextNode: makeTextNode,
  addEventListener() {}
};

const sandbox = {
  window: {
    location: { search: "?access=beta_user" },
    crypto: { randomUUID: () => "test-id" },
    STEEL_RAG_FRETBOARD: {
      mountPedalSteelFretboard(container, options) {
        sandbox.mountedFretboardOptions = options;
        container.dataset.mountedFretboard = "true";
        container.dataset.positionCount = String((options.positions || []).length);
        container.dataset.highlightCount = String(options.highlights.length);
        const figure = makeElement("", "figure");
        figure.className = "pedal-steel-fretboard";
        figure.dataset.component = "PedalSteelFretboard";
        container.appendChild(figure);
      }
    },
    matchMedia: () => ({ matches: false }),
    scrollTo() {},
    setTimeout: (callback) => callback()
  },
  document: documentStub,
  localStorage: {
    getItem: () => "beta_user",
    setItem() {}
  },
  fetch: async (url) => ({
    ok: true,
    status: 200,
    json: async () => {
      if (url === "/api/session") {
        return { authenticated: true, role: "beta_user", authProvider: "local_dev" };
      }
      return {
        question: "What is my copedent?",
        answer: COPEDENT_ANSWER,
        sections: [{ title: "Answer", style: "lead", body: COPEDENT_ANSWER }],
        response: {
          fretboard: {
            title: "G major positions",
            description: "Three common G major locations on E9.",
            maxFret: 24,
            stringCount: 10,
            positions: [
              {
                id: "g-open-3",
                label: "G major",
                fret: 3,
                strings: [4, 5, 6],
                grip: [4, 5, 6],
                role: "No pedals"
              }
            ],
            query: {
              display_scale_notes: {
                natural_minor: ["G", "A", "Bb", "C", "D", "Eb", "F"]
              }
            }
          }
        },
        sources: [],
        followups: []
      };
    }
  }),
  URLSearchParams,
  Date,
  Math,
  Array,
  String,
  Number,
  Boolean,
  setInterval() {},
  requestAnimationFrame: (callback) => callback()
};
sandbox.window.fetch = sandbox.fetch;

vm.createContext(sandbox);
vm.runInContext(clientCode, sandbox);
sandbox.STEEL_RAG_ANSWER_UI = sandbox.window.STEEL_RAG_ANSWER_UI;
vm.runInContext(inlineScript, sandbox);

(async () => {
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(sandbox.submitQuestion("What is my copedent?"), true);
  await new Promise((resolve) => setImmediate(resolve));
  await new Promise((resolve) => setImmediate(resolve));

  const grid = getElement("#answer-section-grid");
  assert.equal(grid.classList.contains("is-structured-answer"), true);
  const renderedSections = grid.children.map((section) => ({
    title: section.children[0]?.textContent,
    text: section.textContent,
    blockTags: section.children.slice(1).map((child) => child.tagName)
  }));

  assert.deepEqual(renderedSections.map((section) => section.title), [
    "Open tuning",
    "Pedals",
    "Levers",
    "Common grips"
  ]);
  assert.deepEqual(renderedSections.map((section) => section.blockTags[0]), [
    "DIV",
    "DIV",
    "DIV",
    "UL"
  ]);
  assert.equal(renderedSections[2].text.includes("F lever"), true);
  assert.equal(renderedSections[2].text.includes("3-4-5"), false);
  assert.equal(renderedSections[2].text.includes("Common grips"), false);
  assert.equal(renderedSections[3].text.includes("3-4-5"), true);
  assert.equal(renderedSections[3].text.includes("6-8-10"), true);

  const fretboardSection = getElement("#answer-fretboard");
  const fretboardDetails = getElement("#answer-fretboard-details");
  const fretboardTitle = getElement("#answer-fretboard-title");
  const fretboardDescription = getElement("#answer-fretboard-description");
  const fretboardMount = getElement("#answer-fretboard-mount");
  assert.equal(fretboardSection.hidden, false);
  assert.equal(fretboardDetails.open, true);
  assert.equal(fretboardTitle.textContent, "G major positions");
  assert.equal(fretboardDescription.textContent, "Three common G major locations on E9.");
  assert.equal(fretboardMount.dataset.mountedFretboard, "true");
  assert.equal(fretboardMount.dataset.positionCount, "1");
  assert.equal(fretboardMount.dataset.highlightCount, "0");
  assert.equal(sandbox.mountedFretboardOptions.maxFret, 24);
  assert.equal(sandbox.mountedFretboardOptions.stringCount, 10);
  assert.equal(sandbox.mountedFretboardOptions.positions[0].id, "g-open-3");
  assert.equal(sandbox.mountedFretboardOptions.positions[0].role, "No pedals");
  assert.equal(sandbox.mountedFretboardOptions.query.display_scale_notes.natural_minor.join(" "), "G A Bb C D Eb F");

  const tabSection = getElement("#answer-tab");
  const tabList = getElement("#answer-tab-list");
  sandbox.renderResponse({
    answer: "Here is a G major grip.",
    sections: [{ title: "Answer", style: "lead", body: "Here is a G major grip." }],
    tabs: [
      {
        title: "G major 4-5-6 grip",
        context: "",
        tabText: "Strings | 4  5  6\\nFret    | 3  3  3",
        ok: true,
        validation: "Validated",
        metadata: { key: "G", tuning: "E9", grip: "4-5-6", difficulty: "beginner" },
        why: "A compact validated G grip.",
        intervals: ["1", "3", "5"],
        chordTones: ["G", "B", "D"],
        issues: []
      }
    ],
    fretboard: {
      title: "G major 4-5-6 grip",
      description: "Strings 4-5-6 at fret 3.",
      positions: [
        {
          id: "g-major-456-open-1",
          label: "G major",
          fret: 3,
          strings: [4, 5, 6],
          grip: [4, 5, 6]
        }
      ]
    },
    sources: [],
    followups: []
  });
  assert.equal(tabSection.hidden, false);
  assert.equal(tabList.textContent.includes("G major 4-5-6 grip"), true);
  assert.equal(tabList.textContent.includes("Strings | 4  5  6\\nFret    | 3  3  3"), true);
  assert.equal(fretboardSection.hidden, false);
  assert.equal(fretboardTitle.textContent, "G major 4-5-6 grip");
  assert.equal(fretboardDescription.textContent, "Strings 4-5-6 at fret 3.");
  assert.equal(sandbox.mountedFretboardOptions.positions[0].id, "g-major-456-open-1");

  sandbox.renderResponse({
    answer: "Here is a static G major grip.",
    sections: [{ title: "Answer", style: "lead", body: "Here is a static G major grip." }],
    fretboard: {
      title: "G major 4-5-6 grip",
      description: "Static grip view.",
      positions: [
        {
          id: "g-major-static-456",
          label: "G major",
          fret: 3,
          strings: [4, 5, 6],
          grip: [4, 5, 6]
        }
      ]
    },
    sources: [],
    followups: []
  });
  assert.equal(tabSection.hidden, true);
  assert.equal(tabList.children.length, 0);
  assert.equal(fretboardSection.hidden, false);
  assert.equal(fretboardTitle.textContent, "G major 4-5-6 grip");
  assert.equal(fretboardDescription.textContent, "Static grip view.");
  assert.equal(sandbox.mountedFretboardOptions.positions[0].id, "g-major-static-456");

  sandbox.renderResponse({
    answer: "No fretboard here.",
    sections: [{ title: "Answer", style: "lead", body: "No fretboard here." }],
    sources: [],
    followups: []
  });
  assert.equal(tabSection.hidden, true);
  assert.equal(tabList.children.length, 0);
  assert.equal(fretboardSection.hidden, true);
  assert.equal(fretboardTitle.textContent, "Fretboard view");
  assert.equal(fretboardDescription.textContent, "");
  assert.equal(fretboardMount.children.length, 0);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_frontend_answer_input_submit_rules_are_enter_without_shift() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const code = fs.readFileSync("ui/answer-client.js", "utf8");
const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const answerUi = vm.runInContext("STEEL_RAG_ANSWER_UI", sandbox);

assert.equal(answerUi.shouldSubmitQuestionKey({ key: "Enter", shiftKey: false }), true);
assert.equal(answerUi.shouldSubmitQuestionKey({ key: "Enter", shiftKey: true }), false);
assert.equal(answerUi.shouldSubmitQuestionKey({ key: "a", shiftKey: false }), false);
assert.equal(answerUi.hasSubmittableQuestion("Why does my amp buzz?"), true);
assert.equal(answerUi.hasSubmittableQuestion("   \n\t  "), false);
assert.equal(answerUi.hasSubmittableQuestion(""), false);
assert.equal(answerUi.normalizeAccessRole("anonymous"), "anonymous");
assert.equal(answerUi.normalizeAccessRole("member"), "beta_user");
assert.equal(answerUi.normalizeAccessRole("beta_user"), "beta_user");
assert.equal(answerUi.normalizeAccessRole("admin"), "admin");
assert.equal(answerUi.normalizeAccessRole("unknown"), "anonymous");
assert.equal(answerUi.canSubmitLiveQuestion("anonymous"), false);
assert.equal(answerUi.canSubmitLiveQuestion("beta_user"), true);
assert.equal(answerUi.canSubmitLiveQuestion("admin"), true);
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_answer_ui_wires_enter_and_send_button_to_same_submit_path() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert "question.addEventListener(\"keydown\"" in html
    assert "followupQuestion.addEventListener(\"keydown\"" in html
    assert "STEEL_RAG_ANSWER_UI.shouldSubmitQuestionKey(event)" in html
    assert "event.preventDefault();" in html
    assert "function submitQuestion(questionText)" in html
    assert "STEEL_RAG_ANSWER_UI.hasSubmittableQuestion(questionText)" in html
    assert "submitQuestion(question.value);" in html
    assert "primarySend.addEventListener(\"click\", submitHomeQuestion)" in html
    assert "answerSend.addEventListener(\"click\", () =>" in html
    assert "submitFollowupQuestion();" in html


def test_answer_ui_gates_live_submission_by_mock_access_state() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert 'value="anonymous"' in html
    assert 'value="beta_user"' in html
    assert 'value="admin"' in html
    assert "STEEL_RAG_ANSWER_UI.canSubmitLiveQuestion(mockAccessState)" in html
    assert 'openBackstage({ initialTab: "pass" });' in html
    assert 'question.disabled = !canAskLive;' in html
    assert 'Private beta answers need a Backstage Pass.' in html
    assert 'accessHelper.textContent = "Get a Backstage Pass to ask Steel Guitar RAG live.";' in html
    assert 'initialTab: STEEL_RAG_ANSWER_UI.canSubmitLiveQuestion(mockAccessState) ? "overview" : "pass"' in html
    assert "function bootstrapSessionAccess()" in html
    assert "const session = await requestBackendSession();" in html
    assert "applySessionAccess(session);" in html
    assert "setDevPreviewAccessEnabled(isLocalDevSession);" in html


def test_answer_ui_applies_backend_session_as_authoritative_access_state() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert "const accessPreview = document.querySelector(\".access-preview\");" in html
    assert "let devPreviewAccessEnabled = true;" in html
    assert "let backendSession = {" in html
    assert "function applySessionAccess(session)" in html
    assert "function requestBackendSession()" in html
    assert 'fetch(STEEL_RAG_ANSWER_UI.SESSION_ENDPOINT || "/api/session"' in html
    assert "backendSession = session;" in html
    assert "const isLocalDevSession = sessionUsesLocalDev(session);" in html
    assert "setDevPreviewAccessEnabled(isLocalDevSession);" in html
    assert "sessionGrantsLiveAccess(session)" in html
    assert "? STEEL_RAG_ANSWER_UI.normalizeAccessRole(session.role)" in html
    assert ": STEEL_RAG_ANSWER_UI.ACCESS_ROLES.ANONYMOUS;" in html
    assert "mockAccessState = STEEL_RAG_ANSWER_UI.normalizeAccessRole(session.role);" in html
    assert "if (!devPreviewAccessEnabled || !sessionUsesLocalDev(backendSession))" in html


def test_answer_ui_hides_dev_preview_controls_outside_local_dev() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert ".access-preview[hidden]" in html
    assert "display: none;" in html
    assert "function setDevPreviewAccessEnabled(isEnabled)" in html
    assert "accessPreview.hidden = !devPreviewAccessEnabled;" in html
    assert "accessPreview.setAttribute(\"aria-hidden\", String(!devPreviewAccessEnabled));" in html
    assert "radio.disabled = !devPreviewAccessEnabled;" in html
    assert "setDevPreviewAccessEnabled(isLocalDevSession);" in html


def test_answer_ui_page_load_bootstraps_session_access_state() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const clientCode = fs.readFileSync("ui/answer-client.js", "utf8");
const html = fs.readFileSync("ui/steel-guitar-rag-mock.html", "utf8");
const inlineScript = html.match(/<script>\n([\s\S]*)\n  <\/script>/)[1];

function makeElement(selector = "") {
  return {
    selector,
    id: selector.startsWith("#") ? selector.slice(1) : "",
    value: "",
    textContent: "",
    innerHTML: "",
    hidden: false,
    disabled: false,
    tabIndex: 0,
    dataset: {},
    attributes: {},
    children: [],
    lastChild: { textContent: "" },
    classList: {
      add() {},
      remove() {},
      toggle() {}
    },
    setAttribute(name, value) {
      this.attributes[name] = String(value);
    },
    getAttribute(name) {
      return this.attributes[name] || "";
    },
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    append(...nodes) {
      this.children.push(...nodes);
    },
    replaceChildren(...nodes) {
      this.children = nodes;
    },
    focus() {},
    addEventListener() {},
    querySelector() {
      return makeElement();
    },
    querySelectorAll() {
      return [];
    },
    closest() {
      return null;
    }
  };
}

async function runPage(sessionPayload, storedAccess = "anonymous") {
  const elements = new Map();
  const radioValues = ["anonymous", "beta_user", "admin"];
  const radios = radioValues.map((value) => ({ ...makeElement(), value, checked: false }));
  const tabs = ["overview", "setup", "pass", "feedback", "account"].map((name) => {
    const tab = makeElement();
    tab.dataset.backstageTab = name;
    return tab;
  });
  const panels = ["overview", "setup", "pass", "feedback", "account"].map((name) => {
    const panel = makeElement();
    panel.id = `backstage-panel-${name}`;
    return panel;
  });

  function getElement(selector) {
    if (!elements.has(selector)) {
      elements.set(selector, makeElement(selector));
    }
    return elements.get(selector);
  }

  const fetchCalls = [];
  const sandbox = {
    console,
    URLSearchParams,
    Date,
    Math,
    JSON,
    setInterval() {},
    requestAnimationFrame(callback) { callback(); },
    localStorage: {
      getItem(key) {
        if (key === "steel-guitar-rag.mockAccessState.v1") return storedAccess;
        return null;
      },
      setItem() {}
    },
    window: {
      location: { search: "" },
      crypto: { randomUUID: () => "test-id" },
      scrollTo() {},
      setTimeout(callback) { callback(); },
      fetch: async (url, options) => {
        fetchCalls.push({ url, options });
        return {
          ok: true,
          status: 200,
          json: async () => sessionPayload
        };
      }
    },
    document: {
      querySelector(selector) {
        return getElement(selector);
      },
      querySelectorAll(selector) {
        if (selector === "input[name='mock-access-state']") return radios;
        if (selector === "[data-backstage-tab]") return tabs;
        if (selector === ".backstage-tab-panel") return panels;
        if (selector === ".hero, .prompt-shell, .try-asking") return [makeElement(), makeElement(), makeElement()];
        return [];
      },
      createElement(tagName) {
        return makeElement(tagName);
      },
      createTextNode(text) {
        return { textContent: text };
      },
      addEventListener() {}
    }
  };
  sandbox.window.localStorage = sandbox.localStorage;
  sandbox.window.URLSearchParams = URLSearchParams;
  sandbox.window.setTimeout = sandbox.window.setTimeout;

  vm.createContext(sandbox);
  vm.runInContext(clientCode, sandbox);
  vm.runInContext(inlineScript, sandbox);
  await new Promise((resolve) => setImmediate(resolve));

  return {
    fetchCalls,
    question: getElement("#question"),
    accessPreview: getElement(".access-preview"),
    backstageCtaLabel: getElement("#backstage-cta-label"),
    radios
  };
}

(async () => {
  const beta = await runPage({
    authenticated: true,
    role: "beta_user",
    email: "beta@example.test",
    authProvider: "cloudflare_access"
  });
  assert.equal(beta.fetchCalls[0].url, "/api/session");
  assert.equal(beta.fetchCalls[0].options.method, "GET");
  assert.equal(beta.question.disabled, false);
  assert.equal(beta.accessPreview.hidden, true);
  assert.equal(beta.radios.every((radio) => radio.disabled), true);
  assert.equal(beta.backstageCtaLabel.textContent, "Go Backstage");

  const admin = await runPage({
    authenticated: true,
    role: "admin",
    email: "admin@example.test",
    authProvider: "cloudflare_access"
  });
  assert.equal(admin.question.disabled, false);
  assert.equal(admin.backstageCtaLabel.textContent, "Go Backstage");

  const anonymous = await runPage({
    authenticated: false,
    role: "anonymous",
    email: null,
    authProvider: "cloudflare_access"
  }, "beta_user");
  assert.equal(anonymous.question.disabled, true);
  assert.equal(anonymous.accessPreview.hidden, true);
  assert.equal(anonymous.radios.every((radio) => radio.disabled), true);

  const localDev = await runPage({
    authenticated: false,
    role: "anonymous",
    email: null,
    authProvider: "local_dev"
  });
  assert.equal(localDev.question.disabled, true);
  assert.equal(localDev.accessPreview.hidden, false);
  assert.equal(localDev.radios.every((radio) => !radio.disabled), true);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_answer_ui_prompt_chips_submit_instead_of_only_filling_input() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert "Show movement without sliding everywhere" in html
    assert "Show me a G to C move on E9." in html
    assert "Explain a simple G turnaround on E9." in html
    assert "Show me a smoother turnaround" not in html
    assert "Explain this lick like a steel player would" not in html
    assert 'button.type = "button";' in html
    assert "button.dataset.promptText = prompt.text;" in html
    assert "button.textContent = prompt.text;" in html
    assert "suggestedPrompts.addEventListener(\"click\"" in html
    assert "submitQuestion(button.dataset.promptText || button.textContent.trim());" in html
    assert "question.value = button.dataset.promptText" not in html
    assert "suggestedPrompts.querySelectorAll(\".example\")" in html
    assert "button.disabled = isBusy;" in html


def test_answer_ui_styles_sections_and_bullets_as_readable_answer_content() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert "sectionEl.classList.add(`is-${section.style}`);" in html
    assert "function shouldUseWideAnswerSection(section)" in html
    assert 'title.includes("why these families matter")' in html
    assert 'title.includes("terminology note")' in html
    assert 'sectionEl.classList.add("is-wide");' in html
    assert 'title.className = "answer-section-title";' in html
    assert 'const list = document.createElement(ordered ? "ol" : "ul");' in html
    assert "section.blocks?.length" in html
    assert 'list.className = "try-list";' in html
    assert ".answer-section.is-bullets" in html
    assert ".answer-section.is-wide" in html
    assert ".answer-detail-grid:empty" in html
    assert "display: none;" in html
    assert "grid-column: 1 / -1;" in html
    assert "grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr));" in html
    assert "columns: 2 280px;" in html
    assert re.search(r"\.answer-lead\s*\{[^}]*max-width:\s*100%;", html, re.S)
    assert re.search(r"\.answer-fretboard-description\s*\{[^}]*max-width:\s*100%;", html, re.S)
    assert re.search(r"@media \(max-width: 960px\)[\s\S]*?\.answer-section\.is-wide \.try-list\s*\{[^}]*columns:\s*1;", html)
    assert re.search(r"\.try-list\s*\{[^}]*font-size:\s*18px;", html, re.S)
    assert re.search(r"\.answer-section p\s*\{[^}]*font-size:\s*17px;", html, re.S)
    assert "sourceGrid.appendChild(card);" in html
    assert "source.forum" in html
    assert "source.excerpt" in html
    assert "appendAnswerSectionContent(answerLead" in html


def test_answer_ui_styles_markdown_tables_as_readable_answer_content() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert 'function renderAnswerTable(table)' in html
    assert 'wrap.className = "answer-table-wrap";' in html
    assert 'tableEl.className = "answer-table";' in html
    assert 'th.scope = "col";' in html
    assert 'container.appendChild(renderAnswerTable(table));' in html
    assert ".answer-table-wrap" in html
    assert "overflow-x: auto;" in html
    assert ".answer-table th," in html
    assert ".answer-table td" in html
    assert re.search(r"\.answer-table\s*\{[^}]*font-size:\s*16px;", html, re.S)


def test_frontend_answer_client_normalizes_tab_render_payloads() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const code = fs.readFileSync("ui/answer-client.js", "utf8");
const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const answerUi = vm.runInContext("STEEL_RAG_ANSWER_UI", sandbox);

const tabText = "Strings | 5  4\\nFret    | 3A 3";
const result = answerUi.normalizeAnswerResponse({
  ok: true,
  tab: tabText,
  issues: [],
  metadata: {
    profile: "default_e9",
    event_count: 2
  }
});

assert.equal(result.tabs.length, 1);
assert.equal(result.tabs[0].title, "Tab example");
assert.equal(result.tabs[0].tabText, tabText);
assert.equal(result.tabs[0].validation, "Validated");
assert.equal(result.tabs[0].metadata.profile, "default_e9");
assert.equal(result.tabs[0].metadata.event_count, 2);

const tabExample = answerUi.normalizeAnswerResponse({
  tab_example: {
    id: "g-major-456-open",
    title: "G major 4-5-6 grip",
    context: { tuning: "E9", profile: "default_e9", difficulty: "beginner" },
    rendered_tab: tabText,
    validation: { ok: true, issues: [], profile: "default_e9", eventCount: 2 },
    explanation: "A compact validated G grip.",
    intervals: [{ role: "root", note: "G" }],
    events: []
  }
});

assert.equal(tabExample.tabs.length, 1);
assert.equal(tabExample.tabs[0].id, "g-major-456-open");
assert.equal(tabExample.tabs[0].title, "G major 4-5-6 grip");
assert.equal(tabExample.tabs[0].tabText, tabText);
assert.equal(tabExample.tabs[0].metadata.difficulty, "beginner");
assert.equal(tabExample.tabs[0].metadata.event_count, 2);
assert.equal(tabExample.tabs[0].why, "A compact validated G grip.");
assert.equal("fretboard" in tabExample, false);

const tabExampleWithFretboard = answerUi.normalizeAnswerResponse({
  tab_example: {
    id: "g-major-456-open",
    title: "G major 4-5-6 grip",
    context: { tuning: "E9", profile: "default_e9", difficulty: "beginner" },
    rendered_tab: tabText,
    validation: { ok: true, issues: [], profile: "default_e9", eventCount: 1 },
    explanation: "A compact validated G grip.",
    fretboard: {
      description: "Strings 4-5-6 at fret 3.",
      positions: [
        {
          id: "g-major-456-open-1",
          label: "G major",
          fret: 3,
          strings: [4, 5, 6],
          grip: [4, 5, 6],
          colorRole: "open"
        }
      ]
    }
  }
});

assert.equal(tabExampleWithFretboard.tabs.length, 1);
assert.equal(tabExampleWithFretboard.fretboard.title, "G major 4-5-6 grip");
assert.equal(tabExampleWithFretboard.fretboard.description, "Strings 4-5-6 at fret 3.");
assert.equal(tabExampleWithFretboard.fretboard.positions[0].id, "g-major-456-open-1");
assert.deepEqual(Array.from(tabExampleWithFretboard.fretboard.positions[0].strings), [4, 5, 6]);

const staticGrip = answerUi.normalizeAnswerResponse({
  answer: "Here is a G major grip.",
  tab_example: {
    id: "g-major-456-open",
    title: "G major 4-5-6 grip",
    rendered_tab: tabText,
    display_tab: false,
    preferred_display: "fretboard_only",
    validation: { ok: true, issues: [], profile: "default_e9", eventCount: 1 }
  },
  fretboard: {
    title: "G major 4-5-6 grip",
    description: "Strings 4-5-6 at fret 3.",
    positions: [
      {
        id: "g-major-456-open-1",
        label: "G major",
        fret: 3,
        strings: [4, 5, 6],
        grip: [4, 5, 6]
      }
    ]
  }
});

assert.equal("tabs" in staticGrip, false);
assert.equal(staticGrip.fretboard.title, "G major 4-5-6 grip");
assert.deepEqual(Array.from(staticGrip.fretboard.positions[0].strings), [4, 5, 6]);

const tabList = answerUi.normalizeAnswerResponse({
  tabs: [
    {
      title: "G grip",
      tabText,
      context: { key: "G", tuning: "E9" },
      metadata: { grip: "4-5-6", difficulty: "Beginner" },
      intervals: ["root", { third: "B" }],
      chordTones: ["G", "B", "D"],
      issues: [{ code: "educational", message: "Short validated example" }]
    }
  ]
});

assert.equal(tabList.tabs.length, 1);
assert.equal(tabList.tabs[0].context, "");
assert.equal(tabList.tabs[0].metadata.grip, "4-5-6");
assert.deepEqual(tabList.tabs[0].intervals, ["root", "third: B"]);
assert.equal(tabList.tabs[0].issues[0].message, "Short validated example");
assert.equal(JSON.stringify(tabList.tabs).includes("[object Object]"), false);
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_answer_ui_wires_tab_examples_between_answer_and_fretboard() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    answer_card_index = html.index('<article class="answer-card">')
    tab_index = html.index('<section class="answer-tab" id="answer-tab"')
    fretboard_index = html.index('<section class="answer-fretboard" id="answer-fretboard"')
    source_index = html.index('<section class="source-section" aria-labelledby="source-notes-title">')
    assert answer_card_index < tab_index < fretboard_index < source_index
    assert 'id="answer-tab-list"' in html
    assert ".answer-tab[hidden]" in html
    assert ".tab-card" in html
    assert ".tab-block" in html
    assert "font-family: ui-monospace" in html
    assert "white-space: pre;" in html
    assert "overflow-x: auto;" in html
    assert "function renderTabExamples(tabs)" in html
    assert "function renderTabCard(tab)" in html
    assert "function clearTabExamples()" in html
    assert "renderTabExamples(response.tabs);" in html
    assert "clearTabExamples();" in html


def test_answer_ui_wires_optional_fretboard_visualization_section() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    answer_card_index = html.index('<article class="answer-card">')
    fretboard_index = html.index('<section class="answer-fretboard" id="answer-fretboard"')
    source_index = html.index('<section class="source-section" aria-labelledby="source-notes-title">')
    assert answer_card_index < fretboard_index < source_index
    assert 'id="answer-fretboard-details"' in html
    assert 'id="answer-fretboard-title">Fretboard view</summary>' in html
    assert 'id="answer-fretboard-mount"' in html
    assert ".answer-fretboard[hidden]" in html
    assert ".fretboard-card" in html
    assert "function renderFretboardVisualization(fretboard)" in html
    assert "window.STEEL_RAG_FRETBOARD.mountPedalSteelFretboard(answerFretboardMount" in html
    assert "legend: fretboard.legend" in html
    assert "function clearFretboardVisualization()" in html
    assert "clearFretboardVisualization();" in html
    assert 'window.matchMedia("(max-width: 640px)").matches' in html


def test_answer_ui_hides_searched_row_but_preserves_source_card_metadata() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert "Searched:" not in html
    assert "searched-row" not in html
    assert "searched-chip" not in html
    assert "source-meta" in html
    assert "source.title" in html
    assert "source.excerpt" in html
    assert "source.url" in html
    assert "source.forum" in html
