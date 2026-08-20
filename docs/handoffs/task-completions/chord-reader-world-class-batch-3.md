# Chord reader world-class batch 3

## Outcome

The v4 development challenger adds a composition-balanced harmonic-CQT root guide to the v3 boundary-guided ensemble. The CQT model votes only on chord roots; chord quality remains controlled by the proven multiband ensemble. This eliminates the quality regression seen with ordinary heterogeneous logit blending.

The model was trained from all 934 available recordings and evaluated once on the frozen 124-recording, composition-held-out test set after a 0.3 root-guide weight was selected on development compositions.

## Why this architecture

- The remaining error gap was primarily root selection, not major/minor quality.
- Multiband chroma discards most octave/register information.
- The new front end suppresses percussion, retains six octaves of CQT energy, includes temporal deltas, and exposes bass-supported roots.
- Each composition receives one unit of training weight divided among its renditions, preventing repeated performances from dominating unique songs.
- Root-marginal fusion preserves the base ensemble's conditional quality distribution instead of allowing the CQT specialist to overwrite chord quality.

## Sealed gains over v3

| Corpus | v3 MM | v4 MM | v3 root | v4 root | v3 detailed | v4 detailed | v3 boundary | v4 boundary |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GuitarSet | 55.89% | 56.86% | 58.47% | 60.05% | 51.36% | 52.28% | 51.26% | 53.25% |
| Tiny AAM | 82.83% | 84.19% | 83.16% | 84.51% | 82.83% | 84.19% | 86.20% | 87.45% |
| Winterreise | 73.49% | 75.38% | 75.80% | 77.89% | 40.97% | 40.98% | 49.01% | 50.59% |
| IDMT Guitar | 77.18% | 79.02% | 81.83% | 83.41% | 37.61% | 38.75% | 41.80% | 44.30% |

Across all 124 recordings, v4 reaches 73.44% duration-weighted major/minor recall, 76.69% root recall, 48.76% detailed recall, and 48.84% track-macro boundary F1. The projected four-minute offline runtime is 3.99 seconds.

## Audible proof

- v4: 46/49 dominant bars and 90.59% duration-weighted major/minor recall;
- v3: 46/49 bars and 89.92%;
- v2: 43/49 bars and 85.91%.

The licensed human “Amazing Grace” recording rises to 80.41%, now slightly above v2's 79.99%, although bar 11 C and bar 13 Em remain incorrect. “When the Saints Go Marching In” reaches 96.16%; “Oh! Susanna” reaches 97.71%.

## Decision

v4 replaces v3 as the development proof candidate because it improves every tracked metric in every sealed corpus and improves the audible suite. Production remains v2, and Travis has not been contacted.

## Remaining bottlenecks

- GuitarSet is still only 56.86% major/minor and 60.05% root recall.
- Large-vocabulary detailed quality remains weak on Winterreise and IDMT.
- Human-song boundary timing remains far below the proof player's authored grid.
- The Amazing Grace tonic-persistence errors remain a targeted hard-example case.

The next batch should add more unique human full-song compositions and a structured root/quality/bass model, then use confidence-calibrated abstention before the steel-domain review.
