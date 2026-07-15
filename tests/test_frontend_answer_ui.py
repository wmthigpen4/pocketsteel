from __future__ import annotations

import gzip
import hashlib
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
    authenticated: true,
    role: "beta_user",
    features: { melodyExercise: true, melodyCatalog: true, melodyImport: false }
  }).features), JSON.stringify({ melodyExercise: true, melodyCatalog: true }));

  assert.equal(JSON.stringify(answerUi.normalizeSessionResponse({
    authenticated: true,
    role: "beta_user",
    features: { accountCopedents: true },
    account: { id: "acct_opaque", passId: "creator", passLabel: "Creator Access", entitlementSource: "creator_grant", billingManaged: false },
    entitlements: ["copedent.custom.use", "copedent.custom.manage", "copedent.custom.use"]
  })), JSON.stringify({
    authenticated: true,
    role: "beta_user",
    authProvider: "local_dev",
    features: { accountCopedents: true },
    account: { id: "acct_opaque", passId: "creator", passLabel: "Creator Access", entitlementSource: "creator_grant", billingManaged: false },
    entitlements: ["copedent.custom.use", "copedent.custom.manage"]
  }));

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


def test_frontend_answer_client_fetches_and_validates_monthly_usage() -> None:
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
  const usage = await answerUi.requestAccountUsage({
    accessRole: "beta_user",
    fetchImpl: async (url, options) => {
      capturedRequest = { url, options };
      return {
        ok: true,
        status: 200,
        json: async () => ({
          schemaVersion: "account_usage_v1",
          period: {
            startsAt: "2026-07-01T00:00:00+00:00",
            resetsAt: "2026-08-01T00:00:00+00:00"
          },
          usage: {
            successfulAnswers: 42,
            recentActivity: { eventType: "melody.edited", occurredAt: "2026-07-14T16:30:00+00:00", count: 2 },
            recentConnectedRoute: [
              { eventType: "connected.answer_to_explorer", occurredAt: "2026-07-14T16:20:00+00:00", count: 1 }
            ]
          },
          updatedAt: "2026-07-14T16:30:00+00:00"
        })
      };
    }
  });

  assert.equal(capturedRequest.url, "/api/account/usage");
  assert.equal(capturedRequest.options.method, "GET");
  assert.equal(capturedRequest.options.credentials, "same-origin");
  assert.equal(capturedRequest.options.headers["X-Steel-Rag-Dev-Access-Role"], "beta_user");
  assert.equal(usage.schemaVersion, "account_usage_v1");
  assert.equal(usage.startsAt, "2026-07-01T00:00:00+00:00");
  assert.equal(usage.resetsAt, "2026-08-01T00:00:00+00:00");
  assert.equal(usage.successfulAnswers, 42);
  assert.equal(usage.activity.explorer.ideasExplored, 0);
  assert.equal(usage.activity.aiAssisted.actions, 0);
  assert.equal(usage.recentActivity.eventType, "melody.edited");
  assert.equal(usage.recentConnectedRoute[0].eventType, "connected.answer_to_explorer");
  assert.equal(usage.updatedAt, "2026-07-14T16:30:00+00:00");

  assert.equal(JSON.stringify(answerUi.normalizeSessionResponse({
    authenticated: true,
    role: "beta_user",
    features: { accountUsage: true }
  }).features), JSON.stringify({ accountUsage: true }));

  assert.throws(() => answerUi.normalizeAccountUsageResponse({
    period: { startsAt: "2026-07-01T00:00:00+00:00" },
    usage: { successfulAnswers: 42 }
  }), /invalid/);
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


def test_backstage_plan_and_activity_has_honest_states_without_mock_counts() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert "Plan &amp; Activity" in html
    assert "Your activity this month" in html
    assert "Checking this month’s activity…" in html
    assert "Monthly activity is available for verified accounts." in html
    assert "Activity tracking is temporarily unavailable." in html
    assert 'id="usage-answer-count"' in html
    assert 'id="usage-reset-date"' in html
    assert 'id="activity-explorer-ideas">0</strong>' in html
    assert 'id="activity-ai-actions">0 this month</strong>' in html
    assert "No monthly limit is enforced." in html
    assert "function refreshMonthlyUsage()" in html
    assert 'tabName === "overview" || tabName === "pass"' in html
    assert "STEEL_RAG_ANSWER_UI.requestAccountUsage" in html
    assert "Standing Room" not in html
    assert "Bandleader Pass" not in html
    assert "Monthly Ask Usage" not in html
    assert "Premium responses remaining" not in html
    assert "Estimated monthly usage" not in html
    assert "Questions used this period" not in html
    assert "AI Usage" not in html


def test_backstage_plan_and_activity_uses_all_approved_assets() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    asset_version = "plan-activity-artwork-20260714-2"
    for name in (
        "pass-ticket.png",
        "fretboard-activity.png",
        "melody-activity.png",
        "lessons-activity.png",
        "brain-activity.png",
        "connected-learning.png",
        "ai-assisted.png",
    ):
        path = Path("ui/assets/backstage") / name
        assert path.is_file()
        assert f'src="assets/backstage/{name}?v={asset_version}" alt=""' in html
        assert f'src="assets/backstage/{name}" alt=""' not in html
        assert path.read_bytes().startswith(b"\x89PNG")


def test_backstage_overview_is_a_truthful_control_room_with_real_state_hooks() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    overview = html.split('id="backstage-panel-overview"', 1)[1].split('id="backstage-panel-setup"', 1)[0]

    assert "Ready to play" in overview
    assert "Your backstage is set. Pick up where you left off." in overview
    assert 'src="assets/backstage/overview-road-case.png?v=control-room-20260714-1" alt="" width="1672" height="941"' in overview
    assert "hanging" not in overview.lower()
    assert "BACKSTAGE ALL ACCESS" not in overview
    for state_id in (
        "copedent-overview-summary",
        "overview-account-status",
        "backstage-overview-pass-badge",
        "overview-last-workspace",
        "overview-continue-cta",
    ):
        assert f'id="{state_id}"' in overview
    for station in ("My Setup", "Plan &amp; Activity", "Feedback", "Account"):
        assert station in overview
    for destination in ("setup", "pass", "feedback", "account"):
        assert f'data-backstage-jump="{destination}"' in overview
    assert "No connected learning route yet." in overview
    assert 'id="overview-resume-route"' in overview and " hidden>" in overview
    assert "upgrade" not in overview.lower()
    assert "billing" not in overview.lower()

    assert "const overviewActivityDestinations = {" in html
    assert '"connected.answer_to_explorer"' in html
    assert '"connected.explorer_to_melody"' in html
    assert "renderOverviewActivity(usage);" in html
    assert 'overviewRouteEmpty.hidden = route.length > 0;' in html
    assert 'overviewResumeRoute.hidden = route.length === 0;' in html
    assert 'overviewAccountStatus.textContent = verifiedAccount ? "Verified login" : "Local preview";' in html


def test_backstage_overview_road_case_is_rgba_with_transparent_left_field() -> None:
    from PIL import Image

    asset = Path("ui/assets/backstage/overview-road-case.png")
    with Image.open(asset) as image:
        assert image.mode == "RGBA"
        assert image.size == (1672, 941)
        alpha = image.getchannel("A")
        assert alpha.getpixel((0, 0)) == 0
        assert alpha.getpixel((image.width - 1, image.height - 1)) > 0
        assert alpha.getbbox() == (574, 11, 1672, 941)


def test_backstage_overview_has_responsive_control_room_layout() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert ".overview-stations {" in html
    assert "grid-template-columns: repeat(4, minmax(0, 1fr));" in html
    assert ".overview-road-case {" in html
    assert "object-fit: contain;" in html
    assert "@media (max-width: 640px)" in html
    assert ".overview-road-case { position: relative;" in html
    assert ".overview-stations { grid-template-columns: 1fr; }" in html
    assert ".overview-primary-cta:focus-visible" in html


def test_backstage_feedback_is_an_accessible_talkback_workspace() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    feedback_match = re.search(
        r'id="backstage-panel-feedback".*?hidden>(.*?)\n\s*</div>\n\n\s*</div>\n\n\s*<div class="backstage-content backstage-tab-panel" id="backstage-panel-account"',
        html,
        re.DOTALL,
    )
    assert feedback_match is not None
    feedback_panel = feedback_match.group(1)

    assert "Talk to the crew" in feedback_panel
    assert "Tell us what helped, what missed, or where the steel-guitar reasoning needs more work." in feedback_panel
    assert feedback_panel.count('name="feedback-category"') == 4
    assert 'value="answer-quality" checked' in feedback_panel
    assert 'value="missing-source"' in feedback_panel
    assert 'value="wrong-steel-logic"' in feedback_panel
    assert 'value="ux-product-issue"' in feedback_panel
    assert "Answer quality" in feedback_panel
    assert "Missing or weak source" in feedback_panel
    assert "Wrong steel logic" in feedback_panel
    assert "UX or product issue" in feedback_panel

    assert 'for="backstage-feedback-message"' in feedback_panel
    assert 'id="backstage-feedback-message" maxlength="2000"' in feedback_panel
    assert 'aria-describedby="backstage-feedback-help backstage-feedback-count"' in feedback_panel
    assert 'id="backstage-feedback-count"' in feedback_panel
    assert "0 / 2000" in feedback_panel
    assert "function updateBackstageFeedbackCount()" in html
    assert 'backstageFeedbackMessage.addEventListener("input", updateBackstageFeedbackCount)' in html

    assert "Include context" not in feedback_panel
    assert 'id="backstage-feedback-current-page"' not in feedback_panel
    assert 'id="backstage-feedback-browser"' not in feedback_panel
    assert 'name="feedback-impact"' not in feedback_panel
    assert "How did this affect your session?" not in feedback_panel
    assert 'class="feedback-submit-button" type="button" disabled' in feedback_panel
    assert "Send feedback · coming soon" in feedback_panel
    assert "Feedback submission is not connected yet." in feedback_panel
    assert "your feedback type and message" in feedback_panel
    assert "Mock only" not in feedback_panel
    assert "claim success" not in feedback_panel
    assert "<img" not in feedback_panel
    assert feedback_panel.count("<svg") >= 9


def test_backstage_feedback_uses_native_single_selection_and_session_only_draft_state() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert 'type="radio" name="feedback-category"' in html
    assert 'type="radio" name="feedback-impact"' not in html
    assert '.feedback-choice > input:focus-visible + .feedback-choice-content' in html
    assert '.feedback-choice > input:checked + .feedback-choice-content' in html
    assert "localStorage.setItem(\"backstage-feedback" not in html
    assert "sessionStorage.setItem(\"backstage-feedback" not in html
    assert "backstageFeedbackMessage.value =" not in html
    assert "backstageFeedbackMessage.value.length" in html
    assert 'grid-template-columns: minmax(0, 1fr) minmax(260px, 0.3fr)' in html
    assert re.search(r"\.feedback-choice\s*\{[^}]*height: 100%;", html, re.DOTALL)
    assert re.search(r"\.feedback-choice-content\s*\{[^}]*height: 100%;", html, re.DOTALL)
    assert re.search(r"\.feedback-category-grid\s*\{[^}]*grid-auto-rows: 1fr;", html, re.DOTALL)
    assert ".feedback-talkback," in html
    assert ".feedback-category-grid {" in html


def test_backstage_account_uses_verified_credential_ui_without_fabricated_controls() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    account_match = re.search(
        r'id="backstage-panel-account".*?hidden>(.*?)\n        </div>\n\n      </section>',
        html,
        re.DOTALL,
    )
    assert account_match is not None
    account_panel = account_match.group(1)

    assert 'src="assets/backstage/artist-credentials.png?v=artist-credentials-20260714-1"' in account_panel
    assert 'alt="" width="1122" height="1402"' in account_panel
    assert "object-fit: contain" in html
    assert "Player account" in account_panel
    assert "Connected account services" in account_panel
    assert "Access provider" in account_panel
    assert "Saved copedents" in account_panel
    assert "Last synchronization" not in account_panel
    assert "Active device" not in account_panel
    assert "Login verification" not in account_panel
    assert "Setup ownership" in account_panel
    assert "Data &amp; privacy summary" in account_panel
    assert "Delete account · coming soon" in account_panel
    assert 'class="account-control-button is-destructive" type="button" disabled' in account_panel
    assert 'id="backstage-copy-account-row"' not in account_panel
    assert "Password and billing controls remain with the login or future billing provider." not in account_panel
    assert 'class="account-info-footer"' not in account_panel
    assert 'backstageAccountHeading.textContent = verifiedAccount ? "Account connected" : "Sign in required";' in html
    assert 'backstageAccountStatusLabel.textContent = verifiedAccount ? "Verified access" : "Not connected";' in html
    assert 'backstageAccountLogin.textContent = verifiedAccount ? "Connected" : "Not connected";' in html
    assert 'backstageAccountBacked.textContent = verifiedAccount ? "Confirmed" : "Unavailable";' in html
    assert re.search(r"\.account-status-icon svg\s*\{[^}]*display: block;[^}]*margin: auto;", html, re.DOTALL)
    assert re.search(r"\.account-control-button\.is-destructive\s*\{[^}]*margin: 0;[^}]*border: 0;[^}]*padding: 0;", html, re.DOTALL)
    assert "Sign out" not in account_panel
    assert "Manage password" not in account_panel
    assert "Payment" not in account_panel
    assert "Bandleader" not in account_panel


def test_backstage_account_masks_identifier_and_copies_only_authorized_runtime_value() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert 'let currentAuthorizedAccountId = "";' in html
    assert "function maskAccountId(value)" in html
    assert "function copyAccountIdWithSelection(accountId)" in html
    assert 'copyField.setAttribute("aria-hidden", "true")' in html
    assert 'document.execCommand("copy")' in html
    assert "copyField.remove();" in html
    assert "backstageAccountId.textContent = maskAccountId(currentAuthorizedAccountId);" in html
    assert "navigator.clipboard.writeText(currentAuthorizedAccountId)" in html
    assert "backstageCopyAccountId.disabled = !currentAuthorizedAccountId;" in html
    assert "backstageCopyAccountRow" not in html
    assert 'role="status" aria-live="polite"' in html
    assert "backstageAccountId.textContent = verifiedAccount ? (account.id || account.accountId)" not in html


def test_backstage_account_credential_asset_is_rgba_png_with_stable_dimensions() -> None:
    asset = Path("ui/assets/backstage/artist-credentials.png")
    payload = asset.read_bytes()

    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
    assert int.from_bytes(payload[16:20], "big") == 1122
    assert int.from_bytes(payload[20:24], "big") == 1402
    assert payload[25] == 6  # PNG color type RGBA; the checkerboard is not baked into the asset.


def test_backstage_my_setup_uses_live_three_stage_rig_locker_structure() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    manager = Path("ui/backstage-copedent-manager.js").read_text(encoding="utf-8")
    setup_panel = html.split('id="backstage-panel-setup"', 1)[1].split('id="backstage-panel-pass"', 1)[0]

    active_index = setup_panel.index('class="setup-stage setup-active-stage"')
    library_index = setup_panel.index('class="setup-stage setup-library-stage"')
    workbench_index = setup_panel.index('class="setup-stage setup-workbench-stage"')
    assert active_index < library_index < workbench_index
    assert "Your Active Setup" in setup_panel
    assert "Setup Library" in setup_panel
    assert "Copedent Workbench" in setup_panel
    assert 'src="assets/backstage/setup-nameplate.png?v=rig-locker-20260714-1"' in setup_panel
    assert 'backstage-copedent-manager.js?v=control-room-20260714-1' in html
    assert 'elements.activeBadge.textContent = validationLabel(currentProfile);' in manager
    assert 'alt="" width="2022" height="778"' in setup_panel
    assert 'id="setup-active-heading">Loading active setup…</h3>' in setup_panel
    assert 'id="setup-nameplate-name">Loading active setup…</span>' in setup_panel
    assert "Cory’s E9th" not in setup_panel
    assert "Cory's E9th" not in setup_panel
    assert "object-fit: contain;" in html
    assert "aspect-ratio: 2022 / 778;" in html
    assert "-webkit-line-clamp: 2;" in html
    assert 'id="copedent-library-groups"' in setup_panel
    assert 'id="copedent-local-import"' in setup_panel
    assert 'id="copedent-profile-library" hidden aria-hidden="true" tabindex="-1"' in setup_panel
    assert 'data-setup-profile="${escapeHtml(profile.id)}"' in manager
    assert 'aria-pressed="${String(selected)}"' in manager
    assert 'renderProfileGroup("Active setup"' in manager
    assert 'renderProfileGroup("Included setups"' in manager
    assert 'renderProfileGroup("Custom setups"' in manager
    assert "No browser-local setups are waiting to be imported." in manager
    assert 'input[type="checkbox"]:checked' in manager
    assert "importSelectedLocalProfiles" in manager
    assert "localProfilesForImport" in manager
    assert "profileName(active)" in manager
    assert 'elements.plateName.textContent = name;' in manager
    assert 'elements.workbenchTitle.textContent = profileName(currentProfile);' in manager
    assert 'id="copedent-grid"' in setup_panel
    assert 'id="save-copedent"' in setup_panel
    assert 'id="activate-edited-copedent"' in setup_panel
    assert 'id="add-copedent-change"' in setup_panel
    assert 'id="copedent-profile-details"' in setup_panel
    assert 'id="copedent-mobile-group"' in setup_panel


def test_backstage_setup_nameplate_is_rgba_without_opaque_checkerboard() -> None:
    asset = Path("ui/assets/backstage/setup-nameplate.png")
    payload = asset.read_bytes()

    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
    assert int.from_bytes(payload[16:20], "big") == 2022
    assert int.from_bytes(payload[20:24], "big") == 778
    assert payload[25] == 6

    from PIL import Image

    with Image.open(asset) as image:
        assert image.mode == "RGBA"
        alpha = image.getchannel("A")
        assert alpha.getpixel((0, 0)) == 0
        assert alpha.getpixel((image.width - 1, image.height - 1)) == 0
        assert alpha.getpixel((image.width // 2, image.height // 2)) == 255
        assert alpha.getbbox() is not None


def test_account_activity_client_is_bounded_and_deduplicated() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const code = fs.readFileSync("ui/account-activity.js", "utf8");
const sandbox = {
  URLSearchParams,
  Date,
  Math,
  globalThis: null,
  location: { search: "" },
  crypto: { randomUUID: () => "00000000-0000-4000-8000-000000000001" }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const tracker = vm.runInContext("STEEL_RAG_ACCOUNT_ACTIVITY", sandbox);
let calls = 0;
const fetchImpl = async () => ({ ok: true, json: async () => ({ recorded: true }) });
(async () => {
  const first = await tracker.track("lesson.started", { dedupeKey: "lesson-one", fetchImpl: async (...args) => { calls += 1; return fetchImpl(...args); } });
  const duplicate = await tracker.track("lesson.started", { dedupeKey: "lesson-one", fetchImpl: async (...args) => { calls += 1; return fetchImpl(...args); } });
  const spoofed = await tracker.track("ask.ai_assisted", { dedupeKey: "fake", fetchImpl });
  assert.equal(first, true);
  assert.equal(duplicate, false);
  assert.equal(spoofed, false);
  assert.equal(calls, 1);
})().catch((error) => { console.error(error); process.exit(1); });
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_frontend_answer_client_posts_and_normalizes_melody_exercise() -> None:
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
  const melodyRequest = {
    kind: "artist_solo_lesson",
    key: "G",
    melody: ["1", "2", "3"],
    material: { artist: "Example Artist", song: "Example Song" }
  };
  const result = await answerUi.requestAnswer("Teach this solo", {
    accessRole: "beta_user",
    requestPayload: { melodyRequest },
    fetchImpl: async (url, options) => {
      capturedRequest = { url, options };
      return {
        ok: true,
        status: 200,
        json: async () => ({
          answer: "Here is Section 1.",
          sources: [],
          melody_exercise: {
            schemaVersion: "melody_exercise_v0",
            id: "melody-g-section-1",
            status: "ready",
            kind: "artist_solo_lesson",
            title: "Example Artist — Example Song",
            sourceCopedentId: "source-e9-abc-defg-v1",
            targetCopedentId: "saved:road-e9",
            targetCopedentLabel: "Road E9",
            arrangedFor: "Road E9",
            styleFamily: "vocal_steel",
            styleLabel: "Singing Steel",
            styleReason: "Uses singing support.",
            styleCatalog: [{ id: "auto", label: "Best Fit", description: "Balanced." }, { id: "vocal_steel", label: "Singing Steel", description: "Vocal." }],
            decisionModelVersion: "melody-decision-ranker-v1",
            decisionModelStatus: "seed",
            decisionRules: { modelVersion: "melody-decision-ranker-v1" },
            material: { artist: "Example Artist", song: "Example Song" },
            renderingMode: "e9_adaptation",
            accuracy: { label: "approximate", confidence: "medium", note: "Checked against the supplied phrase." },
            section: { number: 1, total: 2, label: "Solo", hasMore: true, nextSection: 2 },
            validation: { ok: true },
            events: [{
              id: "melody-step-1",
              step: 1,
              inputToken: "1",
              resolvedNote: "G",
              scaleDegree: "1",
              technique: "pick",
              explanation: "Play G on string 4 at fret 3.",
              resolvedPitch: "G4",
              movement: "Start at fret 3.",
              performanceControls: ["road-e-raise"],
              performanceControlLabels: ["My E raise"],
              pedalControls: [],
              leverControls: ["road-e-raise"],
              controlLayout: { "road-e-raise": "RKL" },
              mechanicalNotesByString: { "4": "G" },
              mechanicalPitchesByString: { "4": 67 },
              mechanicalActions: [{ string: 4, startingPitch: "E", destinationPitch: "F", semitoneChange: 1 }],
              targetCopedentId: "saved:road-e9",
              notes: [{ string: 4, fret: 3, changes: ["road-e-raise"], changeLabels: ["My E raise"] }]
            }],
            selectedRouteId: "single-note",
            routes: [{
              id: "single-note",
              label: "Playable single-note melody",
              harmonyType: "single_note",
              arrangedFor: "Road E9",
              sourceCopedentId: "source-e9-abc-defg-v1",
              targetCopedentId: "saved:road-e9",
              styleFamily: "vocal_steel",
              styleLabel: "Singing Steel",
              styleReason: "Uses singing support.",
              decisionModelVersion: "melody-decision-ranker-v1",
              decisionModelStatus: "seed",
              recommended: false,
              recommendation: "Learn the melody first.",
              textureSummary: { singleNotes: 1, dyads: 0, triads: 0, barSlides: 1 },
              transitions: [{
                id: "transition-1", kind: "bar_slide", scope: "full_grip",
                fromEventId: "melody-step-0", toEventId: "melody-step-1",
                controlsBefore: ["A", "B"], controlsAfter: [],
                fromStrings: [4, 5, 6], toStrings: [4, 5, 6], sustainedStrings: [4, 5, 6],
                repickedStrings: [], releasedStrings: [],
                voiceActions: [{string: 4, action: "bar_slide"}, {string: 5, action: "bar_slide"}, {string: 6, action: "bar_slide"}]
              }],
              pathSummary: { totalBarTravel: 0, harmonicFamilyChanges: 0 },
              events: [{ id: "melody-step-1", step: 1, resolvedNote: "G", resolvedPitch: "G4", texture: "single_note", arrangementRole: "arrival", performanceControls: ["A", "B"], patternFamily: "middle-pocket", canonicalGrip: "4-5-6", selectionReason: "Keeps the phrase in one pocket.", transitionFromPreviousId: "transition-1", notes: [{ string: 4, fret: 3, changes: [] }] }],
              tabExample: { id: "single-tab", title: "Single", rendered_tab: "S4 |--3--|", printTabText: "S4 |--3--|", validation: { ok: true } },
              fretboard: {
                type: "pedal-steel-fretboard",
                positions: [{ id: "melody-step-1", fret: 3, strings: [4] }],
                strings: { count: 10, labels: { "4": "E" } },
                copedent: { id: "saved:road-e9", label: "Road E9" },
                openPitchValues: { "4": 52 }
              }
            }]
          }
        })
      };
    }
  });

  const body = JSON.parse(capturedRequest.options.body);
  assert.equal(body.question, "Teach this solo");
  assert.equal(body.melodyRequest.kind, "artist_solo_lesson");
  assert.equal(result.melodyExercise.title, "Example Artist — Example Song");
  assert.equal(result.melodyExercise.sourceCopedentId, "source-e9-abc-defg-v1");
  assert.equal(result.melodyExercise.targetCopedentId, "saved:road-e9");
  assert.equal(result.melodyExercise.arrangedFor, "Road E9");
  assert.equal(result.melodyExercise.styleFamily, "vocal_steel");
  assert.equal(result.melodyExercise.styleLabel, "Singing Steel");
  assert.equal(result.melodyExercise.styleReason, "Uses singing support.");
  assert.deepEqual(result.melodyExercise.styleCatalog.map((item) => item.label), ["Best Fit", "Singing Steel"]);
  assert.equal(result.melodyExercise.decisionModelVersion, "melody-decision-ranker-v1");
  assert.equal(result.melodyExercise.decisionModelStatus, "seed");
  assert.equal(result.melodyExercise.decisionRules.modelVersion, "melody-decision-ranker-v1");
  assert.equal(result.melodyExercise.events[0].resolvedNote, "G");
  assert.equal(result.melodyExercise.events[0].notes[0].fret, 3);
  assert.equal(result.melodyExercise.events[0].resolvedPitch, "G4");
  assert.equal(result.melodyExercise.routes[0].harmonyType, "single_note");
  assert.equal(result.melodyExercise.routes[0].events[0].texture, "single_note");
  assert.equal(result.melodyExercise.routes[0].events[0].arrangementRole, "arrival");
  assert.deepEqual(result.melodyExercise.routes[0].events[0].performanceControls, ["A", "B"]);
  assert.equal(result.melodyExercise.routes[0].arrangedFor, "Road E9");
  assert.equal(result.melodyExercise.routes[0].targetCopedentId, "saved:road-e9");
  assert.equal(result.melodyExercise.routes[0].decisionModelVersion, "melody-decision-ranker-v1");
  assert.equal(result.melodyExercise.routes[0].decisionModelStatus, "seed");
  assert.equal(result.melodyExercise.routes[0].styleLabel, "Singing Steel");
  assert.equal(result.melodyExercise.routes[0].events[0].patternFamily, "middle-pocket");
  assert.equal(result.melodyExercise.routes[0].events[0].canonicalGrip, "4-5-6");
  assert.equal(result.melodyExercise.routes[0].events[0].selectionReason, "Keeps the phrase in one pocket.");
  assert.equal(result.melodyExercise.routes[0].events[0].transitionFromPreviousId, "transition-1");
  assert.equal(result.melodyExercise.routes[0].transitions[0].kind, "bar_slide");
  assert.equal(result.melodyExercise.routes[0].transitions[0].scope, "full_grip");
  assert.deepEqual(result.melodyExercise.routes[0].transitions[0].controlsBefore, ["A", "B"]);
  assert.deepEqual(result.melodyExercise.routes[0].transitions[0].sustainedStrings, [4, 5, 6]);
  assert.deepEqual(result.melodyExercise.routes[0].transitions[0].voiceActions.map((item) => item.string), [4, 5, 6]);
  assert.equal(result.melodyExercise.routes[0].textureSummary.barSlides, 1);
  assert.equal(result.melodyExercise.routes[0].pathSummary.harmonicFamilyChanges, 0);
  assert.equal(result.melodyExercise.routes[0].tab.tabText, "S4 |--3--|");
  assert.equal(result.melodyExercise.routes[0].tab.printTabText, "S4 |--3--|");
  assert.deepEqual(result.melodyExercise.events[0].performanceControlLabels, ["My E raise"]);
  assert.deepEqual(result.melodyExercise.events[0].mechanicalPitchesByString, { "4": 67 });
  assert.deepEqual(result.melodyExercise.events[0].notes[0].changeLabels, ["My E raise"]);
  assert.equal(result.melodyExercise.routes[0].fretboard.copedent.id, "saved:road-e9");
  assert.equal(result.melodyExercise.routes[0].fretboard.openPitchValues["4"], 52);
  assert.equal(result.melodyExercise.section.hasMore, true);
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


def test_frontend_answer_client_surfaces_safe_api_validation_error() -> None:
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const code = fs.readFileSync("ui/answer-client.js", "utf8");
const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const answerUi = vm.runInContext("STEEL_RAG_ANSWER_UI", sandbox);

(async () => {
  await assert.rejects(
    answerUi.requestAnswer("Arrange this song", {
      fetchImpl: async () => ({
        ok: false,
        status: 400,
        json: async () => ({ error: "This copedent action needs a unique control." })
      })
    }),
    /This copedent action needs a unique control\./
  );
})().catch((error) => { console.error(error); process.exit(1); });
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_answer_ui_keeps_melody_lesson_renderer_without_cross_feature_header_link() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    client = Path("ui/answer-client.js").read_text(encoding="utf-8")

    assert 'id="melody-studio-link"' not in html
    assert 'class="header-action-button melody-studio-header-link"' not in html
    assert 'id="melody-tool"' not in html
    assert 'id="melody-submit"' not in html
    assert 'id="answer-melody"' in html
    assert "function renderMelodyExercise(exercise)" in html
    assert "function clearMelodyExercise()" in html
    assert "renderMelodyExercise(response.melodyExercise);" in html
    assert "button.dataset.melodyEventId = event.id;" in html
    assert "answerTab.dataset.activeMelodyEvent = selectedEvent.id;" in html
    assert "answerFretboardMount.dataset.activeMelodyEvent = selectedEvent.id;" in html
    assert "answerFretboardMount.dataset.activeMelodyPosition = selectedEvent.renderablePositionId;" in html
    assert "selectPedalSteelFretboardPosition" in html
    assert "renderablePositionId: firstTextValue(event.renderablePositionId, event.positionId)" in client
    assert 'studioLink.textContent = "Open in Melody Studio";' in html


def test_answer_ui_uses_live_answer_client_not_mock_answer_data() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")

    assert '<script src="answer-client.js?v=plan-activity-20260714-1"></script>' in html
    assert '<script src="account-activity.js?v=plan-activity-20260714-1"></script>' in html
    assert '<script src="answer-client.js?v=e9-explorer-home-entry-20260623"></script>' not in html
    assert '<script src="pedal-steel-fretboard-styles.js?v=module-boundaries-20260713"></script>' in html
    assert '<script src="pedal-steel-fretboard.js?v=landing-bubble-labels-20260713"></script>' in html
    assert '<script src="pedal-steel-fretboard.js?v=e9-explorer-home-entry-20260623"></script>' not in html
    assert '<script src="mock-answer-data.js"></script>' not in html
    assert "STEEL_RAG_ANSWER_UI.requestAnswer" in html
    assert "STEEL_RAG_ANSWER_UI.requestSession" in html
    assert "No sources returned" in html
    assert 'id="answer-progression"' in html
    assert "renderProgressionGuide(response.progressionGuide)" in html
    assert "clearProgressionGuide()" in html


def test_answer_ui_uses_safari_safe_transparent_home_and_answer_logos() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    shell_css = Path("ui/workspace-shell.css").read_text(encoding="utf-8")

    assert 'class="home-sign hero-hanging-sign"' in html
    assert 'class="landing-sign" autoplay muted loop playsinline' in html
    assert 'poster="brand/steel-guitar-rag-hanging-sign-cloudflare-login.png?v=mobile-logo-safari-20260713-1"' in html
    assert 'src="brand/steel-guitar-rag-landing-alpha.webm?v=landing-alpha-return-20260713"' in html
    assert 'type="video/webm"' in html
    assert 'type="video/mp4"' not in html
    assert 'class="landing-sign-fallback" src="brand/steel-guitar-rag-hanging-sign-cloudflare-login.png?v=mobile-logo-safari-20260713-1"' in html
    assert ".app-shell-header .home-sign" in shell_css
    assert "position: absolute;" in shell_css
    assert "left: calc((100vw - 100%) / -2 - 12px);" in shell_css
    assert "width: clamp(330px, 24vw, 350px);" in shell_css
    assert "width: clamp(300px, 40vw, 340px);" in shell_css
    assert "width: min(290px, 86vw);" in shell_css
    assert "@media (max-width: 520px)" in shell_css
    assert "@media (hover: none) and (pointer: coarse)" in shell_css
    assert "pointer-events: auto;" in shell_css
    assert ".hero-hanging-sign.is-animated .landing-sign" in html
    assert ".hero-hanging-sign.is-animated .landing-sign-fallback" in html
    assert "@media (prefers-reduced-motion: reduce)" in shell_css
    assert ".app-shell-header .landing-sign-fallback" in shell_css
    assert "object-fit: contain;" in html
    assert "object-position: top left;" in html
    assert "image-rendering: auto;" in html
    assert 'prefers-reduced-motion: reduce' in html
    assert ".brand-home {\n      display: none;" in html
    assert ".page.is-answering .brand-home {\n      display: inline-flex;" in html
    assert ".page.is-answering .home-sign" in shell_css
    assert 'class="answer-brand-badge" src="brand/steel-guitar-rag-answer-badge-fallback-alpha.png?v=mobile-logo-safari-20260713-1"' in html
    assert '<video class="answer-brand-badge"' not in html
    assert "width: clamp(160px, 18vw, 240px);" in html
    assert "max-height: 86px;" in html
    assert Path("ui/brand/steel-guitar-rag-landing-alpha.webm").is_file()
    assert Path("ui/brand/steel-guitar-rag-landing-fallback-alpha.png").is_file()
    assert Path("ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png").is_file()
    assert Path("ui/brand/steel-guitar-rag-answer-badge-alpha.webm").is_file()
    assert Path("ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png").is_file()
    assert Path("public/brand/steel-guitar-rag-answer-badge-alpha.webm").is_file()
    assert Path("public/brand/steel-guitar-rag-answer-badge-fallback-alpha.png").is_file()


def test_answer_ui_header_only_exposes_home_ask_and_backstage() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    shell_css = Path("ui/workspace-shell.css").read_text(encoding="utf-8")

    assert 'class="header-action-button home-header-link"' in html
    assert 'aria-label="Return home"' in html
    assert 'class="header-action-button ask-header-link"' in html
    assert 'aria-label="Ask another steel guitar question"' in html
    assert 'class="header-action-button backstage-trigger"' in html
    assert ".app-shell-header .header-action-button" in shell_css
    assert "min-height: 46px;" in shell_css
    assert 'aria-controls="backstage"' in html
    assert 'id="backstage-cta-label">Go Backstage</span>' in html
    assert html.index('class="header-action-button home-header-link"') < html.index('class="header-action-button ask-header-link"')
    assert html.index('class="header-action-button ask-header-link"') < html.index('class="header-action-button backstage-trigger"')
    assert "explorer-header-link" not in html
    assert "melody-studio-header-link" not in html
    assert "lessons-header-link" not in html
    assert ">Go Backstage</a>" not in html
    assert "explorer-entry-card" not in html
    assert "not corpus retrieval or RAG-generated fretboard positions" not in html
    assert "[object Object]" not in html
    assert 'homeHeaderLink.addEventListener("click", () => returnToStage({ focusTarget: "home" }));' in html
    assert 'askHeaderLink.addEventListener("click", () => returnToStage({ focusTarget: "question" }));' in html
    assert 'document.querySelector(".home-sign")?.focus();' in html
    assert "question.focus();" in html


def test_backstage_more_action_pill_centers_summary_text() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    rule = html.split(".copedent-more summary {", 1)[1].split("}", 1)[0]

    assert '<summary class="backstage-button" aria-label="More copedent actions">More</summary>' in html
    assert "display: inline-flex;" in rule
    assert "align-items: center;" in rule
    assert "justify-content: center;" in rule
    assert "box-sizing: border-box;" in rule


def test_e9_fretboard_explorer_surface_uses_display_fields_and_validated_data() -> None:
    html = Path("ui/e9-fretboard-explorer.html").read_text(encoding="utf-8")
    config = Path("ui/e9-fretboard-explorer-config.js").read_text(encoding="utf-8")
    script = config + "\n" + Path("ui/e9-fretboard-explorer.js").read_text(encoding="utf-8")
    loader = Path("ui/e9-fretboard-explorer-loader.js").read_text(encoding="utf-8")
    rules = Path("ui/e9-music-rules.js").read_text(encoding="utf-8")
    data = Path("ui/e9-fretboard-explorer-data.js").read_text(encoding="utf-8")
    payloads = json.loads(data.split("window.STEEL_RAG_E9_EXPLORER_PAYLOADS = ", 1)[1].split(";\nwindow.", 1)[0])
    payload = payloads["G"]

    assert "E9 Fretboard Explorer" in html
    assert "Validated Explorer data" in html
    assert "checked against tuning and pedal/lever changes" in html
    assert "These Explorer rows are deterministic teaching data, separate from source-card answers." not in html
    assert "not corpus retrieval or RAG-generated fretboard positions" not in html
    assert '<script src="pedal-steel-fretboard-styles.js?v=module-boundaries-20260713"></script>' in html
    assert '<script src="pedal-steel-fretboard.js?v=module-boundaries-20260713"></script>' in html
    assert "pedal-steel-fretboard.js?v=e9-explorer-explanation-ui-20260623" not in html
    assert "pedal-steel-fretboard.js?v=explorer-ui-cleanup-20260623" not in html
    assert "pedal-steel-fretboard.js?v=selected-svg-render-20260623" not in html
    assert "pedal-steel-fretboard.js?v=explorer-compact-copedent-20260625" not in html
    assert '<script src="e9-fretboard-explorer-data.js?v=single-grip-octave-results-20260628"></script>' not in html
    assert "[hidden] {\n      display: none !important;\n    }" in html
    assert '<script src="e9-music-rules.js?v=voicing-readability-20260704"></script>' in html
    assert '<script src="e9-fretboard-explorer-loader.js?v=account-copedents-20260714-2"></script>' in html
    assert "e9-fretboard-explorer.js?v=table-first-copedent-20260714-2" in loader
    assert 'typeof STEEL_RAG_ANSWER_UI !== "undefined"' in loader
    assert "const session = await answerUi?.requestSession?.({ accessRole });" in loader
    assert "window.STEEL_RAG_ANSWER_UI?.requestSession" not in loader
    assert "e9-fretboard-explorer-data.js" not in loader
    assert 'dataset.explorerDataMode = "unavailable"' in loader
    assert html.index("e9-music-rules.js?v=voicing-readability-20260704") < html.index("e9-fretboard-explorer-loader.js?v=account-copedents-20260714-2")
    assert "e9-fretboard-explorer.js?v=voicing-identifier-hardening-20260704" not in html
    assert "e9-fretboard-explorer.js?v=explorer-workbench-redesign-20260628" not in html
    assert "e9-fretboard-explorer.js?v=e-lower-pocket-d-major-20260628" not in html
    assert "e9-fretboard-explorer.js?v=compact-explorer-tools-20260628" not in html
    assert "e9-fretboard-explorer.js?v=voicing-identifier-copy-20260627" not in html
    assert "e9-fretboard-explorer.js?v=chord-map-label-cleanup-20260627" not in html
    assert "e9-fretboard-explorer.js?v=explorer-octave-register-20260627" not in html
    assert "e9-fretboard-explorer.js?v=path-card-colors-20260627" not in html
    assert "e9-fretboard-explorer.js?v=impact-control-groups-20260627" not in html
    assert "e9-fretboard-explorer.js?v=compact-fretboard-tools-20260627" not in html
    assert "e9-fretboard-explorer.js?v=grip-vocabulary-20260627" not in html
    assert "e9-fretboard-explorer.js?v=post-fretboard-impact-20260628" not in html
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
    assert '<option value="emmons-e9-basic" selected>Emmons E9 starter</option>' in html
    assert '<option value="day-e9-basic">Day E9 starter</option>' in html
    assert '<option value="custom-e9-lkv">' not in html
    assert '<option value="my-copedent-e9"' not in html
    assert '<div class="explorer-copedent-control-row">' not in html
    task_home_markup = html.split('<section class="explorer-task-home" aria-label="Explorer task shortcuts">', 1)[1].split('<section class="explorer-mode-panel explorer-mode-panel--state-only" aria-label="Explorer mode">', 1)[0]
    mode_markup = html.split('<section class="explorer-mode-panel explorer-mode-panel--state-only" aria-label="Explorer mode">', 1)[1].split("</section>", 1)[0]
    context_markup = html.split('<section class="explorer-context-strip" id="explorer-context-strip" aria-label="Selected Explorer task">', 1)[1].split("</section>", 1)[0]
    controls_markup = html.split('<section class="explorer-controls" aria-label="Explorer filters">', 1)[1].split("</section>", 1)[0]
    workbench_markup = html.split('<section class="explorer-workbench" aria-label="Explorer workbench">', 1)[1].split('<section class="explorer-details"', 1)[0]
    panel_markup = html.split('<section class="explorer-panel" aria-label="Explorer fretboard">', 1)[1].split('<aside class="explorer-inspector"', 1)[0]
    inspector_markup = html.split('<aside class="explorer-inspector" aria-label="Why this works">', 1)[1].split("</aside>", 1)[0]
    details_markup = html.split('<section class="explorer-details" aria-label="Explorer position details"', 1)[1].split("</section>", 1)[0]
    assert html.index('<section class="explorer-task-home" aria-label="Explorer task shortcuts">') < html.index('<section class="explorer-mode-panel explorer-mode-panel--state-only" aria-label="Explorer mode">')
    assert html.index('<section class="explorer-mode-panel explorer-mode-panel--state-only" aria-label="Explorer mode">') < html.index('<section class="explorer-context-strip" id="explorer-context-strip" aria-label="Selected Explorer task">')
    assert html.index('<section class="explorer-context-strip" id="explorer-context-strip" aria-label="Selected Explorer task">') < html.index('<section class="explorer-controls" aria-label="Explorer filters">')
    assert "Choose what you want to learn" in task_home_markup
    assert "These start the existing Explorer modes; the full controls stay available below." in task_home_markup
    for task_id, mode_id, label, action in [
        ("find-chord", "chord", "Find chords and voicings", "Open chord finder"),
        ("find-note", "note", "Find a note", "Open note finder"),
        ("explore-grip", "single", "Explore a grip", "Open single grip"),
        ("walk-harmonized-scale", "path", "Walk a harmonized scale", "Open scale path"),
        ("study-movement-path", "path", "Study a movement path", "Open path view"),
        ("identify-voicing", "voicing", "Identify a voicing", "Open identifier"),
    ]:
        assert f'data-explorer-task-card="{task_id}"' in task_home_markup
        assert f'data-explorer-task-mode="{mode_id}"' in task_home_markup
        assert f"<strong>{label}</strong>" in task_home_markup
        assert f'<span class="explorer-task-card__action">{action}</span>' in task_home_markup
    assert 'data-explorer-task-card="explore-grip" data-explorer-task-mode="single" aria-pressed="true"' in task_home_markup
    assert "Example: no-pedals to A+B" in task_home_markup
    assert ".explorer-task-home__grid" in html
    assert "grid-template-columns: repeat(6, minmax(132px, 1fr));" in html
    assert "min-height: 96px;" in html.split(".explorer-task-card {", 1)[1].split("}", 1)[0]
    assert "scroll-snap-type: x proximity;" in html
    assert "Current task" in context_markup
    assert "Explore a grip" in context_markup
    assert "Key: G" in context_markup
    assert ".explorer-context-strip {" in html
    assert "function updateContextStrip(rows)" in script
    assert "TASK_CARD_META" in script
    assert 'id="explorer-copedent-open"' not in controls_markup
    assert '<dialog class="explorer-copedent-dialog" id="explorer-copedent-dialog"' in html
    assert '<button class="explorer-inline-button" id="explorer-copedent-close" type="button">Close</button>' in html
    assert "This is the global active profile. Manage common and custom setups in Backstage." in html
    assert "Choose the E9 setup that matches your guitar" not in html
    assert "My Copedent (E9) is coming soon in Backstage" not in html
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
    assert 'class="explorer-control explorer-control--mode explorer-mode-select-proxy"' in mode_markup
    assert '<div class="explorer-mode-tabs" role="tablist" aria-label="Explorer mode">' not in html
    assert "explorer-mode-tab" not in html
    assert "data-explorer-mode-tab" not in html
    for label in ["Single Grip", "Harmonized Scale Path", "Single-Note Finder"]:
        assert f"<strong>{label}</strong>" not in html
    assert '<option value="single" selected>Single grip</option>' in html
    assert '<option value="path">Harmonized scale path</option>' in html
    assert '<option value="note">Single-note finder</option>' in html
    assert '<option value="voicing">Voicing identifier</option>' in html
    assert '<option value="chord">Chord / Voicing Finder</option>' in html
    assert "Single grip filters exact strings" in html
    assert "Voicing identifier explains one shape." in html
    assert "Chord / Voicing Finder searches practical shapes for a target chord." in html
    assert "function applyExplorerQueryState()" in script
    assert "queryModeValue(params.get(\"mode\"))" in script
    assert "safeSelectValue(els.stringGroup, grip)" in script
    assert "if (CHORD_FINDER_ROOT_OPTIONS.includes(root))" in script
    assert "selectedChordQuality = quality;" in script
    assert "data-explorer-task-card" in script
    assert "function applyTaskCard(taskId)" in script
    assert "study-movement-path" in script
    assert "voicing-readability-20260704" in html
    assert "explorer-mode-home-dedupe-20260704" not in html
    assert "explorer-handoff-20260701" not in html
    assert ".explorer-mode-panel {" in html
    assert "grid-template-columns: 1fr;" in html.split(".explorer-mode-panel {", 1)[1].split("}", 1)[0]
    assert "grid-template-columns: minmax(220px, 340px) minmax(0, 1fr);" not in html
    assert ".explorer-mode-panel--state-only {" in html
    assert "display: none;" in html.split(".explorer-mode-panel--state-only {", 1)[1].split("}", 1)[0]
    assert ".explorer-mode-tabs {" not in html
    assert ".explorer-mode-select-proxy {" in html
    assert "Start by choosing the kind of fretboard question you want to explore" not in mode_markup
    assert '<section class="explorer-details" aria-label="Explorer position details" hidden aria-hidden="true">' in html
    assert 'id="explorer-row-list"' in details_markup
    assert "display: none;" in html.split(".explorer-details {", 1)[1].split("}", 1)[0]
    assert "display: none;" in html.split(".explorer-row-list {", 1)[1].split("}", 1)[0]
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
    assert "<span>Home</span>" in html
    assert "<span>Go Backstage</span>" in html
    assert html.count('<svg viewBox="0 0 24 24" aria-hidden="true">') >= 4
    assert '<span>Ask</span>' not in html
    assert '<a class="explorer-back" href="/ui/melody-workbench.html"><span>Arrange</span></a>' not in html
    assert '<a class="explorer-back" href="/ui/lesson-workbench.html"><span>Learn</span></a>' not in html
    assert ".explorer-back {" in html
    explorer_back_rule = html.split(".explorer-back {", 1)[1].split("}", 1)[0]
    for expected_style in [
        "display: inline-flex;",
        "align-items: center;",
        "gap: 9px;",
        "min-height: 44px;",
        "padding: 0 16px;",
        "border-radius: 999px;",
        "border: 1px solid rgba(240, 191, 105, 0.34);",
        "background: rgba(13, 14, 14, 0.68);",
        "color: rgba(244, 234, 214, 0.88);",
        "cursor: pointer;",
        'font-family: "Gill Sans", "Gill Sans MT", "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif;',
        "font-size: 14px;",
        "font-weight: 600;",
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
    explorer_hover_rule = html.split('.explorer-back:hover,\n    .explorer-back:focus-visible,\n    .explorer-back[aria-current="page"] {', 1)[1].split("}", 1)[0]
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
    assert ".explorer-control select {\n      height: 36px;" in html
    assert "min-height: 36px;" in html
    assert '<label for="explorer-grip-vocabulary">Grip vocabulary</label>' in html
    assert '<option value="core" selected>Core</option>' in html
    assert '<option value="extended">Extended</option>' in html
    assert '<option value="song_tab">Song/tab vocabulary</option>' in html
    assert '<option value="e_lower_pockets">E-lower pockets</option>' in html
    assert '<option value="two_string">Two-string</option>' in html
    assert '<option value="all">All legitimate</option>' in html
    assert "Core keeps the default view clean. Extended, song/tab, E-lower pockets, and two-string vocabulary are opt-in." in html
    assert ".explorer-controls-note {" not in html
    assert "explorer-controls-note" not in html
    assert "explorer-grip-help-disclosure" not in html
    assert "<summary>About grip vocabulary</summary>" not in html
    assert "Core grips are common string sets. Extended, song/tab, E-lower pocket, and two-string vocabulary are opt-in" not in controls_markup
    assert "5-7-8 is the first-class E-lower pocket" not in controls_markup
    assert "5-8 appears in 2-string branch routes" not in controls_markup
    assert "5-7-8 is the required pocket case" in html
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
    assert '<optgroup label="Path grips">' in html
    assert '<optgroup label="Extended grips">' in html
    assert '<optgroup label="Song/tab vocabulary grips">' in html
    assert '<optgroup label="E-lower pocket grips">' in html
    assert '<option value="3-5-9">3-5-9</option>' in html
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
    assert "<dt>Path grip</dt><dd>A string set used to keep harmonized movement connected" in html
    assert "<dt>Extended grip</dt><dd>A real-world tab or voicing-discovery grip" in html
    assert "<dt>Song/tab vocabulary grip</dt><dd>A context-dependent grip seen in real playing vocabulary" in html
    assert "<dt>E-lower pocket</dt><dd>A grip whose practical value depends on the E-lower lever" in html
    assert "<dt>Two-string grip / dyad</dt><dd>A two-note grip." in html
    assert "<dt>Pad / sustain</dt><dd>A held support sound" in html
    assert "<dt>Partial voicing</dt><dd>A useful part of a chord" in html
    assert 'id="explorer-tooltip"' in html
    assert 'id="explorer-active-results"' in html
    assert 'id="explorer-copedent-chart"' in html
    assert 'id="explorer-control-impact-preview"' in html
    assert 'id="explorer-scale-notes"' not in html
    assert "explorer-scale-summary" not in html
    assert "Scale: <span" not in html
    assert 'id="explorer-selected-detail"' in html
    assert '<section class="explorer-workbench" aria-label="Explorer workbench">' in html
    assert '<aside class="explorer-inspector" aria-label="Why this works">' in html
    assert '<strong>Why this works</strong>' in inspector_markup
    assert '<span>Selected position</span>' in inspector_markup
    assert 'id="explorer-selected-detail"' in inspector_markup
    assert ".explorer-workbench {" in html
    assert "grid-template-columns: minmax(0, 1fr) minmax(280px, 0.28fr);" in html
    assert ".explorer-inspector {" in html
    assert "position: sticky;" in html.split(".explorer-inspector {", 1)[1].split("}", 1)[0]
    assert ".explorer-stage-header {" in html
    assert "<h2>E9 Fretboard</h2>" in panel_markup
    assert '<span class="explorer-stage-trust">Validated data</span>' in panel_markup
    assert html.count('id="explorer-notation-control"') == 1
    assert html.count('id="explorer-notation-label"') == 1
    assert html.count('id="explorer-notation-help"') == 1
    assert "data-explorer-notation-mode" not in controls_markup
    assert '<div class="explorer-fretboard-tools" aria-label="Fretboard display controls">' in panel_markup
    assert '<div class="explorer-control explorer-control--notation explorer-panel-notation" id="explorer-notation-control">' in panel_markup
    assert '<span class="explorer-control-label" id="explorer-string-action-label-label">Labels</span>' not in panel_markup
    assert 'aria-label="String labels"' in panel_markup
    assert 'class="explorer-string-label-toggle__track"' in panel_markup
    assert 'class="explorer-string-label-toggle__knob"' in panel_markup
    assert panel_markup.index('id="explorer-notation-control"') < panel_markup.index('id="explorer-active-results"')
    assert panel_markup.index('id="explorer-pitch-register-control"') < panel_markup.index('id="explorer-active-results"')
    assert panel_markup.index('id="explorer-string-action-label-control"') < panel_markup.index('id="explorer-active-results"')
    assert panel_markup.index('id="explorer-notation-control"') < panel_markup.index('id="explorer-fretboard"')
    assert panel_markup.index('id="explorer-pitch-register-control"') < panel_markup.index('id="explorer-fretboard"')
    assert panel_markup.index('id="explorer-string-action-label-control"') < panel_markup.index('id="explorer-fretboard"')
    assert panel_markup.index('id="explorer-fretboard"') < panel_markup.index('id="explorer-control-impact-preview"')
    assert panel_markup.index('id="explorer-control-impact-preview"') < panel_markup.index('id="explorer-active-results"')
    assert panel_markup.index('id="explorer-fretboard"') < panel_markup.index('id="explorer-active-results"')
    assert workbench_markup.index('id="explorer-fretboard"') < workbench_markup.index('id="explorer-selected-detail"')
    assert html.index('id="explorer-fretboard"') < html.index('id="explorer-control-impact-preview"')
    assert "Marker detail" not in panel_markup
    assert ".explorer-panel-notation {" in html
    assert ".explorer-fretboard-tools {" in html
    assert "display: flex;" in html.split(".explorer-fretboard-tools {", 1)[1].split("}", 1)[0]
    assert "flex-wrap: wrap;" in html.split(".explorer-fretboard-tools {", 1)[1].split("}", 1)[0]
    assert "grid-template-columns: minmax(240px, 1.25fr) minmax(260px, 1.35fr) minmax(150px, auto);" not in html
    active_result_track_rule = html.split(".explorer-active-results__track {", 1)[1].split("}", 1)[0]
    for expected_style in [
        "display: flex;",
        "overflow-x: auto;",
        "scroll-snap-type: x proximity;",
        "-webkit-overflow-scrolling: touch;",
    ]:
        assert expected_style in active_result_track_rule
    active_result_rule = html.split(".explorer-active-result {", 1)[1].split("}", 1)[0]
    assert "flex: 0 0 clamp(136px, 13vw, 168px);" in active_result_rule
    assert "scroll-snap-align: start;" in active_result_rule
    path_step_rule = html.split(".explorer-path-step {", 1)[1].split("}", 1)[0]
    assert "--explorer-marker-color: #f7bd58;" in path_step_rule
    assert "color-mix(in srgb, var(--explorer-marker-color)" in path_step_rule
    assert '.explorer-path-step[data-marker-tone="1"]' in html
    assert '.explorer-path-step[data-marker-tone="8"]' in html
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
    assert 'e9-fretboard-explorer-loader.js?v=account-copedents-20260714-2' in html
    assert ".explorer-chord-map-card .explorer-active-result__fields {" in html
    assert ".explorer-chord-map-card .explorer-active-result__fields span {" in html
    assert "grid-template-columns: minmax(72px, 0.48fr) minmax(0, 1fr);" in html
    assert "overflow-wrap: anywhere;" in html
    assert "payloadsByCopedent" in script
    assert "renderCopedentChart" in script
    assert "openCopedentDialog" in script
    assert "closeCopedentDialog" in script
    assert "data-explorer-notation-mode" in script
    assert "data-explorer-pitch-register" in script
    assert "updateExploreModeTabs" in script
    assert 'notationMode = "notes"' in script
    assert 'pitchRegisterMode = "off"' in script
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
    assert "showHighlightLabels: options.showHighlightLabels !== false" in script
    assert "renderFretboard(rowsForMap, { showHighlightLabels: false })" in script
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
    assert "explorer-octave-register-20260627" not in html
    assert "notes_with_register" in script
    assert "note_registers" in script
    assert "Open note with register" in script
    assert "Final note with register" in script
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
    assert [row["chord_name"] for row in g_major_456[:8]] == ["G", "A", "B", "C", "D", "E", "F#", "G"]
    assert [row["fret"] for row in g_major_456[:8]] == [3, 3, 5, 8, 10, 10, 13, 15]
    assert [row["chord_name"] for row in g_major_456[8:]] == ["A", "B", "C", "D", "E"]
    assert [row["fret"] for row in g_major_456[8:]] == [15, 17, 20, 22, 22]
    g_major_345_top_g = [
        row for row in g_major_three
        if row["string_group"] == "3-4-5"
        and row["display_top_voice"]["note"] == "G"
        and row["pedals"] == ["B", "C"]
        and row["levers"] == []
    ]
    assert [row["fret"] for row in g_major_345_top_g] == [10, 22]
    g_minor_456 = [row for row in g_minor_three if row["string_group"] == "4-5-6"]
    assert [row["chord_name"] for row in g_minor_456[:8]] == ["G", "A", "Bb", "C", "D", "Eb", "F", "G"]
    assert [row["fret"] for row in g_minor_456[:8]] == [1, 4, 6, 6, 8, 11, 13, 13]
    assert [row["chord_name"] for row in g_minor_456[8:]] == ["A", "Bb", "C", "D", "Eb"]
    assert [row["fret"] for row in g_minor_456[8:]] == [16, 18, 18, 20, 23]
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
    assert 'id="explorer-pitch-register-control"' in html
    assert 'data-explorer-pitch-register="off"' in html
    assert 'data-explorer-pitch-register="scientific"' in html
    assert 'data-explorer-pitch-register="band"' in html
    assert "<dt>Scientific octave notation</dt>" in html
    assert "<dt>Pitch register</dt>" in html
    assert "<dt>Octave band</dt>" in html
    assert "<dt>Peterson octave labels</dt>" in html
    assert all("notes_with_register" in row for row in payload["positions"])
    assert all("note_registers" in row for row in payload["positions"])
    assert any(register["scientific_pitch"].endswith("4") for row in payload["positions"] for register in row["notes_with_register"])
    assert payloads["C"]["query"]["display_scale_notes"]["natural_minor"] == ["C", "D", "Eb", "F", "G", "Ab", "Bb"]
    assert payloads["Db"]["query"]["display_scale_notes"]["major"] == ["Db", "Eb", "F", "Gb", "Ab", "Bb", "C"]
    assert payloads["Bb"]["query"]["display_scale_notes"]["major"] == ["Bb", "C", "D", "Eb", "F", "G", "A"]
    assert payloads["Eb"]["query"]["display_scale_notes"]["major"] == ["Eb", "F", "G", "Ab", "Bb", "C", "D"]
    assert any(row["string_group"] == "5-7-8" and row["harmony_type"] == "advanced_pocket" for row in payload["positions"])
    assert any(row.get("warnings") for row in payload["positions"])
    assert all(row["pitch_validated"] is True for row in payload["positions"])
    assert not re.search(r"\\b\\d+\\s+(?:I|ii|iii|iv|v|vi|vii)\\b", script)


def test_explorer_static_manifest_is_complete_hashed_and_bounded() -> None:
    manifest = json.loads(Path("ui/explorer-data-v1/manifest.json").read_text(encoding="utf-8"))
    records = [
        record
        for copedent in manifest["copedents"].values()
        for record in copedent["chunks"].values()
    ]

    assert manifest["schemaVersion"] == "explorer_static_manifest_v1"
    assert manifest["defaultCopedentId"] == "emmons-e9-basic"
    assert manifest["defaultKey"] == "G"
    assert len(records) == 51
    assert sum(record["compressedBytes"] for record in records) < 2 * 1024 * 1024
    assert max(record["compressedBytes"] for record in records) < 64 * 1024

    default_record = manifest["copedents"]["emmons-e9-basic"]["chunks"]["G"]
    chunk_path = Path("ui") / Path(default_record["path"]).relative_to("/ui")
    raw = gzip.decompress(chunk_path.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == default_record["sha256"]
    assert json.loads(raw)["query"]["key"] == "G"


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
assert.equal(rules.resolveE9Note({ stringNumber: 4, fret: 0, scaleNotes: gMajor }).finalScientificPitch, "E4");
assert.equal(rules.resolveE9Note({ stringNumber: 8, fret: 0, scaleNotes: gMajor }).finalScientificPitch, "E3");
assert.equal(rules.resolveE9Note({ stringNumber: 5, fret: 3, scaleNotes: gMajor }).finalScientificPitch, "D4");
assert.equal(rules.resolveE9Note({ stringNumber: 5, fret: 3, controls: ["A"], scaleNotes: gMajor }).finalScientificPitch, "E4");
assert.equal(rules.resolveE9Note({ stringNumber: 3, fret: 3, scaleNotes: gMajor }).finalScientificPitch, "B4");
assert.equal(rules.resolveE9Note({ stringNumber: 3, fret: 3, controls: ["B"], scaleNotes: gMajor }).finalScientificPitch, "C5");
assert.equal(rules.resolveE9Note({ stringNumber: 5, fret: 3, scaleNotes: gMajor }).finalOctaveBand, "middle");

const cOverFNotes = [4, 6, 10].map((stringNumber) => resolve(stringNumber, 3, ["A", "B"], fMajor));
assert.deepEqual(cOverFNotes, ["G", "C", "E"]);
const cOverF = rules.identifyVoicing(cOverFNotes, fContext);
assert.equal(cOverF.label, "C");
assert.equal(cOverF.functionText, "V function in F");
assert.equal(cOverF.voicing_status, "full");
assert.deepEqual(cOverF.present_tones, ["root (C)", "3rd (E)", "5th (G)"]);
assert.deepEqual(cOverF.omitted_tones, []);

const gNoThirdColor = rules.identifyVoicing(["D", "A", "G"], gContext);
assert.equal(gNoThirdColor.label, "G5/add9(no3)");
assert.equal(gNoThirdColor.quality, "no-3rd color");
assert.equal(gNoThirdColor.voicing_status, "color");
assert.equal(gNoThirdColor.confidence, "medium");
assert.deepEqual(gNoThirdColor.present_tones, ["root (G)", "9th (A)", "5th (D)"]);
assert.deepEqual(gNoThirdColor.omitted_tones, ["3rd (B)"]);
assert.match(gNoThirdColor.explanation, /no-3rd color voicing/);
assert.match(gNoThirdColor.warnings.join(" "), /does not define major vs minor/);
assert.doesNotMatch(gNoThirdColor.label, /^G$/);

const fMajNo3 = rules.identifyVoicing(["E", "C", "F"], gContext);
assert.equal(fMajNo3.label, "Fmaj7(no3)");
assert.equal(fMajNo3.quality, "partial major 7");
assert.equal(fMajNo3.confidence, "medium");
assert.equal(fMajNo3.voicing_status, "partial");
assert.match(fMajNo3.omitted_tones.join(" "), /3rd/);
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
assert.equal(rules.gripTierLabel("5-6-7"), "Path grip");
assert.equal(rules.gripTierLabel("3-5-9"), "Song/tab vocabulary grip");
assert.equal(rules.gripTierLabel("5-7-8"), "E-lower pocket");
assert.equal(rules.gripMetadata("5-7-8").tier, "e_lower_pocket");
assert.match(rules.gripMetadata("5-7-8").explanation, /E-lower pocket grip/);
assert.match(rules.gripMetadata("3-5-9").watchOut, /9th-string color is context-dependent/);
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

const progression = answerUi.normalizeAnswerResponse({
  question: "Show me a C F G C progression on E9.",
  answer: "Here is a practical C I-IV-V-I route on E9.",
  progression_guide: {
    type: "e9-progression-guide-v0",
    key: "C",
    progression: "I-IV-V-I",
    chords: ["C", "F", "G", "C"],
    recommendedRouteId: "c-home",
    routes: [
      {
        id: "c-home",
        family: "home_pocket",
        label: "C home route",
        difficulty: "starter",
        summary: "Stay near fret 8.",
        events: [
          {
            id: "c-home-event-1",
            renderablePositionId: "c-home-1",
            function: "I",
            chordName: "C",
            root: "C",
            quality: "major",
            fret: 8,
            strings: [5, 6, 8],
            grip: "5-6-8",
            pedals: [],
            levers: [],
            changes: [],
            notes: { 5: "G", 6: "C", 8: "E" },
            intervals: { 5: "5", 6: "1", 8: "3" },
            contains: ["1", "3", "5"],
            omits: [],
            voicingType: "root_position",
            isFullChord: true,
            isPartial: false,
            routeReason: "Straight-bar home position.",
            nextMove: "Press A+B.",
            difficulty: "starter",
            routeFamily: "home_pocket",
            validationStatus: "pitch_validated"
          }
        ]
      }
    ]
  },
  fretboard: {
    title: "C progression route",
    description: "Validated E9 route.",
    positions: [{ id: "c-home-1", label: "C", fret: 8, strings: [5, 6, 8], grip: "5-6-8" }],
    highlights: []
  },
  sources: []
});
assert.equal(progression.progressionGuide.key, "C");
assert.equal(progression.progressionGuide.recommendedRoute.id, "c-home");
assert.equal(progression.progressionGuide.recommendedRoute.events[0].notes[0], "5: G");
assert.equal(progression.progressionGuide.recommendedRoute.events[0].intervals[1], "6: 1");
assert.equal(JSON.stringify(progression.progressionGuide).includes("[object Object]"), false);

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
    removeAttribute(name) {
      delete this.attributes[name];
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
    assert "function submitQuestion(questionText, requestPayload = {})" in html
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
        if (selector === ".home-overview") return [makeElement()];
        if (selector === ".backstage-trigger") return [getElement(".backstage-trigger"), makeElement()];
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
    kind: "parameterized_chord_movement",
    context: { tuning: "E9", profile: "default_e9", difficulty: "beginner" },
    rendered_tab: tabText,
    validation: { ok: true, issues: [], profile: "default_e9", eventCount: 2 },
    explanation: "A compact validated G grip.",
    intervals: [{ role: "root", note: "G" }],
    events: [
      {
        id: "g-major-456-open-event-1",
        label: "I",
        function: "I",
        chord: "G",
        lyric: "pick",
        notes: [
          { string: 4, fret: 3, changes: [] },
          { string: 5, fret: 3, changes: [] },
          { string: 6, fret: 3, changes: [] }
        ]
      }
    ]
  }
});

assert.equal(tabExample.tabs.length, 1);
assert.equal(tabExample.tabs[0].id, "g-major-456-open");
assert.equal(tabExample.tabs[0].title, "G major 4-5-6 grip");
assert.equal(tabExample.tabs[0].tabText, tabText);
assert.equal(tabExample.tabs[0].kind, "parameterized_chord_movement");
assert.equal(tabExample.tabs[0].contextData.tuning, "E9");
assert.equal(tabExample.tabs[0].metadata.difficulty, "beginner");
assert.equal(tabExample.tabs[0].metadata.event_count, 2);
assert.equal(tabExample.tabs[0].why, "A compact validated G grip.");
assert.equal(tabExample.tabs[0].events.length, 1);
assert.equal(tabExample.tabs[0].events[0].chord, "G");
assert.equal(tabExample.tabs[0].events[0].notes[1].string, 5);
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
    assert ".movement-lesson-card" in html
    assert "function renderMovementLessonCard(tab)" in html
    assert "card.dataset.movementLessonCard" in html
    assert "Movement lesson" in html
    assert "Why this move works" in html
    assert "Tab ↔ fretboard" in html
    assert "Practice it slowly" in html
    assert "function movementExplorerUrl(tab)" in html
    assert 'link.dataset.explorerHandoff = "movement";' in html
    assert 'link.textContent = "Explore related path";' in html
    assert "/ui/e9-fretboard-explorer.html" in html
    assert "function shouldRenderMovementLesson(tab)" in html
    assert "tab.events.length" in html
    assert "tab.contextData?.progression" in html
    assert "font-family: ui-monospace" in html
    assert "white-space: pre;" in html
    assert "overflow-x: auto;" in html
    assert "function renderTabExamples(tabs)" in html
    assert "function renderTabCard(tab)" in html
    assert "function clearTabExamples()" in html
    assert "renderTabExamples(response.tabs);" in html
    assert "clearTabExamples();" in html
    assert "hideEmptySourceCards" in html
    assert "Boolean(response.progressionGuide)" in html
    assert "Boolean(response.fretboard)" in html
    assert "Boolean(response.melodyExercise)" in html
    assert "response.tabs?.some((tab) => shouldRenderMovementLesson(tab))" in html


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
