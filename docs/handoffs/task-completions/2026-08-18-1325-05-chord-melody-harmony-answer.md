# Chord Melody And Harmony Teacher Answer

Date: 2026-08-18 13:25 America/Chicago
Lane: 05 Backend / RAG Integration, with Lane 15 QA and Lane 01 exact-path commit
Commit: `1158df2d backend: teach melody harmony over chords`

## Task summary

- Requested: repair the refusal shown for the long question about mixing melody, harmony, and chords on pedal steel, and produce an answer that is more useful than the supplied Google result.
- Completed: added a narrow teacher-first matcher and deterministic answer for chord/melody/harmony questions. The answer explains top-voice thinking, the division of work across the right hand, bar, pedals, and levers, practical harmony rules, a pitch-checked standard-E9 G-to-C common-tone example at fret 3, and a five-minute drill.
- The exact supplied prompt and natural shorter variants are source-free teaching questions. They do not call the canonical frontier or legacy retrieval, do not emit source cards or warnings, and do not attach a fretboard to this broad conceptual question.
- Intentionally not changed: corpus, embeddings, Chroma/vector indexes, source-inbox material, private profile data, UI code, auth, deployment configuration, DNS, Cloudflare policy, or the protected-preview runtime.

## Root cause

The classifier treated this stable steel-guitar mechanics question as `unknown` and source-backed. With the canonical frontier enabled, that sent the question to the external verified-source path, where an evidence gate could refuse it. The local curated layer also had no matching teacher answer.

The repair recognizes the chord-plus-melody/harmony teaching family before retrieval and returns a locally verified `fretboard_concept` answer. It remains nonvisual because the question asks for principles rather than a position map.

## Files changed and committed

- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_canonical_frontier_client.py`

Created after the implementation commit:

- `docs/handoffs/task-completions/2026-08-18-1325-05-chord-melody-harmony-answer.md`

Deleted files: none.

## Tests and checks

- Focused new regressions:
  - `.venv/bin/python -m pytest -q tests/test_answer_intent_classifier.py::test_chord_melody_harmony_question_uses_source_free_teacher_route tests/test_canonical_frontier_client.py::test_chord_melody_harmony_content_leads_without_frontier_or_legacy_retrieval`
  - Result: `2 passed`.
- Routing, frontier, answer-eval, and API-contract suite:
  - `.venv/bin/python -m pytest -q tests/test_answer_intent_classifier.py tests/test_canonical_frontier_client.py tests/test_answer_eval.py tests/test_api_contract.py`
  - Result: `153 passed`.
- Full repository suite:
  - `.venv/bin/python -m pytest -q`
  - Result: `1724 passed` in 87.08 seconds.
- `git diff --check`: passed before exact-path staging.
- `git diff --cached --check`: passed.
- Exact staged paths were reviewed before commit; no unrelated paths were staged.

## Browser smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8899/ui/steel-guitar-rag-mock.html?access=beta_user&v=chord-harmony-local`
- Cache-busted URL tested: same as above
- Exact URL the user should use: none until a reviewed protected release includes `1158df2d`
- Auth required: no
- Auth provider: local scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8899`
- Expected backend port: `8899`
- Expected git HEAD: `1158df2d`
- Version endpoint: not required for the disposable local server; version was established from the exact working tree and commit
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: exact local repository HEAD plus the route trace from the disposable server
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: yes; the same-origin server maps it to the main UI
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: do not treat current protected or production answers as containing this commit until release selection and restart are complete
- Known caveats: the in-app browser screenshot encoder tiled the captured viewport; live DOM, visible text inspection, response trace, and console inspection were clean

Browser result: PASS locally.

- Exact long prompt returned HTTP 200.
- Route trace: `classification=steel_guitar:practice_plan`, `route=deterministic`, `retrieval=not_needed`, `evidence=curated_rules`, `synthesis=curated_practical_answer`.
- The answer visibly rendered as paragraphs and bullet lists.
- No `[object Object]`, raw JSON, raw forum fragment, or weak-source refusal appeared.
- Payload had `sources=[]`, `warnings=[]`, and no fretboard.
- Browser console warnings/errors: none.
- The disposable server was stopped after smoke.

## Integration notes

- Public `/api/answer` response shape is unchanged.
- No schema, corpus, retrieval ranking, embedding, or UI contract changed.
- The matcher requires chord language, melody/harmony language, and practical pedal-steel/right-hand/over-a-chord context, keeping the new route narrow.
- The standard-E9 example is pitch-checked: fret 3 strings 4-5-6 are G-D-B with no pedals and G-E-C with A+B, preserving G as the top common tone across G-to-C.

## Risk assessment

- Risk: low for the committed code. The route is narrowly matched, source-free, contract-checked, and covered with canonical-frontier-enabled regression testing.
- Rollback: revert commit `1158df2d`.
- Deployment risk remains separate: this branch contains unrelated commits ahead of the protected release, so restarting the protected runtime from the branch would broaden the deployment beyond this fix.

## Human decision needed

Yes, for deployment only: select or approve a reviewed protected release that contains `1158df2d` without unintentionally promoting the branch's unrelated ahead-of-release commits. No further product decision is needed for the answer repair itself.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-18-1325-05-chord-melody-harmony-answer.md`

The four implementation/test files are already committed in `1158df2d`.

## Files that must not be staged

- Pre-existing dirty `docs/handoffs/task-completions/integration-status.md` unless its full combined diff is reviewed separately
- Pre-existing untracked handoffs from 2026-08-04, 2026-08-12, and 2026-08-13
- `output/`
- Corpus, Chroma/vector, embedding, source-inbox, private-source, auth, deployment, and generated artifact paths

## Recommended next lane

Lane 12 Self-Hosted Deployment after reviewed release selection.

Suggested next step: build or select a protected release containing `1158df2d`, verify `/api/version`, restart only through the documented private-preview mechanism, and browser-smoke the exact long prompt at the cache-busted protected Q&A URL.

## Commit readiness

Safe to commit for this handoff only. The implementation is already committed as `1158df2d`.
