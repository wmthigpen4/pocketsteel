from pathlib import Path
import subprocess
import tempfile


LANDING_PAGE = Path("ui/steel-guitar-rag-landing.html")
DEPLOY_PAGE = Path("deploy/landing/index.html")
INTEREST_FUNCTION = Path("functions/api/interest.js")
INTEREST_DIGEST_WORKER = Path("workers/interest-digest.js")


def test_public_landing_page_has_required_beta_copy_and_ctas() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    assert "Steel Guitar RAG is a source-backed AI assistant" in html or "Source-backed AI for pedal steel players." in html
    assert "Private preview in preparation" in html
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
      email: "buddy@steelguitarrag.com",
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
assert.match(saved[0].sql, /status/);
assert.match(saved[0].sql, /spam_score/);
assert.match(saved[0].sql, /admin_notes/);
assert.match(saved[0].sql, /source/);
assert.doesNotMatch(saved[0].sql, /submitted_at/);
assert.doesNotMatch(saved[0].sql, /interests_json/);
assert.equal(saved[0].values[3], "buddy@steelguitarrag.com");
assert.equal(saved[0].values[5], JSON.stringify(["gear-tone", "e9-copedent"]));
assert.equal(saved[0].values[9], "new");
assert.equal(saved[0].values[10], 0);
assert.equal(saved[0].values[11], "");
assert.equal(saved[0].values[12], "landing_page");
assert.equal(saved[0].values.length, 13);
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


def test_interest_function_marks_test_example_email_as_test() -> None:
    script = _interest_function_test_script(
        """
const normalized = mod.__test.normalizeSubmission({
  name: "Test",
  email: "test@example.com",
  interests: ["gear-tone"],
  message: "smoke test"
});
assert.equal(normalized.ok, true);
assert.equal(normalized.submission.status, "test");
assert.equal(normalized.submission.spamScore, 100);
assert.equal(normalized.submission.source, "landing_page");
assert.match(normalized.submission.adminNotes, /obvious test email/);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_function_marks_example_and_test_domains_as_junk() -> None:
    script = _interest_function_test_script(
        """
const exampleDomain = mod.__test.normalizeSubmission({
  name: "Example",
  email: "person@example.com",
  message: "Trying the form."
});
const testDomain = mod.__test.normalizeSubmission({
  name: "Domain Test",
  email: "person@contestmail.com",
  message: "Trying the form."
});
assert.equal(exampleDomain.submission.status, "test");
assert.equal(exampleDomain.submission.spamScore, 80);
assert.match(exampleDomain.submission.adminNotes, /reserved test\\/example email domain/);
assert.equal(testDomain.submission.status, "review");
assert.equal(testDomain.submission.spamScore, 30);
assert.match(testDomain.submission.adminNotes, /email domain contains test/);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_function_marks_url_heavy_message_review() -> None:
    script = _interest_function_test_script(
        """
const normalized = mod.__test.normalizeSubmission({
  name: "Links",
  email: "links@steelguitarrag.com",
  message: "Please review https://spam.example and www.bad.example"
});
assert.equal(normalized.ok, true);
assert.equal(normalized.submission.status, "review");
assert.equal(normalized.submission.spamScore, 60);
assert.match(normalized.submission.adminNotes, /URL-heavy message/);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_function_marks_blank_and_long_entries_review() -> None:
    script = _interest_function_test_script(
        """
const blank = mod.__test.normalizeSubmission({
  email: "blank@steelguitarrag.com"
});
const longMessage = mod.__test.normalizeSubmission({
  name: "Long",
  email: "long@steelguitarrag.com",
  message: "x".repeat(1700)
});
assert.equal(blank.ok, true);
assert.equal(blank.submission.status, "review");
assert.equal(blank.submission.spamScore, 20);
assert.match(blank.submission.adminNotes, /blank name and message/);
assert.equal(longMessage.ok, true);
assert.equal(longMessage.submission.status, "review");
assert.equal(longMessage.submission.spamScore, 40);
assert.match(longMessage.submission.adminNotes, /very long message/);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_function_does_not_log_secrets() -> None:
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
const logs = [];
const originalLog = console.log;
const originalError = console.error;
console.log = (...args) => logs.push(args.join(" "));
console.error = (...args) => logs.push(args.join(" "));
try {
  const response = await mod.__test.handleInterestRequest({
    request: new Request("https://steelguitarrag.com/api/interest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "Secret Safe",
        email: "safe@steelguitarrag.com",
        message: "Please invite me."
      })
    }),
    env: {
      STEEL_RAG_INTEREST_D1: d1,
      PUSHOVER_APP_TOKEN: "app-secret-token",
      PUSHOVER_USER_KEY: "user-secret-key"
    }
  });
  assert.equal(response.status, 200);
} finally {
  console.log = originalLog;
  console.error = originalError;
}
const joined = logs.join("\\n");
assert.doesNotMatch(joined, /app-secret-token/);
assert.doesNotMatch(joined, /user-secret-key/);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_filters_obvious_test_email() -> None:
    script = _interest_digest_test_script(
        """
const rows = mod.__test.classifySubmissions([
  makeRow({ id: "test-1", email: "test@example.com", name: "Test" })
]);
assert.equal(rows[0].include, false);
assert.equal(rows[0].status, "spam");
assert.equal(rows[0].spam_score, 100);
assert.match(rows[0].admin_notes, /obvious test email/);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_keeps_real_submission() -> None:
    script = _interest_digest_test_script(
        """
const rows = mod.__test.classifySubmissions([
  makeRow({
    id: "real-1",
    email: "buddy@steel.example",
    name: "Buddy",
    interests: JSON.stringify(["gear-tone"]),
    message: "I want tone help."
  })
]);
assert.equal(rows[0].include, true);
assert.equal(rows[0].status, "new");
assert.equal(rows[0].spam_score, 0);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_groups_duplicate_email() -> None:
    script = _interest_digest_test_script(
        """
const rows = mod.__test.classifySubmissions([
  makeRow({ id: "dup-1", email: "player@steel.example", message: "First" }),
  makeRow({ id: "dup-2", email: "PLAYER@steel.example", message: "Second" })
]);
const groups = mod.__test.groupIncludedSubmissions(rows);
const digest = mod.__test.buildDigestBody(rows, new Date("2026-05-28T12:00:00.000Z"));
assert.equal(groups.length, 1);
assert.equal(groups[0].email, "player@steel.example");
assert.equal(groups[0].submissions.length, 2);
assert.match(digest.message, /player@steel\\.example \\(2 submissions\\)/);
assert.match(digest.message, /Submission 1\\/2/);
assert.match(digest.message, /Submission 2\\/2/);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_marks_url_heavy_message_review() -> None:
    script = _interest_digest_test_script(
        """
const rows = mod.__test.classifySubmissions([
  makeRow({
    id: "url-1",
    email: "links@steel.example",
    message: "Check http://spam.example and www.bad.example now"
  })
]);
assert.equal(rows[0].include, true);
assert.equal(rows[0].status, "review");
assert.equal(rows[0].spam_score, 60);
assert.match(rows[0].admin_notes, /URL-heavy message/);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_body_includes_submission_details() -> None:
    script = _interest_digest_test_script(
        """
const rows = mod.__test.classifySubmissions([
  makeRow({
    id: "real-2",
    created_at: "2026-05-27T15:00:00.000Z",
    email: "player@steel.example",
    name: "Lloyd",
    player_level: "intermediate",
    interests: JSON.stringify(["gear-tone", "practice"]),
    message: "I want a better practice path."
  })
]);
const digest = mod.__test.buildDigestBody(rows, new Date("2026-05-28T12:00:00.000Z"));
assert.match(digest.message, /Lloyd/);
assert.match(digest.message, /player@steel\\.example/);
assert.match(digest.message, /gear-tone, practice/);
assert.match(digest.message, /I want a better practice path\\./);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_does_not_log_secrets() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({ id: "real-3", email: "player@steel.example", name: "Paul", message: "Invite me." })
]);
const logs = [];
const originalLog = console.log;
const originalError = console.error;
console.log = (...args) => logs.push(args.join(" "));
console.error = (...args) => logs.push(args.join(" "));
try {
  await mod.__test.runInterestDigest({
    env: {
      STEEL_RAG_INTEREST_D1: d1,
      PUSHOVER_APP_TOKEN: "app-secret-token",
      PUSHOVER_USER_KEY: "user-secret-key"
    },
    now: new Date("2026-05-28T12:00:00.000Z"),
    fetchImpl: async () => new Response("{}", { status: 200 })
  });
} finally {
  console.log = originalLog;
  console.error = originalError;
}
const joined = logs.join("\\n");
assert.doesNotMatch(joined, /app-secret-token/);
assert.doesNotMatch(joined, /user-secret-key/);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_updates_notified_only_after_successful_send() -> None:
    script = _interest_digest_test_script(
        """
const rows = [makeRow({ id: "real-4", email: "player@steel.example", name: "Sarah" })];
const failingD1 = makeD1(rows);
await assert.rejects(
  () => mod.__test.runInterestDigest({
    env: {
      STEEL_RAG_INTEREST_D1: failingD1,
      PUSHOVER_APP_TOKEN: "app-token",
      PUSHOVER_USER_KEY: "user-key"
    },
    now: new Date("2026-05-28T12:00:00.000Z"),
    fetchImpl: async () => new Response("bad", { status: 500 })
  }),
  /Pushover send failed/
);
assert.equal(failingD1.operations.some((op) => /notified_at/.test(op.sql)), false);

const successD1 = makeD1(rows);
await mod.__test.runInterestDigest({
  env: {
    STEEL_RAG_INTEREST_D1: successD1,
    PUSHOVER_APP_TOKEN: "app-token",
    PUSHOVER_USER_KEY: "user-key"
  },
  now: new Date("2026-05-28T12:00:00.000Z"),
  fetchImpl: async () => new Response("{}", { status: 200 })
});
const notifiedUpdates = successD1.operations.filter((op) => /notified_at/.test(op.sql));
assert.equal(notifiedUpdates.length, 1);
assert.equal(notifiedUpdates[0].values[0], "2026-05-28T12:00:00.000Z");
assert.equal(notifiedUpdates[0].values[1], "real-4");
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


def _interest_digest_test_script(body: str) -> str:
    source = INTEREST_DIGEST_WORKER.read_text(encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as handle:
        handle.write(source)
        module_path = handle.name

    return f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
(async () => {{
  const mod = await import("file://{module_path}");
  fs.unlinkSync("{module_path}");

  function makeRow(overrides = {{}}) {{
    return {{
      id: "row-1",
      created_at: "2026-05-27T12:00:00.000Z",
      name: "",
      email: "player@steel.example",
      player_level: "",
      interests: JSON.stringify(["forum-wisdom"]),
      message: "Please invite me.",
      status: "new",
      spam_score: 0,
      admin_notes: "",
      notified_at: null,
      source: "landing_page",
      ...overrides
    }};
  }}

  function makeD1(rows) {{
    const operations = [];
    return {{
      operations,
      prepare: (sql) => ({{
        bind: (...values) => ({{
          all: async () => ({{ results: rows }}),
          run: async () => {{
            operations.push({{ sql, values }});
            return {{ success: true }};
          }}
        }})
      }})
    }};
  }}

  {body}
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
