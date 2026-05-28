from pathlib import Path
import subprocess
import tempfile


LANDING_PAGE = Path("ui/steel-guitar-rag-landing.html")
DEPLOY_PAGE = Path("deploy/landing/index.html")
INTEREST_FUNCTION = Path("functions/api/interest.js")


def test_public_landing_page_has_required_beta_copy_and_ctas() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    assert "Steel Guitar RAG is a source-backed AI assistant" in html or "Source-backed AI for pedal steel players." in html
    assert "Private beta in preparation" in html
    assert "Join the interest list" in html
    assert "Request early access" in html
    assert "See example questions" in html
    assert "Live AI access requires login and is not public yet." in html


def test_public_landing_page_lists_expected_example_questions() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    expected_questions = [
        "What are common Fender Steel King settings?",
        "How do I use the E9 6th string lower?",
        "What should I practice tonight?",
        "Why does my amp buzz until I touch the changer?",
        "How do players use B+C pedals?",
    ]

    for question in expected_questions:
        assert question in html


def test_public_landing_page_is_static_and_uses_local_assets() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    assert 'src="assets/steel-guitar-rag-logo-transparent.png"' in html
    assert 'url("assets/steel_on_stage2.png")' in html
    assert "/api/answer" not in html
    assert 'action="/api/interest"' in html
    assert 'fetch("/api/interest"' in html
    assert 'id="interest-form"' in html
    assert 'name="email"' in html
    assert 'name="interests"' in html
    assert 'name="turnstileToken"' in html
    assert "steel-guitar-rag-mock.html" not in html
    assert "chromadb" not in html.lower()
    assert "bb.steelguitarforum.com" not in html.lower()
    assert "stripe" not in html.lower()


def test_cloudflare_pages_static_output_matches_landing_source() -> None:
    source_html = LANDING_PAGE.read_text(encoding="utf-8")
    deploy_html = DEPLOY_PAGE.read_text(encoding="utf-8")

    assert deploy_html == source_html
    assert Path("deploy/landing/assets/steel-guitar-rag-logo-transparent.png").is_file()
    assert Path("deploy/landing/assets/steel_on_stage2.png").is_file()


def test_cloudflare_pages_static_output_does_not_expose_private_app_or_rag() -> None:
    html = DEPLOY_PAGE.read_text(encoding="utf-8")

    forbidden = [
        "/api/answer",
        "steel-guitar-rag-mock.html",
        "answer-client.js",
        "mock-answer-data.js",
        "Ollama",
        "Chroma",
        "bb.steelguitarforum.com",
        "stripe",
    ]

    for value in forbidden:
        assert value not in html


def test_interest_function_accepts_valid_submission_and_uses_d1_storage() -> None:
    script = _interest_function_test_script(
        """
const saved = [];
const d1 = {
  prepare: (sql) => ({
    bind: (...values) => ({
      run: async () => saved.push({ sql, values })
    })
  })
};
const response = await mod.__test.handleInterestRequest({
  request: new Request("https://steelguitarrag.com/api/interest", {
    method: "POST",
    headers: { "Content-Type": "application/json", "User-Agent": "pytest" },
    body: JSON.stringify({
      name: "Buddy",
      email: "buddy@example.com",
      playerLevel: "working",
      interests: ["gear-tone", "e9-copedent"],
      message: "I want tone and copedent help.",
      turnstileToken: ""
    })
  }),
  env: { STEEL_RAG_INTEREST_D1: d1 }
});
const payload = await response.json();
assert.equal(response.status, 200);
assert.equal(payload.ok, true);
assert.equal(payload.stored, true);
assert.equal(payload.storage, "d1");
assert.equal(saved.length, 1);
assert.match(saved[0].sql, /created_at/);
assert.match(saved[0].sql, /interests/);
assert.doesNotMatch(saved[0].sql, /submitted_at/);
assert.doesNotMatch(saved[0].sql, /interests_json/);
assert.equal(saved[0].values[3], "buddy@example.com");
assert.equal(saved[0].values[5], JSON.stringify(["gear-tone", "e9-copedent"]));
assert.equal(saved[0].values.length, 9);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_function_returns_safe_json_when_d1_insert_fails() -> None:
    script = _interest_function_test_script(
        """
const d1 = {
  prepare: () => ({
    bind: () => ({
      run: async () => {
        throw new Error("no such column: submitted_at");
      }
    })
  })
};
const response = await mod.__test.handleInterestRequest({
  request: new Request("https://steelguitarrag.com/api/interest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "player@example.com" })
  }),
  env: { STEEL_RAG_INTEREST_D1: d1 }
});
const payload = await response.json();
assert.equal(response.status, 500);
assert.deepEqual(payload, { ok: false, error: "storage_error" });
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_function_rejects_invalid_email() -> None:
    script = _interest_function_test_script(
        """
const response = await mod.__test.handleInterestRequest({
  request: new Request("https://steelguitarrag.com/api/interest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "not-an-email" })
  }),
  env: {}
});
const payload = await response.json();
assert.equal(response.status, 400);
assert.equal(payload.ok, false);
assert.match(payload.error, /valid email/i);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_function_fails_safely_without_storage_binding() -> None:
    script = _interest_function_test_script(
        """
const response = await mod.__test.handleInterestRequest({
  request: new Request("https://steelguitarrag.com/api/interest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "player@example.com" })
  }),
  env: {}
});
const payload = await response.json();
assert.equal(response.status, 200);
assert.equal(payload.ok, true);
assert.equal(payload.stored, false);
assert.equal(payload.storage, "missing");
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def _interest_function_test_script(body: str) -> str:
    source = INTEREST_FUNCTION.read_text(encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as handle:
        handle.write(source)
        module_path = handle.name

    return f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
(async () => {{
  const mod = await import("file://{module_path}");
  fs.unlinkSync("{module_path}");
  {body}
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
