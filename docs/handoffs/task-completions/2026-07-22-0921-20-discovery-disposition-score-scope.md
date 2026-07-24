# Lane 20 Discovery Disposition and Score Scope

## Task summary

Separated complete discovery disposition from complete printed-score audit for canonical challenger readiness. This resolves the final discovery blocker without asserting that the single main-cohort tablature-only approval also approved its printed score. Tablature-only records remain restricted to `alignment:tab_only` movement/style evidence and cannot supervise score-to-tab mapping.

The aggregate readiness check now passes with zero undispositioned discovery pages, exact 16/6/10 preference accounting, current rights/copedents, and held-out data still closed. Main reports one tablature-only approval and `scoreAuditComplete=false`; licks reports `scoreAuditComplete=true`.

Intentionally not changed: raw/private evidence, source facts, review decisions, model promotion, validation data, sealed-test data, runtime behavior, embeddings, auth, and deployment.

## Files changed

- `steel_guitar_rag/amazing_tablature_training.py`
- `tests/test_amazing_tablature_training.py`
- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-22-0921-20-discovery-disposition-score-scope.md`

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py tests/test_amazing_tablature_sealed_test.py` — 35 passed.
- Real private `canonical-readiness --base-model-id at-f1adc00edf1b27db` — ready, zero blockers, 0 remaining, preferences 16 reviewed / 6 training / 10 co-valid, validation unopened, sealed test unopened.
- `.venv/bin/python -m pytest -q` — 1,338 passed in 61.06 seconds.

## Integration notes

`discoveryDispositionComplete` is the canonical training gate. `scoreAuditComplete` and `tabOnlyApprovedPageCount` preserve the narrower factual scope. Seed/model artifacts also pin `fullDiscoveryScoreAuditComplete`; this program will truthfully report false until every retained score-bearing approval has score scope. Structured score-input evaluation may use only score-supported validation records, while tab-only evidence remains a separately reported cohort.

## Risk assessment

Medium-low. The change relaxes no mechanical or pitch rule and grants no new factual approval. Its risk is semantic misuse of tab-only evidence; that is mitigated by existing support-mode filtering plus the newly explicit lineage fields and cohort reporting.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_training.py`
- `tests/test_amazing_tablature_training.py`
- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-22-0921-20-discovery-disposition-score-scope.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Unrelated historical handoffs
- `corpus-private/` and all private model/evidence artifacts

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit.

## Suggested next step

Run the full suite, exact-path commit, rebuild the canonical discovery challenger from the clean HEAD, shadow-test lineage/no-rereview accounting, then open validation only.
