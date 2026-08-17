# Howdy viewer MP3 download

## Task summary

Replaced the instructor-facing MP3 upload controls beneath the simulated lesson video with the learner-facing Howdy backing-track download. The card identifies the existing full-song recording, its 3:57 duration, and key D. It provides a direct same-origin MP3 download and does not render an empty additional-track placeholder.

## Files changed

- `partner_companions/travis_howdy/templates/embed.html`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/README.md`
- `tests/test_travis_companion.py`
- This handoff

## Verification

- `77 passed` across the companion and shared practice-tool suites.
- JavaScript syntax check, Ruff, and `git diff --check` passed.
- Release packaging and the isolation verifier passed for the 18-file static bundle.
- The packaged MP3 returned `200 audio/mpeg` and 5,693,902 bytes.
- In-app browser verification confirmed the learner download is visible and enabled, its URL targets the packaged backing track, its filename is `Howdy - Full Song Play Along.mp3`, and the page contains no file input, instructor setup copy, or additional-MP3 placeholder.

## Smoke Target

- Local route: `http://127.0.0.1:8897/practice-guide/howdy/`
- Authentication: none
- Expected behavior: one learner-facing full-song MP3 download immediately below the lesson video
- General app routes: unavailable in this isolated static bundle
- Caveat: local owner-review preview only; no deployment, DNS, Access, or Teachable changes

## Risks

- The download filename and displayed duration/key are Howdy-specific authored presentation data.
- Future lessons with multiple real tracks need a data-driven list, but should render only tracks that actually exist.

## Human decision needed

None for the Howdy local preview.

## Safe-to-stage list

- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/embed.html`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-17-0846-05-howdy-viewer-mp3-download.md`

## Must-not-stage list

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user edit)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `~/.steel-rag/`

## Recommended next lane

Generalize the same learner track-list presentation for future lessons with multiple approved MP3s, rendering no empty slots.

## Commit readiness

Safe to commit.
