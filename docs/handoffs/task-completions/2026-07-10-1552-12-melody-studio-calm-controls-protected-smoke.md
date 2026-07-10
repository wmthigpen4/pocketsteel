# Melody Studio calm controls protected smoke

## Task summary

Authenticated protected-preview smoke passed for the simplified Melody Studio controls at runtime commit `d41a9a9`. User smoke may continue.

## Files changed

- this handoff
- `docs/handoffs/task-completions/integration-status.md`

## Tests and checks

- Focused frontend/same-origin suite: 41 passed.
- Full pytest: 918 passed.
- Core JavaScript syntax: passed.
- `/api/version`: `d41a9a9`, expected branch/auth/feature state.
- Authenticated protected browser smoke: passed.

## Protected results

- Task cards hide after task selection and do not remain above the editor/result.
- Phrase renders one simple button per note with token and resolved pitch; no nested per-chip buttons.
- Selecting the third note and choosing Move up one octave visibly changed it from G4 to G5.
- The Selected note toolbar exposes six plain-language actions in one location.
- The editor explains that later automatic notes may follow an octave override to keep the path smooth.
- Result shows only Single Note and Recommended Harmony initially.
- Specialist harmony choices remain available under a closed More arrangements disclosure.
- No `[object Object]`, stale branding, or image-background regression.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-studio-calm-d41a9a9-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-studio-calm-d41a9a9-20260710`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `d41a9a9`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: matched `d41a9a9`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: previously verified; not repeated in this focused adjustment smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: previously verified; not the focused target
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: stale URLs using `338a890` or older script cache keys
- Known caveats: an explicit octave change can shift later automatic notes to preserve the closest-playable contour; the UI discloses this

## Preview restart result

Succeeded without `sudo` by terminating only the user-owned port-8770 listener and allowing the installed LaunchDaemon to restart it. `/api/version` confirmed the target commit.

## Risk assessment

Low. UI-only simplification with full-suite and authenticated browser verification.

## Human decision needed

No.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-10-1552-12-melody-studio-calm-controls-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty/untracked paths.

## Recommended next lane

01 Repo Steward docs-only exact-path commit, then user smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the two coordination docs and ask the user to test the selected-note control at the exact protected URL.
