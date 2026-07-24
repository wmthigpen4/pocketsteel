# Blocking and Lever-Density Arranger Fixtures

## Task summary

Added narrowly reviewed regression fixtures for two accepted E9 arranger rules:

- A validated full-grip slide sustains every attacked string; a changed-grip melody-only exception must distinguish the sustained voice, strings blocked before the slide, reused strings repicked at the destination, and newly added strings.
- E-lower and F-lever should not be entered when an equally correct no-lever position has no musical or mechanical disadvantage, but a required lever span should remain continuous rather than exiting for one note and immediately re-entering.

The blocking fixture exposed and corrected one instruction bug: reused and newly introduced destination strings were previously grouped under one `repick` verb. They are now described separately.

Intentionally not changed: candidate generation, pitch validation, texture selection, public API structure, tab connector semantics, UI layout, corpus/private data, source routing, embeddings, scraping, auth, DNS, Cloudflare policy, deployment configuration, or custom copedents.

## Lane classification

- Primary lane: 05 Backend / RAG Integration
- Supporting lanes: 15 QA / Answer Eval, 01 Repo Steward, 12 Self-Hosted Deployment
- Task type: backend wording correction, deterministic fixtures, documentation, tests, and smoke
- Mode: user-approved Autopilot feature adjustment

## Files changed

- `steel_guitar_rag/melody_arranger.py`
  - changed melody-only transition instructions to say which abandoned strings to block before the move;
  - separated destination strings into reused strings to repick and new strings to add;
  - left full-grip sustain and semantic `voiceActions` unchanged.
- `tests/test_melody_arranger_decision_fixtures.py`
  - added two blocking fixtures and three lever-density cases covering E-lower and F-lever.
- `docs/llm-guidance/e9-arranger-decision-rules.md`
  - promoted the reviewed fixture boundaries into the implemented-rule section while retaining broader non-transition blocking and phrase-level lever limits as future work.
- `docs/handoffs/task-completions/2026-07-13-1214-05-blocking-lever-density-fixtures.md`
  - this handoff.

No files were deleted or generated in protected corpus, private-data, vector, source, deployment, or design paths.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_melody_arranger_decision_fixtures.py tests/test_melody_assistant.py tests/test_tab_engine.py`
  - **75 passed** after narrowing the lever-span fixture to prevent exit/re-entry chatter rather than forcing a lever through an equally correct final open resolution.
- `.venv/bin/python -m pytest -q tests/test_melody_arranger_decision_fixtures.py tests/test_melody_assistant.py tests/test_tab_engine.py tests/test_melody_import.py tests/test_api_search.py tests/test_melody_workbench_ui.py`
  - **383 passed**.
- `.venv/bin/python -m pytest -q`
  - **971 passed**.
- `.venv/bin/python -m py_compile steel_guitar_rag/melody_arranger.py tests/test_melody_arranger_decision_fixtures.py`
  - pass.
- `node --check ui/melody-workbench.js`
  - pass.
- `node --check ui/pedal-steel-fretboard.js`
  - pass.
- `git diff --check` on scoped files
  - pass.
- Local authenticated API smoke on port 8783
  - `1 2 3 5` returned a ready four-event exercise with single, mixed, thirds, and sixths routes;
  - tab validation passed and serialized output contained no `[object Object]`.
  - An initial POST using only the session query parameter correctly returned 401; the documented local development access header then authenticated the request and returned 200.

## Smoke Target

- Target type: local
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not applicable
- Cache-busted URL tested: not applicable
- Exact URL the user should use: protected-preview URL will be recorded after exact-path commit, restart, and authenticated browser smoke
- Auth required: yes
- Auth provider: local development scaffold
- Cloudflare Access login result: not attempted; this was local API smoke
- Local backend URL: `http://127.0.0.1:8783`
- Expected backend port: 8783
- Expected git HEAD: worktree based on `337b71972b7d71ceb443f158e2dbed5e920d8a45`
- Version endpoint: not used for the temporary local worktree server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: scoped worktree diff over the recorded HEAD
- Whether app root `/` works: not tested in API fallback
- Whether app root `/` is expected to work: yes in the protected preview
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in API fallback
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex will test protected preview after commit
- Do not test these URLs: prior cache keys
- Known caveats: API fallback is not browser smoke; the temporary local server was stopped after verification.

## Integration notes

- No schema or component contract changed. Existing `releasedStrings`, `repickedStrings`, and per-string `voiceActions` remain authoritative.
- The string-level action remains `release` in the transition contract; Melody Studio already presents that semantic action as blocking/releasing before a melody-only slide.
- The new tests deliberately do not impose a blanket lever quota. They protect two reviewed boundaries: no-benefit lever entries lose, while a lever required again on the next event remains held through the intermediate event.

## Risk assessment

- Risk: low.
- The runtime change affects only player-facing transition wording for melody-only changed-grip moves.
- Full-grip slides, scoring, selected paths, notes, tab validation, and public API fields are unchanged.
- Rollback is the normal revert of the scoped commit; there is no migration or data cleanup.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/melody_arranger.py`
- `tests/test_melody_arranger_decision_fixtures.py`
- `docs/llm-guidance/e9-arranger-decision-rules.md`
- `docs/handoffs/task-completions/2026-07-13-1214-05-blocking-lever-density-fixtures.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` during the implementation commit; it is a separate coordination artifact.
- All unrelated dirty corpus, source, pipeline, private-data, landing, deployment, design, brand, and interest-digest files.
- `corpus-private/`, `corpus-v2/`, vector/Chroma stores, embeddings, source-inbox raw/provenance data, `public/`, `ui/brand/`, `Neon Sign/`, auth policy, DNS, and secrets.

## Recommended next lane

`01 Repo Steward` exact-path commit, followed by `12 Self-Hosted Deployment` protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with the four exact paths above, then verify the cache-busted Melody Studio URL against the committed HEAD.
