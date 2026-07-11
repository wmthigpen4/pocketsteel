# Melody Studio Scientific-Octave Map Protected Smoke

## Task summary

Verified the committed Melody Studio scientific-octave map adjustment on the authenticated protected preview.

The initial protected pass exposed a stale asset-cache pairing: current HTML loaded an earlier Melody Studio script. Commit `f6868d5` assigned a fresh cache key, the supervised preview was refreshed again, and the full protected interaction then passed.

No auth, DNS, Tunnel, corpus, source, private-data, scraper, vector, or deployment-policy configuration changed. The only runtime mutation was terminating the user-owned port-8770 listener so the installed LaunchDaemon restarted the current commit.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-0742-12-melody-octave-map-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- Implementation commits:
  - `35f36bc Improve Melody Studio octave map controls`
  - `f6868d5 Refresh Melody Studio octave map assets`
- Full pytest after the implementation: 922 passed.
- Final focused cache-bust suite: 54 passed.
- Core JavaScript syntax checks: passed.
- Loopback `/api/version`: `f6868d5`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`.
- Cloudflare Access authenticated browser smoke: passed at the exact Melody Studio target.
- Protected root and canonical home-route browser checks: loaded successfully.
- Anonymous protected root request: HTTP 302 to Cloudflare Access, as expected.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-octave-map-f6868d5-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-octave-map-f6868d5-20260711`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-octave-map-f6868d5-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded for the direct Melody Studio target
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `f6868d5`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: HTTP 200, `git_sha=f6868d5`, expected branch, retrieval/auth modes, and Melody feature flag
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; authenticated browser navigation redirected to the home application
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes; canonical route loaded in the browser
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: earlier `melody-octave-guide-*`, `melody-octave-map-35f36bc-*`, or unversioned Studio URLs
- Known caveats: the separate protected home tab showed the existing signed-out/backstage feature state; the direct Studio target was authenticated and fully exercised. Loopback version evidence is API verification, not browser smoke. The per-string background lanes represent the unpedaled fret path, while pedal/lever note markers use their exact mechanically adjusted pitch.

## Smoke result

PASS. On the direct protected target:

- entered `5 6 1`, selected only event 3, and raised it from G4 to G5;
- the compact control updated to `Octave 5 · +1 octave`, with exact G4/G5 accessible raise/lower labels and a working automatic action;
- the lesson rendered 30 string-aware octave zones across the fretboard;
- the default-on toggle changed between **Hide octave map** and **Show octave map**, hid/restored the SVG overlay, and hid/restored the scientific-octave legend;
- the selected G5 marker used the octave-5 amber color, matching the legend and event step;
- Recommended harmony kept the selected lesson step labeled by the G5 top melody voice while its displayed string-3 and string-5 markers were correctly tagged octaves 5 and 4;
- Current note, event step, fretboard marker, harmony route, and tab remained synchronized;
- no browser console errors appeared;
- no `[object Object]` text rendered.

## Integration notes

The shared fretboard option remains opt-in and off by default. Melody Studio is the only current consumer. Scientific-octave event labels depend on color plus visible pitch text, and marker colors are derived from exact string/fret/control pitch calculations.

## Risk assessment

Low. Full regression, focused component coverage, local browser smoke, and authenticated protected browser smoke passed. Rollback is commits `f6868d5` then `35f36bc`.

## Human decision needed

No. User smoke may continue at the exact URL above.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-0742-12-melody-octave-map-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All unrelated dirty and untracked corpus, source-inbox, private-data, brand/design, public asset, deployment, generated-report, and parked documentation paths.

## Recommended next lane

User smoke. Any observed defect returns to the approved end-to-end autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

Use the exact cache-busted protected URL and verify that the map makes scientific register changes clearer without adding too much visual weight.
