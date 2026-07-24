# Shared Explorer Music Rules Boundary

Pass/warn/fail: pass

## Task Summary

Requested: add the smallest shared deterministic music-rules boundary for the E9 Fretboard Explorer so pitch, interval, notation, chord/voicing naming, confidence, omitted-tone handling, and grip semantics do not fork between the Explorer UI, answer generation, and future tab/fretboard sync.

Completed:
- Added `ui/e9-music-rules.js` as a shared deterministic browser/CommonJS rules module.
- Moved shared Explorer music logic out of `ui/e9-fretboard-explorer.js` and into that boundary.
- Updated the Explorer HTML script order so the rules boundary loads before the Explorer controller.
- Added focused regression coverage for the required acceptance cases.

Intentionally not changed:
- No backend API schema or `/api/answer` behavior.
- No corpus, Chroma/vector store, embeddings, scraping, source records, auth, DNS, secrets, deployment config, or source cards.
- No broad UI redesign.
- No persistent custom-copedent behavior.

## Boundary Introduced

New shared module: `ui/e9-music-rules.js`

The module exposes deterministic rules for:
- E9 final note calculation from string/fret/controls.
- Note normalization and pitch-class display spelling.
- Major/natural-minor scale-degree mapping.
- Notes, NNS, Roman, and Numbers notation labels.
- Major, minor, diminished, half-diminished, major-7, dominant-7, minor-7, 9th, and minor-9 chord/voicing naming.
- Omitted-tone labels and confidence.
- Extended-chord quality gates so partial/rootless voicings are not overclaimed.
- Grip tier and role metadata already modeled by the Explorer.

The Explorer now calls this shared boundary for the migrated rules instead of owning those definitions locally.

## Files Changed

- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1152-05-shared-explorer-music-rules-boundary.md`

Generated artifacts: none.

Deleted files: none.

## Duplicated Logic Reduced

Moved from `ui/e9-fretboard-explorer.js` into `ui/e9-music-rules.js`:
- Core, advanced, two-string, extended, and dominant-grip sets.
- Grip registry and grip tier metadata.
- E9 open strings and control-change note resolution.
- Chord-quality patterns and parsing helpers.
- Scale-sequence notation tables.
- Interval formatting, NNS/Roman/Numbers notation, and scale-degree lookup.
- Voicing identification, omitted-tone handling, confidence, and function labels.
- Chord Finder target parsing and quality gating.

## Tests And Checks

Commands run:
- `git status --short`
- `git branch --show-current`
- `node --check ui/e9-music-rules.js` - pass
- `node --check ui/e9-fretboard-explorer.js` - pass
- `node --check ui/e9-fretboard-explorer-data.js` - pass
- `node --check ui/answer-client.js` - pass
- `node --check ui/pedal-steel-fretboard.js` - pass
- `.venv/bin/python -m py_compile tests/test_frontend_answer_ui.py` - pass
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - pass, `24 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - pass, `38 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - pass, `34 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` - pass, `5 passed`
- `git diff --check` - pass

One earlier frontend test run failed because `notationLabelForFinalNote` existed in the shared module but was not exported. The export was added and the suite passed afterward.

## Acceptance Coverage

Focused tests now cover:
- String 3 fret 3 no pedals/no levers = B.
- String 3 fret 3 with B pedal = C.
- String 5 fret 3 with A pedal = E.
- String 9 fret 3 no pedals/no levers = F.
- Key F / fret 3 / strings 4-6-10 / A+B = C major / V in F.
- Key G / fret 3 / strings 5-6-9 / A+B = Fmaj7(no3), not dominant/V7.
- Key G / fret 3 / strings 5-7-9 / A+B = Fmaj7(no5), not dominant/V7.
- F-A-Eb = F7(no5) / dominant-7 color, not Fmaj7.
- V7 in G resolves to D7.
- Imaj7 in F resolves to Fmaj7.
- Cmin9/Cm9 partial/rootless gating.
- Missing 3rd lowers confidence.
- Missing 5th can remain practical.
- 9th-string involvement alone does not imply dominant 7.
- Notes, NNS, Roman, and Numbers notation render consistently.

## Smoke Target

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8899/ui/e9-fretboard-explorer.html?v=shared-music-rules-local-smoke-20260627`
- Cache-busted URL tested: `http://127.0.0.1:8899/ui/e9-fretboard-explorer.html?v=shared-music-rules-local-smoke-20260627`
- Exact URL the user should use: protected preview after Lane 12 updates/restarts the preview
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: static `python3 -m http.server` on `127.0.0.1:8899`
- Expected backend port: 8899 for this local static smoke only
- Expected git HEAD: local working tree before commit
- Version endpoint: not applicable for static browser smoke
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local uncommitted working tree served by static file server
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this Explorer static smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer static smoke
- Who should test this URL: Codex locally; Lane 12/user should test protected preview after update
- Do not test these URLs: do not treat API fallback or stale protected preview as proof of this change
- Known caveats: browser automation runs page evaluation in an isolated context, so direct page-global checks were not reliable; DOM script tags, rendered rows, no console errors, and no `[object Object]` were verified. The local static server logged 404s for `brand/pedal-steel-fretboard-background.svg` and `favicon.ico`; the missing public fretboard background route is a known unrelated caveat and was not changed here.

Local browser smoke result:
- The Explorer loaded with script tags for `e9-music-rules.js?v=shared-music-rules-20260627` and `e9-fretboard-explorer.js?v=shared-music-rules-20260627`.
- Rendered row count: 33.
- Browser console errors: none.
- `[object Object]`: not present.

Protected-preview smoke status:
- Not run in this lane. No protected-preview restart/deploy action was requested or performed.

## Remaining Duplication

Remaining UI-only logic stays in `ui/e9-fretboard-explorer.js`:
- DOM state/rendering.
- filter behavior.
- event sync UI.
- row-card/detail rendering.
- interaction state.

Backend Explorer row generation remains in `steel_guitar_rag/fretboard_explorer.py`. This slice does not yet make Python and browser share one generated artifact or one source file. It creates the smallest browser-side shared boundary for current UI/future answer-tab sync without a broad rewrite.

## Risks / Blockers

Risk: medium-low.

Reasoning:
- The module extraction is substantial by line count but localized to Explorer music rules and covered by focused tests.
- Protected preview has not been updated or smoked at the new commit.
- Python backend Explorer generation still has its own deterministic logic; future work may need a generated JSON contract or Python/JS parity test if backend answer generation starts consuming these same rules directly.

Rollback:
- Revert the commit restoring `ui/e9-fretboard-explorer.js` to own its local rule definitions and removing the new script include.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1152-05-shared-explorer-music-rules-boundary.md`

## Files That Must Not Be Staged

- Any unrelated dirty files shown by `git status --short`.
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/`
- `.wrangler/`
- deployment/auth/DNS/secrets files
- `public/`
- `ui/brand/`
- `Neon Sign/`
- raw design assets
- generated private/source/corpus reports

## Recommended Next Lane

Lane 15 QA / Answer Eval: run focused Explorer smoke against the committed local build.

Then Lane 12 Self-Hosted Deployment: update/restart protected preview if approved, verify `/api/version` or static asset version as appropriate, and run protected-preview smoke at the Explorer URL.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 15 prompt:

```text
Lane 15: QA the shared Explorer music-rules boundary from the latest commit. Verify the E9 Fretboard Explorer still loads, chord/voicing finder names major 7 vs dominant 7 correctly, notation modes remain consistent, and no [object Object] or console errors appear. Use the handoff docs/handoffs/task-completions/2026-06-27-1152-05-shared-explorer-music-rules-boundary.md.
```
