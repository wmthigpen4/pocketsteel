# Amazing Tablature protected-preview smoke pass

## Task summary

Completed the authenticated protected-preview smoke for the bounded Amazing Tablature release. The protected Melody Studio loaded after Cloudflare Access sign-in and arranged the four-note phrase `1 2 3 5` in G using the deterministic E9 fallback selected by the release gate.

The runtime remains pinned to implementation commit `4b443c7`. The unpromoted discovery challenger `at-ca3af91682513311` was not activated. No validation or sealed-test data was opened, and no source data, private annotations, embeddings, or model artifacts were changed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=arrangement-engine-4b443c7-20260722`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=arrangement-engine-4b443c7-20260722`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=arrangement-engine-4b443c7-20260722`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: runtime implementation `4b443c7`; coordination repo HEAD before this handoff `e353f41439eaf53ce8a48c27111456390d218117`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `200`, `{"status":"ok","git_sha":"4b443c7"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; local upstream returns `302`
- Whether app root `/` is expected to work: yes, by redirect
- Whether `/ui/steel-guitar-rag-mock.html` works: yes; local upstream returns `200`
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex and the user
- Do not test these URLs: generated private review consoles or validation/sealed-test paths
- Known caveats: the exact runtime is served from the immutable external release checkout `~/.steel-rag/releases/4b443c7-standalone` using an external Python environment; current repo HEAD contains later documentation-only commits

## Browser smoke result

PASS.

- Protected page loaded as the Melody Studio workspace rather than an Access login page.
- Input phrase: `1 2 3 5`; key: G major.
- Result heading: `Your melody exercise in G`.
- Four accessible score-note events were rendered: note 1 through note 4.
- The score event names exposed the rendered pitches, including harmony where the Recommended route added it.
- The Melody Studio fretboard rendered.
- Ten-string E9 tablature rendered with six sounding string positions across the four events.
- The visible engine disclosure read: `Arrangement method: verified E9 rules. Imported score images are reviewed before arranging.`
- The note navigator reported `Note 1 of 4`.
- No `[object Object]` text appeared.
- No browser console warnings or errors were recorded.

## Runtime verification

- `/health/live`: `{"status":"live"}`
- `/health/ready`: `{"status":"ready"}`
- `/api/version`: runtime `4b443c7`
- Local `/`: `302`
- Local `/ui/steel-guitar-rag-mock.html`: `200`
- Local `/ui/melody-workbench.html`: `200`
- LaunchDaemon `com.steelguitarrag.private-preview`: running, PID `41636`, release directory `~/.steel-rag/releases/4b443c7-standalone`, never exited

## Files changed

- Created this handoff only.

## Tests and checks

- Authenticated in-app-browser smoke at the exact cache-busted protected URL: PASS.
- Browser console warnings/errors check: PASS, zero findings.
- Runtime liveness, readiness, version, and route-status checks: PASS.
- Earlier release verification: full test suite `1375 passed`.
- `git diff --check`: required after this handoff is written.

## Integration notes

- Production-facing Melody Studio now clearly uses deterministic verified E9 rules because no learned challenger passed the fixed promotion gate.
- The active source authority remains the 278-page main batch plus the 34-page licks batch. The superseded 51-image batch remains excluded.
- The discovery challenger remains available for analysis but is not promoted to beta, stable, or runtime use.
- Validation and sealed-test partitions remain closed.

## Risk assessment

Low. The release is deterministic and review-first for image imports. The main operational caveat is that the protected preview is intentionally pinned to an external immutable release checkout rather than the coordination repo's later documentation HEAD.

## Human decision needed

No. The user may continue product smoke at the exact protected URL.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-22-1855-12-amazing-tablature-protected-smoke-pass.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing unrelated untracked historical handoffs
- `corpus-private/` and all source, annotation, evaluation, challenger, validation, and sealed-test artifacts
- External release and virtual-environment directories under `~/.steel-rag/`

## Recommended next lane

Lane 15 may independently record user-smoke findings if any are reported. Otherwise, the bounded release goal is complete and future work should begin as a separately scoped feature slice.

## Commit readiness

Safe to commit.

## Suggested next step

Use the protected Melody Studio normally. If a specific melody produces a poor deterministic arrangement, capture that user-level example as a new regression without reopening validation or sealed-test data.
