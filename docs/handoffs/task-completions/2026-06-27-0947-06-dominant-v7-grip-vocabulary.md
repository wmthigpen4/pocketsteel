# Lane 06 - Dominant 7 / V7 Grip Vocabulary UI Follow-through

## Task Summary
Requested: add learner-facing dominant 7 / V7 grip vocabulary to the E9 Fretboard Explorer, including practical 9th-string uses, glossary language, and regression coverage without changing backend routing, corpus, Chroma, embeddings, auth, DNS, deployment config, or private/source data.

Completed in this finishing slice: verified the current Explorer baseline already contains the dominant/V7 vocabulary, 9th-string grip support, glossary entries, and script cache-bust. Local browser smoke found one learner-facing label gap: an exact D7/V7 voicing on strings 4-5-6-9 was still labeled `9th-string color grip`. Patched that exact dominant-7 identifier display to show `Dominant 7 / V7 grip`, while preserving softer color-grip language for partial 9th-string colors.

Intentionally not changed: no backend rules, no Explorer data rows, no fretboard geometry, no notation math, no corpus/source/retrieval/auth/deployment files.

## Files Changed
- `ui/e9-fretboard-explorer.js`
  - In Voicing Identifier mode, exact dominant-7 identities now override the grip label to `Dominant 7 / V7 grip`.
- `tests/test_frontend_answer_ui.py`
  - Updated the D7/V7 regression assertion for fret 10 strings 4-5-6-9 to expect the dominant/V7 learner-facing grip label.

## Tests and Checks
- `node --check ui/e9-fretboard-explorer.js` - passed
- `node --check ui/e9-fretboard-explorer-data.js` - passed
- `node --check ui/answer-client.js` - passed
- `node --check ui/pedal-steel-fretboard.js` - passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - passed, 23 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - passed, 34 passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - passed, 38 passed
- `git diff --check` - passed

## Local Browser Smoke
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=dominant-v7-grips-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=dominant-v7-grips-local`
- Exact URL the user should use: protected-preview URL after Lane 12 smoke, not this local URL
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `4843e4d` before this commit
- Version endpoint: not checked for local static smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local file/browser state plus git HEAD
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant to this Explorer UI smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this Explorer UI smoke
- Who should test this URL: Codex locally; user should test protected-preview after Lane 12
- Do not test these URLs: uncache-busted Explorer URLs for this change
- Known caveats: local smoke does not prove protected-preview freshness

Smoke result:
- Explorer loaded the refreshed `e9-fretboard-explorer.js?v=dominant-v7-grips-20260627` script.
- Build Grip workflow exposed `Core triads`, `Dominant 7 / V7`, `Extended grips`, and `All practical` vocabulary controls.
- Selecting `Dominant 7 / V7` revealed D7/V7 candidates and practical 9th-string grip cards, including `4-5-6-9` at fret 10 with notes `D, A, F#, C`.
- Voicing Identifier accepted fret 10 strings 4-5-6-9 with no pedals/levers and displayed `D7`, `V7 in G`, `D, A, F#, C`, and `Dominant 7 / V7 grip`.
- Glossary contained flat-7, V7, dominant-7, and 9th-string definitions.
- No `[object Object]` appeared.
- Browser console errors: none relevant; error log empty.

## Integration Notes
- This is a learner-facing UI label correction on top of existing deterministic V7/9th-string vocabulary support.
- Exact dominant-7 matches now present as dominant/V7 grips; partial 9th-string color grips still use partial/color language to avoid overclaiming.
- No API/schema/data contract change.

## Risk Assessment
Low. The change is narrow and affects only the Voicing Identifier grip label after an already-computed dominant-7 identity. Rollback is a one-line revert plus test expectation revert.

## Human Decision Needed
No.

## Safe-to-stage Exact File List
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-0947-06-dominant-v7-grip-vocabulary.md`

## Files That Must Not Be Staged
All unrelated dirty/untracked files, especially corpus/source files, Chroma/vector data, embeddings, auth/deployment config, brand/raw assets, and the parked unrelated docs/source/code changes currently visible in `git status --short`.

## Recommended Next Lane
Lane 01 exact-path commit for this scoped UI/test/handoff slice, then Lane 12 protected-preview smoke for the cache-busted Explorer URL, then Lane 15/user smoke if protected-preview is green.

## Commit Readiness
Safe to commit.

## Suggested Next Step
After commit, run protected-preview smoke against:
`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=<commit-or-dominant-v7-cachebuster>`
