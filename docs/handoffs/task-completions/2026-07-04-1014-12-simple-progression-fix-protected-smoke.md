# 2026-07-04 10:14 - Lane 12 Simple Progression Fix Protected Smoke

## Task Summary

Lane 12 was asked to restart/verify protected preview for the Progression Guide simple-song routing fix and run authenticated protected-preview browser smoke.

Completed:

- Verified current repo HEAD is `15a9c15`.
- Verified required app-code commit `bf26e17` is an ancestor of HEAD.
- Verified protected-preview runtime was stale at `8c2536c`.
- Refreshed the LaunchDaemon-supervised runtime to `15a9c15`.
- Ran authenticated protected-preview browser smoke at the exact cache-busted URL.
- Verified the previous blocker prompt now renders Progression Guide v0 instead of the generic specificity fallback.
- Refreshed integration status.

Intentionally not changed:

- No app runtime, backend, or UI implementation files were modified.
- No Cloudflare Access policy, DNS, secrets, auth configuration, deployment architecture, corpus, scraping, embeddings, Chroma/vector stores, private transcripts, licensing metadata, or unrelated assets were changed.
- No API fallback was used as proof of browser behavior.

## Smoke Target

- Target type: protected-preview browser smoke
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=progression-guide-simple-song-fix`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=progression-guide-simple-song-fix`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=progression-guide-simple-song-fix`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `15a9c15`
- Required app-code commit: `bf26e17`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"15a9c15","git_branch":"feature/answer-api","server_started_at":"2026-07-04T15:13:23.580161+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as redirect; root drops query string
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, canonical cache-busted smoke URL
- Who should test this URL: the user may smoke this direct URL
- Do not test these URLs: root URL for cache-busted validation, because it drops the query string
- Known caveats: root redirect behavior is unchanged

## Runtime Verification

- Branch: `feature/answer-api`
- Starting repo HEAD: `15a9c15`
- Final repo HEAD before docs commit: `15a9c15`
- Expected runtime/app HEAD: `15a9c15`
- Required app-code commit present: yes, `git merge-base --is-ancestor bf26e17 HEAD` returned success
- Runtime before restart: `8c2536c`
- Runtime after restart: `15a9c15`
- Listener after restart: Python on `127.0.0.1:8770`, PID `35350`
- Listener start time: `Sat Jul 4 10:13:23 2026`
- LaunchDaemon: `system/com.steelguitarrag.private-preview`, running, PID `35350`, runs `7`
- Restart notes: `launchctl kickstart -k system/com.steelguitarrag.private-preview` was permission-blocked from this process. The stale user-owned listener process was terminated with `SIGTERM`; the LaunchDaemon `KeepAlive` respawned it on current repo HEAD.

## Protected Browser Results

Loaded frontend assets:

- `https://app.steelguitarrag.com/ui/answer-client.js?v=progression-guide-v0-20260704`
- `https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=explorer-compare-fix-20260702b`

Root behavior:

- `https://app.steelguitarrag.com/?v=progression-guide-simple-song-fix` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- The root redirect drops the query string, so root is not suitable for cache-busted validation.

Console/page errors:

- No relevant browser console errors were recorded.
- No `[object Object]` was observed.

## Prompt Results

| Prompt | Result | Notes |
| --- | --- | --- |
| `How do I move through a simple song progression in G?` | PASS | Renders deterministic G I-IV-V-I Progression Guide v0, fretboard visible, no tab, no source cards, no empty source shell, no specificity fallback. |
| `Show me a 1 4 5 1 progression in G.` | PASS | Renders Progression Guide v0, fretboard visible, no tab, no source shell. |
| `Show me a G C D G progression route.` | PASS | Renders Progression Guide v0, fretboard visible, no tab, no source shell. |
| `Show me a G to C move.` | PASS | Renders Movement Lesson Card plus deterministic tab and matching fretboard; no source shell. |
| `Show me a G major grip.` | PASS | Static fretboard-first response with full 4-5-6 G major grip; no tab, no source shell. |
| `Where is G on E9?` | PASS | Defaults to full G major starter positions; not 5-7-8 open as a full chord; no tab. |
| `Show me a 5-7-8 G grip.` | PASS | Correct partial/color/no-3rd wording, fretboard visible, no tab, no source shell. Generic glossary mentions A+B, but the selected 5-7-8 grip remains open/no-pedals. |
| `What are good Fender Steel King settings?` | PASS | Concrete Buddy Emmons Steel King settings block, source cards secondary, no stale fretboard/tab/progression UI. |

## Screenshots

- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/simple-song-progression-g.png`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/progression-g-1451.png`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/movement-g-to-c.png`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/static-g-major-grip.png`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/explicit-578-g-grip.png`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/steel-king-settings.png`

## Tests And Checks

Run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log --oneline -8`
- `git merge-base --is-ancestor bf26e17 HEAD`
- `curl -sS http://127.0.0.1:8770/api/version`
- `launchctl print system/com.steelguitarrag.private-preview`
- `launchctl kickstart -k system/com.steelguitarrag.private-preview` - permission blocked
- `kill -TERM $(lsof -tiTCP:8770 -sTCP:LISTEN)` - used to let LaunchDaemon respawn stale runtime
- `lsof -nP -iTCP:8770 -sTCP:LISTEN`
- `ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command`
- authenticated protected-preview browser smoke at the exact cache-busted URL
- root redirect check for `https://app.steelguitarrag.com/?v=progression-guide-simple-song-fix`
- browser console error checks
- `git diff --check`

Results:

- Runtime version check passed after refresh: `15a9c15`.
- Browser auth passed.
- All requested protected browser prompt checks passed.
- `git diff --check` passed before docs changes; rerun required after this handoff/status update before commit.

Skipped:

- Full pytest was not rerun in Lane 12; Lane 05 already recorded full local test pass with `890 passed`.

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-07-04-1014-12-simple-progression-fix-protected-smoke.md`

Updated:

- `docs/handoffs/task-completions/integration-status.md`

Generated artifacts:

- Screenshots under `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/`

Deleted:

- None.

## Risk Assessment

Risk: low.

Why:

- No app implementation code was changed in Lane 12.
- The protected runtime is proven current at `15a9c15`.
- The exact previously failing prompt now passes in the authenticated protected browser.
- Regression prompts passed.

Rollback notes:

- No app code rollback is needed for this Lane 12 run.
- If runtime rollback is needed, use the documented private-preview process after checking out the intended repo state.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-07-04-1014-12-simple-progression-fix-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/simple-song-progression-g.png`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/progression-g-1451.png`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/movement-g-to-c.png`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/static-g-major-grip.png`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/explicit-578-g-grip.png`
- `docs/handoffs/task-completions/assets/2026-07-04-simple-progression-fix-protected-smoke/steel-king-settings.png`

## Files That Must Not Be Staged

- Existing unrelated dirty and untracked corpus/provenance/RAG/brand/design/docs files.
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/` raw/provenance files
- `.wrangler/`
- secrets, env files, Cloudflare credentials, auth/DNS/deployment policy files
- existing transient screenshots from prior smoke runs not listed above

## Recommended Next Lane

Lane 15 QA / Answer Eval or user smoke.

Suggested next step:

```text
User smoke the protected preview at:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=progression-guide-simple-song-fix

Focus on progression-guide prompts, movement-card regressions, static G fretboard cards, explicit 5-7-8 partial/no-3rd behavior, and Fender Steel King settings.
```

## Commit Readiness

Safe to commit with exact-path staging only after `git diff --check` and `git diff --cached --check` pass.
