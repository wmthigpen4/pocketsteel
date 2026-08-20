# Chord Reader ML v3

## Latest challenger

The current development challenger is the harmonic-CQT root-guided ensemble documented in `docs/handoffs/task-completions/chord-reader-world-class-batch-3.md`. On 124 composition-held-out recordings it improves v3 on root, major/minor, detailed, boundary, and sequence metrics in every corpus. The audible three-song proof reaches 90.59% major/minor WCSR versus 85.91% for v2. Production remains v2; the 98% and Travis gates remain open.

## Objective

Improve the Play Along chord reader with measured gains on held-out public audio while preserving the current v2 analyzer as an immediate fallback. The work is isolated on `feature/chord-reader-ml-v3`; production remains unchanged until every promotion gate passes.

## System design

The development system has four reported readers:

1. `play-along-v2` is the exact current browser analyzer, invoked through `scripts/chord_reader_v2.js`.
2. `btc-ismir19-hf-baseline` is the 170-class pretrained BTC challenger. Its Hugging Face commit and every imported source/weight file are pinned by SHA-256. The historical checkpoint is loaded with PyTorch's weights-only unpickler.
3. `chord-student-v1` is the browser production candidate. It consumes the same 4096-point spectral chroma that its JavaScript worker computes, uses a small temporal convolution network, and emits 49 classes: no-chord plus major, minor, dominant seventh, and minor seventh for all roots.
4. `hybrid-v1` is a conservative product layer over v2 and the raw student. It preserves every raw-student chord boundary except when v2 finds a strong leading no-chord region of at least three seconds and the student's average confidence there is at most 0.32. This narrow gate fixes count-in hallucination without bar-snapping the model output.

The student is trained with full-chord, root, major/minor, and joint root-plus-major/minor losses. Pitch-class rolling supplies transposition augmentation. Composition-level splits keep different players and comp/solo recordings of the same progression together.

The browser runs v2 and the student in separate workers when the `pocketSteel.chordReaderEngine=ml-v3` feature flag is set, then applies the same deterministic hybrid gate used by the Python benchmark. If ONNX or the model fails, the client returns v2 and records `chordReaderEngine: "v2-fallback"` plus a diagnostic reason.

## Data policy

- GuitarSet: supervised ground truth; 360 mono pickup-mix recordings.
- AAM: supervised synthetic ground truth; the importer consumes `*_beatinfo.arff` plus audio mixes.
- Lo-Fi Chords: excluded from supervised training because its paired JSON contains tempo, time signature, and instrument metadata but no chord progression.
- Steel Guitar Forum pairs: held-out steel evaluation first. A pair becomes a weak training example only after complete coverage, monotonic alignment, at least 90% of boundaries within half a beat, and at least 80% duration agreement between independent readers. Accepted weak examples have a maximum training weight of 0.35.

Public songs and charts may be evaluated locally. Audio, charts, and private Travis material are not committed or redistributed by this branch.

Forum charts are never auto-corrected from the challenger being evaluated. A reviewed local chart spec declares every chord and every timing-grid span; `build-chart-reference` only projects those declarations onto frozen bar/beat times. The resulting alignment report may admit a chart for low-weight training only if it passes all weak-label gates. A failed admission remains useful as an evaluation candidate but contributes no training weight.

## Reproduce

Install the hashed Python environment and the pinned browser runtime:

```bash
python3.12 -m pip install -r requirements/chord-reader.lock
npm ci
```

Prepare GuitarSet after downloading the two archives listed in `chord_reader/datasets/downloads.json`:

```bash
python scripts/chord_reader.py prepare-guitarset \
  --annotations-root "$DATA/guitarset/annotations" \
  --audio-root "$DATA/guitarset/audio_mono-pickup_mix" \
  --output-root "$DATA/guitarset/processed" \
  --manifest "$DATA/guitarset/manifest.json"
```

Freeze v2 and BTC on the held-out split before training:

```bash
python scripts/chord_reader.py benchmark "$DATA/guitarset/manifest.json" \
  --engine v2 --split test --output-root "$RUNS/baseline" --report "$RUNS/baseline/v2.json"
python scripts/chord_reader.py benchmark "$DATA/guitarset/manifest.json" \
  --engine btc --split test --local-files-only \
  --output-root "$RUNS/baseline" --report "$RUNS/baseline/btc.json"
```

Cache worker-compatible features, train, export, and benchmark:

```bash
python scripts/chord_reader.py cache-student-features "$DATA/guitarset/manifest.json" \
  --output-root "$DATA/guitarset/features-v1" --cache-manifest "$DATA/guitarset/features-v1.json"
python scripts/chord_reader.py train-student "$DATA/guitarset/features-v1.json" \
  --output-root "$RUNS/student" --epochs 80 --device mps
python scripts/chord_reader.py export-student "$RUNS/student" \
  --output ui/models/chord-student-v1.onnx --report chord_reader/models/chord-student-v1-export.json
python scripts/chord_reader.py benchmark "$DATA/guitarset/manifest.json" \
  --engine student --model ui/models/chord-student-v1.onnx --split test \
  --output-root "$RUNS/student-test" --report "$RUNS/student-test/report.json"
python scripts/chord_reader.py benchmark-hybrid "$DATA/guitarset/manifest.json" \
  --v2-predictions "$RUNS/baseline/predictions/v2" \
  --student-predictions "$RUNS/student-test/predictions/student" \
  --split test --output-root "$RUNS/hybrid-test" --report "$RUNS/hybrid-test/report.json"
```

Run one model directly or build a local chart reference without committing source material:

```bash
python scripts/chord_reader.py predict-student "$AUDIO" \
  --model ui/models/chord-student-v1.onnx --output "$RUNS/song/student.json"
python scripts/chord_reader.py build-chart-reference "$PRIVATE/chart-spec.json" "$RUNS/song/v2.json" \
  --reader "$RUNS/song/v2.json" --reader "$RUNS/song/independent-reader.json" \
  --output "$PRIVATE/reference.json" --report "$RUNS/song/alignment.json"
```

## Frozen public result

The tracked GuitarSet test reports contain 36 recordings from three composition-level split groups. Compared with the frozen Play Along v2 baseline, `chord-student-v1` achieved:

| Metric | v2 | Student | Absolute gain |
| --- | ---: | ---: | ---: |
| Major/minor WCSR | 0.3928 | 0.5214 | +0.1286 |
| Root WCSR | 0.4062 | 0.5835 | +0.1774 |
| Detailed WCSR | 0.3304 | 0.4726 | +0.1421 |
| Boundary F1 | 0.3558 | 0.5013 | +0.1455 |

The projected student runtime for four minutes of audio is 0.25 seconds on the benchmark machine. The frozen public promotion report passes every currently applicable automated gate. This is evidence of a material improvement on public guitar recordings, not a claim that the model is ready for steel-guitar production: the broader steel set and Travis review remain required.

## Visual proof suite on real songs

Serve the repository locally and open `/ui/chord-reader-proof/` to inspect three public-domain songs against 49 hand-authored bars. The synchronized player switches among a licensed human performance of “Amazing Grace” and app-owned deterministic performances of “When the Saints Go Marching In” and “Oh! Susanna.” It shows the chart, current v2 output, raw-student output, and hardened-hybrid output for every bar; any bar can be clicked to hear the underlying audio.

Across the suite, the hybrid identifies 47 of 49 musical bars versus 43 of 49 for v2. Duration-weighted major/minor WCSR is 88.7% for the hybrid versus 85.9% for v2. The gain is concentrated in the human “Amazing Grace” performance: the hybrid reaches 88.8% versus 80.0% for v2 by preserving its count-in as no-chord. On the two deterministic recordings, hybrid WCSR trails v2 by 0.3 and 1.5 percentage points even though it ties or beats v2 on dominant bar labels. Those regressions are displayed per song in the player.

The first attempted post-processor forced one student label per v2 bar. It raised the single-song proof score but reduced held-out GuitarSet major/minor WCSR from 52.1% to 44.5%, so it was rejected. The committed hybrid instead exactly matches the raw student on all 36 frozen GuitarSet test recordings: 52.1% major/minor WCSR, 58.4% root WCSR, 47.3% detailed WCSR, and 50.1% boundary F1. This is a zero-regression safety result on that held-out set, not evidence that the gate is universally safe.

Regenerate all proof JSON from the tracked model, audio, authored timeline, and frozen GuitarSet reports:

```bash
python scripts/build_chord_reader_proof.py
```

## Promotion contract

Against frozen v2, the challenger must achieve all of the following:

- at least +0.08 absolute pooled major/minor WCSR;
- at least +0.05 absolute pooled root WCSR;
- at least +0.05 major/minor WCSR on the steel stratum;
- no named stratum worse by more than 0.03;
- boundary F1 no worse by more than 0.02;
- a projected four-minute runtime no more than 15 seconds and resident memory no more than 1.2 GiB;
- after automated gates pass, Travis prefers the challenger on at least 7 of 10 sealed steel songs and it needs at least 30% fewer corrections.

Run the machine gates with:

```bash
python scripts/chord_reader.py check-promotion "$RUNS/baseline/v2.json" "$RUNS/student-test/report.json" \
  --output "$RUNS/student-test/promotion.json"
```

The feature flag stays off and v2 remains the product reader until the public, steel, runtime, and Travis gates all pass.

## Travis review handoff

After ten Pocket Steel songs have frozen v2 and student reports, create a blinded packet and store its key outside the packet directory:

```bash
python scripts/chord_reader.py make-travis-packet "$PRIVATE/steel-manifest.json" \
  "$RUNS/steel-v2/report.json" "$RUNS/steel-student/report.json" \
  --packet-root "$PRIVATE/travis-review" --key "$PRIVATE/travis-answer-key.json"
```

The packet strips engine/model identities, deterministically alternates which system is A or B, and asks Travis only for preference plus correction counts. Once he completes `review.json`, unblind it into the promotion-gate contract:

```bash
python scripts/chord_reader.py score-travis-review "$PRIVATE/travis-review/review.json" \
  "$PRIVATE/travis-answer-key.json" --output "$RUNS/steel-student/travis-review.json"
```

This keeps Travis out of the initial training loop. His ten-song pass is a sealed, late-stage domain-expert test after the machine evidence already shows the challenger is better than v2.
