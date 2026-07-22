# Amazing Tablature frontend fallback and release handoff

## Task summary

Completed the approved bounded training-to-frontend run without opening validation imagery or sealed-test data.

- Rebuilt the authoritative discovery-only challenger from clean HEAD `68d9b17cf4f0fb4559a0f706772da23d6fd118bc` using the 278-page main batch and 34-page licks batch only. The superseded 51-image batch remains excluded.
- Selected discovery challenger `at-ca3af91682513311` (artifact SHA-256 `7a815d7cd7a8d8a7ffc5cb48c5cd2ad950ee5c72c856e505d3ec87bb0cdbcbf1`) after the bounded two-configuration comparison. Its discovery source agreement is `0.909434`; this is not a validation or production-accuracy claim.
- Preserved exact preference accounting (`16` reviewed, `6` training, `10` co-validation), suppressed all previously reviewed lines from re-review selection, and confirmed `validationAccessed=false` and `sealedTestAccessed=false`.
- Did not promote the challenger. Existing structural preflight leaves 56 of 57 main validation lines and 5 of 6 licks validation lines blocked, so it cannot produce a trustworthy human comparison packet.
- Retired the old learned runtime model based on the superseded dataset and left Melody Studio on `deterministic-fallback-v1`, with hard E9 mechanics and pitch validation intact.
- Added visible Melody Studio result copy that distinguishes verified deterministic E9 rules from a future enabled trained ranker. It also states that imported score images are reviewed before arranging.

Intentionally not changed: validation or sealed-test membership/content; raw images; embeddings/vector stores; scraper behavior; auth; DNS; Cloudflare policy; source material; score-image recognition; exact challenger promotion.

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-22-1725-06-amazing-tablature-frontend-fallback.md`

No files were deleted. Private challenger artifacts remain beneath ignored `corpus-private/melody-decisions/` and must not be staged.

## Tests and checks

- `node --check ui/melody-workbench.js` — passed.
- `.venv/bin/pytest -q tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py tests/test_frontend_answer_ui.py tests/test_copedent_transfer.py tests/test_amazing_tablature_training.py` — `122 passed`.
- `.venv/bin/pytest -q` — `1375 passed`.
- `git diff --check` — passed.
- In-app browser local same-origin smoke — passed for `1 2 3 5` in G. Melody Studio rendered four score events, synchronized fretboard/tab output, and the visible deterministic engine status. No blank result event was observed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8784/ui/melody-workbench.html?access=beta_user&v=arrangement-engine-68d9b17-local`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL to be recorded after exact release activation
- Auth required: no (explicit loopback-only local development role used)
- Auth provider: local development scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8784`
- Expected backend port: `8784`
- Expected git HEAD: `68d9b17cf4f0fb4559a0f706772da23d6fd118bc` plus the scoped uncommitted UI slice
- Version endpoint: `http://127.0.0.1:8784/api/version`
- Version endpoint result: local working-tree server; exact committed preview verification remains next
- If version endpoint missing, how version is inferred: current repository HEAD plus scoped diff
- Whether app root `/` works: covered by same-origin tests
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: covered by same-origin tests
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex only
- Do not test these URLs: validation or sealed-test review URLs; stale discovery review packets
- Known caveats: this smoke proves deterministic arrangement rendering, not score-image recognition and not protected-preview behavior

## Integration notes

The normalized notes/interval/staff-editor path can produce and validate score events before arrangement. Score-image upload remains a separate review-first recognition step. The discovery challenger remains useful research evidence but is not wired into runtime because its 21-feature canonical schema is not yet supplied by the runtime adapter and the independent validation capture gate is not structurally ready.

The next trained-ranker slice must first build a production inference adapter that emits the exact canonical feature schema, add parity fixtures between trainer and runtime, and obtain a valid independent comparison set. No ranker should be enabled merely by copying the discovery weights.

## Risk assessment

Medium product risk, low release risk. The principal unresolved risk is score-image/event recognition, not deterministic arrangement from structured notes. The frontend change is informational and backed by existing response metadata. Rollback is a normal revert of the scoped UI commit; the deterministic arranger remains the safe fallback.

## Human decision needed

No. The approved fallback path can proceed through exact-path commit and protected-preview smoke. A future exact challenger promotion still requires explicit model-ID approval after independent QA.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-22-1725-06-amazing-tablature-frontend-fallback.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing unrelated dirty coordination state)
- All other untracked historical handoffs
- Everything under `corpus-private/`
- Raw source images, validation data, sealed-test data, embeddings, vector stores, credentials, environment files, logs, and generated reports

## Recommended next lane

Lane 01 Repo Steward for exact-path commit, followed by Lane 12 Self-Hosted Deployment for exact-release activation and authenticated protected-preview browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Stage only the five exact paths above, commit the frontend fallback status slice, activate the exact release using `docs/private-preview-operations.md`, verify `/api/version`, and browser-smoke the cache-busted protected Melody Studio URL.
