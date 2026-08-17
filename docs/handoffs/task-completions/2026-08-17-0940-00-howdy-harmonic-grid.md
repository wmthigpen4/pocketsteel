# Howdy harmonic-transition beat alignment

## Task summary

Replaced independent nearest-beat snapping with a deterministic global alignment pass. For each public-chart boundary, the authoring tool now compares the audio chroma immediately before and after neighboring detected beats, scores the expected root transition, and chooses one monotonic boundary path across the song. Exact taught-solo scope anchors and lesson-authored solo chord offsets remain unchanged.

## Files changed

- `scripts/author_travis_song_chords.js`
- `scripts/lib/song_chart_authoring.js`
- `partner_companions/travis_howdy/README.md`
- `tests/test_travis_companion.py`
- This handoff

## Private/generated artifacts

- `/Users/cory/.steel-rag/travis-preview/howdy/howdy.transcribed-review.9.json`
- `output/pdf/Howdy-music-first-review-v10.pdf` (ignored; do not commit)
- Local reviewed bundle: `tmp/howdy-owner-review-2026-08-17.22`

## Howdy results

- The audio tracker found 630 beats with a typical 372 ms interval.
- All 53 non-anchor reference boundaries received harmonic evidence scores.
- The global path moved eight reference boundary points to a neighboring beat; seven changes remain visible after same-root/section merging.
- The selected path gained `0.852` harmonic-evidence score over nearest-beat snapping.
- Exact taught-solo offsets from 118,320 through 142,384 ms were preserved.
- An independent chroma-novelty audit improved from 22 to 23 boundaries within 80 ms and from 30 to 33 within 120 ms. This is corroborating authoring evidence, not human approval.
- Live browser QA confirmed `song-chord-008` activates G at the revised audio time of 37,361 ms.

## Verification

- `78 passed` across companion and shared practice-tool suites.
- JavaScript syntax, Ruff, and `git diff --check` passed.
- Static bundle isolation verification passed for revision `.9` with 18 files and all general-app routes blocked.
- The three-page PDF was rasterized and visually inspected; revision `.9`, headers, footers, notation, and tab render without clipping.

## Smoke target

- `http://127.0.0.1:8897/practice-guide/howdy/?build=harmonic-grid-9`
- Authentication: none.
- Select `Full song` and listen especially around 0:37, 0:45, 1:31, 1:34, 3:16, 3:29, and 3:42.
- Expected revision: `howdy-transcribed-review-2026-08-17.9`.

## Risks

- Harmonic scoring is an authoring aid, not musical approval. Vocals, passing tones, and arrangement transients can still favor a neighboring beat incorrectly.
- Public references determine chord order and remain imperfect. Uncertain musical claims are still marked for Travis review.
- A human listening pass remains the final authority.

## Safe-to-stage list

- `scripts/author_travis_song_chords.js`
- `scripts/lib/song_chart_authoring.js`
- `partner_companions/travis_howdy/README.md`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-17-0940-00-howdy-harmonic-grid.md`

## Must-not-stage list

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `~/.steel-rag/`

## Human decision needed

Listen through the seven moved visible card boundaries and flag any transition that should remain on the earlier beat.

## Commit readiness

Safe to commit.
