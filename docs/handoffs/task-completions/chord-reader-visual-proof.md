# Chord Reader Real-Song Visual Proof

## Task Summary

Branch: `feature/chord-reader-ml-v3`

Added an inspectable synchronized player in response to the request for direct evidence rather than aggregate claims. It plays the existing CC BY “Amazing Grace” lesson recording and displays the hand-authored expected chord, current v2 result, and revised-model result for every musical bar.

The page also displays the complete frozen 36-recording GuitarSet comparison, exact model/audio hashes, reproduction command, and explicit disclosures about AAM and Lo-Fi Chords.

## Demonstrated Result

- Revised model: 15 of 16 musical bars match the expected root and major/minor class.
- Current v2: 13 of 16 musical bars match.
- Revised model correctly finds C major in bars 3 and 11; v2 emits Am7 and G respectively.
- Both readers miss bar 13 Em as G.
- Raw whole-track major/minor WCSR is 77.8% for the revised model versus 80.0% for v2 because the revised model hallucinates chords during the count-in and has noisier boundaries.
- Frozen GuitarSet test: revised model 52.1% major/minor WCSR versus BTC 43.3% and v2 39.3% across 36 held-out recordings.

This is stronger musical-bar behavior on one real non-guitar recording, not proof of “any song” robustness. The count-in failure is now a specific next defect.

## Files Changed

- `scripts/build_chord_reader_proof.py`
- `ui/chord-reader-proof/index.html`
- `ui/chord-reader-proof/proof.css`
- `ui/chord-reader-proof/proof.js`
- `ui/chord-reader-proof/data/proof.json`
- `ui/chord-reader-proof/data/reference.json`
- `ui/chord-reader-proof/data/student.json`
- `ui/chord-reader-proof/data/v2.json`
- `tests/test_chord_reader_proof.py`
- `docs/chord-reader-ml-v3.md`
- `docs/handoffs/task-completions/chord-reader-visual-proof.md`

## Tests and Checks

- Focused chord-reader/proof tests: `33 passed`.
- Ruff: passed.
- JavaScript syntax: passed.
- `git diff --check`: passed.
- In-app browser DOM inspection: passed; all 16 bars, disclosures, hashes, and benchmark values rendered.
- Interactive browser smoke: clicking bar 3 sought to 9.474 seconds, played audio, highlighted one active bar, and displayed Chart C / v2 Am7 / Revised C.
- Browser console warnings/errors: none.

## Risks

- The revised model still mishandles the two-bar count-in.
- The player compares root and major/minor class per musical bar; it does not claim exact seventh-quality correctness.
- One real song is an intelligible demonstration, not a statistically sufficient steel or instrumentation evaluation.
- The static development server must remain running for the local URL to work.

## Human Decision Needed

Listen to the open player and decide whether the visible improvement justifies the next engineering slice: count-in/no-chord calibration followed by a small public-domain multi-instrument song set. Do not send anything to Travis yet.

## Safe-to-Stage Exact Files

Every file under “Files Changed” is part of this proof experience and safe to stage by exact path.

## Files That Must Not Be Staged

- Local environments, downloaded forum material, training caches, and temporary screenshots.
- Any unrelated file in the original dirty worktree.

## Recommended Next Lane

Lane 15 should listen to this player first. If accepted as a useful proof surface, Lane 05 can fix no-chord/count-in handling and Lane 15 can add multiple frozen public-domain multi-instrument songs before any Travis review.

## Commit Readiness

Ready for an exact-path feature-branch commit after final staged checks. Not ready for production activation or Travis review.
