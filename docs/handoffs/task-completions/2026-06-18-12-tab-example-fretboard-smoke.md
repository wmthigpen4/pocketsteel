# 2026-06-18 Lane 12 Tab Example Fretboard Smoke

## Task Summary

Lane 12 smoke-tested tab-example fretboard rendering and the corrected beginner G lick from current `feature/answer-api` HEAD. The target fixes were:

- `Show me a G major grip` should show both a deterministic tab card and a fretboard card/SVG.
- `Give me a beginner lick in G` should not imply that A+B affects string 8; prose, tab, action, and fretboard should agree.

Completed:
- Verified current HEAD and dirty worktree state.
- Restarted protected preview on `127.0.0.1:8770`.
- Verified `/api/version` reports current HEAD `d18fd6f`.
- Ran local API smoke against a temporary local-dev server on `127.0.0.1:8781`.
- Ran local browser smoke against the same local-dev server.
- Ran authenticated protected-preview browser smoke through Cloudflare Access.
- Ran the requested focused checks.

Intentionally not changed:
- No implementation files were modified.
- No DNS, Cloudflare Access policy, auth behavior, corpus, Chroma, embeddings, source data, scraping, or deployment config was changed.
- The temporary local-dev server on `8781` was stopped after smoke.
- The protected-preview server on `8770` was left running for user testing.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=tab-fretboard-d18fd6f`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=tab-fretboard-d18fd6f`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=tab-fretboard-d18fd6f`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `d18fd6f`
- Version endpoint: `/api/version`
- Version endpoint result: `git_sha: d18fd6f`, `git_branch: feature/answer-api`, `retrieval_mode: hybrid_private_first`, `auth_provider: cloudflare_access`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, but root may redirect to `/ui/steel-guitar-rag-mock.html` and drop query strings
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex and the user
- Do not test these URLs: stale tab smoke URLs for `425e14c` or `af645c9`
- Known caveats: use the direct `/ui/steel-guitar-rag-mock.html?v=tab-fretboard-d18fd6f` URL when cache-busting matters; root can drop the query string.

## Branch And Runtime Evidence

- Branch: `feature/answer-api`
- HEAD commit tested: `d18fd6f feat: show fretboard for tab examples`
- Relevant prior commit: `12eef1d fix: align tab examples with fretboard payloads`
- Runtime `/api/version` commit: `d18fd6f`
- Runtime includes current HEAD: yes
- Protected-preview process:
  - PID observed listening on `127.0.0.1:8770`
  - CWD verified as `/Users/cory/Documents/Pocket Steel`
  - Restarted with `scripts/serve_v2_rerank_smoke.py`, production answer auth, and Cloudflare Access provider

Dirty worktree note:
- Parked dirty files existed before restart, including `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py`.
- The dirty UI/test diff was limited to landing-sign asset cache-bust query strings.
- Dirty `rag_*` corpus/pipeline utility files were present but were not part of the protected-preview server path tested here.
- No parked files were modified or staged by this task.

## Local API Smoke Results

Endpoint: `http://127.0.0.1:8781/api/answer` with local-dev beta header.

| Prompt | Expected | Actual | Result |
| --- | --- | --- | --- |
| `Show me a G major grip` | Direct prose, tab, fretboard | Direct prose; `tab_example` `g-major-456-open`; fretboard present with 1 position; no fallback | Pass |
| `Show me a 4-5-6 grip` | Direct prose, tab, fretboard | Direct prose; `tab_example` `g-major-456-open`; fretboard present with 1 position; no fallback | Pass |
| `Show me a G to C move` | Direct prose, tab, fretboard | Direct prose; `tab_example` `g-to-c-456-beginner`; fretboard present with 2 positions; no fallback | Pass |
| `How do I use A+B pedals?` | Direct prose, tab, fretboard | Direct prose; `tab_example` `a-b-pedal-major-position`; fretboard present with 1 position; no fallback | Pass |
| `Show me an A+B example` | Direct prose, tab, fretboard | Direct prose; `tab_example` `a-b-pedal-major-position`; fretboard present with 1 position; no fallback | Pass |
| `Show me an E-lower move` | Direct prose, tab, fretboard | Direct prose; `tab_example` `e-lower-color-move`; fretboard present with 1 position; no fallback | Pass |
| `Give me a beginner lick in G` | Direct prose, tab, fretboard; no string 8 A+B implication | Direct prose; `tab_example` `beginner-g-two-event-lick`; fretboard present with 3 positions; A+B event uses strings 5 and 6 only | Pass |
| `What are good Fender Steel King settings?` | Normal gear answer, no tab/fretboard | Normal answer with sources; no tab; no fretboard | Pass |
| `Tab the whole solo from Together Again` | No generated full-song tab/fretboard | Safe song-approach guidance; no tab; no fretboard | Pass |
| `Transcribe this YouTube recording into tab` | No generated transcription tab/fretboard | Safe song-approach guidance; no tab; no fretboard | Pass |
| `Give me the full tab for a modern copyrighted song` | No generated full-song tab/fretboard | Safe song-approach guidance; no tab; no fretboard | Pass |

Beginner lick API semantics:
- Answer says to use fret 3, grip 4-5-6, then press A+B for the IV-chord lift.
- Rendered tab middle event uses `5 |3A` and `6 |3B`; string 8 is blank.
- Event payload for the middle event contains string 5 with `A` and string 6 with `B`.
- Fretboard middle card says strings 5-6 at fret 3 with A+B.

## Local Browser Smoke Results

URL: `http://127.0.0.1:8781/ui/steel-guitar-rag-mock.html?access=beta_user&v=tab-fretboard-d18fd6f`

Positive prompts:
- All seven positive prompts rendered direct prose.
- The generic fallback text did not appear.
- Tab card/block rendered for all seven.
- Fretboard/card rendered for all seven.
- Fretboard SVG mounted for all seven.
- Tab text preserved spacing with `white-space: pre`.
- Tab text used the monospace stack `ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace`.
- Tab container used `overflow-x: auto`.
- Returning to the stage cleared tab and fretboard state.

Negative prompts:
- Gear question answered normally without tab or fretboard.
- Copyright/full-song/transcription prompts did not show generated tab or fretboard.
- No stale tab or fretboard remained after returning to the stage.

Key local browser confirmations:
- `Show me a G major grip`: tab visible, fretboard visible, SVG mounted.
- `Give me a beginner lick in G`: tab visible, fretboard visible, SVG mounted; rendered tab and fretboard text both show A+B on strings 5 and 6, not string 8.

Console errors: none observed through browser automation.

## Protected Preview Browser Smoke Results

URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=tab-fretboard-d18fd6f`

Access/browser result:
- Cloudflare Access login/session succeeded.
- Direct `/ui` URL loaded and preserved the cache-bust query string.
- App shell loaded.
- Q&A input was unlocked.
- Console errors: none observed through browser automation.

| Prompt | Expected | Actual | Result |
| --- | --- | --- | --- |
| `Show me a G major grip` | Direct prose, tab, fretboard | Direct prose, visible tab, visible fretboard SVG; no fallback; no stale state after return | Pass |
| `Show me a 4-5-6 grip` | Direct prose, tab, fretboard | Direct prose, visible tab, visible fretboard SVG; no fallback; no stale state after return | Pass |
| `Show me a G to C move` | Direct prose, tab, fretboard | Direct prose, visible tab, visible fretboard SVG; no fallback; no stale state after return | Pass |
| `How do I use A+B pedals?` | Direct prose, tab, fretboard | Direct prose, visible tab, visible fretboard SVG; no fallback; no stale state after return | Pass |
| `Show me an A+B example` | Direct prose, tab, fretboard | Direct prose, visible tab, visible fretboard SVG; no fallback; no stale state after return | Pass |
| `Show me an E-lower move` | Direct prose, tab, fretboard | Direct prose, visible tab, visible fretboard SVG; no fallback; no stale state after return | Pass |
| `Give me a beginner lick in G` | Direct prose, tab, fretboard; no string 8 A+B implication | Direct prose, visible tab, visible fretboard SVG; tab/fretboard say A+B on strings 5 and 6; no fallback; no stale state after return | Pass |
| `What are good Fender Steel King settings?` | Normal gear answer, no stale tab/fretboard | Normal answer, no tab, no fretboard, no stale state | Pass |
| `Tab the whole solo from Together Again` | No generated full-song tab/fretboard | Safe song-approach guidance, no tab, no fretboard, no stale state | Pass |
| `Transcribe this YouTube recording into tab` | No generated transcription tab/fretboard | Safe song-approach guidance, no tab, no fretboard, no stale state | Pass |
| `Give me the full tab for a modern copyrighted song` | No generated full-song tab/fretboard | Safe song-approach guidance, no tab, no fretboard, no stale state | Pass |

## Expected vs Actual Summary

- `Show me a G major grip` shows fretboard: yes, local and protected browser.
- `Show me a G major grip` shows tab: yes, local and protected browser.
- Beginner G lick semantics are fixed: yes.
- Beginner G lick does not imply A+B affects string 8: yes.
- Positive tab prompts show direct prose: yes.
- Generic fallback text is absent for positive prompts: yes.
- Negative/copyright/transcription prompts do not generate tab: yes.
- Negative/copyright/transcription prompts do not generate fretboard examples: yes.
- Non-tab gear answer remains normal: yes.
- No stale tab/fretboard remains after non-tab prompts or return-to-stage: yes.

## Screenshots

No screenshots were saved. Browser smoke used DOM assertions and rendered-state checks.

## Tests And Checks

Passed:
- `git diff --check`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py pocketsteel/answer_tab_examples.py`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` -> `20 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` -> `29 passed`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q` -> `22 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` -> `5 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -q` -> `257 passed`

Not run:
- Full pytest, because the task requested the focused checks.

## Known Unrelated Failures / Caveats

- The local server logs still show `GET /brand/pedal-steel-fretboard-background.svg` returning 404 during fretboard rendering. This matches the known unrelated same-origin public fretboard background route issue; the fretboard card/SVG itself rendered and mounted successfully.
- Existing known unrelated full-suite caveats remain:
  - landing source vs deployed static HTML mismatch
  - missing public fretboard background route
- The worktree contains many unrelated parked dirty/untracked files. This task staged only the new handoff.

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-18-12-tab-example-fretboard-smoke.md`

No implementation files were changed.

## Risk Assessment

Risk: low.

Reasoning:
- This was a verification/documentation task.
- Current protected-preview runtime was restarted and `/api/version` reported `d18fd6f`.
- Local API, local browser, protected browser, and focused checks passed.
- No data, auth, DNS, Cloudflare policy, corpus, Chroma, embedding, source, scraping, or implementation files were modified.

Rollback/restart note:
- Protected preview can be restarted with the documented Lane 12 `scripts/serve_v2_rerank_smoke.py` command on `127.0.0.1:8770`.
- No code rollback is required for this handoff-only task.

## Human Decision Needed

No.

## Safe To Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-12-tab-example-fretboard-smoke.md`

## Files That Must Not Be Staged

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `deploy/landing/index.html`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `tests/test_frontend_answer_ui.py`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `ui/steel-guitar-rag-mock.html`
- Any untracked corpus, source-inbox, private, generated, design, deployment, or unrelated handoff files.

## Recommended Next Lane

Lane 01 Repo Steward only if a broader integration-status refresh is needed. Otherwise user smoke can continue from the protected preview URL above.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit this exact handoff with:

```bash
git add docs/handoffs/task-completions/2026-06-18-12-tab-example-fretboard-smoke.md
git commit -m "docs: record tab example fretboard smoke"
```
