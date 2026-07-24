# 2026-06-28 09:32 - Lane 05 Legitimate Three-String Grip Vocabulary

## Task Summary

Implemented the validated, classified, and explained 3-string E9 grip vocabulary for the E9 Fretboard Explorer.

Completed:
- Added a deterministic 3-string grip vocabulary model and audit in the backend Explorer payload.
- Registered required core, path, extended, song/tab vocabulary, and E-lower pocket grips.
- Preserved the default beginner/core view while making broader vocabulary opt-in.
- Made `5-7-8` with E-lower a first-class E-lower pocket case.
- Added UI vocabulary options for Core, Extended, Song/tab vocabulary, E-lower pockets, Two-string, and All legitimate.
- Added non-core grip explanations/watch-out text in Voicing Identifier and Chord / Voicing Finder details.
- Added no-effect control de-duplication in generated grip/finder candidates.
- Regenerated the static Explorer payload data.

Intentionally not changed:
- No corpus, Chroma, embeddings, scraping, source records, auth, DNS, deployment, private data, or design assets were touched.
- No source cards or provenance records were created for these grips.
- No protected-preview restart/deploy was performed.

## Files Changed

- `steel_guitar_rag/fretboard_explorer.py`
- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`

## Grip Vocabulary Added

Core:
- `3-4-5`
- `4-5-6`
- `5-6-8`
- `6-8-10`

Path:
- `5-6-7`
- `6-7-10`

Extended:
- `4-6-10`
- `4-6-9`
- `5-6-9`
- `3-5-6`
- `4-5-8`
- `5-8-10`

Song/tab vocabulary:
- `3-5-8`
- `3-5-9`

E-lower pocket:
- `5-7-8`

## Required Grip Cases Validated

- `5-6-7` with A+B remains allowed as path/extended vocabulary.
- `6-7-10` with A+B remains allowed as path/extended vocabulary.
- `5-6-7` with B only is accepted in Voicing Identifier and classified conservatively as a D7 color / partial V7 in G.
- `3-5-8` with B+C is accepted in Voicing Identifier and validated as C major / V in F at fret 3.
- `4-6-10` with A+B is accepted in Voicing Identifier and validated as C major / V in F at fret 3.
- `3-5-9` is accepted as song/tab vocabulary and validated as B diminished at G/fret 3.
- `5-7-8` with E-lower is accepted, classified as E-lower pocket, explained, and surfaced in Chord / Voicing Finder when E-lower pocket vocabulary plus lever scope are selected.

## 5-7-8 E-Lower Handling

`5-7-8` is no longer treated as an optional advanced afterthought. It is registered as `e-lower-pocket`, includes a plain-English explanation, includes a watch-out note that the E-lower lever must be part of the control state, and is available in Voicing Identifier and Chord / Voicing Finder.

## 120-Grip Discovery Audit

The backend audit now enumerates all 120 possible 3-string groups from strings 1-10.

Audit result:
- Total possible 3-string groups: `120`
- Registered groups: `15`
- Unclassified groups: `105`
- Hidden from default beginner/core UI: `11`
- Known required cases present: `5-7-8`, `5-6-7`, `6-7-10`, `4-6-10`, `3-5-9`, `3-5-8`

Policy:
> Calculate all 120 mechanical 3-string groups, teach registered/core groups first, and keep unclassified heuristic candidates out of beginner/default views until reviewed.

## Classification And Ranking Rules

- Core grips rank first and remain the default teaching vocabulary.
- Path grips are opt-in through Extended/Song-tab/All and remain visible in harmonized path contexts where already curated.
- Extended grips rank after path grips.
- Song/tab vocabulary ranks after extended grips.
- E-lower pockets are available through the dedicated E-lower vocabulary and All legitimate.
- Two-string vocabulary remains separate.
- Unclassified 3-string groups are not exposed as normal/default vocabulary.
- Chord / Voicing Finder removes no-effect control duplicates, so pedals/levers that do not change selected strings do not create repeated identical candidates.

## Local Browser Smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=legitimate-grip-vocabulary-local-20260628`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=legitimate-grip-vocabulary-local-20260628`
- Exact URL the user should use: pending protected-preview update
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `178fdf8` plus uncommitted local slice during smoke
- Version endpoint: not checked for local static smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree under current branch
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not required for this local Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer smoke
- Who should test this URL: Codex locally; user after protected-preview update
- Do not test these URLs: do not treat API fallback as browser smoke
- Known caveats: protected-preview smoke was not run in this lane because no deployment/restart was authorized

Smoke checks:
- Page loaded.
- Vocabulary options present: Core, Extended, Song/tab vocabulary, E-lower pockets, Two-string, All legitimate.
- Voicing Identifier accepted and classified `4-6-10` with A+B as C / V in F.
- Voicing Identifier accepted and classified `3-5-8` with B+C as C / V in F.
- Voicing Identifier accepted and classified `5-7-8` with E-lower as G / I in G and showed E-lower pocket explanation.
- Voicing Identifier accepted and classified `5-6-7` with B only as D7 color / partial V7 in G.
- Voicing Identifier accepted and classified `3-5-9` as Bdim and showed 9th-string context.
- Chord / Voicing Finder surfaced `5-7-8` E-lower pocket with E-lower pocket vocabulary plus Include levers scope.
- Default Harmonized Scale Path remained uncluttered.
- No `[object Object]`.
- Browser console errors: none.

## Tests And Checks Run

- `git status --short` - pass, unrelated dirty files remain parked.
- `git diff --check` - pass.
- `node --check ui/e9-fretboard-explorer.js` - pass.
- `node --check ui/e9-music-rules.js` - pass.
- `node --check ui/e9-fretboard-explorer-data.js` - pass.
- `node --check ui/answer-client.js` - pass.
- `node --check ui/pedal-steel-fretboard.js` - pass.
- `.venv/bin/python -m py_compile steel_guitar_rag/fretboard_explorer.py` - pass.
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py -q` - `4 passed`.
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - `42 passed`.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `24 passed`.
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `36 passed`.
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` - `5 passed`.
- `.venv/bin/python -m pytest` - `868 passed`.

## Integration Notes

- `ui/e9-fretboard-explorer-data.js` was regenerated from `steel_guitar_rag.fretboard_explorer.build_explorer_payload(...)`.
- The payload now includes `grip_vocabulary` with `three_string_entries` and `three_string_audit`.
- The UI now mirrors the shared grip vocabulary tiers in `ui/e9-music-rules.js`.
- Chord Finder E-lower pocket results require both E-lower pocket vocabulary and a lever-inclusive control scope.

## Protected Preview Smoke

Not run in this lane. No deployment/restart action was authorized. Lane 12 should run protected-preview smoke after the scoped commit is available to the protected-preview runtime.

Recommended protected-preview URL:
`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=<commit>`

## Risk Assessment

Risk: medium.

Reason:
- The change intentionally expands Explorer vocabulary and candidate search surfaces.
- Default views remain narrow/core, and no-effect control de-duplication reduces candidate spam.
- The full test suite passed, and local browser smoke passed, but protected-preview smoke still needs Lane 12.

Rollback:
- Revert the scoped commit containing the seven Explorer files and this handoff.

## Human Decision Needed

No for the implemented slice.

Future human review needed:
- Decide how to classify or reject the 105 currently unclassified 3-string combinations.
- Decide whether to expose heuristic/unusual candidates beyond registered vocabulary.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/fretboard_explorer.py`
- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-28-0932-05-legitimate-three-string-grip-vocabulary.md`

## Files That Must Not Be Staged

- All unrelated dirty files shown by `git status --short`, including repo docs, corpus metadata, raw/source-inbox files, private/corpus outputs, brand/design assets, public assets, RAG scripts, and generated report artifacts outside the safe-to-stage list.
- Do not stage `corpus-private/`, `corpus-v2/`, `source-inbox/`, Chroma/vector data, embeddings, auth/deployment/DNS files, `public/`, `ui/brand/`, `Neon Sign/`, or raw design assets.

## Recommended Next Lane

Lane 01 Repo Steward for exact-path staging/commit, then Lane 12 protected-preview smoke.

Exact next prompt:
> Lane 12: Run ProtectedPreviewSmoke for the E9 Fretboard Explorer legitimate 3-string grip vocabulary using `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=<commit>`. Verify Core/Extended/Song-tab/E-lower/All legitimate controls, Voicing Identifier required grips, Chord Finder E-lower pocket with Include levers, default path uncluttered, no `[object Object]`, and no console errors.

## Commit Readiness

Safe to commit.
