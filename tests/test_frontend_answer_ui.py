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


def test_answer_ui_uses_live_answer_client_not_mock_answer_data() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert '<script src="answer-client.js"></script>' in html
    assert '<script src="mock-answer-data.js"></script>' not in html
    assert "STEEL_RAG_ANSWER_UI.requestAnswer" in html
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
    assert 'const list = document.createElement(section.ordered ? "ol" : "ul");' in html
    assert 'list.className = "try-list";' in html
    assert ".answer-section.is-bullets" in html
    assert re.search(r"\.try-list\s*\{[^}]*font-size:\s*18px;", html, re.S)
    assert re.search(r"\.answer-section p\s*\{[^}]*font-size:\s*17px;", html, re.S)
    assert "sourceGrid.appendChild(card);" in html
    assert "source.forum" in html
    assert "source.excerpt" in html


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
