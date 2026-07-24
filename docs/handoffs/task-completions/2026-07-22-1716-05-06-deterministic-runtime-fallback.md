# Lanes 05/06 — Deterministic Amazing Tablature runtime fallback

## Task summary

Retired the superseded 51-image model from Melody Studio's live ranking path.
Until an exact current challenger passes the fixed held-out gates and receives
explicit promotion approval, the public runtime policy is
`deterministic-fallback-v1` and contributes zero learned penalty.

The existing deterministic pitch, harmony, phrase-role, mechanics, style, tab,
and fretboard behavior remains active. Runtime metadata now states that the
ranker is disabled, accuracy applies to normalized score events, and score-image
recognition is separate and review-required. Missing style weights fail safely
instead of raising.

## Files changed

- `steel_guitar_rag/amazing_tablature_model.py`
- `steel_guitar_rag/melody_arranger.py`
- `tests/test_melody_arranger_decision_fixtures.py`
- `tests/test_copedent_transfer.py`
- `tests/test_amazing_tablature_training.py`
- `docs/llm-guidance/melody-copedent-transfer-rules.md`
- This handoff.

No private source, model artifact, validation record, sealed-test artifact,
embedding, auth setting, deployment setting, or frontend layout was changed.

## Tests and checks

- Focused melody, copedent, training, import, and parity tests — PASS, 104 tests.
- API contract/search and frontend/workbench tests — PASS, 393 tests.
- `node --check ui/answer-client.js` — PASS.
- `node --check ui/melody-workbench.js` — PASS.
- `git diff --check` for the scoped files — PASS.

## Integration notes

The trained challenger uses the v3 21-feature phrase-sequence schema, while the
runtime adapter previously supplied only the legacy basic candidate fields.
Therefore copying challenger weights directly would not reproduce training
behavior. This fallback is the safe release state until an exact v3 runtime
adapter and held-out promotion are complete.

Because the Amazing Tablature runtime policy is included in rules-code hashing,
the selected discovery challenger must be rebuilt after this commit before any
validation freeze.

## Risk assessment

Low. This removes an ineligible learned influence and preserves the tested
deterministic arranger. Rollback would reactivate a model whose source batch the
user explicitly superseded and is not recommended.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_model.py`
- `steel_guitar_rag/melody_arranger.py`
- `tests/test_melody_arranger_decision_fixtures.py`
- `tests/test_copedent_transfer.py`
- `tests/test_amazing_tablature_training.py`
- `docs/llm-guidance/melody-copedent-transfer-rules.md`
- `docs/handoffs/task-completions/2026-07-22-1716-05-06-deterministic-runtime-fallback.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- Historical untracked handoffs and unrelated deployment/UI work.

## Recommended next lane

Lane 01 exact-path commit, then Lane 20 rebuild the selected discovery
configuration from the new clean HEAD.

## Commit readiness

Safe to commit

## Suggested next step

Commit this exact fallback slice, rebuild the selected averaged challenger from
clean HEAD, verify lineage/no-rereview accounting, and keep the sealed test
closed.
