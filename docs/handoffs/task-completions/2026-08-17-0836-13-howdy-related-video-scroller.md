# Howdy related-video scroller

## Task summary

Expanded the static Howdy related-lesson recommendations from three cards to four and presented them in a horizontal video scroller. The previously omitted `How Intervals Make Chords` recommendation is now included with a Howdy-specific explanation. The scroller has explicit previous/next controls plus native horizontal swipe and trackpad behavior. Recommendations are rendered once and remain unchanged during playback.

## Files changed

- `partner_companions/travis_howdy/content/related-lessons.json`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/site/companion.css`
- `tests/test_travis_companion.py`
- This handoff

## Verification

- `77 passed` across practice analysis, reference validation, Travis companion, practice guide, concept graph, play-songs UI, and practice tools suites.
- `node --check partner_companions/travis_howdy/site/companion.js`
- Ruff passed for the touched Python files.
- `git diff --check` passed.
- Release packaging and allowlist verifier passed for an 18-file, same-origin-only bundle.
- In-app browser smoke test confirmed all four video recommendations render, the next/previous buttons move the horizontal viewport, and recommendation content stays identical while the backing track plays.

## Smoke Target

- Local route: `http://127.0.0.1:8897/practice-guide/howdy/`
- Authentication: none
- Expected build: the feature commit created from this handoff
- Expected behavior: four static related-video cards in a horizontal scroller, with arrows and native swipe/trackpad scrolling
- General app routes: unavailable in this isolated static bundle
- Caveat: local owner-review preview only; no deployment, DNS, Access, or Teachable changes

## Risks

- Related-video thumbnails and timestamps remain dependent on the approved private source package used at bundle time.
- A narrow viewport intentionally shows part of the next card as a scroll affordance.
- Editorial relevance is source-grounded and Howdy-specific, but remains an owner-review decision before partner publication.

## Human decision needed

None for the local implementation. Cory can still revise the recommendation order or wording during owner review.

## Safe-to-stage list

- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/content/related-lessons.json`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-17-0836-13-howdy-related-video-scroller.md`

## Must-not-stage list

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user edit)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `~/.steel-rag/`

## Recommended next lane

Owner-review the four recommendations in the live local preview, then apply the same 1-to-6-card static scroller contract to other lesson companions as their source-grounded related-video sets are approved.

## Commit readiness

Safe to commit.
