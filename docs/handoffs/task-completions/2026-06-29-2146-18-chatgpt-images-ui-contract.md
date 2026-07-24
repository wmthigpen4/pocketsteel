# 2026-06-29 21:46 - Lane 18 ChatGPT Images UI Contract

## Pass / Warn / Fail

Warn.

The docs-only contract was created successfully, but the repo already had substantial unrelated dirty and untracked work before this task. No staging or commit was performed.

## Task Summary

Requested:
- Create a design-implementation contract for turning ChatGPT Images mockups into Codex-buildable UI for the Steel Guitar RAG / Steel Guitar RAG frontend.
- Cover mockup interpretation, design tokens, component chunks, asset handling, responsive behavior, browser screenshot smoke, and acceptance criteria.
- Inspect existing UI/docs and avoid runtime UI implementation.

Completed:
- Created a stable product/architecture contract at `docs/chatgpt-images-ui-implementation-contract.md`.
- Defined a repeatable workflow for converting visual mockups into specs, chunks, smoke checks, and handoffs.
- Included guidance for asset export versus CSS/SVG recreation.
- Included Lane 06 and Lane 19 prompt templates for future implementation and asset preparation.

Intentionally not changed:
- No runtime UI files.
- No app code.
- No tests.
- No assets.
- No deployment, auth, DNS, corpus, scraper, embeddings, Chroma/vector stores, private materials, or integration-status refresh.

## Repo State

- Branch: `feature/answer-api`
- Starting HEAD: `697435e`
- Final HEAD: `697435e`
- Commit hash: not committed
- Task type: docs-only
- Lane: `18 Product / Architecture`
- Task mode: GREEN

## Files Changed

Created:
- `docs/chatgpt-images-ui-implementation-contract.md`
- `docs/handoffs/task-completions/2026-06-29-2146-18-chatgpt-images-ui-contract.md`

Changed:
- None

Deleted:
- None

Generated artifacts:
- None

## Key Product Decisions

- ChatGPT Images mockups are visual briefs, not pixel-perfect specs by default.
- Implementation source of truth remains HTML, CSS, SVG, JavaScript, and existing data contracts.
- The SVG fretboard/grid remains the source of truth for strings, frets, hit targets, and musical geometry.
- Decorative images can provide mood but must not encode functional UI state or fretboard coordinates.
- Text, controls, diagrams, fretboard marks, source cards, tab cards, and dynamic states should be recreated in accessible HTML/CSS/SVG, not baked into images.
- Raster assets should be exported directly only when they are the visual subject/material, such as generated hero imagery, photography, brand-sign media, stage texture, or complex decorative foregrounds.
- Mockup-driven UI work should be implemented in chunks: shell/tokens, primary stage, controls, cards/inspectors, assets, responsive pass, and screenshot smoke.
- Browser smoke for mockup-derived UI must include screenshot evidence and manual comparison against the reference, not just DOM assertions.

## Tests And Checks

Required for this docs-only task:
- `git status --short`
- `git diff --check`
- `git diff --check -- docs/chatgpt-images-ui-implementation-contract.md docs/handoffs/task-completions/2026-06-29-2146-18-chatgpt-images-ui-contract.md`
- `git diff --cached --name-only`
- `git diff --cached --check`

Results:
- `git status --short`: run before editing; showed broad unrelated dirty/untracked files already present.
- `git diff --check`: passed.
- `git diff --check -- docs/chatgpt-images-ui-implementation-contract.md docs/handoffs/task-completions/2026-06-29-2146-18-chatgpt-images-ui-contract.md`: passed.
- `git status --short -- docs/chatgpt-images-ui-implementation-contract.md docs/handoffs/task-completions/2026-06-29-2146-18-chatgpt-images-ui-contract.md`: showed only the two new docs as untracked.
- `git diff --cached --name-only`: no staged files.
- `git diff --cached --check`: passed; no staged diff.

Tests skipped:
- Frontend/browser tests skipped because this task did not change runtime UI.
- Pytest skipped because this task was docs-only.
- Browser smoke skipped because this task did not implement visible UI.

## Integration Notes

Future Lane 06 UI slices should use `docs/chatgpt-images-ui-implementation-contract.md` before implementing from ChatGPT Images mockups.

Future Lane 19 asset slices should be used when a mockup requires new or edited raster/video assets. Lane 06 should not modify protected or raw asset directories unless the task explicitly authorizes those paths.

No integration-status refresh was performed because this contract did not change runtime behavior, test status, protected-preview state, or committed integration state.

## Risks

Risk: low for runtime, medium for git hygiene.

Why:
- The change is docs-only and does not alter app behavior.
- The worktree contains many unrelated dirty and untracked files, including protected categories such as corpus/source and visual asset paths. Exact-path staging is required if this is later committed.

Rollback:
- Delete `docs/chatgpt-images-ui-implementation-contract.md`.
- Delete this handoff.

## Blockers

None for the contract.

## Human Decision Needed

No for this docs-only contract.

Potential future decisions:
- Whether future mockup implementation should target the landing page, Explorer, answer UI, or a new shared visual system first.
- Whether pixel-perfect matching is required for any specific mockup. The contract defaults to visual-direction matching, not pixel-perfect matching.

## Safe-To-Stage Exact File List

- `docs/chatgpt-images-ui-implementation-contract.md`
- `docs/handoffs/task-completions/2026-06-29-2146-18-chatgpt-images-ui-contract.md`

## Files That Must Not Be Staged

Do not stage unrelated existing dirty or untracked files, including:
- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `Neon Sign/`
- `answer_private_lessons.py`
- `config/`
- `data/`
- `deploy/landing/brand/`
- Existing unrelated untracked docs, handoffs, generated reports, assets, corpus/source files, private data, Chroma/vector stores, embeddings, deployment/auth files, and raw design assets.

## Recommended Next Lane

Lane 06 UX/UI Design.

## Next Recommended Lane 06 Prompt

```text
Lane 06 UX/UI Design

Use docs/chatgpt-images-ui-implementation-contract.md and the attached ChatGPT Images mockup(s) to implement a scoped UI slice for <target route/component>.

Before coding:
- Inspect AGENTS.md, docs/handoffs/task-completions/integration-status.md, the target UI file(s), relevant tests, and the latest related handoff.
- Convert the mockup into a short implementation spec covering hierarchy, design tokens, component chunks, asset decisions, responsive behavior, and acceptance criteria.
- Do not touch backend, auth, deployment, corpus, Chroma/vector stores, scraping, embeddings, private materials, or unrelated assets.

Implement only <exact target files/UI area>.

Run:
- syntax checks for touched JS
- focused frontend/static tests
- git diff --check
- local browser screenshot smoke at desktop and mobile viewports

Write a handoff with screenshot paths, visual comparison notes, risks, safe-to-stage files, files that must remain unstaged, and the next lane. If committed and preview-bound, route to Lane 12 for protected-preview browser smoke with a direct cache-busted URL.
```

## Commit Readiness

Needs human review first.

Reason:
- The docs are safe to review, but the user did not explicitly request a commit.
- Exact-path staging is required due the broad unrelated dirty worktree.

## Suggested Next Step

Review the contract, then run a Lane 06 implementation slice against one specific mockup and one target route.
