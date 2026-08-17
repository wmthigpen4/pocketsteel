# Howdy default playback speed

## Task summary

Changed the taught-solo player default from 50% to 100%. The 50% and 75% controls remain available when a learner chooses to slow the lesson down.

## Files changed

- `partner_companions/travis_howdy/site/companion.js`
- `tests/test_travis_companion.py`
- This handoff

## Verification

- Travis companion tests pass.
- JavaScript syntax and `git diff --check` pass.
- Browser QA must confirm the 100% button is selected and the audio element uses playback rate `1` on initial load.

## Safe-to-stage list

- `partner_companions/travis_howdy/site/companion.js`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-17-0943-00-howdy-default-speed.md`

## Must-not-stage list

- `docs/handoffs/task-completions/integration-status.md`
- Existing unrelated untracked handoffs
- `output/`
- `tmp/`
- `~/.steel-rag/`

## Commit readiness

Safe to commit after browser QA.
