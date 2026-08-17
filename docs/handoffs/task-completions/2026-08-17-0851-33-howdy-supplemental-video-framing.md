# Howdy supplemental-video framing

## Task summary

Reframed the related Travis videos as just-in-time supplemental help for the current Howdy lesson. Replaced the after-lesson language with `Help with this lesson` and explicitly tells learners to use a video when a technique or concept in Howdy needs more explanation.

## Files changed

- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/site/companion.js`
- `tests/test_travis_companion.py`
- This handoff

## Verification

- `77 passed` across the companion and shared practice-tool suites.
- JavaScript syntax and `git diff --check` passed.
- Static bundle isolation verifier passed.
- In-app browser confirmed the new current-lesson framing and absence of `Go deeper after this lesson`.

## Smoke Target

- Local route: `http://127.0.0.1:8897/practice-guide/howdy/`
- Authentication: none
- Expected behavior: supplemental video section is framed as help within Howdy, not post-lesson progression
- Caveat: local preview only

## Risks

None beyond normal editorial review.

## Human decision needed

None.

## Safe-to-stage list

- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/site/companion.js`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-17-0851-33-howdy-supplemental-video-framing.md`

## Must-not-stage list

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user edit)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `~/.steel-rag/`

## Recommended next lane

Use the same current-lesson framing for supplemental videos in every companion.

## Commit readiness

Safe to commit.
