# Four-workspace architecture and Lessons v1

## Task summary

Implemented the approved four-workspace product architecture:

- `Ask` remains the source-aware Chat workspace.
- `Explore` remains the E9 Fretboard Explorer.
- `Arrange` remains Melody Studio.
- `Learn` is a new Lessons workspace.

Lessons v1 combines five reviewed paths with a custom lesson builder. Every lesson includes a goal, concept explanation, timed exercises, listening targets, common mistakes, a session-only checklist, a next step, and an exact Explorer, Melody, or Chat handoff when relevant. The UI explicitly says progress is not saved.

The Explorer chord doorway is now `Find chords and voicings`; no standalone Chord Studio was created. No broad product rename was performed.

Intentionally unchanged: corpus, retrieval ranking, Chroma/vector stores, scraping, private lesson sources, auth policy, DNS, Cloudflare configuration, secrets, Backstage persistence, saved progress, and brand assets.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lanes: `18 Product / Architecture`, `05 Backend / RAG Integration`, `15 QA / Answer Eval`, `01 Repo Steward`, then `12 Self-Hosted Deployment`
- Task mode: YELLOW feature/UI/API work explicitly approved by the user as an Autopilot feature scope.

## Files changed

Created:

- `steel_guitar_rag/lesson_studio.py`
- `ui/lesson-workbench.html`
- `ui/lesson-workbench.js`
- `tests/test_lesson_studio.py`
- `tests/test_lesson_workbench_ui.py`
- This handoff.

Modified:

- `steel_guitar_rag/api.py`
- `steel_guitar_rag/api_contract.py`
- `ui/steel-guitar-rag-mock.html`
- `ui/e9-fretboard-explorer.html`
- `ui/melody-workbench.html`
- `tests/test_api_contract.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`

Deleted files: none.

Generated artifacts: none.

## Public interfaces and behavior

- `GET /api/lessons/catalog` returns authenticated `lesson_catalog_v1` reviewed paths.
- `POST /api/lessons/build` accepts either `lessonId` or `topic`, `level`, and `duration`, returning `lesson_v1`.
- Valid custom levels: `beginner`, `intermediate`, `advanced`.
- Valid durations: `5_min`, `15_min`, `deep_dive`.
- Lesson links are restricted to app-local `/ui/` destinations.
- Reviewed and custom lesson generation is deterministic and source-free; it does not read private transcripts or claim personalization.

## Tests and checks

- `node --check ui/lesson-workbench.js` — passed.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/e9-fretboard-explorer.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- Focused lesson/API/frontend suite — **60 passed**.
- `tests/test_api_search.py` — **297 passed**.
- Full pytest — **983 passed**.
- Scoped `git diff --check` — passed.
- New-file naming check found no use of the rejected app name.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8771/ui/lesson-workbench.html?access=beta_user`
- Cache-busted URL tested: not required for the isolated local server
- Exact URL the user should use: pending the protected-preview restart and post-commit smoke
- Auth required: yes
- Auth provider: local-dev role header
- Cloudflare Access login result: not attempted; local smoke did not claim protected-preview behavior
- Local backend URL: `http://127.0.0.1:8771`
- Expected backend port: 8771 for this isolated smoke; protected preview remains 8770
- Expected git HEAD: pre-commit working tree based on `337b71972b7d71ceb443f158e2dbed5e920d8a45`
- Version endpoint: `/api/version`
- Version endpoint result: not used to infer the uncommitted working-tree implementation
- If version endpoint missing, how version is inferred: source files and local server requests were verified directly; this does not prove a committed runtime version
- Whether app root `/` works: not tested in this focused local browser run
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes; the four workspace actions rendered and a lesson handoff prefilled Chat
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: old Melody-only cache keys as proof of this feature
- Known caveats: the isolated local server intentionally left Melody disabled; protected-preview smoke must verify the already-enabled Melody workspace after restart

## Browser smoke result

- PASS: five reviewed paths loaded with two lessons each.
- PASS: an advanced deep-dive custom lesson rendered four exercises and all required lesson sections.
- PASS: a reviewed lesson rendered its exact Explorer handoff URL.
- PASS: Ask, Explore, Arrange, and Learn appeared across all four workspace headers.
- PASS: Chat accepted a lesson handoff question through its URL.
- PASS: Explorer opened in chord mode with `Find chords and voicings` and the expected root.
- PASS: no page-level horizontal overflow at desktop or the tested mobile breakpoint.
- PASS: no browser warning or error logs.
- PASS: no `[object Object]` output.

## Integration notes

- Lesson checkboxes are deliberately session-only and use no storage.
- The endpoint uses the existing answer authorization boundary without changing auth policy.
- The protected-preview service must be restarted after the implementation commit because `steel_guitar_rag/api.py` changed.
- Protected smoke should test the home page, Lessons catalog, one reviewed lesson, one custom lesson, one Explorer handoff, Melody availability, root redirect, and `/api/version`.

## Risk assessment

Medium. This adds an authenticated API surface and a new user-facing workflow, but it is deterministic, source-free, persistence-free, covered by the full test suite, and isolated from corpus/retrieval/auth configuration.

Rollback: revert the scoped implementation commit and restart the protected-preview service. No data migration or cleanup is required.

## Human decision needed

No. The approved feature scope is implemented and test-green. User smoke should evaluate the lesson content, navigation clarity, and whether this is sufficient to begin the broader UI polish phase.

## Safe-to-stage exact file list

- `steel_guitar_rag/api.py`
- `steel_guitar_rag/api_contract.py`
- `steel_guitar_rag/lesson_studio.py`
- `ui/steel-guitar-rag-mock.html`
- `ui/e9-fretboard-explorer.html`
- `ui/melody-workbench.html`
- `ui/lesson-workbench.html`
- `ui/lesson-workbench.js`
- `tests/test_api_contract.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_lesson_studio.py`
- `tests/test_lesson_workbench_ui.py`
- `docs/handoffs/task-completions/2026-07-13-1413-06-four-workspace-lessons-v1.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` in the implementation commit.
- Existing untracked `docs/lesson-mode.md` unless separately reviewed and approved for a documentation commit.
- Every unrelated dirty or untracked path, especially corpus, source-inbox, private-data, Chroma/vector, scraping, deployment, config, `public/`, `ui/brand/`, `Neon Sign/`, generated reports, credentials, and secrets.

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with the exact file list above, commit the feature, restart the protected preview, and run authenticated browser smoke at one new cache-busted Lessons URL.
