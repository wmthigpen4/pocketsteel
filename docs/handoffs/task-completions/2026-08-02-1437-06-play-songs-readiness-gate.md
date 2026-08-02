# Play Songs readiness gate

## Task summary

Fixed the catalog contract that advertised **When the Saints Go Marching In**
as playable even though the player could not build a lesson for it. The Saints
record currently has no authored melody lesson or beginner E9 route, and its
launch status still requires exact-master rights review. The catalog now exposes
an explicit `playAlongReady` decision and the player refuses incomplete lessons
before entering its arrangement path.

The resulting catalog state is truthful:

- Amazing Grace: `Play Along`
- When the Saints Go Marching In: `Track & lesson in review`
- Hard Times Come Again No More: `Track in review`

This change prevents another incomplete catalog record from becoming a broken
Play Along link. It does not claim that Saints or Hard Times is complete.

## Files changed

- `steel_guitar_rag/song_practice.py`
- `ui/songs.js`
- `ui/songs.html`
- `ui/play-song.js`
- `ui/play-song.html`
- `tests/test_song_practice.py`
- `tests/test_play_songs_ui.py`
- `docs/handoffs/task-completions/2026-08-02-1437-06-play-songs-readiness-gate.md`

No recording, timeline, rights document, authentication rule, Cloudflare
configuration, corpus, saved user data, or private source was changed.

## Tests and checks

- Focused song-practice, Play Songs UI, and API suite: `366 passed in 20.07s`.
- Full repository regression suite: `1549 passed in 78.78s`.
- `node --check ui/songs.js`: passed.
- `node --check ui/play-song.js`: passed.
- Direct registry check confirmed only Amazing Grace returns a playable project.
- `git diff --check` on the exact implementation paths: passed.

## Risks

Low implementation risk. The user-visible limitation is now explicit: Amazing
Grace remains the only complete lesson. Saints needs a cleared, acceptable
recording plus an authored beginner E9 route. Hard Times needs the recording,
beat/chord/lyric timeline, and route approved together.

## Human decision needed

No decision is needed for the readiness fix. Completing another song is a
separate curated-content slice; do not promote the existing synthetic Saints
preview merely to increase the song count.

Production activation has not been attempted in this slice. That avoids another
unexpected macOS administrator sign-in. If activation is requested, perform one
final exact-release activation after the committed build is prepared, with no
repeated sign-in attempts.

## Safe-to-stage exact file list

- `steel_guitar_rag/song_practice.py`
- `ui/songs.js`
- `ui/songs.html`
- `ui/play-song.js`
- `ui/play-song.html`
- `tests/test_song_practice.py`
- `tests/test_play_songs_ui.py`
- `docs/handoffs/task-completions/2026-08-02-1437-06-play-songs-readiness-gate.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- unrelated historical handoffs and generated files
- releases, logs, credentials, secrets, corpus data, vector stores, or private
  training data

## Recommended next lane

Lane 18 should select the next genuinely shippable curated song master, then
Lane 20/06 should author and verify its musical lesson before Lane 12 activation.

## Commit readiness

Ready for exact-path staging and commit. The unrelated dirty worktree must be
left untouched.
