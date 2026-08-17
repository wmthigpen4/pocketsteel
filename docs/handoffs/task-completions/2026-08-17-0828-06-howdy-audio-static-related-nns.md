# Howdy instructor audio selection, static related lessons, and NNS chart mode

## Task summary

Added three scoped lesson-companion improvements requested during local owner
smoke:

1. The Teachable-style lesson page now has an instructor audio-source area
   directly beneath the video. It accepts one required `primaryTrack`, multiple
   `additionalTracks`, and generates an `analysisTrack` radio group so the exact
   MP3 selected for companion authoring is explicit.
2. Related Travis videos are now three lesson-level recommendations rendered
   once. They remain unchanged and visible while the selected phrase, playback
   position, practice view, chord, and fretboard state change.
3. The full-song scrolling chart now has a `Chords / NNS` switch. Chord mode
   keeps chord symbols large with Nashville numbers below; NNS mode promotes
   Nashville numbers to the large label and retains chord symbols below.

The browser-only instructor form stores selected `File` objects in the current
page, exposes the selected role/index/name as data attributes, and emits the
`ttt:companion-audio-selection` event. It intentionally makes no upload or API
request. Connecting authenticated instructor storage and an authoring queue is
future integration work.

Also removed stale loop language from the full-page hero. No musical events,
tablature, chord claims, PDF, audio, Cloudflare, Access, DNS, deployment,
Teachable authorization, analytics, RAG, or model behavior changed.

## Lane classification

- Primary lane: 06 UX/UI Design
- Supporting lane: 18 Product / Architecture for the instructor file-selection
  contract
- Mode: YELLOW, explicitly authorized by the user

## Files changed

- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/content/related-lessons.json`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/templates/embed.html`
- `partner_companions/travis_howdy/templates/full.html`
- `tests/test_travis_companion.py`
- this handoff

Generated and intentionally uncommitted:

- `tmp/howdy-owner-review-2026-08-17.5/`
- `tmp/howdy-owner-review-2026-08-17.6/`
- `tmp/howdy-owner-review-2026-08-17.release-manifest.json`
- existing `output/pdf/Howdy-music-first-review-v7.pdf`

## Tests and checks run

- `node --check partner_companions/travis_howdy/site/companion.js` — passed.
- `.venv/bin/ruff check partner_companions/travis_howdy/release.py tests/test_travis_companion.py` — passed.
- `.venv/bin/pytest -q tests/test_practice_analysis_v2.py tests/test_practice_reference_validation.py tests/test_travis_companion.py tests/test_travis_practice_guide.py tests/test_ttt_concept_graph.py tests/test_play_songs_ui.py tests/test_practice_tools.py` — 77 passed.
- `git diff --check` — passed.
- deterministic bundle verifier — passed with 18 allowlisted files,
  same-origin-only networking, and blocked general-app/RAG routes.
- in-app browser upload smoke — passed with one primary MP3, two additional
  MP3s, multiple-file selection, generated radios, and deterministic selection
  of `additional:1`.
- in-app browser related-video smoke — the same three titles remained before
  and after a phrase change plus audio playback, and remained visible in both
  taught-solo and full-song views.
- in-app browser NNS smoke — scrolling labels changed from
  `N.C., D, A, D, G, A` to `N.C., I, V, I, IV, V` while the canonical chart
  events stayed unchanged.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/practice-guide/howdy/`
- Cache-busted URL tested: `http://127.0.0.1:8897/practice-guide/howdy/?build=audio-nns-static-2`
- Exact URL the user should use: the same local route with the final feature
  commit hash as its `build` query
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: `8897`
- Expected git HEAD: the feature commit containing this handoff; repackage the
  ignored bundle after commit so the visible marker matches it
- Version endpoint: none
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: visible companion
  revision and build SHA marker
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes; it redirects to `/howdy`
- Whether `/ui/steel-guitar-rag-mock.html` works: no
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no
- Who should test this URL: Codex and the user
- Do not test these URLs: external preview, Cloudflare, Access, DNS, Teachable
  production iframe, or previous ignored bundle directories
- Known caveats: the instructor form is a local static interaction contract;
  no audio is transmitted or stored

## Integration notes

- Future instructor upload handling should consume multipart fields named
  `primaryTrack`, `additionalTracks`, and `analysisTrack`.
- `analysisTrack` values use `primary:0` or `additional:<zero-based-index>`.
- The DOM also publishes `data-selected-track-role`,
  `data-selected-track-index`, and `data-selected-track-name` on the setup
  section and emits `ttt:companion-audio-selection` after every selection.
- Release validation requires one to three static featured related lessons and
  a concise lesson-level `companionReason`; phrase-level evidence remains in
  the authoring data but no longer drives runtime card replacement.
- NNS mode is purely presentational and does not mutate companion JSON.

## Risk assessment

Low for the local deterministic preview. Rollback is the single feature commit.

- The upload form does not yet persist or transmit files. It must remain labeled
  preview-only until authenticated instructor storage is implemented.
- Instructor controls must not be exposed to ordinary learners in the final
  Teachable integration.
- The NNS preference resets to Chords on page reload.
- The selected three related lessons remain owner-review editorial choices.

## Human decision needed

Yes, before production integration: decide where authenticated instructor audio
is stored, who may submit it, retention/deletion policy, and how a submission
enters the offline authoring queue. No decision is needed to continue local
owner smoke.

## Safe-to-stage exact file list

```text
partner_companions/travis_howdy/README.md
partner_companions/travis_howdy/content/related-lessons.json
partner_companions/travis_howdy/release.py
partner_companions/travis_howdy/site/companion.css
partner_companions/travis_howdy/site/companion.js
partner_companions/travis_howdy/templates/companion.fragment.html
partner_companions/travis_howdy/templates/embed.html
partner_companions/travis_howdy/templates/full.html
tests/test_travis_companion.py
docs/handoffs/task-completions/2026-08-17-0828-06-howdy-audio-static-related-nns.md
```

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user
  change; do not overwrite or stage)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `/Users/cory/.steel-rag/`
- all private audio, transcript, comments, screenshots, rights, approval, and
  musical-reference inputs

## Recommended next lane

Lane 15 for continued owner smoke. Future production upload integration should
begin in Lane 18 for the authenticated storage/retention contract, then Lane 11
for security review before implementation.

## Commit readiness

Safe to commit.

## Suggested next step

Lane 15: continue local owner smoke at the cache-busted Howdy URL. Do not start
upload-service, auth, storage, or Teachable production work without a separately
approved contract.
