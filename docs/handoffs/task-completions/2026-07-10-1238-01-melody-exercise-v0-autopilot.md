# Melody Exercise v0 Autopilot Handoff

## Task summary

Implemented the approved stabilization and Melody Exercise v0 slice. Copyright status no longer blocks artist-solo, recording, or complete-arrangement teaching. The implementation preserves attribution and accuracy, asks for inaccessible source material, sections long material, and renders validated E9 melody events through a shared tab/fretboard sequence. The app-wide feature flag defaults off; the approved protected-preview wrapper defaults it on for testing.

Intentionally not changed: corpus ingestion, scraping, embeddings, Chroma/vector data, private transcripts, auth policy, DNS, Cloudflare Access policy, raw source-inbox data, or unrelated parked work.

## Lane classification

- Lanes: 18 Product / Architecture, 05 Backend / RAG Integration, 06 UX/UI Design, 15 QA, 01 Repo Steward, then 12 Self-Hosted Deployment.
- Mode: approved mixed Autopilot feature run.
- Repo Steward: proceeding under auto-approval because the feature scope is approved and the exact file list is clear.

## Files changed

- Governance/status: `AGENTS.md`, workflow/completion docs, canonical Melody Exercise contract, API/answer/teacher/tab/progression guidance, two historical-status banners, and the authenticated answer-eval report.
- Backend: optional Melody Exercise API contract/routing, deterministic E9 G/C placement, shared event validation, song/solo teaching routing, and updated curated guidance.
- Frontend: feature-gated Melody/Arrangement form, stepper, attribution/accuracy/section UI, synchronized event identifiers, fixed-width tab, and empty-source handling.
- QA/deployment: evaluator local-auth header, regression tests, frontend cache-buster, and protected-preview feature enablement.
- Created: `pocketsteel/melody_assistant.py`, `tests/test_melody_assistant.py`, `docs/melody-exercise-v0.md`.
- Deleted: none.
- Generated artifact explicitly approved for replacement: `docs/answer-eval-report.md`.

## Tests and checks

- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 911 passed.
- Expanded focused suite — 462 passed.
- Final focused contract/frontend/eval suite — 69 passed.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `bash -n deploy/macos/run-private-preview-app.sh deploy/macos/install-private-preview-launchdaemon.sh` — passed.
- `git diff --check` — passed after fixing generated-report whitespace.
- Authenticated local evaluation: 295 requests against `http://127.0.0.1:8898` with explicit `beta_user` development role; zero 401-only failure pattern. Automated buckets: 29 pass, 76 directness, 1 formatting, 1 retrieval mismatch, 188 weak/no-source. These are quality/backlog signals, not authentication failures.
- One initial combined pytest invocation failed collection because `PYTHONPATH` omitted the repo-required `.:scripts`; rerun with the expected path passed.
- First local smoke server attempt used the absent legacy v1 Chroma path; the documented v2 store was then used read-only. No Chroma data was changed.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/steel-guitar-rag-mock.html?access=beta_user&v=melody-v0-local-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL only after Lane 12 passes
- Auth required: yes
- Auth provider: local scaffold development role
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: 8898
- Expected git HEAD: pre-commit working tree based on `da1a7630f991fa16c60d39c2b81f8c5629163549`
- Version endpoint: `http://127.0.0.1:8898/api/version`
- Version endpoint result: `da1a763`, branch `feature/answer-api`, `features.melodyExercise=true`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not used in local smoke
- Whether app root `/` is expected to work: not asserted
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: legacy v1/absent `rag-data/electronics/chroma` server path
- Known caveats: the answer eval intentionally exercises existing answer-quality backlog; local API/browser smoke does not prove protected preview.

Browser results:

- Artist lesson rendered recording identity, approximate/medium label, eight steps, source reference, fixed-width tab, and fretboard.
- Step 2 selected the same `melody-step-2` and `melody-g-section-1-event-2` identifiers in tab and fretboard state.
- Tab computed `white-space: pre` and `overflow-x: auto`; responsive check preserved spacing.
- Original exercise suppressed stale recording identity and all source links.
- No `[object Object]` rendering.

## Integration notes

- Optional request key: `melodyRequest` (snake-case alias also accepted).
- Optional response key: `melody_exercise`.
- Feature flag: `STEEL_RAG_ENABLE_MELODY_EXERCISE`; app default off, protected-preview wrapper default on.
- Deterministic v0 scope: E9, G/C major, at most eight events per section.
- Structured input accepts `melody`, `tokens`, or `events` aliases and nested or top-level material identity.
- Artist/song requests without accessible notes return `needs_source`, not a refusal.

## Risk assessment

- Risk: medium because answer routing, API, frontend, and private-preview startup behavior change.
- Mitigations: default-off app flag, deterministic scope, mechanical validation, 911-test full suite, browser smoke, and exact-path staging.
- Rollback: disable `STEEL_RAG_ENABLE_MELODY_EXERCISE` in the protected-preview environment or revert the scoped implementation commit.

## Dirty worktree classification

- Baseline contained 45 tracked modified paths and 1,789 untracked porcelain entries.
- Protected/generated groups include corpus/vector/source-inbox/design/deployment-adjacent artifacts; their contents were not inspected or staged unless explicitly named in this approved slice.
- Unrelated tracked files such as `README.md`, corpus/source policy files, raw pipeline scripts, source-inbox inventory, landing assets/docs, and prior handoffs remain parked.
- No broad staging, deletion, cleanup, reset, checkout, or private/generated content inspection was performed.

## Human decision needed

No. The user approved the full feature loop through protected-preview smoke. A genuine sudo/auth/runtime blocker remains a stop condition.

## Safe-to-stage exact file list

- `AGENTS.md`
- `deploy/macos/run-private-preview-app.sh`
- `docs/answer-eval-report.md`
- `docs/api-contract.md`
- `docs/chatgpt-project-context/05_Current_Integration_Snapshot.md`
- `docs/codex-workflow.md`
- `docs/current-project-status.md`
- `docs/handoffs/task-completions/2026-07-10-1238-01-melody-exercise-v0-autopilot.md`
- `docs/llm-guidance/answer-contract.md`
- `docs/llm-guidance/teacher-first-answer-policy.md`
- `docs/mac-mini-private-preview-launchd.md`
- `docs/melody-exercise-v0.md`
- `docs/process/codex-completion-protocol.md`
- `docs/progression-guide-v0.md`
- `docs/tab-feature-guardrails.md`
- `pocketsteel/answer_contracts.py`
- `pocketsteel/answer_tab_examples.py`
- `pocketsteel/answering.py`
- `pocketsteel/api.py`
- `pocketsteel/api_contract.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/curated_song_references.py`
- `pocketsteel/melody_assistant.py`
- `pocketsteel/progression_guide.py`
- `pocketsteel/resources/curated/steel-guitar-rag-expert-reference.md`
- `scripts/run_answer_eval.py`
- `tests/test_answer_contract_schemas.py`
- `tests/test_answer_eval.py`
- `tests/test_api_contract.py`
- `tests/test_api_search.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_assistant.py`
- `tests/test_same_origin_smoke_server.py`
- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`

## Files that must not be staged

Every path not listed above, especially corpus/private/vector/embedding/source-inbox/raw data, `public/`, `ui/brand/`, `Neon Sign/`, `.wrangler/`, unrelated pipeline scripts, landing assets, and unrelated status/handoff changes.

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 protected-preview restart/version/authenticated browser smoke and an integration-status refresh.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the exact files above, review the cached diff, commit the scoped feature, then run the authorized protected-preview lifecycle.
