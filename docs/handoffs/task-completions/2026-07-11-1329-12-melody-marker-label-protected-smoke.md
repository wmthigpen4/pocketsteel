# Melody Studio marker-label protected-preview smoke

## Task summary

Refreshed protected preview to `6fe67a3` and completed authenticated browser smoke for the user-reported repeated fretboard marker-label defect.

The fix passes. Melody Studio now labels the seven test positions `D4`, `E4`, `G4`, `B4`, `A4`, `G4`, and `B4`. The old repeated `Your melody exercise in G — Single-note melody` label is absent. Chord melody preserves the same resolved top-voice pitch labels while selecting its correct multi-string fretboard positions.

No auth, DNS, Tunnel, Cloudflare Access, secret, backend/API, arranger, corpus, Chroma, source-inbox, private-data, brand, or deployment-policy behavior changed.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-1329-12-melody-marker-label-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- Implementation commit: `6fe67a3 Fix Melody fretboard marker labels`.
- Focused UI/same-origin/frontend slice: `7 passed, 35 deselected`.
- Full pytest: `934 passed in 38.02s`.
- Core JavaScript syntax: passed.
- Protected refresh: passed by terminating only the user-owned port-8770 listener and allowing the installed LaunchDaemon to restart it.
- Loopback `/api/version`: HTTP 200, `git_sha=6fe67a3`, expected branch/retrieval/auth/feature state.
- Loopback root: HTTP 302 to canonical home.
- Loopback home, Studio, and cache-busted controller asset: HTTP 200.
- Cloudflare Access authentication: succeeded.
- Authenticated protected browser smoke: passed.
- Browser warning/error logs: empty.
- Page-level horizontal overflow: zero.
- `[object Object]`: absent.

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-marker-labels-6fe67a3-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-marker-labels-6fe67a3-20260711`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-marker-labels-6fe67a3-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `6fe67a3`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: HTTP 200, `git_sha=6fe67a3`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes through canonical home redirect
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: production; unversioned Studio route
- Known caveats: none specific to this fix

API fallback was not used as a substitute for browser smoke.

## Smoke result

PASS.

Authenticated protected verification proved:

- Faithful melody position labels match the resolved notes exactly;
- the full route title no longer appears in the fretboard label layer;
- the current note is D4 and the selected position is `melody-g-section-1-single-note-event-1`;
- Chord melody retains D4/E4/G4/B4/A4/G4/B4 labels and selects `melody-g-section-1-chord-melody-event-1`;
- all existing route, score, fretboard, navigator, and tab rendering remains available;
- no browser warnings/errors, object-string output, or document overflow appeared.

## Integration notes

The protected preview is ready for the user to continue the existing Melody Studio smoke session at the exact cache-busted URL.

## Risk assessment

Low. The change is isolated to Melody Studio's position-label adapter.

## Human decision needed

No. User smoke may continue.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-1329-12-melody-marker-label-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

User smoke. Any observed defect returns to the scoped Autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

Continue user smoke at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-marker-labels-6fe67a3-20260711`.
