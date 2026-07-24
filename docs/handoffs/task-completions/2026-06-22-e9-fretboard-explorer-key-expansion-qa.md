# E9 Fretboard Explorer Key Expansion QA

## Task Summary

Lane 15 QA-reviewed the committed E9 Fretboard Explorer backend key expansion before any UI exposure work.

Completed:

- Read the required governance docs, integration snapshot, Lane 05 key-expansion handoff, prior Explorer backend QA handoffs, current backend implementation, and focused tests.
- Verified the current branch and HEAD.
- Preserved unrelated dirty/untracked worktree state.
- Added narrow backend QA coverage for expanded-key invariants and sharp-key learner-facing display spelling.
- Ran focused Explorer tests, full pytest, row-summary validation, and whitespace checks.

Intentionally not changed:

- No UI exposure for expanded keys.
- No corpus, Chroma/vector stores, embeddings, scraper output, deployment, auth, DNS, assets, private source data, source-inbox data, or unrelated dirty/untracked files were modified.
- No backend implementation code was changed.

## Pass/Warn/Fail

Pass.

The backend key expansion is ready for Lane 06 UI exposure work.

## Current Branch

`feature/answer-api`

## Current HEAD

`be3be01 docs: refresh e9 explorer integration status`

## Key-Expansion Commit Under QA

`e90e157 feat: expand e9 fretboard explorer keys`

## Governance / Startup Notes

Read or inspected:

- `AGENTS.md`
- `agents.md`
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-22-e9-explorer-integration-status-refresh.md`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-key-expansion.md`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-qa.md`
- `docs/handoffs/task-completions/2026-06-22-1345-05-e9-explorer-key-aware-display-spelling.md`
- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`

Missing files from requested governance list:

- `PLAN.md`
- `plan.md`

Task classification:

- Lane: `15 QA / Answer Eval`
- Mode: GREEN, test/handoff-only QA coverage.

Protected paths and unrelated dirty files constrained the work. Broad unrelated modified/untracked files remain parked and were not staged.

## Files Inspected

- `AGENTS.md`
- `agents.md`
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-22-e9-explorer-integration-status-refresh.md`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-key-expansion.md`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-qa.md`
- `docs/handoffs/task-completions/2026-06-22-1345-05-e9-explorer-key-aware-display-spelling.md`
- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`

## Files Changed

- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-key-expansion-qa.md`

## QA Coverage Added

Added focused tests for:

- Sharp-key learner display spelling:
  - `C#` major scale display: `C# D# E# F# G# A# B#`.
  - `F#` major scale display: `F# G# A# B C# D# E#`.
  - `C#` I chord row keeps canonical validation note `F` while learner-facing display uses `E#`.
- Expanded-key invariants for `C`, `D`, `F`, `Bb`, and `Eb`:
  - Payloads validate.
  - Rows remain pitch validated.
  - Frets stay `0-24`.
  - Strings stay `1-10`.
  - No `rag`, `corpus`, or `sgf` refs are introduced.
  - Major and natural-minor scale degrees remain ordered `[1, 2, 3, 4, 5, 6, 7, 1]`.
  - `5-7-8` rows remain `advanced_pocket`, `advanced`, and `e_lower_pocket`.
  - Three-note diminished rows remain `partial`, omit `b7`, and include the warning that the grip does not include b7.

Existing coverage retained:

- G behavior and compatibility helpers.
- C/D/F/Bb major representative rows.
- C natural minor display flats.
- G natural minor display spelling.
- E9 mechanical labels such as `F#`, `D#`, `G#`, and `Eb/D#`.
- Per-string A/B/C/E-raise/E-lower mechanics.
- B+C invalidity on unsupported groups.
- No RAG/corpus dependency for G deterministic rows.

## Validated Keys

Focused tests and row-summary validation covered:

- `G`
- `C`
- `C#`
- `D`
- `Eb`
- `F`
- `F#`
- `Bb`

Representative row-summary validation:

```text
G rows 106; I 4-5-6 fret 3; major scale G A B C D E F#; natural minor G A Bb C D Eb F
C rows 105; I 4-5-6 fret 8; major scale C D E F G A B; natural minor C D Eb F G Ab Bb
D rows 106; I 4-5-6 fret 10; major scale D E F# G A B C#; natural minor D E F G A Bb C
F rows 106; I 4-5-6 fret 1; major scale F G A Bb C D E; natural minor F G Ab Bb C Db Eb
Bb rows 106; I 4-5-6 fret 6; major scale Bb C D Eb F G A; natural minor Bb C Db Eb F Gb Ab
Eb rows 106; I 4-5-6 fret 11; major scale Eb F G Ab Bb C D; natural minor Eb F Gb Ab Bb Cb Db
C# rows 105; I 4-5-6 fret 9; major scale C# D# E# F# G# A# B#; natural minor C# D# E F# G# A B
F# rows 106; I 4-5-6 fret 2; major scale F# G# A# B C# D# E#; natural minor F# G# A B C# D E
```

## Display Spelling Results

Pass.

- Flat keys use flat learner-facing spelling where musically correct:
  - `Bb` major displays `Bb C D Eb F G A`.
  - `Eb` major displays `Eb F G Ab Bb C D`.
  - `C` natural minor displays `C D Eb F G Ab Bb`.
- Sharp keys use sharp learner-facing spelling where musically correct:
  - `C#` major displays `C# D# E# F# G# A# B#`.
  - `F#` major displays `F# G# A# B C# D# E#`.
- Canonical pitch validation remains separate from display spelling:
  - `C#` I row canonical notes include `F`, while display notes spell that pitch as `E#`.
  - `Bb` I row canonical notes include `A#`, while display notes spell that pitch as `Bb`.
  - `Eb` I row canonical notes include `D#`/`A#`, while display notes spell them as `Eb`/`Bb`.

## Advanced Swap Results

Pass.

- Advanced swaps remain separate from beginner core grips:
  - Core grips: `3-4-5`, `4-5-6`, `5-6-8`, `6-8-10`.
  - Advanced swaps: `5-6-7`, `6-7-10`, `5-7-8`.
- For representative expanded keys, every `5-7-8` row remained:
  - `harmony_type: advanced_pocket`
  - `difficulty_tier: advanced`
  - `position_family: e_lower_pocket`
  - `levers: ["E-lower"]`
  - per-string change on string 8 from `E` to `Eb/D#`

Observed `5-7-8` rows:

- `G`: frets `8`, `20`
- `C`: fret `13`
- `D`: frets `3`, `15`
- `F`: frets `6`, `18`
- `Bb`: frets `11`, `23`
- `Eb`: frets `4`, `16`
- `C#`: fret `14`
- `F#`: frets `7`, `19`

The single-row cases are expected duplicate-suppression outcomes when octave-equivalent rows collapse onto the same validated fret.

## Partial Voicing Labeling Results

Pass.

- Three-note `1-b3-b5` diminished rows remain `chord_quality: diminished`.
- They remain `voicing_status: partial`.
- They retain `omitted_intervals: ["b7"]`.
- They warn that the grip does not include b7.
- No generated row was treated as a full m7b5 without b7.

## Internal Canonical / Mechanical Results

Pass.

- Internal canonical pitch validation remains unchanged and separate from display spelling.
- E9 mechanical/copedent labels still preserve sharp-oriented spellings where appropriate:
  - Open string labels retain `F#`, `D#`, and `G#`.
  - E-lower still exposes `Eb/D#`.
- Per-string controls remain local to affected strings:
  - A affects strings `5`, `10`.
  - B affects strings `3`, `6`.
  - C affects strings `4`, `5`.
  - E-raise/E-lower affect E strings `4`, `8`.
- A+B and B+C do not become global whole-grip changes.

## No RAG / Corpus Dependency

Pass.

- The Explorer module remains deterministic and imports pitch helpers only.
- Focused tests assert no `rag`, `corpus`, or `sgf` source references are introduced in representative expanded-key rows.
- No Chroma/vector, corpus, scraper, `/api/answer`, UI, deployment, auth, DNS, or private-source files were changed.

## Tests Run

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
.venv/bin/python - <<'PY'
from collections import Counter
from steel_guitar_rag.fretboard_explorer import build_explorer_payload, validate_explorer_payload
keys = ['G','C','D','F','Bb','Eb','C#','F#']
for key in keys:
    payload = build_explorer_payload(key)
    validate_explorer_payload(payload)
    rows = payload['positions']
    h = Counter(row['harmony_type'] for row in rows)
    print(key, 'rows', len(rows), 'harmony', dict(h))
    print('  major scale:', ' '.join(payload['query']['display_scale_notes']['major']))
    print('  natural minor scale:', ' '.join(payload['query']['display_scale_notes']['natural_minor']))
    i456 = next(row for row in rows if row['scale_type']=='major' and row['harmony_type']=='three_string_diatonic' and row['string_group']=='4-5-6' and row['chord_function']=='I')
    print('  I 4-5-6:', i456['fret'], i456['notes'], i456['display_notes'])
    pocket = [row for row in rows if row['string_group']=='5-7-8']
    print('  5-7-8:', [(row['fret'], row['difficulty_tier'], row['position_family'], row['levers'], row['per_string_changes']) for row in pocket])
    dims = [row for row in rows if row['chord_quality']=='diminished' and set(row['intervals'].values()) == {'1','b3','b5/#11'}]
    print('  partial diminished rows:', len(dims), sorted({tuple(row['omitted_intervals']) for row in dims}), sorted({row['voicing_status'] for row in dims}))
PY
git diff --check
```

Results:

- `tests/test_fretboard_explorer.py -q`: `21 passed`
- Full pytest: `801 passed`
- Row-summary validation: passed for all inspected keys
- `git diff --check`: passed

## Issues Found

No product blockers.

No backend implementation defects found.

## Blockers

None.

## Risks

Low-to-medium.

Reasons:

- The backend expansion is deterministic, pitch-validated, and isolated.
- Existing and added tests cover representative flat keys, sharp keys, C natural minor, G compatibility, advanced swaps, partial diminished labeling, and no RAG/corpus dependency.
- UI still does not expose expanded keys; Lane 06 must consume the generalized backend payload deliberately rather than assuming the current static G-oriented fixture is complete.

Rollback:

- Revert the exact key-expansion backend/test commit if needed.
- Revert this QA test/handoff commit if the added tests need adjustment.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-key-expansion-qa.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked worktree files.
- UI files.
- Corpus/private corpus files.
- Chroma/vector stores.
- Embeddings.
- Scraper output.
- Deployment/auth/DNS/secrets files.
- `source-inbox` raw/provenance files.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated handoffs/docs.

## Recommended Next Lane

Lane 06 UX/UI Design.

## Commit Readiness

Safe to commit.

## Recommended Next Prompt

```text
Lane 06: expose the expanded deterministic E9 Fretboard Explorer keys in the browser UI selector. Use the generalized `build_explorer_payload(key)` backend contract and preserve the current G behavior, key-aware display fields, advanced/core grip separation, no dense SVG text, and no RAG/corpus source implication. Do not touch corpus, Chroma, embeddings, scraping, deployment, auth, DNS, private source data, or unrelated dirty files. Add focused UI tests and browser smoke for representative keys after implementation.
```
