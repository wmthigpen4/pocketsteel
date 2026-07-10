# Melody Studio background protected smoke

## Task summary

Verified the committed Melody Studio brand/background user-smoke adjustment after the user restarted the protected-preview LaunchDaemon. The protected runtime reports commit `6f95e9f`, Cloudflare Access served the enabled Studio, the page uses the E9 Fretboard Explorer gradient without a background image, and no `The Turnaround` text remains.

## Files changed

- `docs/handoffs/task-completions/2026-07-10-1404-12-melody-studio-background-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

No implementation files were changed during protected smoke.

## Tests and checks

- Loopback `/api/version` — passed; returned `6f95e9f`, branch `feature/answer-api`, Cloudflare Access auth, and `features.melodyExercise=true`.
- Authenticated protected browser smoke — passed at the exact cache-busted Melody Studio URL.
- DOM verification — passed; guided task cards rendered, proving the feature-enabled authenticated state.
- Computed-style verification — passed; body background contains the Explorer radial and linear gradients and no image URL.
- Copy verification — passed; no `The Turnaround` text.
- Rendering hygiene — passed; no `[object Object]`.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-studio-background-6f95e9f-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-studio-background-6f95e9f-20260710`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; the authenticated feature-enabled workflow rendered
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `6f95e9f36577cfde65ebbc90736aef30a523517a`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `6f95e9f`, expected branch/auth/feature values
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: previously verified for this service; not repeated in the focused browser adjustment smoke
- Whether app root `/` is expected to work: yes; it redirects to the home UI
- Whether `/ui/steel-guitar-rag-mock.html` works: previously verified; not the focused target
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: stale URL ending in `4a00fc2` or uncached file URLs
- Known caveats: direct navigation to the JSON session endpoint was blocked by browser-client policy; the feature-enabled authenticated Studio rendering and loopback version endpoint provide the relevant smoke evidence

## Integration notes

User smoke may continue. The restart helper remains a system LaunchDaemon command and therefore prompts for an administrator password. Credentials must not be stored in an env file. A separately approved deployment/security task can add a narrowly scoped sudoers rule or redesign the service as a user LaunchAgent.

## Risk assessment

Low. This task only verified the committed UI change and refreshed coordination docs.

## Human decision needed

No for Melody Studio user smoke. Yes only if the user wants to authorize a separate privileged restart-automation change.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-10-1404-12-melody-studio-background-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty/untracked files, especially corpus, source-inbox, brand binaries, private/generated content, auth material, and deployment assets.

## Recommended next lane

01 Repo Steward exact-path documentation commit; then resume user smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the smoke handoff and integration refresh, then give the user the exact cache-busted Studio URL. Treat any reported issue as the next scoped autopilot repair.
