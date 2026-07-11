# Melody string/action labels protected smoke

## Task summary

Refreshed the protected preview to implementation commit `c850411` and completed authenticated browser smoke for pedal/lever-aware Melody Studio string labels.

The optional String labels control now shows the active string plus its required compact action, such as `6B`, rather than dropping the pedal/lever information.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-1357-12-melody-string-action-labels-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

No runtime code, auth policy, deployment configuration, corpus, sources, private data, or generated assets were changed in this phase.

## Tests and checks

- Focused Melody/same-origin suite: `16 passed`.
- Full pytest: `934 passed in 38.25s`.
- Core JavaScript syntax checks: pass.
- Exact-path `git diff --check`: pass.
- Loopback `/api/version`: `c850411`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, and `features.melodyExercise=true`.
- Loopback `/`: `302` to `/ui/steel-guitar-rag-mock.html`.
- Loopback home, versioned Studio, and versioned controller asset: `200`.
- Anonymous loopback `/api/answer`: expected `401`; API fallback is not browser smoke.
- Authenticated protected browser smoke: pass.

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-string-action-labels-c850411-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-string-action-labels-c850411-20260711`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-string-action-labels-c850411-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `c850411`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `c850411`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; redirects to canonical home
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex and the user
- Do not test these URLs: unversioned Studio URL; API fallback as a substitute for browser behavior
- Known caveats: import/catalog feature flag remains intentionally off; unrelated parked work remains uncommitted

Authenticated browser proof used the literal validated event `S6:3B`:

- String labels visibly rendered `6B` inside the active marker.
- Current note displayed `String 6 · Fret 3 · B`.
- The active resolved note label was `C4` and exactly one active dot remained.
- Octave colors remained independently enabled.
- Horizontal overflow was zero and `[object Object]` was absent.

## Integration notes

- Runtime refresh terminated only the user-owned port-8770 listener; the installed LaunchDaemon restarted at committed HEAD.
- No privileged file or service configuration changed.
- API fallback remained unauthenticated by design and is not counted as browser smoke.

## Risk assessment

Low. The fix is scoped, full-suite green, and visibly verified through Cloudflare Access.

## Human decision needed

No. The user stated the rest of this feature passes user smoke; this final defect is ready for confirmation.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-1357-12-melody-string-action-labels-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

Lane 06 final user confirmation, then close the Melody Studio user-smoke slice.

## Commit readiness

Safe to commit

## Suggested next step

Confirm `6B` at the exact protected URL; if correct, Melody Studio passes this user-smoke slice.
