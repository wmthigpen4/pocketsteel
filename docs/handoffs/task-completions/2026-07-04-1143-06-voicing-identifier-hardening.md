# 2026-07-04 11:43 - Lane 06 - Voicing Identifier Hardening

## Task Summary

Implemented the scoped Voicing Identifier v1 hardening from `docs/handoffs/task-completions/2026-07-04-1045-18-voicing-identifier-v1-readiness-audit.md`.

Completed:
- Added explicit learner-facing voicing status handling for full, partial, color/no-3rd, rootless, ambiguous, and unsupported voicing results.
- Added present-tone, omitted-tone, alternate-reading, confidence, and warning fields to the Voicing Identifier row/card path.
- Hardened the 5-7-8 open G case so `D, A, G` is shown as `G5/add9(no3)` color/no-3rd, not as a definitive G major chord.
- Kept 5-7-8 with E-lower at fret 8 as a full G major result.
- Updated focused frontend tests for full chord, partial voicing, and no-3rd/color behavior.

Intentionally not changed:
- No backend answer routing.
- No direct note picking.
- No melody input.
- No arbitrary tab generation.
- No corpus, scraping, embeddings, Chroma/vector stores, auth, DNS, deployment config, private transcript, licensing metadata, secret, or asset changes.

## Files Changed

- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-07-04-1143-06-voicing-identifier-hardening.md`

Deleted files: none.

Generated artifacts: none.

## Tests and Checks

Passed:

```bash
node --check ui/e9-music-rules.js
node --check ui/e9-fretboard-explorer.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
git diff --check
```

Results:
- `tests/test_frontend_answer_ui.py`: 24 passed.
- `tests/test_fretboard_explorer.py`: 43 passed.

Skipped:
- Full pytest was not run; this slice touched focused Explorer/frontend voicing presentation, and the focused suites cover the changed contract/UI behavior.
- Protected-preview smoke was not run before commit; local browser smoke was completed first.

## Browser Smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-identifier-hardening-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-identifier-hardening-local`
- Exact URL the user should use: pending protected-preview commit/cache-bust
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `c301b47` plus local scoped changes
- Version endpoint: not checked for local browser smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local git diff and cache-busted route
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not required for this Explorer-only smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer-only smoke
- Who should test this URL: Codex locally; the user after protected-preview update
- Do not test these URLs: uncache-busted protected-preview Explorer URLs for this change
- Known caveats: protected preview may still serve the previous committed build until Lane 12 restart/update

Local browser smoke verified:
- Direct Explorer load works and shows six task cards.
- Voicing Identifier default full major case shows `Full chord`, present tones, and no `[object Object]`.
- 5-7-8 open G at fret 3 shows `G5/add9(no3)`, `Color voicing / no 3rd`, omitted `3rd (B)`, and a no-3rd warning.
- 5-7-8 with E-lower at fret 8 remains a full G chord.
- Static handoff URL loads useful single-grip context.
- Movement/path handoff URL loads useful path context.
- Mobile/narrow viewport loads the Voicing Identifier without `[object Object]`.
- Console had no relevant errors or warnings.

Smoke URLs:
- `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-identifier-hardening-local`
- `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?mode=single&source=answer&key=G&fret=3&strings=4-5-6&grip=4-5-6&v=voicing-identifier-hardening-local-static`
- `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?mode=path&source=movement-card&key=G&progression=I-IV&v=voicing-identifier-hardening-local-path`
- `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-identifier-hardening-local-rerun`

Screenshot notes:
- No screenshots were saved as artifacts.
- Browser DOM smoke confirmed the relevant desktop and mobile text states and console health.

## Integration Notes

- `identifyVoicing(...)` now returns display-facing fields that the Explorer can render directly:
  - `voicing_status`
  - `present_tones`
  - `omitted_tones`
  - `alternate_readings`
  - `warnings`
- The Explorer synthetic row for Voicing Identifier passes those fields through to the fretboard/card/detail renderer.
- Full chords still use the word `chord`; partial/color/no-3rd/rootless/ambiguous/unsupported cases use status-aware voicing language.
- The 5-7-8 open G case is explicitly a no-3rd color voicing. The 5-7-8 E-lower G case remains full G.

## Risk Assessment

Risk: low to medium.

Why:
- The change is scoped to frontend deterministic music-rule display and Explorer presentation.
- Focused tests and browser smoke passed.
- Remaining risk is wording/product nuance around exact labels like `G5/add9(no3)` and whether future backend/Explorer data should expose these fields from a central contract rather than the frontend rule helper.

Rollback notes:
- Revert the scoped commit touching `ui/e9-music-rules.js`, `ui/e9-fretboard-explorer.js`, `tests/test_frontend_answer_ui.py`, and this handoff.

## Human Decision Needed

No.

Optional future product decision:
- Decide whether `G5/add9(no3)` is the final learner-facing name or whether the product should prefer a softer label such as `G color voicing (no 3rd, add 9)`.

## Safe-to-Stage Exact File List

- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-07-04-1143-06-voicing-identifier-hardening.md`

## Files That Must Not Be Staged

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- Any untracked `Neon Sign/`, `source-inbox/`, `public/brand/`, `ui/brand/`, corpus/private/generated, deployment, auth, asset, or unrelated handoff files.

## Recommended Next Lane

Lane 12 protected-preview restart/smoke after the scoped commit, then user smoke against a cache-busted Explorer URL.

Suggested next prompt:

```text
Lane 12: Run protected-preview smoke for the Voicing Identifier hardening commit. Test /ui/e9-fretboard-explorer.html?v=voicing-identifier-hardening-<commit> and verify the 5-7-8 open G case shows G5/add9(no3), Color voicing / no 3rd, omitted 3rd (B), no plain G chord label, no [object Object], and no console errors.
```

## Commit Readiness

Safe to commit.
