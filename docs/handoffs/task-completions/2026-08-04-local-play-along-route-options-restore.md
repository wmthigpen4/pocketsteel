# Device-local Play Along route options restore

## Task summary

Restored the missing lesson choice for device-local Play Along songs without rebuilding or restyling the application. Local songs now expose two functional routes in the existing Play Along lesson selector:

- `Chord Foundation · Move the Bar`
- `Chord Foundation · Stay Near Fret N`, where the home fret is derived from the song key (for example, A uses fret 5)

The two choices use distinct deterministic backend policies. Stay Near centers valid E9 grips on the key's home fret and favors pedal/lever changes. Move the Bar favors practical movement between separate chord pockets. Curated-song route behavior is preserved.

## Files changed

- `steel_guitar_rag/song_practice.py`
- `ui/play-song.js`
- `ui/play-song-route-options-v6.js` (immutable asset alias)
- `ui/play-song.html`
- `tests/test_song_practice.py`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- this handoff

No visual styling, fretboard rendering, audio, local project storage, authentication, Cloudflare, DNS, Tunnel, secrets, corpus, or private data changed.

## Verification

- Focused player and arranger suite: `36 passed`
- Asset-digest and catalog checks: `2 passed`
- Final player and same-origin asset checks: `23 passed`
- Full repository suite: `1587 passed in 84.52s`
- `node --check ui/play-song.js`: passed
- `git diff --check`: passed
- Deterministic A-major route check:
  - Stay Near: A, D, and E remain at fret 5 using validated controls
  - Move the Bar: A, D, and E travel through separate validated pockets

## Deployment

Runtime commit `3f483bb32f999dfaa6591e22211d450c28b23542` is active from the immutable detached release at `/Users/cory/.steel-rag/releases/3f483bb3-local-route-options-production`. Exact-release preflight, alternate-port health/version checks, production live/ready/version checks, and authenticated browser smoke passed.

The user's existing `Shenandoah_NOVOCAL-200223-081529` device-local song retained its OPFS audio and saved map. The protected page displayed both `Move the Bar` and `Stay Near Fret 5`; switching to Stay Near updated the objective without an error, switching back restored Move the Bar, and the browser console remained clean. A new immutable script alias was required because protected browser smoke proved that the prior asset path remained stale at the edge despite a changed digest query.

## Risk

Low. The change is limited to device-local chord route selection and the deterministic song-practice route scorer. Existing balanced and authored curated routes retain their prior path.

## Safe-to-stage exact paths

- `docs/handoffs/task-completions/2026-08-04-local-play-along-route-options-restore.md`
- `steel_guitar_rag/song_practice.py`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_song_practice.py`
- `ui/play-song.html`
- `ui/play-song.js`
- `ui/play-song-route-options-v6.js`

Do not stage `.venv` or unrelated files.
