# Howdy detected full-song chord chart

## Outcome

Populated the deterministic Howdy Full Song lane with the repository's existing
local Play Along chord reader. The learner runtime remains static and contains
no analyzer or model call; analysis happens once during private authoring and
is published as canonical companion events.

Private owner-review revision `howdy-transcribed-review-2026-08-14.5` contains
80 contiguous chord/NNS events spanning the complete 237,187 ms backing track.
It preserves 71 local-reader events and replaces the taught-solo window with
the nine existing source-timed lesson-solo events. Thirty-two events are
visibly marked `check`; none is marked approved.

## Authoring correction

Unconstrained analysis detected a false 157 BPM E-minor/B-minor interpretation.
The reusable authoring command now supplies the known lesson context:

- D major;
- 4/4;
- 79.8 BPM;
- one full-song key region.

The reader resolves the pulse to 80 BPM and 78 bars, producing the expected
D/G/A-centered vocabulary. Confidence, raw candidates, alternatives, review
reasons, analysis version, and attention state are retained in the private
artifact.

## Files

- `scripts/author_travis_song_chords.js`
- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `tests/test_travis_companion.py`
- this handoff

Private, untracked output:

- `/Users/cory/.steel-rag/travis-preview/howdy/howdy.transcribed-review.5.json`

The prior `.4` private artifact remains unchanged for rollback.

## Verification

- `node --check scripts/author_travis_song_chords.js` — passed.
- `node --check partner_companions/travis_howdy/site/companion.js` — passed.
- `.venv/bin/pytest -q tests/test_travis_companion.py` — 25 passed.
- `git diff --check` — passed.
- Draft package and allowlist verifier — passed; 13 files, same-origin-only,
  blocked-route inventory intact.
- Browser QA:
  - Full Song reported `Complete detected chart · Travis review required`.
  - 80 segments and zero pending segments were present.
  - Playback advanced from A7/V7 at 0:13 to D/I at 0:16 while horizontal
    scroll advanced.
  - Map retained the taught-solo form without hidden attention-label noise.

## Deployment status

Local owner preview only. Nothing was deployed or gated, and Travis was not
added.
