# Integration Status - Browser-Ready 05e8748 Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## 1. Current Overall Project State

- Current repository HEAD: `449cdee docs: record 05e8748 browser-ready verification`.
- Verified protected-preview runtime HEAD: `05e8748 backend: replace quarantine fallback with teacher routes`.
- Current app readiness: browser-ready for user smoke/use.
- Exact user smoke URL: `https://app.steelguitarrag.com/`.
- Root behavior: protected-preview root redirects to `/ui/steel-guitar-rag-mock.html` and was verified in an authenticated Cloudflare Access browser session.
- Q&A unlock: passed after session initialization.
- Do not reopen completed `05e8748` smoke work unless new evidence shows a real user-facing blocker.
- Do not restart broad QA today unless a new real blocker is found.

## 2. Recent Tasks Completed By Active Lane

### Lane 01 Repo Steward

- Committed browser-ready verification docs:
  - `449cdee docs: record 05e8748 browser-ready verification`
  - committed `minimal-browser-verification-05e8748.md`
  - committed `2026-06-14-1700-15-runtime-05e8748-automated-qa.md`
  - committed `root-user-smoke-verification-after-resolver-fix-05e8748.md`
- Refreshed final readiness docs:
  - `docs/handoffs/task-completions/integration-status.md`
  - `docs/handoffs/task-completions/final-readiness-refresh-05e8748.md`
- Cleaned trailing whitespace in `docs/answer-eval-report.md` so `git diff --check` passes, but did not commit it because the file also contains a large parked generated-report rewrite.

### Lane 05 Backend / RAG Integration

- `05e8748 backend: replace quarantine fallback with teacher routes`
  - replaced remaining quarantine/backstop leakage paths with teacher routes;
  - fixed deterministic resolver issues for off-domain math bait, A-minor/B-flat parsing, string/fret/pedal diagnostics, Cmaj7/C7 where-to-play prompts, frustration prompts, repair prompts, and SGF quarantine regressions.
- Prior supporting backend fixes remain committed:
  - `24fd8e9 backend: fix repair fallback and chord classifier drift`
  - `1f91ed2 backend: block sgf primary answer leakage`
  - `c8b0d3b backend: quarantine sgf text from answer body`
  - `fd89e2d backend: fix remaining broad qa p1 blockers`
  - `a9eaa82 backend: fix broad qa chord and guardrail blockers`
  - `2cdea8a backend: normalize natural chord intent prompts`
  - `36ab10e backend: route chord qualities to fretboard answers`
  - `658c069 backend: answer practical chord questions directly`

### Lane 06 UX/UI Design

- `6a5f978 ui: improve answer page spacing`
- `28ae8f4 Fix answer card desktop section width`
- Recent user-smoke UI/layout work is not the blocker now; app root/browser readiness is verified for runtime `05e8748`.
- Known static/UI full-suite caveats remain backlog unless reclassified:
  - landing source vs deployed static HTML mismatch;
  - missing public fretboard background route in same-origin static smoke.

### Lane 12 Self-Hosted Deployment

- Root protected-preview verification after `05e8748`: passed.
- Verified:
  - runtime `/api/version` reported `05e8748`;
  - root URL loaded through Cloudflare Access and redirected to `/ui/steel-guitar-rag-mock.html`;
  - Q&A unlocked in the authenticated browser session;
  - fallback `/ui/steel-guitar-rag-mock.html` worked;
  - authenticated browser smoke passed.

### Lane 15 QA / Answer Eval

- Runtime `05e8748` automated QA:
  - focused automated API fallback smoke: `36` prompts, `36` true pass / `0` true blockers;
  - strict scorer SGF leakage gates: `0` hits across SGF primary leakage, forum-fragment leakage, weak-source primary wording, off-domain source cards, lesson/scale/lick hard gates, and deterministic teacher answer source fragments;
  - focused pytest set: `376 passed`.
- Minimal authenticated browser verification:
  - six requested prompts passed;
  - off-domain source cards absent;
  - fretboard rendered where expected;
  - Q&A unlocked after Cloudflare Access session initialization.

## 3. Files Changed Across Recent Tasks

Committed in `449cdee`:

- `docs/handoffs/task-completions/minimal-browser-verification-05e8748.md`
- `docs/handoffs/task-completions/2026-06-14-1700-15-runtime-05e8748-automated-qa.md`
- `docs/handoffs/task-completions/root-user-smoke-verification-after-resolver-fix-05e8748.md`

Currently changed by recent coordination/cleanup:

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/final-readiness-refresh-05e8748.md`
- `docs/handoffs/task-completions/repo-steward-05e8748-browser-ready-docs-commit.md`
- `docs/handoffs/task-completions/repo-steward-answer-eval-whitespace-cleanup.md`
- `docs/answer-eval-report.md` (trailing whitespace cleaned, but content rewrite remains parked/uncommitted)

Broad parked dirty/untracked files remain outside the 05e8748 readiness scope, including docs/corpus/source metadata, root RAG scripts, landing/static/design assets, source-inbox metadata, historical handoffs/assets, `public/`, `ui/brand/`, `Neon Sign/`, and private-lesson helper scripts/data.

## 4. Conflicts Or Overlapping Changes

- `docs/answer-eval-report.md` is the main overlap risk:
  - whitespace has been cleaned;
  - `git diff --check` passes;
  - the file still contains a large generated report-content rewrite, so it is not safe to stage as a whitespace-only change.
- `docs/handoffs/task-completions/integration-status.md` is a coordination artifact and should not be bundled with implementation commits.
- Many untracked handoffs/assets are historical or parked; do not stage them without exact scope.
- Static/UI full-suite caveats should not be mixed with backend answer/RAG commits.

## 5. Schema / API / Component / Data Contract Changes

- No new `/api/answer` schema change is pending from this readiness refresh.
- Runtime `05e8748` confirms answer routing behavior is ready without schema migration.
- Protected-preview `/api/version` was used as the runtime identity source.
- Root route behavior: `/` redirects to `/ui/steel-guitar-rag-mock.html`; this is verified and acceptable for current user smoke.
- API fallback QA must remain labeled as API fallback, not browser smoke.
- No corpus, Chroma/vector, embedding, source-inbox, scraping, auth-policy, DNS, or deployment contract changes are part of the current ready state.

## 6. Tests Reported By Lane

### Lane 05 Backend

- `05e8748` implementation handoff reported:
  - focused answer/classifier/API tests: `364 passed`;
  - contract/eval tests: `68 passed`;
  - full pytest: `703 passed, 2 failed`.
- The two full-suite failures were classified as unrelated static/UI failures:
  - landing source vs deployed static HTML mismatch;
  - missing public fretboard background route.

### Lane 12 Deployment / Protected Preview

- Authenticated protected-preview browser smoke: passed.
- `/api/version`: reported `05e8748`.
- Root route: passed.
- Fallback UI route: passed.
- Unauthenticated local `/api/answer`: still returned `401`, as expected.

### Lane 15 QA

- Focused automated API fallback smoke: `36` true pass / `0` true blockers.
- Strict scorer:
  - `295` questions;
  - `152` pass, `33` warn, `110` fail by broad scorer;
  - true blocker count for requested runtime QA scope: `0`;
  - strict SGF leakage hard gates all `0`.
- Focused pytest set: `376 passed`.
- Minimal browser verification: six prompt smoke passed.

### Lane 01 Repo Steward

- `git diff --check`: passed after `docs/answer-eval-report.md` trailing whitespace cleanup.
- Browser-ready handoff docs committed in `449cdee`.
- Current coordination refresh not committed.

## 7. Blockers Or Human Decisions Needed

- User smoke/use is ready now at `https://app.steelguitarrag.com/`.
- No human decision is needed before using the app.
- Human decision is needed only if someone wants to commit parked docs/report/source/static work.
- Do not treat broad strict eval failures as user-smoke blockers unless a future lane reclassifies a specific row as a true product failure.
- Do not restart broad QA today unless a new real blocker appears.

## 8. Dirty Worktree / Commit Readiness

- Current worktree is broadly dirty with parked non-runtime work.
- `git diff --check`: passes.
- Runtime readiness remains based on committed runtime `05e8748` and committed verification docs, not the broad dirty worktree.
- Dirty tracked files include:
  - `README.md`
  - `corpus_metadata/source_policies/README.md`
  - `corpus_metadata/source_registry.json`
  - `deploy/landing/index.html`
  - `docs/answer-eval-report.md`
  - `docs/cloudflare-pages-landing.md`
  - `docs/copyright-provenance.md`
  - `docs/corpus-license-policy.md`
  - `docs/current-commands.md`
  - `docs/handoffs/task-completions/integration-status.md`
  - `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
  - `docs/source-inbox-inventory.md`
  - root RAG scripts
  - `source-inbox/inventory.json`
- Many untracked historical handoffs/assets and design/source/corpus helper files remain parked.

## 9. Files Safe To Stage

Safe only if a docs-only coordination commit is explicitly requested:

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/final-readiness-refresh-05e8748.md`
- `docs/handoffs/task-completions/repo-steward-05e8748-browser-ready-docs-commit.md`
- `docs/handoffs/task-completions/repo-steward-answer-eval-whitespace-cleanup.md`

Safe only if explicitly approving the generated report-content rewrite as its own docs/report slice:

- `docs/answer-eval-report.md`

## 10. Files That Should Remain Unstaged

Keep unstaged unless a later exact lane approves them:

- implementation/runtime files not part of a current scoped task;
- root RAG/build scripts;
- corpus metadata/source policy files;
- `source-inbox/` inventory/provenance files;
- `public/`, `ui/brand/`, `Neon Sign/`, raw/generated design assets;
- deployment/static files such as `deploy/landing/index.html` unless a Lane 06/static task owns them;
- broad historical handoffs/assets;
- `docs/answer-eval-report.md` unless committing the full generated report-content update is explicitly approved.

## 11. Recommended Next Tasks By Lane

- Primary action: use the app at `https://app.steelguitarrag.com/`.
- Lane 12: no action unless runtime becomes unavailable or a new protected-preview issue appears.
- Lane 15: optional scorer calibration backlog only; do not run broad QA today unless a new real blocker appears.
- Lane 06: optional static/full-suite cleanup only if someone wants full-suite cleanliness.
- Lane 01: optional docs-only coordination commit if desired.
- Lane 05: only open new backend work for a new true user-facing blocker.

## 12. Exact Codex Prompts For Next Recommended Tasks

### Primary User Smoke / Use

```text
Use https://app.steelguitarrag.com/ for authenticated protected-preview user smoke. If a new issue appears, report the exact prompt, expected behavior, actual browser behavior, and whether the issue is visible in the UI or only in API output. Do not reopen completed 05e8748 smoke work unless new evidence contradicts the committed handoffs.
```

### Optional Lane 15 Scorer Calibration

```text
LANE: 15 QA / Answer Eval
REASONING: LOW
Branch: feature/answer-api

Calibrate scorer false positives from the 05e8748 runtime QA run without changing backend product behavior.

Read:
- docs/handoffs/task-completions/2026-06-14-1700-15-runtime-05e8748-automated-qa.md
- scripts/run_full_answer_quality_eval.py
- tests/test_full_answer_quality_eval.py

Focus only on scorer/eval noise:
- music-theory notation such as I-to-IV being mistaken for first-person forum fragments;
- direct capability caveats being mistaken for raw SGF/forum text;
- joke/song-title prompts where the scorer overstates unrelated theory fragments.

Do not modify backend answer behavior, UI, deployment, auth, corpus, Chroma/vector stores, embeddings, source-inbox, scraping, DNS, secrets, or visual assets.

Run focused scorer tests and write a handoff. Do not commit unless Repo Steward is explicitly invoked.
```

### Optional Lane 06 Static / Full-Suite Cleanup

```text
LANE: 06 UX/UI Design
REASONING: MEDIUM
Branch: feature/answer-api

Fix only the two unrelated static/UI full-suite failures if full-suite cleanliness is desired:
- landing source vs deployed static HTML mismatch;
- missing public fretboard background route in same-origin static smoke.

Read:
- AGENTS.md
- tests/test_public_landing_page.py
- tests/test_same_origin_smoke_server.py
- deploy/landing/index.html
- relevant public/static files

Do not touch backend answer routing, /api/answer schema, corpus, Chroma/vector stores, embeddings, source-inbox, scraping, DNS, auth policy, secrets, or unrelated handoffs.

Run the two focused static tests and any minimal related frontend/static checks. Write a handoff naming exact files/hunks for Repo Steward.
```

### Optional Lane 01 Docs Coordination Commit

```text
LANE: 01 Repo Steward
REASONING: LOW
Branch: feature/answer-api

Commit only the docs-only final readiness coordination refresh if desired.

Candidate files:
- docs/handoffs/task-completions/integration-status.md
- docs/handoffs/task-completions/final-readiness-refresh-05e8748.md
- docs/handoffs/task-completions/repo-steward-05e8748-browser-ready-docs-commit.md
- docs/handoffs/task-completions/repo-steward-answer-eval-whitespace-cleanup.md

Do not stage docs/answer-eval-report.md unless separately approving the full generated report-content rewrite. Do not stage implementation files, UI files, deployment/auth/DNS files, corpus/source-inbox/Chroma/embedding data, design assets, or unrelated handoffs.

Run git diff --cached --check, git diff --cached --name-only, and git diff --cached before committing.
```

## 2026-06-18 Tab Engine UI And Planning Follow-On

- Current repository HEAD after Repo Steward reconciliation: `54a28c7 fix: clear tab examples on stage return`.
- Relevant committed tab-engine follow-on commits:
  - `0bd0780 test: add tab engine ui QA coverage`
  - `07f9b9d feat: render tab examples on answer page`
  - `54a28c7 fix: clear tab examples on stage return`
- Backend baseline remains `686fd3c feat: add deterministic tab engine slice`.
- UI state:
  - Answer-page tab rendering is committed.
  - Tab examples render from normalized backend/API tab payloads; no fake frontend tab generator was added.
  - Follow-up fix clears tab examples when returning from answer workspace to the home/stage view.
- Planning handoffs to keep with this follow-on work:
  - `docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples-implementation-plan.md`
  - `docs/handoffs/task-completions/2026-06-18-12-tab-engine-deploy-smoke-plan.md`
  - `docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md`
  - `docs/handoffs/task-completions/2026-06-18-19-tab-card-visual-guidance.md`
- Focused checks run by Repo Steward:
  - `.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py`: passed.
  - `.venv/bin/python -m pytest tests/test_tab_engine.py -q`: `16 passed`.
  - `.venv/bin/python -m pytest tests/test_api_contract.py -q`: `4 passed`.
  - `.venv/bin/python -m pytest tests/test_api_search.py -q`: `246 passed`.
  - `node --check ui/answer-client.js`: passed.
  - `node --check ui/pedal-steel-fretboard.js`: passed.
  - `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`: `20 passed`.
  - `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`: `29 passed`.
  - `git diff --check`: passed.
  - `.venv/bin/python -m pytest -q`: `738 passed, 2 failed`.
- Full-suite failures remain the known unrelated static/UI caveats:
  - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
  - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
- Dirty runtime caveat:
  - `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py` still contain unrelated landing-sign cache-bust changes after the tab-specific hunk was committed.
- Next recommended slice: Lane 05 answer-triggered deterministic tab examples using the architecture and implementation-plan handoffs above.
