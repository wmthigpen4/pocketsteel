# Play Songs catalog pipeline — Phase 1 implementation

## Task summary

Implemented Phase 1 of the Play Songs catalog pipeline. The public Songs API is
now a publication registry rather than a prospect list: only candidates that
pass screening, rights, master, timeline, E9 lesson, QA, and publication gates
can appear in Starter Songs.

The implementation adds:

- versioned JSON Schemas for `SongCandidate` and `RightsRecord`;
- non-public candidate and rights registries;
- deterministic structural, checksum, gate-order, rights, and publication
  validation;
- a CLI that reports the exact next or rejected gate for every candidate;
- a runtime publication gate tying the public manifest to the internal
  published-candidate registry;
- Amazing Grace as the SHA-256-pinned golden published fixture;
- a rejected record for the unsuitable synthesized Saints preview;
- an exact, rights-verified Hard Times open recording candidate stopped at the
  musical master gate instead of being prematurely authored or published.

The public catalog now contains Amazing Grace only. Hard Times and Saints do not
appear as disabled or broken cards.

## Candidate pipeline evidence

`.venv/bin/python scripts/song_catalog_pipeline.py --check` reports:

- registry: PASS;
- Amazing Grace: `published`;
- Hard Times Come Again No More: `rights_cleared`, next gate `master`;
- When the Saints synthesized preview: `rejected` at the master gate.

The exact Grant Raymond Barrett Hard Times Commons master was downloaded to
ignored staging for technical inspection only:

- SHA-256: `1b426cde50c02809a4463403b2076dae43df64944dbce25880fbb23daab579a8`;
- duration: `145946 ms`;
- format: stereo Ogg Vorbis, 44.1 kHz, approximately 97 kbps;
- detected ending silence: approximately 3.08 seconds;
- staged path: `tmp/song-candidates/hard-times-grant-barrett.ogg` (ignored and
  not staged).

Its exact master and CC BY 3.0 candidate-use basis are pinned in the internal
registries. Musical master approval remains pending by design.

## Files changed

- `docs/play-songs-catalog-pipeline.md`
- `docs/song-practice-v1.md`
- `docs/handoffs/task-completions/2026-08-02-1443-18-play-songs-catalog-pipeline-plan.md`
- `docs/handoffs/task-completions/2026-08-02-1454-18-play-songs-catalog-pipeline-phase1.md`
- `scripts/song_catalog_pipeline.py`
- `steel_guitar_rag/song_catalog_pipeline.py`
- `steel_guitar_rag/song_practice.py`
- `steel_guitar_rag/resources/song_catalog/candidates.json`
- `steel_guitar_rag/resources/song_catalog/rights_records.json`
- `steel_guitar_rag/resources/song_catalog/song_candidate.schema.json`
- `steel_guitar_rag/resources/song_catalog/rights_record.schema.json`
- `tests/test_song_catalog_pipeline.py`
- `tests/test_song_practice.py`
- `tests/test_api_search.py`

No bundled audio, authentication rule, Cloudflare configuration, deployment,
corpus, vector store, private training source, saved copedent, or user track was
changed. Candidate and rights records are not exposed by the public API.

## Tests and checks

- Candidate registry CLI `--check`: PASS.
- Focused pipeline, Song Practice, UI, and API suite: `373 passed in 19.28s`.
- Full repository regression suite: `1556 passed in 78.04s`.
- Ruff on changed Python files: PASS.
- Python compile check: PASS.
- JavaScript syntax checks for Songs and player: PASS.
- JSON parse checks for both schemas: PASS.
- `git diff --check` on the exact Phase 1 paths: PASS.

Local browser smoke at
`http://127.0.0.1:8897/songs?v=phase1-catalog-1`:

- Starter Songs rendered exactly one card: Amazing Grace;
- the card contained the expected `/play/amazing-grace-guided` action;
- no disabled review buttons rendered;
- Hard Times and Saints did not appear;
- My Tracks remained available;
- browser warning/error log was empty.

The disposable local server shut down cleanly after smoke.

## Risks

Low runtime risk. The catalog fails closed if the internal registries are
invalid. Future songs cannot bypass the pipeline through the older
`learnerReady` manifest field alone.

The Hard Times candidate has not passed musical audition. Its verified license
and clean technical fingerprint do not prove that it is a suitable master. This
is expected gate behavior, not an incomplete publication claim.

## Human decision needed

No engineering decision is needed for Phase 1. A musical reviewer must audition
the exact Hard Times master before it may advance to timeline authoring. It may
be approved or rejected; the pipeline does not require that candidate to ship.

Production activation was not attempted. This avoids another unexpected macOS
administrator sign-in. Activation remains a separate protected-preview action.

## Safe-to-stage exact file list

- `docs/play-songs-catalog-pipeline.md`
- `docs/song-practice-v1.md`
- `docs/handoffs/task-completions/2026-08-02-1443-18-play-songs-catalog-pipeline-plan.md`
- `docs/handoffs/task-completions/2026-08-02-1454-18-play-songs-catalog-pipeline-phase1.md`
- `scripts/song_catalog_pipeline.py`
- `steel_guitar_rag/song_catalog_pipeline.py`
- `steel_guitar_rag/song_practice.py`
- `steel_guitar_rag/resources/song_catalog/candidates.json`
- `steel_guitar_rag/resources/song_catalog/rights_records.json`
- `steel_guitar_rag/resources/song_catalog/song_candidate.schema.json`
- `steel_guitar_rag/resources/song_catalog/rights_record.schema.json`
- `tests/test_song_catalog_pipeline.py`
- `tests/test_song_practice.py`
- `tests/test_api_search.py`

## Files that must not be staged

- `tmp/song-candidates/` and its downloaded audio candidates;
- `docs/handoffs/task-completions/integration-status.md`;
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`;
- unrelated historical handoffs and generated files;
- releases, logs, credentials, secrets, corpus data, vector stores, and private
  training data.

## Recommended next lane

Lane 15 / musical review should audition or reject the exact Hard Times master.
In parallel, Lane 05/06 can begin Phase 2 device-only analysis and correction
using the same confirmed-timeline contract.

## Commit readiness

Ready for exact-path staging and commit. The unrelated dirty worktree and
ignored candidate audio must remain untouched.
