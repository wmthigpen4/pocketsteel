# Full-song songbook implementation

## Task summary

Expanded Melody Studio's reviewed songbook from short excerpts to complete melodic forms. Every catalog title now contains one complete melody cycle: a verse plus a distinct chorus/refrain where the music changes, or one complete verse/refrain when additional lyrical verses reuse the same tune. Fixed eight-note slicing was replaced by reviewed phrase/measure sections, with a 16-event fallback for manually entered melodies.

The lesson view now keeps the complete lead sheet visible, identifies the current phrase, moves backward and forward between phrases without losing the reviewed score, and prepares all phrases of the selected arrangement route for complete-song tablature printing.

Intentionally unchanged: audio transcription, authentication, corpus/Chroma, scraping, source-inbox, private data, Cloudflare policy, DNS, brand assets, and general answer behavior.

## Files changed

- `docs/melody-exercise-v0.md`
- `pocketsteel/melody_assistant.py`
- `pocketsteel/melody_import.py`
- `pocketsteel/resources/public_domain_songs/amazing_grace_new_britain.json`
- `pocketsteel/resources/public_domain_songs/starter_songbook_v1.json`
- `ui/answer-client.js`
- `ui/melody-score.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_api_search.py`
- `tests/test_melody_assistant.py`
- `tests/test_melody_import.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-0913-18-full-song-songbook-diagnosis.md`
- `docs/handoffs/task-completions/2026-07-12-1005-01-full-song-songbook-implementation.md`

No files were deleted. No generated artifacts were added.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_melody_import.py tests/test_melody_assistant.py tests/test_melody_workbench_ui.py tests/test_frontend_answer_ui.py tests/test_api_contract.py tests/test_api_search.py tests/test_same_origin_smoke_server.py` — pass after updating stale excerpt/cache assertions.
- `.venv/bin/python -m pytest -q` — **938 passed**.
- `node --check ui/answer-client.js` — pass.
- `node --check ui/melody-score.js` — pass.
- `node --check ui/melody-workbench.js` — pass.
- `git diff --check` — pass.
- Programmatic all-catalog traversal — every phrase of all 12 songs produced a validated E9 lesson.
- Local browser smoke — pass for catalog metadata, 35-note Amazing Grace review, complete lead-sheet rendering, phrase 1 → phrase 2 → phrase 1 navigation, synchronized tab/fretboard, and absence of visible errors.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=full-song-local-20260712`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=full-song-local-20260712`
- Exact URL the user should use: protected-preview URL to be recorded after commit/restart
- Auth required: local development role header
- Auth provider: scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: pre-commit working tree
- Version endpoint: not used for local pre-commit smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: local files served directly from the working tree
- Whether app root `/` works: not tested in this feature smoke
- Whether app root `/` is expected to work: yes in protected preview
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in this focused local smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: production root before the protected-preview restart
- Known caveats: reviewed public-domain melodies can have traditional variants; catalog labels identify these as teaching versions

## Integration notes

- `melodyRequest.sections` is optional and backward compatible. Each item carries a phrase label plus `startMeasure` and `endMeasure`.
- `melody_exercise.section` now additionally carries `previousSection`, `eventStart`, `eventEnd`, `measureStart`, and `measureEnd`.
- Existing top-level event/tab/fretboard compatibility fields remain unchanged.
- Import limits are now 128 melody events and 64 measures. Reviewed section boundaries remain intact through client-side score edits/reflow.
- Songbook card metadata now includes complete-form label, note count, measure count, and phrase count.

## Risk assessment

Medium. Runtime/API changes are backward compatible and fully regression-tested. The remaining product risk is variant choice in traditional melodies; every catalog item is explicitly labeled as a reviewed teaching version rather than a performance-exact transcription. Rollback is the scoped implementation commit.

## Human decision needed

No. The complete-melody-cycle and phrase-section direction was explicitly approved.

## Safe-to-stage exact file list

- `docs/melody-exercise-v0.md`
- `pocketsteel/melody_assistant.py`
- `pocketsteel/melody_import.py`
- `pocketsteel/resources/public_domain_songs/amazing_grace_new_britain.json`
- `pocketsteel/resources/public_domain_songs/starter_songbook_v1.json`
- `ui/answer-client.js`
- `ui/melody-score.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_api_search.py`
- `tests/test_melody_assistant.py`
- `tests/test_melody_import.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-0913-18-full-song-songbook-diagnosis.md`
- `docs/handoffs/task-completions/2026-07-12-1005-01-full-song-songbook-implementation.md`

## Files that must not be staged

All other modified and untracked paths, especially corpus/source-inbox/private-data work, deployment files, `public/`, `ui/brand/`, `Neon Sign/`, generated reports, and unrelated docs/runtime files.

## Recommended next lane

`01 Repo Steward` exact-path commit, then `12 Self-Hosted Deployment` protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with exact-path staging of the listed files, commit the complete-song slice, restart the protected preview, verify `/api/version`, and perform authenticated browser smoke on a cache-busted Melody Studio URL.
