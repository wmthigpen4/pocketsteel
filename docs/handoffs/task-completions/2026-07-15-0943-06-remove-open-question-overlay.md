# Remove Landing Ask Overlay Label

## Task summary

Removed the decorative `OPEN QUESTION →` pseudo-element from the landing Ask example panel because it overlapped the `EXAMPLE QUESTION` heading. The example panel remains an accessible clickable prefill button. Bumped the shell stylesheet cache key and added a focused regression.

No other landing, Ask, answer, backend, auth, retrieval, or branding behavior changed.

## Files changed

- `ui/workspace-shell.css`
- Cache-key hunk only in `ui/steel-guitar-rag-mock.html`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- This handoff

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_same_origin_smoke_server.py` — 24 passed.
- Local browser: pseudo-element content is `none`, matching CSS rule count is zero, and the button contains only the intended example label/question/support copy.
- `git diff --check` — passed.

## Integration notes

`ui/steel-guitar-rag-mock.html` contains unrelated parked work. Stage only the stylesheet cache-key hunk from that file.

## Risk assessment

Low. This is a CSS deletion plus cache bust and regression assertion.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/workspace-shell.css`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-15-0943-06-remove-open-question-overlay.md`
- Cache-key hunk only from `ui/steel-guitar-rag-mock.html`

## Files that must not be staged

All unrelated dirty/untracked files and all other `ui/steel-guitar-rag-mock.html` hunks.

## Recommended next lane

Lane 01 exact-hunk commit, then Lane 12 protected-preview smoke.

## Commit readiness

Safe to commit.

## Suggested next step

Commit the exact scoped changes and refresh the protected preview.
