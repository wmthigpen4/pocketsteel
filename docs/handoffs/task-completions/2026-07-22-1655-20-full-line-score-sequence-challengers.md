# Lane 20 — Full-line score sequence challengers

## Task summary

Implemented the first isolated neural full-line conventional-score reader around the immutable reviewed score-sequence dataset. The reader emits ordered attack groups with simultaneous scientific pitches, preserves unison multiplicity, and treats blank or structurally incomplete output as a hard failure.

Training used only the 27 discovery-development cases. Configuration selection used a deterministic content-unit-grouped development/calibration split. Each exact model configuration and weight file was frozen and hashed before the 12 already-opened discovery-shadow cases were scored. The third candidate added rights-safe synthetic staff pretraining generated in memory only from approved development labels.

All three candidates were rejected by the unified review gate. No review packet was created. No model was promoted or wired into runtime.

Intentionally not changed:

- no validation or sealed-test data was opened;
- no tablature, source text, rhythm, duration, ties, or unreviewed localization entered the targets;
- no raw source or reviewed record was modified;
- no application dependency, embeddings, runtime behavior, or public artifact was created.

## Private candidate results

Baseline opened-shadow performance:

- exact score sequences: 2/12;
- exact attack counts: 7/12;
- exact attack groups: 74/105;
- token error rate: 28.18%;
- blank lines: 1.

| Candidate | Training formulation | Exact sequences | Exact counts | Exact groups | Token error | Complete/nonblank | Result |
|---|---|---:|---:|---:|---:|---:|---|
| `score-ctc-348da9aa93b7fb8d` | scratch CTC, original early selection | 0/12 | 0/12 | 0/105 | 100.00% | 0/12 | rejected |
| `score-ctc-cb15696121b1b094` | scratch CTC, anti-blank initialization and corrected selection | 0/12 | 0/12 | 1/105 | 80.30% | 11/12 | rejected |
| `score-ctc-6d9b5024314d514e` | synthetic staff pretraining then real-line fine-tuning | 0/12 | 2/12 | 6/105 | 65.15% | 12/12 | rejected |

The synthetic formulation materially improves the neural reader, but it remains worse than the pretrained Audiveris/semantic baseline on every accuracy gate. Its zero-blank result does not make its pitches trustworthy.

All private contracts, weights, logs, and reports remain ignored beneath `corpus-private/melody-decisions/`. The private PyTorch installation also remains there and is not an application dependency.

## Files changed

- `pocketsteel/amazing_tablature_score_sequence.py`
  - added the optional-dependency CTC model, token contract, metrics, grouped calibration, deterministic training, private artifact freeze, baseline comparison, and fail-closed review gate;
  - added in-memory synthetic score rendering for staff, chord, accidental, octave, scan, and layout variation.
- `pocketsteel/amazing_tablature_extraction.py`
  - exposed the private trainer through the existing Lane 20 extractor workflow.
- `scripts/amazing_tablature.py`
  - added `train-discovery-score-sequence-challenger` with private dependency root, seed, and epoch controls.
- `tests/test_amazing_tablature_score_sequence.py`
  - added target encoding, CTC collapse, completeness, metric, vocabulary, and grouped-split tests.
- `docs/amazing-tablature-training.md`
  - documented the isolated trainer, lineage, target scope, and unified rejection gate.
- This handoff.

Generated private artifacts, never to be staged:

- private PyTorch trainer dependencies;
- three immutable model contracts and weight files;
- three opened-shadow reports and training histories.

## Tests and checks

- `.venv/bin/python -m pytest tests/test_amazing_tablature_score_sequence.py tests/test_amazing_tablature_extraction.py -q`
  - PASS: 157 passed.
- `.venv/bin/python scripts/amazing_tablature.py train-discovery-score-sequence-challenger --help`
  - PASS.
- `.venv/bin/python -m py_compile pocketsteel/amazing_tablature_score_sequence.py pocketsteel/amazing_tablature_extraction.py scripts/amazing_tablature.py`
  - PASS.
- `git diff --check`
  - PASS.
- Three private discovery-only training/shadow commands completed and wrote immutable rejected lineage.

## Integration notes

The experiment establishes that the present 27 real development lines are insufficient to replace pretrained OMR with an end-to-end pixel model. The next score-reader work should be residual learning on top of Audiveris/head-graph features, with additional approved discovery score lines added through automatic label harvesting only where existing human feedback already supplies complete score order, chord membership, and pitch. It should not ask the user to audit more lines merely to compensate for a blank or structurally inconsistent machine packet.

The stronger current semantic baseline remains authoritative. The neural models may be used only as private diagnostics until a later frozen candidate beats every unified shadow gate.

## Risk assessment

Risk: low to medium.

There is no runtime effect and all weights/data remain ignored. The main risk is overinterpreting the improvement between neural candidates; it is evidence that synthetic pretraining helps, not evidence that the neural reader is ready.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_score_sequence.py`
- `pocketsteel/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_score_sequence.py`
- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-22-1655-20-full-line-score-sequence-challengers.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- all unrelated untracked historical handoffs
- everything beneath `corpus-private/`
- private dependencies, source images, labels, model weights, logs, reports, embeddings, and indexes

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit.

## Suggested next step

Build a discovery-only residual score model that consumes the pretrained Audiveris/head-graph sequence plus source-image features, expand labels only from already-complete approved score feedback, and compare it against the semantic baseline under the same frozen no-review gate. Keep validation and sealed test closed.
