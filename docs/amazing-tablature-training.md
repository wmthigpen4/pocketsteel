# Lane 20 — Amazing Tablature Training

Lane 20 is the durable, private operating lane for teaching Melody Studio better tablature decisions from reviewed score-and-tab examples. It has no frontend trainer. Codex operates the same checked-in command workflow on every run.

## Start every run

1. Read `AGENTS.md` and this file.
2. Run `git status --short` and keep unrelated work parked.
3. Read the latest `*-20-*` handoff.
4. Run `.venv/bin/python scripts/amazing_tablature.py status`.
5. Resume from the recorded checkpoint rather than repeating completed work.

Private state lives under ignored `corpus-private/melody-decisions/`. Never stage that directory or copy its source text, images, literal tab, filesystem metadata, annotations, or review details into a public handoff.

## Natural requests

The user does not need a memorized prompt. These are sufficient:

- `Process the tablature examples in ~/Downloads/New Tabs.`
- `Show me the current training status.`
- `Review the unresolved exceptions.`
- `Build a challenger and compare it with the current model.`
- `Approve challenger <exact-model-id> for beta.`

If intake does not include a known source copedent, stop and request only that missing fact. Never guess a source setup from control labels alone.

## Command workflow

Register an immutable batch:

```bash
.venv/bin/python scripts/amazing_tablature.py ingest ~/Downloads/New\ Tabs \
  --source-copedent source-e9-abc-defg-v1
```

For a full collection that needs a sealed final test, partition immediately after intake and before annotations or rule work:

```bash
.venv/bin/python scripts/amazing_tablature.py partition <batch-id> \
  --document-break IMG_0312.JPG \
  --force-discovery IMG_0161.JPG \
  --force-discovery IMG_0162.JPG \
  --discovery-target 194 \
  --validation-target 28 \
  --test-target 56
```

Repeat `--force-discovery` for every page already viewed during planning. The partitioner expands each named page by the configured one-page guard, treats the remaining contiguous runs as indivisible provisional content units, links exact and very-close perceptual matches, balances source sequences and structural image categories, and generates the split from a private random seed.

Normal status output contains counts and digests but not sealed-test membership. Discovery pages replace the normal annotation work queue, validation has a separate queue, and the test mapping and pending ground-truth state live in a permission-restricted `sealed-test/` directory. Re-running the same partition configuration is idempotent; changing it after sealing fails.

Because this partition stage deliberately performs no OCR or semantic transcription, status labels its guarded content units `provisional_structural` and keeps page-type/musical-content stratification pending independent Lane 15 review. If that review finds a unit crossing partitions, create a corrected replacement batch and split, then supersede the unopened batch before any discovery annotations or rule work begin.

When an earlier collection has been replaced, preserve it for audit while excluding it from future datasets:

```bash
.venv/bin/python scripts/amazing_tablature.py supersede-batch <old-batch-id> \
  --replacement-batch <new-batch-id> \
  --approval-reference '<user decision>'
```

Superseding does not delete the old batch or silently change a runtime model. It makes the replacement authoritative, blocks new annotation/review/validation work on the old batch, excludes its accepted records from future challengers and evaluations, and marks models derived from it as historical and ineligible for future comparison.

Verify that registered source bytes remain unchanged at any time:

```bash
.venv/bin/python scripts/amazing_tablature.py verify-intake <batch-id>
```

Codex writes private annotations, then imports and validates them:

```bash
.venv/bin/python scripts/amazing_tablature.py annotate <batch-id> <private-annotations.jsonl>
.venv/bin/python scripts/amazing_tablature.py validate <batch-id>
```

Review resolutions contain stable decision IDs and `accept`, `exclude`, or `correct` actions. Corrections never overwrite the immutable raw annotation file:

```bash
.venv/bin/python scripts/amazing_tablature.py review <batch-id> <private-resolutions.jsonl>
```

Build, evaluate, and report a deterministic challenger:

```bash
.venv/bin/python scripts/amazing_tablature.py train
.venv/bin/python scripts/amazing_tablature.py evaluate <exact-model-id>
.venv/bin/python scripts/amazing_tablature.py report <exact-model-id>
```

Training stops here. After explicit approval of the exact ID:

```bash
.venv/bin/python scripts/amazing_tablature.py promote <exact-model-id> \
  --channel beta \
  --approval-reference '<approval record>'
```

Stable promotion additionally requires an existing independent Lane 15 handoff. Rollback is limited to a model that was previously active on the selected channel.

## Durable records

Each batch has an immutable manifest and separate mutable processing state. The manifest records file hashes, source copedent, evidence type, and an immutable digest. The state records checkpoints, counts, and generated model IDs. Re-ingesting identical inputs resumes the batch; reusing a batch ID for changed inputs fails.

A partitioned batch additionally pins the source-copedent revision and digest, split-seed digest, document groups, provisional content units, discovery/validation/test counts, structural distribution summary, and immutable partition digest. Annotation imports must match the assigned discovery or validation partition. The normal annotation command rejects sealed-test inputs.

Annotations use stable source control IDs and record source mechanics plus copedent-neutral chosen-versus-alternative features. Mechanical validation checks the source string, fret, pitch change, control effect, sounding and sustained strings, and melody-on-top invariant before a decision may train.

High-confidence machine-validated expert decisions may enter beta training while retaining that review label. Low-confidence or contradictory decisions block. A deterministic ten-percent audit sample remains visible without blocking the beta dataset. Player feedback receives one-quarter the training authority of expert score/tab evidence and can never create a hard rule.

Every challenger is rebuilt from the complete accepted discovery partition of the authoritative batch. Legacy unsplit batches continue to use `train` and `holdout`, but superseded batches are excluded. Challenger IDs derive from the dataset hash and training configuration. Refinement evaluation uses validation records, requires 100% mechanical validity, checks the current required benchmark groups, and compares abstract chosen-versus-alternative preference accuracy against an eligible stable champion. The sealed test remains outside normal annotation and evaluation commands until a later Lane 15 rules-freeze workflow opens it once.

## Lane boundaries

- Lane 20: private evidence, annotations, exceptions, training, evaluation, and promotion readiness.
- Lane 05: load an approved sanitized model in the runtime and preserve deterministic mechanics.
- Lane 06: player-facing arrangement and style controls only.
- Lane 15: independent release evaluation; required before stable promotion.
- Lane 01: exact-path staging and commits.
- Lane 12: protected-preview update and smoke.

Lane 20 never owns scraping, embeddings, Chroma, RAG ingestion, auth, billing, DNS, Tunnel, deployment policy, or a browser-based model trainer.

## Handoff contract

Every Lane 20 run writes a `docs/handoffs/task-completions/YYYY-MM-DD-HHMM-20-<task>.md` handoff containing only safe summaries: batch/model IDs, counts, hashes, checks, gate results, risks, exact safe-to-stage files, and the next lane. It must never contain source images, literal passages, private annotations, private paths that identify a person, or custom copedent snapshots.
