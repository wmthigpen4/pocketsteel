# Lane 06 - Voicing Identifier Mode

## Task Summary

Requested a new E9 Fretboard Explorer mode that lets a learner choose key, copedent, fret, strings, and pedal/lever state, then see the computed notes, intervals, likely voicing/chord name, function, confidence, and per-string changes.

Completed a narrow frontend-only slice:

- Added `Voicing identifier` to Explorer mode.
- Added a mode-specific panel with fret input, string-set input, common grip chips, and pedal/lever control chips.
- Computes final notes from the selected copedent and fret using existing Explorer tuning/control helpers.
- Identifies common triads/sevenths/sus/diminished/partial voicings conservatively.
- Renders a matching SVG highlight/card/detail from one synthetic computed row.
- Shows per-string before/after/control details.
- Hides normal row filters, fret range filter, top-label filter, and pedal/lever impact preview in this mode.
- Preserves existing Single grip, Harmonized scale path, and Single-note finder behavior.

Intentionally not changed:

- Backend Explorer generation, answer routing, retrieval, corpus, Chroma, embeddings, scraping, auth, DNS, deployment, or visual assets.
- No frontend fake tab generation.
- No new API endpoint.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-0843-06-voicing-identifier-mode.md`

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
- `git diff --check`

Local browser smoke:

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-identifier-local-2`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-identifier-local-2`
- Exact URL the user should use: protected-preview URL after Lane 12 restart/smoke
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: pre-commit local working tree
- Version endpoint: not checked for local UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local file-backed page and focused UI checks
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant to this local Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this Explorer smoke
- Who should test this URL: Codex locally; Lane 12/user on protected preview after commit
- Do not test these URLs: none
- Known caveats: local browser smoke does not prove protected-preview cache freshness

Local smoke results:

- Explorer loaded and exposed `Voicing identifier` in Explore mode.
- Default G / fret 3 / strings 3-4-5 / open computed notes `B, G, D` and identified `G` / `I function in G`.
- B+C computed notes `C, A, E` and identified `Am` / `ii function in G`.
- Invalid `3-3-11` string entry showed a clear validation message and removed stale highlight.
- SVG rendered one matching highlight for the computed voicing.
- No `[object Object]` appeared.

## Integration Notes

- The feature uses existing client-side copedent data from `ui/e9-fretboard-explorer-data.js`.
- `ui/e9-fretboard-explorer.html` bumps the Explorer script cache-bust to `voicing-identifier-20260627`.
- The computed voicing row is explicitly frontend presentation over the validated copedent profile; it does not claim RAG/source generation.

## Risk Assessment

Risk: medium-low.

Reason:

- Change is scoped to Explorer UI and tests.
- The chord identifier is intentionally conservative but still a first-slice heuristic. Ambiguous voicings can have alternate readings.
- Protected preview must be restarted/smoked to prove the new cache-busted script is live.

Rollback:

- Revert the scoped commit to remove the mode and restore the previous Explorer script cache-bust.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-0843-06-voicing-identifier-mode.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files shown by `git status --short`
- `README.md`
- `corpus_metadata/**`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/**`
- raw corpus/private/source/generated assets

## Recommended Next Lane

Lane 12 protected-preview restart/smoke, then Lane 15/user smoke of the Explorer mode.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12: restart protected preview and smoke `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-identifier-<commit>` to verify `Voicing identifier` loads, computes G 3-4-5 open and B+C, and shows no stale script.
