# Melody Studio multi-input and lead-sheet builder

## Task summary

Implemented the approved Melody Studio multi-input feature across Lane 18 product contract, Lane 05 import/arranger behavior, Lane 06 UI, and Lane 15 QA. The existing notes/intervals/E9-position phrase editor remains intact as an equal input method.

Added:

- Six equal entry cards: notes/intervals, score builder, photo/music file, play/hum, recording companion, and public-domain catalog.
- A session-only `score_draft_v1` contract and structured melody request metadata for exact pitch, rhythm, measure, beat, chord, tie, lyric, and event origin.
- A focused G/C lead-sheet builder with 3/4 and 4/4, pickup, notes/rests, supported durations, chords, lyrics/labels, ties, selection editing, keyboard entry, staff entry, undo/redo, measure actions, duplicate, transpose, browser synthesis, and deliberate local MusicXML download.
- A pinned, locally served VexFlow 5.0.0 SVG renderer with the prior local SVG implementation retained as a browser fallback.
- Authenticated, default-off `GET /api/melody/catalog` and `POST /api/melody/import` endpoints with no-store responses, bounded bodies, in-memory MXL processing, local-loopback vision, MusicXML/MIDI part selection, and no arbitrary URL fetching.
- Client-side, 15-second monophonic pitch capture that discards microphone audio and retains only editable candidates.
- Official YouTube embed/A-B companion controls and a non-scraping Ultimate Guitar/reference-link path.
- Reviewed Amazing Grace / NEW BRITAIN catalog data with public-domain attribution, source checksum, melody, chords, and exact E9 pilot route.
- Faithful melody, vocal steel, and harmony routes. Generated ornaments remain separate metadata, are labeled in score/tab teaching UI, and disappear when Faithful melody is selected.

Intentionally not changed: auth policy, Cloudflare policy, DNS, scraping, corpus, Chroma/embeddings, source-inbox, raw/private data, broad app naming, public launch policy, or unrelated dirty worktree files.

## Files changed

- `pocketsteel/api.py`
- `pocketsteel/api_contract.py`
- `pocketsteel/melody_arranger.py`
- `pocketsteel/melody_assistant.py`
- `pocketsteel/melody_import.py`
- `pocketsteel/resources/public_domain_songs/amazing_grace_new_britain.json`
- `ui/answer-client.js`
- `ui/melody-score.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `ui/vendor/vexflow-5.0.0.js`
- `ui/vendor/VEXFLOW-LICENSE.txt`
- `tests/test_api_search.py`
- `tests/test_melody_assistant.py`
- `tests/test_melody_import.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- This handoff.

No files were deleted. The VexFlow bundle and license are the only generated/vendor artifacts in scope.

## Tests and checks

- `python3 -m py_compile pocketsteel/api.py pocketsteel/api_contract.py pocketsteel/melody_arranger.py pocketsteel/melody_assistant.py pocketsteel/melody_import.py` — pass.
- `node --check ui/answer-client.js` — pass.
- `node --check ui/melody-score.js` — pass.
- `node --check ui/melody-workbench.js` — pass.
- Focused melody/API/UI/import test slice — `39 passed, 300 deselected`.
- Relevant combined backend/frontend slice — `365 passed`.
- Full test suite — `933 passed in 38.57s`.
- `git diff --check` on the exact feature paths — pass.
- Local browser smoke — pass: manual input visible, six cards visible, score event editing/arranging works, VexFlow 5.0.0 is the active renderer, Amazing Grace loads eight exact notes and six chord changes, exact initial E9 positions render, generated F#4→G4 ornament toggles with the Vocal steel/Faithful melody routes, and the mobile page has no document-level horizontal overflow.

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-multi-input-20260711-3`
- Exact URL the user should use: protected-preview URL to be recorded after commit/restart
- Auth required: yes
- Auth provider: local dev scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: `8765`
- Expected git HEAD: `8821890` before feature commit
- Version endpoint: `http://127.0.0.1:8765/api/version`
- Version endpoint result: `git_sha=8821890`, `melodyExercise=true`, `melodyImport=true`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, `302` to the main UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes, `200`
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: production; arbitrary external upload targets
- Known caveats: image recognition requires the configured local `gemma4:12b` loopback model; public release still requires legal/privacy review

## Integration notes

- `STEEL_RAG_ENABLE_MELODY_IMPORT` defaults off. Protected preview must explicitly enable it alongside `STEEL_RAG_ENABLE_MELODY_EXERCISE` to expose catalog/import methods.
- Imported/uploaded files and drafts are never placed in a database, local/session storage, corpus, R2, or disk by this feature.
- MusicXML/MXL and MIDI report multipart choices and suggest the highest sustained voice. Simultaneous voices derive harmony only when an explicit chord symbol is absent, marked `basis: derived`.
- Image output cannot arrange until the user reviews and explicitly chooses “Confirm and arrange for E9.”
- YouTube is player-only; Ultimate Guitar is link/paste-reference-only. Neither source is downloaded or scraped.
- No schema migration or persistent store was added.

## Risk assessment

Medium. This is a broad but feature-flagged UI/API slice. Main residual risks are local vision-model availability, browser microphone quality across devices, and legal/privacy review before public release. Rollback is the single scoped feature commit; disabling `STEEL_RAG_ENABLE_MELODY_IMPORT` removes server import/catalog exposure while preserving the existing phrase editor.

## Human decision needed

No for implementation and protected-preview smoke. Yes before public release: legal/privacy review of copyrighted teaching workflows and upload disclosures remains required.

## Safe-to-stage exact file list

- `pocketsteel/api.py`
- `pocketsteel/api_contract.py`
- `pocketsteel/melody_arranger.py`
- `pocketsteel/melody_assistant.py`
- `pocketsteel/melody_import.py`
- `pocketsteel/resources/public_domain_songs/amazing_grace_new_britain.json`
- `ui/answer-client.js`
- `ui/melody-score.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `ui/vendor/vexflow-5.0.0.js`
- `ui/vendor/VEXFLOW-LICENSE.txt`
- `tests/test_api_search.py`
- `tests/test_melody_assistant.py`
- `tests/test_melody_import.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-0837-18-melody-studio-multi-input-builder.md`

## Files that must not be staged

Every other dirty or untracked path, especially corpus/source-inbox files, `public/`, brand/design assets, `Neon Sign/`, deploy/Cloudflare files, private lesson files, generated reports, Chroma/vector data, and unrelated documentation.

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 protected-preview restart and browser smoke using the committed HEAD.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the exact files above, review the cached diff, commit the feature, update the protected preview with the documented safe restart command, and run the required cache-busted browser smoke.
