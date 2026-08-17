# Howdy song-level heading

## Task summary

Changed the companion heading from `Practice the “Howdy” solo` to `Practice “Howdy”` so the page title encompasses both the taught-solo and full-song practice choices.

## Files changed

- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/site/companion.js`
- `tests/test_travis_companion.py`
- This handoff

## Verification

- `77 passed` across the companion and shared practice-tool suites.
- JavaScript syntax and `git diff --check` passed.
- Static bundle isolation verifier passed for companion revision `.8`.
- In-app browser confirmed the new heading and absence of the solo-only heading.

## Smoke Target

- Local route: `http://127.0.0.1:8897/practice-guide/howdy/`
- Authentication: none
- Expected heading: `Practice “Howdy”`
- Caveat: local preview only

## Risks

None beyond editorial preference.

## Human decision needed

None.

## Safe-to-stage list

- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/site/companion.js`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-17-0923-13-howdy-song-level-heading.md`

## Must-not-stage list

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user edit)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `~/.steel-rag/`

## Recommended next lane

Use song-level headings whenever a companion offers both lesson-excerpt and complete-song practice.

## Commit readiness

Safe to commit.
