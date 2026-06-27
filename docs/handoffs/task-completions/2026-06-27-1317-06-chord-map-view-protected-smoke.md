# 2026-06-27 13:17 - Lane 06 - Chord Map View Protected Smoke

## Task Summary

Protected-preview smoke was run after commit `c423e4b feat: map chord finder candidates on fretboard`.

## Smoke Target

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-view-c423e4b
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-view-c423e4b
- Exact URL the user should use: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-view-c423e4b
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded via existing authenticated in-app browser session
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: c423e4b
- Version endpoint: https://app.steelguitarrag.com/api/version
- Version endpoint result: not available through browser direct navigation; in-app browser reported net::ERR_BLOCKED_BY_CLIENT
- If version endpoint missing, how version is inferred: cache-busted static Explorer URL served `e9-fretboard-explorer.js?v=chord-map-view-20260627`; implementation commit is static UI only
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes, current app-root behavior redirects to app shell
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: unversioned Explorer URL for this slice
- Known caveats: API version endpoint could not be read in browser due `net::ERR_BLOCKED_BY_CLIENT`, so this is protected static/browser behavior proof rather than runtime SHA proof
```

## Protected Smoke Result

PASS with version-endpoint caveat.

Verified:
- Protected Explorer page loaded after Cloudflare Access authentication.
- Page served `e9-fretboard-explorer.js?v=chord-map-view-20260627`.
- Chord / Voicing Finder was selectable.
- `F` + `Major` + `All practical` controls and `All practical` grip vocabulary rendered 24 candidate cards and 13 SVG marker clusters.
- Filter chips rendered: All, Open, Pedals, Levers, Low frets, Mid frets, High frets, Complete, Core.
- Open filter reduced view to 8 open cards and 8 SVG markers.
- Card selection selected the matching SVG marker and updated the detail panel.
- No `[object Object]` appeared.
- Browser console had no relevant warnings/errors.
- Root `/` redirected to `/ui/steel-guitar-rag-mock.html`.
- Direct app shell URL loaded.

## Files Changed

None in this smoke handoff aside from this report.

## Tests And Checks

Browser smoke only for this handoff. Implementation checks are recorded in `docs/handoffs/task-completions/2026-06-27-1259-06-chord-voicing-finder-map-view.md`.

## Risks

Medium-low:
- Same-fret adjacent candidates can still visually overlap. Cards and filters are now the primary disambiguation layer, and marker clusters remain visible on the SVG.
- Version endpoint was blocked by the browser surface, so strict runtime SHA proof was not available.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-27-1317-06-chord-map-view-protected-smoke.md`

## Files That Must Not Be Staged

- Existing unrelated dirty/untracked files, especially corpus, Chroma/vector, source-inbox, brand/public assets, raw design assets, and unrelated RAG scripts.

## Recommended Next Lane

Lane 15 focused QA or user smoke at:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-view-c423e4b
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke the Chord / Voicing Finder map view with `F` + `Major` + `All practical`.
