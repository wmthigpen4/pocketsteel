# Play Along Amazing Tablature implementation

## Task summary

Implemented the approved Play Along/Amazing Tablature plan for the curated
Amazing Grace lesson. The player now teaches the song melody instead of
presenting one accompaniment grip per chord.

The default **Follow the Melody** lesson uses all 35 reviewed NEW BRITAIN
melody events against the Kevin MacLeod recording's authored audio clock,
chords, lyrics, and beat grid. It preserves the exact pitch and register as the
highest mechanical voice. The opening is locked at fret 3 as D4 on 5-6-8, G4
on 4-5-6, and B4 on 3-4-5.

The Lesson selector also preserves **Chord Foundation · Move the Bar** and
**Chord Foundation · Stay Near Fret 3**, and adds **Full Chord Melody ·
Advanced**. Chord Foundation copy explicitly says its highest note is not
necessarily the song melody.

Amazing Tablature now returns a versioned `play_along_melody_lessons_v1`
adapter payload. The browser renders that authoritative result; it does not
copy route ranking logic. Device imports remain chord-only.

The fretboard adds separate current and muted upcoming melody tags, keeps
pedal and lever labels on the individual strings they affect, separates
same-fret current/upcoming clusters, and retains all 24 frets. While paused,
the player explains melody note, scale degree, chord role, supporting pitches,
grip/control posture, movement reason, and up to two exact-melody alternatives.
Less Help retains only the playable current marker and hides melody and
upcoming details.

## Lane classification

- Product/API contract: Lane 18 / Lane 05
- Player and responsive teaching UI: Lane 06
- Musical and regression verification: Lane 15
- Exact-path commit: Lane 01
- Protected activation: Lane 12

## Files changed

- `docs/handoffs/task-completions/2026-08-01-1325-18-play-along-amazing-tablature-plan.md`
- `docs/handoffs/task-completions/2026-08-01-1348-18-play-along-amazing-tablature-implemented.md`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/song_practice.py`
- `tests/test_api_search.py`
- `tests/test_play_songs_ui.py`
- `tests/test_song_practice.py`
- `tests/test_song_projects_ui.py`
- `ui/play-song.html`
- `ui/play-song.js`
- `ui/play-songs.css`

No audio, rights file, curated track manifest, auth policy, home feature,
saved-data migration, Studio route, corpus, vector store, private source,
Cloudflare setting, DNS, Tunnel, or secret changed.

## Tests and checks

- Focused backend/UI/timeline suite: `35 passed in 4.68s`
- Full repository suite: `1548 passed in 83.09s`
- `node --check ui/play-song.js`: passed
- `git diff --check`: passed
- Golden opening: 5-6-8 / 4-5-6 / 3-4-5 at fret 3: passed
- Both melody lessons contain 35 exact reviewed events: passed
- Every melody position has the reviewed pitch as its highest mechanical
  pitch: passed
- Recommended route contains single-note, dyad, and triad textures: passed
- Full Chord Melody contains validated three-note events: passed
- Alternatives preserve the exact melody pitch/register: passed
- Audio-clock boundary promotion tests: passed at exact timestamp and +79 ms

## Local browser smoke

Smoke Target:

- Target type: local
- Result type: browser and responsive smoke
- Exact browser URL tested:
  `http://127.0.0.1:8897/play/amazing-grace-guided?v=melody-lessons-3`
- Auth provider: local development scaffold
- Local backend: `http://127.0.0.1:8897`
- Do not test: the retired `pocket-steel-play-along` prototype

Verified:

- Four lessons render in the approved order and Follow the Melody is default.
- D4/G4/B4 opening grips and current/upcoming melody tags are correct.
- The B4 explanation says why 3-4-5 is used and why 4-5-6 is not.
- Current and upcoming same-fret labels remain separately readable.
- A, B, and E-lower labels remain attached to their affected strings.
- Rest spans retain the authored chord and say `Rest · listen.`
- Less Help removes next markers, melody note names, lyrics, and explanations
  while retaining the current playable grip.
- The Kevin MacLeod MP3 reached ready state 4, played with `muted=false`,
  advanced against `audio.currentTime`, and reported no media error.
- 0.5x playback, restart, seeking, and a two-bar loop passed. The loop returned
  to the authored bar boundary at 4.737 seconds.
- Lyrics changed on their authored phrase timestamps.
- Runtime browser logs contained no errors.
- 844x390 landscape and 390x844 portrait screenshots were inspected. Portrait
  cards stack, current/upcoming details remain readable, and the 24-fret neck
  is horizontally pannable.

## Protected-preview status

Pending exact-commit release creation and Lane 12 activation. The prior
Play Songs handoff documents that LaunchDaemon activation requires a local
macOS administrator password. Codex will create and preflight the immutable
release after commit, but will not collect or handle that password.

## Risks

Medium-low in application code. The route uses existing hard pitch,
top-voice, chord-support, and mechanical validation, and the complete suite is
green. The remaining operational risk is that the protected origin may still
run an older immutable release until a local administrator authorizes
activation.

## Human decision needed

No product decision is needed. A local administrator may need to authorize
the protected-preview LaunchDaemon activation if the documented password gate
appears again.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-01-1325-18-play-along-amazing-tablature-plan.md`
- `docs/handoffs/task-completions/2026-08-01-1348-18-play-along-amazing-tablature-implemented.md`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/song_practice.py`
- `tests/test_api_search.py`
- `tests/test_play_songs_ui.py`
- `tests/test_song_practice.py`
- `tests/test_song_projects_ui.py`
- `ui/play-song.html`
- `ui/play-song.js`
- `ui/play-songs.css`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- unrelated historical handoffs
- audio, rights, corpus, vector data, private training, generated reports,
  release state, logs, environment files, credentials, and secrets

## Recommended next lane

Lane 01 should make the exact-path commit, then Lane 12 should create the
immutable release, verify its preflight, activate it if authorization is
available, and run authenticated protected browser smoke.

## Commit readiness

Safe to commit exact paths.
