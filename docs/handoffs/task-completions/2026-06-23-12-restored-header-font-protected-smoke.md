# 2026-06-23 Lane 12 Restored Header Font Protected Smoke

## Task Summary

Requested Lane 12 protected-preview verification for `706d8cd fix: restore accepted header button font`.

Completed:
- Confirmed repo HEAD is `706d8cd`.
- Confirmed the launchd-supervised protected-preview runtime was stale at `b547178`.
- Refreshed the LaunchDaemon-owned process so local `/api/version` reports `706d8cd`.
- Verified Cloudflare Access-authenticated app, root redirect, and Explorer routes.
- Verified the header buttons use the restored inherited typography behavior from the accepted historical state.
- Ran the requested prompt spot checks through the authenticated browser UI.

Intentionally not changed:
- No app code, UI logic, backend logic, DNS, Cloudflare Access policy, tunnel configuration, secrets, corpus, Chroma/vector stores, embeddings, scraping, private transcript/source data, or unrelated dirty files.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=706d8cd`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=706d8cd`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=706d8cd`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `706d8cd`
- Version endpoint: `/api/version`
- Version endpoint result: local supervised origin returned `git_sha: 706d8cd`, `git_branch: feature/answer-api`, `auth_provider: cloudflare_access`, `retrieval_mode: hybrid_private_first`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as an entry redirect, not as the canonical cache-busted smoke URL
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: do not use unauthenticated API fallback as browser smoke
- Known caveats: root redirect drops the `?v=706d8cd` query string

## Runtime And Launchd Evidence

- Branch: `feature/answer-api`
- Starting HEAD: `706d8cd`
- Runtime commit expected: `706d8cd`
- Runtime before refresh: `/api/version` reported `b547178`
- Runtime after refresh: `/api/version` reported `706d8cd`
- Server started at: `2026-06-23T22:25:44.573765+00:00`
- LaunchDaemon: `system/com.steelguitarrag.private-preview`
- LaunchDaemon path: `/Library/LaunchDaemons/com.steelguitarrag.private-preview.plist`
- LaunchDaemon state after refresh: running
- Listener after refresh: Python PID `26925` on `127.0.0.1:8770`
- PID start time: `Tue Jun 23 17:25:44 2026`
- Durable stdout log: `~/Library/Logs/steel-guitar-rag/app.out.log`
- Durable stderr log: `~/Library/Logs/steel-guitar-rag/app.err.log`
- Manual `screen` runtime: absent
- Cloudflare Tunnel status: cloudflared process present; token contents were not recorded
- Service helper caveat: `deploy/macos/install-private-preview-launchdaemon.sh status` requires sudo in this shell and failed non-interactively. `deploy/macos/install-private-preview-launchdaemon.sh version`, `launchctl print`, listener checks, and local `/api/version` supplied runtime evidence.

## Header Button Font Result

Protected app URL checked:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=706d8cd
```

Observed header controls:
- `Explore Fretboard`
- `Get a Backstage Pass` before unlock, then `Go Backstage` after unlock

Computed font family for both header controls:

```text
"Gill Sans", "Gill Sans MT", "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif
```

Computed shared button metrics before unlock:
- `font-size: 16px`
- `font-weight: 400`
- `line-height: normal`
- `letter-spacing: normal`
- `padding: 0px 16px`
- `border-radius: 999px`
- `height: 42px`
- matching top alignment
- one SVG icon per header control

Result:
- Pass with caveat.
- Both header controls use the restored inherited app-page typography behavior.
- The rejected explicit neutral stack from `b547178` is gone.
- `.header-action-button` no longer presents the `-apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` explicit neutral stack.
- `Explore Fretboard` remains visible in the upper-right header area.
- `Explore Fretboard` links to `/ui/e9-fretboard-explorer.html`.
- `Go Backstage` remains a separate header action and still opens/toggles Backstage/settings.

Product caveat:
- The restored historical behavior inherits the app page font stack, whose root variable begins with Gill Sans.
- This is the requested prior accepted mechanism from git history.
- If user smoke still rejects this typography, the next step is a product decision for the exact explicit button font before another Lane 06 pass.

## Root Result

Root URL checked:

```text
https://app.steelguitarrag.com/?v=706d8cd
```

Result:
- Cloudflare Access session succeeded.
- Root redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Query string was dropped by the redirect.
- App shell still loaded.

## Explorer Result

Explorer URL checked:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=706d8cd
```

Result:
- Explorer loaded through Cloudflare Access.
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`.
- 12 combined key choices were present:
  - `C`
  - `C# (or D♭)`
  - `D`
  - `D# (or E♭)`
  - `E`
  - `F`
  - `F# (or G♭)`
  - `G`
  - `G# (or A♭)`
  - `A`
  - `A# (or B♭)`
  - `B`
- No duplicate accidental key list was detected.
- Harmony/View selector contains only:
  - `2-string harmonized scale`
  - `3-string diatonic harmony`
- No standalone `5&8 branch` option appears in Harmony/View.
- `5-7-8` remains present only as a string-group option, as expected.
- Bad internal deterministic/source-card copy remained absent.
- No `[object Object]`.
- No relevant browser console errors.

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
- Answer refused full copyrighted song tab / full modern arrangement / full solo or YouTube/recording transcription.
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
git log -10 --oneline
git diff --name-only
git diff --cached --name-only
launchctl print system/com.steelguitarrag.private-preview
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh version
curl -sS http://127.0.0.1:8770/api/version || true
lsof -nP -iTCP:8770 -sTCP:LISTEN || true
ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command || true
screen -ls || true
pgrep -fl cloudflared || true
git diff --check
```

Browser checks run:
- Protected main app URL load.
- Header button computed style inspection.
- Backstage/Q&A unlock behavior.
- Root redirect behavior.
- Explorer URL load.
- Explorer key/control inspection.
- Three prompt spot checks through authenticated browser UI.
- Console error checks on app and Explorer pages.

Result:
- `git diff --check` passed before handoff creation.
- Browser smoke passed with the product caveat noted above.

Skipped:
- Broad test suite was not run because this was a protected-preview deployment smoke verification, not an implementation change.
- No API fallback was used as browser-smoke proof.

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-23-12-restored-header-font-protected-smoke.md`

Modified:
- None.

Deleted:
- None.

Generated artifacts:
- None.

## Integration Notes

- Protected preview is now serving `706d8cd`.
- The restored inherited header typography behavior is verified live through Cloudflare Access.
- The rejected explicit neutral system stack from `b547178` is no longer present.
- Root still drops the cache-bust query on redirect. Use the direct `/ui/steel-guitar-rag-mock.html?v=706d8cd` URL when exact asset/runtime cache-busting matters.
- The inherited Gill Sans stack caveat is intentional for this slice and should be evaluated by user smoke.

## Risk Assessment

Risk: low.

Reason:
- The only file change is this docs handoff.
- No app implementation, auth, DNS, Cloudflare, corpus, Chroma/vector, embeddings, scraping, private-source, or generated data files were changed.
- The only runtime mutation was terminating the stale listener process so the already-installed LaunchDaemon restarted the current HEAD.

Rollback note:
- If the runtime must be reverted, Lane 12 should use the documented LaunchDaemon workflow after restoring the intended repo revision, then verify `/api/version` and protected-preview behavior again.

## Human Decision Needed

No for deployment smoke.

Potential product decision:
- Yes only if user smoke rejects the restored inherited Gill Sans-backed typography. In that case, decide the exact explicit button font before returning to Lane 06.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-restored-header-font-protected-smoke.md`

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

- User smoke the header buttons first.
- If accepted, Lane 01 Repo Steward can refresh `docs/handoffs/task-completions/integration-status.md`.
- If rejected, Lane 18 or the user should make the explicit typography product decision, then Lane 06 should implement it.

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=706d8cd
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=706d8cd
```

If accepted, run Lane 01 integration-status refresh for `706d8cd`.
