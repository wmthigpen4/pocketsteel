# 2026-06-27 11:10 - Lane 18 - Fretboard Musical Product Audit

## Pass / Warn / Fail

Warn.

The current E9 Fretboard Explorer is a strong deterministic teaching surface with validated pitch math, Emmons/Day copedent selection, note finder workflows, harmonized paths, a voicing identifier, and a chord/voicing finder. It is not yet ready to be treated as monetization-critical without additional protected-preview smoke, copedent-control naming cleanup, cross-copedent behavior constraints, and focused musical red-team coverage.

## Branch And HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `ec40156`
- Final HEAD / commit hash if committed: pending at handoff creation; report after exact-path docs commit.
- Task type: docs-only audit/report.
- Lane: `18 Product / Architecture`.
- Task mode: GREEN for this report only.

## Task Summary

Requested: perform a full Fretboard Explorer product, musical-rules, source/copyright, QA, and monetization audit after recent smoke-test-driven expansion.

Completed:

- Inspected repo governance, integration status, recent Explorer handoffs, Explorer rules/data/UI/tests, and recent git history.
- Ran focused pitch spot checks for exact red-team cases.
- Ran focused Explorer/backend/frontend checks.
- Created this architecture/product handoff.

Intentionally not changed:

- No app behavior.
- No UI implementation.
- No backend implementation.
- No tests.
- No corpus, scraping, embeddings, Chroma/vector stores, auth, DNS, deployment, source-inbox raw/provenance data, private sources, secrets, visual assets, or public-domain/song records.

## Files Inspected

Repo governance/status:

- `AGENTS.md`
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`

Explorer implementation and tests:

- `pocketsteel/e9_copedents.py`
- `pocketsteel/fretboard_explorer.py`
- `pocketsteel/fretboard_examples.py`
- `ui/e9-fretboard-explorer.js`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`

Recent handoffs reviewed:

- `docs/handoffs/task-completions/2026-06-23-18-e9-copedent-selector-contract.md`
- `docs/handoffs/task-completions/2026-06-26-2124-06-explorer-copedent-label-copy.md`
- `docs/handoffs/task-completions/2026-06-26-2218-06-single-note-learning-workflows.md`
- `docs/handoffs/task-completions/2026-06-27-0843-06-voicing-identifier-mode.md`
- `docs/handoffs/task-completions/2026-06-27-0952-12-voicing-identifier-protected-smoke-stale.md`
- `docs/handoffs/task-completions/2026-06-27-1011-06-grip-vocabulary-and-pad-roles.md`
- `docs/handoffs/task-completions/2026-06-27-1037-06-grip-help-disclosure.md`
- `docs/handoffs/task-completions/2026-06-27-1104-06-chord-voicing-finder.md`

Recent commits reviewed:

- `ec40156 docs: refresh integration status after chord finder`
- `a08eba4 feat: add explorer chord voicing finder`
- `187df4b fix: hide grip help by default`
- `2196af3 fix: move explorer notation near fretboard`
- `8d0c9bd feat: expand explorer grip vocabulary`
- `9048687 docs: refresh dominant seven grip status`
- `c6fa25e fix: label dominant seven grip vocabulary`
- `4843e4d docs: record voicing identifier protected smoke status`
- `f305c49 fix: classify partial extended voicings`
- `b73d017 docs: record voicing controls protected smoke`
- `6f3fb48 docs: refresh voicing identifier control status`
- `de7f545 fix: polish voicing identifier controls`
- `fd2750c docs: refresh explorer voicing identifier status`
- `4ac80e8 feat: add e9 voicing identifier mode`
- `c57ba92 feat: add explorer harmonized path rail`
- `bc4d8b8 feat: expand single-note finder workflows`
- `88678f2 feat: add e9 single-note finder`

## Musical Correctness Findings

### Pitch Math

Pass for the audited concrete spot checks.

Observed deterministic outputs:

- String 3, fret 3, open = `B`.
- String 3, fret 3, `B` pedal = `C`.
- String 5, fret 3, open = `D`.
- String 5, fret 3, `A` pedal = `E`.
- String 9, fret 3, open = `F`.
- Key F, fret 3, strings 4-6-10, `A+B` = `G, C, E`, correctly reads as C major / V in F.
- Key G, fret 3, strings 5-6-9, `A+B` = `E, C, F`; current tests assert `Fmaj7(no3)` and prevent dominant/V7 leakage.
- Key G, fret 3, strings 5-7-9, `A+B` = `E, A, F`; current tests assert `Fmaj7(no5)` and prevent dominant/V7 leakage.

### E9 Tuning And Copedent Model

Pass with naming warnings.

What is strong:

- Open 10-string E9 strings are modeled high-to-low as expected: 1 `F#`, 2 `D#`, 3 `G#`, 4 `E`, 5 `B`, 6 `G#`, 7 `F#`, 8 `E`, 9 `D`, 10 `B`.
- Emmons E9 and Day E9 are separated as selectable profiles.
- Day changes physical pedal order to `C, B, A` while preserving named A/B/C musical semantics.
- `My Copedent (E9)` remains disabled / future Backstage, which is correct for the current architecture.
- The Custom E9 with LKV profile is visible as app rules data and has 10 controls in the payload preview, while Emmons and Day have 7 controls.

Warnings:

- The generated Explorer rows remain default row families with the same 110 positions across Emmons, Day, and Custom LKV. That is acceptable for Emmons/Day because named-pedal semantics are stable, but it is not enough for paid custom-copedent claims.
- Current default control IDs use `E-raise`, `E-lower`, `D-lower`, and `G-lower`; prior product contracts used canonical shorthand such as `F`, `E`, `G+`, `G-`, `D-`, `D--`, and `V`. This naming drift should be resolved before monetization or persistent user profiles.
- `G-lower` currently includes both string 1 `F# -> G` and string 6 `G# -> F#`. That may be mechanically true for the represented app profile, but the label can mislead because it combines a raise and a lower under one shorthand. The UI should expose the actual string changes wherever this control is used.
- `D-lower` represents string 2 half-stop and string 9 lower in the default profile. Full-stop behavior is present in Custom as `RKR-full`, not as canonical `D--`. This is acceptable as app data, but not as a universal E9 claim.

### Chord / Voicing Naming

Pass with confidence-boundary risks.

What is strong:

- Voicing identification now distinguishes dominant 7 from major 7.
- Major 7, dominant 7, minor 7, 9th, diminished, half-diminished, sus, and 6th qualities have explicit matching logic in the client.
- Partial extended voicings are labeled with omitted tones, for example `Fmaj7(no3)` and `Fmaj7(no5)`.
- Missing third/root conditions reduce confidence.
- The current tests explicitly prevent 9th-string/color grips from leaking into dominant/V7 labels when the pitch set is actually major-7 color.

Risks:

- The richer voicing/chord-finder logic is currently client-side. That is acceptable for Explorer UX, but it is not yet a shared product rules engine that answer generation, tab, and backend validation can rely on.
- Chord naming is heuristic for ambiguous steel grips. That is unavoidable, but the UI must keep confidence, omitted tones, and alternate readings visible.
- Rootless and partial extended voicings should not be promoted as beginner defaults. They are valuable, but should remain behind vocabulary/tier controls unless the question asks for advanced color.

### Notation Modes

Pass with QA caveats.

What is strong:

- Notes, NNS, Roman, and Numbers modes are present.
- Marker labels and top-note filters change with notation mode.
- The tests cover expected G major and G natural minor scale spelling, plus NNS/Roman/Numbers label changes.

Risks:

- Notation is mostly exercised through a broad frontend harness. Add smaller fixtures for all 12 keys, enharmonic edge cases, dominant/major-7 labels, diminished and half-diminished notation, and selected-key vs voicing-root intervals.

### Harmonized Scale Path

Pass for current scope.

What is strong:

- Path mode avoids dumping all rows by default.
- The path rail supports step, ghost all, and compare same fret.
- Current G major low/middle/high path behavior is tested, including same-fret collisions and string-group changes.
- Movement remains visually represented as a sequence, not as stacked static cards.

Risks:

- This is still a teaching path, not a full movement/tab engine. Do not let path mode expand into arbitrary licks or song phrases. Movement over time should stay owned by the tab engine.
- More musical red-team is needed for minor paths, non-G keys, and whether alternate string groups should be shown as deliberate "why choose this" decisions rather than mere fallback rows.

## Product / UX Findings

### Strengths

- The Explorer has become a real teaching instrument, not just a decorative fretboard.
- The current mode split is product-sensible:
  - Single grip for static chord/grip inspection.
  - Harmonized scale path for sequence learning.
  - Single-note finder for pitch literacy and control impact.
  - Voicing identifier for "what is this shape?".
  - Chord / Voicing Finder for "where can I find this color?".
- Grip vocabulary defaults to Core and hides broader vocabulary unless requested.
- The chart/dialog language now uses `Copedent`, which is better user-facing terminology.
- Details include notes, intervals, string actions, grip roles, and why-this-works teaching copy.

### Product Risks

- Control density is now high. The Explorer is powerful, but new users need a guided first-run path or task-specific entry points.
- `Voicing identifier` currently uses a fret selector constrained to `1-10` in the frontend tests. That may be intentional for first-slice UX, but a paid Explorer should either support `0-24` consistently or clearly label the narrowed range.
- Copedent selection currently explains chart/preview state better than generated row state. Until custom-copedent rows are actually generated, paid copy should avoid "works with your exact copedent" claims.
- Advanced terms such as rootless, omitted, dominant color, partial major 7, and half-diminished need compact glossary help near where users encounter them.
- The default answer/UI experience should not dump every possible card. The current tier/vocabulary controls are a good start; preserve them.

## Source / Copyright Findings

Pass with monetization guardrails.

What is strong:

- The inspected Explorer behavior is deterministic rules/UI behavior. It does not appear to claim SGF provenance for generated grips or chord names.
- Existing handoffs consistently distinguish deterministic examples from source-backed or public-domain material.
- No app code or docs in this task created copyrighted song tab, public-domain song claims, or new source/provenance records.

Guardrails before paid features:

- Deterministic exercises must be labeled as deterministic/original educational examples.
- SGF/forum content can support prose guidance, but should not be implied as the source of exact generated fretboard positions unless the data path actually proves that.
- Public-domain song arrangements need explicit public-domain status and melody/chord source provenance per song.
- Private lesson or profile-backed features must remain behind auth and source review.
- Do not monetize copyrighted song transcription, copyrighted tab generation, or "sounds like [copyrighted song]" output.

## QA Gaps

Highest-priority gaps:

1. Protected-preview smoke has not yet passed for the latest Chord / Voicing Finder commit `a08eba4`. Integration status says local smoke passed, but protected preview is not yet verified for that slice.
2. Add a musical red-team matrix for exact pitch and voicing traps:
   - `G / fret 3 / 5-6-9 / A+B` must be `Fmaj7(no3)`, not dominant/V7.
   - `G / fret 3 / 5-7-9 / A+B` must be `Fmaj7(no5)`, not dominant/V7.
   - 9th-string color alone must not imply dominant 7.
   - Missing 3rd must lower confidence.
   - Missing 5th can still be practical.
3. Add cross-copedent tests that distinguish:
   - selected chart/preview behavior,
   - generated row behavior,
   - voicing/chord-finder behavior,
   - future custom-copedent behavior.
4. Add notation fixtures across all supported keys and enharmonic spellings.
5. Add mobile browser smoke for marker readability, path rail, chart/dialog, and high-density controls.
6. Add answer-integration tests only when the Explorer payload is exposed through answers; Explorer correctness alone does not prove answer routing.

Existing useful coverage:

- `tests/test_fretboard_explorer.py` validates deterministic payloads, copedent chart options, Day pedal order, control previews, transposition, partial diminished labeling, and pitch-row rules.
- `tests/test_frontend_answer_ui.py` exercises the Explorer client including notation, path rail, note finder workflows, voicing identifier, chord/voicing finder, object-string leak prevention, and the exact recent major-7 versus dominant-7 red-team cases.
- `tests/test_pedal_steel_fretboard_ui.py` exercises SVG/fretboard presentation behavior.

## Monetization Roadmap

### Free / Acquisition

Keep free:

- Basic E9 Explorer with Emmons and Day selection.
- Static positions and core grip vocabulary.
- Basic note finder.
- Basic chord finder for major/minor/dominant/major-7 with conservative candidate counts.
- Read-only copedent chart.

Reason: this proves product value quickly and differentiates from generic chatbot answers.

### Paid Individual Learner

Highest-value paid tier:

1. Saved custom E9 copedent profiles.
2. Profile-aware generated positions and chord/voicing finder.
3. Practice drills with progress tracking.
4. Guided progression/path exercises with tab-engine movement where time is involved.
5. Printable/shareable diagrams and practice sheets.
6. Advanced chord color packs: 6ths, 7ths, 9ths, altered-color warnings, substitutions, and rootless voicings.

Dependency: copedent naming and custom profile correctness must be stronger first.

### Teacher / Studio

Potential paid tier:

- Assignable Explorer drills.
- Shareable teacher-created fretboard snapshots.
- Student copedent profiles.
- Class-safe worksheets.
- Embeddable diagrams for lessons.

Dependency: stable payload URLs, saved state, and permissions.

### Advanced Pro

Potential paid tier:

- C6 / universal / 12-string support after E9 is mature.
- Advanced substitution and voice-leading explorer.
- Exportable deterministic JSON/CSV diagrams.
- Deeper tab/fretboard sync for original exercises.

Dependency: a shared deterministic pitch/chord engine and stronger QA fixtures.

### Future / Risky

Only after provenance design:

- Public-domain song arrangements.
- Private lesson transcript-backed examples.
- Source-backed lick/practice suggestions.

Do not monetize:

- Copyrighted song tab generation.
- Prompt-only transcription.
- SGF quote-dump "tabs".
- Claims that generated exercises come from public-domain or SGF sources without actual provenance.

## Highest-Priority Fixes Before Monetization

1. Run Lane 12 protected-preview smoke for `a08eba4` / current HEAD and record whether Chord / Voicing Finder is live.
2. Normalize copedent control naming across product contract, data, UI, and future answer payloads. Resolve `G+`/`G-`, `D-`/`D--`, `F` shorthand, and `V`/B-to-Bb naming before persistent profiles.
3. Create a shared deterministic Explorer music-rules package or API boundary so answer generation, tab sync, and UI do not fork chord/voicing logic.
4. Add red-team fixtures for major-7/dominant-7/rootless/partial traps across multiple keys.
5. Add a strict product copy rule: "selected copedent chart" is supported now; "your exact copedent drives every generated answer" is not supported until custom profile generation exists.
6. Verify mobile UX for the dense Explorer controls before using it as a paid feature.

## Highest-Value Paid Features

1. Saved custom E9 copedent with profile-aware output.
2. Practice drills built from deterministic note/grip/path rules.
3. Advanced chord/voicing finder with confidence, omitted tones, alternates, and filters.
4. Teacher share/assignment workflow around fretboard snapshots.
5. Tab-engine movement examples synced to SVG fretboard events.
6. Printable practice sheets and diagrams.
7. Public-domain song arrangements only after explicit provenance support exists.
8. Private lesson/profile-backed guidance behind auth and review.

## Specific Recommended Next Codex Prompts

### Lane 12 - Protected Preview Smoke

```text
Lane 12: Run ProtectedPreviewSmoke for the latest Fretboard Explorer Chord / Voicing Finder. Use docs/handoffs/task-completions/integration-status.md and smoke the direct Explorer URL:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-a08eba4

Verify Cloudflare Access, current HEAD/version expectations, Chord / Voicing Finder availability, Fmaj7 candidates, Cmin9 no-practical-candidate behavior, V7 in G resolving to D7, no [object Object], and no relevant console errors. Do not modify files, stage, commit, deploy, change DNS, or touch auth/secrets.
```

### Lane 18 - Copedent Naming Cleanup Contract

```text
Lane 18 Product / Architecture: Define a short contract that reconciles Explorer copedent control labels with product canonical names. Resolve how the app should display and serialize E-raise/F, E-lower/E, G+/G-, D-/D--, and V/B-to-Bb for Emmons, Day, and future My Copedent. Do not implement code. Write the required handoff under docs/handoffs/task-completions/.
```

### Lane 05 - Shared Music Rules Boundary

```text
Lane 05 Backend / RAG Integration: Design and implement the smallest shared deterministic music-rules boundary for E9 Explorer voicing/chord naming so answer generation and UI can use the same pitch/interval/quality semantics. Preserve current UI behavior, add focused tests for Fmaj7(no3), Fmaj7(no5), F7(no5), V7 in G, missing-third confidence, and no dominant leakage. Do not touch corpus, Chroma, embeddings, scraping, auth, DNS, or deployment.
```

### Lane 15 - Musical Red-Team QA

```text
Lane 15 QA / Answer Eval: Build a focused Explorer musical red-team matrix for pitch math, copedent controls, notation modes, major-7 versus dominant-7 traps, partial/rootless labels, and cross-copedent UI behavior. Run existing Explorer/fretboard/frontend tests plus targeted browser/API checks as appropriate. Write a QA handoff with pass/warn/fail and exact next blockers.
```

### Lane 06 - UX Density / Mobile Review

```text
Lane 06 UX/UI Design: Audit the E9 Fretboard Explorer control density and mobile usability without changing music rules. Focus on mode entry points, glossary placement, copedent chart readability, marker legibility, path rail, and chord/voicing finder candidate cards. Implement only small UI/copy fixes if scoped and covered by tests; otherwise write a design handoff.
```

## Checks Run

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log --oneline -20
git diff --cached --name-only
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Focused pitch spot-check command:

```bash
.venv/bin/python - <<'PY'
from pocketsteel.fretboard_explorer import resolve_notes, build_explorer_payload, validate_explorer_payload

cases = [
    ("string 3 fret 3 open", 3, (3,), ()),
    ("string 3 fret 3 with B", 3, (3,), ("B",)),
    ("string 5 fret 3 open", 3, (5,), ()),
    ("string 5 fret 3 with A", 3, (5,), ("A",)),
    ("string 9 fret 3 open", 3, (9,), ()),
    ("key F fret 3 strings 4-6-10 A+B", 3, (4, 6, 10), ("A", "B")),
    ("key G fret 3 strings 5-6-9 A+B", 3, (5, 6, 9), ("A", "B")),
    ("key G fret 3 strings 5-7-9 A+B", 3, (5, 7, 9), ("A", "B")),
]
for label, fret, strings, controls in cases:
    print(f"{label}: {resolve_notes(fret, strings, controls)}")
for copedent in (None, "emmons-e9-basic", "day-e9-basic", "custom-e9-lkv"):
    payload = build_explorer_payload("G", copedent)
    validate_explorer_payload(payload)
    print(f"payload {payload['copedent_profile']['id']}: controls={len(payload['control_impact_preview']['controls'])} positions={len(payload['positions'])}")
PY
```

Results:

- `node --check ui/e9-fretboard-explorer.js`: pass.
- `node --check ui/e9-fretboard-explorer-data.js`: pass.
- `tests/test_fretboard_explorer.py`: 38 passed.
- `tests/test_frontend_answer_ui.py`: 23 passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed.
- `git diff --check`: pass before this handoff; rerun after handoff before commit.
- Focused pitch spot checks: pass with expected note outputs.

Skipped:

- Full `pytest`: not required for this docs-only audit; focused Explorer/fretboard/frontend tests were run because they directly support the audit.
- Browser smoke: not run in this Lane 18 audit; latest protected-preview smoke for Chord / Voicing Finder remains a Lane 12 gap.

## Risks

Risk: medium for monetization readiness, low for this docs-only change.

Reasons:

- The Explorer has good deterministic foundations, but paid claims depend on copedent correctness, protected-preview verification, and QA breadth.
- Some high-value logic is client-side and should not become a separate, unverified truth source for answer generation.
- The worktree has broad unrelated dirty files that must remain parked.

Rollback:

- Revert the docs-only audit commit if this report needs replacement. No runtime behavior was changed.

## Human Decision Needed

No for this docs-only audit.

Yes before monetization copy or paid-gating decisions:

- Decide whether "Custom E9 with LKV" remains a demo selectable profile or becomes part of "My Copedent" later.
- Decide canonical public labels for `G+`, `G-`, `D-`, `D--`, `F`, `E`, and `V`.
- Decide whether advanced voicing/chord finder remains free acquisition or moves behind a paid tier after correctness hardening.

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-27-1110-18-fretboard-musical-product-audit.md`

No implementation, UI, backend, test, corpus, deployment, auth, DNS, source, or asset files changed.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-27-1110-18-fretboard-musical-product-audit.md`

## Files That Must Not Be Staged

All unrelated dirty or untracked work, including but not limited to:

- `README.md`
- `corpus_metadata/**`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- `corpus-private/**`
- `corpus-v2/**`
- Chroma/vector/embedding artifacts
- auth, DNS, deployment, secrets, raw source, generated report, design, or private-source files

## Recommended Next Lane

Lane 12 Self-Hosted Deployment for protected-preview smoke of the latest Chord / Voicing Finder Explorer build.

After that:

1. Lane 18 for copedent naming cleanup contract.
2. Lane 15 for musical red-team QA.
3. Lane 05 for a shared deterministic music-rules boundary.
4. Lane 06 for Explorer mobile/control-density review.

## Commit Readiness

Safe to commit as an exact-path docs-only audit, after rerunning:

```bash
git diff --check
git diff --cached --name-only
git diff --cached
git diff --cached --check
```

## Suggested Next Step

Run Lane 12 protected-preview smoke for the latest Explorer Chord / Voicing Finder URL and do not start monetization implementation until that smoke and the copedent naming cleanup are complete.
