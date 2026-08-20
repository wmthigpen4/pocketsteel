# Chord Reader v9 integrity and architecture integration

## Task summary

Integrated the first production-quality v9 research slice on the isolated
`feature/chord-reader-ssl-v9` branch. The slice adds rich factorized chord
heads, multiple feature/architecture challengers, a permissively licensed
Dasheng offline teacher, same-feature logit ensembles, soft routing and
beat-aware segmental research paths, native bar timing, leak-resistant
train/development/calibration partitions, tamper-evident feature/label seals,
coverage-correct scoring, literal-bar confidence evaluation, and a strict v2
promotion contract.

The strict certification claim is intentionally narrower than general detailed
chord accuracy: at least 98% precision for accepted simplified Play Along chord
products, with coverage disclosed and statistical/real-corpus support gates.
No production player/runtime was changed, no Travis packet was created, and no
calibration or confirmation threshold was selected.

## Files changed

- `steel_guitar_rag/chord_reader/artifact_integrity.py`
- `steel_guitar_rag/chord_reader/bar_product.py`
- `steel_guitar_rag/chord_reader/bar_promotion.py`
- `steel_guitar_rag/chord_reader/benchmark.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `steel_guitar_rag/chord_reader/dasheng.py`
- `steel_guitar_rag/chord_reader/dasheng_cache.py`
- `steel_guitar_rag/chord_reader/datasets.py`
- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/metrics.py`
- `steel_guitar_rag/chord_reader/promotion.py`
- `steel_guitar_rag/chord_reader/routing.py`
- `steel_guitar_rag/chord_reader/segmental.py`
- `steel_guitar_rag/chord_reader/split_protocol.py`
- `steel_guitar_rag/chord_reader/student.py`
- `chord_reader/models/dasheng-base.json`
- `requirements/chord-reader-dasheng.in`
- `requirements/chord-reader-dasheng.lock`
- focused `tests/test_chord_reader*.py` coverage and the linked component
  handoffs from this date.

## Important contracts

- Prediction gaps count against the full reference duration and report covered,
  missing, and total prediction coverage.
- Detailed vocabulary ceiling/OOV duration, full confusion matrices,
  insertion/deletion/substitution counts, confidence calibration, musical chord
  changes, and authored-segment boundaries are separate metrics.
- Factorized labels cover 41 exact qualities plus root, product, mode,
  structure, bass, and boundary heads.
- Strict training requires an artifact seal and a validated split protocol.
- Calibration benchmarking selects exactly the frozen explicit-bar-eligible
  set and verifies the supplied timing manifests.
- Certification requires clean committed source; exact model/cache/reference/
  prediction/timing/decoder hashes; no oracle timing; at least 150 accepted
  bars, 50% coverage, 75% bar eligibility, and a one-sided 95% Wilson lower
  bound of at least 98%. AAM, GuitarSet, and IDMT each require at least 30
  accepted bars, 25% coverage, and 98% empirical precision.
- Same-feature ensembles average independent head logits before exactly one
  decode; they never vote or average decoded segments.

## Generated research artifacts (ignored; do not stage)

Native timing was regenerated and verified for 20 AAM, 360 GuitarSet, 506
IDMT, and 1,500 NRG-CP tracks. Winterreise remains correctly ineligible for
literal-bar certification.

Sealed protocols currently contain:

- multiband: 2,212 sealed source tracks; artifact set
  `9bcbc8256721cc796dac22b05fa44af3ea08cbb7c4298a1d5d131bfa7b1291c5`;
- harmonic CQT: 2,212 tracks; artifact set
  `04607dae313110ad43c7c09d8a6080d1fb78d945203a207a0b5f037c88c45d9e`;
- Dasheng: 1,650 tracks; artifact set
  `f63d76ac59c4503f1a53e803f2bc16e03a84b9a3f9e6e0d84195fee34414e3c1`;
- Basic Pitch: 428 tracks; artifact set
  `65c5df0447edf3d721d3029e2bf0527d907cd1d78d9ec02bfb1231a87002504e`.

The first three share assignment
`d5d589583ee81feed881103557dd4d088b08e4d9e6e50fe27cb0672fdd311017`:
1,158 training, 246 development, and 246 calibration tracks. Exactly 242
calibration tracks have frozen explicit bars (2 AAM, 36 GuitarSet, 48 IDMT,
156 NRG-CP); their set hash is
`144a643a4ffb635ba65018f705d80f863f0b2bd48570494b567fa57c93bfdb2f`.

## Tests and checks

- `.venv/bin/pytest -q tests/test_chord_reader*.py` — 241 passed, 2 optional
  runtime tests skipped.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader tests/test_chord_reader*.py`
  — passed.
- `git diff --check` — passed.
- Full repository collection is unavailable in this worktree environment
  because unrelated suites require uninstalled `cv2` and `yaml`; focused chord
  reader collection is clean.

## Risks

- No post-seal model has been trained yet; prior model scores are development
  diagnostics from pre-seal code and are not certification evidence.
- Dasheng is an offline/server teacher, not a browser-sized model. Its Apache
  checkpoint is permissive, but training-data provenance still needs product
  review before shipping a derived production path.
- The beat-aware segmental default hurt development accuracy and remains off.
- The soft router has runtime support but still requires composition-grouped,
  development-only counterfactual calibration.
- Basic Pitch currently covers only AAM/GuitarSet/Winterreise and cannot satisfy
  the required IDMT stratum as a standalone promotion candidate.
- The strict 98% bar gate is expected to fail current challengers; failure is a
  valid result and must not be weakened after seeing calibration/confirmation.

## Human decision needed

None before the approved research tournament. Do not contact Travis until a
clean, sealed candidate passes public-song proof and the frozen gates. A later
commercial/product review is required before shipping an SSL-derived teacher
path.

## Safe-to-stage exact files

All source, model-contract, requirement, focused test, and handoff files listed
in `git status --short` for this isolated v9 slice are safe to stage by exact
path. Use no broad staging command.

## Files that must not be staged

- `tmp/` feature caches, labels, protocols, models, predictions, reports, and
  audio;
- downloaded Dasheng snapshots or temporary virtual environments;
- private corpus material, transcripts, vector stores, credentials, or
  unrelated worktree changes.

## Recommended next lane

Lane 20 should train matched multiband seeds and one transformer/CQT boundary
specialist from the sealed train partition. Lane 15 should select ensemble
weights on development only, then freeze a single calibration operating point
and run one presealed confirmation evaluation. Lane 06 should update the proof
player only if a candidate materially improves the three public songs and the
strict gate remains honestly disclosed.

## Commit readiness

Ready for one exact-path research-branch commit after final status review. No
production branch or deployed runtime is in scope.
