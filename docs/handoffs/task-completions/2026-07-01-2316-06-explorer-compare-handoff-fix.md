# 2026-07-01 23:16 Lane 06 - Explorer Compare Handoff Fix

## Task Summary

Requested: fix the Explorer Handoff v1 protected-smoke blocker where static answer-page fretboard cards exposed `Explore this position` but did not expose `Compare in Explorer`.

Completed:
- Fixed static fretboard card handoff rendering so `Compare in Explorer` is available even when the backend payload has no top-level `fretboard.query`.
- Added fallback root/quality derivation from normalized position metadata and simple position labels such as `G major`.
- Removed the previous multi-position gate so a one-position static grip answer can still open a broader Explorer comparison context.
- Refreshed the answer-page fretboard renderer cache-bust to `pedal-steel-fretboard.js?v=explorer-compare-fix-20260702b`.
- Added focused regression coverage for label-only and single-position static payloads.

Intentionally not changed:
- No backend, answer routing, corpus, Chroma/vector store, embeddings, scraping, auth, DNS, deployment config, private transcript, licensing metadata, secret, or unrelated asset changes.
- No new Explorer abstraction.
- No melody input or tab generation changes.

## Files Changed

- `ui/pedal-steel-fretboard.js`
  - Preserves normalized `root` and `quality` metadata.
  - Derives root/quality from position labels when explicit metadata is missing.
  - Renders `Compare in Explorer` for one-position static payloads when a root can be inferred.
- `ui/steel-guitar-rag-mock.html`
  - Refreshed `pedal-steel-fretboard.js` cache-bust to `explorer-compare-fix-20260702b`.
- `tests/test_pedal_steel_fretboard_ui.py`
  - Added coverage for no-query payloads and single-position label-only payloads.
- `tests/test_frontend_answer_ui.py`
  - Updated expected answer-page fretboard renderer cache-bust.
- `docs/handoffs/task-completions/2026-07-01-2316-06-explorer-compare-handoff-fix.md`
  - This handoff.

Deleted files: none.

Generated artifacts: none.

## Tests And Checks

Passed:
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/answer-client.js`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q --tb=short`
  - `37 passed`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q --tb=short`
  - `24 passed`
- `git diff --check`

## Local Browser Smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8899/ui/steel-guitar-rag-mock.html?access=beta_user&v=explorer-compare-fix-local-final`
- Cache-busted URL tested: `http://127.0.0.1:8899/ui/steel-guitar-rag-mock.html?access=beta_user&v=explorer-compare-fix-local-final`
- Exact URL the user should use: pending protected-preview smoke after commit/restart
- Auth required: no
- Auth provider: none for local controlled-states server
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8899`
- Expected backend port: `8899`
- Expected git HEAD: starting HEAD `f2b100f`; final commit pending at handoff creation
- Version endpoint: not checked for the local controlled-states server
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: current working tree served by `scripts/serve_answer_smoke.py`
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: existing local server redirects to `/ui/steel-guitar-rag-mock.html`
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally; Lane 12/user after protected-preview refresh
- Do not test these URLs: root URL for exact cache-busted verification
- Known caveats: local static deterministic answers include a `No sources returned` source-note shell for some static prompts; this slice did not change source-note behavior.

Local smoke command:

```bash
PYTHONPATH=. \
STEEL_RAG_CHROMA_PATH="$HOME/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma" \
STEEL_RAG_CHROMA_COLLECTION="steel_guitar_unified" \
.venv/bin/python scripts/serve_answer_smoke.py --controlled-states --port 8899
```

Local answer prompt results:

| Prompt | Result |
| --- | --- |
| `Show me a G major grip.` | PASS: static fretboard rendered, no tab, `Explore this position` and `Compare in Explorer` present. Compare href: `/ui/e9-fretboard-explorer.html?mode=chord&root=G&quality=major&source=answer`. |
| `Where is G on E9?` | PASS: multi-position static fretboard rendered; every visible selected/detail state exposed both position and compare links. |
| `Show me a 5-7-8 G grip.` | PASS: static 5-7-8 fretboard rendered, no tab, both handoff actions present. |
| `Show me a G to C move.` | PASS: Movement Lesson Card rendered with tab and fretboard; `Explore related path` still present; deterministic movement source cards remained absent. |
| `Show me a 1 4 5 1 move in G.` | PASS: Movement Lesson Card rendered with tab and fretboard; `Explore related path` still present. |
| `What are good Fender Steel King settings?` | PASS: no stale fretboard, movement card, tab, or Explorer handoff links. Source cards rendered for the source-backed gear answer. |

Local Explorer direct-load checks:

| URL | Result |
| --- | --- |
| `http://127.0.0.1:8899/ui/e9-fretboard-explorer.html?mode=single&source=answer&fret=3&strings=4-5-6&grip=4-5-6&v=explorer-compare-fix-local-final` | PASS: mode `single`, key `G`, fretboard present, no `[object Object]`, no page-level horizontal overflow. |
| `http://127.0.0.1:8899/ui/e9-fretboard-explorer.html?mode=chord&root=G&quality=major&source=answer&v=explorer-compare-fix-local-final` | PASS: mode `chord`, root `G`, quality `major`, fretboard present, no `[object Object]`, no page-level horizontal overflow. |
| `http://127.0.0.1:8899/ui/e9-fretboard-explorer.html?mode=path&source=movement-card&key=G&progression=I-IV&v=explorer-compare-fix-local-final` | PASS: mode `path`, key `G`, fretboard present, no `[object Object]`, no page-level horizontal overflow. |

Mobile/narrow check:
- Viewport: `390x844`.
- Prompt: `Show me a G major grip.`
- Result: PASS. Static fretboard rendered, no tab, both handoff actions present, no `[object Object]`, and no page-level horizontal overflow.

Console:
- No relevant warning/error logs during the local smoke matrix.

Screenshots:
- None captured. Browser smoke used DOM/state checks.

## Root Cause

`Compare in Explorer` depended on `model.query.root/chord/key` and required `model.allHighlights.length >= 2`.

Protected/local static grip payloads can be one-position fretboard payloads without top-level `query` and without explicit `root`/`quality` fields. The selected position did carry learner-facing label text such as `G major`, enough to derive a safe comparison URL, but the previous code did not use that label. As a result, `compareExplorerParams()` returned `null` and the compare link was omitted.

## Integration Notes

- `Explore this position` behavior is unchanged.
- `Compare in Explorer` now opens the existing Explorer Chord / Voicing Finder mode with safe query params:
  - `mode=chord`
  - `root=<derived root>`
  - `quality=<derived-or-default quality>`
  - `source=answer`
- Existing Explorer query startup remains fail-soft; unsupported params are ignored safely.
- Movement Lesson Card `Explore related path` was not changed.

## Risk Assessment

Risk: low.

Why:
- Frontend-only change.
- Root/quality fallback is conservative and only drives the Explorer handoff URL.
- If a root cannot be inferred, `Compare in Explorer` still does not render.
- Existing no-query Explorer behavior is unchanged.

Rollback notes:
- Revert this commit to restore the previous stricter compare-link gating and script cache-bust.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/pedal-steel-fretboard.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-07-01-2316-06-explorer-compare-handoff-fix.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked work, including but not limited to:
- `README.md`
- `corpus_metadata/**`
- `source-inbox/**`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- unrelated untracked docs/handoffs/assets
- `docs/handoffs/task-completions/integration-status.md` unless performing a separate integration refresh

## Recommended Next Lane

Lane 01 exact-path commit for this scoped fix, then Lane 12 protected-preview restart/smoke.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit this scoped fix, then run protected-preview smoke against:
- `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?access=beta_user&v=explorer-compare-fix`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compare-fix`
