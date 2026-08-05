# v980 Protected Preview Pass

- Date: 2026-08-05
- Lane: 12 Self-Hosted Deployment
- Status: PASS; ready for owner test use
- Expected site commit: `78a0d0e5`
- Model service: `canonical-frontier-v980-hybrid-semantic-passages`

## Task summary

The committed waiting experience and the v980 loopback knowledge candidate are deployed together in the protected preview. The protected browser completed a real source-backed answer request from the question form through the site adapter to the loopback model service.

## Deployment

- Detached release: `/Users/cory/.steel-rag/releases/78a0d0e5-v980-waiting`
- Existing user-owned production release pointer was atomically moved from the prior immutable release to the new preflighted immutable release.
- The exact port-8770 listener was terminated so the existing LaunchDaemon could restart it.
- Automatic rollback was prepared but not needed.
- No DNS, Cloudflare Access policy, secret, corpus, Chroma, vector index, or raw data changed.
- The port-8771 candidate remained running throughout the handoff.

The repository's activation preflight passed. The full plist-replacement activation path stopped at the macOS administrator-password prompt and was cancelled without changing the plist. No password was requested from or supplied by the owner.

## Protected browser smoke

- Exact cache-busted URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=v980-waiting-78a0d0e5-20260805`
- Auth result: PASS; the protected session loaded the app and exposed the live question form with the owner's saved Emmons setup
- Question: `What is the effect of winding strings under the tuning post on string breakage?`
- Waiting state: PASS; source-check status and rotating steel fact visible
- Final answer: PASS; correctly stated that winding under increases downward angle and tends to increase string breakage
- Source card: PASS; exact supporting Steel Guitar Forum excerpt and URL visible
- Waiting cleanup: PASS; waiting card hidden when the answer arrived
- Browser console warnings/errors: none
- The verified protected answer tab was left open for owner inspection

## Endpoint verification

- `/api/version`: `78a0d0e5`
- `/health/live`: PASS
- `/health/ready`: PASS
- Root `/`: `302` to `/ui/steel-guitar-rag-mock.html`
- `/ui/steel-guitar-rag-mock.html`: `200`
- LaunchDaemon: running, PID `35634`
- Listener working directory: exact detached `78a0d0e5-v980-waiting` release
- Port `8771`: ready; v980 architecture reported

## Tests/checks run

- Deployment preflight — PASS
- `uv run --with pytest pytest tests/test_frontend_answer_ui.py -q` — PASS, `51 passed`
- `git diff --check` before the implementation commit — PASS
- Protected browser smoke — PASS
- Loopback endpoint and supervisor checks — PASS

## Risks

- This is a protected test deployment, not public release authorization.
- The previously exposed v931 protected evaluation cannot be reused for promotion.
- Hard-question abstentions remain the primary model-quality gap.
- The release pointer is user-owned and recoverable, but a future administrator-authorized activation should update the LaunchDaemon plist to reference the exact release directly.

## Human decision needed

No decision is needed to test the protected preview. Public promotion still requires a fresh, untouched protected evaluation and an explicit release decision.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-05-1610-12-v980-protected-preview-pass.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md` (pre-existing unrelated untracked file)
- Release worktrees, environment files, credentials, logs, corpus, Chroma, vector indexes, and evaluation state

## Recommended next lane

Lane 15: build a new source-disjoint protected evaluation and keep the development loop blind to its answers. Lane 05 can then address the abstention bucket without changing the validated citation and tablature safeguards.

## Commit readiness

Ready for an exact-path documentation commit.
