# Melody active-fretboard controls protected smoke

## Task summary

Refreshed the protected preview to implementation commit `a7f5ad9` and completed authenticated browser smoke for the Melody Studio active-only fretboard adjustment.

The preview now shows only the active event's validated fretboard position. Single-note navigation replaces the marker rather than accumulating the phrase. Harmony routes show only the active grip's strings. Octave colors, string labels, and note labels are independent controls.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-1345-12-melody-active-fretboard-controls-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

No runtime, deployment-policy, auth, corpus, source, private-data, or generated-asset files were changed in this phase.

## Tests and checks

Implementation verification inherited from the committed implementation handoff:

- Focused Melody/same-origin suite: `16 passed`.
- Full pytest: `934 passed in 39.00s`.
- Core JavaScript syntax checks: pass.
- Exact-path `git diff --check`: pass.

Protected preview checks:

- `/api/version` returned `a7f5ad9`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, and `features.melodyExercise=true`.
- Loopback `/` returned `302` to `/ui/steel-guitar-rag-mock.html`.
- Loopback home, Melody Studio, and versioned controller asset returned `200`.
- Anonymous loopback `/api/answer` returned the expected `401`; this API fallback is not browser smoke.
- Authenticated protected browser smoke passed.

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-active-marker-controls-a7f5ad9-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-active-marker-controls-a7f5ad9-20260711`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-active-marker-controls-a7f5ad9-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `a7f5ad9`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `a7f5ad9`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; redirects to canonical home
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex and the user
- Do not test these URLs: unversioned Studio URL; production-root behavior as a substitute for the exact Studio URL
- Known caveats: import/catalog feature flag remains intentionally off; unrelated parked work remains uncommitted

Authenticated browser assertions for `5 6 1 3 2 1 3`:

- Faithful melody opened at D4 with one active position and no string-number label by default.
- Next note replaced D4 with the E4 event and selected the matching second step.
- String labels enabled the active string number (`5`) without affecting note navigation.
- Note labels could be hidden while the active fretboard marker remained visible.
- Chord melody showed only the active three-string grip, with string labels `5`, `6`, and `8`, and one D4 top-voice label.
- Octave colors remained enabled independently.
- Horizontal overflow was zero and `[object Object]` was absent.

## Integration notes

- Runtime refresh used the existing installed user-owned preview service path: only the user-owned port-8770 listener was terminated, and the LaunchDaemon restarted it at the committed HEAD.
- No service configuration or privileged file was changed.
- API fallback remained unauthenticated by design and is not counted as browser smoke.

## Risk assessment

Low. The scoped UI adjustment is committed, test-green, and authenticated-preview verified. Rollback is the implementation commit `a7f5ad9`.

## Human decision needed

No. User smoke may continue at the exact URL above.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-1345-12-melody-active-fretboard-controls-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

Continue Lane 06 user smoke; any observed smoke defect returns to the scoped autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

Test note navigation and each of the three display toggles at the cache-busted protected URL.
