# Howdy full-song and taught-solo playback scopes

## Task summary

Implemented the user-confirmed split between the complete Howdy backing track
and the specific solo taught in Travis's lesson.

- `Full Song` now owns the complete 237.187-second backing track and a 3:57
  transport. Solo move, fretboard, phrase-aside, tab, and loop animation are
  hidden in this scope.
- `Solo` now owns a 24.064-second practice window. Its authored event times
  remain relative to the solo, while the browser deterministically seeks the
  source recording at 118.320-142.384 seconds.
- The map presents both scopes explicitly, and `Jump to taught solo` moves from
  the full recording into the exact lesson window.
- The existing G/A/D/C chart is now labeled only as the taught solo's
  eight-bar harmony. It is not represented as a chart for the complete song.
- The printable three-page notation-plus-E9-tab handout was regenerated from
  the same solo event graph as revision
  `howdy-transcribed-review-2026-08-14.4`.

The Teachable lesson was inspected again. Its title is explicitly
`"Howdy" Solo (Eddy Dunlap)`, and it supplies the complete custom backing-track
MP3 as a download. No Travis-authored full-song chord chart is surfaced on the
lesson page. A deterministic full-recording chord-analysis experiment inferred
the wrong tonal center and a chord vocabulary that conflicts with the
transcript-backed D-major solo data, so that result was rejected and was not
written into the companion.

## Lane and task mode

- Primary lane: `06 UX/UI Design` plus private companion authoring.
- Verification lane: `15 QA / Browser Smoke`.
- Mode: GREEN for the playback-scope split; musical and print content remains
  visibly Travis-review-required.

## Files changed

- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/release-config.example.json`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `scripts/package_travis_companion.py`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-14-1314-15-howdy-backing-duration-diagnosis.md`
- this implementation handoff

Private/generated owner-review inputs changed outside Git:

- The canonical companion was advanced to revision `.4` with explicit
  `fullSong` and `taughtSolo` scopes.
- The browser-ready full recording was regenerated from the untouched licensed
  master as one metadata-stripped audio-only MP3. Its SHA-256 is
  `0ae27efc959383a80151e91bae12e03bc50ec9bdbfb5d8c1973cacfc482a11c6`.
- The exact solo excerpt remains hash-pinned at
  `975ead0dc8d78b7f2cd11bafe75c4c6d8661592fa678c450eb8d0544f7ea8cab`.
- The rendered PDF and temporary Pages bundle remain ignored and outside the
  exact staged file list.

No deployment, Cloudflare project, DNS, Access policy, tester identity, remote
gate, Teachable OAuth app, model/RAG service, or general application runtime
was changed.

## Deterministic media contract

- Full source duration: `237187 ms` (`3:57.187`).
- Taught-solo source range: `118320-142384 ms`.
- Taught-solo duration: `24064 ms` (`0:24.064`).
- The exact excerpt was located by waveform cross-correlation against the full
  source at `118.3200` seconds with score `0.999407`.
- Tab, phrase, solo-chord, fretboard, and coaching events stay solo-relative
  from `0-24064 ms`.
- Browser state converts deterministically between scope-relative UI time and
  absolute source-audio time.
- Both scopes use one fully loaded same-origin audio Blob in the local preview,
  avoiding reliance on MP3 byte-range behavior that Wrangler Pages dev does
  not provide. No external media or model request is made.
- A separate hash-pinned exact solo excerpt is still required by packaging as
  review evidence and a portable fallback asset.

## Tests and checks

- `node --check partner_companions/travis_howdy/site/companion.js`: PASS.
- `pytest tests/test_travis_companion.py -q`: **23 passed**.
- `git diff --check`: PASS.
- Deterministic owner-review packaging: PASS, 13 allowlisted files.
- Bundle verifier: PASS, same-origin-only network policy and blocked general
  app routes.
- Browser smoke through Wrangler Pages dev:
  - Map shows `Full song 3:57` and `Taught solo 0:24`.
  - Key remains visibly `D`.
  - Discussion space remains after the companion.
  - Solo scope seeks the full source to `118.320` seconds and advances authored
    relative UI time, bars, and exact transcript-backed move copy.
  - Full Song resets the same source to `0:00`, exposes a 237187 ms seek range,
    advances playback, and hides loop, tab, move, fretboard, and phrase-aside
    animation.
  - Search remains confined to the Map layer.
- PDF QA:
  - 3 US-letter pages.
  - Every page rasterized at 144 DPI and inspected.
  - No clipped systems, split phrase headings, missing controls, broken footer,
    or page-number defect observed.
  - Revision `.4`, key D, 4/4, 79.8 BPM, chord review status, `0hA` legend,
    notation, and ten-string tab are visible.
- Browser-ready audio QA:
  - 237.187052 seconds.
  - One MP3 audio stream only.
  - No embedded cover image or source title/artist/composer tags.

## Integration notes

The complete backing track and taught solo are distinct product layers even
though they share one source recording. Do not merge their clocks again and do
not stretch the eight-bar solo chord form across the 3:57 song.

A complete full-song chord play-along still requires a human-reviewed song
chart or another trusted authored source. The current deterministic audio
analyzer was deliberately not accepted as musical ground truth after it failed
this track. The preview is honest about this: it provides full-song playback
and the exact taught-solo chart, rather than a plausible-looking full-song
chart with unverified chords.

## Risk assessment

- Code/runtime risk: low. The scope conversion and package contract are covered
  by focused tests and browser smoke.
- Musical risk: medium until Travis reviews the solo transcription and harmony.
- Full-song chord-chart risk: high if inferred automatically; no such chart was
  shipped.
- Deployment risk: none in this task because the preview remains local and
  ungated.

## Human decision needed

No decision is needed to inspect the local split. A later decision is needed
on how to source a trustworthy complete-song chord chart: Travis-provided or
human-reviewed transcription is recommended.

## Safe-to-stage exact file list

- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/release-config.example.json`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `scripts/package_travis_companion.py`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-14-1314-15-howdy-backing-duration-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-14-1342-06-howdy-full-song-solo-scopes.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`, `tmp/`, `.wrangler/`, `/tmp/howdy-*`, private companion JSON,
  backing audio, videos, transcripts, rendered PDFs, identities, credentials,
  and all unrelated dirty files

## Recommended next lane

- Lane 15: owner review of the local split and solo tab.
- Private musical authoring: obtain or review a complete-song chord chart only
  if full-song chord karaoke is required for the pilot.
- Lane 12/Cloudflare only after explicit deployment authorization.

## Commit readiness

Safe to commit the exact file list above.

## Suggested next step

Have Cory inspect `/howdy/embed-demo` and switch between `Full Song` and `Solo`.
Treat the solo tab/harmony as review material and the complete-song chart as a
separate future musical approval item.
