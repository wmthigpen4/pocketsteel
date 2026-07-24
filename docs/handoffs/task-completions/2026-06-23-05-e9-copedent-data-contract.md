# 2026-06-23 - Lane 05 - E9 Copedent Data Contract

## Pass / Warn / Fail

Pass.

Reason: implemented the backend/data contract for selectable E9 copedents, chart-ready copedent data, and copedent-aware pedal/lever impact preview data. Focused backend tests and requested API tests pass. Broad unrelated dirty work remains parked and was not staged.

## Branch / HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `bbf385d docs: define E9 copedent selector contract`
- Final HEAD / commit hash if committed: exact commit hash reported in the final task response after exact-path commit.

## Task Summary

Requested: implement the first backend/rules data contract for E9 copedent selection and visual copedent chart data.

Completed:

- Added a deterministic E9 copedent model module.
- Added selectable data for:
  - `emmons-e9-basic` / `Emmons E9`, enabled and app-default.
  - `day-e9-basic` / `Day E9`, enabled.
  - `my-copedent-e9` / `My Copedent (E9)`, disabled with `Coming soon in Backstage`.
- Added chart-ready payload data:
  - rows for strings 1-10 with open notes,
  - ordered control columns,
  - per-cell `from -> to`, semitone direction, and raise/lower arrow data.
- Wired Explorer payloads to include `selected_copedent` and `filters.available_copedents`.
- Made `control_impact_preview` consume the selected copedent profile so Day mode changes pedal order without changing named A/B/C semantics.
- Kept existing deterministic Explorer row generation behavior on the Emmons/default named changes.
- Added focused tests for Emmons, Day, disabled My Copedent, C6 exclusion, chart payload shape, and right-knee change representation.

Intentionally not changed:

- No UI files were edited.
- No static Explorer data file was regenerated.
- No custom copedent editor or persistence was implemented.
- No C6 support was added.
- No corpus, SGF, Chroma, embeddings, scraping, private-source, source-inbox, auth, DNS, deployment, tunnel, or asset files were touched by this slice.

## Data Contract Summary

New module:

- `steel_guitar_rag/e9_copedents.py`

Key helpers:

- `available_e9_copedents()`
- `selectable_e9_copedents()`
- `get_e9_copedent_profile(copedent_id=None)`
- `selected_copedent_payload(copedent_id=None)`
- `control_changes_for_profile(copedent_id=None)`
- `control_labels_for_profile(copedent_id=None)`
- `control_types_for_profile(copedent_id=None)`
- `control_order_for_profile(copedent_id=None)`

Explorer payload additions:

- `selected_copedent`
- `filters.available_copedents`
- `control_impact_preview.selected_copedent_id`

`selected_copedent` includes:

- `id`
- `label`
- `instrument`
- `status`
- `pedal_order`
- `strings`
- `controls`
- `chart.rows`
- `chart.columns`
- `available_options`
- `source_context`
- `warnings`

## Default Copedent Choice

Default is `Emmons E9`:

- ID: `emmons-e9-basic`
- Status: `app-default`
- Pedal order: `A`, `B`, `C`

Day mode:

- ID: `day-e9-basic`
- Pedal order: `C`, `B`, `A`
- Named pedal semantics remain unchanged:
  - `A` still raises strings 5 and 10 B to C#.
  - `B` still raises strings 3 and 6 G# to A.
  - `C` still raises string 4 E to F# and string 5 B to C#.

My Copedent:

- ID: `my-copedent-e9`
- Disabled.
- Disabled reason: `Coming soon in Backstage`.

## Files Touched

Created:

- `steel_guitar_rag/e9_copedents.py`
- `docs/handoffs/task-completions/2026-06-23-05-e9-copedent-data-contract.md`

Changed:

- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`

Deleted:

- None.

Generated artifacts:

- None.

## Checks Run

Passed:

- `git diff --check`
- `.venv/bin/python -m py_compile steel_guitar_rag/api.py steel_guitar_rag/fretboard_examples.py steel_guitar_rag/fretboard_explorer.py steel_guitar_rag/tab_engine.py steel_guitar_rag/answer_intent_classifier.py steel_guitar_rag/e9_copedents.py`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - `37 passed`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - `25 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - `5 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'copedent or pedal or lever or fretboard or tab_example' -q`
  - `49 passed, 230 deselected`
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - `279 passed`

Not run:

- Full `pytest`; the requested checks were run, and this slice is scoped to deterministic Explorer/copedent data. Existing integration-status caveats for unrelated broad/static/UI areas remain parked.

## Risks

Low to medium.

- The backend contract is deterministic and tested, but UI has not rendered the new selector/chart yet.
- The right-knee controls are represented as explicit app-profile changes, not universal E9 truth. The payload includes warnings that copedents vary.
- `ui/e9-fretboard-explorer-data.js` was not regenerated, so browser-visible Explorer data will not include this contract until Lane 06/12 updates the frontend/static data path.

Rollback:

- Revert the scoped commit containing `steel_guitar_rag/e9_copedents.py`, `steel_guitar_rag/fretboard_explorer.py`, and `tests/test_fretboard_explorer.py`.

## Blockers

None for backend contract completion.

Lane 06 must still render the selector/chart and decide whether static Explorer data regeneration belongs in its UI slice.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/e9_copedents.py`
- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-23-05-e9-copedent-data-contract.md`

## Files That Must Remain Unstaged

- Existing unrelated dirty files, including but not limited to:
  - `README.md`
  - corpus metadata/source policy files
  - root RAG/corpus helper scripts
  - `docs/handoffs/task-completions/integration-status.md` unless a separate Repo Steward integration refresh stages it
  - `tests/test_frontend_answer_ui.py`
  - `ui/e9-fretboard-explorer-data.js`
  - `ui/e9-fretboard-explorer.html`
  - `ui/e9-fretboard-explorer.js`
  - `ui/brand/`, `public/`, `Neon Sign/`, generated assets
  - `source-inbox/`, `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, scraper outputs, deployment/auth/DNS/secrets/private-source files

## Recommended Next Lane

Lane 06 UX/UI Design.

Exact recommended prompt:

```text
Lane 06 UX/UI Design:
Render the E9 copedent selector and chart from the backend contract committed in Lane 05. Use `selected_copedent`, `filters.available_copedents`, `selected_copedent.chart.rows`, and `selected_copedent.chart.columns` from `build_explorer_payload()`. Do not create a duplicate UI-only copedent table. Emmons E9 is default, Day E9 changes physical pedal order to C-B-A, and My Copedent (E9) is disabled with “Coming soon in Backstage.” Keep the existing Explorer row rendering and pedal/lever impact preview behavior intact. Do not touch corpus, Chroma, embeddings, scraping, auth, DNS, deployment, private sources, or C6. Add focused frontend tests and write a handoff.
```

## Commit Readiness

Safe to commit.

Required exact-path commit message:

```text
feat: add E9 copedent data contract
```
