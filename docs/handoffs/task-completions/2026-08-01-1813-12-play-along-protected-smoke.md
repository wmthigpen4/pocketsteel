# Play Along protected activation and smoke

## Task summary

Activated the approved Play Along / Amazing Tablature release in the
application serving `app.steelguitarrag.com` and completed authenticated
Cloudflare Access browser smoke.

The first protected smoke of runtime commit `6933998d` exposed a
production-only copedent bootstrap defect: Play Along had loaded the account
session but had not synchronized the account-backed copedent before arranging
the lesson. A browser-local custom profile snapshot was therefore sent to the
production API and correctly rejected. The fix initializes account copedents
before arrangement, sends only the authoritative account profile reference,
and falls back to standard Emmons E9 when account synchronization is
unavailable.

The fix is committed as `7b9331094d67d316249ace6bb484805556f496b2` and
activated from the standalone detached release at
`/Users/cory/.steel-rag/releases/7b933109-play-along-copedent-fix`.

## Protected-preview smoke

- Exact cache-busted URL:
  `https://app.steelguitarrag.com/play/amazing-grace-guided?v=play-along-7b933109-20260801`
- Auth result: Cloudflare Access sign-in passed in the in-app browser.
- Expected runtime commit: `7b9331094d67d316249ace6bb484805556f496b2`.
- `/api/version`: `200`, `git_sha=7b93310`.
- Root `/`: `302` to the canonical application home.
- `/ui/steel-guitar-rag-mock.html`: `200`.
- `/songs`: `200`.
- `/play/amazing-grace-guided`: `200`.
- LaunchDaemon: running from
  `/Users/cory/.steel-rag/releases/7b933109-play-along-copedent-fix`.
- API fallback: loopback health, version, home, Songs, and Play routes passed.
  This fallback evidence is recorded separately and is not being used as a
  substitute for the authenticated browser pass above.

Authenticated browser verification:

- The production page loaded `Amazing Grace` without the prior copedent error.
- `Follow the Melody` was the initial/default lesson.
- All four approved lessons were available:
  `Follow the Melody`, `Chord Foundation · Move the Bar`,
  `Chord Foundation · Stay Near Fret 3`, and
  `Full Chord Melody · Advanced`.
- The Kevin MacLeod lesson audio reached media ready state 4, had no media
  error, was not muted, and advanced from `audio.currentTime` at the selected
  0.5x speed.
- Pause and restart passed; restart returned the audio clock to `0`.
- Live lesson switching succeeded among melody and chord-foundation routes.
- The current/upcoming chord region, 24-fret E9 display, per-string controls,
  melody label, synchronized lyric, lesson controls, and rights attribution
  rendered on the protected page.
- Browser console warning/error log was empty after initialization, playback,
  route switching, pause, and restart.

## Files changed

Runtime fix commit `7b933109`:

- `ui/play-song.js`
- `ui/play-song.html`
- `tests/test_play_songs_ui.py`

This completion record:

- `docs/handoffs/task-completions/2026-08-01-1813-12-play-along-protected-smoke.md`

No auth policy, Cloudflare Access rule, Tunnel, DNS, secret, corpus, vector
store, audio master, rights record, private source, or saved user data changed.

## Tests and checks

- Focused Play Along, copedent account, API, and song-practice tests:
  `41 passed in 3.52s`.
- Full repository regression suite: `1548 passed in 83.82s`.
- `node --check ui/play-song.js`: passed.
- Detached release preflight: passed for exact commit
  `7b9331094d67d316249ace6bb484805556f496b2`.
- Alternate-port release startup: live, ready, and exact version passed before
  activation.
- LaunchDaemon activation health and exact-version verification: passed.
- Authenticated protected browser smoke: passed.
- `git diff --check`: passed before this handoff was written.

## Risks

Low. The production-only account bootstrap gap is covered by focused tests,
the complete regression suite, exact-release preflight, and authenticated
browser playback. Account synchronization may add a short initial loading
delay; its failure path safely uses standard Emmons E9 rather than sending an
untrusted browser snapshot.

## Human decision needed

No engineering or deployment decision is required. The feature is ready for
normal user evaluation of the teaching experience and musical guidance.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-01-1813-12-play-along-protected-smoke.md`

The runtime fix files are already committed in `7b933109`.

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- unrelated historical handoffs
- release directories, logs, environment files, credentials, secrets, audio,
  rights metadata dumps, corpus data, vector stores, private training data,
  and generated reports

## Recommended next lane

Lane 06 / user smoke may continue refining the musical teaching experience
from the now-active protected Play Along page. No additional Lane 12 work is
required for this release.

## Commit readiness

Ready to commit the exact handoff path above. Do not stage any unrelated dirty
or untracked files.
