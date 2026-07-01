# Movement Lesson Card UI v1

## Task Summary
Implemented Movement Lesson Card UI v1 for deterministic movement answers that include a validated `tab_example` plus matching fretboard payload. Movement answers now present a compact lesson section that explains the move, start and resolve positions, controls used, event path, why it works, how the tab relates to the fretboard, and a short practice nudge.

Intentionally not changed:
- Backend answer routing or tab generation.
- Corpus, scraping, embeddings, Chroma/vector stores, auth, DNS, deployment config, private transcripts, licensing metadata, secrets, or assets.
- Static grip/location behavior: static answers remain fretboard-first and no-tab by default.
- Gear/source-backed answer behavior.

## Files Changed
- `ui/answer-client.js`
  - Preserves tab payload metadata needed by the UI: `kind`, object-shaped `contextData`, and normalized tab `events`.
- `ui/steel-guitar-rag-mock.html`
  - Adds Movement Lesson Card styling and rendering.
  - Hides empty source-card sections for deterministic movement examples with no sources.
- `tests/test_frontend_answer_ui.py`
  - Adds focused assertions for tab event normalization and movement lesson wiring.
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card/`
  - Local browser smoke screenshots.
- `docs/handoffs/task-completions/2026-06-30-2217-06-movement-lesson-card-ui-v1.md`
  - This handoff.

## UI Behavior Added
For movement prompts such as `Show me a G to C move.`:
- Shows `Movement lesson` section inside the tab card.
- Shows start and resolve positions.
- Shows pedals/levers used.
- Shows step/path rows from tab events.
- Shows concise `Why this move works` from existing deterministic tab explanation.
- Shows `Tab ↔ fretboard` relationship copy.
- Shows `Practice it slowly` nudge.
- Keeps fixed-width tab block unchanged.
- Keeps matching fretboard visible.
- Hides empty source-card area for deterministic movement examples with `sources: []`.

Static grip/location prompts remain no-tab and fretboard-first. Non-tab gear answers do not show stale tab/fretboard UI.

## Smoke Target
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8899/ui/steel-guitar-rag-mock.html?access=beta_user&v=movement-lesson-card-local`
- Cache-busted URL tested: `http://127.0.0.1:8899/ui/steel-guitar-rag-mock.html?access=beta_user&v=movement-lesson-card-local`
- Exact URL the user should use: protected-preview URL to be set after commit/protected smoke
- Auth required: no for local smoke
- Auth provider: local-dev scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8899`
- Expected backend port: `8899`
- Expected git HEAD: `24fc988` plus uncommitted scoped UI changes during local smoke
- Version endpoint: not used for local smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: local worktree and smoke URL cache-bust
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this UI slice
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally; user should test protected-preview after commit/protected smoke
- Do not test these URLs: API fallback URLs as browser proof
- Known caveats: in-app browser full-page screenshots tiled repeated page content; DOM/browser assertions and viewport state were used as authoritative smoke evidence.

## Local Browser Smoke Prompts
Passed via real UI submit controls:
- `Show me a G to C move.`: movement lesson + tab + fretboard, no source cards.
- `Show me a G to D move.`: movement lesson + tab + fretboard, no source cards.
- `Show me a 1 to 4 move in G.`: movement lesson + tab + fretboard, no source cards.
- `Show me a 1 to 5 move in G.`: movement lesson + tab + fretboard, no source cards.
- `Show me a 1 4 5 1 move in G.`: movement lesson + tab + fretboard, no source cards.
- `How do I connect no-pedals to A+B positions?`: movement lesson + tab + fretboard, no source cards.
- `Show me a G major grip.`: fretboard visible, no tab, no movement lesson.
- `Where is G on E9?`: fretboard visible, no tab, no movement lesson.
- `Show me a 5-7-8 G grip.`: fretboard visible, no tab, no movement lesson; existing partial/color/no-3rd answer preserved.
- `What are good Fender Steel King settings?`: source-backed answer, no tab, no fretboard, no movement lesson.

Additional local smoke assertions:
- No `[object Object]` rendered.
- Console errors: none observed.
- Tab text retains newline-preserved `<pre><code>` content.
- Mobile/narrow smoke showed no page-level horizontal overflow in DOM metrics.

## Protected-Preview Smoke After Commit
WARN / not ready for user smoke.

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?access=beta_user&v=movement-lesson-card-29bfd24`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?access=beta_user&v=movement-lesson-card-29bfd24`
- Exact URL the user should use: none yet; protected-preview needs Lane 12 restart/update and re-smoke first
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; protected page loaded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `29bfd24`
- Version endpoint: `/api/version`
- Version endpoint result: loopback `http://127.0.0.1:8770/api/version` returned `git_sha: e449180`; protected browser navigation to `/api/version` was blocked by the browser client
- If version endpoint missing, how version is inferred: protected static page loaded, but runtime version did not match expected commit
- Whether app root `/` works: loopback `/` returns `302` to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as redirect
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex after Lane 12 restart/update; user after protected re-smoke passes
- Do not test these URLs: stale cache-bust `movement-lesson-card-29bfd24` as proof of current committed UI
- Known caveats: protected-preview served old answer UI behavior; movement prompts still had tab + fretboard but no Movement Lesson Card and showed the empty source-card section.

Protected prompts checked:
- `Show me a G to C move.`: tab + fretboard rendered, but `movementLessons: 0`; not pass.
- `Show me a G to D move.`: tab + fretboard rendered, but `movementLessons: 0`; not pass.
- `Show me a 1 4 5 1 move in G.`: tab + fretboard rendered, but `movementLessons: 0`; not pass.
- `Show me a G major grip.`: static fretboard/no-tab behavior preserved.
- `What are good Fender Steel King settings?`: source-backed/no-fretboard behavior preserved.

Protected console errors: none observed.

## Screenshots
- Desktop: `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card/g-to-c-movement-desktop.png`
- Mobile/narrow: `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card/g-to-c-movement-mobile.png`

## Tests and Checks Run
- `git status --short` - passed; unrelated dirty work remains parked.
- `git diff --check` - passed.
- `node --check ui/answer-client.js` - passed.
- `node --check ui/pedal-steel-fretboard.js` - passed.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 24 passed.
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 37 passed.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_pedal_steel_fretboard_ui.py -q` - 61 passed.
- `.venv/bin/python -m pytest tests/test_api_search.py -q -k "tab_example or parameterized or steel_king or static_grip or fretboard"` - 49 passed, 236 deselected.
- Local browser smoke prompt matrix - passed.

## Integration Notes
- Frontend now depends on existing tab payload fields only: `kind`, `context`, and `events` from deterministic `tab_example` payloads.
- No frontend tab generation was added.
- No backend contract change was required.
- Movement Lesson Card appears only when normalized tab events exist.

## Risk Assessment
Risk: low-to-medium.
- Low backend risk: no backend changes.
- Medium UI risk: `shouldRenderMovementLesson` currently treats any normalized tab with events as movement-lesson eligible, which is acceptable for this slice because static grip answers do not expose visible tab examples. If future non-movement tab examples use events, they may also receive lesson-card framing unless refined by `kind`.
- Rollback: revert `ui/answer-client.js`, `ui/steel-guitar-rag-mock.html`, and related test changes.

## Human Decision Needed
No.

## Safe-to-Stage Exact File List
- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-30-2217-06-movement-lesson-card-ui-v1.md`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card/g-to-c-movement-desktop.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card/g-to-c-movement-mobile.png`

## Files That Must Not Be Staged
All unrelated dirty and untracked files, including but not limited to:
- `README.md`
- `corpus_metadata/**`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/integration-status.md` unless refreshed as a separate protocol step
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- private/corpus/generated/source data and all unrelated untracked handoffs/assets

## Recommended Next Lane
Lane 12 protected-preview restart/update and smoke. The local implementation is test-green, but protected preview is still serving old answer-page UI behavior.

## Commit Readiness
Safe to commit after exact-path staging and staged-diff checks.

## Suggested Next Step
Lane 12: restart or update the protected-preview runtime for commit `29bfd24`, then run protected-preview smoke for Movement Lesson Card UI v1 using a fresh cache-busted `/ui/steel-guitar-rag-mock.html` URL. Verify movement prompts show lesson card + tab + fretboard and static/gear prompts do not show stale UI.
