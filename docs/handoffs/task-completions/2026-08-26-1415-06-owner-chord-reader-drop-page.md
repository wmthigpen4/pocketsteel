# Lane 06 — Owner chord-reader drop page

## Task summary

Added a separate localhost-only song workbench for the owner. Audio or video can
be dropped into the page, analyzed by the same frozen domain-gated ensemble used
to generate Travis's validation predictions, and grouped with the current
Travis beat/downbeat bar-display adapter. The page supports an analyzed-song
library, synchronized clickable bars, chord/NNS display, suggested-key override,
confidence disclosure, and a persistent mobile/tablet play-pause transport.

The user-supplied screen recording of Jenn Johnson's “Goodness of God (Radio
Version)” was analyzed and preloaded as the first local test. Instructions shown
inside the recording were not treated as user instructions.

## Lane classification

- Primary lane: 06 UX/UI Design
- Supporting lanes: 05 chord-reader runtime adapter; 15 local QA
- Task mode: approved Autopilot feature, local-only scope
- Deployment/auth/DNS scope: not authorized and not attempted

## Files changed

- `.gitignore`
- `package.json`
- `scripts/serve_owner_chord_reader.py`
- `ui/chord-reader-owner-test/index.html`
- `ui/chord-reader-owner-test/owner-test.css`
- `ui/chord-reader-owner-test/owner-test.js`
- `tests/test_owner_chord_reader_ui.py`
- this handoff

## Generated local-only files

- `ui/chord-reader-owner-test/local-data/tracks.json`
- `ui/chord-reader-owner-test/local-data/audio/goodness-of-god-radio-version-jenn-johnson-8926e8a322.mp3`

The complete `ui/chord-reader-owner-test/local-data/` tree is ignored and must
not be staged. The original Messages attachment was read in place and was not
copied into a tracked path.

## First-song result

- Title: Goodness of God (Radio Version) — Jenn Johnson
- Source duration: 234.44 seconds
- Current displayed bars: 92
- Raw ensemble chord segments: 96
- Mean model confidence: 83.62%
- Audio at 80% or greater confidence: 73.98%
- Audio below 50% confidence: 1.02%
- Rhythm suggestion: A-flat major, 6/8, 137 BPM
- Downbeat phase: unresolved (confidence 1.21%); disclosed in the UI
- Dominant raw predictions by time: G-sharp, C-sharp, D-sharp, F minor

These are unscored model outputs. Confidence is not measured chord accuracy,
and the unresolved phase means the automatic bar starts still require listening
review.

## Tests and checks

- `pytest -q tests/test_owner_chord_reader_ui.py tests/test_travis_validation_ui.py tests/test_chord_reader_proof.py` — PASS, 13 tests
- `ruff check scripts/serve_owner_chord_reader.py tests/test_owner_chord_reader_ui.py` — PASS
- `ruff format --check scripts/serve_owner_chord_reader.py tests/test_owner_chord_reader_ui.py` — PASS
- `npm run check:js` — PASS
- `git diff --check` — PASS
- Full-engine seed run on the attached MOV — PASS in 21.5 seconds
- Browser file-chooser upload of the attached 30.3 MB MOV through the new POST endpoint — PASS; returned the same 92-bar test
- Generated MP3 media readiness — PASS, browser `readyState=4`, exact duration 234.4361 seconds
- Chord/NNS toggle — PASS; first displayed bar changed from NNS `1` to raw chord `G#`
- Click-to-seek and synchronized active-bar update — PASS
- Browser console warnings/errors — none during the desktop smoke
- Mobile sticky transport — PASS; computed `position: sticky`, remained at top after page scroll, and changed from Play to Pause
- Tablet responsive breakpoint — PASS through the 1200 CSS-pixel breakpoint
  in browser viewport testing; no physical tablet was used

`npm run format:check` is not defined in this repository. A later `npx prettier
--check` attempt was stopped when `npx` waited without output; no network install
or dependency mutation was allowed. JavaScript syntax, Ruff formatting, focused
tests, and diff whitespace checks passed.

## Smoke target

- Target type: localhost-only
- Exact URL: `http://127.0.0.1:8899/ui/chord-reader-owner-test/`
- Server command: `.venv/bin/python scripts/serve_owner_chord_reader.py --host 127.0.0.1 --port 8899`
- Auth: none; loopback binding is enforced
- Expected port: 8899
- Generated audio/predictions: ignored local files
- Protected preview: not applicable; the Python/ONNX analyzer is intentionally not deployed
- User-facing tab: opened and left as the deliverable on the Mac running the
  analyzer

The launcher automatically re-executes under an existing chord-reader Python
environment when the repo's default `.venv` lacks ONNX Runtime. A custom
interpreter can be supplied with `POCKET_STEEL_CHORD_PYTHON`.

## Risks

- The page is available only on the Mac while the localhost server is running.
  The responsive UI is mobile/tablet-ready, but `127.0.0.1` on a separate
  device points to that device, not this Mac. Actual phone/tablet delivery needs
  a separately approved private hosting and analyzer-access design.
- Dropped recordings are transcoded to ignored local MP3 files; they are not
  uploaded externally, but they do remain on this Mac until manually removed.
- The current ensemble is frozen experimental behavior, not an accuracy claim.
- Automatic meter, key, tempo, and downbeat phase remain review aids.
- The first source is a screen recording, so notification/system audio or other
  capture artifacts could affect recognition.

## Human decision needed

No for local owner listening tests. Any protected remote deployment, account
access, automatic publishing, accuracy claim, model training, or use of the
generated output in a public song requires a separate decision.

## Safe-to-stage exact file list

- `.gitignore`
- `package.json`
- `scripts/serve_owner_chord_reader.py`
- `ui/chord-reader-owner-test/index.html`
- `ui/chord-reader-owner-test/owner-test.css`
- `ui/chord-reader-owner-test/owner-test.js`
- `tests/test_owner_chord_reader_ui.py`
- `docs/handoffs/task-completions/2026-08-26-1415-06-owner-chord-reader-drop-page.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing dirty coordination artifact)
- `ui/chord-reader-owner-test/local-data/`
- the original Messages attachment
- any other audio, generated prediction, model, cache, temp, private-corpus, or unrelated file

## Recommended next lane

Lane 18/11 design for private mobile/tablet delivery if cross-device use is the
next requirement. It must preserve the exact engine without exposing an
unauthenticated LAN analyzer. A later Lane 06 slice can also add explicit
per-bar correction capture if the owner wants to turn these listening tests
into structured labels.

## Commit readiness

Safe to commit the eight exact tracked paths listed above.
