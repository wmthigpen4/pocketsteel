# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current State

- Current branch: `feature/answer-api`.
- Current repo HEAD at this refresh: `5a59739 docs: refresh integration status after compact explorer UI`.
- Runtime commit smoked for E9 copedent selector/chart: `ecec173 feat: add E9 copedent selector and chart`.
- Related impact-preview runtime smoke: `670d635 feat: add e9 pedal lever impact preview contract`.
- Latest local UI smoke status: **PASS for compact Explorer/copedent controls at commit `9a3513b`**.
- Protected-preview status: **blocked before smoke**. Lane 12 verified the LaunchDaemon runtime is still serving `ffac52a`; the documented non-interactive restart attempt could not run because `sudo` requires a password in this shell.
- User-smoke status: **hold for compact Explorer/copedent UI until `/api/version` reports `5a59739` and protected-preview smoke passes**.
- App control state: **park or choose the next small slice**.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage.

## Protected URLs

Use direct `/ui/...?...` URLs for cache-busted validation after Cloudflare Access login:

```text
Explorer copedent selector/chart:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625

Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=explorer-compact-copedent-20260625

Root:
https://app.steelguitarrag.com/?v=explorer-compact-copedent-20260625
```

Root caveat:

- Root redirects to `/ui/steel-guitar-rag-mock.html`.
- Root drops query strings during redirect.
- Direct `/ui/...?...` URLs remain required when exact cache-busting matters.

## E9 Copedent Selector Status

Selector status: **PASS**.

Recorded behavior:

- `Emmons E9` is visible and selected by default.
- `Day E9` is visible and selectable.
- `My Copedent (E9)` is visible but disabled.
- Backstage/coming-soon copy is visible for the disabled personal copedent option.
- C6 is not exposed as an active Explorer copedent option.
- Existing Explorer key/scale/harmony/string-group controls remain available.
- No `[object Object]` was reported in the accepted selector/chart smoke.

## E9 Copedent Chart Status

Chart status: **PASS**.

Recorded behavior:

- Visual copedent chart renders in the Explorer.
- Chart shows strings 1-10.
- Chart shows open notes.
- Chart shows control columns for pedals and knee levers.
- Chart shows physical positions such as `P1`, `P2`, `P3`, `LKL`, `LKR`, `LKV`, `RKR`, and `RKL`.
- Chart shows note movement cells such as `B -> C#`, `E -> F`, `E -> Eb/D#`, `D -> C#`, and raise/lower labels.
- Day E9 switches physical pedal order to C-B-A while preserving named A/B/C semantics.
- Right-knee lever controls appear where present in the contract.

## Pedal / Lever Impact Preview Status

Impact preview status: **PASS with provenance caveat from earlier Lane 12 evidence**.

Recorded behavior:

- `Pedal and lever impact preview` section renders.
- Preview cards render A pedal, B pedal, C pedal, E-raise lever, and E-lower lever.
- Preview shows affected strings and before/after changes such as `B -> C#`, `G# -> A`, `E -> F#`, `E -> F`, and `E -> Eb/D#`.
- Selected-row detail renders `Changes used here`.
- Row-level active controls show string-level pedal effects.
- Explorer filtering remained functional during impact-preview smoke, including `5-7-8` reducing visible cards to that group.
- No `[object Object]` and no relevant console/page errors were reported.

Known impact-preview caveat:

- Earlier protected-preview impact-preview evidence was gathered while serving scoped Lane 06 Explorer UI worktree assets. The later copedent selector/chart commit now contains the selector/chart UI baseline, but future user-smoke defects should still be routed by exact slice rather than broad feature work.

## Compact Explorer / Copedent Controls Status

Local smoke status at commit `9a3513b`: **PASS**.

Protected-preview status at commit `5a59739`: **BLOCKED BEFORE SMOKE**.

Lane 12 blocker summary:

- Repo HEAD: `5a59739`.
- Expected runtime: `5a59739`.
- Actual `/api/version`: `ffac52a`.
- LaunchDaemon: running as `system/com.steelguitarrag.private-preview`.
- Listener: Python on `127.0.0.1:8770`.
- Documented restart path attempted non-interactively:

```bash
sudo -n launchctl kickstart -k system/com.steelguitarrag.private-preview
```

- Result:

```text
sudo: a password is required
```

No protected-preview browser smoke was run against the stale runtime. The next required action is an interactive Mac mini restart using:

```bash
cd /Users/cory/Documents/Pocket\ Steel
deploy/macos/install-private-preview-launchdaemon.sh restart
curl -sS http://127.0.0.1:8770/api/version
```

Proceed to protected-preview smoke only after `/api/version` reports `5a59739`.

Recorded behavior:

- Copedent chart is hidden by default and opens from a compact `View chart` dialog control.
- `Emmons E9` remains the default and no longer exposes the user-specific LKV/B-to-Bb control.
- `Custom E9 (with LKV)` is selectable and retains the LKV/B-to-Bb setup.
- External E9 reference context is not exposed in Explorer learner-facing UI or payload source context.
- Pedal/lever impact preview is compact by default and opens details from control tabs.
- Fretboard labels use either interval labels or note labels; they do not combine fret numbers with note/interval text.
- Desktop local smoke at 1280x720 showed the fretboard visible without scrolling after the compact control pass.
- Mobile local smoke at 390x844 had no page-level horizontal overflow; the fretboard remains below the first viewport because of normal mobile stacking.

Smoke Target:

```text
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
- Exact URL the user should use: blocked pending LaunchDaemon restart to `5a59739`; intended URL remains https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
- Auth required: no for local smoke / yes for protected preview
- Auth provider: none for local smoke / Cloudflare Access for protected preview
- Cloudflare Access login result: not required for local smoke / not attempted for protected preview
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 9a3513b
- Version endpoint: http://127.0.0.1:8770/api/version
- Version endpoint result: git_sha=ffac52a during pre-commit local smoke; implementation commit after smoke is 9a3513b
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested in this local smoke
- Whether app root `/` is expected to work: yes, protected root redirects to app UI
- Whether `/ui/steel-guitar-rag-mock.html` works: yes, local entry smoke passed at http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=explorer-compact-copedent-20260625
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Lane 12 first, then the user
- Do not test these URLs: uncache-busted Explorer URLs for this slice
- Known caveats: local smoke is not protected-preview smoke; Lane 12 restart is currently blocked by interactive sudo requirement; user smoke remains on hold
```

## Latest Relevant Handoffs

- `docs/handoffs/task-completions/2026-06-23-12-e9-copedent-selector-protected-smoke.md`
- `docs/handoffs/task-completions/2026-06-23-15-e9-copedent-selector-qa.md`
- `docs/handoffs/task-completions/2026-06-23-06-e9-copedent-selector-chart.md`
- `docs/handoffs/task-completions/2026-06-24-12-e9-pedal-lever-impact-preview-protected-smoke.md`
- `docs/handoffs/task-completions/2026-06-24-1045-06-e9-pedal-lever-impact-preview-ui.md`
- `docs/handoffs/task-completions/2026-06-25-1920-06-explorer-compact-copedent-ui.md`
- `docs/handoffs/task-completions/2026-06-25-2045-12-explorer-compact-copedent-protected-smoke.md`

## Remaining Caveats

- Root URL redirects to `/ui/steel-guitar-rag-mock.html` and drops query strings.
- Direct `/ui/...?...` URLs remain required for cache-busted smoke.
- `deploy/macos/install-private-preview-launchdaemon.sh status` and `restart` need interactive sudo in this environment. Lane 12 could verify runtime health with `launchctl`, `lsof`, `ps`, and `/api/version`, but could not restart the LaunchDaemon non-interactively.
- Current protected-preview runtime is stale at `ffac52a` until the interactive restart is run.
- Broad unrelated dirty/untracked files remain parked.

## Current Git / Worktree Notes

Current checked state at this refresh:

- Branch: `feature/answer-api`.
- Repo HEAD before this docs refresh: `5a59739`.
- Cached index before this docs refresh: empty.
- `git diff --check`: to be run for this docs refresh.

Broad parked dirty/untracked work remains outside this refresh, including:

- README/docs/provenance/legal/source-policy edits.
- Corpus metadata and source-inbox metadata.
- Root RAG/corpus helper scripts.
- Private/corpus-adjacent scripts and data.
- Landing/sign/brand assets and generated visual files.
- Historical untracked handoffs and screenshot/report assets.

Do not stage parked work unless a later exact-scope handoff approves it.

## Safe To Stage For This Refresh

- `docs/handoffs/task-completions/integration-status.md`
- no new handoff required; this is the integration-status refresh after `9a3513b`

## Files Not To Stage For This Refresh

- Backend/runtime files, tests, UI files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, paid transcript files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Unrelated handoffs or generated reports.

## Recommended Next Slice

Run an interactive Mac mini LaunchDaemon restart so `/api/version` reports `5a59739`, then rerun Lane 12 protected-preview smoke. Resume user smoke only if protected-preview evidence passes.

Recommended next slice if continuing:

- Lane 12 Self-Hosted Deployment: restart/verify the launchd-supervised protected preview against `5a59739` and smoke the cache-busted Explorer URL.

Recommended exact control step:

```text
Lane 12: after an interactive Mac mini restart makes /api/version report 5a59739, smoke https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625 and the main app entry URL.
```
