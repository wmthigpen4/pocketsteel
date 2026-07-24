# Lane 15 - Steel Guitar Rag Curated QA

## Task Summary

Lane: 15 QA / Answer Eval

Requested: run song-specific QA for the newly added Steel Guitar Rag curated reference path, verifying answer quality, attribution, source cards, links/metadata, routing, tab/copyright guardrails, and non-Steel-Guitar-Rag regressions.

Completed:
- Reviewed repo guidance and the Lane 05 implementation handoff.
- Inspected the curated song-reference loader, curated resource, curated answer routing, and focused tests.
- Ran prompt-level API fallback checks through the existing `/api/answer` WSGI test helper.
- Ran the requested focused checks.
- Created this QA handoff.

Intentionally not changed:
- No curated reference content changed.
- No backend implementation changed.
- No frontend/source-card UI files changed.
- No tab generation added.
- No Chroma, embeddings, scraping, corpus-private, corpus-v2, source-inbox, auth, DNS, deployment, public/static, brand, or unrelated UI touched.

Task type: QA verification plus handoff.

Task mode: GREEN for QA/handoff.

## Commit Tested

- Branch: `feature/answer-api`
- HEAD at task start: `bb6745b add steel guitar rag curated reference`
- Current working tree has broad unrelated parked changes. They were left untouched.

## Files Inspected

- `AGENTS.md`
- `agents.md`
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-19-1053-05-steel-guitar-rag-curated-reference.md`
- `steel_guitar_rag/curated_song_references.py`
- `steel_guitar_rag/resources/curated/steel-guitar-rag-expert-reference.md`
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `tests/test_api_contract.py`

No `PLAN.md` or `plan.md` guidance file was found during the requested guidance scan.

## Prompt QA Method

Prompt checks used the existing `tests.test_api_search.answer_for_question(...)` helper. That exercises the local WSGI `/api/answer` route with deterministic answer provider and fake noisy SGF sources.

This is API fallback QA, not browser/protected-preview smoke.

## Prompt Results

| Prompt | Result | Sources | Notes |
| --- | --- | --- | --- |
| Tell me about Steel Guitar Rag. | Pass | 5 curated reference cards | Teacher-first overview; mentions Western swing, 1936 Bob Wills/Texas Playboys, Leon McAuliffe; no warnings or fretboard. |
| Who wrote Steel Guitar Rag? | Pass | 5 curated reference cards | Correctly avoids "Leon wrote it" oversimplification; mentions McAuliffe, Weaver/Guitar Rag, Cliffie Stone, Merle Travis. |
| What is the history of Steel Guitar Rag? | Pass | 5 curated reference cards | Uses curated overview, no SGF leakage. |
| Why is Steel Guitar Rag important? | Pass | 5 curated reference cards | Explains steel-guitar and Western-swing importance; no unsupported tab. |
| What are common versions or variations of Steel Guitar Rag? | Pass | 5 curated reference cards | Mentions arrangement choices, three 16-bar sections, C6/E9 adaptations, listening references. |
| Does the app know Steel Guitar Rag? | Pass | 5 curated reference cards | Routes to curated reference; does not confuse song/app identity in a harmful way. |
| Give me a source-backed overview of Steel Guitar Rag. | Pass | 5 curated reference cards | Source-backed route used; source cards present. |
| What should a steel player know about Steel Guitar Rag? | Pass | 5 curated reference cards | Gives useful high-level context; no source fragments as primary answer. |
| Give me full Steel Guitar Rag tab. | Pass | 5 curated reference cards | Refuses full note-for-note dump by default and provides short original E9 study with "not a transcription" framing. |
| Give me the whole Steel Guitar Rag arrangement. | Pass with polish note | 5 curated reference cards | Does not provide a full arrangement; returns variations/form guidance. Could be more explicit that a whole arrangement is not provided by default. |
| Transcribe a Steel Guitar Rag YouTube recording. | Pass with polish note | 5 curated reference cards | Does not transcribe, generate tab, or leak sources. It returns generic overview instead of an explicit recording-transcription guardrail. |
| Give me a short public-domain-style Steel Guitar Rag teaching example. | Pass with polish note | 5 curated reference cards | Safe output; no unsupported tab. It does not provide the short example because current tab trigger keys on tab/teach/how-to wording. |
| What are good Fender Steel King settings? | Pass | Normal non-curated source path | Did not route to Steel Guitar Rag curated reference. |
| What are common uses for the E9 9th string? | Pass | Normal non-curated source path | Did not route to Steel Guitar Rag curated reference. |
| Show me a G major grip. | Pass | Normal non-curated source path | Fretboard present; no Steel Guitar Rag curated source cards. |
| Show me a G to C move. | Pass | Normal non-curated source path | Fretboard and tab payload present; no Steel Guitar Rag curated source cards. |

## Source-Card Findings

Verdict: Pass.

Observed curated source cards:
- `Steel Guitar Rag expert reference`
- `Steel guitar rag / Texas Playboys, Brunswick matrix C1479`
- `Guy Cundell, Steel Guitar Blag`
- `Steel Guitar Rag work page`
- `Steel Guitar Rag copyright and licensing listing`

Findings:
- Source labels/titles are clear.
- `source_system` is consistently `curated_reference`.
- External links are preserved for UCSB DAHR, Cundell PDF, SecondHandSongs, and Easy Song.
- Local curated reference path is preserved as `steel_guitar_rag/resources/curated/steel-guitar-rag-expert-reference.md`.
- No broken empty source-card titles or URLs were observed in API payloads.

Frontend source-card display was not exercised, so this handoff does not prove browser rendering.

## Answer-Quality Findings

Verdict: Pass.

Findings:
- History/context answers are concise and source-backed.
- Authorship answer correctly handles the McAuliffe/Weaver/Guitar Rag nuance.
- Variations answer distinguishes arrangement choices from one fixed modern pedal-steel tab.
- Answers did not use raw SGF/forum fragments as primary text.
- Warnings were empty for all Steel Guitar Rag prompts tested.
- No fretboard payload appeared for history/context/song-reference prompts.

Polish items:
- "Transcribe a Steel Guitar Rag YouTube recording" should ideally produce an explicit guardrail stating that the app cannot transcribe arbitrary recordings, then offer a short original study or source-backed listening guidance.
- "Give me the whole Steel Guitar Rag arrangement" should ideally say it cannot provide a full arrangement by default before giving form/variation guidance.

These are not hard QA blockers because no unsafe transcription, full tab, or unsupported arrangement was generated.

## Tab / Copyright Guardrail Findings

Verdict: Pass.

Findings:
- Full-tab prompt did not return a full note-for-note transcription.
- Full-tab prompt explicitly says it should not dump a full copyrighted arrangement by default.
- Returned teaching tab is framed as a compact original Steel Guitar Rag-style E9 study and says it is not a transcription.
- Whole-arrangement and YouTube-transcription prompts did not generate tab or transcription.
- No new tab-generation route was introduced by this QA task.

Follow-up:
- Lane 05 should consider tightening transcription/whole-arrangement wording so those prompts get an explicit guardrail response instead of a generic overview or variations answer.

## Regression Findings

Verdict: Pass.

Findings:
- Fender Steel King settings did not route to Steel Guitar Rag curated reference.
- E9 9th string did not route to Steel Guitar Rag curated reference.
- G major grip retained fretboard behavior and did not route to Steel Guitar Rag curated reference.
- G to C move retained fretboard/tab behavior and did not route to Steel Guitar Rag curated reference.

Note:
- Some non-Steel-Guitar-Rag prompts returned normal fake-source cards from the existing test harness's noisy SGF source. That is existing behavior in these tests, not a Steel Guitar Rag regression.

## Defects

No hard defects found.

Non-blocking Lane 05 polish:
- Add explicit guardrail language for `Transcribe a Steel Guitar Rag YouTube recording.`
- Add explicit "not a full arrangement by default" wording for `Give me the whole Steel Guitar Rag arrangement.`
- Optionally route `short public-domain-style ... teaching example` to the existing safe short-study branch if product wants that phrase to produce a teaching example.

## Tests And Checks Run

```bash
git diff --check
# passed

.venv/bin/python -m py_compile steel_guitar_rag/curated_song_references.py steel_guitar_rag/curated_answers.py steel_guitar_rag/api.py
# passed

.venv/bin/python -m pytest tests/test_api_search.py -k 'Steel_Guitar_Rag or steel_guitar_rag' -q
# 4 passed, 259 deselected

.venv/bin/python -m pytest tests/test_api_search.py -q
# 263 passed

.venv/bin/python -m pytest tests/test_api_contract.py -q
# 5 passed
```

Additional prompt-level API fallback inspection was run with the existing `answer_for_question(...)` helper for all prompts listed above.

Skipped:
- `node --check ui/answer-client.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`

Reason: frontend/source-card UI was not exercised or changed in this QA task.

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-19-15-steel-guitar-rag-curated-qa.md`

No files deleted.

## Risk Assessment

Risk: low.

Reason:
- QA handoff only.
- Required backend/API checks passed.
- No implementation, UI, corpus, Chroma, scraping, auth, DNS, deployment, public/static, private corpus, source-inbox, brand, or generated assets changed.

Rollback:
- Revert this handoff if needed.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-19-15-steel-guitar-rag-curated-qa.md`

Do not use `git add .`.

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files, especially:
- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `deploy/landing/index.html`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `tests/test_public_landing_page.py`
- `ui/steel-guitar-rag-landing.html`
- `ui/brand/`
- `public/brand/`
- `Neon Sign/`
- `source-inbox/provenance.json`
- any `corpus-private/`, `corpus-v2/`, Chroma/vector, embedding, scraping, deployment secret, generated report, raw corpus, source-inbox raw/provenance, or design asset paths.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment.

Suggested next task:

```text
Lane 12: Run protected-preview smoke for the Steel Guitar Rag curated reference at the current committed runtime. Verify Steel Guitar Rag history/authorship/variation/tab prompts show curated source cards, no full copyrighted tab or recording transcription is generated, and non-Steel-Guitar-Rag prompts do not route to the curated reference.
```

Optional Lane 05 follow-up:

```text
Lane 05: Tighten Steel Guitar Rag guardrail wording for "whole arrangement" and "transcribe YouTube recording" prompts. Do not add full tab generation; keep curated source cards and short original-study behavior intact.
```

## Commit Readiness

Safe to commit.
