from __future__ import annotations

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

    assert '<script src="answer-client.js?v=answer-tables-20260529"></script>' in html
    assert '<script src="mock-answer-data.js"></script>' not in html
    assert "STEEL_RAG_ANSWER_UI.requestAnswer" in html
    assert "STEEL_RAG_ANSWER_UI.requestSession" in html
    assert "No sources returned" in html


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
    "Your saved E9 copedent is organized below.",
    "",
    "Open tuning",
    "",
    "| String | Note |",
    "| --- | --- |",
    "| 1 | F# |",
    "| 2 | D# |",
    "| 3 | G# |",
    "",
    "Pedals",
    "",
    "| Pedal | String | Change |",
    "| --- | --- | --- |",
    "| A | 5 | B to C# |",
    "| B | 3 | G# to A |",
    "",
    "Levers",
    "",
    "| Lever | String | Change |",
    "| --- | --- | --- |",
    "| LKL | 4 | E to F |",
    "| LKR | 4 | E to D# |",
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
assert.equal(formatted.sections[0].body, "Your saved E9 copedent is organized below.");
assert.equal(JSON.stringify(sectionOrder), JSON.stringify(["Answer", "Open tuning", "Pedals", "Levers", "Common grips"]));
assert.equal(JSON.stringify(openTuning.tables[0].headers), JSON.stringify(["String", "Note"]));
assert.equal(JSON.stringify(openTuning.tables[0].rows), JSON.stringify([["1", "F#"], ["2", "D#"], ["3", "G#"]]));
assert.equal(JSON.stringify(pedals.tables[0].headers), JSON.stringify(["Pedal", "String", "Change"]));
assert.equal(JSON.stringify(pedals.tables[0].rows), JSON.stringify([["A", "5", "B to C#"], ["B", "3", "G# to A"]]));
assert.equal(JSON.stringify(levers.tables[0].headers), JSON.stringify(["Lever", "String", "Change"]));
assert.equal(JSON.stringify(levers.tables[0].rows), JSON.stringify([["LKL", "4", "E to F"], ["LKR", "4", "E to D#"]]));
assert.equal(JSON.stringify(levers.bullets), JSON.stringify([]));
assert.equal(JSON.stringify(commonGrips.bullets), JSON.stringify(["3-4-5", "4-5-6", "5-6-8", "6-8-10"]));
assert.equal(levers.blocks[0].type, "table");
assert.equal(commonGrips.blocks[0].type, "bullets");
assert.equal(JSON.stringify(commonGrips.blocks[0].items), JSON.stringify(["3-4-5", "4-5-6", "5-6-8", "6-8-10"]));
assert.equal(JSON.stringify(formatted.sections).includes("| --- |"), false);

const sectionPayload = answerUi.normalizeAnswerResponse({
  sections: [
    {
      title: "Answer",
      style: "lead",
      body: [
        "Your saved E9 copedent is organized below.",
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
assert.equal(sectionPayload.sections[0].body, "Your saved E9 copedent is organized below.");
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
    assert 'title.className = "answer-section-title";' in html
    assert 'const list = document.createElement(ordered ? "ol" : "ul");' in html
    assert "section.blocks?.length" in html
    assert 'list.className = "try-list";' in html
    assert ".answer-section.is-bullets" in html
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
