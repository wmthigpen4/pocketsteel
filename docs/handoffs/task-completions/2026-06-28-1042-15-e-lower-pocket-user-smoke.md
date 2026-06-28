# 2026-06-28 10:42 - Lane 15 E-lower Pocket User Smoke

## Pass / Warn / Fail

Pass / Warn.

The protected-preview browser smoke passed for the latest E9 Fretboard Explorer E-lower pocket D major fix and legitimate grip vocabulary behavior. The warning is the known runtime-version caveat: local `/api/version` still reports `a6abc61`, and the protected browser could not open `/api/version` directly because the browser blocked the endpoint with `net::ERR_BLOCKED_BY_CLIENT`. This smoke verifies the cache-busted protected static/browser Explorer behavior, not a strict Python runtime restart to `67f6823`.

## Task Summary

Requested: run Codex-driven user smoke for the current Explorer build at the protected-preview URL, verify the full checklist, record pass/warn/fail, refresh integration status, and commit docs/status only unless a scoped non-RED regression required a fix.

Completed:

- Inspected repo guidance, integration status, and the latest relevant Explorer handoffs.
- Confirmed current branch and HEAD.
- Confirmed current HEAD contains `67f6823`.
- Ran the protected-preview browser smoke at the exact cache-busted URL.
- Ran required focused checks.
- Refreshed integration status.

Intentionally not changed:

- No implementation files.
- No tests.
- No protected-preview restart/deployment.
- No auth, DNS, scraping, embeddings, Chroma/vector stores, raw corpus, private transcripts, source records, secrets, Cloudflare Access policy, or deployment config.

## Branch And HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `c7018dc`
- Final HEAD: reported after the scoped docs/status commit.
- Required implementation commit: `67f6823 fix: surface e-lower pocket major candidates`
- `git merge-base --is-ancestor 67f6823 HEAD`: passed

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded from existing authenticated in-app browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `c7018dc`, containing `67f6823`
- Version endpoint: `http://127.0.0.1:8770/api/version`; protected browser endpoint `https://app.steelguitarrag.com/api/version`
- Version endpoint result: local returned `{"git_sha": "a6abc61", "git_branch": "feature/answer-api", "server_started_at": "2026-06-27T17:30:30.410070+00:00", "python_module": "pocketsteel.api", "retrieval_mode": "hybrid_private_first", "auth_provider": "cloudflare_access"}`; protected browser endpoint was blocked with `net::ERR_BLOCKED_BY_CLIENT`
- If version endpoint missing, how version is inferred: static/browser behavior inferred from the exact protected URL plus loaded Explorer script `e9-fretboard-explorer.js?v=e-lower-pocket-d-major-20260628`
- Whether app root `/` works: yes, root redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes for the app shell; not valid for exact cache-busted Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user may use the exact direct Explorer URL above
- Do not test these URLs: root `/` for exact Explorer cache-busted validation, because root drops the query string
- Known caveats: stale runtime-version endpoint; this is protected static/browser smoke, not API fallback

## Basic Load

Pass.

- Explorer loaded at the exact protected URL.
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`.
- Cloudflare Access did not block the page.
- Explorer script loaded as `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.js?v=e-lower-pocket-d-major-20260628`.
- Shared music rules script loaded as `https://app.steelguitarrag.com/ui/e9-music-rules.js?v=legitimate-grip-vocabulary-20260628`.
- No `[object Object]`.
- No relevant console warnings/errors captured.
- Chord / Voicing Finder mode selectable.
- Root / Quality controls present and worked.
- Grip vocabulary control present and worked.
- Pedals / levers scope control present and worked.

## Main Acceptance Case

Pass.

State tested:

- Explore Mode: Chord / Voicing Finder
- Key: G
- Root: D
- Quality: Major
- Grip vocabulary: All legitimate
- Pedals / levers scope: All practical

Observed:

- `5-7-8` with E-lower appears.
- Fret: `3`.
- Card text: `D`, strings `5-7-8`, `With E-lower`, `E-lower pocket`.
- Notes / present tones: root `D`, 3rd `F#`, 5th `A`.
- Omitted tones: `none`.
- Confidence: high.
- Selected detail shows notes `D, A, F#`.
- Selected detail shows string actions:
  - String 5 no change `D -> D`.
  - String 7 no change `A -> A`.
  - String 8 E-lower `G -> F#`.
- Candidate renders on the SVG fretboard.
- Selecting the candidate selects the fretboard highlight for the candidate.
- String labels ON shows `5`, `7`, `8E`.
- No `S`-prefix labels.
- No internal `E-raise/E-lower` marker labels.

Function in G was not shown on this Chord / Voicing Finder card/detail surface, so the checklist item `V if function/context is shown` is not applicable to the current UI copy.

## Filter / Exclusion Behavior

Pass.

- Open-only hides the `5-7-8` E-lower candidate.
- Open-only shows an E-lower requirement/exclusion explanation.
- Core hides the `5-7-8` E-lower candidate.
- Core shows E-lower pocket vocabulary / All legitimate guidance.
- Switching back to All legitimate / All practical restores the broader candidate set.
- When the selected E-lower candidate is excluded, selection moves to a visible core candidate; no hidden stale selected card remains.
- No `[object Object]`.

## Duplicate Card Check

Pass.

- Candidate rail/list appears once.
- Observed `48` chord-map cards in the primary active-results rail for D major / All legitimate / All practical.
- Observed `0` lower `.explorer-row-button` candidate-list entries in Chord / Voicing Finder mode.
- Observed `1` selected-detail panel.
- Selected detail is separate from the all-candidate rail and does not duplicate the full list.

## String Label Toggle

Pass.

- String labels OFF keeps selected markers clean; the marker text set showed static strings/fret markers only.
- String labels ON shows marker labels on visible/selected marker bubbles.
- For the main selected E-lower candidate, labels include `5`, `7`, `8E`.
- Changed strings use number + lever/pedal shorthand; unchanged strings use number only.
- E-lower marker shorthand is `E`.
- E-raise marker shorthand appears as `F`.
- D-lower marker shorthand appears as `D` (`2D`, `9D`).
- G lever shorthand appears as `G` (`1G`, `6G`).
- No `S3`/`S4`/`S5` labels.
- No `[object Object]`.

## Broader Vocabulary Sanity Checks

Pass.

Voicing Identifier browser checks:

- `4-6-10` with A+B at fret 3: accepted as `C chord (IV function in G)`, notes `G, C, E`, with alternate spread-grip explanation.
- `3-5-9` open at fret 3: accepted as `Bdim chord (iii function in G)`, notes `B, D, F`, with 9th-string context/watch-out copy.
- `5-6-7` with B only: accepted and classified conservatively as `D7 color / partial V7 in G`, notes `D, C, A`.
- `3-5-8` with B+C: accepted as `C chord (IV function in G)`, notes `C, E, G`, with spread-grip explanation.
- `5-6-7` with A+B: remains a path grip; classified as `Am chord (ii function in G)`.
- `6-7-10` with A+B: remains a lower path grip; classified as `Am chord (ii function in G)`.
- Non-core grips show tier/context and why-use-this explanations.
- Default/core views remain uncluttered; broader vocabulary is opt-in.
- No `[object Object]`.

## Regression Checks

Pass.

- `Fmaj7` remains major-7/rootless where appropriate and is not mislabeled as dominant/V7.
- `D` + `Dominant 7` resolves to D7 candidates; this covers `V7 in G` behavior for the structured Root / Quality picker.
- `Cmin9` / `Cm9` under Core shows a clean no-practical-candidate state with `0 candidates`; no parser failure or object-string output.
- Structured Root / Quality picker still has no required free-text parser box.
- Chord finder map view shows mapped candidates.
- Card/marker synchronization works.
- Notation selector near the fretboard works; `NNS` can be selected.
- Pitch register control is present and does not clutter the map in the default Off state.
- No `[object Object]`.
- No relevant console warnings/errors.

## Root Behavior

Pass with expected caveat.

- Tested root: `https://app.steelguitarrag.com/?v=e-lower-pocket-d-major-67f6823`
- Final URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- Root redirects to the app shell and drops the query string.
- This is expected; use the direct Explorer URL for exact cache-busted Explorer validation.

## API Fallback Status

Not used.

This report is based on authenticated protected-preview browser smoke. Local `/api/version` was checked only to record the known runtime-version caveat.

## Bugs Found

None.

## Fixes Made

None.

## Screenshots

Not captured. This smoke used DOM state, visible browser interaction, selected detail text, SVG marker text, and console logs.

## Tests And Checks Run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git merge-base --is-ancestor 67f6823 HEAD`
- `curl -sS http://127.0.0.1:8770/api/version || true`
- `git diff --check`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-music-rules.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py -q` -> 4 passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` -> 42 passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` -> 24 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` -> 36 passed
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` -> 5 passed
- Protected-preview browser smoke at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823`
- Protected-preview root behavior check
- Protected `/api/version` browser open attempt, blocked with `net::ERR_BLOCKED_BY_CLIENT`

## Files Touched

- `docs/handoffs/task-completions/2026-06-28-1042-15-e-lower-pocket-user-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files Intentionally Left Unstaged

All unrelated dirty/untracked work remains untouched, including broad docs, corpus/source/provenance files, RAG scripts, source-inbox files, generated/private outputs, public/brand assets, `ui/brand/`, `Neon Sign/`, and deployment-adjacent artifacts.

## Risk Assessment

Low for static/browser Explorer behavior.

Remaining risk: strict runtime-version proof remains caveated until the protected-preview runtime reports a commit containing `67f6823` or later. Current observed behavior is valid for cache-busted static Explorer UI smoke.

## Human Decision Needed

No for this smoke result.

Optional product decision: decide whether strict `/api/version` runtime certification is required before broader user review. The Explorer behavior itself passed in the protected browser.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-28-1042-15-e-lower-pocket-user-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files.
- Corpus/source/provenance files, Chroma/vector stores, embeddings, private transcripts, source-inbox files, secrets/env files, auth/DNS/deployment config, `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, and generated private reports.

## Recommended Next Lane

Lane 01 / Repo Steward only if another coordination/status commit is needed after this docs/status commit. Otherwise the exact Explorer URL is ready for focused user review.

## Commit Readiness

Safe to commit docs/status only.
