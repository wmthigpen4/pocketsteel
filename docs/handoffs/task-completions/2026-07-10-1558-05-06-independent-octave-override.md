# Independent Melody Studio octave override

## Task summary

Fixed the user-smoke defect where changing one note's octave re-anchored all later automatic notes. Per-note octave overrides now modify only the selected musical event. Phrase-level Ascending/Descending remains the intentional control for reshaping the whole contour.

Musical clarification: unmarked `5 6 1` remains ambiguous in the abstract, but closest/ascending G major resolves naturally as D4-E4-G4, with the tonic above the 6. An explicit octave-up on only `1` produces D4-E4-G5 while surrounding events retain their baseline registers.

## Files changed

- `pocketsteel/melody_arranger.py`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- this handoff

## Tests and checks

- Focused melody/frontend suite: 60 passed.
- Full pytest: 920 passed.
- Core JavaScript syntax: passed.
- `git diff --check`: passed.
- Local browser smoke: `5 6 1 3` displayed D4-E4-G4-B4; selecting only `1` and moving it up displayed and generated D4-E4-G5-B4. No `[object Object]`.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/melody-workbench.html?access=beta_user&v=octave-fix-local-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview commit/restart smoke
- Auth required: no
- Auth provider: scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: 8898
- Expected git HEAD: working tree based on `4ee5063`
- Version endpoint: `/api/version`
- Version endpoint result: protected verification pending commit
- Whether app root `/` works: expected; not the focused target
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: expected; not the focused target
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale script cache keys
- Known caveats: literal tab fixes register and therefore disables/rejects octave override; edit its string/fret instead

## Risk assessment

Low to medium. This corrects arranger semantics shared by frontend preview and backend output. It is tightly covered and leaves phrase-level contour modes unchanged.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/melody_arranger.py`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-10-1558-05-06-independent-octave-override.md`

## Files that must not be staged

All other dirty/untracked paths.

## Recommended next lane

01 Repo Steward exact-path commit, then 12 protected-preview restart/browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact seven paths, refresh the supervised preview, and verify independent octave editing at one cache-busted URL.
