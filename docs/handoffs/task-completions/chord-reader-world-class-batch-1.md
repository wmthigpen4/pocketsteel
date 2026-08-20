# Chord reader world-class batch 1

## Outcome

The ML-v3 branch now has a conservative hybrid reader, a frozen no-regression GuitarSet report, and a browser proof suite where the result can be heard and inspected bar by bar. Production remains unchanged and Travis has not been engaged.

## Branch and scope

- Branch: `feature/chord-reader-ml-v3`
- Development player: `/ui/chord-reader-proof/`
- Production feature flag: still off
- Public proof: three public-domain compositions, 112.2 seconds of audio, 49 hand-authored bars
- Public held-out benchmark: 36 GuitarSet recordings, 1,292.0 seconds

## Results

| Evidence | v2 | Raw student | Hardened hybrid |
| --- | ---: | ---: | ---: |
| Proof-suite dominant bars | 43/49 | 47/49 | 47/49 |
| Proof-suite major/minor WCSR | 85.9% | 84.5% | 88.7% |
| GuitarSet major/minor WCSR | 39.3% | 52.1% | 52.1% |
| GuitarSet root WCSR | 40.6% | 58.4% | 58.4% |
| GuitarSet detailed WCSR | 33.0% | 47.3% | 47.3% |
| GuitarSet boundary F1 | 35.6% | 50.1% | 50.1% |

The suite gain is concentrated in the licensed human “Amazing Grace” recording. The hybrid is 0.3 and 1.5 percentage points behind v2 in duration-weighted major/minor WCSR on the two deterministic performances; the player discloses those regressions. The hybrid exactly reproduces the raw-student outputs on all 36 held-out GuitarSet tracks.

## Engineering decision

An initial bar-pooled hybrid was rejected after it reduced held-out GuitarSet major/minor WCSR from 52.1% to 44.5%. The accepted hybrid changes only a long leading v2 no-chord region when v2 confidence is at least 0.75 and mean student confidence is at most 0.32. It preserves every other student boundary.

Python and browser implementations use the same thresholds and semantics. The frozen hybrid benchmark can be rebuilt from existing v2 and student predictions with `benchmark-hybrid`; it does not rerun or silently retune either model.

## Reproduction

```bash
python scripts/build_chord_reader_proof.py
python -m pytest -q tests/test_chord_reader.py tests/test_chord_reader_proof.py
node --check ui/chord-reader-proof/proof.js
node --check ui/practice-analysis-client.js
```

## Next promotion work

1. Expand the human-performance proof set before tuning thresholds again.
2. Add explicit percussion/count-in and fade-out annotations to the evaluation schema.
3. Test richer temporal decoding as a new frozen challenger, never by changing the current held-out outputs in place.
4. Run the sealed ten-song steel test and only then prepare Travis's blinded comparison packet.
