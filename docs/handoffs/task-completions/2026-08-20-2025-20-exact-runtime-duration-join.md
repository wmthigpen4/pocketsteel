# Exact runtime/prediction duration join

## Task summary

The Play Along runtime reports the target Chrome `AudioBuffer` duration at the
player's integer-millisecond timebase, while the frozen multiband feature cache
retains a full-precision duration. The prediction-only bar summarizer now
accepts those two values only when:

```text
runtimeDurationSeconds == floor(predictionDurationSeconds * 1000 + 0.5) / 1000
```

There is no tolerance-based match and neither duration is overwritten. The
runtime duration, prediction duration, and whether the relation was exact or
player-canonical-millisecond are all disclosed in the sealed bar summary. Bar
features and the final bar end use the full-precision prediction duration; the
runtime timing SHA-256 continues to bind the original player value.

The rule is part of `BAR_FEATURE_CONTRACT_SHA256`. The development label join
independently proves the same relation before scoring and binds its final-bar
policy into the bar outcome/eligibility contract.

## Files changed

- `steel_guitar_rag/chord_reader/bar_uncertainty.py`
- `tests/test_chord_reader_bar_uncertainty.py`
- this handoff

The separately reviewed example builder and selector consume the changed
feature-contract hash dynamically and test exact contract agreement.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_bar_uncertainty.py`
  - `22 passed`
- `.venv/bin/python -m pytest -q tests/test_chord_reader_bar_examples.py tests/test_chord_reader_bar_selector.py`
  - `82 passed`
- Integrated runtime/examples/selector/uncertainty suite with live Chrome tests
  deselected:
  - `178 passed, 2 deselected`
- Ruff, Ruff format check, `py_compile`, and `git diff --check` passed.

## Risks and human decision

This exact rule still does not prove that a prediction and timing artifact came
from the same audio bytes. The required development audio-lineage attestation
must bind both sides before the real 246-track join. No human decision is
needed for this additive development-only contract.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/bar_uncertainty.py`
- `tests/test_chord_reader_bar_uncertainty.py`
- `docs/handoffs/task-completions/2026-08-20-2025-20-exact-runtime-duration-join.md`

Do not stage generated predictions, timing grids, summaries, selectors, audio,
references, feature caches, or sealed calibration/test artifacts.

## Recommended next lane and commit readiness

Lane 01 may commit this with the reviewed development example-builder and
grouped-selector contracts. Then the model-development lane should require the
audio-lineage artifact before running the full development join. Ready for
exact-path staging.
