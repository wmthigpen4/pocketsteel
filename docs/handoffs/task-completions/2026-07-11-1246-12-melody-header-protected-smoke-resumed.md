# Melody Studio lesson-header protected smoke resumed

## Task summary

Resumed the protected-preview browser smoke that was previously blocked by concurrent incomplete arranger work. The overlapping work is now committed in `b0944c7`, the protected runtime is stable on that implementation, and the lesson-header cleanup from `deac899` remains intact in the integrated build.

Authenticated browser smoke passed. Melody Studio omits the generic practice kicker, the exactness/confidence/section metadata line, and the hidden More arrangements disclosure. All six available routes appear together in one horizontally scrollable row. Building `5 6 1 3 2 1 3`, switching to Chord melody, and synchronizing the current-note readout and fretboard selection all worked without console errors or `[object Object]` output.

No runtime restart was required because the installed protected service was already serving the stable committed implementation `b0944c7`. No application, auth, DNS, Tunnel, Access, secret, corpus, Chroma, scraping, source-inbox, private-data, brand, or deployment-policy file changed.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-1246-12-melody-header-protected-smoke-resumed.md`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- Current implementation baseline: `b0944c7 Build Melody Studio multi-input score workflow`.
- Current repository docs HEAD before this report: `cc8cc99 Record Melody multi-input protected smoke`.
- Full pytest for the integrated implementation: `933 passed`, recorded in the multi-input implementation/protected-smoke handoffs.
- Focused final melody/API/UI/import tests: `39 passed, 300 deselected`, recorded in the same handoffs.
- Loopback `/api/version`: HTTP 200; `git_sha=b0944c7`, branch `feature/answer-api`, retrieval `hybrid_private_first`, auth `cloudflare_access`, and `features.melodyExercise=true`.
- Loopback root: HTTP 302 to `/ui/steel-guitar-rag-mock.html`.
- Loopback canonical home: HTTP 200.
- Loopback Melody Studio: HTTP 200.
- Anonymous protected root: HTTP 302 to Cloudflare Access, as expected.
- Cloudflare Access authentication on the direct protected Melody Studio target: succeeded.
- Protected browser smoke: passed.
- Browser console errors: none.
- Page-level horizontal overflow: none.
- `[object Object]`: absent.

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-header-resume-b0944c7-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-header-resume-b0944c7-20260711`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-header-resume-b0944c7-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded on the direct protected target
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: runtime implementation `b0944c7`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: HTTP 200, `git_sha=b0944c7` with the expected branch, retrieval, auth, and Melody feature state
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes on loopback; an anonymous protected request redirects to Cloudflare Access
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes on loopback; a separately opened protected browser tab requested a fresh Access login rather than inheriting the direct-target session
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: production; unversioned Studio route; external upload destinations
- Known caveats: separate newly opened protected tabs may request a fresh Cloudflare Access login; this did not affect authenticated smoke of the exact direct Studio target. Protected catalog/upload import remains default off as previously documented.

API fallback was not used as a substitute for browser smoke. Loopback requests supplied only service freshness and route evidence.

## Smoke result

PASS.

The authenticated protected browser verified:

- a seven-degree phrase builds successfully;
- the result title appears without the removed Practice the lesson kicker;
- the exactness/confidence/single-section metadata line is absent;
- no More arrangements disclosure exists;
- Faithful melody, Vocal steel, Recommended harmony, Diatonic thirds, Diatonic sixths, and Chord melody appear together in one row;
- the route row uses horizontal overflow rather than wrapping or hiding routes;
- switching to Chord melody visibly updates the selected route, fretboard position, and current-note readout;
- no console errors, object-string rendering, or page overflow appeared.

## Integration notes

The earlier `NameError: re` blocker is closed by the committed multi-input implementation. The lesson-header cleanup is verified on the current protected runtime, so user smoke may resume.

## Risk assessment

Low. This task changed documentation only after read-only protected and loopback checks. The remaining caveat is normal Cloudflare Access session behavior in separately opened tabs.

## Human decision needed

No.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-1246-12-melody-header-protected-smoke-resumed.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

User smoke on the exact protected URL. Any observed defect returns to the scoped Autopilot bug-fix loop.

## Commit readiness

Safe to commit

## Suggested next step

Continue Melody Studio user smoke at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-header-resume-b0944c7-20260711`, focusing on route selection and the cleaned result header.
