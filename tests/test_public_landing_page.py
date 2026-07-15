from pathlib import Path
import subprocess
import tempfile


LANDING_PAGE = Path("ui/steel-guitar-rag-landing.html")
DEPLOY_PAGE = Path("deploy/landing/index.html")
INTEREST_FUNCTION = Path("functions/api/interest.js")
INTEREST_DIGEST_WORKER = Path("workers/interest-digest.js")
INTEREST_DIGEST_CONFIG = Path("wrangler-interest-digest.toml")
INTEREST_DIGEST_MIGRATION = Path("migrations/interest-digest/0001_delivery_state.sql")
PUBLIC_PREVIEW_SCRIPTS = (
    "pedal-steel-fretboard-styles.js",
    "melody-score.js",
    "landing-home.js",
)
PUBLIC_PREVIEW_ASSETS = (
    "assets/landing/melody-score.png",
    "assets/landing/spotlight.png",
    "brand/pedal-steel-fretboard-background.svg",
    "brand/steel-guitar-rag-hanging-sign-fallback.png",
)


def test_interest_digest_config_enables_scoped_migrations_and_observability() -> None:
    config = INTEREST_DIGEST_CONFIG.read_text(encoding="utf-8")
    migration = INTEREST_DIGEST_MIGRATION.read_text(encoding="utf-8")

    assert 'migrations_dir = "migrations/interest-digest"' in config
    assert "[observability]" in config
    assert "enabled = true" in config
    assert "head_sampling_rate = 1" in config
    assert "create table if not exists interest_digest_deliveries" in migration
    assert "unique (window_start, window_end)" in migration
    assert "create table if not exists interest_digest_delivery_parts" in migration
    assert "primary key (delivery_id, part_index)" in migration
    assert "content_hash text not null" in migration


def test_public_landing_page_has_conversion_focused_copy_and_ctas() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    assert "Built for pedal steel" in html
    assert "See the neck. Understand the music. Play with confidence." in html
    assert "Explore E9 positions. Build and practice melodies. Follow guided lessons. Get source-aware help from the Steel Guitar Brain." in html
    assert html.count("Get launch invite") == 2
    assert "No app access yet. We’ll email you when launch invites open." in html
    assert "You’re on the list. We’ll email you when launch invites open." in html
    assert '<form class="interest-form" id="interest-form" action="/api/interest" method="post">' in html
    assert 'href="#interest-form" data-focus-interest' in html
    assert "Open app" not in html
    assert "Pricing" not in html
    assert "Payments" not in html


def test_public_landing_header_status_is_plain_and_has_no_duplicate_invite_cta() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")
    header = html.split('<header class="app-shell-header">', 1)[1].split("</header>", 1)[0]
    label_style = html.split(".preview-label {", 1)[1].split("}", 1)[0]

    assert '<span class="preview-label">' in header
    assert "Private preview" in header
    assert "Get launch invite" not in header
    assert "invite-button" not in header
    assert "preview-chip" not in html
    assert "border" not in label_style
    assert "border-radius" not in label_style
    assert "background" not in label_style


def test_public_landing_footer_centers_the_app_rag_explainer() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    assert 'class="home-trust-footer home-ai-footer"' in html
    assert "Built deep for pedal steel." in html
    assert "Powered by source-aware AI underneath." in html
    assert 'class="footer-trigger footer-shimmer"' in html
    assert 'aria-expanded="false" aria-controls="tech-popover"' in html
    assert 'id="tech-popover" role="dialog" aria-modal="true"' in html
    assert "Inside the RAG" in html
    assert "Retrieve" in html and "Augment" in html and "Generate" in html
    assert 'title: "What’s underneath?"' in html
    assert '“RAG” stands for retrieval-augmented generation' in html
    assert "searches organized knowledge before responding" in html
    assert "techPopoverClose.focus();" in html
    assert 'event.key === "Escape"' in html
    assert "Private preview · Features remain locked until launch." not in html
    assert "Steel Guitar RAG · Built deep for pedal steel." not in html


def test_public_landing_page_uses_dark_product_led_visual_direction() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    assert "--amber: #ffb12b;" in html
    assert 'url("assets/steel_on_stage2.png")' in html
    assert 'src="brand/steel-guitar-rag-hanging-sign-fallback.png"' in html
    assert '<video class="landing-sign"' not in html
    assert "steel-guitar-rag-landing-alpha.webm" not in html
    assert 'class="app-shell-header"' in html
    assert 'class="home-explorer-panel"' in html
    assert 'id="home-explorer-preview"' in html
    assert 'class="home-product-grid"' in html
    assert 'class="trust-section"' in html
    assert 'src="pedal-steel-fretboard.js?v=locked-public-app-home-2-20260715"' in html
    assert 'src="landing-home.js?v=locked-public-app-home-2-20260715"' in html


def test_public_landing_page_reuses_the_real_app_home_previews() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")
    app_home = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    shared_copy = (
        "One chord. Three positions. A whole neck opens up.",
        "Visualize E9 positions, grips, intervals, scales, harmony, and movement across the neck.",
        "Build, edit, play back, and practice melodies while connecting each note to a playable E9 position.",
        "Follow reviewed learning paths or build a focused lesson for the topic, level, and time you have.",
        "Get practical, teacher-first pedal-steel help grounded in trusted sources and your setup.",
        "Uses your active E9 setup",
    )
    for value in shared_copy:
        assert value in html
        assert value in app_home

    assert 'window.STEEL_RAG_LANDING?.mountExplorerPreview' in html
    assert 'window.STEEL_RAG_LANDING?.mountMelodyPreview' in html
    assert 'class="home-card-preview home-fretboard-mini"' in html
    assert 'class="home-card-preview home-score-preview"' in html
    assert 'class="home-card-preview home-lesson-mini"' in html
    assert 'class="ask-launch-example" role="img"' in html


def test_public_landing_hanging_sign_stays_anchored_to_the_left_edge() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    assert "left: calc((100vw - 100%) / -2 - 12px);" in html
    assert "left: calc((100vw - 100%) / -2);" in html
    assert ".home-sign { top: -12px; left: 50%;" not in html
    assert "transform: translateX(-50%)" not in html
    assert ".app-shell-header { grid-template-columns: 1fr; min-height: 0; padding-top: 225px; }" in html


def test_public_landing_mobile_sign_and_melody_card_avoid_ios_failures() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")
    mobile_css = html.split("@media (max-width: 720px)", 1)[1].split("@media (prefers-reduced-motion: reduce)", 1)[0]

    assert '<a class="home-sign" href="#top"' in html
    assert '<img class="landing-sign-art"' in html
    assert ".skip-link:focus-visible { transform: translateY(0); }" in html
    assert ".skip-link:focus { transform: translateY(0); }" not in html
    assert ".home-product-card { min-height: 0; padding: 20px; }" in mobile_css
    assert ".home-card-preview { height: 100px; margin-bottom: 0; }" in mobile_css
    assert ".locked-label { margin-top: 16px; }" in mobile_css
    assert '.home-product-card[data-locked-workspace="melody-studio"]' in mobile_css
    assert ".home-score-preview {" in mobile_css
    assert "height: 126px;" in mobile_css
    assert ".home-score-preview .home-melody-score-image { width: 100%; max-width: none; }" in mobile_css


def test_public_landing_page_describes_four_locked_workspaces() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    expected_workspaces = [
        "Fretboard Explorer",
        "Melody Studio",
        "Lessons",
        "Steel Guitar Q&amp;A",
    ]
    for workspace in expected_workspaces:
        assert workspace in html
    assert html.count('<article class="home-product-card') == 4
    assert html.count("Coming at launch") == 4
    assert "See what you’ll be able to do." in html
    assert "They are shown here as static previews and do not open the app." in html
    assert "Validated E9 logic" in html
    assert "Real copedents" in html
    assert "Source-aware answers" in html
    assert "Show me a classic country move." in html


def test_public_landing_page_is_static_email_only_and_accessible() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    assert "/api/answer" not in html
    assert 'action="/api/interest"' in html
    assert 'fetch("/api/interest"' in html
    assert 'id="interest-form"' in html
    assert html.count('name="email"') == 1
    assert 'name="name"' not in html
    assert 'name="playerLevel"' not in html
    assert 'name="interests"' not in html
    assert 'name="message"' not in html
    assert 'name="turnstileToken"' not in html
    assert '<label for="interest-email">Email address</label>' in html
    assert 'role="status" aria-live="polite"' in html
    assert '<a class="skip-link" href="#main-content">Skip to main content</a>' in html
    assert 'JSON.stringify({ email: email.value.trim() })' in html
    assert "steel-guitar-rag-mock.html" not in html
    assert "app.steelguitarrag.com" not in html
    assert "chromadb" not in html.lower()
    assert "bb.steelguitarforum.com" not in html.lower()
    assert "stripe" not in html.lower()
    assert "Pocket Steel" not in html
    assert html.count('<button class="invite-button"') == 1
    assert '<article class="home-product-card' in html
    assert '<button class="ask-launch-example"' not in html
    assert '<a class="home-card-link"' not in html
    assert 'href="/ui/' not in html


def test_cloudflare_pages_static_output_matches_landing_source() -> None:
    source_html = LANDING_PAGE.read_text(encoding="utf-8")
    deploy_html = DEPLOY_PAGE.read_text(encoding="utf-8")

    assert deploy_html == source_html
    assert Path("deploy/landing/assets/steel-guitar-rag-logo-transparent.png").is_file()
    assert Path("deploy/landing/assets/steel_on_stage2.png").is_file()
    assert Path("deploy/landing/brand/steel-guitar-rag-hanging-sign-fallback.png").is_file()
    for relative_path in PUBLIC_PREVIEW_SCRIPTS:
        deploy_script = Path("deploy/landing") / relative_path
        source_script = Path("ui") / relative_path
        assert deploy_script.read_bytes() == source_script.read_bytes()
    public_fretboard = Path("deploy/landing/pedal-steel-fretboard.js").read_text(encoding="utf-8")
    assert "mountPedalSteelFretboard" in public_fretboard
    assert 'function explorerUrl(params) {\n    return "";\n  }' in public_fretboard
    assert "/ui/" not in public_fretboard
    for relative_path in PUBLIC_PREVIEW_ASSETS:
        assert (Path("deploy/landing") / relative_path).is_file()


def test_cloudflare_pages_static_output_does_not_expose_private_app_or_rag() -> None:
    html = DEPLOY_PAGE.read_text(encoding="utf-8")

    forbidden = [
        "/api/answer",
        "steel-guitar-rag-mock.html",
        "answer-client.js",
        "mock-answer-data.js",
        "app.steelguitarrag.com",
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


def test_interest_function_accepts_email_only_submission_as_new() -> None:
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
    body: JSON.stringify({ email: "launch@steelguitarrag.com" })
  }),
  env: { STEEL_RAG_INTEREST_D1: d1 }
});
const payload = await response.json();
assert.equal(response.status, 200);
assert.equal(payload.ok, true);
assert.equal(payload.stored, true);
assert.equal(saved.length, 1);
assert.equal(saved[0].values[3], "launch@steelguitarrag.com");
assert.equal(saved[0].values[4], "");
assert.equal(saved[0].values[5], "[]");
assert.equal(saved[0].values[6], "");
assert.equal(saved[0].values[9], "new");
assert.equal(saved[0].values[10], 0);
assert.equal(saved[0].values[11], "");
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


def test_interest_function_keeps_email_only_new_and_marks_long_entries_review() -> None:
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
assert.equal(blank.submission.status, "new");
assert.equal(blank.submission.spamScore, 0);
assert.equal(blank.submission.adminNotes, "");
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


def test_interest_digest_excludes_existing_spam_and_test_statuses() -> None:
    script = _interest_digest_test_script(
        """
const rows = mod.__test.classifySubmissions([
  makeRow({ id: "spam-1", email: "spam@steel.example", status: "spam" }),
  makeRow({ id: "test-1", email: "tester@steel.example", status: "test" }),
  makeRow({ id: "new-1", email: "player@steel.example", status: "new" })
]);
const digest = mod.__test.buildDigestBody(rows, new Date("2026-05-28T12:00:00.000Z"));
assert.equal(rows[0].include, false);
assert.equal(rows[1].include, false);
assert.equal(rows[2].include, true);
assert.equal(digest.includedCount, 1);
assert.equal(digest.skippedCount, 2);
assert.doesNotMatch(digest.message, /spam@steel\\.example/);
assert.doesNotMatch(digest.message, /tester@steel\\.example/);
assert.match(digest.message, /player@steel\\.example/);
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


def test_interest_digest_includes_new_and_review_rows() -> None:
    script = _interest_digest_test_script(
        """
const rows = mod.__test.classifySubmissions([
  makeRow({ id: "new-1", email: "new@steel.example", name: "New Player", status: "new" }),
  makeRow({ id: "review-1", email: "review@steel.example", name: "Review Player", status: "review" })
]);
const digest = mod.__test.buildDigestBody(rows, new Date("2026-05-28T12:00:00.000Z"));
assert.equal(digest.includedCount, 2);
assert.equal(digest.reviewCount, 1);
assert.match(digest.message, /New Player/);
assert.match(digest.message, /Review Player/);
assert.match(digest.message, /review@steel\\.example/);
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


def test_interest_digest_candidate_query_fetches_unnotified_rows_needed_for_cleanup() -> None:
    script = _interest_digest_test_script(
        """
let capturedSql = "";
let bindValues = null;
const d1 = {
  prepare: (sql) => {
    capturedSql = sql;
    return {
      bind: (...values) => {
        bindValues = values;
        return { all: async () => ({ results: [] }) };
      }
    };
  }
};
await mod.__test.fetchCandidateRows(d1);
assert.match(capturedSql, /notified_at is null/);
assert.match(capturedSql, /lower\\(coalesce\\(status, 'new'\\)\\) in \\('new', 'review', 'spam', 'test'\\)/);
assert.match(capturedSql, /order by created_at asc/);
assert.doesNotMatch(capturedSql, /created_at >=/);
assert.deepEqual(bindValues, []);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_filters_high_confidence_marketing_and_gibberish_spam() -> None:
    script = _interest_digest_test_script(
        """
const rows = mod.__test.classifySubmissions([
  makeRow({ id: "seo", name: "SEO Seller", message: "We offer SEO and organic traffic packages." }),
  makeRow({ id: "search", name: "Search Bot", message: "Register steelguitarrag.com in GoogleSearchIndex now." }),
  makeRow({ id: "video", name: "Video Seller", message: "Our videos cost $195 for a 30 second video." }),
  makeRow({ id: "social", name: "Social Seller", message: "We can grow your Instagram followers every month." }),
  makeRow({ id: "automation", name: "Growth Seller", message: "Our AI automation system improves lead generation. Book a discovery call." }),
  makeRow({ id: "outreach", name: "Outreach Seller", message: "We introduce services using website contact pages; our platform supports outreach." }),
  makeRow({ id: "gibberish", name: "lgrqyxpqlq", message: "mdxpzimrtxdqsqloqpelgjempmzhhg" }),
  makeRow({ id: "real", name: "Real Player", message: "I want help learning E9 grips and getting a cleaner tone." })
]);
for (const row of rows.slice(0, 7)) {
  assert.equal(row.include, false, row.id);
  assert.equal(row.status, "spam", row.id);
  assert.equal(row.spam_score, 100, row.id);
}
assert.equal(rows[7].include, true);
assert.equal(rows[7].status, "new");
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
const staleBrand = "The " + "Turnaround";
assert.match(digest.title, /Steel Guitar RAG/);
assert.match(digest.message, /Steel Guitar RAG/);
assert.equal(digest.title.includes(staleBrand), false);
assert.equal(digest.message.includes(staleBrand), false);
assert.match(digest.message, /Lloyd/);
assert.match(digest.message, /player@steel\\.example/);
assert.match(digest.message, /gear-tone, practice/);
assert.match(digest.message, /I want a better practice path\\./);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_deletes_spam_before_sending_real_rows() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({ id: "real-before-send", name: "Real Player", email: "real@steel.example", message: "Please invite me." }),
  makeRow({ id: "spam-before-send", name: "SEO Seller", email: "sales@spam.example", message: "We offer SEO and backlink packages." }),
  makeRow({ id: "test-before-send", name: "Test", email: "test@example.com", status: "test" })
]);
let fetchCalled = false;
const result = await mod.__test.runInterestDigest({
  env: {
    STEEL_RAG_INTEREST_D1: d1,
    PUSHOVER_APP_TOKEN: "app-token",
    PUSHOVER_USER_KEY: "user-key"
  },
  now: new Date("2026-05-28T12:00:00.000Z"),
  fetchImpl: async () => {
    fetchCalled = true;
    const deletes = d1.operations.filter((op) => /delete from interest_submissions/.test(op.sql));
    assert.equal(deletes.length, 2);
    assert.deepEqual(deletes.map((op) => op.values[0]), ["spam-before-send", "test-before-send"]);
    assert.match(deletes[0].sql, /notified_at is null/);
    assert.equal(d1.operations.some((op) => /notified_at = [?]/.test(op.sql)), false);
    return new Response("{}", { status: 200 });
  }
});
assert.equal(fetchCalled, true);
assert.equal(result.deletedSpamCount, 2);
assert.equal(result.includedCount, 1);
assert.equal(result.skippedCount, 2);
assert.doesNotMatch(result.message, /sales@spam[.]example/);
const notified = d1.operations.filter((op) => /notified_at = [?]/.test(op.sql));
assert.equal(notified.length, 1);
assert.equal(notified[0].values[1], "real-before-send");
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_does_not_notify_when_spam_deletion_fails() -> None:
    script = _interest_digest_test_script(
        """
const rows = [
  makeRow({ id: "delete-failure", name: "SEO Seller", message: "We offer SEO packages and backlinks." })
];
let fetchCalled = false;
const d1 = {
  prepare: (sql) => ({
    bind: (...values) => ({
      all: async () => ({ results: rows }),
      run: async () => {
        if (/delete from interest_submissions/.test(sql)) {
          throw new Error("delete failed");
        }
        return { success: true, meta: { changes: 1 } };
      }
    })
  })
};
await assert.rejects(
  () => mod.__test.runInterestDigest({
    env: {
      STEEL_RAG_INTEREST_D1: d1,
      PUSHOVER_APP_TOKEN: "app-token",
      PUSHOVER_USER_KEY: "user-key"
    },
    fetchImpl: async () => {
      fetchCalled = true;
      return new Response("{}", { status: 200 });
    }
  }),
  /delete failed/
);
assert.equal(fetchCalled, false);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_dry_run_previews_spam_deletion_without_writing() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({ id: "dry-real", name: "Real Player", message: "Please invite me." }),
  makeRow({ id: "dry-spam", name: "SEO Seller", message: "We offer SEO packages and backlinks." })
]);
const result = await mod.__test.runInterestDigest({
  env: { STEEL_RAG_INTEREST_D1: d1 },
  now: new Date("2026-05-28T12:00:00.000Z"),
  dryRun: true
});
assert.equal(result.deletedSpamCount, 0);
assert.equal(result.wouldDeleteCount, 1);
assert.equal(result.rows.find((row) => row.id === "dry-spam").would_delete, true);
assert.equal(d1.operations.length, 0);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_sends_weekly_summary_when_no_rows_are_pending() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([]);
const fetchCalls = [];
const result = await mod.__test.runInterestDigest({
  env: {
    STEEL_RAG_INTEREST_D1: d1,
    PUSHOVER_APP_TOKEN: "app-token",
    PUSHOVER_USER_KEY: "user-key"
  },
  now: new Date("2026-05-28T12:00:00.000Z"),
  fetchImpl: async (url, options) => {
    fetchCalls.push({ url, options });
    return new Response("{}", { status: 200 });
  }
});
assert.equal(result.sent, true);
assert.equal(result.sentMessageCount, 1);
assert.equal(result.deletedSpamCount, 0);
assert.equal(fetchCalls.length, 1);
const body = new URLSearchParams(fetchCalls[0].options.body);
assert.match(body.get("message"), /No new real interest-list submissions/);
assert.match(body.get("message"), /Filtered as spam[/]test: 0/);
assert.equal(d1.operations.length, 0);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_splits_long_body_without_losing_content() -> None:
    script = _interest_digest_test_script(
        """
const rows = mod.__test.classifySubmissions([
  makeRow({
    id: "long-1",
    email: "long-one@steel.example",
    name: "Long One",
    message: "First complete message. ".repeat(55)
  }),
  makeRow({
    id: "long-2",
    email: "long-two@steel.example",
    name: "Long Two",
    message: "Second complete message. ".repeat(55)
  })
]);
const digest = mod.__test.buildDigestBody(rows, new Date("2026-05-28T12:00:00.000Z"));
assert.ok(digest.messages.length > 1);
assert.equal(digest.messages.join(""), digest.message);
for (const message of digest.messages) {
  assert.ok(Array.from(message).length <= 950);
}
assert.doesNotMatch(digest.message, /Digest truncated/);
assert.match(digest.message, /First complete message/);
assert.match(digest.message, /Second complete message/);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_sends_numbered_parts_before_marking_rows_notified() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({
    id: "multipart-1",
    email: "multipart@steel.example",
    name: "Multipart",
    message: "Keep every word in this long submission. ".repeat(80)
  })
]);
const fetchCalls = [];
const result = await mod.__test.runInterestDigest({
  env: {
    STEEL_RAG_INTEREST_D1: d1,
    PUSHOVER_APP_TOKEN: "app-token",
    PUSHOVER_USER_KEY: "user-key"
  },
  now: new Date("2026-05-28T12:00:00.000Z"),
  fetchImpl: async (url, options) => {
    fetchCalls.push({ url, options });
    return new Response("{}", { status: 200 });
  }
});
assert.ok(fetchCalls.length > 1);
assert.equal(result.sentMessageCount, fetchCalls.length);
for (const [index, call] of fetchCalls.entries()) {
  const body = new URLSearchParams(call.options.body);
  assert.ok(body.get("title").endsWith(` (${index + 1}/${fetchCalls.length})`));
  assert.ok(Array.from(body.get("message")).length <= 950);
}
assert.equal(d1.operations.some((op) => /notified_at/.test(op.sql)), true);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_partial_multipart_failure_does_not_mark_rows_notified() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({
    id: "multipart-failure",
    email: "multipart-failure@steel.example",
    name: "Multipart Failure",
    message: "This multipart digest must finish before notification. ".repeat(80)
  })
]);
let fetchCount = 0;
await assert.rejects(
  () => mod.__test.runInterestDigest({
    env: {
      STEEL_RAG_INTEREST_D1: d1,
      PUSHOVER_APP_TOKEN: "app-token",
      PUSHOVER_USER_KEY: "user-key"
    },
    now: new Date("2026-05-28T12:00:00.000Z"),
    fetchImpl: async () => {
      fetchCount += 1;
      return new Response(fetchCount === 2 ? "bad" : "{}", { status: fetchCount === 2 ? 500 : 200 });
    }
  }),
  /part 2[/]/
);
assert.equal(fetchCount, 2);
assert.equal(d1.operations.some((op) => /notified_at/.test(op.sql)), false);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_durable_retry_sends_only_unsent_parts() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeDurableD1([
  makeRow({
    id: "durable-retry",
    email: "durable@steel.example",
    name: "Durable Retry",
    message: "Keep each successful digest part exactly once. ".repeat(80)
  })
]);
let firstAttemptCalls = 0;
await assert.rejects(
  () => mod.__test.runInterestDigest({
    env: {
      STEEL_RAG_INTEREST_D1: d1,
      PUSHOVER_APP_TOKEN: "app-token",
      PUSHOVER_USER_KEY: "user-key"
    },
    now: new Date("2026-07-13T14:00:00.000Z"),
    fetchImpl: async () => {
      firstAttemptCalls += 1;
      return new Response(firstAttemptCalls === 2 ? "bad" : "{}", {
        status: firstAttemptCalls === 2 ? 500 : 200
      });
    }
  }),
  /part 2[/]/
);
const afterFailure = [...d1.state.parts.values()].sort((a, b) => a.part_index - b.part_index);
assert.ok(afterFailure.length > 2);
assert.equal(afterFailure[0].status, "sent");
assert.equal(afterFailure[1].status, "failed");
assert.equal(d1.state.rows[0].notified_at, null);
const firstPartHash = afterFailure[0].content_hash;
let retryCalls = 0;
const retryResult = await mod.__test.runInterestDigest({
  env: {
    STEEL_RAG_INTEREST_D1: d1,
    PUSHOVER_APP_TOKEN: "app-token",
    PUSHOVER_USER_KEY: "user-key"
  },
  now: new Date("2026-07-20T14:05:00.000Z"),
  fetchImpl: async () => {
    retryCalls += 1;
    return new Response("{}", { status: 200 });
  }
});
const completedParts = [...d1.state.parts.values()].sort((a, b) => a.part_index - b.part_index);
assert.equal(retryCalls, completedParts.length - 1);
assert.equal(completedParts[0].content_hash, firstPartHash);
assert.equal(completedParts[0].attempts, 1);
assert.equal(completedParts[1].attempts, 2);
assert.ok(completedParts.every((part) => part.status === "sent"));
assert.equal(retryResult.sentMessageCount, completedParts.length - 1);
assert.equal(d1.state.rows[0].status, "notified");
assert.ok(d1.state.rows[0].notified_at);
assert.ok(d1.state.batchCalls >= 6);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_durable_claim_prevents_concurrent_and_ambiguous_retries() -> None:
    script = _interest_digest_test_script(
        """
const concurrentD1 = makeDurableD1([
  makeRow({ id: "concurrent", email: "concurrent@steel.example", name: "Concurrent" })
]);
let releaseSend;
let markSendStarted;
const sendGate = new Promise((resolve) => { releaseSend = resolve; });
const sendStarted = new Promise((resolve) => { markSendStarted = resolve; });
const env = {
  STEEL_RAG_INTEREST_D1: concurrentD1,
  PUSHOVER_APP_TOKEN: "app-token",
  PUSHOVER_USER_KEY: "user-key"
};
const firstRun = mod.__test.runInterestDigest({
  env,
  now: new Date("2026-07-13T14:00:00.000Z"),
  fetchImpl: async () => {
    markSendStarted();
    await sendGate;
    return new Response("{}", { status: 200 });
  }
});
await sendStarted;
let secondFetchCalled = false;
const secondRun = await mod.__test.runInterestDigest({
  env,
  now: new Date("2026-07-13T14:01:00.000Z"),
  fetchImpl: async () => {
    secondFetchCalled = true;
    return new Response("{}", { status: 200 });
  }
});
assert.equal(secondRun.duplicatePrevented, true);
assert.equal(secondFetchCalled, false);
releaseSend();
await firstRun;

const ambiguousD1 = makeDurableD1([
  makeRow({ id: "ambiguous", email: "ambiguous@steel.example", name: "Ambiguous" })
]);
const ambiguousEnv = { ...env, STEEL_RAG_INTEREST_D1: ambiguousD1 };
await assert.rejects(
  () => mod.__test.runInterestDigest({
    env: ambiguousEnv,
    now: new Date("2026-07-13T14:00:00.000Z"),
    fetchImpl: async () => { throw new TypeError("network connection closed"); }
  }),
  /network connection closed/
);
let ambiguousRetryFetchCalled = false;
const ambiguousRetry = await mod.__test.runInterestDigest({
  env: ambiguousEnv,
  now: new Date("2026-07-13T14:02:00.000Z"),
  fetchImpl: async () => {
    ambiguousRetryFetchCalled = true;
    return new Response("{}", { status: 200 });
  }
});
assert.equal(ambiguousRetry.duplicatePrevented, true);
assert.equal(ambiguousRetry.deliveryStatus, "ambiguous");
assert.equal(ambiguousRetryFetchCalled, false);
assert.equal([...ambiguousD1.state.parts.values()][0].status, "ambiguous");
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_missing_pushover_secrets_fails_without_notifying() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({ id: "real-missing-secret", email: "player@steel.example", name: "Paul" })
]);
await assert.rejects(
  () => mod.__test.runInterestDigest({
    env: { STEEL_RAG_INTEREST_D1: d1 },
    now: new Date("2026-05-28T12:00:00.000Z"),
    fetchImpl: async () => new Response("{}", { status: 200 })
  }),
  /Missing Pushover credentials/
);
assert.equal(d1.operations.some((op) => /notified_at/.test(op.sql)), false);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_dry_run_endpoint_previews_without_notifying() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({ id: "dry-1", email: "dry@steel.example", name: "Dry Run" })
]);
const response = await mod.default.fetch(
  new Request("http://localhost/dry-run", {
    method: "GET",
    headers: { Authorization: "Bearer admin-token" }
  }),
  {
    STEEL_RAG_INTEREST_D1: d1,
    INTEREST_DIGEST_ADMIN_TOKEN: "admin-token",
    INTEREST_DIGEST_LOCAL_ACCESS_BYPASS: "1"
  }
);
const payload = await response.json();
assert.equal(response.status, 200);
assert.equal(payload.ok, true);
assert.equal(payload.dryRun, true);
assert.equal(payload.sent, false);
assert.equal(payload.includedCount, 1);
assert.equal(payload.rows[0].email, "dry@steel.example");
assert.equal(d1.operations.some((op) => /notified_at/.test(op.sql)), false);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_dry_run_requires_admin_token() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({ id: "dry-2", email: "dry@steel.example", name: "Dry Run" })
]);
const response = await mod.default.fetch(
  new Request("https://steel-rag-interest-digest.example/dry-run", { method: "GET" }),
  {
    STEEL_RAG_INTEREST_D1: d1,
    INTEREST_DIGEST_ADMIN_TOKEN: "admin-token"
  }
);
const payload = await response.json();
assert.equal(response.status, 403);
assert.deepEqual(payload, { ok: false, error: "forbidden" });
assert.equal(d1.operations.length, 0);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_production_dry_run_requires_valid_access_jwt_and_admin_token() -> None:
    script = _interest_digest_test_script(
        """
const identity = await makeAccessIdentity({ issuer: `https://prod-${crypto.randomUUID()}.cloudflareaccess.com` });
const d1 = makeD1([makeRow({ id: "access-dry-run", email: "access@steel.example" })]);
const originalFetch = globalThis.fetch;
globalThis.fetch = async (url) => {
  assert.equal(String(url), identity.env.INTEREST_DIGEST_ACCESS_JWKS_URL);
  return new Response(JSON.stringify({ keys: [identity.jwk] }), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
};
try {
  const response = await mod.default.fetch(
    new Request("https://steel-rag-interest-digest.example/dry-run", {
      method: "GET",
      headers: {
        Authorization: "Bearer admin-token",
        "Cf-Access-Jwt-Assertion": identity.token
      }
    }),
    {
      STEEL_RAG_INTEREST_D1: d1,
      INTEREST_DIGEST_ADMIN_TOKEN: "admin-token",
      ...identity.env
    }
  );
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.dryRun, true);
  assert.equal(payload.rows.length, 1);
} finally {
  globalThis.fetch = originalFetch;
}
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_access_jwt_rejects_expiry_and_refreshes_rotated_key() -> None:
    script = _interest_digest_test_script(
        """
const issuer = `https://rotation-${crypto.randomUUID()}.cloudflareaccess.com`;
const kid = "rotating-key";
const first = await makeAccessIdentity({ issuer, kid });
const second = await makeAccessIdentity({ issuer, kid });
const expired = await makeAccessIdentity({ issuer, kid: "expired-key", exp: Math.floor(Date.now() / 1000) - 1 });
let fetchCount = 0;
const rotatingFetch = async () => {
  fetchCount += 1;
  return new Response(JSON.stringify({ keys: [fetchCount === 1 ? first.jwk : second.jwk] }), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
};
const requestFor = (token) => new Request("https://steel-rag-interest-digest.example/dry-run", {
  headers: { "Cf-Access-Jwt-Assertion": token }
});
assert.equal(await mod.__test.requestHasAccessIdentity(requestFor(first.token), first.env, rotatingFetch), true);
assert.equal(await mod.__test.requestHasAccessIdentity(requestFor(second.token), second.env, rotatingFetch), true);
assert.equal(fetchCount, 2);
assert.equal(await mod.__test.requestHasAccessIdentity(requestFor(expired.token), expired.env, rotatingFetch), false);
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_manual_run_endpoint_sends_and_notifies() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({ id: "run-1", email: "run@steel.example", name: "Manual Run" })
]);
const fetchCalls = [];
const originalFetch = globalThis.fetch;
globalThis.fetch = async (url, options) => {
  fetchCalls.push({ url, options });
  return new Response("{}", { status: 200 });
};
try {
  const response = await mod.default.fetch(
    new Request("http://localhost/run", {
      method: "POST",
      headers: { "x-interest-digest-token": "admin-token" }
    }),
    {
      STEEL_RAG_INTEREST_D1: d1,
      PUSHOVER_APP_TOKEN: "pushover-app-secret",
      PUSHOVER_USER_KEY: "pushover-user-secret",
      INTEREST_DIGEST_ADMIN_TOKEN: "admin-token",
      INTEREST_DIGEST_LOCAL_ACCESS_BYPASS: "1"
    }
  );
  const text = await response.text();
  const payload = JSON.parse(text);
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.dryRun, false);
  assert.equal(payload.sent, true);
  assert.equal(fetchCalls.length, 1);
  assert.equal(d1.operations.some((op) => /notified_at/.test(op.sql)), true);
  assert.doesNotMatch(text, /pushover-app-secret/);
  assert.doesNotMatch(text, /pushover-user-secret/);
} finally {
  globalThis.fetch = originalFetch;
}
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_manual_run_requires_admin_token() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({ id: "run-2", email: "run@steel.example", name: "Manual Run" })
]);
const originalFetch = globalThis.fetch;
let fetchCalled = false;
globalThis.fetch = async () => {
  fetchCalled = true;
  return new Response("{}", { status: 200 });
};
try {
  const response = await mod.default.fetch(
    new Request("https://steel-rag-interest-digest.example/run", { method: "POST" }),
    {
      STEEL_RAG_INTEREST_D1: d1,
      PUSHOVER_APP_TOKEN: "pushover-app-secret",
      PUSHOVER_USER_KEY: "pushover-user-secret",
      INTEREST_DIGEST_ADMIN_TOKEN: "admin-token"
    }
  );
  const payload = await response.json();
  assert.equal(response.status, 403);
  assert.deepEqual(payload, { ok: false, error: "forbidden" });
  assert.equal(fetchCalled, false);
  assert.equal(d1.operations.length, 0);
} finally {
  globalThis.fetch = originalFetch;
}
"""
    )

    result = subprocess.run(["node", "-e", script], cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_interest_digest_manual_run_failure_does_not_expose_pushover_secrets() -> None:
    script = _interest_digest_test_script(
        """
const d1 = makeD1([
  makeRow({ id: "run-3", email: "run@steel.example", name: "Manual Run" })
]);
const originalFetch = globalThis.fetch;
globalThis.fetch = async () => new Response("bad", { status: 500 });
try {
  const response = await mod.default.fetch(
    new Request("http://localhost/run", {
      method: "POST",
      headers: { Authorization: "Bearer admin-token" }
    }),
    {
      STEEL_RAG_INTEREST_D1: d1,
      PUSHOVER_APP_TOKEN: "pushover-app-secret",
      PUSHOVER_USER_KEY: "pushover-user-secret",
      INTEREST_DIGEST_ADMIN_TOKEN: "admin-token",
      INTEREST_DIGEST_LOCAL_ACCESS_BYPASS: "1"
    }
  );
  const text = await response.text();
  assert.equal(response.status, 500);
  assert.deepEqual(JSON.parse(text), { ok: false, error: "run_failed" });
  assert.doesNotMatch(text, /pushover-app-secret/);
  assert.doesNotMatch(text, /pushover-user-secret/);
  assert.equal(d1.operations.some((op) => /notified_at/.test(op.sql)), false);
} finally {
  globalThis.fetch = originalFetch;
}
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
            return {{ success: true, meta: {{ changes: 1 }} }};
          }}
        }})
      }})
    }};
  }}

  function makeDurableD1(inputRows) {{
    const state = {{
      rows: inputRows.map((row) => ({{ ...row }})),
      deliveries: new Map(),
      parts: new Map(),
      operations: [],
      batchCalls: 0
    }};
    const result = (changes = 0, results = []) => ({{ success: true, results, meta: {{ changes }} }});
    const normalizedSql = (sql) => sql.replace(/\\s+/g, " ").trim().toLowerCase();
    const partsFor = (deliveryId) => [...state.parts.values()]
      .filter((part) => part.delivery_id === deliveryId)
      .sort((left, right) => left.part_index - right.part_index);
    const canComplete = (deliveryId, claimToken) => {{
      const delivery = state.deliveries.get(deliveryId);
      return Boolean(
        delivery && delivery.claim_token === claimToken && delivery.status === "sending" &&
        partsFor(deliveryId).every((part) => part.status === "sent")
      );
    }};
    const execute = (statement) => {{
      const {{ sql, values }} = statement;
      const compact = normalizedSql(sql);
      state.operations.push({{ sql, values }});

      if (compact.startsWith("select id, created_at") && compact.includes("from interest_submissions")) {{
        return result(0, state.rows
          .filter((row) => row.notified_at == null && ["new", "review", "spam", "test"].includes(String(row.status || "new").toLowerCase()))
          .sort((left, right) => String(left.created_at).localeCompare(String(right.created_at)))
          .map((row) => ({{ ...row }})));
      }}
      if (compact === "select id from interest_digest_deliveries where status != 'sent' order by window_start asc limit 1") {{
        const delivery = [...state.deliveries.values()]
          .filter((candidate) => candidate.status !== "sent")
          .sort((left, right) => left.window_start.localeCompare(right.window_start))[0];
        return result(0, delivery ? [{{ id: delivery.id }}] : []);
      }}
      if (compact.startsWith("select id, window_start") && compact.includes("from interest_digest_deliveries")) {{
        const delivery = state.deliveries.get(values[0]);
        return result(0, delivery ? [{{ ...delivery }}] : []);
      }}
      if (compact.startsWith("select delivery_id, part_index") && compact.includes("from interest_digest_delivery_parts")) {{
        return result(0, partsFor(values[0]).map((part) => ({{ ...part }})));
      }}
      if (compact.startsWith("insert into interest_digest_deliveries")) {{
        const [id, windowStart, windowEnd, contentHash, title, includedRowIds, createdAt, updatedAt] = values;
        const exists = [...state.deliveries.values()].some(
          (delivery) => delivery.window_start === windowStart && delivery.window_end === windowEnd
        );
        if (exists) return result(0);
        state.deliveries.set(id, {{
          id, window_start: windowStart, window_end: windowEnd, content_hash: contentHash,
          title, included_row_ids_json: includedRowIds, status: "pending", claim_token: null,
          claimed_at: null, lease_expires_at: null, completed_at: null, last_error: null,
          created_at: createdAt, updated_at: updatedAt
        }});
        return result(1);
      }}
      if (compact.startsWith("insert into interest_digest_delivery_parts")) {{
        const [deliveryId, partIndex, partCount, contentHash, title, message, createdAt, updatedAt] = values;
        const key = `${{deliveryId}}:${{partIndex}}`;
        if (state.parts.has(key)) return result(0);
        state.parts.set(key, {{
          delivery_id: deliveryId, part_index: partIndex, part_count: partCount,
          content_hash: contentHash, title, message, status: "pending", attempts: 0,
          attempt_started_at: null, sent_at: null, last_error: null,
          created_at: createdAt, updated_at: updatedAt
        }});
        return result(1);
      }}
      if (compact.startsWith("update interest_digest_deliveries") && compact.includes("set status = 'sending'")) {{
        const [claimToken, claimedAt, leaseExpiresAt, updatedAt, deliveryId, nowIso] = values;
        const delivery = state.deliveries.get(deliveryId);
        const blockedPart = partsFor(deliveryId).some((part) => ["sending", "ambiguous"].includes(part.status));
        const leaseAvailable = !delivery?.claim_token || !delivery?.lease_expires_at || delivery.lease_expires_at <= nowIso;
        if (!delivery || delivery.status === "sent" || blockedPart || !leaseAvailable) return result(0);
        Object.assign(delivery, {{
          status: "sending", claim_token: claimToken, claimed_at: claimedAt,
          lease_expires_at: leaseExpiresAt, last_error: null, updated_at: updatedAt
        }});
        return result(1);
      }}
      if (compact.startsWith("delete from interest_submissions")) {{
        const index = state.rows.findIndex((row) => row.id === values[0] && row.notified_at == null);
        if (index < 0) return result(0);
        state.rows.splice(index, 1);
        return result(1);
      }}
      if (compact.startsWith("update interest_submissions") && compact.includes("set status = ?, spam_score")) {{
        const row = state.rows.find((candidate) => candidate.id === values[3]);
        if (!row) return result(0);
        [row.status, row.spam_score, row.admin_notes] = values.slice(0, 3);
        return result(1);
      }}
      if (compact.startsWith("update interest_digest_delivery_parts") && compact.includes("set status = 'sending'")) {{
        const [attemptAt, updatedAt, deliveryId, partIndex, guardDeliveryId, claimToken] = values;
        const part = state.parts.get(`${{deliveryId}}:${{partIndex}}`);
        const delivery = state.deliveries.get(guardDeliveryId);
        if (!part || !["pending", "failed"].includes(part.status) || delivery?.claim_token !== claimToken || delivery.status !== "sending") return result(0);
        Object.assign(part, {{
          status: "sending", attempts: part.attempts + 1, attempt_started_at: attemptAt,
          last_error: null, updated_at: updatedAt
        }});
        return result(1);
      }}
      if (compact.startsWith("update interest_digest_delivery_parts") && compact.includes("set status = 'sent'")) {{
        const [sentAt, updatedAt, deliveryId, partIndex] = values;
        const part = state.parts.get(`${{deliveryId}}:${{partIndex}}`);
        if (!part || part.status !== "sending") return result(0);
        Object.assign(part, {{ status: "sent", sent_at: sentAt, last_error: null, updated_at: updatedAt }});
        return result(1);
      }}
      if (compact.startsWith("update interest_digest_delivery_parts") && compact.includes("set status = ?, last_error")) {{
        const [status, lastError, updatedAt, deliveryId, partIndex] = values;
        const part = state.parts.get(`${{deliveryId}}:${{partIndex}}`);
        if (!part || part.status !== "sending") return result(0);
        Object.assign(part, {{ status, last_error: lastError, updated_at: updatedAt }});
        return result(1);
      }}
      if (compact.startsWith("update interest_digest_deliveries") && compact.includes("set status = ?, claim_token = null")) {{
        const [status, lastError, updatedAt, deliveryId, claimToken] = values;
        const delivery = state.deliveries.get(deliveryId);
        if (!delivery || delivery.claim_token !== claimToken) return result(0);
        Object.assign(delivery, {{
          status, claim_token: null, lease_expires_at: null,
          last_error: lastError, updated_at: updatedAt
        }});
        return result(1);
      }}
      if (compact.startsWith("update interest_submissions") && compact.includes("set notified_at = ?")) {{
        const [notifiedAt, rowId, deliveryId, claimToken] = values;
        if (!canComplete(deliveryId, claimToken)) return result(0);
        const row = state.rows.find((candidate) => candidate.id === rowId);
        if (!row) return result(0);
        row.notified_at = notifiedAt;
        if (String(row.status || "new").toLowerCase() !== "review") row.status = "notified";
        return result(1);
      }}
      if (compact.startsWith("update interest_digest_deliveries") && compact.includes("set status = 'sent'")) {{
        const [completedAt, updatedAt, deliveryId, claimToken] = values;
        const delivery = state.deliveries.get(deliveryId);
        if (!canComplete(deliveryId, claimToken)) return result(0);
        Object.assign(delivery, {{
          status: "sent", claim_token: null, lease_expires_at: null,
          completed_at: completedAt, last_error: null, updated_at: updatedAt
        }});
        return result(1);
      }}
      if (compact.startsWith("update interest_digest_deliveries set updated_at")) {{
        const [updatedAt, deliveryId, claimToken] = values;
        const delivery = state.deliveries.get(deliveryId);
        if (!delivery || delivery.claim_token !== claimToken || delivery.status !== "sending") return result(0);
        delivery.updated_at = updatedAt;
        return result(1);
      }}
      throw new Error(`Unhandled durable D1 statement: ${{compact}}`);
    }};
    const prepare = (sql) => ({{
      bind: (...values) => {{
        const statement = {{ sql, values }};
        statement.all = async () => execute(statement);
        statement.run = async () => execute(statement);
        return statement;
      }}
    }});
    return {{
      state,
      prepare,
      batch: async (statements) => {{
        state.batchCalls += 1;
        return statements.map(execute);
      }}
    }};
  }}

  function base64Url(value) {{
    return Buffer.from(value)
      .toString("base64")
      .replace(/[+]/g, "-")
      .replace(/[/]/g, "_")
      .replace(/=+$/g, "");
  }}

  async function makeAccessIdentity(overrides = {{}}) {{
    const issuer = overrides.issuer || "https://steel.cloudflareaccess.com";
    const audience = overrides.audience || "interest-digest-aud";
    const kid = overrides.kid || `kid-${{crypto.randomUUID()}}`;
    const keyPair = overrides.keyPair || await crypto.subtle.generateKey(
      {{ name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }},
      true,
      ["sign", "verify"]
    );
    const header = base64Url(JSON.stringify({{ alg: "RS256", kid, typ: "JWT" }}));
    const now = Math.floor(Date.now() / 1000);
    const claims = base64Url(JSON.stringify({{
      iss: issuer,
      aud: [audience],
      exp: overrides.exp ?? now + 300,
      nbf: overrides.nbf ?? now - 5,
      sub: "service-token",
      type: "service_token"
    }}));
    const signingInput = `${{header}}.${{claims}}`;
    const signature = await crypto.subtle.sign(
      "RSASSA-PKCS1-v1_5",
      keyPair.privateKey,
      new TextEncoder().encode(signingInput)
    );
    const jwk = await crypto.subtle.exportKey("jwk", keyPair.publicKey);
    return {{
      token: `${{signingInput}}.${{base64Url(new Uint8Array(signature))}}`,
      jwk: {{ ...jwk, kid, alg: "RS256", use: "sig" }},
      keyPair,
      env: {{
        INTEREST_DIGEST_ACCESS_ISSUER: issuer,
        INTEREST_DIGEST_ACCESS_AUD: audience,
        INTEREST_DIGEST_ACCESS_JWKS_URL: `${{issuer}}/cdn-cgi/access/certs`
      }}
    }};
  }}

  {body}
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});
"""
