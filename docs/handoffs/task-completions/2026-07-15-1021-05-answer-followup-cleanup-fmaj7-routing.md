# Answer Follow-up Cleanup and Fmaj7 Routing

## Task summary

- Removed the `KEEP GOING` chip row and bottom follow-up composer from the answer workspace.
- Preserved the restored full-screen Ask workspace as the place to ask another question.
- Extended compound chord-question parsing so `What is an Fmaj7? Where can I find it on the fretboard?` returns the concrete Fmaj7 explanation and F-major E9 fretboard positions.
- Added focused backend and frontend regression coverage.
- Intentionally did not change APIs, authentication, source handling, the full-screen Ask submission flow, or unrelated dirty work.

## Lane classification

- Mixed Lane 05 Backend / RAG Integration, Lane 06 UX/UI Design, Lane 15 QA, and Lane 01 Repo Steward.
- User-smoke bug-fix autopilot; implementation and exact-path commit are approved.

## Files changed

- `steel_guitar_rag/basic_chord_answers.py`
- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_api_search.py` (one exact regression hunk only)
- `ui/steel-guitar-rag-mock.html` (answer follow-up removal hunks only)
- `tests/test_frontend_answer_ui.py` (answer follow-up regression hunks only)
- This handoff.

No files were deleted. No generated, corpus, private, vector, authentication, or deployment-policy artifacts were changed.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_api_search.py tests/test_answer_intent_classifier.py` — PASS, 427 tests.
- Exact Fmaj7/major-seventh API regression subset — PASS, 5 tests.
- `.venv/bin/python -m pytest -q tests/test_frontend_answer_ui.py -k 'answer_workspace_has_no_followup_chips_or_composer or answer_ui_header_only_exposes_home_ask_and_backstage or answer_ui_keeps_submission_in_full_screen_ask_workspace'` — PASS, 3 tests.
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py -k 'ask or landing'` — PASS, 9 tests.
- `node --check ui/answer-client.js` — PASS.
- `node --check ui/pedal-steel-fretboard.js` — PASS.
- Inline scripts from `ui/steel-guitar-rag-mock.html` parsed with Node `vm.Script` — PASS.
- Broad landing/frontend/same-origin run — WARN: one relevant stale assertion was fixed; the remaining failure is an unrelated parked Melody Studio copy expectation in `tests/test_same_origin_smoke_server.py`.
- `git diff --check` — PASS before staging.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8766/ui/steel-guitar-rag-mock.html?v=answer-cleanup-local-20260715`
- Cache-busted URL tested: `http://127.0.0.1:8766/ui/steel-guitar-rag-mock.html?v=answer-cleanup-local-20260715`
- Exact URL the user should use: protected-preview URL to be recorded after commit
- Auth required: no; controlled beta-member state selected locally
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8766`
- Expected backend port: 8766
- Expected git HEAD: working tree based on `47bf77e0ff00b50e6dc4acab39e08ad4bda23cd7`
- Version endpoint: `http://127.0.0.1:8766/api/version`
- Version endpoint result: local working-tree server
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not used for this smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale protected-preview cache keys
- Known caveats: local access state is controlled and is not Cloudflare Access authentication

Results:
- Exact compound Fmaj7 question returned `Fmaj7 is F-A-C-E`, major-seventh guidance, and the F-major E9 fretboard visualization.
- Zero answer-workspace follow-up sections and zero answer-workspace composers.
- Desktop and narrow viewport had zero horizontal overflow.
- No relevant browser console warnings or errors.

## Integration notes

- The parser change accepts `where can I find it on the fretboard` as a suffix on an otherwise supported chord-theory request.
- The existing major-position visual remains the practical E9 anchor while the copy explains how to target E as F's major seventh.
- The answer-page removal does not remove the full-screen Ask input, Send/Enter behavior, or suggested questions.

## Risk assessment

- Low. The backend change is a narrow suffix-recognition expansion and the UI change removes only the two user-selected answer follow-up surfaces.
- Rollback is the scoped implementation commit.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `steel_guitar_rag/basic_chord_answers.py`
- `steel_guitar_rag/fretboard_examples.py`
- Exact regression hunk in `tests/test_api_search.py`
- Exact answer-follow-up hunks in `ui/steel-guitar-rag-mock.html`
- Exact answer-follow-up regression hunks in `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-07-15-1021-05-answer-followup-cleanup-fmaj7-routing.md`

## Files that must not be staged

- Every unrelated dirty or untracked file, including unrelated hunks in the three overlapping files above.
- `docs/handoffs/task-completions/integration-status.md` must be refreshed separately after commit and remain unstaged.

## Recommended next lane

- Lane 01 exact-hunk commit, then Lane 12 protected-preview update and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the listed exact files/hunks, commit, refresh the isolated protected-preview runtime, and verify the exact cache-busted URL at desktop and phone widths.
