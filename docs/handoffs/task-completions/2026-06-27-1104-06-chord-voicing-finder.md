# 2026-06-27 11:04 - Lane 06 Chord / Voicing Finder

## Task Summary

Pass.

Added a deterministic `Chord / Voicing Finder` mode to the E9 Fretboard Explorer. The new mode reverses the existing Voicing Identifier workflow: users can enter a desired chord or function such as `Fmaj7`, `Cmin9`, or `V7 in G`, then see practical E9 fret/string/control candidates ranked by completeness, grip practicality, control scope, and omitted tones.

Intentionally not changed:
- Backend answer routing, RAG, corpus, Chroma/vector stores, embeddings, scraping, auth, DNS, deployment, private source data, or visual assets.
- Existing Explorer modes: Single grip, Harmonized scale path, Single-note finder, and Voicing identifier.

## Files Changed

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1104-06-chord-voicing-finder.md`

## Chord Qualities Supported

Initial finder support includes:
- major
- minor
- diminished
- minor 7 flat 5 / half-diminished
- dominant 7
- major 7
- minor 7
- dominant 9
- major 9
- minor 9
- major 6
- minor 6
- sus2
- sus4

Parser coverage added for direct chord names and key functions, including:
- `Fmaj7`, `F major 7`, `FΔ7`
- `Cmin9`, `Cm9`, `C minor 9`
- `D7`, `G9`, `Bbmaj7`
- `V7 in G`, `ii9 in Bb`, `Imaj7 in F`, `vi minor 7 in G`

## Finder And Ranking Behavior

The finder builds target chord tones from root + quality, searches practical string groups across the selected fret range and pedal/lever scope, and ranks candidates by:
- complete chord tones before partials,
- required tone coverage,
- 3rd/7th/9th importance for extended chords,
- lower omission severity,
- core grips before extended/two-string/advanced grips,
- control-scope practicality,
- lower fret preference as a secondary tiebreaker.

Cards and details show:
- likely voicing label,
- confidence,
- fret,
- strings,
- pedals/levers,
- notes,
- present chord tones,
- omitted tones,
- grip type,
- explanation and warnings.

Major 7 and dominant 7 are kept distinct. Partial/rootless candidates are labeled as partial and list omitted tones; the UI no longer exposes numeric interval warnings such as `omitted 0`.

## Local Browser Smoke Result

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-local-2`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-local-2`
- Exact URL the user should use: protected-preview URL after Lane 12 refresh, suggested `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-<commit>`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `187df4b` at implementation start
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree files loaded through cache-busted static URL
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not required for this Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer smoke
- Who should test this URL: Codex locally; Lane 12/user on protected preview after commit
- Do not test these URLs: unversioned Explorer URL for cache-sensitive smoke
- Known caveats: local smoke does not prove protected-preview runtime freshness

Verified locally:
- Page loads.
- `Chord / Voicing Finder` is selectable.
- `Fmaj7` returns practical partial and complete candidates.
- `Fmaj7` candidates show present and omitted tones and do not show `F7`/dominant labels.
- `Cmin9` parses as `Cm9`; current default filters show a clear no-practical-candidate state rather than broken UI.
- `V7 in G` resolves to `D7` candidates.
- Selecting a candidate updates the selected card/detail and leaves one selected SVG highlight.
- Switching Grip vocabulary from Core to All practical changes Fmaj7 candidate breadth from 14 to 24.
- No `[object Object]`.
- No learner-facing `omitted 0`.

Protected-preview smoke result: not run in this Lane 06 implementation pass. Recommended next lane is Lane 12 protected-preview smoke against the committed cache-busted URL.

## Tests And Checks

Passed:
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` (`23 passed`)
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` (`34 passed`)
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` (`38 passed`)
- `git diff --check`

Skipped:
- `tests/test_api_contract.py` because no backend/API contract files changed.
- Full pytest because the scoped UI/fretboard/Explorer checks cover the touched files and unrelated parked work is present.

## Risks

Low-to-medium.

The feature is deterministic and scoped to the Explorer UI, but it adds non-trivial client-side search/ranking logic. The main remaining risk is product tuning of candidate ranking and whether some extended voicings should be considered too obscure for the default view. Current behavior is intentionally conservative and labels partial/rootless results.

Rollback note: revert the scoped commit or restore the previous `e9-fretboard-explorer.js` script cache-bust in `ui/e9-fretboard-explorer.html`.

## Human Decision Needed

No for this implementation slice.

Future product decisions may be useful on:
- default target chord,
- ranking weight for rootless vs complete voicings,
- which extended grips should be in default Core vs All practical vocabulary.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1104-06-chord-voicing-finder.md`

## Files That Must Not Be Staged

Do not stage unrelated parked work, including but not limited to:
- `README.md`
- `corpus_metadata/**`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `Neon Sign/**`
- `public/brand/**`
- untracked corpus, private, generated, design, deployment, or provenance files.

## Recommended Next Lane

Lane 12 protected-preview smoke after the scoped commit.

Suggested smoke URL:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-<commit>
```

Then Lane 15 can run focused QA on:
- Fmaj7 search,
- Cmin9 search,
- V7 in G function search,
- candidate ranking,
- omitted-tone labels,
- selected-card fretboard highlighting.

## Commit Readiness

Safe to commit.
