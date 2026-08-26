# Travis phase backsolve bounded result

## Outcome

One fixed-threshold anchor/backsolve implementation and one evaluation were
completed. The system now uses sustained, confident chord changes after the
intro to infer which detected pulse is Beat 1, then works backward to expose a
count-in or pickup before numbered Bar 1.

The acceptance gate was fixed before evaluation: at least 8 reliable anchors
and a normalized winning margin of at least 0.12. Ten of 15 pilot songs cleared
the gate, five remained visibly unresolved, and five accepted songs received a
nonzero phase correction. No threshold was tuned after seeing the result.

## Accuracy result

This is a timing change, not a chord-label model change. The existing held-out
chord-label measurements therefore remain 79.936% at full coverage and 99.597%
precision at 39.807% selective coverage.

On the 15-song pilot, where human downbeat labels do not yet exist, the
predeclared sustained-change alignment proxy changed as follows:

| Timing proxy | Before | After |
| --- | ---: | ---: |
| Weighted reliable changes on Beat 1 | 50.58% | 66.36% |
| Weighted reliable changes on Beat 1 or Beat 3 | 73.81% | 79.75% |

The separate three-track hand-authored timing check stayed at 43 of 49 bars
within 250 ms (87.76%) before and after. All three short tracks lacked the 8
required anchors, so the conservative gate correctly made no phase change.

## Reviewer controls

- An audible click overlay uses a higher click for Beat 1.
- Accepted and unresolved phase status is shown per song.
- A reviewer can select a phase or make the nearest playing beat Beat 1 with one
  click; the choice autosaves to the protected backend.
- Missing early pulses are backfilled, pickup beats are labeled separately, and
  numbered Bar 1 begins on the first inferred full musical downbeat.
- The fixed horizontal review rail remains visible without page scrolling.

## Verification

- phase-anchor Node tests: 3 passed;
- focused UI tests: 4 passed;
- Worker validation tests: 7 passed;
- TypeScript check passed;
- all 15 browser smokes showed Bar 1, beats 1–4, and phase status;
- reviewer phase override and click-track controls worked in browser;
- JavaScript syntax and `git diff --check` passed.

The generated 15-song proof, evaluation JSON, audio, credentials, and browser
state remain private/ignored and must not be committed.
