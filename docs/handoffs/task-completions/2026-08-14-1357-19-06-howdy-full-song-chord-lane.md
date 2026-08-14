# Howdy full-song chord lane correction

## Outcome

Corrected the Howdy companion's Full Song presentation so it no longer reuses
the taught solo's eight-bar chord form. Full Song now has a dedicated,
horizontally scrolling chord/NNS lane synchronized to the complete 3:57
backing track. The solo form remains available only in Map and Solo.

The private owner-review artifact does not yet contain an authored full-song
chart. Rather than publish inferred harmony, the UI places the current
lesson-solo chord events at their absolute position in the recording and marks
all other spans `Chart pending` / `No guessed chord`.

## Implementation

- Added distinct full-song timeline markup and responsive styling.
- Added deterministic segment construction, seek actions, current chord/NNS
  state, and transport-following horizontal scroll.
- Added optional `songChordTimeline` support. When present, packaging and the
  browser require it to be contiguous, labeled, and complete for the full
  recording.
- Preserved the same canonical companion data and same-origin static runtime;
  no audio analyzer, arranger, model call, or network service was added.

## Verification

- `node --check partner_companions/travis_howdy/site/companion.js` — passed.
- `.venv/bin/pytest -q tests/test_travis_companion.py` — 24 passed.
- `git diff --check` — passed.
- Draft packaging and bundle verification — passed; 13-file allowlist,
  same-origin policy, and blocked-route inventory intact.
- In-app browser:
  - Full Song displayed `Full-song chord lane · Key D` and did not display the
    eight-bar solo form.
  - At 0:00 the current state was `Chart pending`.
  - Selecting the source-timed event at 1:58 sought to `G / IV`.
  - Playback advanced to `A` at 1:59 while the lane scroll position advanced.
  - Solo restored the eight-bar chart and hid the full-song lane.

## Deployment status

Local owner preview only. Nothing was deployed, gated, or changed in
Cloudflare, and Travis was not added.
