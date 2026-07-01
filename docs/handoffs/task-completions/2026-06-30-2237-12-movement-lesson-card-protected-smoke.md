# 2026-06-30 22:37 Lane 12 - Movement Lesson Card Protected Smoke

## Task Summary

Requested Lane 12 protected-preview restart and authenticated browser smoke for Movement Lesson Card UI v1.

Completed:

- Verified repo branch and HEAD.
- Confirmed current repo HEAD `a2f3b81` contains required app-code commit `29bfd24`.
- Verified the LaunchDaemon-supervised protected-preview runtime was stale at `e449180`.
- Restarted the normal protected-preview runtime by terminating the stale `127.0.0.1:8770` listener and allowing `com.steelguitarrag.private-preview` to restart it.
- Verified local `/api/version` now reports `a2f3b81`.
- Ran authenticated protected-preview browser smoke through Cloudflare Access at the exact cache-busted URL.
- Confirmed movement prompts still render direct prose, deterministic tab, and matching fretboard.
- Confirmed the new Movement Lesson Card is still not visible in protected preview.
- Identified the likely blocker: protected HTML still references stale `answer-client.js?v=e9-explorer-home-entry-20260623`, so the browser can keep loading the older answer-client asset that lacks tab-event normalization needed by the Movement Lesson Card.
- Refreshed `docs/handoffs/task-completions/integration-status.md` with the blocker.

Intentionally not changed:

- No backend or UI implementation files were modified.
- No cache-bust fix was applied from Lane 12 because the prompt instructed to stop with WARN/FAIL if the Movement Lesson Card was not visible.
- No DNS, Cloudflare Access policy, auth configuration, tunnel configuration, secrets, deployment architecture, corpus, scraping, embeddings, Chroma/vector stores, private transcripts, licensing metadata, or unrelated assets.
- No API fallback was used as proof of browser behavior.

## Smoke Target

- Target type: protected-preview browser smoke
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=movement-lesson-card-29bfd24`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=movement-lesson-card-29bfd24`
- Exact URL the user should use: not ready for user smoke yet
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; app shell loaded in the authenticated browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected repo/runtime HEAD: `a2f3b81`
- Required app-code commit: `29bfd24`
- Version endpoint: `/api/version`
- Version endpoint result: local origin returned `{"git_sha":"a2f3b81","git_branch":"feature/answer-api","server_started_at":"2026-07-01T05:35:31.777264+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- Whether app root `/` works: not rechecked in this failed smoke; standing behavior is redirect to `/ui/steel-guitar-rag-mock.html` while dropping query strings
- Whether app root `/` is expected to work: yes as a redirect, not as the exact cache-busted target
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes; this remains the canonical cache-busted smoke URL
- API fallback status: not used
- Who should test this URL: Codex after Lane 06/Lane 12 fixes the stale script cache-bust; not ready for user smoke
- Do not test these URLs: root-only URL when exact cache-busting matters, because root drops query strings during redirect
- Known caveats: protected browser direct `/api/version` navigation has historically been blocked by the browser environment; local origin version proof was used for runtime SHA

## Runtime Restart Evidence

Before restart:

- `/api/version`: `e449180`
- Listener PID: `47454`
- Listener command: `scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 ... --answer-auth-mode production --auth-provider cloudflare-access`
- LaunchDaemon: `system/com.steelguitarrag.private-preview`, state `running`

Restart action:

- Terminated stale listener PID `47454`.
- LaunchDaemon restarted the process automatically.

After restart:

- `/api/version`: `a2f3b81`
- Listener PID: `72790`
- Start time: `Tue Jun 30 22:35:31 2026`
- `server_started_at`: `2026-07-01T05:35:31.777264+00:00`
- Branch: `feature/answer-api`
- Auth provider: `cloudflare_access`
- Retrieval mode: `hybrid_private_first`

## Protected Browser Result

Overall result: WARN / blocked for user smoke.

The protected preview is no longer runtime-stale, but the Movement Lesson Card still does not render.

Observed protected page scripts:

```text
answer-client.js?v=e9-explorer-home-entry-20260623
pedal-steel-fretboard.js?v=e9-explorer-home-entry-20260623
```

Expected Movement Lesson Card selectors/copy were absent:

- `.movement-lesson-card`: `0`
- Visible `Movement lesson` text: absent
- `Tab ↔ fretboard`: absent
- `Practice it slowly`: absent

This points to a stale static asset cache-bust, especially for `answer-client.js`. The committed HTML contains Movement Lesson Card renderer code, but the page still requests the old answer-client cache key.

## Prompt Results

| Prompt | Result | Browser observations |
| --- | --- | --- |
| `Show me a G to C move.` | FAIL for Movement Lesson Card; PASS for old behavior | Direct prose, deterministic tab, matching fretboard, fixed-width tab spacing; no Movement Lesson Card. |
| `Show me a G to D move.` | FAIL for Movement Lesson Card; PASS for old behavior | Direct prose, deterministic tab, matching fretboard; no Movement Lesson Card. |
| `Show me a 1 to 4 move in G.` | FAIL for Movement Lesson Card; PASS for old behavior | Routed to G I-IV movement with tab and fretboard; no Movement Lesson Card. |
| `Show me a 1 to 5 move in G.` | FAIL for Movement Lesson Card; PASS for old behavior | Routed to G I-V movement with tab and fretboard; no Movement Lesson Card. |
| `Show me a 1 4 5 1 move in G.` | FAIL for Movement Lesson Card; PASS for old behavior | Four-event movement tab and matching fretboard; no Movement Lesson Card. |
| `How do I connect no-pedals to A+B positions?` | FAIL for Movement Lesson Card; PASS for old behavior | Defaults to G, movement tab and matching fretboard; no Movement Lesson Card. |
| `Show me a G major grip.` | PASS regression | Static fretboard-first answer, no visible tab block, no Movement Lesson Card. |
| `Where is G on E9?` | PASS regression | Defaults to full G major starter positions, not 5-7-8 open; no visible tab block, no Movement Lesson Card. |
| `Show me a 5-7-8 G grip.` | PASS regression | Explicit 5-7-8 remains partial/color/no-3rd; no inert A+B; no visible tab block. |
| `What are good Fender Steel King settings?` | PASS regression | Concrete Buddy Emmons Steel King settings block with source notes; no stale tab/fretboard/movement UI. |

Additional checks:

- No generic `I need a more specific steel-guitar question` fallback appeared for movement prompts.
- Movement tab blocks used monospace font family and `white-space: pre`.
- No visible `[object Object]`.
- Browser console warnings/errors: none recorded.

## Screenshots

These screenshots document the protected-preview blocker; the filenames reflect the intended scenarios, but the Movement Lesson Card is absent in the captured UI:

- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-g-to-c-movement-lesson.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-1451-movement-lesson.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-static-g-major-no-lesson.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-steel-king-no-stale-movement.png`

## Files Changed

- `docs/handoffs/task-completions/2026-06-30-2237-12-movement-lesson-card-protected-smoke.md`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-g-to-c-movement-lesson.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-1451-movement-lesson.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-static-g-major-no-lesson.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-steel-king-no-stale-movement.png`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files:

- None.

Generated artifacts:

- Four protected-preview smoke screenshots listed above.

## Tests And Checks

- `git status --short` - run before and after; broad unrelated dirty/untracked work remains parked.
- `git branch --show-current` - `feature/answer-api`.
- `git rev-parse --short HEAD` - `a2f3b81`.
- `git log --oneline -8` - confirmed `a2f3b81` after `29bfd24`.
- `git merge-base --is-ancestor 29bfd24 HEAD` - PASS, current HEAD contains required app-code commit.
- `git status --short -- 'pocketsteel/*.py' 'ui/*.js' 'scripts/*.py' tests` - no dirty runtime-affecting files.
- `curl -sS http://127.0.0.1:8770/api/version` before restart - stale `e449180`.
- `lsof -nP -iTCP:8770 -sTCP:LISTEN` before restart - PID `47454`.
- `launchctl print system/com.steelguitarrag.private-preview` - state `running`.
- Terminated stale listener PID `47454`; launchd restarted the app.
- `curl -sS http://127.0.0.1:8770/api/version` after restart - PASS, `a2f3b81`.
- `lsof -nP -iTCP:8770 -sTCP:LISTEN` after restart - PID `72790`.
- Protected-preview browser smoke through Cloudflare Access - WARN/FAIL for Movement Lesson Card.
- Static asset inspection - protected HTML/page references stale `answer-client.js?v=e9-explorer-home-entry-20260623`.
- Browser console warning/error read - none recorded.
- `git diff --check` - PASS.

Skipped:

- No implementation tests were rerun in Lane 12 because this task changed no app code. Lane 06 recorded focused and local browser test pass for the implementation.
- API fallback was not used.

## Integration Notes

- Protected preview now serves runtime HEAD `a2f3b81`.
- Runtime staleness is resolved.
- User smoke remains blocked because protected browser behavior still lacks the Movement Lesson Card.
- The next fix should update the app page script cache-bust for `answer-client.js` to a Movement Lesson Card-specific value, then rerun protected browser smoke at the same exact target URL or a fresh equivalent cache-busted URL.

## Risk Assessment

Risk: low for this Lane 12 action.

Why:

- Lane 12 only restarted the existing LaunchDaemon-supervised app and wrote docs/screenshots.
- No app implementation, auth, DNS, tunnel, corpus, Chroma/vector, scraping, private transcript, licensing, or secret files were changed.

Rollback:

- If needed, revert the docs-only smoke/blocker commit.
- Runtime rollback would require restarting the LaunchDaemon from a prior checked-out commit; no rollback was needed during this task.

## Human Decision Needed

No for the blocker classification.

Yes for next implementation lane: approve/route the cache-bust/static-asset fix.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-30-2237-12-movement-lesson-card-protected-smoke.md`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-g-to-c-movement-lesson.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-1451-movement-lesson.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-static-g-major-no-lesson.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-card-protected-smoke/protected-steel-king-no-stale-movement.png`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Existing unrelated parked dirty/untracked files in `README.md`, `corpus_metadata/`, `docs/`, `rag_*.py`, `source-inbox/`, `ui/brand/`, `public/brand/`, `Neon Sign/`, corpus/private/vector/scraper/auth/deploy/source-data paths, and generated/private artifacts.
- Existing untracked enhanced-learning-card handoff/screenshots from prior work unless a separate task explicitly scopes them.

## Recommended Next Lane

Lane 06 UX/UI Design for the static script cache-bust fix, then Lane 12 protected-preview rerun.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 06 prompt:

```text
Fix protected-preview Movement Lesson Card stale asset loading. Update only the app page script cache-busts needed for Movement Lesson Card UI v1, especially `answer-client.js`, so protected preview no longer serves `answer-client.js?v=e9-explorer-home-entry-20260623`. Do not change backend behavior. Run `node --check ui/answer-client.js`, `node --check ui/pedal-steel-fretboard.js`, focused frontend/fretboard tests, and `git diff --check`. Write a handoff and commit the scoped cache-bust fix.
```

Then rerun Lane 12 protected-preview browser smoke at:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=movement-lesson-card-29bfd24
```
