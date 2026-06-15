# Curated Guidance Routing Design QA

## Task Summary

- What was requested: run `Lane15DesignReview` for `docs/handoffs/task-completions/curated-guidance-routing-design.md` before Lane 05 implements curated-guidance routing.
- What was completed: reviewed `AGENTS.md`, the curated-guidance routing design, and the relevant design sections for private/public separation, feature flags, source-card labeling, excerpt limits, full-body exposure, and implementation slice size.
- What was intentionally not changed: no implementation files, tests, `/api/answer`, UI, SGF retrieval, Chroma/vector stores, embeddings, corpus-private files, auth, DNS, deployment, staging, or commits were touched.

## Pass/Fail Decision

Pass.

The design is ready for a small Lane 05 implementation plan/slice, with the constraints below preserved exactly.

## Required Confirmations

| Requirement | QA result | Notes |
| --- | --- | --- |
| Private-review guidance stays separated from public SGF evidence | Pass | Design explicitly separates SGF evidence and private teaching guidance in routing, card grouping, labels, and hybrid behavior. |
| Public users cannot receive private-review guidance | Pass | Public and anonymous users are explicitly forbidden from receiving curated guidance, private excerpts, filenames, paths, raw visibility labels, or `private_review` metadata. |
| Feature flags fail closed | Pass | Design requires multiple default-off flags before curated guidance can participate: private-review umbrella, retriever, answer integration, source cards, and hybrid mode where applicable. |
| Source-card labels are clear | Pass | Recommended labels are "Private teaching guidance" and "Curated guidance note"; raw `private_review`, `content_layer`, local paths, and filenames are forbidden in normal UI. |
| Excerpts stay capped | Pass | Backend cap remains 500 characters; user-facing card target is 240-320 characters; admin/backstage expanded excerpt remains capped at 500. |
| Full private bodies are never rendered | Pass | Design repeatedly forbids full bodies in `/api/answer`, answer body, source cards, JSON response, and normal UI. |
| First Lane 05 slice is small and protected-preview only | Pass with clarification | The design's Slice 1 is classifier-only and changes no answer behavior. The first runtime answer-integration slice is explicitly admin/backstage protected-preview only, default off, and no public route behavior change. |

## Design Review Notes

- Curated guidance is positioned as a private-review teaching aid, not a public evidence layer.
- The design correctly forbids using curated guidance as a generic weak-SGF fallback. It must be intent-routed.
- The first runtime integration should retrieve curated guidance only after guardrails, deterministic routing, auth, role, feature-flag, corpus-existence, and quality checks pass.
- Hybrid mode is correctly deferred behind its own flag and requires separate SGF and private teaching guidance labeling.
- The design correctly keeps deterministic fretboard/pitch logic authoritative for visualizable chord/position questions.
- The QA plan includes the right regression buckets for public leaks, full-body leaks, path/filename leaks, wrong intent, missing corpus fallback, confusing labels, hybrid blending, and over-cap excerpts.

## Lane 05 Implementation Boundaries

Approved design direction for Lane 05:

- Start with the classifier-only eligibility slice or the protected-preview answer-orchestration slice, but keep runtime behavior protected-preview/admin-backstage only.
- Keep all flags default off.
- Do not change public/anonymous behavior.
- Do not wire curated guidance into SGF retrieval or Chroma.
- Do not return full bodies.
- Do not expose filenames, local paths, raw `private_review`, or raw `content_layer` in public or ordinary beta UI.
- Do not add curated guidance source cards unless the dedicated source-card flag and auth/role gates pass.

Not approved by this QA review:

- Public production promotion.
- Anonymous/public curated-guidance answers.
- Broad beta exposure.
- Hybrid SGF + curated guidance without a dedicated flag and separate card labeling.
- Any full-body or local-path rendering.
- Any `/api/answer` integration that does not fail closed.

## Files Changed

- Created:
  - `docs/handoffs/task-completions/curated-guidance-routing-design-qa.md`
- Reviewed:
  - `AGENTS.md`
  - `docs/handoffs/task-completions/curated-guidance-routing-design.md`
- Deleted:
  - None
- Generated artifacts:
  - None

## Tests And Checks

Commands run:

- `sed -n '1,260p' AGENTS.md`
  - Passed. Reviewed lane/workflow rules and `Lane15DesignReview` constraints.
- `sed -n '1,260p' docs/handoffs/task-completions/curated-guidance-routing-design.md`
  - Passed. Reviewed executive recommendation, current state, use/avoid criteria, routing matrix, auth/private-review policy, and source-card label policy.
- `sed -n '260,620p' docs/handoffs/task-completions/curated-guidance-routing-design.md`
  - Passed. Reviewed excerpt/full-body policy, feature flags, answer-engine interaction, Lane 05 slices, Lane 15 QA plan, risks, and non-goals.
- `sed -n '620,740p' docs/handoffs/task-completions/curated-guidance-routing-design.md`
  - Passed. Reviewed design handoff checks, integration notes, and next-lane recommendation.
- `rg -n "feature|flag|public|private|source|excerpt|full|body|Lane 05|slice|protected|SGF|Chroma|auth|label" docs/handoffs/task-completions/curated-guidance-routing-design.md`
  - Passed. Verified the requested safety and design topics are explicitly covered.
- `git status --short`
  - Passed. Broad pre-existing dirty worktree remains; this QA task only created this handoff.
- `git diff --check`
  - Passed.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/curated-guidance-routing-design-qa.md`
  - Passed with expected exit code `1` for a new untracked file diff and no whitespace-error output.
- `git status --short -- docs/handoffs/task-completions/curated-guidance-routing-design-qa.md`
  - Passed. Shows this QA handoff as untracked.
- `git status --short -- docs/handoffs/task-completions/curated-guidance-routing-design.md docs/handoffs/task-completions/curated-guidance-routing-design-qa.md`
  - Passed. Shows both the design handoff and this QA handoff as untracked in this task scope.

Skipped tests:

- Pytest, API, browser, and UI tests were skipped because this was a docs-only design review with no executable behavior changed.

## Integration Notes

- Lane 05 may implement the next slice only within the design's fail-closed constraints.
- Any first runtime behavior must be protected-preview/admin-backstage only and default off.
- Lane 15 should review the implementation before Repo Steward commit if `/api/answer` orchestration or source cards are touched.
- Lane 12 protected-preview smoke is not needed for this docs-only design review.

## Risk Assessment

Risk level: low for the design handoff; medium for later implementation.

Why:

- The design itself is docs-only and strongly preserves private/public separation.
- Later implementation can become risky if feature flags, auth gates, source-card labels, or full-body caps are weakened.

Rollback notes:

- Revert this QA handoff only if the design review needs to be replaced.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/curated-guidance-routing-design.md`
- `docs/handoffs/task-completions/curated-guidance-routing-design-qa.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files outside the two safe-to-stage paths above.
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/` raw data or provenance
- `.wrangler/`
- DNS/deployment secrets
- `public/`
- `ui/brand/`
- `Neon Sign/`
- generated reports or raw design assets

## Commit Readiness

Safe to commit.

## Recommended Next Lane

Recommended lane: `05 Backend / RAG Integration`.

Suggested next prompt:

```text
Lane 05: Implement only the first curated_guidance routing slice from docs/handoffs/task-completions/curated-guidance-routing-design.md and docs/handoffs/task-completions/curated-guidance-routing-design-qa.md. Keep all curated-guidance runtime behavior default-off, fail-closed, and protected-preview/admin-backstage only. Do not expose private guidance to public users, do not return full bodies, do not merge private guidance with SGF cards, and do not touch Chroma, SGF retrieval, UI, auth, DNS, deployment, or corpus-private outputs beyond read-only access explicitly required by the existing retriever.
```
