# Answer-Triggered Tab Architecture Review

## Task Summary

- What was requested: review and finalize the product architecture for answer-triggered deterministic tab examples without implementing code or touching UI files.
- What was completed: reviewed the existing primary architecture handoff at `docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md` against the required criteria, relevant commits, and nearby Lane 05/06/15 handoffs. This review found the architecture is directionally complete and should not be duplicated.
- What was intentionally not changed: no backend code, frontend code, UI files, tests, `/api/answer`, `/api/tab/render`, Chroma/vector stores, embeddings, corpus/source data, auth, deployment, staging of unrelated files, or commits were changed by this Lane 18 review.

## Files Reviewed

- `AGENTS.md`
- `docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md`
- `docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples-implementation-plan.md`
- `docs/handoffs/task-completions/2026-06-18-06-answer-triggered-tab-example-ux-followup.md`
- `docs/handoffs/task-completions/2026-06-18-15-tab-engine-ui-qa.md`

Relevant commits checked:

- `686fd3c feat: add deterministic tab engine slice`
- `54a28c7 fix: clear tab examples on stage return`
- `7834c67 docs: plan tab engine follow-on slices`

## Review Criteria

| Criterion | Review result | Notes |
| --- | --- | --- |
| Deterministic tab examples only | Pass | Architecture requires registry-backed examples, structured events, and validation before attach. |
| No LLM-only tab generation | Pass | Explicitly forbids LLM/RAG-generated events and SGF-created events. |
| No full copyrighted song tab generation | Pass | Blocks full song tab, named modern arrangements, whole solos, artist recreations, and arbitrary recording extraction. |
| Safe intent routing | Pass | Defines safe categories, unsafe categories, narrow allowlist, and feature flag default-off behavior. |
| Validated tab payload before display | Pass | Requires `tab_engine` renderer/validator and says invalid normal-answer tab examples should not attach. |
| Backward-compatible API shape | Pass | Defines optional `tab_example` addition and notes answer contract tests must allow it like `fretboard`. |
| UI optional tab card behavior | Pass | Primary handoff defines tab as supporting content; Lane 06 follow-up defines optional compact card behavior and no empty tab shell. |
| Future SVG event sync path | Minor gap | Architecture names v5 sync and event ids, but should add a future payload shape for `fretboardSync` before implementation reaches SVG sync. |
| Future user-copedent profile path | Minor gap | Architecture requires `profile=default_e9` and revalidation later, but should add explicit future profile status values before user-copedent rollout. |

## Gaps Found

No blocking gaps were found for the current Lane 05 answer-triggered deterministic tab example slice.

Two minor future-contract gaps should be preserved for later lanes:

1. SVG event sync needs a concrete payload addition before Lane 06/05 implement event-linked fretboard highlighting.
2. User-copedent support needs an explicit profile-status contract before any saved user setup affects generated tab.

These are not blockers for v1 fixed deterministic examples.

## Final Architecture Clarifications

### SVG Sync Future Contract

Before implementing SVG event sync, add an optional payload block like:

```json
{
  "fretboardSync": {
    "mode": "tab-events",
    "selectedEventId": "g-to-c-1",
    "eventPositionMap": {
      "g-to-c-1": {
        "strings": [4, 5, 6],
        "fret": 3,
        "pedals": [],
        "levers": [],
        "positionId": "g-open-3"
      }
    }
  }
}
```

Rules:

- Backend sends event ids, string numbers, fret numbers, pedals/levers, and optional position ids.
- UI owns geometry, marker placement, animation, selected state, and decorative image behavior.
- No backend raw x/y coordinates.
- Sync is optional; tab cards must work without fretboard sync.

### User-Copedent Future Contract

Before user-copedent-backed tab generation, add explicit profile status values:

- `default_e9`
- `assumed_default_e9`
- `user_profile_e9`
- `unsupported_user_profile`
- `profile_required`

Rules:

- v1 fixed examples should use `default_e9` or `assumed_default_e9`.
- Saved user profile support must revalidate every event against that profile before display.
- If the user profile lacks a required control, omit the tab example or return a clear caveat in the answer rather than showing invalid tab.
- Do not silently adapt private/profile-backed data into public answers without auth/profile controls.

## Final Product Decision

The primary architecture handoff is accepted for v1 with the two future clarifications above.

Lane 05 can proceed with a feature-flagged, deterministic registry-backed `tabExample`/`tab_example` attachment as long as:

- examples come from structured events,
- rendered tab comes from `pocketsteel.tab_engine`,
- invalid events are omitted from normal answers,
- unsafe/copyrighted categories do not attach tab,
- the response shape is optional and backward-compatible,
- UI files remain untouched in the backend slice.

Field-name note:

- The primary Lane 18 architecture used snake_case `tab_example`.
- The Lane 05 implementation plan recommends camelCase `tabExample`.
- Backend and UI lanes should choose one canonical public response field before final implementation. If current API conventions favor camelCase for new frontend-facing fields, use `tabExample`; otherwise document the exception and test it.

## Recommended Next Engineering Slices

1. Lane 05: finish the feature-flagged deterministic registry implementation behind default-off `ENABLE_ANSWER_TAB_EXAMPLES`.
2. Lane 15: verify the implementation against safe/unsafe routing, copyright refusals, feature flag off behavior, and schema compatibility.
3. Lane 06: verify optional compact tab card rendering against the final field name and payload shape.
4. Later Lane 18/06/05: define and implement `fretboardSync` only after v1 tab cards are stable.
5. Later Lane 11/05: define saved user-copedent authorization/profile contract before profile-backed generated tab.

## Files Changed

- Created:
  - `docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md`
- Changed:
  - None
- Deleted:
  - None
- Generated artifacts:
  - None

## Tests And Checks

Commands run:

- `sed -n '1,520p' AGENTS.md`
  - Passed. Read repo protocol and workflow rules.
- `git status --short`
  - Passed before editing. Worktree had broad unrelated dirty files, including active Lane 05 backend files and Lane 06 UI files.
- `git show --stat --oneline 686fd3c 54a28c7 7834c67 --`
  - Passed. Confirmed relevant commit context.
- `test -f docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md; printf 'architecture=%s\n' $?; test -f docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md; printf 'review=%s\n' $?`
  - Passed. Architecture existed; review did not exist.
- `sed -n '1,260p' docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md`
  - Passed. Reviewed primary architecture handoff.
- `sed -n '260,620p' docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md`
  - Passed. Reviewed primary architecture handoff.
- `rg --files docs/handoffs/task-completions | rg 'answer-triggered-tab|tab-engine|tab-card'`
  - Passed. Found related current handoffs and the actual Lane 05 implementation plan filename.
- `sed -n '1,260p' docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples-implementation-plan.md`
  - Passed. Reviewed Lane 05 implementation plan context.
- `sed -n '1,220p' docs/handoffs/task-completions/2026-06-18-06-answer-triggered-tab-example-ux-followup.md`
  - Passed. Reviewed Lane 06 UI behavior context.
- `sed -n '1,220p' docs/handoffs/task-completions/2026-06-18-15-tab-engine-ui-qa.md`
  - Passed. Reviewed Lane 15 QA context.

- `git status --short`
  - Passed after editing. Broad unrelated dirty worktree remains; this task created only this review handoff.
- `git diff --check`
  - Passed.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md`
  - Passed. Used because this handoff is new and untracked, so normal `git diff --check` does not inspect its contents.
- `git status --short -- docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md`
  - Passed. Shows `?? docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md` before staging.
- `git diff --cached --name-only`
  - Passed before staging. No staged files were present.
- `git diff --cached --check`
  - Passed before staging.

- `git diff --check`
  - Passed after final handoff update.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md`
  - Passed after final handoff update.
- `git add docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md`
  - Passed. Used exact-path staging for this review handoff only.
- `git diff --cached --name-only`
  - Mixed staged state after staging: included this review handoff plus `docs/handoffs/task-completions/2026-06-18-12-answer-triggered-tab-examples-smoke.md`.
- `git diff --cached --check`
  - Passed.

Staging note:

- This task staged only `docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md`.
- The cached diff also contains `docs/handoffs/task-completions/2026-06-18-12-answer-triggered-tab-examples-smoke.md`, which is outside this Lane 18 task and was not modified by this review.
- No commit was made because the cached diff is not limited to this task's handoff and the broader worktree is dirty.

Skipped tests:

- Unit, API, browser, and eval tests were skipped because this was a docs-only architecture review with no executable behavior changed.

## Risk Assessment

Risk level: low.

Why:

- This review is docs-only.
- No runtime code, UI files, tests, deployment, corpus, Chroma/vector stores, source data, or auth files were modified.
- The review narrows future implementation rather than expanding scope.

Rollback notes:

- Remove this review handoff if the architecture review is superseded.

## Human Decision Needed

No for v1.

Future decisions:

- Choose the canonical public field name: `tabExample` or `tab_example`.
- Decide when saved user-copedent profile data may influence generated tab.
- Decide when SVG tab-event sync is ready to move from contract to implementation.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md`

## Files That Must Not Be Staged

- Any pre-existing dirty files outside the safe-to-stage path above.
- `pocketsteel/api.py`
- `pocketsteel/api_contract.py`
- `pocketsteel/answer_tab_examples.py`
- `tests/test_api_contract.py`
- `tests/test_tab_engine.py`
- `ui/steel-guitar-rag-mock.html`
- `ui/answer-client.js`
- `tests/test_frontend_answer_ui.py`
- App code, backend implementation files, frontend files, tests, deployment files, auth files, Chroma/vector data, embeddings, corpus-private, source-inbox data, generated reports, raw design assets, and secrets.

## Commit Readiness

Not ready to commit

Reason:

- The review handoff itself is safe to commit.
- The current cached diff is not limited to this review handoff because another Lane 12 smoke handoff is also staged.
- No commit should be made from this Lane 18 task while unrelated staged/dirty work is present.

## Recommended Next Lane

Recommended lane: `15 QA / Answer Eval`.

Suggested next step:

```text
Lane 15: Review the in-progress answer-triggered tab implementation against docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md and docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md. Verify deterministic-only tab events, no LLM-generated tab, copyright blocking, feature flag off behavior, validated payloads only, and backward-compatible optional tab response shape.
```
