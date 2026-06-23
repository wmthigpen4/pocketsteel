# 2026-06-23 Lane 12 Header Button Font Protected Smoke

## Task Summary

Requested Lane 12 protected-preview verification for `b547178 fix: use plain UI font for header buttons`.

Completed:
- Refreshed the launchd-supervised protected-preview runtime because it was still serving `fd342b9`.
- Verified local `/api/version` from the supervised origin reports `b547178`.
- Verified Cloudflare Access-authenticated app and Explorer URLs load.
- Verified the header action buttons use the neutral system UI font stack rather than Gill Sans, `var(--font-ui)`, or decorative display styling.
- Ran minimal browser spot checks for a static grip, a movement tab/fretboard answer, and a blocked copyrighted full-tab request.

Intentionally not changed:
- No app code, UI logic, backend behavior, auth policy, DNS, tunnel configuration, corpus, Chroma/vector data, embeddings, scraping, or private source data.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=b547178`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=b547178`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=b547178`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `b547178`
- Version endpoint: `/api/version`
- Version endpoint result: local supervised origin returned `git_sha: b547178`, `git_branch: feature/answer-api`, `auth_provider: cloudflare_access`, `retrieval_mode: hybrid_private_first`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as an entry redirect, not as the canonical cache-busted smoke URL
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: do not use unauthenticated API fallback as browser smoke
- Known caveats: root redirect drops the `?v=b547178` query string

## Runtime And Launchd Evidence

- Branch: `feature/answer-api`
- Starting HEAD: `b547178`
- Runtime before refresh: `/api/version` reported `fd342b9`
- Runtime after refresh: `/api/version` reported `b547178`
- LaunchDaemon: `system/com.steelguitarrag.private-preview`
- LaunchDaemon state after refresh: running
- Listener after refresh: Python PID `9695` on `127.0.0.1:8770`
- PID start time: `Tue Jun 23 17:15:17 2026`
- Server started at: `2026-06-23T22:15:18.402071+00:00`
- Durable stdout log: `~/Library/Logs/steel-guitar-rag/app.out.log`
- Durable stderr log: `~/Library/Logs/steel-guitar-rag/app.err.log`
- Cloudflare Tunnel status: cloudflared process present; token contents were not recorded
- Service helper caveat: `deploy/macos/install-private-preview-launchdaemon.sh status` still requires sudo in this shell, but `launchctl print` and local `/api/version` confirmed the running LaunchDaemon.

## Header Button Font Result

Protected app page checked:
- `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=b547178`

Observed header controls:
- `Explore Fretboard`
- `Go Backstage`

Computed font family for both controls:

```text
-apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif
```

Result:
- Both controls used the same neutral system UI stack.
- No computed Gill Sans font was present.
- No `var(--font-ui)` unresolved value was present.
- No decorative/display font was present.
- Both controls matched on `font-size: 14px`, `font-weight: 800`, `padding: 0px 16px`, `border-radius: 999px`, `height: 42px`, and top alignment.
- Both controls included one SVG icon.
- `Explore Fretboard` linked to `/ui/e9-fretboard-explorer.html`.
- `Go Backstage` toggled/unlocked the protected Q&A path.

## Root And Explorer Result

Root URL checked:
- `https://app.steelguitarrag.com/?v=b547178`

Result:
- Cloudflare Access session succeeded.
- Root redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Query string was dropped by the redirect.
- App shell still loaded and Q&A was available after Backstage activation.

Explorer URL checked:
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=b547178`

Result:
- Explorer page loaded.
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`.
- Back navigation link was present.
- No `[object Object]`.
- No browser console errors were recorded.

## Prompt Spot Checks

### `Show me a G major grip.`

- Pass.
- Answer was direct and teacher-facing.
- Fretboard rendered.
- No visible tab card rendered.
- No generic fallback appeared.
- No `[object Object]`.
- App showed the standard "No sources returned" source-note placeholder; no actual source cards were returned.

### `Show me a G to C move.`

- Pass.
- Answer was direct and teacher-facing.
- Deterministic tab rendered.
- Fretboard rendered.
- Tab and fretboard both described the same G-to-C movement.
- No generic fallback appeared.
- No `[object Object]`.
- App showed the standard "No sources returned" source-note placeholder; no actual source cards were returned.

### `Give me the full tab for a modern copyrighted song.`

- Pass.
- Answer refused full copyrighted song tab / full modern arrangement / solo or recording transcription.
- Safe alternatives were shown.
- No tab rendered.
- No fretboard rendered.
- No generic fallback appeared.
- No `[object Object]`.
- App showed the standard "No sources returned" source-note placeholder; no actual source cards were returned.

## Tests And Checks

Commands/checks run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log --oneline -10
git diff --name-only
git diff --cached --name-only
launchctl print system/com.steelguitarrag.private-preview
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh version
curl -sS http://127.0.0.1:8770/api/version || true
lsof -nP -iTCP:8770 -sTCP:LISTEN
ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command
screen -ls
pgrep -fl cloudflared
git diff --check
```

Browser checks run:
- Protected app URL load.
- Header button computed style inspection.
- Root redirect behavior.
- Backstage/Q&A unlock behavior.
- Explorer URL load.
- Three prompt spot checks through authenticated browser UI.
- Console error checks on app and Explorer pages.

Result:
- `git diff --check` passed before handoff creation.
- Browser smoke passed.

Skipped:
- Broad test suite was not run because this was a deployment/protected-preview smoke verification, not an implementation change.
- Protected `/api/version` direct browser navigation was blocked by the browser client; local origin `/api/version` was used to verify the launchd-supervised runtime.

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-23-12-header-button-font-protected-smoke.md`

Modified:
- None.

Deleted:
- None.

Generated artifacts:
- None.

## Integration Notes

- The protected-preview origin is now refreshed to `b547178`.
- Header button font styling is verified live through Cloudflare Access.
- Root is usable as an entry point but drops cache-bust query strings; the canonical smoke URL remains the direct `/ui/steel-guitar-rag-mock.html?v=b547178` URL.
- The prompt spot checks did not identify a Lane 05 or Lane 06 blocker.

## Risk Assessment

Risk: low.

Reason:
- This was a docs-only handoff plus read-only smoke after a launchd-managed runtime refresh.
- No app code or configuration was changed.
- The only operational mutation was terminating the stale listener process so launchd could restart the already-installed service from current HEAD.

Rollback note:
- If the runtime needs to return to a previous commit, Lane 12 should use the documented LaunchDaemon workflow after checking out the intended commit or restoring the intended runtime revision.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-header-button-font-protected-smoke.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files shown by `git status --short`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- scraper output
- private source data
- credentials, tokens, env files, and logs
- Cloudflare/DNS/auth configuration
- app implementation files not explicitly scoped to this handoff

## Recommended Next Lane

Lane 01 Repo Steward, only if integration status should be refreshed after this smoke result.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 01: refresh `docs/handoffs/task-completions/integration-status.md` with the `b547178` protected-preview smoke result if the current coordination protocol requires the status update now.
