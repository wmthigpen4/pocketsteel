# 2026-06-18 Lane 12 Fretboard-First Static Grips Smoke

## Task Summary

Lane 12 verified the current protected-preview runtime after the fretboard-first static grip work. The task was verification only: restart the Mac-hosted protected preview from current `HEAD`, prove `/api/version` matched the runtime, smoke local API, local browser, and authenticated protected-preview browser behavior, then record the result.

No implementation files, DNS, Cloudflare Access policy, Chroma/vector data, embeddings, corpus files, source data, scraping, or deployment configuration were changed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-first-20d2f84`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-first-20d2f84`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-first-20d2f84`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; browser was past Access and the app shell loaded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `20d2f84`
- Version endpoint: `/api/version`
- Version endpoint result: `git_sha=20d2f84`, `git_branch=feature/answer-api`, `retrieval_mode=hybrid_private_first`, `auth_provider=cloudflare_access`
- If version endpoint missing, how version is inferred: not needed
- Whether app root `/` works: root route was not the target for this smoke
- Whether app root `/` is expected to work: root may redirect to the UI shell; direct `/ui` path was used to preserve cache-bust
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both Codex and the user
- Do not test these URLs: long-stale cache-bust URLs from earlier commits
- Known caveats: broad parked dirty files remain in the worktree; full pytest was not requested for this Lane 12 smoke

## Branch And Runtime

- Branch: `feature/answer-api`
- HEAD commit tested: `20d2f84 fix: render fretboard-first static grip answers`
- Recent backend commit included: `0006905 fix: prefer fretboard for static grip examples`
- Protected-preview runtime commit: `20d2f84`
- Protected-preview process: listening on `127.0.0.1:8770`
- Protected-preview cwd: repo path, `~/Documents/Steel Guitar RAG`
- Temporary local smoke server: started on `127.0.0.1:8781` for local API/browser smoke, then stopped after verification

Protected preview was restarted with the documented private-preview server command using:

```bash
PYTHONPATH=. \
STEEL_RAG_AUTH_PROVIDER=cloudflare_access \
STEEL_RAG_ANSWER_AUTH_MODE=production \
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_RETRIEVAL_DEBUG=false \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

## Local API Smoke Results

Endpoint: `http://127.0.0.1:8781/api/answer` with local dev beta-user scaffold header.

| Prompt | Expected | Actual | Result |
| --- | --- | --- | --- |
| `Show me a G major grip` | Direct prose, fretboard, no visible tab | Direct prose; `fretboard=true`; `tab=false`; one G position | Pass |
| `Show me a 4-5-6 grip` | Direct prose, fretboard, no visible tab | Direct prose; `fretboard=true`; `tab=false`; one G 4-5-6 position | Pass |
| `Show me a G chord on strings 4-5-6` | Direct prose, fretboard, no visible tab | Direct prose; `fretboard=true`; `tab=false`; one G 4-5-6 position | Pass |
| `Where is G on E9?` | Direct prose, fretboard, no visible tab | Direct G position answer; `fretboard=true`; `tab=false`; position catalog returned | Pass |
| `Show me a G to C move` | Direct prose, tab, fretboard | Direct prose; tab example `g-to-c-456-beginner`; fretboard positions for G and C partial | Pass |
| `How do I use A+B pedals?` | Direct prose, tab, fretboard | Direct prose; tab example `a-b-pedal-major-position`; fretboard position at fret 10 A+B | Pass |
| `Show me an A+B example` | Direct prose, tab, fretboard | Same A+B tab/fretboard behavior as above | Pass |
| `Show me an E-lower move` | Direct prose, tab, fretboard | Direct prose; tab example `e-lower-color-move`; matching fretboard | Pass |
| `Give me a beginner lick in G` | Direct prose, tab, fretboard; A+B on strings 5 and 6 only | Direct prose; tab example `beginner-g-two-event-lick`; A on string 5 and B on string 6; string 8 not marked | Pass |
| `What are good Fender Steel King settings?` | Normal gear answer, no stale tab/fretboard | Gear answer; sources present; `tab=false`; `fretboard=false` | Pass |
| `Tab the whole solo from Together Again` | No generated full-song tab/fretboard | Safe song-approach answer; `tab=false`; `fretboard=false` | Pass |
| `Transcribe this YouTube recording into tab` | No generated transcription tab/fretboard | Safe song-approach answer; `tab=false`; `fretboard=false` | Pass |
| `Give me the full tab for a modern copyrighted song` | No generated full-song tab/fretboard | Safe song-approach answer; `tab=false`; `fretboard=false` | Pass |

## Local Browser Smoke Results

URL: `http://127.0.0.1:8781/ui/steel-guitar-rag-mock.html?access=beta_user&v=fretboard-first-20d2f84`

- App shell loaded.
- Q&A input was available through local dev scaffold access.
- Static grip prompts rendered the fretboard SVG and no visible tab card.
- Movement prompts rendered both the tab block and fretboard SVG.
- Tab blocks used monospace styling, preserved spacing with `white-space: pre`, and horizontally scrollable overflow.
- The beginner G lick rendered A+B on strings 5 and 6; no string 8 A/B implication was visible.
- Negative prompts rendered no generated tab and no generated fretboard.
- Returning to the stage after each prompt cleared tab/fretboard state; no stale tab or stale fretboard remained.
- Browser console errors: none.

Known local-only caveat: the temporary local server logged 404s for `/brand/pedal-steel-fretboard-background.svg`, matching the known unrelated public fretboard background route caveat. This did not block the tested UI behavior; the fretboard SVG and answer cards rendered.

## Protected Preview Browser Smoke Results

URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-first-20d2f84`

- Cloudflare Access login state: succeeded; the app shell loaded rather than the Access login page.
- Q&A input: available.
- `/api/version`: reported `20d2f84`.
- Browser console errors: none.

| Prompt | Expected | Actual | Result |
| --- | --- | --- | --- |
| `Show me a G major grip` | Fretboard/SVG visible, no tab | Fretboard visible with G 4-5-6 grip at fret 3; tab card count `0` | Pass |
| `Show me a 4-5-6 grip` | Fretboard/SVG visible, no tab | Fretboard visible with G 4-5-6 grip at fret 3; tab card count `0` | Pass |
| `Show me a G chord on strings 4-5-6` | Fretboard/SVG visible, no tab | Fretboard visible with G 4-5-6 grip at fret 3; tab card count `0` | Pass |
| `Where is G on E9?` | Fretboard/SVG visible, no tab | G position catalog rendered; starter positions included 3 open, 6 A+F, 10 A+B; tab card count `0` | Pass |
| `Show me a G to C move` | Tab and fretboard visible | Tab rendered G to C move; fretboard showed matching G and C partial events | Pass |
| `How do I use A+B pedals?` | Tab and fretboard visible | Tab rendered A+B major position on strings 3-4-5; fretboard matched | Pass |
| `Show me an A+B example` | Tab and fretboard visible | Same A+B tab/fretboard behavior as above | Pass |
| `Show me an E-lower move` | Tab and fretboard visible | Tab rendered E-lower color move; fretboard matched | Pass |
| `Give me a beginner lick in G` | Tab and fretboard visible; string 8 not treated as A+B | Tab rendered strings 5 and 6 with A/B; string 8 blank; fretboard matched G/C partial/G events | Pass |
| `What are good Fender Steel King settings?` | Normal answer, no stale tab/fretboard | Gear answer rendered; no tab; no fretboard | Pass |
| `Tab the whole solo from Together Again` | No generated tab/fretboard | Safe song-approach answer; no tab; no fretboard | Pass |
| `Transcribe this YouTube recording into tab` | No generated tab/fretboard | Safe song-approach answer; no tab; no fretboard | Pass |
| `Give me the full tab for a modern copyrighted song` | No generated tab/fretboard | Safe song-approach answer; no tab; no fretboard | Pass |

## Behavior Summary

- Static grip behavior: pass. Static grip prompts are now fretboard-first: direct prose plus visible fretboard/SVG, with no visible tab card.
- Movement tab behavior: pass. Movement prompts still show direct prose, visible tab, and visible fretboard/SVG.
- Beginner G lick semantics: pass. The rendered tab/action/prose/fretboard agree that A+B affects strings 5 and 6; string 8 is not shown as affected by A+B.
- Stale-state behavior: pass. Returning to stage cleared tab/fretboard state, and negative prompts did not retain stale tab or fretboard.
- Negative prompt behavior: pass. Gear answered normally without stale generated examples. Copyright/full-song/transcription requests did not generate tab or fretboard examples.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git log --oneline -12
curl -sS http://127.0.0.1:8770/api/version
git diff --check
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m py_compile steel_guitar_rag/tab_engine.py steel_guitar_rag/api.py steel_guitar_rag/answer_tab_examples.py
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_tab_engine.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
.venv/bin/python -m pytest tests/test_api_search.py -q
```

Results:

- `git diff --check`: passed
- `node --check ui/answer-client.js`: passed
- `node --check ui/pedal-steel-fretboard.js`: passed
- `py_compile steel_guitar_rag/tab_engine.py steel_guitar_rag/api.py steel_guitar_rag/answer_tab_examples.py`: passed
- `tests/test_frontend_answer_ui.py`: 20 passed
- `tests/test_pedal_steel_fretboard_ui.py`: 29 passed
- `tests/test_tab_engine.py`: 23 passed
- `tests/test_api_contract.py`: 5 passed
- `tests/test_api_search.py`: 259 passed

## Files Changed

- Created: `docs/handoffs/task-completions/2026-06-18-12-fretboard-first-static-grips-smoke.md`

No implementation files were changed.

## Unrelated Dirty Files Left Untouched

Existing dirty/parked work remained untouched, including but not limited to:

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `deploy/landing/index.html`
- `docs/handoffs/task-completions/integration-status.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `tests/test_frontend_answer_ui.py`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `ui/steel-guitar-rag-mock.html`
- numerous untracked historical handoffs/assets/docs and generated/private-adjacent paths already present before this task

## Risks

Risk: low for this handoff. The runtime was restarted under the documented protected-preview command, and the only repository change from this task is a smoke handoff.

Caveats:

- Full pytest was not requested and was not run.
- The worktree has broad unrelated dirty/untracked parked files; exact-path staging is required.
- The local server logged the known unrelated `/brand/pedal-steel-fretboard-background.svg` 404 during local browser smoke.
- Root `/` was not the smoke target; direct `/ui/steel-guitar-rag-mock.html` was used to preserve the cache-bust query.

Rollback/restart note:

- The protected preview can be restarted with the same documented `scripts/serve_v2_rerank_smoke.py` command from this handoff.
- If this smoke handoff needs removal, revert only this markdown file/commit; no runtime code was changed.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-12-fretboard-first-static-grips-smoke.md`

## Files That Must Not Be Staged

- Any corpus, Chroma/vector, embedding, source-inbox, private corpus, scraping, credential, `.wrangler`, DNS/deployment secret, generated data, visual-design asset, or unrelated dirty file.
- Existing parked dirty files listed above.

## Recommended Next Lane

Lane 01 Repo Steward only if an integration-status refresh is desired. Otherwise, user smoke may continue from the protected-preview URL above.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Continue user smoke on `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-first-20d2f84`, focusing on static grip prompts, movement examples, and no-stale-state transitions.
