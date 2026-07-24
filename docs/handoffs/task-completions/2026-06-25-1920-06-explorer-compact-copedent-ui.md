# Lane 06 - Explorer Compact Copedent UI

## Task Summary

Requested: revise the E9 Fretboard Explorer so the page is compact, the full copedent chart is optional, Emmons is separated from the user-specific LKV setup, the pedal/lever impact preview is interactive instead of bulky, and fretboard labels separate fret numbers from note/interval text.

Completed:
- Removed LKV/B-to-Bb from the standard Emmons E9 and Day E9 app presets.
- Added an enabled first custom option, `Custom E9 (with LKV)`, generated from the existing structured user copedent data.
- Removed external reference/source context from the copedent payload so it is not surfaced in UI payloads.
- Moved the copedent chart into a keyboard-reachable native dialog opened from the E9 setup selector.
- Replaced the always-expanded pedal/lever impact card grid with compact control tabs that reveal detail on select/focus/hover.
- Added an Intervals/Notes toggle for Explorer fretboard/card labels.
- Changed row/card/SVG labels so fret numbers stay separate from note/interval labels.
- Tightened the Explorer header/filter layout so the fretboard panel is visible without scrolling on a normal 1280x720 desktop viewport.

Intentionally not changed:
- No backend routing, retrieval, Chroma, embeddings, corpus, scraping, auth, DNS, deployment, or visual asset files were changed.
- No broad app rename or product copy rename was attempted.
- No external reference URL, site name, or person name was added to app UI copy.

## Files Changed

- `steel_guitar_rag/e9_copedents.py`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`
- `ui/e9-fretboard-explorer-data.js`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `docs/handoffs/task-completions/2026-06-25-1920-06-explorer-compact-copedent-ui.md`
- `docs/handoffs/task-completions/assets/2026-06-25-06-explorer-compact-copedent-ui/desktop-explorer-compact-final.png`
- `docs/handoffs/task-completions/assets/2026-06-25-06-explorer-compact-copedent-ui/mobile-explorer-compact.png`

Generated artifacts:
- `ui/e9-fretboard-explorer-data.js` regenerated from `steel_guitar_rag.fretboard_explorer.build_explorer_payload(key)` for default, Day, and custom LKV copedent payloads.
- Browser-smoke screenshots saved under the asset directory above.

Deleted files: none.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625`
- Exact URL the user should use: pending protected-preview refresh; local smoke URL above is valid only on this machine.
- Auth required: no for local smoke
- Auth provider: local controlled-states smoke server
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `ffac52a`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `{"git_sha":"ffac52a","git_branch":"feature/answer-api",...}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested in this local smoke
- Whether app root `/` is expected to work: not required for this local Explorer UI smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally, then Lane 12/user on protected preview after commit/restart
- Do not test these URLs: unversioned protected-preview Explorer URL until Lane 12 refreshes runtime/cache-bust
- Known caveats: mobile first viewport still requires scrolling to reach the fretboard; desktop/laptop 1280x720 shows the fretboard panel without scrolling.

## Browser Smoke Result

Local server command:

```bash
PYTHONPATH=. STEEL_RAG_CHROMA_PATH="$HOME/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma" STEEL_RAG_CHROMA_COLLECTION="steel_guitar_unified" .venv/bin/python scripts/serve_answer_smoke.py --controlled-states --port 8770
```

Observed:
- Main app entry `Explore Fretboard` opens `/ui/e9-fretboard-explorer.html`.
- `Get a Backstage Pass` remains separate.
- Desktop 1280x720: Explorer fretboard panel top was about `567px`, visible before scroll.
- Copedent chart is hidden by default and opens in a native dialog from `View chart`.
- Emmons chart has no `B-to-Bb` / LKV column.
- `Custom E9 (with LKV)` appears as the first custom option and retains `B-to-Bb vertical`.
- Pedal/lever impact preview defaults to compact tabs; selecting `A pedal` reveals affected strings and interval effect.
- Intervals/Notes toggle changes card/SVG labels.
- No combined labels like `3 I`, `3 ii`, or `5 iii` were found.
- No `[object Object]` text was found.
- Browser console had no relevant warnings/errors.

Screenshots:
- `docs/handoffs/task-completions/assets/2026-06-25-06-explorer-compact-copedent-ui/desktop-explorer-compact-final.png`
- `docs/handoffs/task-completions/assets/2026-06-25-06-explorer-compact-copedent-ui/mobile-explorer-compact.png`

## Tests And Checks

Passed:

```bash
python3 -m py_compile steel_guitar_rag/e9_copedents.py
python3 -m py_compile steel_guitar_rag/e9_copedents.py steel_guitar_rag/fretboard_explorer.py
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_pedal_steel_fretboard_ui.py tests/test_fretboard_explorer.py tests/test_api_contract.py -q
git diff --check
```

Final focused bundle result:

```text
100 passed in 2.56s
```

Skipped:
- Full pytest was not run because the task-required focused UI/Explorer/API contract checks passed and the worktree contains many unrelated parked changes. The touched scope is covered by the focused bundle above.
- Protected-preview smoke not yet run at the time this handoff was written; it should run after exact-path commit and runtime refresh.

## Integration Notes

- `DEFAULT_COPEDENT_ID` remains `emmons-e9-basic`.
- New enabled copedent id: `custom-e9-lkv`.
- Disabled future Backstage placeholder remains `my-copedent-e9`.
- Standard Emmons/Day control order now omits LKV/B-to-Bb.
- Custom LKV payload includes `B-to-Bb`, `RKL-half`, `G-lower`, `D-lower`, and `RKR-full`.
- `ui/e9-fretboard-explorer-data.js` is larger because it now includes the custom LKV copedent payload map in addition to default and Day.

## Risk Assessment

Risk: medium.

Reason:
- UI changes are scoped but affect the main Explorer route and generated static data.
- Backend data change is intentionally narrow but changes visible default copedent semantics.
- The generated Explorer data file is large; exact-path staging and review are required.

Rollback notes:
- Revert this scoped commit to restore previous Emmons/Day/LKV behavior and the always-visible Explorer layout.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/e9_copedents.py`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`
- `ui/e9-fretboard-explorer-data.js`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `docs/handoffs/task-completions/2026-06-25-1920-06-explorer-compact-copedent-ui.md`
- `docs/handoffs/task-completions/assets/2026-06-25-06-explorer-compact-copedent-ui/desktop-explorer-compact-final.png`
- `docs/handoffs/task-completions/assets/2026-06-25-06-explorer-compact-copedent-ui/mobile-explorer-compact.png`

## Files That Must Not Be Staged

All unrelated parked dirty/untracked work, including but not limited to:
- `README.md`
- `corpus_metadata/*`
- `docs/answer-eval-report.md`
- `docs/current-commands.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/*`
- `ui/brand/*`
- `public/brand/*`
- `Neon Sign/`
- private/source/corpus/generated data paths

## Recommended Next Lane

Lane 01 exact-path commit, then Lane 12 protected-preview restart/smoke for the committed Explorer UI.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 01 / Autopilot exact-path commit of only the safe-to-stage files above, then Lane 12 protected-preview smoke using:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=<commit-or-slice-cachebuster>
```
