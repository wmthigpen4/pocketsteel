# Explorer Mode Home Protected Smoke

## Task Summary

Protected-preview browser smoke was run for Explorer Mode Home v1 after implementation commit `777842f feat: add explorer mode home` and integration-status refresh commit `75c45e6 docs: refresh integration status for explorer mode home`.

Completed:

- Verified the cache-busted protected Explorer page loads.
- Verified the task-first mode-home cards render.
- Verified all six task cards switch to the expected existing Explorer modes.
- Verified safe startup for static answer handoff and movement/path handoff query URLs.
- Verified app shell and root behavior.
- Verified mobile/narrow layout for the task-home layer.

Intentionally not changed:

- No implementation files were changed in this smoke pass.
- No backend, corpus, Chroma, embeddings, auth, DNS, deployment config, scraping, private transcripts, licensing metadata, secrets, or unrelated assets were touched.
- No API fallback was used as browser proof.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-777842f`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-777842f`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-777842f`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded/already authenticated in the in-app browser
- Local backend URL: not used for protected smoke
- Expected backend port: not applicable for protected URL
- Expected git HEAD: `75c45e6` for repo docs HEAD; UI implementation commit `777842f`
- Version endpoint: `https://app.steelguitarrag.com/api/version`
- Version endpoint result: `git_sha=2c8c7e`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`
- If version endpoint missing, how version is inferred: not missing
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes, with known query-string-drop caveat
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: root URL for cache-busted Explorer verification, because root redirects to app shell and drops query strings
- Known caveats: `/api/version` reports backend runtime `2c8c7e2`, not `777842f` or `75c45e6`; this smoke verifies protected static/browser behavior at the cache-busted URL, not a backend runtime restart to the latest commit.

## Files Changed

- Created: `docs/handoffs/task-completions/2026-07-02-2240-12-explorer-mode-home-protected-smoke.md`

No implementation files were changed.

## Protected Smoke Results

Main protected Explorer URL:

- URL: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-777842f`
- Result: PASS
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`
- Explorer title visible: yes
- Task-home visible: yes
- Task-card count: 6
- Default selected task: `explore-grip`
- Default mode: `single`
- Existing controls visible: yes
- Fretboard visible: yes
- No `[object Object]`: pass
- Relevant console warnings/errors: none

Scripts observed:

- `https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=explorer-harmonized-path-mode-20260626`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer-data.js?v=single-grip-octave-results-20260628`
- `https://app.steelguitarrag.com/ui/e9-music-rules.js?v=legitimate-grip-vocabulary-20260628`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.js?v=explorer-mode-home-20260702`

Task-card interaction results:

- `Find a chord`: selected and switched to `chord`
- `Find a note`: selected and switched to `note`
- `Explore a grip`: selected and switched to `single`
- `Walk a harmonized scale`: selected and switched to `path`
- `Study a movement path`: selected and switched to `path`
- `Identify a voicing`: selected and switched to `voicing`

Note:

- Single-note Finder starts in note mode without an immediate fretboard marker until note-specific state is selected. This is existing mode behavior, not a task-home regression.

Handoff query startup:

- Static answer handoff URL: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?mode=single&source=answer&key=G&fret=3&strings=4-5-6&grip=4-5-6&v=explorer-mode-home-777842f-static`
- Result: PASS. Mode `single`, selected task `explore-grip`, fretboard visible.
- Movement/path handoff URL: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?mode=path&source=movement-card&key=G&progression=I-IV&v=explorer-mode-home-777842f-movement`
- Result: PASS. Mode `path`, selected task `study-movement-path`, fretboard visible.

App shell and root:

- App shell URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=explorer-mode-home-777842f`
- Result: PASS. App shell loaded and no `[object Object]`.
- Root URL: `https://app.steelguitarrag.com/?v=explorer-mode-home-777842f`
- Result: PASS with known caveat. Root redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html` and dropped the query string.

Mobile/narrow protected smoke:

- URL: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-777842f-mobile`
- Result: PASS
- Task-home visible: yes
- Task-card count: 6
- Existing controls visible: yes
- Fretboard visible: yes
- Task grid scrolls horizontally inside its container: yes
- Page-level horizontal overflow: no
- No `[object Object]`: pass
- Relevant console warnings/errors: none

## Tests And Checks

Commands run before implementation commit:

- `node --check ui/e9-fretboard-explorer.js` - passed
- `node --check ui/e9-fretboard-explorer-data.js` - passed
- `node --check ui/pedal-steel-fretboard.js` - passed
- `node --check ui/answer-client.js` - passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `24 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `37 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - `43 passed`
- `git diff --check` - passed
- `git diff --cached --check` - passed before commit

Commands run during this protected-smoke pass:

- `git status --short` - completed; unrelated dirty/parked work remains
- `git branch --show-current` - `feature/answer-api`
- `git rev-parse --short HEAD` - `75c45e6`
- `git diff --check` - passed

## Integration Notes

- Protected static/browser behavior for Explorer Mode Home v1 is verified at the direct cache-busted Explorer URL.
- `/api/version` still reports backend runtime `2c8c7e2`; that is a runtime-version caveat, not a browser UI failure for this static Explorer smoke.
- Root `/` should not be used to verify this cache-busted Explorer UI because it redirects to the app shell and drops the query string.

## Risk Assessment

Risk: low.

Reason:

- The new task-home layer switches existing Explorer modes and states only.
- No backend or music-rule behavior changed.
- Protected browser smoke verified the page, task cards, handoff query startup, mobile layout, and console state.

Rollback:

- Revert implementation commit `777842f` if the task-home layer needs to be removed.
- Revert docs commits `75c45e6` and this handoff/status commit if only coordination text needs rollback.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-07-02-2240-12-explorer-mode-home-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Any unrelated dirty/parked files shown by `git status --short`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/` raw/provenance files
- `.wrangler/`
- DNS/deploy secrets
- `public/`
- `ui/brand/`
- `Neon Sign/`
- raw design assets

## Recommended Next Lane

Lane 15 QA / Answer Eval for focused user-smoke readiness review, or user smoke directly at:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-777842f`

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke the exact cache-busted Explorer URL and verify:

- The six task cards are visible and understandable.
- Each task card enters the expected workflow.
- Existing lower controls are still available.
- Mobile task cards are readable and not too tall.
- Static and movement answer handoff links still land in useful Explorer context.
