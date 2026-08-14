# Howdy companion feedback: lesson search, layers, tab, and chord play-along

## Task summary

Implemented the six owner-smoke corrections for the deterministic Howdy
companion. The local preview now has a timestamped transcript-backed technical
search, four materially different layer workspaces, step-by-step phrase study,
unambiguous open-position pedal-hammer notation, a chord-centered play-along,
persistent Key D context, and an eight-bar chord chart. No Access gate,
identity, remote deployment, DNS, Cloudflare project, general application
surface, model call, retrieval client, raw transcript, or partner access was
added.

The opening move remains at the open fret because Travis explicitly teaches an
open attack followed by the A pedal. It is now rendered as `0hA`, with the
sustained sixth string rendered as a continuation mark and copy stating that
the bar does not move.

The chord chart was derived deterministically from the private supplied
backing track on the authored 79.8 BPM grid. It is marked
`Audio-derived · Travis review required` everywhere and is not represented as
approved.

## Lane classification

- Primary: `06 UX/UI Design`
- Verification: `15 QA / Answer Eval`
- Closeout: `01 Repo Steward`
- Task mode: YELLOW UI-flow change already explicitly approved by the user's
  implementation request and follow-up feedback.

## Files changed

- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/README.md`
- `tests/test_travis_companion.py`
- this handoff

Ignored/private outputs refreshed outside Git:

- `~/.steel-rag/travis-preview/howdy/howdy.transcribed-review.json`
- `tmp/travis-preview-draft/`
- `output/pdf/Howdy-transcript-backed-review.pdf`

No raw transcript, lesson video, source backing track, review audio, PDF, or
private companion JSON is staged.

## Behavior completed

- Search: seven timestamped technical lesson moments, exact excerpts labeled
  separately from authored summaries, deterministic all-term matching, and
  one-click navigation to the corresponding event and phrase.
- Lesson Map: overview only, with the phrase route and chord chart.
- Phrase Practice: pauses by default, selects 50%, enables the phrase loop,
  and exposes Previous/Next move controls.
- Play Along: selects Chord Foundation, uses 75%, removes the solo tab from
  that layer, and holds fixed E9 chord grips until analyzed harmony changes.
- Explore: pauses playback and displays only two lesson-demonstrated comparison
  positions without replacing the primary route.
- Key/chords: Key D, 4/4, and 79.8 BPM remain visible; the chart displays
  `G→A | A | D | D→A→D | G→A | A | C→D | D` with NNS labels.
- Print: Key D, tempo, chord chart, `0hA` legend, chord symbols, six notation
  systems, ten-string E9 tab, revision, page numbers, and member-use footer are
  generated from the same canonical data.

## Tests and checks

- `.venv/bin/python -m pytest tests/test_travis_companion.py -q` — 19 passed.
- `node --check partner_companions/travis_howdy/site/companion.js` — passed.
- Private `validate_companion(..., release=False)` — passed for 54 events,
  nine chord ranges, seven lesson moments, and 24,064 ms.
- Local deterministic package and verifier — passed; 12 allowlisted files,
  same-origin-only networking, eight blocked route/traversal checks.
- HTTP route smoke — `/howdy/`, `/howdy/embed-demo/`, `/howdy/print/` returned
  200; `/api/search`, `/chat`, and `/lessons` returned 404.
- Browser smoke — search `hammer` returned only the open-position pedal moment;
  opening it switched to Phrase Practice at bar 1 beat 1.5 with `0hA`, a
  continuation mark, and `bar stays put` copy.
- Browser smoke — Play Along exposed the G chord grip at fret 10 with A+B,
  identified the next A grip at fret 5, and hid the solo tablature.
- Browser smoke — Explore exposed both fixed comparisons and no transport.
- Browser smoke — full page and print routes showed Key D, search/chart, chord
  chart, `0hA`, and the closing phrase.
- PDF QA — all three letter-size pages rasterized at 120 DPI and inspected;
  no clipped systems, phrase headings, controls, chart cells, or footers.
- `git diff --check` — required before commit.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8899/howdy/embed-demo/`
- Cache-busted URL tested: not needed for the local content-hashed bundle
- Exact URL the user should use: `http://127.0.0.1:8899/howdy/embed-demo/`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8899`
- Expected backend port: `8899`
- Expected git HEAD: implementation commit produced by this task
- Version endpoint: none in this isolated static product
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: visible companion
  revision and 12-character build SHA in the preview ribbon
- Whether app root `/` works: yes; it redirects to `/howdy`
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: no
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no; isolation
  requires 404
- Who should test this URL: Codex and the user
- Do not test these URLs: general Steel Guitar RAG app or API routes
- Known caveats: local owner review only; musical, chord, copedent, print, brand,
  and audio-rights approvals remain false

## Integration notes

The browser remains model-free. Search is an in-memory index lookup over
allowlisted technical moments; switching, playback, stepping, looping, tab,
fretboard, chord highlighting, and print use only static canonical data.
`lessonMoments` and labeled chord grips receive additional packager validation.

The owner-review chord range at bar 5 moves to A at the nearest authored event
boundary (bar 5 beat 3.25). This preserves a single canonical event graph and
is intentionally review-required.

## Risk assessment

Medium. The implementation and isolation behavior are test-green, but the
musical content is still a review artifact. The audio-derived chord chart and
all solo/tab/copedent details must be reviewed before a partner-facing release.
Rollback is the prior local bundle or the preceding Git commit; no remote state
was changed.

## Human decision needed

Yes: review the chord chart—especially the bar 4 turnaround, bar 5 boundary,
and bar 7 C-to-D close—and continue correcting any literal tab events before
requesting Travis approval. No decision is needed to inspect the local preview.

## Safe-to-stage exact file list

- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-14-1250-06-howdy-feedback-search-chords.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- the three pre-existing unrelated untracked handoffs
- `tmp/`, `.wrangler/`, `output/`, private companion/source/video/audio data,
  identities, credentials, and all unrelated dirty files

## Recommended next lane

Continue owner smoke in Lane 06. After owner corrections settle, Lane 15 should
perform independent musical/print QA. Lane 12 remains out of scope until a
separate remote deployment is explicitly authorized.

## Commit readiness

Safe to commit

## Suggested next step

Open `http://127.0.0.1:8899/howdy/embed-demo/`, search `hammer`, step through
Phrase Practice, then review each chord transition in Play Along against the
supplied backing track.

## Commit and post-commit smoke result

- Implementation commit: `bd60cb7bc0f335035ce32db3284136d46acef71b`
- The local content-hashed bundle was rebuilt from that commit and the
  allowlist/isolation verifier passed again.
- Browser smoke confirmed revision
  `howdy-transcribed-review-2026-08-14.2`, build `bd60cb7bc0f3`, Key D, seven
  indexed moments, the chord chart, held G chord grip, hidden solo tab in Play
  Along, and the two isolated Explore comparisons.
- `integration-status.md` was not refreshed because it already contains a
  pre-existing unrelated dirty edit; it remains parked and unstaged.
