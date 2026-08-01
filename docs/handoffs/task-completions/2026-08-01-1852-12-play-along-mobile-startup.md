# Play Along mobile startup and landscape activation

## Task summary

Fixed the protected Amazing Grace Play Along page failing to become usable on
mobile, made phone landscape the primary compact layout, and activated the
exact tested release serving `app.steelguitarrag.com`.

The failure had two production-specific causes:

1. Play Along could wait indefinitely for account-copedent synchronization
   before showing any interface.
2. A signed-in custom copedent silently triggered a bespoke whole-song melody
   arrangement on every curated-song open. The observed protected request took
   about 67 seconds, which made the page appear broken.

Bundled beginner lessons now use their authored standard ten-string Emmons E9
profile. Account-copedent initialization remains bounded and retained for the
device-project path, where a custom setup can be an explicit project choice.

The player also shows a disabled but informative loading shell immediately,
loads the recording before route generation finishes, requests only the compact
Play Along lesson response instead of the complete 4.2 MB arranger response,
and keeps the fretboard plus transport inside the tested landscape viewport.

The implementation commits are:

- `08d1944f3eae92c0e88e65f5c44c277ac7e4bd8a` — bounded startup, visible
  loading shell, compact API response, and landscape layout.
- `ea9687a3d9d30aec3f622947b143f4a7b9ea98ab` — pin curated bundled lessons to
  their authored standard E9 route instead of silently arranging against the
  account custom copedent.

The active protected runtime is the exact detached release at
`/Users/cory/.steel-rag/releases/ea9687a3-play-along-mobile`.

## Protected mobile smoke

- Exact cache-busted URL:
  `https://app.steelguitarrag.com/play/amazing-grace-guided?v=play-along-ea9687a3-mobile-20260801`
- Auth result: the existing Cloudflare Access session remained valid; no new
  application sign-in was required.
- `/api/version`: `200`, `git_sha=ea9687a`.
- Root `/`: `302` to the canonical application home.
- `/ui/steel-guitar-rag-mock.html`: `200`.
- `/songs`: `200`.
- `/play/amazing-grace-guided`: `200`.
- Exact-release preflight, alternate-port live/ready/version checks, activation
  health, and supervised verification passed.

Authenticated in-app browser verification at a phone-landscape viewport:

- The branded Play Along shell appeared in about 0.3 seconds instead of
  remaining blank.
- The page showed a clear `Preparing the reviewed melody route…` state while
  controls were safely disabled.
- Amazing Grace became ready with all four lesson modes and no error panel.
- The responsive document height matched the tested landscape viewport; the
  fretboard and full transport were visible without vertical scrolling.
- The Kevin MacLeod lesson audio reached media ready state 4, had no media
  error, was unmuted, and advanced from the audio clock after Play.
- Pause succeeded after playback began.
- Browser console warning/error log was empty.

Secondary portrait verification kept the document within the portrait viewport
width, with intentional horizontal scrolling confined to the 24-fret fretboard
shell.

## Files changed

Runtime commits `08d1944f` and `ea9687a3`:

- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `tests/test_play_songs_ui.py`
- `ui/play-song.html`
- `ui/play-song.js`
- `ui/play-songs.css`

This completion record:

- `docs/handoffs/task-completions/2026-08-01-1852-12-play-along-mobile-startup.md`

No audio master, lyric/beat timeline, chord data, rights record, authentication
policy, Cloudflare Access rule, Tunnel, DNS, secret, corpus, vector store,
private source, or saved user data changed.

## Tests and checks

- Focused Play Along, API, song-practice, song-project, and copedent tests:
  `62 passed in 6.08s`.
- Full repository regression suite after the final curated-E9 correction:
  `1549 passed in 88.45s`.
- The preceding full suite on the main mobile-startup implementation also
  passed: `1549 passed in 89.75s`.
- `node --check ui/play-song.js`: passed.
- `git diff --check`: passed before both implementation commits.
- Local phone-landscape startup, route readiness, exact-fit layout, audio play,
  pause, and portrait compatibility: passed.
- Detached exact-release preflight and alternate-port smoke: passed.
- Protected authenticated phone-landscape startup and playback: passed.

## Risks

Low. Curated bundled lessons intentionally use their reviewed standard E9
route, which is the documented beginner default and avoids unpredictable custom
arrangement latency. A custom copedent is not silently substituted into the
curated lesson. The future device-project path retains bounded account-copedent
support and should present custom setup as an explicit choice.

The standard melody route still takes several seconds to prepare on a cold
load. The player now makes that work visible, loads audio early, and cannot be
held blank by account synchronization. A later optimization may materialize
the reviewed route as a versioned curated artifact, but that is not required to
resolve this activation failure.

## Human decision needed

No engineering, authentication, or deployment decision is required. The
protected mobile Play Along page is ready for normal musical evaluation.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-01-1852-12-play-along-mobile-startup.md`

The runtime files are already committed in `08d1944f` and `ea9687a3`.

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- unrelated historical handoffs
- release directories, logs, environment files, credentials, secrets, audio,
  rights metadata dumps, corpus data, vector stores, private training data, and
  generated reports

## Recommended next lane

Lane 06 / user smoke can continue evaluating the musical teaching experience
from the active mobile landscape player. A later performance slice may package
the reviewed standard-E9 route as a static curated lesson artifact.

## Commit readiness

Ready to commit the exact handoff path above. Do not stage unrelated dirty or
untracked files.
