# Isolated VTT Guidance Admin Pilot

This pilot keeps transcript-derived teaching guidance removable from the SGF corpus and answer. Raw inputs remain read-only outside this repository. Every derived artifact is written beneath the ignored `corpus-private/vtt-guidance-v2/` directory.

## Isolation contract

- The SGF corpus, SGF source cards, Chroma collections, and embeddings are not read or written by VTT retrieval.
- Runtime uses a dedicated, checksummed SQLite FTS5 index.
- Only human-approved E9 and general-technique cards can enter that index.
- `answer` stays the base deterministic/SGF answer and `sources` stays SGF-only.
- The only user-visible addition is a `sections` item titled `Curated lesson guidance` with `style=guidance`.
- Runtime never returns lesson titles, filenames, paths, source IDs, excerpts, transcript attribution, or provenance fields.
- The legacy 899-row curated-guidance retriever remains an offline artifact and is disconnected from `/api/answer`. Its old flags do not activate an answer path.

## Private corpus workflow

All commands run from the repository root with `.venv/bin/python scripts/vtt_guidance.py`.

1. Build the exact approved 62-record manifest:

   ```bash
   .venv/bin/python scripts/vtt_guidance.py prepare-manifest
   ```

2. Generate paraphrased candidates and a privacy review queue using local Ollama only:

   ```bash
   .venv/bin/python scripts/vtt_guidance.py generate
   ```

   Generation stops before publishing if either `qwen3.5:27b` or `gemma4:12b` is unavailable. Qwen runs deterministically with hidden reasoning disabled and a bounded JSON response. Gemma reviews each card independently. There is no hosted or embedding code path.

3. Run the metadata-only candidate corpus audit:

   ```bash
   .venv/bin/python scripts/vtt_guidance.py audit-corpus
   ```

   The command fails on manifest/card/checkpoint inconsistencies, changed source hashes, private-marker or normalized ten-word overlap hits, version mismatches, or enabled quote/embedding policy. Its report contains counts and statuses only—never lesson text, paths, source IDs, or transcript attribution. A passing candidate audit does not make cards runtime-ready.

4. Review every row in `corpus-private/vtt-guidance-v2/review/review-queue.jsonl`. Copy the decision template to a separate private decision ledger and set every decision to `approve` or `reject` with a human reviewer. Do not commit either file. Reject every automated-blocked card and any C6, non-pedal, or unknown-instrument card; the final gate will not admit them.

5. Apply the complete human ledger:

   ```bash
   .venv/bin/python scripts/vtt_guidance.py apply-review \
     --decisions corpus-private/vtt-guidance-v2/review/decisions.jsonl
   ```

   Automated-blocked cards cannot be overridden by the ledger. Approved cards must pass privacy, ten-word overlap, quote/embedding, runtime-instrument, human-approval, and deterministic E9 gates again.

6. Build the dedicated FTS5 index:

   ```bash
   .venv/bin/python scripts/vtt_guidance.py build-index
   ```

7. Add the private retrieval probe ledger at `corpus-private/vtt-guidance-v2/review/retrieval-probes.jsonl`. Each row contains `probe_id`, `kind` (`detail`, `broad`, or `human`), `question`, and `useful_source_ids`; human rows also contain `expected_instruments`. The ledger must contain exactly 43 detail probes, exactly 10 broad probes, and at least one human-labeled probe.

8. Enforce the retrieval gates:

   ```bash
   .venv/bin/python scripts/vtt_guidance.py evaluate
   ```

   The command fails unless detail retrieval reaches Top-3 14/43, Top-5 23/43, and MRR 0.30; all ten broad probes retain a useful Top-3 source; human Top-3 usefulness reaches 80%; and wrong-instrument results remain zero. Its report contains aggregate metrics only.

## Local admin activation

The feature is default-off and requires all three flags plus an authenticated `admin` role:

```bash
ENABLE_PRIVATE_REVIEW_SOURCES=1 \
ENABLE_VTT_GUIDANCE_RETRIEVAL=1 \
ENABLE_VTT_GUIDANCE_IN_ANSWER=1 \
<local app start command>
```

Public, anonymous, beta, developer, dev, and backstage requests never open the VTT index. Gear, entity/history, forum-wisdom, guardrail, and deterministic-fretboard questions are ineligible. Missing, corrupt, unsigned, or version-mismatched indexes fail closed and leave the base response unchanged.

Protected-preview activation is a separate deployment decision. This implementation does not enable flags, change deployment configuration, or authorize beta/public access.

## Status and removal

Metadata-only status:

```bash
.venv/bin/python scripts/vtt_guidance.py status
```

Safe purge preview:

```bash
.venv/bin/python scripts/vtt_guidance.py purge
```

The dry run resolves exactly `corpus-private/vtt-guidance-v2/`, reports its file count, and prints the required confirmation token. It rejects symlinks and path escapes. A confirmed purge is:

```bash
.venv/bin/python scripts/vtt_guidance.py purge --confirm DELETE-VTT-GUIDANCE-V2
```

For a full product break:

1. Clear all three VTT flags.
2. Restart the app and verify the answer event reports VTT guidance as disabled without index access.
3. Run the purge dry run and, if desired, the exact confirmed purge.
4. Rerun the SGF API/UI and world-class answer regression checks.

Purging removes only the generated v2 directory. It does not delete or modify raw `~/Documents/vtt-test` material.
