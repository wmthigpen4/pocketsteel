# 2026-06-24 10:36 - Lane 05 - E9 Pedal/Lever Impact Preview Contract

## Task Summary

Implemented a deterministic backend Explorer data contract for pedal/lever impact previews. The Explorer payload can now describe what each standard E9 pedal/lever changes, and each validated row can describe the active-control effect in that row's chord context.

Completed:
- Added top-level `control_impact_preview` to `build_explorer_payload(key)`.
- Added row-level `control_impacts` to every `ExplorerRow`.
- Added deterministic note, semitone, interval-effect, and key-context helpers.
- Added tests for top-level key-context previews and row-level B+C chord-context impacts.

Intentionally not changed:
- No UI/frontend changes.
- No generated `ui/e9-fretboard-explorer-data.js` update.
- No corpus, Chroma, embeddings, scraper, auth, DNS, deployment, source-inbox, private-source, or visual asset changes.
- No RAG/source usage for Explorer musical truth.

## Files Changed

- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-24-1036-05-e9-pedal-lever-impact-preview-contract.md`

## Backend Contract Added

Top-level Explorer payload now includes:

```json
{
  "control_impact_preview": {
    "type": "e9-pedal-lever-impact-preview",
    "version": "1.0",
    "instrument": "E9",
    "copedent_profile": {
      "id": "mvp-e9-standard",
      "status": "assumed",
      "label": "Standard 10-string E9"
    },
    "key_context": {
      "key": "G",
      "major_scale": ["G", "A", "B", "C", "D", "E", "F#"],
      "natural_minor_scale": ["G", "A", "Bb", "C", "D", "Eb", "F"]
    },
    "controls": []
  }
}
```

Each control includes:
- `id`
- `label`
- `control_type`
- `affected_strings`
- `string_impacts`
- `summary`
- `validation_status`

Each top-level `string_impacts` item includes:
- `string`
- `before_note`
- `after_note`
- `semitone_delta`
- `interval_effect`
- `before_key_context`
- `after_key_context`

Each Explorer row now includes `control_impacts`. Row-level impacts are scoped to active controls on that validated row and include:
- `before_open_note`
- `after_open_note`
- `before_note`
- `after_note`
- `display_before_note`
- `display_after_note`
- `before_interval`
- `after_interval`
- `semitone_delta`
- `interval_effect`
- `resulting_context`

## Deterministic Behavior Examples

For key `G`, top-level `A` pedal preview:
- affected strings: `5`, `10`
- string 5: `B -> C#`
- semitone delta: `+2`
- interval effect: `raises 2 semitones`
- against G major: `B` is scale degree `3`; `C#` is outside the major scale and interval `b5/#11`.

For key `G`, top-level `E-lower` preview:
- affected strings: `4`, `8`
- string 4: `E -> Eb/D#`
- semitone delta: `-1`
- interval effect: `lowers 1 semitone`
- against G natural minor: `Eb` is scale degree `6`.

For the validated G-major `ii` row on strings `4-5-6` with `B+C`:
- row validates as `A minor`.
- `B` pedal impact on string 6: `B -> C`, interval `2/9 -> b3`.
- `C` pedal impact on string 4: `G -> A`, interval `b7 -> 1`.
- `C` pedal impact on string 5: `D -> E`, interval `4/11 -> 5`.

## Tests And Checks

Passed:
- `.venv/bin/python -m py_compile steel_guitar_rag/fretboard_explorer.py`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
- `git diff --check`

Results:
- `tests/test_fretboard_explorer.py`: 34 passed
- `tests/test_api_contract.py`: 5 passed

Full pytest not run for this slice. Rationale: this is a narrow deterministic Explorer payload/test change; integration status already records known unrelated full-suite caveats around static/UI output.

## Integration Notes

The new contract is backend/data-model only. Lane 06 should decide how to expose:
- top-level all-control preview (`control_impact_preview`)
- selected-row active-control preview (`positions[*].control_impacts`)

The static browser fixture `ui/e9-fretboard-explorer-data.js` was not regenerated in this lane. If Lane 06 needs browser-visible data, regenerate or update the fixture in that lane with exact-path staging.

## Risk Assessment

Risk: medium-low.

Why:
- The change adds new payload fields without removing existing fields.
- Existing Explorer row validation and API contract tests pass.
- The main compatibility risk is that UI code may ignore the new fields until Lane 06 wires them.

Rollback:
- Revert the `control_impact_preview` and `control_impacts` additions in `steel_guitar_rag/fretboard_explorer.py`.
- Revert the new focused tests in `tests/test_fretboard_explorer.py`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-24-1036-05-e9-pedal-lever-impact-preview-contract.md`

## Files That Must Not Be Staged

Do not stage parked unrelated dirty/untracked files, including:
- README/docs/provenance/legal/source-policy edits unrelated to this slice.
- Corpus metadata and source-inbox metadata.
- RAG/corpus helper scripts.
- Private/corpus-adjacent scripts and data.
- `public/`, `ui/brand/`, `Neon Sign/`, deployment assets, generated visual assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, scraper outputs, secrets, or private source data.

## Commit Readiness

Safe to commit.

## Recommended Next Lane

Lane 01 Repo Steward exact-path commit, then Lane 06 UI implementation.

## Downstream Prompts

### 1. Repo Steward Commit

```text
Lane 01 Repo Steward:
Run ExactPathCommit for docs/handoffs/task-completions/2026-06-24-1036-05-e9-pedal-lever-impact-preview-contract.md.
Commit only:
- steel_guitar_rag/fretboard_explorer.py
- tests/test_fretboard_explorer.py
- docs/handoffs/task-completions/2026-06-24-1036-05-e9-pedal-lever-impact-preview-contract.md
Use commit message:
feat: add e9 pedal lever impact preview contract
Do not stage unrelated parked files.
```

### 2. Lane 06 UI Prompt

```text
Lane 06 UX/UI Design:
Use the backend contract from docs/handoffs/task-completions/2026-06-24-1036-05-e9-pedal-lever-impact-preview-contract.md.
Expose the Explorer pedal/lever impact preview without changing backend logic.
Show top-level control impacts and selected-row active-control impacts. Preserve existing Explorer behavior, filters, and fretboard rendering.
Do not touch corpus, Chroma, embeddings, scraping, auth, DNS, deployment, source-inbox, or private data.
Run focused frontend tests and browser smoke where practical. Write a Lane 06 handoff.
```

### 3. Lane 15 Smoke Prompt

```text
Lane 15 QA / Answer Eval:
Smoke the E9 Explorer pedal/lever impact preview after Lane 06 UI wiring.
Verify A/B/C/E-raise/E-lower show affected strings, before/after notes, semitone effect, key-context scale-degree implications, and selected-row chord-context impacts.
Verify no regression in existing Explorer filters, selected cards, localized SVG clusters, and answer-page fretboards.
Write a Lane 15 handoff.
```

### 4. Lane 12 Protected-Preview Smoke Prompt

```text
Lane 12 Self-Hosted Deployment:
After Lane 06 and Lane 15 pass locally, restart protected preview using the documented current command.
Verify /api/version matches the expected HEAD.
Run protected-preview browser smoke on the Explorer URL with cache bust.
Include the full Smoke Target block and write a Lane 12 handoff.
```

### 5. User Smoke Prompt

```text
User smoke:
Open the protected-preview Explorer URL from the Lane 12 handoff.
Select G major rows with no pedals, B+C rows, A/B rows, and E-lower pocket rows.
Confirm the impact panel explains affected strings, before/after notes, interval effect, and scale/chord implications.
Report any confusing wording or missing controls.
```

### 6. Integration-Status Refresh Prompt

```text
Lane 01 Repo Steward:
After protected-preview and user smoke pass, refresh docs/handoffs/task-completions/integration-status.md.
Include current HEAD, runtime HEAD, smoke URLs, test results, remaining caveats, dirty worktree summary, and whether user smoke may continue.
Do not broad-stage parked files.
```
