# Device-local Play Along route options restore

## Task summary

Restored the missing lesson choice for device-local Play Along songs without rebuilding or restyling the application. Local songs now expose two functional routes in the existing Play Along lesson selector:

- `Chord Foundation · Move the Bar`
- `Chord Foundation · Stay Near Fret N`, where the home fret is derived from the song key (for example, A uses fret 5)

The two choices use distinct deterministic backend policies. Stay Near centers valid E9 grips on the key's home fret and favors pedal/lever changes. Move the Bar favors practical movement between separate chord pockets. Curated-song route behavior is preserved.

## Files changed

- `steel_guitar_rag/song_practice.py`
- `ui/play-song.js`
- `ui/play-song.html`
- `tests/test_song_practice.py`
- `tests/test_play_songs_ui.py`
- this handoff

No visual styling, fretboard rendering, audio, local project storage, authentication, Cloudflare, DNS, Tunnel, secrets, corpus, or private data changed.

## Verification

- Focused player and arranger suite: `36 passed`
- Asset-digest and catalog checks: `2 passed`
- Full repository suite: `1587 passed in 84.52s`
- `node --check ui/play-song.js`: passed
- `git diff --check`: passed
- Deterministic A-major route check:
  - Stay Near: A, D, and E remain at fret 5 using validated controls
  - Move the Bar: A, D, and E travel through separate validated pockets

## Deployment

Activation must use an immutable detached release at this exact commit, pass preflight and alternate-port health/version checks, then verify the authenticated protected Play Along page. The active user's device-local song should show both route choices without losing its OPFS audio or saved map.

## Risk

Low. The change is limited to device-local chord route selection and the deterministic song-practice route scorer. Existing balanced and authored curated routes retain their prior path.

## Safe-to-stage exact paths

- `docs/handoffs/task-completions/2026-08-04-local-play-along-route-options-restore.md`
- `steel_guitar_rag/song_practice.py`
- `tests/test_play_songs_ui.py`
- `tests/test_song_practice.py`
- `ui/play-song.html`
- `ui/play-song.js`

Do not stage `.venv` or unrelated files.
