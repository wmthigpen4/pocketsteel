# Classic-country answer fretboard

## Task summary

- Fixed the answer for `Show me a classic country move.` so the written E9 pickup is accompanied by an interactive, deterministic three-state fretboard.
- The displayed sequence is fret 1 strings 4-5 with A down, fret 3 strings 4-5 with A down, then fret 3 strings 4-5-6 open for the G-major landing.
- The existing answer wording, API schema, retrieval behavior, authentication, and general fretboard renderer were not changed.

## Files changed

- `pocketsteel/fretboard_examples.py`
- `pocketsteel/api.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-07-15-1057-05-classic-country-fretboard.md`

## Tests and checks

- `.venv/bin/pytest -q tests/test_fretboard_examples.py tests/test_api_search.py -k 'classic_country_move'` — 2 passed, 385 deselected.
- `.venv/bin/pytest -q tests/test_fretboard_examples.py tests/test_api_search.py` — 387 passed.
- `.venv/bin/python -m py_compile pocketsteel/api.py pocketsteel/fretboard_examples.py` — passed.
- `git diff --check` — passed.
- Local desktop browser smoke — passed. The answer rendered `Classic-country pickup in G`, all three position controls, and the interactive pedal-steel fretboard; selecting the second state updated the displayed position. No horizontal overflow was detected.
- Automated phone-width browser smoke was not run because the available in-app browser session did not expose viewport resizing. Responsive behavior remains a protected-preview/manual-smoke item.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8768/ui/steel-guitar-rag-mock.html?v=classic-country-fretboard-local-20260715`
- Cache-busted URL tested: `http://127.0.0.1:8768/ui/steel-guitar-rag-mock.html?v=classic-country-fretboard-local-20260715`
- Exact URL the user should use: protected-preview URL to be recorded by Lane 12 after commit
- Auth required: no external auth; local controlled beta state enabled
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8768`
- Expected backend port: 8768
- Expected git HEAD: working tree based on `746c7a354505ed2c99eb84682228c6bbe02cea15`; branch advanced concurrently before commit
- Version endpoint: `http://127.0.0.1:8768/api/version`
- Version endpoint result: `746c7a3`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, redirects with HTTP 302
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes, HTTP 200
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale cache-busted protected-preview URLs
- Known caveats: local phone-width automation was unavailable; the final committed SHA and protected URL will supersede this local working-tree version.

## Integration notes

- `classic_country_move_payload_for_question()` is intentionally exact-prompt scoped and uses the existing pitch-validated position builder.
- `practical_intent_answer()` attaches the payload before returning because this curated answer exits before the generic late fretboard enrichment path.
- No API or component contract changed; the response now fills the existing `fretboard` field.
- Unrelated staged and unstaged work remains parked.

## Risk assessment

- Risk: low to medium. The route is exact-prompt scoped and fully covered by API and fretboard-contract regressions. The remaining visual risk is narrow-screen layout, which needs protected/manual verification.
- Rollback: revert the scoped commit; no data migration or persistent state is involved.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `pocketsteel/api.py`
- `pocketsteel/fretboard_examples.py`
- `tests/test_api_search.py`
- `tests/test_fretboard_examples.py`
- `docs/handoffs/task-completions/2026-07-15-1057-05-classic-country-fretboard.md`

## Files that must not be staged

- Every other staged, modified, or untracked path in the worktree, including protected corpus, source-inbox, brand, public, deployment, and unrelated handoff work.

## Recommended next lane

- Lane 01 Repo Steward for exact-path commit, followed by Lane 12 protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

- Commit only the five paths listed above, update the protected preview to the resulting SHA, and verify the exact prompt produces the interactive three-state fretboard.
