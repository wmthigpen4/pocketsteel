# Public-domain Melody Studio songbook implementation

## Task summary

Implemented the approved starter songbook as an authenticated, built-in Melody Studio capability. The catalog now contains 12 reviewed teaching phrases in G or C, opens directly in the existing score review workflow, and continues through the validated E9 arranger. The built-in catalog is available whenever Melody Exercise is enabled; user uploads and MusicXML/MIDI/image imports remain independently gated.

The songbook browser now provides title/attribution search plus difficulty, meter, and feel filters. Cards show source identity, teaching-version labels, key, meter, difficulty, feel, note count, and section count. Source links remain attribution references and never imply automatic transcription.

Intentionally not changed: auth policy, upload/import enablement, persistence, source-link transcription, scraping, corpus data, Chroma, embeddings, private sources, deployment configuration, brand assets, or unrelated dirty files.

## Files changed

- `steel_guitar_rag/api.py`
- `steel_guitar_rag/melody_import.py`
- `steel_guitar_rag/resources/public_domain_songs/starter_songbook_v1.json` (new)
- `ui/answer-client.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_api_search.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_import.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-2340-18-public-domain-songbook-expansion-plan.md` (approved plan)
- `docs/handoffs/task-completions/2026-07-12-0847-01-public-domain-songbook-implementation.md` (this handoff)

No files were deleted. No generated runtime artifacts are part of the feature scope.

## Tests and checks

- `PYTHONPATH=. .venv/bin/pytest -q` — **936 passed**.
- Focused catalog/API/frontend/same-origin suite — **346 passed**.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- `node --check ui/melody-score.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- Scoped `git diff --check` — passed.
- Parsed the new catalog JSON successfully.
- Checked every source URL; replaced two stale IMSLP URLs with resolving Library of Congress provenance pages. Library of Congress item endpoints return bot-protection responses to command-line checks but are valid browser-facing records.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8789/ui/melody-workbench.html?access=beta_user&v=melody-songbook-local-20260712`
- Cache-busted URL tested: `http://127.0.0.1:8789/ui/melody-workbench.html?access=beta_user&v=melody-songbook-local-20260712`
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: yes
- Auth provider: local controlled-state beta role
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8789`
- Expected backend port: 8789
- Expected git HEAD: pre-commit working tree on `bf25733`
- Version endpoint: `http://127.0.0.1:8789/api/version?access=beta_user`
- Version endpoint result: feature contract exposed `melodyExercise=true` and `melodyCatalog=true`
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: bare local URLs without the controlled-state access query
- Known caveats: local browser smoke does not prove Cloudflare Access or protected-preview runtime state

Local browser results:

- Songbook remained available while upload/import entry was hidden.
- `Browse songbook (12)` loaded 12 cards.
- Searching for `Shenandoah` returned one matching card.
- Opening Shenandoah entered Review melody with 16 events, source identity, and C key intact.
- Arrange for E9 rendered the score, route choices, synchronized fretboard, and tablature without an error.
- Catalog copy explicitly states that source links identify the teaching version and are not automatically transcribed.

## Integration notes

- New session/version feature: `features.melodyCatalog=true` whenever `melodyExercise=true`.
- `GET /api/melody/catalog` and catalog-only `POST /api/melody/import` now depend on Melody Exercise, not the broader import flag.
- Non-catalog imports remain blocked unless `melodyImport=true`.
- Existing `score_draft_v1`, `melodyRequest`, and `melody_exercise` contracts are unchanged.
- New catalog records are compact at rest and deterministically expanded into normalized, checksummed score drafts.
- Teaching phrases are labeled `interpretive`; they do not claim note-for-note fidelity to a specific performance.

## Risk assessment

Medium-low. Runtime and contract changes are narrowly feature-gated and fully regression-tested. Musical examples are explicit reviewed teaching phrases rather than exact-performance transcriptions. Rollback is the scoped feature commit; no persistent data migration exists.

## Human decision needed

No. The feature scope was approved. User smoke should begin only after committed protected-preview smoke passes.

## Safe-to-stage exact file list

- `steel_guitar_rag/api.py`
- `steel_guitar_rag/melody_import.py`
- `steel_guitar_rag/resources/public_domain_songs/starter_songbook_v1.json`
- `ui/answer-client.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_api_search.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_import.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-2340-18-public-domain-songbook-expansion-plan.md`
- `docs/handoffs/task-completions/2026-07-12-0847-01-public-domain-songbook-implementation.md`

## Files that must not be staged

All other modified or untracked files, including the separate octave-help recommendation, corpus and source-inbox paths, private-data tooling, deployment files, `public/`, `ui/brand/`, `Neon Sign/`, generated reports, and unrelated docs/runtime changes.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with exact-path staging, then restart the documented protected preview and verify the cache-busted Melody Studio URL end to end.
