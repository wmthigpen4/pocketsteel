# Play-Along Direction Cues Staging Smoke

## Task Summary

- Deployed the exact movement-cue feature commit to the isolated staging
  service.
- Verified explicit up, down, and same-fret states on the user's imported song.
- Production at `app.steelguitarrag.com` was not changed.

## Release And Smoke Target

- Expected feature commit: `919a4eef372c5f898c03c70099b6808aa170fe0d`
- Staging `/api/version`: `919a4ee`
- Detached release: `/Users/cory/.steel-rag/releases/919a4eef-play-along-staging`
- Exact cache-busted browser URL:
  `https://test.steelguitarrag.com/play/local-585b976d-b82b-4321-b035-f08a73216544?v=direction-cues-919a4ee-top`

## Tests And Checks Run

- Full pytest before deployment: `1559 passed`.
- Authenticated browser smoke loaded the imported song and restored its local
  project data.
- Same-fret smoke: `● SAME FRET` with `Stay at fret 5 · repick`.
- Up-fret smoke: `↑ UP 2 FRETS`, accessible as `Move up 2 frets, from fret 3
  to fret 5`.
- Down-fret smoke: `↓ DOWN 1 FRET`.
- The original saved position was restored to `3:25 / 3:39` after smoke.
- Unauthenticated staging root redirects to Cloudflare Access.
- Authenticated in-app browser session loaded the protected page.
- Loopback root redirects to `/ui/steel-guitar-rag-mock.html`.
- Loopback home returns 200.
- Loopback `/api/answer` without auth returns 401. This API fallback result is
  not browser smoke.

## Risks

- Low. Direction is based only on the numerical difference between the current
  and next recommended frets.
- The badge intentionally disappears in Less Help mode.

## Human Decision Needed

- None. Ready for user smoke on staging.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-08-02-2130-12-play-along-direction-cues-staging-smoke.md`

## Files That Must Not Be Staged

- `.venv`
- LaunchAgent, detached release, environment, log, and credential files.

## Recommended Next Lane

- User smoke on staging. Keep production unchanged until the larger Play-Along
  feature is accepted.

## Commit Readiness

- The smoke handoff is safe for an exact-path documentation commit.
