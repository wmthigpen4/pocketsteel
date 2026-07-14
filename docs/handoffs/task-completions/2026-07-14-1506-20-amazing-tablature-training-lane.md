# Lane 20 — Amazing Tablature Training

## Task summary

Implemented the approved dedicated `20 Amazing Tablature Training` lane and its headless, private, repeatable workflow. Added immutable source-batch intake, resumable checkpoints, stable-ID mechanical validation, separate review corrections, deterministic weighted challenger training, held-out champion comparison, privacy gates, exact-model beta/stable promotion, rejection, and rollback. Added descriptive player-facing style metadata and a Melody Studio Arrangement/Playing style selector; no frontend model trainer or admin training API was added.

Registered the supplied 51-photo collection as private batch `atb-20260714-photos-1-001` with confirmed source profile `source-e9-abc-defg-v1`. Intake digest is `6ff7941cdce2bdad4542262cd0002f234cadb99e7139c6c8cef14fe20dcc589c`. The honest checkpoint is `ingest: completed`, `annotate: pending`; no source decisions or model were fabricated.

Created and pinned the persistent Codex task `20 Amazing Tablature Training` with task ID `019f623a-d191-7031-8dce-ac70a2f1046d`.

Intentionally unchanged: scraping, embeddings, Chroma, RAG ingestion, authentication, billing, DNS, Tunnel, deployment policy, public corpus, and source-card behavior.

## Files changed

- Lane contract and workflow documentation: `AGENTS.md`, `docs/amazing-tablature-training.md`, `docs/chatgpt-project-context/03_Lane_Map.md`, `docs/codex-workflow.md`, `docs/llm-guidance/melody-copedent-transfer-rules.md`.
- Headless workflow: `pocketsteel/amazing_tablature_training.py`, `scripts/amazing_tablature.py`.
- Ranker/style/runtime metadata: `pocketsteel/melody_ranker.py`, `pocketsteel/melody_decision_rules.py`, `pocketsteel/melody_arranger.py`, `pocketsteel/melody_assistant.py`.
- Player-facing style selector and normalization: `ui/answer-client.js`, `ui/melody-workbench.html`, `ui/melody-workbench.js`.
- Regression tests: `tests/test_amazing_tablature_training.py`, `tests/test_melody_workbench_ui.py`, `tests/test_frontend_answer_ui.py`.
- This handoff.
- Ignored private state: updated Lane 20 README/schema and created the first batch manifest, registry, state, and annotation work queue under `corpus-private/melody-decisions/`. These files must remain uncommitted.
- Deleted files: none.

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- `.venv/bin/ruff check pocketsteel/amazing_tablature_training.py pocketsteel/melody_ranker.py pocketsteel/melody_decision_rules.py pocketsteel/melody_arranger.py pocketsteel/melody_assistant.py scripts/amazing_tablature.py tests/test_amazing_tablature_training.py tests/test_melody_workbench_ui.py` — passed.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py tests/test_copedent_transfer.py tests/test_melody_workbench_ui.py tests/test_frontend_answer_ui.py` — 57 passed.
- `npm run check:js` — passed.
- `.venv/bin/python -m pytest -q` — 1,118 passed.
- `git diff --check` — passed.
- Real private intake and status commands — passed with 51 inputs and zero source-content output.
- Protected-preview browser smoke — pending exact commit and preview update; Lane 12 owns that follow-up.

## Integration notes

- The canonical operator is `.venv/bin/python scripts/amazing_tablature.py`; the original one-shot trainer remains compatibility-only.
- Raw annotations are immutable. `review-resolutions.jsonl` records accept/exclude/correct decisions separately.
- Source controls must use stable IDs. Validation checks source string/fret/pitch/control effects, sounding/sustained strings, mechanically valid alternatives, and melody as the highest voice.
- High-confidence machine-validated expert decisions may train beta; low-confidence records block; a deterministic ten-percent audit sample is non-blocking. Consented player feedback has `0.25` evidence weight versus `1.0` expert evidence.
- `amazing_grace` is a required holdout benchmark for the initial challenger gate.
- Both beta and stable promotions require an exact model ID and creator approval reference. Stable additionally requires an existing Lane 15 handoff.
- Runtime responses now identify the descriptive style, explanation, model version, and `seed` status. No learned model is active because no challenger has been trained or approved.
- Lane 05 must consume only a sanitized promotion artifact after approval; Lane 20 private records never enter runtime or Git.

## Risk assessment

Medium. This adds a new private training state machine and a visible Melody Studio style selector. Mechanical correctness remains deterministic, the full suite is green, learned weights are not active, promotion is gated, and the previous runtime behavior remains the `seed` policy. Rollback for the code change is the scoped commit; model rollback is an exact registry operation.

## Human decision needed

No for implementation/commit/preview smoke. The next future decision is exception review after the first private annotation pass. No model promotion decision exists yet.

## Safe-to-stage exact file list

- `AGENTS.md`
- `docs/amazing-tablature-training.md`
- `docs/chatgpt-project-context/03_Lane_Map.md`
- `docs/codex-workflow.md`
- `docs/llm-guidance/melody-copedent-transfer-rules.md`
- `docs/handoffs/task-completions/2026-07-14-1506-20-amazing-tablature-training-lane.md`
- `pocketsteel/amazing_tablature_training.py`
- `pocketsteel/melody_ranker.py`
- `pocketsteel/melody_decision_rules.py`
- `pocketsteel/melody_arranger.py`
- `pocketsteel/melody_assistant.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_frontend_answer_ui.py`
- `ui/answer-client.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`

## Files that must not be staged

- Everything under `corpus-private/`, including the real 51-photo batch state.
- The supplied files under `~/Downloads/Photos-1-001`.
- All unrelated dirty and untracked files already present in the worktree, especially source-inbox, corpus, Chroma/vector, private lesson, brand/design, deployment, historical handoff, and integration-status work.

## Recommended next lane

Lane 01 exact-path commit for the listed files, then Lane 12 protected-preview update and browser smoke. After that, continue the first annotation pass in the pinned Lane 20 Codex task.

## Commit readiness

Safe to commit.

## Suggested next step

`Lane 01: Proceed under Autopilot/Repo Steward auto-approval. Stage only the exact files listed in this handoff, commit the Lane 20 foundation, then hand the exact commit to Lane 12 for protected-preview smoke.`
