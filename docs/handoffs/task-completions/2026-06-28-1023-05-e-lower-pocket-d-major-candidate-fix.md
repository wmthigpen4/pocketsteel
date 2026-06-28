# E-lower Pocket D Major Candidate Fix

## Task Summary

- Requested: fix Chord / Voicing Finder so `5-7-8` with E-lower appears as a valid D major candidate in broad legitimate-grip search.
- Completed: fixed the Explorer Chord / Voicing Finder candidate limiting/filtering path so complete high-confidence non-core grip candidates are preserved in broad searches, removed the old Core-only E-lower pocket special-case, added filter exclusion explanations, removed the duplicate lower candidate list, and refreshed the Explorer script cache-bust for protected preview.
- Intentionally not changed: backend/API, corpus, Chroma/vector stores, embeddings, scraper output, source records, auth, DNS, deployment, private data, brand assets, or generated corpus/private artifacts.

## Pass/Warn/Fail

Pass.

Warning: local `/api/version` still reports runtime SHA `a6abc61`, so the protected result is cache-busted static/browser verification for the Explorer UI, not proof of a Python runtime restart to `67f6823`.

## Why The User Was Correct

On standard E9 at fret 3 with strings `5-7-8` and E-lower:

- String 5: B raised by fret 3 = D.
- String 7: F# raised by fret 3 = A.
- String 8: E raised by fret 3 = G, lowered by E-lower to F#.
- Pitch set: D, A, F# = D major.
- In key of G, this is the V major chord.

The previous UI path could validate the grip, but the Chord / Voicing Finder broad result cap and Core/E-lower filter behavior could keep the candidate from surfacing clearly in the target user-smoke path.

## What Changed

- Added a deterministic Chord Finder candidate limiter that:
  - sorts candidates consistently,
  - keeps broad result caps,
  - preserves complete high-confidence non-core candidates such as E-lower pockets when they match the target chord.
- Changed Core grip vocabulary semantics so Core no longer silently injects E-lower pocket groups.
- Kept `All legitimate` and `E-lower pockets` capable of surfacing `5-7-8` E-lower candidates.
- Added user-facing exclusion explanations:
  - Open-only: hidden because it requires E-lower.
  - Core-only: registered as E-lower pocket vocabulary; choose E-lower pockets or All legitimate.
  - Fret-range exclusion: fret 3 outside selected range.
- Removed duplicate Chord Finder candidate cards from the lower row-list area while preserving the primary active-results card rail and selected detail/fretboard behavior.
- Updated the Explorer static script version to `e-lower-pocket-d-major-20260628` so protected preview loads the corrected script.

## 5-7-8 E-lower D Major Behavior

Verified locally and in protected-preview static/browser smoke:

- Root: D.
- Quality: Major.
- Grip vocabulary: All legitimate.
- Pedal/lever scope: All practical.
- Candidate present: `chord-finder:D:5-7-8:3:E-lower`.
- Card includes:
  - Fret 3.
  - Strings 5-7-8.
  - Pedals/levers: With E-lower.
  - Grip: E-lower pocket.
  - Why: `An E-lower pocket grip...`.
  - Present: root D, 3rd F#, 5th A.
  - Omitted: none.
  - Confidence: high.
- Fretboard marker present for fret 3 strings 5, 7, and 8.
- String-action marker labels render as `5`, `7`, and `8E`; no `S` prefixes.

## Filters Tested

- `All legitimate` + `All practical`: includes the fret-3 `5-7-8` E-lower D major candidate.
- `Open only`: excludes the candidate and explains that it requires the E-lower lever.
- `Core`: excludes the candidate and explains that it is E-lower pocket vocabulary.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded from existing authenticated browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `67f6823`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `git_sha=a6abc61`, `git_branch=feature/answer-api`, `server_started_at=2026-06-27T17:30:30.410070+00:00`
- If version endpoint missing, how version is inferred: not missing; runtime is stale, static/browser URL loaded corrected Explorer script `e9-fretboard-explorer.js?v=e-lower-pocket-d-major-20260628`
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes, but it redirects to the app shell and drops query strings
- Whether `/ui/steel-guitar-rag-mock.html` works: yes, root redirected there
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: root `/` for cache-busted Explorer validation, because root redirects and drops query strings
- Known caveats: protected smoke verifies static/browser behavior, not strict Python runtime version at `67f6823`

## Local Smoke Result

Local URL: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=e-lower-d-major-local-20260628`

Result: pass.

Verified:

- Page loaded.
- Chord / Voicing Finder mode loaded.
- D + Major + All legitimate + All practical includes one `5-7-8` E-lower fret-3 card.
- Card text includes E-lower pocket, fret 3, strings 5-7-8, root D / 3rd F# / 5th A, and omitted none.
- Fretboard marker exists.
- String labels show `5`, `7`, `8E`.
- Open-only excludes the candidate with the E-lower reason.
- Core excludes the candidate with the E-lower pocket vocabulary reason.
- Lower duplicate candidate list is empty.
- No `[object Object]`.
- Browser console warnings/errors: none.

## Protected-Preview Smoke Result

Protected URL: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823`

Result: pass with runtime-version caveat.

Verified:

- Page loaded after Cloudflare Access authenticated session.
- Script assets include `e9-fretboard-explorer.js?v=e-lower-pocket-d-major-20260628`.
- D + Major + All legitimate + All practical includes one `5-7-8` E-lower fret-3 card.
- Card/detail text includes E-lower pocket, fret 3, strings 5-7-8, root D / 3rd F# / 5th A, and omitted none.
- Fretboard marker exists.
- String labels show `5`, `7`, `8E`.
- Open-only excludes the candidate with the E-lower reason.
- Core excludes the candidate with the E-lower pocket vocabulary reason.
- Lower duplicate candidate list is empty.
- No `[object Object]`.
- Browser console warnings/errors: none.

## Files Changed

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-28-1023-05-e-lower-pocket-d-major-candidate-fix.md`

## Tests And Checks Run

- `git status --short`
- `git diff --check`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-music-rules.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py -q` - 4 passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - 42 passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 24 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 36 passed
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` - 5 passed
- Local browser smoke at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=e-lower-d-major-local-20260628` - pass
- Protected-preview browser smoke at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823` - pass with runtime-version caveat

## Integration Notes

- Implementation commit: `67f6823 fix: surface e-lower pocket major candidates`.
- No backend/API contract changed.
- No corpus/RAG/source-card behavior changed.
- No deployment/restart performed.
- User-smoke URL is ready for this specific Explorer check:
  `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823`

## Risk Assessment

Low.

The change is scoped to Explorer Chord / Voicing Finder UI candidate filtering/rendering and focused frontend regression coverage. Main risk is product interpretation of whether Core should include E-lower pockets. This slice implements the current user prompt: Core excludes, All legitimate/E-lower pockets include, and exclusions explain why.

Rollback: revert implementation commit `67f6823`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-28-1023-05-e-lower-pocket-d-major-candidate-fix.md`
- `docs/handoffs/task-completions/integration-status.md` if refreshed in the follow-up docs commit

Implementation files are already committed in `67f6823`.

## Files That Must Not Be Staged

- Broad parked dirty/untracked files shown by `git status --short`, including corpus/provenance/RAG scripts, source-inbox files, private/generated reports, `ui/brand/`, `public/brand/`, `Neon Sign/`, and unrelated docs.

## Recommended Next Lane

Lane 12 or user smoke: manually verify the protected Explorer URL with:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e-lower-pocket-d-major-67f6823`

Use Chord / Voicing Finder:

- Root: D
- Quality: Major
- Grip vocabulary: All legitimate
- Pedals/levers scope: All practical

Expected: `5-7-8` with E-lower appears at fret 3 as D major with marker labels `5`, `7`, `8E`.

## Commit Readiness

Safe to commit for the handoff/status docs only.
