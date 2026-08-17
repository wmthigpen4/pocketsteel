# Holistic song-chart authoring and Howdy form correction

## Task summary

Reworked full-song chord authoring so the Play Along reader is useful evidence
without being allowed to turn musical context into a confident learner-facing
guess. Added a deterministic, reusable authoring layer that can align a private,
rights-reviewed quarter-note reference chart to a recording, preserve named song
sections, withhold unsupported chord quality, and replace an exact lesson scope
with its source-timed taught route.

The Howdy owner-review artifact was rebuilt through that path using two public
chart references plus exact lesson-scope anchors. The local companion now shows:

- separate `Solo grid 79.8 BPM` and `Full song · 158 BPM` labels;
- seven named song sections instead of calling 78 half-time measure groups bars;
- a 3:57 horizontally scrolling root/NNS chart with 55 meaningful chord-change
  events and section jump controls;
- only the corroborated roots `D`, `G`, `A`, and `F`, with chart-supplied chord
  qualities withheld;
- the exact lesson-timed solo route over the steel-break window;
- the former bar-7 `C` changed to an owner-review `F / bIII`, including the
  fretboard route and the printable chord form;
- synchronized section, chord, NNS, transport, and fretboard state during
  playback.

The reusable fallback also groups audio-only analysis into repeated eight-measure
forms and withholds roots selected only by key or neighboring-chord context.
Learner interaction remains static, deterministic, same-origin, and model-free.

No Cloudflare, Access, DNS, deployment, Teachable authorization, analytics,
general app, RAG, model, or authentication changes were made.

## Files changed

- `ui/practice-analysis-worker.js`
- `scripts/lib/song_chart_authoring.js`
- `scripts/author_travis_song_chords.js`
- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `tests/test_practice_analysis_v2.py`
- `tests/test_travis_companion.py`
- this handoff

Generated and intentionally uncommitted:

- `/Users/cory/.steel-rag/travis-preview/howdy/howdy.song-chart-reference.v1.json`
- `/Users/cory/.steel-rag/travis-preview/howdy/howdy.transcribed-review.7.json`
- `output/pdf/Howdy-music-first-review-v7.pdf`
- `tmp/howdy-owner-review-2026-08-17.4/`
- `tmp/howdy-owner-review-2026-08-17.release-manifest.json`

## Tests and checks run

- JavaScript syntax checks for the analysis worker, song-chart module, authoring
  command, and browser runtime — passed.
- Ruff for the release validator and changed tests — passed.
- `.venv/bin/pytest -q tests/test_practice_analysis_v2.py tests/test_practice_reference_validation.py tests/test_travis_companion.py tests/test_travis_practice_guide.py tests/test_ttt_concept_graph.py tests/test_play_songs_ui.py tests/test_practice_tools.py` — 77 passed.
- Focused root-only event-merging test after its final assertion — passed.
- Deterministic bundle packaging and allowlist verification — passed with 18
  files, same-origin-only networking, and all general app/RAG routes blocked.
- In-app browser smoke — passed for 3:57 full-song mode, seven section jumps,
  158 BPM label, corrected `F / bIII`, 55-event scrolling chart, playback
  advancing from 2:16 to 2:17, synchronized fretboard state, retained discussion
  placement, and no browser warnings or errors.
- Printable PDF — three Letter pages, rasterized and visually inspected; no
  clipping or missing systems, and extracted text contains the corrected
  `F > D` bar-7 form, revision, attribution, footer, and page numbers.

## Smoke Target

- Target type: local, ungated owner preview
- Browser result: passed in the in-app browser
- Exact route: `http://127.0.0.1:8897/practice-guide/howdy/`
- Cache-busted route: `http://127.0.0.1:8897/practice-guide/howdy/?build=howdy-v7`
- User review route: `http://127.0.0.1:8897/practice-guide/howdy/?build=howdy-v7`
- Auth: none; not required
- Local backend: `http://127.0.0.1:8897`
- Expected port: `8897`
- Expected HEAD/version: the feature commit containing this handoff; the
  post-commit bundle marker must match `git rev-parse --short HEAD`
- Version endpoint: none; verify the visible owner-preview revision and build
  SHA marker instead
- Root route expected: yes
- General `/ui/*` route expected: no; it must return `404`
- Smoke owner: implementation agent and owner
- Do not test: external preview, Cloudflare, Access, DNS, Teachable iframe, or
  any previous ignored bundle directory

## Risks

- The public references support the song form and chord roots, not Travis's
  approval. Every Howdy full-song event remains owner-review content.
- The `F / bIII` correction is supported by both cited public charts and the
  instrumental placement, but it still needs an owner listen-through and later
  Travis approval.
- Chart qualities are deliberately withheld. A future human-reviewed chart can
  add dominant, minor, suspended, or power-chord quality without changing the
  learner runtime.
- Section boundaries are aligned deterministically from reference beats through
  recording and lesson anchors. They are useful navigation points, but an owner
  should listen through every boundary before partner review.
- The taught solo tablature, source copedent, and print layout remain owner
  review, not partner-approved content.
- Rebuilding the complete local preview requires private audio, screenshots,
  reference data, and owner-review artifacts outside Git.

## Human decision needed

Listen through the seven section boundaries and the `A > F > D` ending of the
taught break. Confirm or correct those musical claims before any Travis-facing
preview. No decision is needed to keep using the local ungated build.

## Safe-to-stage exact file list

```text
ui/practice-analysis-worker.js
scripts/lib/song_chart_authoring.js
scripts/author_travis_song_chords.js
partner_companions/travis_howdy/README.md
partner_companions/travis_howdy/release.py
partner_companions/travis_howdy/site/companion.css
partner_companions/travis_howdy/site/companion.js
partner_companions/travis_howdy/templates/companion.fragment.html
tests/test_practice_analysis_v2.py
tests/test_travis_companion.py
docs/handoffs/task-completions/2026-08-17-0815-05-06-15-howdy-holistic-song-chart-authoring.md
```

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user change;
  intentionally not refreshed or overwritten)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `/Users/cory/.steel-rag/`
- all private transcript, comment, audio, screenshot, rights, approval, and
  musical-reference inputs

## Recommended next lane

Lane 15 for owner musical QA of form boundaries, the `F / bIII` correction,
and the printed solo. Stay local and ungated until deployment is separately
authorized.

## Commit readiness

Ready for one exact-path feature commit after the final full suite and diff
checks. The local review server is live on port 8897.
