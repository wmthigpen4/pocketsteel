# Shared Explorer Music Rules Boundary And Copedent Naming Contract

Pass/warn/fail: pass

## Task Summary

Implemented the scoped Lane 05 follow-up for the deterministic E9 Explorer shared-rules boundary and additive copedent naming data contract.

The existing shared frontend music-rules boundary from commit `371de09` remains in place. This slice added the missing copedent naming contract fields and wired the Explorer payload/control-preview path to consume the richer control records without changing row-generation musical behavior.

Intentionally not changed:
- No corpus, SGF, Chroma, embeddings, scraping, private-source, auth, DNS, secrets, or deployment work.
- No stable control IDs were destructively renamed.
- No My Copedent row-generation claim was added.
- No source cards or provenance records were created.
- No protected-preview restart was attempted.

## Files Changed

- `steel_guitar_rag/e9_copedents.py`
- `steel_guitar_rag/fretboard_explorer.py`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1219-05-shared-explorer-music-rules-boundary.md`

Generated artifacts:
- `ui/e9-fretboard-explorer-data.js` was regenerated from `steel_guitar_rag.fretboard_explorer.build_explorer_payload(...)`.

Deleted files:
- None.

## Shared Boundary Introduced

The shared deterministic music-rules boundary itself was already committed in `371de09` via `ui/e9-music-rules.js`, and this slice preserved that boundary.

This slice reduced a remaining contract fork by making `control_impact_preview.controls` derive from the same structured copedent control records used by `selected_copedent.controls` and `selected_copedent.chart.columns`.

## Copedent Naming Contract Implementation

Added additive control metadata to E9 copedent payloads:

- `stable_id`
- `display_label`
- `mechanical_name`
- `player_shorthand`
- `physical_position`
- `travel`
- `change_type`
- `affected_strings`
- `string_actions`
- `compatibility_aliases`

Preserved existing fields:

- `id`
- `label`
- `control_type`
- `changes`
- chart rows/cells

Naming behavior:

- A/B/C stable IDs and named musical semantics are preserved for Emmons and Day.
- Day profile still changes physical order to C-B-A while A/B/C named changes remain the same.
- Standard Emmons/Day do not expose `B-to-Bb`.
- Custom E9 with LKV exposes `B-to-Bb vertical`, `V`/`LKV` shorthand, and string actions for strings 5 and 10.
- The mixed RKL control no longer presents as a simple `G-lower lever`; it now exposes `RKL G raise/lower` plus explicit string 1 raise and string 6 lower actions.
- D lower standard profile now displays as `D lower half-stop`; Custom E9 has separate `D lower half-stop` and `D lower full-stop`.
- E-raise is displayed as `E raise (F lever)` where the profile shorthand supports it; E-lower remains mechanical-first as `E-lower lever`.

## Duplicated Logic Reduced

- `build_control_impact_preview()` now uses `controls_by_id_for_profile()` and each profile control’s serialized payload before adding key-specific impact summaries.
- The frontend now prefers `display_label` before legacy `label` when rendering Explorer control chips, chart headers, and impact-preview labels.
- Static Explorer data was regenerated so the browser bundle matches the backend contract.

## Tests And Checks Run

- `git status --short`
- `git branch --show-current`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m py_compile steel_guitar_rag/e9_copedents.py steel_guitar_rag/fretboard_explorer.py`
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py tests/test_fretboard_explorer.py -q` - 42 passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 24 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_api_contract.py -q` - 39 passed
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py tests/test_fretboard_explorer.py tests/test_frontend_answer_ui.py -q` - 66 passed
- `.venv/bin/python -m pytest` - 861 passed
- `git diff --check` - passed

## Local Smoke Result

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=shared-rules-contract-local-smoke-20260627`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=shared-rules-contract-local-smoke-20260627`
- Exact URL the user should use: local-only URL above, or protected preview after Lane 12 restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `520cf04` before commit
- Version endpoint: not used for local smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local git HEAD and local served files
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not required for this Explorer page smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer page smoke
- Who should test this URL: Codex locally; user after protected-preview restart
- Do not test these URLs: do not treat API fallback as browser smoke
- Known caveats: protected preview previously reported stale `/api/version` at `4040a47`; this task did not restart protected preview

Verified in browser:

- Explorer loads.
- Copedent chart/control labels are understandable.
- Emmons chart shows `E raise (F lever)`, `D lower half-stop`, and `RKL G raise/lower`.
- Custom E9 with LKV shows `B-to-Bb vertical`, RKL half/full, and D lower half/full controls.
- Voicing Identifier renders and uses cleaned labels.
- Chord / Voicing Finder renders Fmaj7 as major-7/rootless partials, not dominant.
- Chord / Voicing Finder renders D7/dominant-7 partials via root/quality controls.
- No `[object Object]`.
- No relevant console warnings/errors.

## Protected-Preview Smoke Result

Not run in this lane. Protected-preview restart/deploy is Lane 12 work. The latest integration status already warned `/api/version` was stale, so this handoff recommends Lane 12 restart and protected-preview smoke after commit.

Suggested protected-preview URL after restart:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=<new-commit-short-sha>`

## Remaining Duplication

- Some UI-only mode orchestration remains in `ui/e9-fretboard-explorer.js`.
- The frontend shared rules boundary owns UI-side voicing discovery for interactive controls; backend row generation owns deterministic Explorer rows.
- Future answer/tab sync should import or mirror the shared rules boundary rather than reimplementing interval/chord confidence rules again.

## Risks

Risk level: low to medium.

Reasons:
- The runtime payload changed additively, but the static data file is large and was regenerated.
- Frontend label rendering now prefers `display_label`, which is intended but user-visible.
- Protected preview still needs a Lane 12 restart/smoke to prove deployed behavior.

Rollback:
- Revert the scoped implementation commit to restore previous copedent payload labels and static data.

## Human Decision Needed

No product decision needed for this scoped slice.

Human/Lane 12 action needed: restart protected preview and smoke the committed cache-busted URL if the user wants protected-preview verification.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/e9_copedents.py`
- `steel_guitar_rag/fretboard_explorer.py`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1219-05-shared-explorer-music-rules-boundary.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty/parked work, especially:

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
- `source-inbox/provenance.json`
- `corpus-private/`, `corpus-v2/`, Chroma/vector/embedding outputs
- `ui/brand/`, `public/brand/`, `Neon Sign/`, deployment/auth/DNS/secrets files
- other untracked parked handoffs/assets not named in the safe-to-stage list

## Recommended Next Lane

Lane 01 exact-path commit for the safe-to-stage list, then Lane 12 protected-preview restart/smoke.

Suggested Lane 12 prompt:

```text
Lane 12: Restart protected preview for the shared Explorer music-rules/copedent naming contract commit. Smoke https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=<commit-short-sha>. Verify /api/version, root behavior, Explorer load, Emmons/Day/Custom copedent labels, Voicing Identifier, Chord / Voicing Finder Fmaj7 and D7/V7 cases, no [object Object], and no relevant console errors. Write the protected-preview smoke handoff.
```

## Commit Readiness

Safe to commit.
