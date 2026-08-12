# 2026-08-12 17:50 Lane 06 Chord Voicing Policy

## Task Summary

Implemented a transposable, per-quality voicing policy for the E9 Chord / Voicing Finder. Results are now classified as **Complete voicing**, **Practical voicing**, **Rootless ensemble voicing**, or **Ambiguous fragment** according to the chord tones that actually define each quality.

The policy explains what is dropped and when every selected string should be played. For 7th, 9th, and 6th qualities, the fifth is normally the first safe omission. Rootless results are reserved for ensemble/context use. A true 9th must retain both its seventh and ninth; `add9` is modeled separately. String count is reported separately from unique chord roles so doubled tones do not imply greater harmonic completeness.

Extended E9 vocabulary now includes three-, four-, and five-string 9th grips. At fret 7 with A+B, Amaj9 can be shown as a rootless 3rd-7th-9th shell (`4-5-7`), a practical root-3rd-7th-9th voicing (`4-5-7-9`), or the complete five-tone grip (`4-5-6-7-9`).

## Files Changed

- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-config.js`
- `ui/e9-fretboard-explorer-loader.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_e9_explorer_controls_ui.py`
- `docs/handoffs/task-completions/2026-08-12-1750-06-chord-voicing-policy.md`

No files were deleted. Backend pitch generation, corpus, embeddings, auth, DNS, and deployment were not changed.

## Tests And Checks

Passed:

- `node --check ui/e9-music-rules.js`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-config.js`
- `node --check ui/e9-fretboard-explorer-loader.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_e9_explorer_controls_ui.py -q`
  - `52 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_fretboard_explorer.py -q`
  - `83 passed`
- `.venv/bin/python -m pytest tests/test_e9_explorer_controls_ui.py::test_e9_fretboard_explorer_controls_are_mode_aware -q`
  - `1 passed` after strengthening the exact Amaj9 five-string card assertion
- `git diff --check`

Regression coverage includes complete, safe-fifth-omission, rootless, and ambiguous major-7 cases; true dominant-9 seventh requirements; add9 parsing; diminished-7 completeness; 6th-quality parsing; string/unique-role counts; learner-facing explanations; and the Amaj9 fret-7 A+B grip family.

## Smoke Result

Result type: executable rendered-DOM smoke. The focused UI harness rendered the Chord Finder controls, cards, detail panel, filters, and fretboard marker inputs. It verified the exact complete Amaj9 card ID for strings `4-5-6-7-9` at fret 7 with A+B, plus practical and rootless alternatives.

No protected-preview restart or deployment was performed. This branch contains unrelated commits ahead of its base, so deploying it would broaden the requested change.

## Integration Notes

- Chord completeness is based on distinct pitch roles, not raw string count.
- `dominant9`, `major9`, and `minor9` require the seventh and ninth to avoid being mislabeled as add9.
- The fifth is a safe omission only for qualities whose policy explicitly permits it.
- Root omission is described as ensemble/context dependent rather than generally interchangeable with a complete chord.
- Major-7 upper-structure triads without the root are classified as ambiguous instead of automatically promoted to rootless ensemble voicings.
- Chord Finder grip discovery now accepts registered groups of up to five strings.

## Risk Assessment

Risk: medium-low. The main behavior is deterministic and covered at both theory and rendered-UI levels. Remaining risk is protected-preview asset propagation because authenticated browser smoke was intentionally not run from this ahead-of-base branch.

Rollback: revert the scoped policy, grip registry, UI labels/details, cache-busters, and tests listed above.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-config.js`
- `ui/e9-fretboard-explorer-loader.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_e9_explorer_controls_ui.py`
- `docs/handoffs/task-completions/2026-08-12-1750-06-chord-voicing-policy.md`

## Files That Must Not Be Staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- All unrelated dirty, generated, private, corpus, Chroma, deployment, and auth files.

## Recommended Next Lane

Lane 12 protected-preview restart and authenticated browser smoke after the scoped commits are integrated onto the deployment branch.

## Commit Readiness

Safe to commit.
