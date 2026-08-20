# Chord reader world-class batch 2

## Outcome

The development branch now has a boundary-guided three-model chord ensemble that improves the prior candidate on every reported metric in every sealed corpus. It was trained from a 934-recording, four-dataset pool and evaluated on 124 composition-held-out recordings totaling 83.2 minutes. Production remains v2 and Travis material was not used.

## Measurement correction

The evaluator compared root spellings as strings, so enharmonic equivalents such as `Eb` and `D#` were counted as different chords. Root, bass, detailed-chord, and sequence comparisons now use pitch class where appropriate. Regression tests cover enharmonic roots and inversions.

This correction changed the prior candidate's IDMT major/minor score from 46.17% to 73.77% and root score from 51.18% to 79.16%. It changed measurement only, not predictions.

## New architecture

- Chord logits: equal-weight ensemble of the generalist multiband TCN, generalist multiband Transformer, and IDMT-trained multiband TCN.
- Boundary evidence: a separately trained boundary Transformer with a binary chord-change head.
- Decoder: Viterbi chord decoding with boundary-conditioned transition evidence.
- Boundary calibration: scale 1.0 and bias -1.5, chosen on composition-held-out AAM, GuitarSet, and Winterreise development splits before sealed testing.
- Product safety layer: the existing narrow leading no-chord overlay remains separate from the learned reader.

## Sealed comparison

| Corpus | Tracks | Prior MM | New MM | Prior root | New root | Prior boundary | New boundary |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GuitarSet | 36 | 55.27% | 55.89% | 58.31% | 58.47% | 47.35% | 51.26% |
| Tiny AAM | 5 | 82.31% | 82.83% | 82.87% | 83.16% | 81.04% | 86.20% |
| Winterreise | 4 | 72.71% | 73.49% | 75.38% | 75.80% | 41.14% | 49.01% |
| IDMT Guitar | 79 | 73.77% | 77.18% | 79.16% | 81.83% | 34.86% | 41.80% |

Across all 124 recordings, duration-weighted major/minor recall rises from 69.98% to 71.89%, root recall from 73.71% to 75.07%, detailed recall from 46.11% to 47.81%, and track-macro boundary F1 from 40.55% to 46.57%. Macro sequence edit rate falls from 124.18% to 61.00%.

## Audible proof

The three-song proof player now reports:

- 46/49 dominant bars for the challenger versus 43/49 for v2;
- 89.92% duration-weighted major/minor recall versus 85.91% for v2;
- 95.34% on “When the Saints Go Marching In”;
- 97.41% on “Oh! Susanna”;
- 79.60% on the licensed human “Amazing Grace,” still 0.39 points behind v2 and still missing its C bar 11 and Em bar 13.

The player was browser-tested after rebuilding: song switching updates the audio source, and clicking a bar seeks and plays from that bar.

## Reproduce

```bash
python scripts/build_chord_reader_proof.py
python -m pytest -q tests/test_chord_reader.py tests/test_chord_reader_proof.py
node --check ui/chord-reader-proof/proof.js
```

The tracked model card is `chord_reader/models/chord-boundary-guided-ensemble-v3.json`; the sealed report is `chord_reader/benchmarks/boundary-guided-ensemble-v3/sealed-summary.json`.

## Remaining work

This is a material root/quality/boundary improvement, not completion of the 98% objective. The next high-value experiment is a dual-stream harmonic/accompaniment front end on human full mixes, followed by hard-example training for tonic overprediction and relative-major/minor mistakes. Travis's ten-song packet remains gated until the public human-song result and steel proxy evidence improve further.
