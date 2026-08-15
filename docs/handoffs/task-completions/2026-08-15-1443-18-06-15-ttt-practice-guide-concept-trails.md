# TTT Practice Guide with Concept Trails — implementation handoff

## Task summary

Implemented the approved local, ungated pilot for a deterministic Travis Toy
Tutorials Practice Guide. The feature answers “what should I practice?” and
“what background do I need?” without a learner-time model call.

The implementation contains:

- a private build-time `ttt_concept_graph_v1` compiler that excludes Zoom,
  preserves exact cue evidence, enforces dedicated-lesson ranking, and writes
  semantic candidates only to an ignored exception-review queue;
- a curated steel-guitar concept taxonomy and safe non-Zoom lesson catalog;
- four `lesson_companion_v2` pilots: right-hand technique, pedal/theory,
  fretboard pathways, and Howdy application;
- explicit deterministic runtime and ordered guide-block contracts that drive
  the browser renderer;
- one vertical Teachable-style guide with comments-space preserved after it;
- source-backed Concept Trail landing pages with explicit detour timestamps and
  short target-lesson excerpts;
- comment-informed diagnostics that contain neither raw comments nor member
  identities;
- four deterministic one-page printable practice cards;
- a source-verifying, allowlisted static packaging command;
- restrictive static headers and isolation checks for non-guide routes.

The Howdy pilot intentionally publishes lesson landmarks and concept detours,
not the unapproved note-for-note tab or inferred chord chart. Its displayed key
is D from the private reviewed transcription context and remains explicitly
review-gated for chord/harmony claims.

## Private audit result

The non-Zoom compiler processed 163 lessons and produced 624 cue-grounded
concept mentions across 14 initial concepts. It identified 392
publication-eligible exact mentions, produced 80 authoring recommendations, and
reduced offline semantic/correction exceptions to a 33-item private review
queue. All applicable concepts passed the dedicated-lesson-first ranking
invariant. Semantic candidates carry `autoPublishAllowed: false`.

The final static pilot publishes only 21 short lesson moments and 10 distinct
Concept Trail targets. All 21 moments passed exact source-window matching. All
10 destinations passed exact cue-boundary validation plus verbatim target-
excerpt matching; titles and semantic suggestions cannot satisfy that check.

Private graph artifacts, raw transcripts, raw comments, member identities, and
the Howdy reviewed evidence file remain outside Git and outside the bundle.

## Files changed

- `steel_guitar_rag/ttt_concept_graph.py`
- `scripts/build_ttt_concept_graph.py`
- `scripts/package_travis_practice_guides.py`
- `partner_companions/travis_practice_guide/__init__.py`
- `partner_companions/travis_practice_guide/README.md`
- `partner_companions/travis_practice_guide/release.py`
- `partner_companions/travis_practice_guide/content/concept-taxonomy.json`
- `partner_companions/travis_practice_guide/content/lesson-catalog.json`
- `partner_companions/travis_practice_guide/content/pilot-guides.draft.json`
- `partner_companions/travis_practice_guide/site/practice-guide.css`
- `partner_companions/travis_practice_guide/site/practice-guide.js`
- `partner_companions/travis_practice_guide/templates/404.html`
- `partner_companions/travis_practice_guide/templates/guide.html`
- `partner_companions/travis_practice_guide/templates/index.html`
- `partner_companions/travis_practice_guide/templates/jump.html`
- `tests/test_ttt_concept_graph.py`
- `tests/test_travis_practice_guide.py`
- `package.json`
- this handoff

Generated and intentionally uncommitted:

- `corpus-private/ttt-concept-graph/graph.json`
- `corpus-private/ttt-concept-graph/report.json`
- `corpus-private/ttt-concept-graph/review-queue.json`
- `tmp/ttt-practice-guide-2026-08-15.2/`
- `tmp/pdfs/ttt-practice-guide-2026-08-15.2/`
- `output/pdf/ttt-practice-guide/*-ttt-practice-guide-2026-08-15.2.pdf`

## Tests and checks run

- `.venv/bin/pytest -q tests/test_travis_companion.py tests/test_ttt_concept_graph.py tests/test_travis_practice_guide.py` — 36 passed.
- `npm run check:js` — passed, including the new runtime.
- `.venv/bin/ruff check ...` for all new Python and tests — passed.
- `git diff --check` — passed.
- real private packaging run — passed with 21 moments and 10 distinct Concept
  Trail targets source-verified.
- real private concept build — 163 non-Zoom lessons, 624 exact mentions, 33
  review-only exceptions, dedicated-first ranking passed, and shorter
  prerequisites are preferred after dedicated coverage.
- generated bundle allowlist/private-source scan — passed.
- local route isolation for `/api/answer`, `/api/search`, `/ui/test`, `/chat`,
  `/melody`, `/lessons`, and encoded traversal — all returned 404.
- in-app browser smoke — four-pilot index rendered; guide selector, 2/5/10
  minute state, collapsed moment search, Concept Trail landing, exact timestamp,
  key display, print action, and comments-space all rendered and behaved as
  designed.
- PDF QA — all four PDFs are one-page Letter documents; every page was
  rasterized and visually inspected; Poppler text extraction found the title,
  page count, success condition, and attribution on every card.

## Risks

- Concept discovery remains an authoring aid. Exact aliases may become ranked
  authoring recommendations; the 33 high-confidence semantic/correction
  exceptions cannot publish without review.
- The static Concept Trail landing page highlights the exact target time. It
  cannot seek the cross-origin Teachable player automatically yet.
- Comment-derived diagnostics are editorial synthesis and should be refined if
  Travis gives direct language or preferred corrections.
- The Howdy musical transcription and chord/harmony remain review-gated. This
  implementation deliberately does not promote the existing inferred material.
- This is a local HTTP preview. Cloudflare, Access, DNS, deployment, analytics,
  and Teachable authorization were not touched.

## Human decision needed

- Review whether this vertical density and the “Need this concept?” placement
  feel appropriate beneath a real lesson.
- Decide which pilot should receive Travis’s first review.
- Decide whether the next slice should add more Tier A/B lessons or pursue
  progressive Teachable timestamp seeking.

No human decision is required for the deterministic runtime or private-source
guardrails in this slice.

## Safe-to-stage exact file list

```text
package.json
steel_guitar_rag/ttt_concept_graph.py
scripts/build_ttt_concept_graph.py
scripts/package_travis_practice_guides.py
partner_companions/travis_practice_guide/__init__.py
partner_companions/travis_practice_guide/README.md
partner_companions/travis_practice_guide/release.py
partner_companions/travis_practice_guide/content/concept-taxonomy.json
partner_companions/travis_practice_guide/content/lesson-catalog.json
partner_companions/travis_practice_guide/content/pilot-guides.draft.json
partner_companions/travis_practice_guide/site/practice-guide.css
partner_companions/travis_practice_guide/site/practice-guide.js
partner_companions/travis_practice_guide/templates/404.html
partner_companions/travis_practice_guide/templates/guide.html
partner_companions/travis_practice_guide/templates/index.html
partner_companions/travis_practice_guide/templates/jump.html
tests/test_ttt_concept_graph.py
tests/test_travis_practice_guide.py
docs/handoffs/task-completions/2026-08-15-1443-18-06-15-ttt-practice-guide-concept-trails.md
```

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user change)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `corpus-private/`
- `partner_companions/travis_practice_guide/__pycache__/`
- all raw/private VTT, comments, rights, review, or Howdy evidence files

## Recommended next lane

Lane 18 Product / Architecture for owner review of the guide shape, then Lane 06
for any density/copy refinements. Remain local until the user separately approves
deployment or Teachable integration work.

## Commit readiness

Ready for one exact-path feature commit. No deployment is authorized or needed
for this local pilot.
