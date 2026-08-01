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

The runtime implementation is committed as
`6933998d9a65c63ff32f74350f43b9c8951215d7`. Its immutable detached release
exists at `/Users/cory/.steel-rag/releases/6933998d-play-along-melody`, and the
documented LaunchDaemon preflight passed for that exact commit.

Activation is blocked by the local macOS administrator-password boundary.
`sudo -n true` reports `a password is required`; Codex did not collect, request,
or handle the credential. The existing loopback protected service still
reports version `1ba8b849`, `/` returns 302, the canonical home returns 200,
and `/play/amazing-grace-guided` returns 404. Protected browser smoke therefore
has not run for this release.

The exact activation command is:

```bash
STEEL_RAG_REPO_DIR=/Users/cory/.steel-rag/releases/6933998d-play-along-melody \
STEEL_RAG_DATA_DIR='/Users/cory/Documents/Steel Guitar RAG' \
STEEL_RAG_EXPECTED_GIT_SHA=6933998d9a65c63ff32f74350f43b9c8951215d7 \
deploy/macos/install-private-preview-launchdaemon.sh activate
```

After activation, verify the local version and run authenticated browser smoke
at:
`https://app.steelguitarrag.com/play/amazing-grace-guided?v=play-along-6933998d-20260801`.

## Risks

Medium-low in application code. The route uses existing hard pitch,
top-voice, chord-support, and mechanical validation, and the complete suite is
green. The protected origin is confirmed to still run an older immutable
release until a local administrator authorizes activation.

## Human decision needed

No product decision is needed. A local administrator must authorize the exact
protected-preview LaunchDaemon activation command above.

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

Lane 12 should authorize the preflighted exact release, verify version
`6933998d`, and run authenticated protected browser smoke.

## Commit readiness

Safe to commit exact paths.
