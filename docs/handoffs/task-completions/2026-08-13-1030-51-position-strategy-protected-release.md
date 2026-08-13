# Position-strategy protected release

## Task summary

- Released the search-quality/position-strategy repair from an isolated worktree whose commit has protected SHA `4a77e849c9c9ba8e13429d91ae055d06d0de7ce5` as its only parent.
- Activated release commit `585e74b1c0e3ab1d90ef4cd8c908244836083b70` through the existing loopback-only macOS LaunchAgent on `127.0.0.1:8770`.
- Preserved the existing Cloudflare Access/Tunnel infrastructure and existing UX/UI. No `chatgpt.site`, public landing page, UI, DNS, Access, Tunnel, or Cloudflare configuration was created or changed.
- Kept the canonical frontier on its independently verified, self-contained service root at `/Users/cory/.steel-rag/services/canonical-frontier-v1034-fallback-20260806`, healthy on `127.0.0.1:8771`.
- Completed authenticated browser smoke for both the repaired deterministic teaching path and a live SGF corpus-backed path.

## Files changed

- This completion record:
  - `docs/handoffs/task-completions/2026-08-13-1030-51-position-strategy-protected-release.md`
- The product repair was already committed as `64b9ce2fe84e55fff44a2617545ddccd503a144f` and isolated into release commit `585e74b1c0e3ab1d90ef4cd8c908244836083b70`; see `2026-08-13-1020-15-position-strategy-release-readiness.md` for its exact file inventory.
- Runtime-only state:
  - Existing user LaunchAgent now points at `/Users/cory/.steel-rag/releases/position-strategy-20260813`.
  - That detached release worktree contains the expected untracked `.venv` symlink used by the supervised runtime.
  - Rollback copy retained at `/tmp/steel-rag-preview-backup.dHmhw7`.

## Tests and checks run

### Release construction and ancestry

- Isolated release `HEAD`: `585e74b1c0e3ab1d90ef4cd8c908244836083b70`.
- Isolated release only parent: protected SHA `4a77e849c9c9ba8e13429d91ae055d06d0de7ce5`.
- `git diff --exit-code 4a77e849..585e74b1 -- ui deploy/landing`
  - PASS: no UI or landing-page changes.
- Detached LaunchAgent preflight
  - PASS.
- Focused isolated tests
  - PASS: 493 passed.
- Isolated full non-contextual suite
  - PASS: 1,653 passed, 2 intentionally deselected branch-context tests.
- Development-worktree complete suite
  - PASS: 1,666 passed in 88.06 seconds.

### Frozen frontier

- `python3 scripts/verify_canonical_frontier_service.py --service-root /Users/cory/.steel-rag/services/canonical-frontier-v1034-fallback-20260806 --manifest deploy/macos/canonical-frontier-service-bundle-v931.json`
  - PASS: 76 files verified; 1,948,039 passages; protected holdout usage zero.
- Frozen service-root inventory
  - PASS: self-contained, zero symlinks, repository manifest byte-identical to the active frozen manifest.
- `http://127.0.0.1:8771/health/live`
  - PASS: HTTP 200.
- `http://127.0.0.1:8771/health/ready`
  - PASS: HTTP 200.

### Supervised application runtime

- Existing user LaunchAgent handover
  - PASS after allowing launchd a two-second settle and retrying bootstrap.
- Supervised runtime verification
  - PASS: running on loopback `127.0.0.1:8770` from the isolated release root.
- `http://127.0.0.1:8770/health/live`
  - PASS: `{"status":"live"}`.
- `http://127.0.0.1:8770/health/ready`
  - PASS: `{"status":"ready"}`.
- `http://127.0.0.1:8770/api/version`
  - PASS: `git_sha` is `585e74b1`; `server_started_at` is `2026-08-13T15:27:43.712113+00:00`.
- Loopback root `/`
  - PASS: HTTP 200, 300,691 bytes.
- Loopback `/ui/steel-guitar-rag-mock.html`
  - PASS: HTTP 200, 300,691 bytes.

### Protected browser smoke

- Target type: protected preview through the existing Cloudflare Access/Tunnel route.
- Exact cache-busted URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=position-strategy-585e74b1`.
- Auth result: PASS; the existing signed-in Access session opened the application.
- Unauthenticated root behavior: PASS; `https://app.steelguitarrag.com/` redirects to the existing Cloudflare Access login.
- Expected release: `585e74b1c0e3ab1d90ef4cd8c908244836083b70`.
- Existing UX/UI: PASS; home, navigation, Q&A form, answer workspace, follow-up area, and source-card layout rendered with no new page or UI replacement.
- Browser console: PASS; no errors or warnings during either answer smoke.
- Repaired question: `How does a steel guitar player decide when to move frets? Why not just stay on one fret?`
  - PASS: complete deterministic lesson rendered, including reasons to stay, reasons to move, and the G/C 3rd-fret versus 8th-fret example.
  - Runtime route: `steel_guitar:position_strategy` -> `deterministic`; `curated_practical_answer`; `answer_contract`; fallback `none`.
- SGF corpus question: `What do Steel Guitar Forum players report as the practical advantages and disadvantages of keyless pedal steel guitars?`
  - PASS: source-backed answer rendered with three source cards from two Steel Guitar Forum threads.
  - Runtime route: `steel_guitar:forum_wisdom` -> `source_backed_rag`; `canonical_frontier_complete`; `frontier_contract_verified`; fallback `none`.
- API fallback status: no fallback was needed in either smoke; deterministic and canonical-frontier routes both completed successfully. The authenticated UI runs above are the browser smoke; loopback API checks are supporting evidence, not substitutes for it.
- The protected browser tab was retained as a deliverable for user smoke.

## Risks

- The repaired deterministic-miss path can send unmatched position-strategy questions to the paid/source-backed frontier; telemetry names this fallback explicitly and regression coverage exercises it.
- The LaunchAgent installer can encounter a transient re-bootstrap race when the same label is immediately reloaded. This release succeeded after a two-second launchd settling interval and bootstrap retry; no application defect was observed.
- Rollback remains the protected parent release `4a77e849`; the retained `/tmp` backup is temporary and may not survive a reboot.

## Human decision needed

- No release decision is needed. The authorized protected release and automated smoke are complete.
- Optional user smoke may evaluate answer tone and teaching quality at the exact protected URL above.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-13-1030-51-position-strategy-protected-release.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing unrelated modification).
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md` (pre-existing unrelated untracked file).
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md` (pre-existing unrelated untracked file).
- The release worktree's runtime-only `.venv` symlink.
- Corpus, source, vector-index, embedding, private-data, environment, secret, log, generated, UI, public-page, DNS, auth, Tunnel, and Cloudflare configuration files.

## Recommended next lane

- User smoke/normal operations. Return to Lane 05 plus Lane 15 only if a specific answer-quality regression is reported.

## Commit readiness

Safe to commit this exact handoff path only.
