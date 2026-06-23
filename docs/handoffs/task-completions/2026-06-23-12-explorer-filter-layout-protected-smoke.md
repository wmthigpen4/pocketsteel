# 2026-06-23 Lane 12 Explorer Filter Layout Protected Smoke

## Task Summary

Requested Lane 12 protected-preview verification for `f2581f8 fix: clarify explorer filters and advanced swaps`.

Completed:
- Confirmed repo HEAD is `f2581f8`.
- Confirmed the launchd-supervised protected-preview runtime was stale at `706d8cd`.
- Refreshed the LaunchDaemon-owned process so local `/api/version` reports `f2581f8`.
- Verified Cloudflare Access-authenticated Explorer, main app, and root redirect behavior.
- Verified Explorer filter layout, 5&8 grouping, Advanced swaps copy, and key-selector behavior through the protected preview.
- Ran the requested optional prompt spot checks through the authenticated browser UI.

Intentionally not changed:
- No app code, UI logic, backend logic, DNS, Cloudflare Access policy, tunnel configuration, secrets, corpus, Chroma/vector stores, embeddings, scraping, private transcript/source data, or unrelated dirty files.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=f2581f8`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=f2581f8`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=f2581f8`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `f2581f8`
- Version endpoint: `/api/version`
- Version endpoint result: local supervised origin returned `git_sha: f2581f8`, `git_branch: feature/answer-api`, `auth_provider: cloudflare_access`, `retrieval_mode: hybrid_private_first`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as an entry redirect, not as the canonical cache-busted smoke URL
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: do not use unauthenticated API fallback as browser smoke
- Known caveats: root redirect drops the `?v=f2581f8` query string

## Runtime And Launchd Evidence

- Branch: `feature/answer-api`
- Starting HEAD: `f2581f8`
- Runtime commit expected: `f2581f8`
- Runtime before refresh: `/api/version` reported `706d8cd`
- Runtime after refresh: `/api/version` reported `f2581f8`
- Server started at: `2026-06-23T22:41:33.640600+00:00`
- LaunchDaemon: `system/com.steelguitarrag.private-preview`
- LaunchDaemon path: `/Library/LaunchDaemons/com.steelguitarrag.private-preview.plist`
- LaunchDaemon state after refresh: running
- Listener after refresh: Python PID `54801` on `127.0.0.1:8770`
- PID start time: `Tue Jun 23 17:41:33 2026`
- Durable stdout log: `~/Library/Logs/steel-guitar-rag/app.out.log`
- Durable stderr log: `~/Library/Logs/steel-guitar-rag/app.err.log`
- Manual `screen` runtime: absent
- Cloudflare Tunnel status: cloudflared process present; token contents were not recorded
- Service helper caveat: `deploy/macos/install-private-preview-launchdaemon.sh status` requires sudo in this shell and failed non-interactively. `deploy/macos/install-private-preview-launchdaemon.sh version`, `launchctl print`, listener checks, and local `/api/version` supplied runtime evidence.

## Explorer Filter Layout Result

Protected Explorer URL checked:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=f2581f8
```

Result: pass.

Observed:
- Explorer loaded through Cloudflare Access.
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`.
- Key / Scale / Harmony controls align in the top control row.
- String group appears below Key / Scale / Harmony as its own full-width control section:
  - `label[for="explorer-string-group"]` spans the control row width.
  - Parent `.explorer-control--string-group` spans the control row width.
  - Parent `.explorer-string-group-layout` spans the control row width.
- The native String group select remains `multiple=true`.
- No `[object Object]`.
- No relevant browser console errors.

## 5&8 Grouping Result

Result: pass.

Observed in 3-string view:
- String group optgroups:
  - `Core grips`: `3-4-5`, `4-5-6`, `5-6-8`, `6-8-10`
  - `Advanced swaps`: `5-6-7`, `6-7-10`, `5-7-8`

Observed after switching Harmony/View to `2-string harmonized scale`:
- String group remains a native multi-select.
- String group options include:
  - `All 2-string groups`
  - `3-5`
  - `5-6`
  - `6-10`
  - `4-6`
  - `3-4`
  - `5-8`
- String group optgroups:
  - `2-string groups`
  - `5&8 branch`
- `5-8` appears under String group, not Harmony/View.
- Harmony/View options remain only:
  - `2-string harmonized scale`
  - `3-string diatonic harmony`
- No standalone disabled or greyed `5&8 branch` option appears in Harmony/View.
- No raw visible label `five_eight_branch` appeared.

## Advanced Swaps Copy Result

Result: pass.

Observed learner-facing copy:

```text
5&8 branch: 5-8 appears with the 2-string harmonized-scale groups when those branch positions are available.
```

```text
Advanced swaps: less direct string combinations or lever-pocket routes that can add useful color after the main grips.
```

Internal copy checks:
- No bad deterministic/source-card copy appeared.
- No raw `five_eight_branch` label appeared.
- No duplicate accidental key list appeared.

## Key Selector Result

Result: pass.

12 combined key choices remain present:
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

## Main App Spot Check Result

Main app URL checked:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=f2581f8
```

Result: pass.

Observed:
- Cloudflare Access session succeeded.
- Main app loaded.
- `Explore Fretboard` and `Get a Backstage Pass` / `Go Backstage` remain separate header actions.
- Header buttons retained the latest committed inherited font/style behavior:
  - font stack begins with `"Gill Sans", "Gill Sans MT", "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif`
  - `font-size: 16px`
  - `font-weight: 400`
  - `padding: 0px 16px`
  - `border-radius: 999px`
  - `height: 42px`
  - one SVG icon per control
- `Explore Fretboard` opens `/ui/e9-fretboard-explorer.html`.
- No relevant browser console errors.

## Root Result

Root URL checked:

```text
https://app.steelguitarrag.com/?v=f2581f8
```

Result:
- Cloudflare Access session succeeded.
- Root redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Query string was dropped by the redirect.
- App shell still loaded.

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
- Protected Explorer URL load.
- Explorer filter layout and computed rectangle inspection.
- 3-string and 2-string String group options.
- 5&8 branch grouping.
- Advanced swaps copy.
- Main app header/link spot check.
- Root redirect behavior.
- Three prompt spot checks through authenticated browser UI.
- Console error checks on app and Explorer pages.

Result:
- `git diff --check` passed before handoff creation.
- Browser smoke passed.

Skipped:
- Broad test suite was not run because this was a protected-preview deployment smoke verification, not an implementation change.
- No API fallback was used as browser-smoke proof.

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-23-12-explorer-filter-layout-protected-smoke.md`

Modified:
- None.

Deleted:
- None.

Generated artifacts:
- None.

## Integration Notes

- Protected preview is now serving `f2581f8`.
- Explorer filter layout and copy are verified live through Cloudflare Access.
- Root still drops the cache-bust query on redirect. Use the direct `/ui/e9-fretboard-explorer.html?v=f2581f8` URL when exact asset/runtime cache-busting matters.
- Prompt spot checks did not identify a Lane 05 or Lane 06 blocker.

## Risk Assessment

Risk: low.

Reason:
- The only file change is this docs handoff.
- No app implementation, auth, DNS, Cloudflare, corpus, Chroma/vector, embeddings, scraping, private-source, or generated data files were changed.
- The only runtime mutation was terminating the stale listener process so the already-installed LaunchDaemon restarted the current HEAD.

Rollback note:
- If the runtime must be reverted, Lane 12 should use the documented LaunchDaemon workflow after restoring the intended repo revision, then verify `/api/version` and protected-preview behavior again.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-explorer-filter-layout-protected-smoke.md`

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

- User smoke the Explorer.
- If accepted, Lane 01 Repo Steward can refresh `docs/handoffs/task-completions/integration-status.md`.
- If rejected, route UI/display defects to Lane 06 and runtime/auth/asset-routing defects to Lane 12.

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=f2581f8
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=f2581f8
```

If accepted, run Lane 01 integration-status refresh for `f2581f8`.
