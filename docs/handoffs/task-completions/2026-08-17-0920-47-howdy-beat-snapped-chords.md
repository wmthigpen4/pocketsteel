# Howdy beat-snapped chord timeline

## Task summary

Replaced coarse linear chord timing with deterministic audio-beat snapping in the reusable song-chart authoring path. Public references still determine the chord order and rough beat position; non-anchor boundaries now move to the nearest beat detected in the exact packaged MP3. Exact recording and taught-solo scope anchors remain unchanged. Re-authored Howdy as private revision `.8` and regenerated the matching printable PDF.

## Files changed

- `scripts/lib/song_chart_authoring.js`
- `scripts/author_travis_song_chords.js`
- `partner_companions/travis_howdy/README.md`
- `tests/test_travis_companion.py`
- This handoff

## Private/generated artifacts

- `/Users/cory/.steel-rag/travis-preview/howdy/howdy.transcribed-review.8.json`
- `output/pdf/Howdy-music-first-review-v9.pdf` (ignored; do not commit)
- Local reviewed bundle: `tmp/howdy-owner-review-2026-08-17.18`

## Verification

- Howdy analysis detected 630 beats at 157 BPM in 4/4.
- 53 distinct reference boundaries snapped to detected beats with zero unsnapped boundaries.
- Mean absolute adjustment: 103 ms; maximum: 186 ms.
- 44 of 46 comparable public-chart chord starts changed from revision `.7`.
- Browser verification confirmed the first D boundary seeks to the authored snapped time of 3,320 ms and displays D / I.
- `77 passed` across the companion and shared practice-tool suites.
- JavaScript syntax, Ruff, and `git diff --check` passed.
- Static bundle isolation verifier passed for revision `.8`.
- The three-page PDF was rasterized and visually inspected; revision `.8`, 157 BPM, systems, headers, footers, and page numbers render without clipping.

## Smoke Target

- Local route: `http://127.0.0.1:8897/practice-guide/howdy/`
- Authentication: none
- Select `Full song`, start playback, and listen through several chord changes in each section.
- Expected revision: `howdy-transcribed-review-2026-08-17.8`
- Expected tempo: 157 BPM for both taught solo and full song
- Caveat: this is an improved deterministic draft, not a Travis-approved chord timeline.

## Risks

- Beat snapping corrects timing-grid drift but does not prove that every public-chart chord change was assigned to the correct musical beat.
- A beat tracker can select the adjacent beat when the recording has a pickup, weak attack, syncopation, or tempo transition. Human listening remains the final authority.
- The taught-solo chord route retains its exact lesson-authored offsets instead of being automatically rewritten.

## Human decision needed

Listen to representative transitions across all seven sections. Flag any change that should land on the preceding/following beat or on an intentional offbeat.

## Safe-to-stage list

- `scripts/lib/song_chart_authoring.js`
- `scripts/author_travis_song_chords.js`
- `partner_companions/travis_howdy/README.md`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-17-0920-47-howdy-beat-snapped-chords.md`

## Must-not-stage list

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user edit)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `~/.steel-rag/`

## Recommended next lane

Add exception-only manual beat overrides for individual boundaries that fail listening review, keeping the detected beat index and reviewer rationale in the private reference artifact.

## Commit readiness

Safe to commit.
