# Copedent-transferable tablature decision engine

## Task summary

Implemented the approved source-copedent to abstract-decision to target-copedent pipeline for Melody Studio.

- Added the photographed `source-e9-abc-defg-v1` chart as an explicit source-only E9 profile without changing the app default or any saved user profile.
- Added effect-based control transfer, target-profile candidate generation, mechanical validation, target labels, exact pitch/register preservation, melody-on-top validation, and triad-to-dyad-to-single fallback.
- Added versioned musical rule contracts, style-family policies, copedent-neutral ranking features, and a private JSONL trainer.
- Made Melody Studio pass the saved E9 profile into the arranger and keep target pitches synchronized across score, tablature, fretboard, and playback.
- Added a private ignored annotation scaffold under `corpus-private/melody-decisions/`; it was intentionally not staged or exposed through RAG, Chroma, source cards, or public fixtures.
- Browser smoke found and fixed a response-normalization gap that initially hid the visible target-profile label and discarded target mechanical fields.

The 51 photographed passages have not been asserted as transcribed training decisions. Their private review/annotation is the next data task; this implementation supplies the source profile, schema, deterministic realization engine, curated seed rules, and training path without fabricating annotations.

## Lane classification

- Primary lane: `05 Backend / RAG Integration`
- Supporting lanes: `06 UX/UI Design`, `15 QA / Answer Eval`, `18 Product / Architecture`
- Task mode: approved YELLOW feature scope running under the Autopilot feature loop

## Files changed

### Runtime and UI

- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/copedent_transfer.py`
- `steel_guitar_rag/e9_copedents.py`
- `steel_guitar_rag/melody_arranger.py`
- `steel_guitar_rag/melody_assistant.py`
- `steel_guitar_rag/melody_decision_rules.py`
- `steel_guitar_rag/melody_models.py`
- `steel_guitar_rag/melody_ranker.py`
- `steel_guitar_rag/tab_engine.py`
- `ui/answer-client.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`

### Training, contract, and tests

- `scripts/train_melody_decision_ranker.py`
- `docs/llm-guidance/melody-copedent-transfer-rules.md`
- `tests/test_api_search.py`
- `tests/test_copedent_transfer.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`

### Ignored private artifacts created but not staged

- `corpus-private/melody-decisions/README.md`
- `corpus-private/melody-decisions/annotation-schema.json`
- `corpus-private/melody-decisions/source-e9-abc-defg-v1/profile.json`

No files were deleted. No embeddings, vector stores, public corpus material, auth policy, deployment policy, or saved user profile were changed.

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- Focused Python/Node UI, transfer, tab, and API suites — passed during implementation.
- `.venv/bin/ruff check` over all changed Python modules, script, and focused tests — passed.
- `.venv/bin/python -m pytest -q` — passed: `1071 passed in 53.65s`.
- `git diff --check` — passed.
- `git check-ignore -v` for all private annotation scaffold files — passed; all resolve to the `corpus-private/` ignore rule.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8872/ui/melody-workbench.html?v=copedent-transfer-local-20260713-2&copedent=day-e9-basic&access=beta_user`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL to be recorded after the committed preview restart
- Auth required: yes, local development role header
- Auth provider: scaffold
- Cloudflare Access login result: not required for local smoke
- Local backend URL: `http://127.0.0.1:8872`
- Expected backend port: `8872`
- Expected git HEAD: `e8df888465d8cea3913acffe9bdaf00a8f693624` plus the scoped working-tree feature diff
- Version endpoint: `http://127.0.0.1:8872/api/version`
- Version endpoint result: not separately queried; version was inferred from `git rev-parse HEAD` and the working-tree diff under test
- If version endpoint missing, how version is inferred: current HEAD plus exact scoped working-tree changes
- Whether app root `/` works: not separately browser-tested in this local run
- Whether app root `/` is expected to work: yes; the same-origin server contract redirects it to the home UI
- Whether `/ui/steel-guitar-rag-mock.html` works: not separately browser-tested in this local run
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale local URLs ending in `copedent-transfer-local-20260713` or `-1`
- Known caveats: this smoke explicitly selected the app-supported Day target profile. Saved custom-profile transport and display are covered by UI normalization, API, and transfer regression tests without overwriting the browser's existing saved profile.

## Smoke result

- PASS: `1 2 3 5` arranged into four synchronized events under the Day profile.
- PASS: the result visibly stated `Arranged for Day E9`.
- PASS: Recommended arrangement, score, tablature, and fretboard rendered.
- PASS: target-copedent fields survived answer-client normalization.
- PASS: browser warning/error log was empty.
- PASS: the temporary local service was stopped after smoke.
- This was actual browser smoke, not API fallback.

## Integration notes

- Source and target identities are distinct at the exercise, route, and event layers.
- Source controls are stored and transferred by their affected string, source/destination pitch, and semitone effect. Matching labels alone do not establish equivalence.
- Extra changes are accepted only outside the sounding/sustained protected-string set.
- Custom saved profiles are validated as ten-string E9 profiles and receive a `saved:` runtime identity; user-facing labels remain separate from normalized mechanical IDs.
- Ranking weights use only abstract musical features. Profile pitch/capability resolution remains deterministic.
- The source-only profile resolves explicitly but is intentionally absent from the normal selectable app profiles.
- No API schema migration or dependency change was introduced.

## Risk assessment

- Risk: medium feature risk, low privacy/deployment-policy risk.
- The mechanical layer is fully regression-tested, but player-quality ranking will improve only after reviewed decisions are annotated and held-out blind review is run.
- The photographed chart is assumed to govern the collection unless a source page overrides it.
- Rollback: revert the scoped feature commit; saved copedent data is untouched.

## Human decision needed

No for implementation, exact-path commit, or normal protected-preview verification. A later human review is needed to approve photographed passage annotations and blind-ranking results before claiming trained great-player preferences.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-13-2315-05-copedent-transferable-tablature.md`
- `docs/llm-guidance/melody-copedent-transfer-rules.md`
- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/copedent_transfer.py`
- `steel_guitar_rag/e9_copedents.py`
- `steel_guitar_rag/melody_arranger.py`
- `steel_guitar_rag/melody_assistant.py`
- `steel_guitar_rag/melody_decision_rules.py`
- `steel_guitar_rag/melody_models.py`
- `steel_guitar_rag/melody_ranker.py`
- `steel_guitar_rag/tab_engine.py`
- `scripts/train_melody_decision_ranker.py`
- `tests/test_api_search.py`
- `tests/test_copedent_transfer.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `ui/answer-client.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`

## Files that must not be staged

- Everything under `corpus-private/melody-decisions/`.
- `docs/handoffs/task-completions/integration-status.md` in the feature commit.
- All unrelated dirty/untracked corpus, source-inbox, public, brand, deployment, auth, vector, and historical handoff files.

## Recommended next lane

`01 Repo Steward` exact-path commit, followed by `12 Self-Hosted Deployment` protected-preview restart and authenticated smoke if the committed runtime scope remains isolated.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval, stage only the exact list above, commit the green slice, restart the protected preview through the documented user-owned listener path, and run authenticated Melody Studio smoke at the exact cache-busted URL.
