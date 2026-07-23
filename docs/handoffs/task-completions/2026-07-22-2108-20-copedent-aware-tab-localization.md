# Lane 20 — Copedent-aware tab localization and sustain-state comparison

## Task summary

Followed the first `validation-machine-recapture-v2` dry run to its machine-readable failures. The replay exposed that the full-line tab prompt had hard-coded the main packet's control-to-string mapping even when reading the licks batch's separately pinned copedent. It also assumed every printed tab state must correspond to a new score attack, which is false for pedal/lever changes during sustain.

Completed:

- Tab localization now receives a prompt-safe control-to-string map derived from the exact source copedent profile for the current batch.
- Removed the hard-coded main-packet lever map from the general localizer prompt.
- Bumped tab-system localization to `tab-system-event-localization-v5`.
- Validation score/tab containment now compares all tab states when their count matches written changes, or picked tab states when extra tab states are explicitly marked `movement_only`.
- Independent OMR completeness accepts only counts that match one of those two complete machine timelines; mismatches remain withheld.
- Added diagnostics identifying the comparison basis and tests for the licks D/E lever mapping and sustain-movement case.

Intentionally not changed:

- No validation result was applied.
- No human validation ground truth was opened or used.
- No sealed-test data was opened.
- No model was promoted or wired into production.
- No source image, corpus, embedding, vector, auth, deployment, or public runtime file was changed.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2108-20-copedent-aware-tab-localization.md`

Private dry-run reports remain ignored beneath `corpus-private/melody-decisions/`.

## Tests and checks

- `.venv/bin/python -m py_compile pocketsteel/amazing_tablature_extraction.py tests/test_amazing_tablature_extraction.py` — pass.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py -x` — **157 passed**.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_input_parity.py tests/test_amazing_tablature_score_sequence.py tests/test_amazing_tablature_sealed_test.py tests/test_amazing_tablature_training.py` — **203 passed**.
- `git diff --check` — pass.

## Integration notes

- Main packet control checks include D on string 2 and E on strings 4/8; the licks source profile instead pins D to strings 4/8 and E to strings 2/9. The localizer now receives the correct map per batch.
- Copedent constraints provide only mechanical row checksums. They do not provide fret, event, or pitch answers.
- A validation line with score count equal to all tab states is compared state-for-state. A line with explicit sustain movements may compare the score to picked tab states. Any other count relationship remains blocked.
- The exact challenger must be rebuilt after this commit before the next validation replay so model and validator code lineage remain identical.

## Risk assessment

Medium. This corrects a cross-batch prompt contamination bug and broadens comparison only for explicitly classified sustain movements. Incorrect or uncertain movement classification still fails downstream mechanical/pitch gates and is not auto-applied.

Rollback: revert this scoped commit and regenerate ignored validation artifacts.

## Human decision needed

No. Continue the approved machine-only validation repair loop. Do not publish incomplete audit lines.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2108-20-copedent-aware-tab-localization.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked handoffs
- `corpus-private/**`
- Raw images, extraction artifacts, model files, validation results, or sealed-test artifacts

## Recommended next lane

Lane 20 Amazing Tablature Training: exact-path commit, rebuild the challenger from the new HEAD, replay licks validation, and rerun unpublished machine remediation.

## Commit readiness

Safe to commit

## Suggested next step

Commit these exact three paths, rebuild the exact challenger, and rerun the five withheld licks validation lines. Apply only lines that pass complete independent score, complete copedent-correct tab, and explicit comparison gates.
