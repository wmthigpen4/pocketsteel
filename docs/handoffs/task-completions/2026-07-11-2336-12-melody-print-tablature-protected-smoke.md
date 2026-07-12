# Melody Studio print-tablature protected smoke

## Task summary

Refreshed the protected runtime at implementation commit `5007011` and verified through authenticated Cloudflare Access browser smoke that Melody Studio now offers **Print tablature** and no longer offers Print score. The installed LaunchDaemon respawned the service after only the user-owned port-8770 listener was terminated.

## Files changed

- this handoff
- `docs/handoffs/task-completions/integration-status.md` (separate coordination refresh)

No runtime implementation, auth, DNS, Tunnel, secrets, corpus, private-data, source, or deployment-policy files changed during this lane.

## Tests and checks

- Implementation commit: `5007011 Print Melody Studio tablature instead of score`
- Loopback `/api/version`: `5007011`, branch `feature/answer-api`, `features.melodyExercise=true`
- Authenticated Cloudflare Access Melody Studio load: pass
- Protected `1 2 3 5` arrangement: pass
- Print tablature action: visible and unique
- Print score action: absent
- Recommended harmony print label: `Arrangement: Recommended harmony`
- Printable tab used the current harmonized route: pass
- Print stylesheet: landscape; tab visible; staff/fretboard/controls/editor hidden
- `[object Object]`: absent
- Browser warnings/errors: none
- Protected root redirect to canonical home UI: pass
- Anonymous protected root: HTTP 302 to Cloudflare Access, expected

The native macOS print dialog was not operated by automation and remains the user-smoke boundary.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-print-tab-5007011-20260711`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-print-tab-5007011-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded for the direct Studio route
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `5007011`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `5007011`, expected branch, auth provider, retrieval mode, and Melody Exercise feature
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; it redirected to the canonical home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: unversioned or earlier protected Melody Studio cache keys
- Known caveats: the native print preview/output was not automated; the root UI loaded in its Backstage-pass state while the direct Studio route retained the authenticated Melody feature session

## Smoke result

PASS for protected print readiness.

- The current selected route was Recommended harmony.
- The hidden print heading and visible tab both reflected Recommended harmony.
- Print CSS parsed successfully and explicitly retained `#studio-tab`, suppressed `#studio-result-score`, and requested landscape orientation.
- API fallback status: loopback `/api/version` passed; it is not browser smoke.

## Integration notes

The user should perform one native print-preview check because browser automation intentionally does not accept or dismiss operating-system print dialogs.

## Risk assessment

Low. The screen action and parsed print rules are verified; the only remaining risk is browser/printer-specific pagination.

## Human decision needed

No product decision. One user smoke action is required: open native print preview and confirm the single landscape tab sheet looks right.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-2336-12-melody-print-tablature-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All unrelated dirty and untracked corpus, source-inbox, private-data, generated-report, deployment, public/brand, `ui/brand/`, `Neon Sign/`, and parked documentation paths.

## Recommended next lane

User smoke. Any reported print defect returns to the existing end-to-end Autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

At the exact cache-busted URL, arrange a phrase, choose a harmony route, click Print tablature, and confirm the native preview contains the title, arrangement, and tab—but no staff or fretboard.
