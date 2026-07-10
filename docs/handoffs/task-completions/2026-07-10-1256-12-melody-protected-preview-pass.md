# Melody Exercise v0 Protected-Preview Pass

## Task summary

Completed the authorized protected-preview update and authenticated browser smoke for Melody Exercise v0. The installed LaunchDaemon wrapper now matches the committed wrapper, the protected runtime reports `c9e3650`, Cloudflare Access authentication succeeded, and the exact cache-busted direct UI passed feature and regression checks.

No auth policy, DNS, Tunnel, secret, private environment, corpus, Chroma, source-inbox, private transcript, or asset content was changed.

## Files changed

- `docs/handoffs/task-completions/integration-status.md` — refreshed from the sudo blocker to the protected-preview pass and user-smoke state.
- `docs/handoffs/task-completions/2026-07-10-1256-12-melody-protected-preview-pass.md` — this report.
- Deleted: none.
- Generated artifacts: none.

## Tests and checks

- Confirmed installed and repo-managed private-preview wrappers match.
- Confirmed loopback `/api/version` reports `c9e3650`, `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, and `features.melodyExercise=true`.
- Confirmed loopback root returns 302 to `/ui/steel-guitar-rag-mock.html`.
- Confirmed loopback canonical UI returns 200.
- Confirmed anonymous loopback `POST /api/answer` returns 401 with Cloudflare Access identity required.
- Authenticated protected browser smoke passed at the exact URL below.
- Earlier implementation verification remains green: full pytest `911 passed`, core JavaScript checks passed, shell syntax passed, authenticated local 295-question eval completed, and local browser smoke passed.
- `git diff --check` must pass before this docs-only closeout is committed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=melody-v0-c9e3650-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=melody-v0-c9e3650-20260710`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `c9e3650` for the runtime smoke, containing implementation commit `f37201a`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `c9e3650`, correct branch/retrieval/auth/feature values
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: redirects to `/ui/steel-guitar-rag-mock.html`; separate root tab showed signed-out/backstage state and dropped the cache-bust
- Whether app root `/` is expected to work: redirect is expected, but it is not the canonical smoke target
- Whether `/ui/steel-guitar-rag-mock.html` works: yes, authenticated at the exact cache-busted URL
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex completed automated smoke; the user should now run the checklist below
- Do not test these URLs: do not use bare root for cache-sensitive user smoke; do not use local `127.0.0.1` as proof of protected behavior
- Known caveats: browser-client navigation to protected `/api/version` returned `ERR_BLOCKED_BY_CLIENT`; loopback `/api/version` supplied exact runtime proof. API fallback is not browser smoke.

## Protected browser results

- Artist-solo lesson rendered the artist, song, recording/version, source link, `Transcription`, `Approximate · Medium confidence`, eight numbered events, tab, and fretboard.
- Selecting Step 2 synchronized `melody-step-2` and `melody-g-section-1-event-2` across the stepper, tab state, and fretboard state.
- Tab retained `white-space: pre` and horizontal overflow behavior.
- A ten-event commercial arrangement rendered Section 1 of 2 with eight events and a Section 2 continuation, with no copyright/refusal language.
- A recording/YouTube solo request without identified notes asked for a recording/video link, upload, pasted passage, or exact version/section; tab and fretboard stayed hidden and the empty source section stayed hidden.
- An original exercise ignored supplied stale artist/source metadata, showed user-entered/original identity, zero source links, and a hidden source section.
- Existing G I-IV-V-I progression behavior remained source-free with fretboard output and no tab.
- No `[object Object]` and no relevant console warnings/errors appeared.

## User-smoke checklist

1. Open **Build a melody or arrangement lesson** and create an Artist solo in G with notes `G A B D E D B G`; confirm the lesson shows steps, tab, fretboard, and an accuracy label.
2. Click Step 2 and confirm the detail changes to A on string 4, fret 5.
3. Submit `Teach me the full artist solo from a commercial recording on YouTube.` in the main question box; confirm it asks for the recording/version and does not refuse for copyright.
4. Create an Original exercise with `1 2 3 5`; confirm there is no Source notes section.
5. On a phone/narrow window, confirm the tab spacing stays aligned and scrolls horizontally if necessary.

## Integration notes

- Protected-preview automated smoke is complete. User smoke may begin.
- Any user-reported defect is approved for the existing end-to-end autopilot repair loop without renewed feature approval.
- Keep the user-smoke freeze: fix observed issues, but do not start unrelated broad feature development until smoke closes.

## Risk assessment

- Risk: low-to-medium during user smoke because this is a new answer/UI path, but it is feature-gated, mechanically validated, fully tested locally, and now protected-browser verified.
- Rollback: set `STEEL_RAG_ENABLE_MELODY_EXERCISE=false` in the protected-preview runtime environment and restart, or revert the implementation commit.

## Human decision needed

Yes: complete the five-item user-smoke checklist and report pass/fail observations.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-10-1256-12-melody-protected-preview-pass.md`

## Files that must not be staged

All other dirty and untracked paths.

## Recommended next lane

User smoke; Lane 01/05/06/15 autopilot repair only if a defect is reported.

## Commit readiness

Safe to commit

## Suggested next step

The user opens the exact cache-busted URL and runs the five-item checklist above.
