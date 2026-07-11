# Melody Score Edit Controls Protected Smoke

## Task summary

Restarted the protected preview at implementation commit `1830881` and verified the Melody Studio score-editing adjustment in the authenticated in-app browser. Both the visible deletion action and keyboard Delete remove only the selected event. The whole-score octave action updates all pitched events, reports the change, and the raised phrase still arranges into an E9 lesson. No deployment configuration, auth policy, DNS, secret, corpus, or private data changed.

## Files changed

- This protected-smoke handoff
- `docs/handoffs/task-completions/integration-status.md` (coordination refresh)

## Tests and checks

- Expected implementation HEAD: `1830881`
- Loopback `/api/version`: `1830881`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`
- Protected restart: pass; terminated only the user-owned listener on port 8770 and the installed LaunchDaemon restarted it
- Loopback `/`: 302 to `/ui/steel-guitar-rag-mock.html`
- Loopback home UI: 200
- Loopback Melody Studio: 200
- Loopback Melody Studio controller: 200
- Loopback anonymous `/api/answer`: 401 with Cloudflare Access identity required
- Authenticated protected browser: pass
- Browser console warnings/errors: none

### Feature smoke

1. Opened Build a score.
2. Added G4, A4, B4; the selection bar identified B4 as note 3 of 3.
3. `Delete selected note` removed B4 and selected A4 as note 2 of 2.
4. Keyboard Delete removed A4 and selected G4 as note 1 of 1.
5. Re-added A4 and B4, then used `All notes up 1 octave`.
6. The selected event changed from B4 to B5 and the panel reported `Moved every note up one octave.`
7. `Arrange for E9` rendered `Your melody exercise in G` with no visible error.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-score-edit-controls-1830881-20260711`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-score-edit-controls-1830881-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; the existing signed-in browser loaded the Studio and completed an answer request
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `1830881`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `1830881`
- If version endpoint missing, how version is inferred: not missing locally; direct protected JSON navigation was blocked by the browser client, so loopback version plus protected committed-asset behavior establishes runtime identity
- Whether app root `/` works: yes; protected browser redirected to the canonical home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: unversioned or prior `melody-lead-sheet-repair-2469975` Studio URLs
- Known caveats: unauthenticated command-line requests are redirected to Cloudflare Access; API fallback is not browser smoke

## Integration notes

- User smoke may continue on `1830881`.
- The in-app browser has been left open on the verified Studio URL.
- All unrelated dirty files remain parked and unstaged.

## Risk assessment

Low. The runtime matches the committed UI-only adjustment and the protected browser exercised the exact requested controls.

## Human decision needed

No.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-1757-12-melody-score-edit-controls-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All unrelated dirty corpus, source-inbox, private-data, deployment, public/brand, Neon Sign, RAG pipeline, README, and pre-existing documentation files.

## Recommended next lane

User smoke. Any reported defect remains an end-to-end user-smoke Autopilot repair.

## Commit readiness

Safe to commit

## Suggested next step

Use the exact cache-busted protected URL and verify deletion plus whole-score octave movement with the original transcription draft.
