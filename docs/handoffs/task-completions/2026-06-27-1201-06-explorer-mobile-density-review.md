# Explorer Mobile Density Review

Pass/warn/fail: pass

## Task Summary

Requested: audit and improve the E9 Fretboard Explorer mobile usability and control density after recent feature expansion.

Completed:
- Verified prerequisite handoffs exist for protected-preview smoke, musical red-team QA, and the shared Explorer music-rules boundary.
- Inspected current Explorer implementation and responsive CSS.
- Browser-audited the Explorer on desktop and narrow/mobile viewports.
- Applied one focused UI layout fix: visible result cards now render as a horizontal scroll rail instead of a deep multi-row wall before the fretboard.
- Added narrow mobile scroll behavior for dense chip groups in top-note, fret-range, and pedal/lever controls.
- Added focused frontend assertions for the new scroll-rail behavior.

Intentionally not changed:
- No music rules, chord/voicing logic, pitch math, Explorer data, fretboard geometry, backend, corpus, Chroma/vector stores, embeddings, source records, auth, DNS, secrets, or deployment configuration.
- No broad Explorer redesign.

## Branch And HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `371de09`
- Implementation commit before handoff amendment: `84844bb fix: improve explorer mobile control density`
- Final HEAD / commit: see final Codex report after the handoff amendment.

## UX Findings

- Prerequisites were present:
  - Protected smoke: `docs/handoffs/task-completions/2026-06-27-1140-12-chord-voicing-finder-protected-smoke.md`
  - Musical red-team: `docs/handoffs/task-completions/2026-06-27-1141-15-explorer-musical-red-team.md`
  - Shared rules: `docs/handoffs/task-completions/2026-06-27-1152-05-shared-explorer-music-rules-boundary.md`
- The current Explorer already has several recent density improvements:
  - Explore mode is above filters.
  - Notation is directly above the fretboard.
  - Copedent and Glossary are header reference actions.
  - Grip vocabulary help is a collapsed disclosure.
- The remaining smoke-blocking density issue was the visible-position card area:
  - Desktop single-grip view rendered `33` cards in a multi-row block before the fretboard.
  - Mobile single-grip view rendered the card block at roughly `5846px` tall before the fretboard.
  - The fretboard started around `7321px` down the page on the narrow/mobile audit.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1201-06-explorer-mobile-density-review.md`

## UI Behavior Changed

- `.explorer-active-results__track` now uses a horizontal scroll rail:
  - `display: flex`
  - `overflow-x: auto`
  - `scroll-snap-type: x proximity`
  - touch scrolling enabled
- `.explorer-active-result` cards now have a fixed responsive rail width with scroll snapping.
- On narrow screens, top-note, fret-range, and pedal/lever chip groups scroll horizontally instead of wrapping into tall stacks.

## Local Browser Smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-mobile-density-371de09-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-mobile-density-371de09-local`
- Exact URL the user should use: protected-preview URL after commit/protected smoke, or the local URL above while the local server is running
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `371de09` plus the local uncommitted UI density patch during smoke
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local working tree served by the existing same-origin local server
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this Explorer direct URL smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but not part of this task
- Who should test this URL: Codex locally; user should test protected-preview URL after commit/smoke
- Do not test these URLs: do not treat API fallback as browser smoke
- Known caveats: protected preview not yet recorded at handoff creation

Desktop local smoke:
- Page loaded.
- Major modes were selectable by script: `single`, `path`, `note`, `voicing`, `chord`.
- Result card rail in single-grip mode dropped from about `620px` tall to about `160px`.
- Fretboard in desktop single-grip mode moved from about `1391px` down to about `930px` down.
- No `[object Object]`.
- Console warnings/errors: none.

Mobile/narrow local smoke:
- Page loaded at a narrow viewport.
- No page-level horizontal overflow from the closed page state.
- Major modes remained selectable.
- Result card rail in single-grip mode dropped from about `5846px` tall to about `257px`.
- Fretboard in single-grip mode moved from about `7321px` down to about `1672px` down.
- Path, note, voicing, and chord modes still rendered selected cards and fretboard areas.
- Glossary and Copedent dialogs opened and closed on mobile.
- No `[object Object]`.
- Console warnings/errors: none.

Protected-preview smoke:
- PASS for the cache-busted static Explorer URL.
- Exact protected URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mobile-density-84844bb`
- Cloudflare Access login result: succeeded; the page loaded directly and did not show the Access login screen.
- Local `/api/version`: `{"git_sha":"4040a47","git_branch":"feature/answer-api","server_started_at":"2026-06-26T01:51:23.747502+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- Version caveat: `/api/version` still reports runtime SHA `4040a47`; this smoke verifies the protected static/browser behavior at the cache-busted Explorer URL, not a Python runtime restart to this UI commit.
- Desktop protected smoke: result rail rendered as `display:flex`, `overflow-x:auto`; `33` single-grip cards were present; rail height was about `115px`; fretboard started around `921px` down; no `[object Object]`; no console warnings/errors.
- Mobile protected smoke at roughly `390x844`: no page-level horizontal overflow; result rail rendered as `display:flex`, `overflow-x:auto`; `33` single-grip cards were present; rail height was about `190px`; result block height was about `256px`; fretboard started around `1803px` down; no `[object Object]`; no console warnings/errors.
- Mode smoke: `single`, `path`, `note`, `voicing`, and `chord` modes were selectable and rendered their card/fretboard areas.
- Dialog smoke: Glossary and Copedent opened and closed on mobile; no console warnings/errors.

## Tests And Checks

Passed:
- `git diff --check`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` -> `24 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` -> `38 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` -> `34 passed`

Not run:
- Full pytest. The requested focused checks were run; the worktree contains extensive unrelated parked dirty/untracked files.

## Risks / Blockers

- Risk: low.
- Reason: CSS/presentation-only change; tests assert the intended card rail and chip scroll behavior.
- Remaining UX risk: the top filter stack is still long on mobile because the Explorer has many real controls. This patch makes the fretboard reachable sooner but does not redesign mode workflows or collapse major sections.
- Protected-preview runtime caveat from prior handoffs may still apply: static Explorer files can be cache-busted independently of `/api/version`.

## Human Decision Needed

No for this scoped density fix.

Yes for any broader Explorer redesign, such as mode-specific progressive disclosure, sticky mini-navigation, or a paid-product information architecture pass.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1201-06-explorer-mobile-density-review.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files.
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/` raw/provenance files
- `.wrangler/`
- auth, DNS, secret, deployment configuration files
- `public/`
- `ui/brand/`
- `Neon Sign/`
- raw design assets
- generated source/corpus reports

## Recommended Next Lane

Focused user smoke on the exact cache-busted Explorer URL.

## Commit Readiness

Safe to commit if exact-path staging includes only the three files listed above and `git diff --cached --check` passes.

## Suggested Next Step

Lane 12 prompt:

```text
Lane 15: run focused QA/user-smoke review for the E9 Fretboard Explorer mobile-density UI fix using https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mobile-density-84844bb. Verify desktop, tablet, and mobile readability, horizontal result rails, dialog usability, no [object Object], and no console errors.
```
