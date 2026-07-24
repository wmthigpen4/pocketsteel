# SGF and Transcript-Informed Arranger Rules

## Task summary

Reviewed the user-named public SGF corpus and internal lesson-transcript review material for reusable E9 pedal, lever, harmony, slide, blocking, and position-choice guidance. Converted only independently corroborated, mechanically validated concepts into a canonical arranger decision contract.

Implemented the smallest high-confidence runtime slice:

- single-note and grip candidates now use the same canonical `E` and `F` lever IDs;
- an already established F-lever or E-lower posture is no longer abandoned merely because a following candidate uses the same lever posture;
- the existing C-pedal restriction remains unchanged;
- reviewed songbook arrangements remain unchanged by this slice.

Intentionally not changed: raw transcripts, cleaned transcript outputs, SGF corpus data, scraping, embeddings, Chroma stores, source cards, private-source routing, auth, deployment configuration, custom copedents, supported keys, UI layout, and unvalidated teaching-summary position claims.

## Lane classification

- Primary lane: 05 Backend / RAG Integration
- Supporting lanes: 02 Corpus Pipeline (read-only evidence review), 18 Product / Architecture (decision contract), 15 QA / Answer Eval
- Task type: mixed research, contract, backend, tests, and local API smoke
- Mode: approved Autopilot feature improvement

## Evidence review

The review used public SGF discussions about B+C usage, I–IV movement, E-raise mechanics, blocking, fretboard mapping, harmonized scales, and two/three-string grips. Internal lesson transcripts were used only to identify and corroborate generalized teaching concepts.

No private body text, metadata, media URLs, or lesson-specific wording was copied into runtime code, public guidance, tests, source cards, or this handoff. Cleaned transcript summaries were treated as research leads rather than positional authority because spot checks found imprecise mechanical descriptions.

Accepted concepts and their evidence gate are recorded in `docs/llm-guidance/e9-arranger-decision-rules.md`.

## Files changed

- `steel_guitar_rag/melody_arranger.py`
  - canonicalized generated single-note lever states to `E` and `F`;
  - added context-aware transition ranking that retains an established non-C lever posture;
  - preserved the existing strong C-pedal exception tier.
- `tests/test_melody_assistant.py`
  - added regression coverage for retaining an established A+F pocket;
  - added regression coverage proving single-note and grip candidates share canonical lever IDs.
- `docs/llm-guidance/e9-arranger-decision-rules.md`
  - added the evidence hierarchy, accepted rules, implemented rules, research-only rules, public SGF index, and privacy boundary.
- `docs/handoffs/task-completions/2026-07-13-0941-05-sgf-transcript-arranger-rules.md`
  - this completion handoff.

No files were deleted or generated in corpus, private-data, vector, or design paths.

## Tests and checks

- `.venv/bin/pytest -q tests/test_melody_assistant.py`
  - **36 passed**.
- `.venv/bin/python -m pytest -q tests/test_melody_assistant.py tests/test_melody_import.py tests/test_api_search.py`
  - **340 passed**.
- `.venv/bin/python -m pytest -q`
  - exit status **0**; full collection contains **958 tests**.
- `.venv/bin/python -m py_compile steel_guitar_rag/melody_arranger.py tests/test_melody_assistant.py`
  - pass.
- `git diff --check` on tracked scoped files
  - pass.
- `git diff --no-index --check /dev/null docs/llm-guidance/e9-arranger-decision-rules.md`
  - pass.
- Twelve-song catalog comparison against the pre-change ranking behavior
  - no reviewed songbook route changed.

One initial direct `.venv/bin/pytest` combined invocation failed during collection because that executable form did not place the repository root on the import path for `rag_common.py`. Re-running through `.venv/bin/python -m pytest`, the repository's supported invocation, passed.

## Smoke Target

- Target type: local
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not applicable; no browser claim is made
- Cache-busted URL tested: not applicable
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: yes for `/api/answer`
- Auth provider: local development header
- Cloudflare Access login result: not attempted; local smoke only
- Local backend URL: `http://127.0.0.1:8783`
- Expected backend port: 8783
- Expected git HEAD: worktree based on `604337cbf4ed2eac5b4e851eedd81159ba4d0e8e`
- Version endpoint: `http://127.0.0.1:8783/api/version`
- Version endpoint result: not used as commit evidence because the implementation was not committed yet
- If version endpoint missing, how version is inferred: current worktree plus recorded base HEAD
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: yes for the same-origin smoke server
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in this backend-only smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex after protected-preview update
- Do not test these URLs: port 8783 after closeout; the temporary server was stopped
- Known caveats: local API fallback proves the arranger contract, not protected-preview browser behavior

## Local API smoke result

- Authenticated `POST /api/answer`: **200**.
- Literal string 4, fret 6, F-lever B4 followed by another B4 returned `status=ready`.
- The faithful route retained canonical `F` for both events.
- Rendered tab showed `6F    6F` on string 4.
- Temporary local server was stopped after smoke.

## Integration notes

- Canonical controls are internal mechanical IDs. User-facing code may continue to render player-friendly names.
- The path selector still favors open/A/B at phrase start. This slice only removes a false complexity penalty when a validated F-lever or E-lower posture is already established.
- C remains exceptional, and the existing validated B+C minor-arrival case remains allowed.
- The evidence contract deliberately keeps blocking guidance, lever-density policy, added harmonic-scale pathways, and custom-copedent work out of runtime until focused fixtures exist.

## Risk assessment

Low. The runtime change is narrow, mechanically validated, and covered by focused and full tests. Reviewed catalog routes are unchanged. The main residual risk is that future arranger work could overgeneralize lesson-summary claims; the new evidence gate is intended to prevent that.

Rollback: revert the scoped implementation commit. No migration, persisted state, corpus output, or index change is involved.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/melody_arranger.py`
- `tests/test_melody_assistant.py`
- `docs/llm-guidance/e9-arranger-decision-rules.md`
- `docs/handoffs/task-completions/2026-07-13-0941-05-sgf-transcript-arranger-rules.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` in the implementation commit; refresh separately after commit/smoke.
- `docs/handoffs/task-completions/2026-07-13-0907-12-c-pedal-full-grip-slide-protected-smoke.md` and all prior parked handoffs.
- All unrelated dirty or untracked corpus, source, pipeline, private-data, design, brand, public, deployment, auth, and generated paths.
- `source-inbox/`, `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, `public/`, `ui/brand/`, and `Neon Sign/`.

## Recommended next lane

01 Repo Steward for exact-path staging and commit, followed by 12 Self-Hosted Deployment for protected-preview restart and authenticated verification.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the four exact files above, review the cached diff, commit the scoped evidence-contract and lever-state fix, then restart and smoke the protected preview.
