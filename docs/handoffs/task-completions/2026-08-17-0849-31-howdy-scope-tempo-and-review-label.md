# Howdy scope tempo and review label

## Task summary

Corrected the lesson-detail tempo pill so it follows the learner's selected audio scope: `Taught solo · 79.8 BPM` for the solo and `Full song · 158 BPM` for the complete play along. Removed the internal `Owner review` pill and all remaining learner-visible owner-review wording. The neutral preview marker still carries the companion revision and build SHA.

## Files changed

- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/site/companion.css`
- `tests/test_travis_companion.py`
- This handoff

## Verification

- `77 passed` across the companion and shared practice-tool suites.
- JavaScript syntax, Ruff, and `git diff --check` passed.
- Static bundle packaging and isolation verification passed.
- In-app browser confirmed the initial facts read `Key D / 4/4 / Taught solo · 79.8 BPM`, then changed to `Key D / 4/4 / Full song · 158 BPM` after selecting Full song.
- In-app browser confirmed `Owner review` is absent and the version marker reads `Preview · revision · SHA`.

## Smoke Target

- Local route: `http://127.0.0.1:8897/practice-guide/howdy/`
- Authentication: none
- Expected behavior: scope-aware tempo pill and no owner-review pill
- Caveat: local owner-review preview only; no deployment or Teachable changes

## Risks

- Both tempo values remain authored lesson data; future companions must supply their own solo and full-song tempo metadata.

## Human decision needed

None for the local Howdy presentation.

## Safe-to-stage list

- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-17-0849-31-howdy-scope-tempo-and-review-label.md`

## Must-not-stage list

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user edit)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `~/.steel-rag/`

## Recommended next lane

Apply the scope-aware tempo-label contract to future song companions that provide both a complete recording and a taught excerpt.

## Commit readiness

Safe to commit.
