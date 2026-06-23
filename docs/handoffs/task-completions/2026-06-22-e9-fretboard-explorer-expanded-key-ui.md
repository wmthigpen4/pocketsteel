# 2026-06-22 - Lane 06 - E9 Fretboard Explorer Expanded Key UI

## Task Summary

Requested: expose the validated expanded E9 Fretboard Explorer keys in the browser UI while preserving deterministic row behavior, key-aware display spelling, mode-aware string-group filtering, compact row buttons, selected-position details, marker tooltip behavior, deduped pedal/lever labels, and non-RAG Explorer wording.

Completed:

- Expanded the static Explorer browser fixture from G-only to keyed payloads generated from `pocketsteel.fretboard_explorer.build_explorer_payload(key)`.
- Exposed the Lane 15 QA-covered UI key set: `G`, `C`, `D`, `F`, `Bb`, and `Eb`.
- Updated the Explorer controller to resolve active payload data from the selected key.
- Preserved the legacy `window.STEEL_RAG_E9_EXPLORER_PAYLOAD` G fallback for compatibility.
- Kept G as the default selected key.
- Preserved G natural minor display spelling: `G A Bb C D Eb F`.
- Preserved flat-key display spelling for `Bb` and `Eb`.
- Preserved mode-aware 2-string vs 3-string string-group filtering.
- Preserved core/advanced grouping and `5-7-8` as advanced E-lower pocket only.
- Updated focused frontend tests for expanded key selector behavior and key-aware display output.

Intentionally not changed:

- Backend Explorer validation/generation logic.
- Corpus, Chroma/vector stores, embeddings, scraper output, deployment, auth, DNS, private source data, source-inbox raw/provenance data, public assets, UI brand assets, or raw design assets.
- Answer/RAG behavior.

## Current Branch And HEAD

- Branch: `feature/answer-api`
- HEAD before commit: `b860cf3 test: add e9 explorer key expansion QA`

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-expanded-key-ui.md`

No files deleted.

## Expanded Keys Exposed

The browser key selector now exposes:

- `G`
- `C`
- `D`
- `F`
- `Bb`
- `Eb`

This intentionally follows the representative Lane 15 QA-covered set rather than exposing all backend enharmonic aliases in the first UI slice.

## Display Spelling Behavior

Verified:

- `G` natural minor: `G A Bb C D Eb F`
- `C` major: `C D E F G A B`
- `D` major: `D E F# G A B C#`
- `F` major: `F G A Bb C D E`
- `Bb` major: `Bb C D Eb F G A`
- `Eb` major: `Eb F G Ab Bb C D`

The UI continues to render learner-facing `display_notes`, `display_top_voice`, `display_summary`, and `query.display_scale_notes`.

## Mode-Aware Filter Behavior

Verified:

- `2-string harmonized scale` shows only valid 2-string groups:
  - `3-5`
  - `5-6`
  - `6-10`
  - `4-6`
  - `3-4`
- `3-string diatonic harmony` keeps core/advanced grouping.
- Core grips remain:
  - `3-4-5`
  - `4-5-6`
  - `5-6-8`
  - `6-8-10`
- Advanced swaps remain:
  - `5-6-7`
  - `6-7-10`
  - `5-7-8`
- `5-7-8` remains advanced/E-lower pocket only.
- Selecting a new key resets stale invalid row selection to a valid row.

## Browser Smoke Target

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8896/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-key-ui-20260623`
- Cache-busted URL tested: `http://127.0.0.1:8896/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-key-ui-20260623`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-key-ui-20260623` after Lane 12 protected-preview restart/freshness verification
- Auth required: local no; protected-preview yes
- Auth provider: local none; protected-preview Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: `http://127.0.0.1:8896`
- Expected backend port: static local server on `8896`
- Expected git HEAD: `b860cf3` before this commit
- Version endpoint: not applicable for local static server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local file server served current working tree
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this Explorer page smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this Explorer page smoke
- Who should test this URL: Lane 12 / Lane 15 / the user after protected-preview restart
- Do not test these URLs: stale Explorer cache-bust URLs from prior slices
- Known caveats: local root static server logged `404` for `/brand/pedal-steel-fretboard-background.svg` because it does not mount `public/` as the web root. Lane 12 should verify the protected-preview `/brand/` static route as part of protected smoke.

Local browser smoke result:

- Key selector rendered `G`, `C`, `D`, `F`, `Bb`, `Eb` in that order.
- Default selected key remained `G`.
- `Showing validated positions` displayed; no primary `validated rows` copy appeared.
- C/D/F/Bb/Eb key selection updated visible rows, markers, selected detail, and scale notes.
- G natural minor showed `G A Bb C D Eb F` with no `A#`/`D#` leak in the scale-note line.
- 2-string view removed core/advanced 3-string groups.
- 3-string `5-7-8` advanced view showed E-lower pocket details without `E-lower+E-lower`.
- No `[object Object]` rendered in the smoke state.

## Tests And Checks

Passed:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/answer-client.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `23 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `31 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - `21 passed`
- `.venv/bin/python -m pytest -q` - `801 passed`
- `git diff --check`

Pending before commit at handoff creation:

- `git diff --cached --check`
- cached diff review

## Integration Notes

- UI fixture now stores keyed payloads at `window.STEEL_RAG_E9_EXPLORER_PAYLOADS`.
- Compatibility fallback remains at `window.STEEL_RAG_E9_EXPLORER_PAYLOAD = window.STEEL_RAG_E9_EXPLORER_PAYLOADS.G`.
- The controller prefers keyed payloads but can still render a single legacy payload.
- Protected-preview needs a cache-busted verification URL because prior Explorer slices required inner script query-string refreshes.

## Risks

Risk: low-to-medium.

Reasons:

- The data fixture grows substantially because it now includes six deterministic payloads.
- Scope is otherwise isolated to the Explorer page/controller/test.
- Full pytest and local browser smoke passed.

Rollback:

- Revert `ui/e9-fretboard-explorer-data.js`, `ui/e9-fretboard-explorer.js`, `ui/e9-fretboard-explorer.html`, and matching frontend test changes to restore the G-only browser surface.

## Human Decision Needed

No.

Future product decision:

- Whether to expose all backend-supported enharmonic aliases or keep the reduced learner-facing key set.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-expanded-key-ui.md`

## Files That Must Not Be Staged

- Any unrelated dirty/untracked files.
- `public/`
- `ui/brand/`
- `Neon Sign/`
- `source-inbox/`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- scraper output
- deployment/auth/DNS/secrets files
- raw design assets
- generated/private data

## Recommended Next Lane

Lane 12 Self-Hosted Deployment, then Lane 15 QA / Answer Eval.

Exact next prompt:

```text
Lane 12: restart or verify protected-preview freshness for commit <commit>. Test https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-key-ui-20260623 and verify /api/version matches HEAD, the Explorer scripts use the expanded-key cache-bust, and the /brand/pedal-steel-fretboard-background.svg route resolves. Then hand off to Lane 15 for expanded-key browser smoke.
```

## Commit Readiness

Safe to commit after exact-path staging, `git diff --cached --check`, and cached diff review.

## Suggested Next Step

Commit this scoped Lane 06 UI slice, then send to Lane 12 for protected-preview freshness and Lane 15 for protected-preview expanded-key smoke.
