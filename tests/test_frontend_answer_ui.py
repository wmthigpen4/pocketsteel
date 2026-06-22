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

    assert '<script src="answer-client.js?v=router-fretboard-smoke-20260612"></script>' in html
    assert '<script src="pedal-steel-fretboard.js?v=router-fretboard-smoke-20260612"></script>' in html
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

    assert "Explore the E9 Fretboard" in html
    assert 'href="e9-fretboard-explorer.html"' in html
    assert "explorer-entry" in html


def test_e9_fretboard_explorer_surface_uses_display_fields_and_validated_data() -> None:
    html = Path("ui/e9-fretboard-explorer.html").read_text(encoding="utf-8")
    script = Path("ui/e9-fretboard-explorer.js").read_text(encoding="utf-8")
    data = Path("ui/e9-fretboard-explorer-data.js").read_text(encoding="utf-8")
    payload = json.loads(data.split(" = ", 1)[1].rsplit(";", 1)[0])

    assert "E9 Fretboard Explorer" in html
    assert "Validated Explorer data" in html
    assert "not corpus retrieval or RAG-generated fretboard positions" in html
    assert '<script src="pedal-steel-fretboard.js?v=e9-explorer-browser-surface-20260622"></script>' in html
    assert '<script src="e9-fretboard-explorer-data.js?v=e9-explorer-browser-surface-20260622"></script>' in html
    assert '<script src="e9-fretboard-explorer.js?v=e9-explorer-browser-surface-20260622"></script>' in html
    assert '<option value="major">G major</option>' in html
    assert '<option value="natural_minor">G natural minor</option>' in html
    assert '<option value="two_string_harmonized">2-string harmonized scale</option>' in html
    assert '<option value="three_string_diatonic" selected>3-string diatonic harmony</option>' in html
    assert '<optgroup label="Core grips">' in html
    assert '<optgroup label="Advanced swaps">' in html
    assert '<option value="5-7-8">5-7-8</option>' in html
    assert '<option value="all" selected>All 3-string groups</option>' in html

    assert "display_notes" in script
    assert "display_top_voice" in script
    assert "display_summary" in script
    assert "display_scale_notes" in script
    assert "per_string_changes" in script
    assert "warnings" in script
    assert "pitch_validated" in script
    assert "hideFilterControls: true" in script
    assert "[object Object]" not in data

    assert payload["query"]["display_scale_notes"]["natural_minor"] == ["G", "A", "Bb", "C", "D", "Eb", "F"]
    assert payload["query"]["display_scale_notes"]["natural_minor"] != ["G", "A", "A#", "C", "D", "D#", "F"]
    assert any(row["string_group"] == "5-7-8" and row["harmony_type"] == "advanced_pocket" for row in payload["positions"])
    assert any(row.get("warnings") for row in payload["positions"])
    assert all(row["pitch_validated"] is True for row in payload["positions"])


def test_e9_fretboard_explorer_controls_are_mode_aware() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class FakeSelect {
  constructor(id, value, options) {
    this.id = id;
    this.value = value;
    this.options = options.map((item) => ({ ...item, disabled: false }));
    this.selectedIndex = Math.max(0, this.options.findIndex((item) => item.value === value));
    this.listeners = {};
    this._innerHTML = "";
  }
  addEventListener(type, handler) {
    this.listeners[type] = handler;
  }
  dispatchChange() {
    this.selectedIndex = Math.max(0, this.options.findIndex((item) => item.value === this.value));
    this.listeners.change();
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
  }
  set innerHTML(value) {
    this._innerHTML = value;
    this.textContent = value.replace(/<[^>]*>/g, "");
  }
  get innerHTML() {
    return this._innerHTML;
  }
}

const elements = {
  "explorer-key": new FakeSelect("explorer-key", "G", [{ value: "G", text: "G only" }]),
  "explorer-scale": new FakeSelect("explorer-scale", "major", [
    { value: "major", text: "G major" },
    { value: "natural_minor", text: "G natural minor" }
  ]),
  "explorer-harmony": new FakeSelect("explorer-harmony", "three_string_diatonic", [
    { value: "two_string_harmonized", text: "2-string harmonized scale" },
    { value: "three_string_diatonic", text: "3-string diatonic harmony" }
  ]),
  "explorer-string-group": new FakeSelect("explorer-string-group", "all", [{ value: "all", text: "All 3-string groups" }]),
  "explorer-scale-notes": new FakeNode("explorer-scale-notes"),
  "explorer-result-count": new FakeNode("explorer-result-count"),
  "explorer-fretboard": new FakeNode("explorer-fretboard"),
  "explorer-row-list": new FakeNode("explorer-row-list"),
  "explorer-empty": new FakeNode("explorer-empty"),
};
let lastMount;
const sandbox = {
  window: {
    STEEL_RAG_FRETBOARD: {
      mountPedalSteelFretboard: (container, options) => {
        lastMount = { container, options };
        container.textContent = JSON.stringify(options.positions.map((row) => row.id));
      }
    }
  },
  document: {
    getElementById: (id) => elements[id]
  },
  console
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("ui/e9-fretboard-explorer-data.js", "utf8"), sandbox);
vm.runInContext(fs.readFileSync("ui/e9-fretboard-explorer.js", "utf8"), sandbox);

assert.match(elements["explorer-string-group"].innerHTML, /All 3-string groups/);
assert.match(elements["explorer-string-group"].innerHTML, /Core grips/);
assert.match(elements["explorer-string-group"].innerHTML, /Advanced swaps/);
assert.match(elements["explorer-string-group"].innerHTML, /5-7-8/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, />3-5</);
assert.equal(lastMount.options.showHighlightLabels, false);
assert.equal(lastMount.options.hideFilterControls, true);
assert.equal(lastMount.options.positions.some((row) => row.grip === "5-7-8"), true);

elements["explorer-string-group"].value = "4-5-6";
elements["explorer-harmony"].value = "two_string_harmonized";
elements["explorer-harmony"].dispatchChange();
assert.equal(elements["explorer-string-group"].value, "all");
assert.match(elements["explorer-string-group"].innerHTML, /All 2-string groups/);
assert.match(elements["explorer-string-group"].innerHTML, />3-5</);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /Core grips/);
assert.doesNotMatch(elements["explorer-string-group"].innerHTML, /5-7-8/);
assert.equal(elements["explorer-empty"].hidden, true);

elements["explorer-scale"].value = "natural_minor";
elements["explorer-scale"].dispatchChange();
assert.equal(elements["explorer-harmony"].value, "three_string_diatonic");
assert.equal(elements["explorer-harmony"].options.find((item) => item.value === "two_string_harmonized").disabled, true);
assert.equal(elements["explorer-string-group"].value, "all");
assert.match(elements["explorer-scale-notes"].textContent, /G A Bb C D Eb F/);
assert.doesNotMatch(elements["explorer-scale-notes"].textContent, /A#|D#/);
assert.equal(elements["explorer-empty"].hidden, true);
assert.doesNotMatch(elements["explorer-row-list"].textContent, /\[object Object\]/);
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
