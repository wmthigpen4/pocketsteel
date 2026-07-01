# 2026-06-30 23:37 Lane 12 - Movement Lesson Cache-Fix Protected Smoke

## Task Summary

Requested Lane 12 restart and authenticated protected-preview browser smoke for the Movement Lesson Card cache-bust fix.

Completed:

- Verified branch `feature/answer-api`.
- Verified current repo HEAD `5988431`.
- Verified required cache-bust commit `681705c` is an ancestor of HEAD.
- Confirmed the LaunchDaemon-supervised protected-preview runtime was stale at `a2f3b81`.
- Restarted the normal protected-preview runtime by terminating the stale `127.0.0.1:8770` listener and allowing `com.steelguitarrag.private-preview` to restart it.
- Verified local `/api/version` now reports `5988431`.
- Ran authenticated protected-preview browser smoke through Cloudflare Access.
- Confirmed the protected browser loads `answer-client.js?v=movement-lesson-card-29bfd24`.
- Confirmed the protected browser does not load the stale `answer-client.js?v=e9-explorer-home-entry-20260623`.
- Ran the full requested prompt matrix.
- Captured protected-preview screenshots for key movement, static, and gear scenarios.
- Refreshed `docs/handoffs/task-completions/integration-status.md`.

Intentionally not changed:

- No backend, UI, auth, DNS, tunnel, deployment architecture, corpus, scraping, embeddings, Chroma/vector store, private transcript, licensing metadata, or unrelated asset files were modified.
- No API fallback was used as proof of browser behavior.

## Smoke Target

- Target type: protected-preview browser smoke
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=movement-lesson-card-29bfd24-cachefix`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=movement-lesson-card-29bfd24-cachefix`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=movement-lesson-card-29bfd24-cachefix`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; app shell loaded and Q&A was usable in the authenticated browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected repo/runtime HEAD: `5988431`
- Required cache-bust commit: `681705c`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"5988431","git_branch":"feature/answer-api","server_started_at":"2026-07-01T06:34:23.251068+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- Loaded answer-client.js URL: `https://app.steelguitarrag.com/ui/answer-client.js?v=movement-lesson-card-29bfd24`
- Stale answer-client.js URL status: `answer-client.js?v=e9-explorer-home-entry-20260623` was not loaded
- Whether app root `/` works: yes, as a redirect to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as a redirect, not as the canonical cache-busted target
- Root URL behavior: `https://app.steelguitarrag.com/?v=movement-lesson-card-29bfd24-cachefix` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html` and dropped the query string
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes; direct `/ui/...?...` remains the canonical cache-busted smoke URL
- API fallback status: not used
- Who should test this URL: the user may run user smoke at the direct cache-busted `/ui/...` URL
- Do not test these URLs: root-only URL when exact cache-busting matters, because root drops query strings during redirect
- Known caveats: root drops query strings; use the direct `/ui/steel-guitar-rag-mock.html?...` URL for exact cache-busted smoke

## Runtime Restart Evidence

Before restart:

- `/api/version`: `a2f3b81`
- Listener PID: `72790`
- Listener command: `scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 ... --answer-auth-mode production --auth-provider cloudflare-access`
- LaunchDaemon: `system/com.steelguitarrag.private-preview`, state `running`

Restart action:

- Terminated stale listener PID `72790`.
- LaunchDaemon restarted the protected-preview process automatically.

After restart:

- `/api/version`: `5988431`
- Listener PID: `86270`
- Start time: `Tue Jun 30 23:34:22 2026`
- `server_started_at`: `2026-07-01T06:34:23.251068+00:00`
- Branch: `feature/answer-api`
- Auth provider: `cloudflare_access`
- Retrieval mode: `hybrid_private_first`

## Protected Browser Result

Overall result: PASS.

The previous stale runtime and stale `answer-client.js` blocker are resolved. Movement prompts render Movement Lesson Cards in the protected authenticated browser.

Observed protected page scripts:

```text
https://app.steelguitarrag.com/ui/answer-client.js?v=movement-lesson-card-29bfd24
https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=e9-explorer-home-entry-20260623
https://static.cloudflareinsights.com/beacon.min.js/v4513226cdae34746b4dedf0b4dfa099e1781791509496
```

## Prompt Results

| Prompt | Result | Browser observations |
| --- | --- | --- |
| `Show me a G to C move.` | PASS | Movement Lesson Card visible; deterministic tab visible; matching fretboard visible; source cards hidden; tab `white-space: pre`; no `[object Object]`. |
| `Show me a G to D move.` | PASS | Movement Lesson Card visible for G I-V; deterministic tab visible; matching fretboard visible; source cards hidden; tab monospace/pre preserved. |
| `Show me a 1 to 4 move in G.` | PASS | Routed to G I-IV; Movement Lesson Card visible; deterministic tab and fretboard visible; no source-card support implied. |
| `Show me a 1 to 5 move in G.` | PASS | Routed to G I-V; Movement Lesson Card visible; deterministic tab and fretboard visible; no source-card support implied. |
| `Show me a 1 4 5 1 move in G.` | PASS | Four-event Movement Lesson Card visible; deterministic tab visible; matching fretboard visible; source cards hidden. |
| `How do I connect no-pedals to A+B positions?` | PASS | Defaults to G I-IV; Movement Lesson Card visible; deterministic tab and matching fretboard visible; source cards hidden. |
| `Show me a G major grip.` | PASS | Static grip answer stayed fretboard-first; no visible tab block; no Movement Lesson Card; no `[object Object]`. |
| `Where is G on E9?` | PASS | Defaults to full G major starter positions, not 5-7-8 open; no visible tab block; no Movement Lesson Card. |
| `Show me a 5-7-8 G grip.` | PASS | Explicit 5-7-8 remains partial/color/no-3rd; no inert A+B; no visible tab block; no Movement Lesson Card. |
| `What are good Fender Steel King settings?` | PASS | Concrete Buddy Emmons source-backed settings block; no Movement Lesson Card; no tab; no answer-fretboard/stale fretboard UI; source cards support the answer. |

Additional checks:

- Supported movement prompts showed `.movement-lesson-card`.
- Movement cards included the move, start/resolution idea, event steps/path, `Tab ↔ fretboard`, and `Practice it slowly`.
- Movement prompts showed deterministic tab plus matching fretboard support.
- Tab blocks used monospace font and `white-space: pre`.
- Movement examples did not show source cards as if they supported deterministic original tab.
- Static G grip/location prompts remained fretboard-first and did not show tab by default.
- `Where is G on E9?` defaulted to full G major positions.
- Explicit `5-7-8` G remained partial/color/no-3rd with no inert A+B.
- Fender Steel King settings returned the concrete Buddy Emmons source-backed block.
- Gear answer did not show stale tab/fretboard/movement UI.
- No visible `[object Object]`.
- Browser console warnings/errors: none recorded.

## Screenshots

- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-g-to-c-movement-lesson-cachefix.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-1451-movement-lesson-cachefix.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-static-g-major-cachefix.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-steel-king-cachefix.png`

## Files Changed

- `docs/handoffs/task-completions/2026-06-30-2337-12-movement-lesson-cachefix-protected-smoke.md`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-g-to-c-movement-lesson-cachefix.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-1451-movement-lesson-cachefix.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-static-g-major-cachefix.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-steel-king-cachefix.png`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files:

- None.

Generated artifacts:

- Four protected-preview smoke screenshots listed above.

## Tests And Checks

- `git status --short` - run before and after; broad unrelated dirty/untracked work remains parked.
- `git branch --show-current` - `feature/answer-api`.
- `git rev-parse --short HEAD` - `5988431` before the docs-only smoke commit.
- `git log --oneline -8` - confirmed `5988431`, `681705c`, `6202c18`, `a2f3b81`, and `29bfd24`.
- `git merge-base --is-ancestor 681705c HEAD` - PASS, current HEAD contains required cache-bust commit.
- `git status --short -- 'pocketsteel/*.py' 'ui/*.js' 'scripts/*.py' tests` - no dirty runtime-affecting files.
- `curl -sS http://127.0.0.1:8770/api/version` before restart - stale `a2f3b81`.
- `lsof -nP -iTCP:8770 -sTCP:LISTEN` before restart - PID `72790`.
- `launchctl print system/com.steelguitarrag.private-preview` - state `running`.
- Terminated stale listener PID `72790`; launchd restarted the app.
- `curl -sS http://127.0.0.1:8770/api/version` after restart - PASS, `5988431`.
- `lsof -nP -iTCP:8770 -sTCP:LISTEN` after restart - PID `86270`.
- Protected-preview browser smoke through Cloudflare Access - PASS.
- Protected page script inspection - PASS, loaded `answer-client.js?v=movement-lesson-card-29bfd24`.
- Browser root behavior check - root redirects to `/ui/steel-guitar-rag-mock.html` and drops query string.
- Browser console warning/error read - none recorded.
- `git diff --check` - PASS.

Skipped:

- No implementation tests were rerun in Lane 12 because this task changed no app code. Lane 06 already recorded focused test pass for the cache-bust implementation.
- API fallback was not used.

## Integration Notes

- Protected preview now serves runtime HEAD `5988431`.
- Runtime includes required cache-bust commit `681705c`.
- The stale `answer-client.js` blocker is resolved in protected preview.
- The direct cache-busted `/ui/steel-guitar-rag-mock.html` URL is ready for user smoke.
- Root continues to drop query strings during redirect, so direct `/ui/...?...` should be used when cache-busting matters.

## Risk Assessment

Risk: low.

Why:

- Lane 12 only restarted the existing LaunchDaemon-supervised app and wrote docs/screenshots.
- No app implementation, auth, DNS, tunnel, corpus, Chroma/vector, scraping, private transcript, licensing, or secret files were changed.

Rollback:

- If needed, revert the docs-only smoke/status commit.
- Runtime rollback would require checking out a prior commit and restarting the LaunchDaemon; no rollback is recommended because smoke passed.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-30-2337-12-movement-lesson-cachefix-protected-smoke.md`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-g-to-c-movement-lesson-cachefix.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-1451-movement-lesson-cachefix.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-static-g-major-cachefix.png`
- `docs/handoffs/task-completions/assets/2026-06-30-movement-lesson-cachefix-protected-smoke/protected-steel-king-cachefix.png`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Existing unrelated parked dirty/untracked files in `README.md`, `corpus_metadata/`, `docs/`, `rag_*.py`, `source-inbox/`, `ui/brand/`, `public/brand/`, `Neon Sign/`, corpus/private/vector/scraper/auth/deploy/source-data paths, and generated/private artifacts.
- Existing untracked handoffs/screenshots from prior work unless a separate task explicitly scopes them.

## Recommended Next Lane

User smoke, then Lane 01 integration-status/closeout only if user smoke adds a new status update.

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke at:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=movement-lesson-card-29bfd24-cachefix
```
