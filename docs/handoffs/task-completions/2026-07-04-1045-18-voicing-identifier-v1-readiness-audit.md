# 2026-07-04 10:45 - Lane 18 - Voicing Identifier v1 Readiness Audit

## Task Summary

Requested: audit readiness for Voicing Identifier v1 in the E9 Fretboard Explorer and define a docs-only implementation contract before any additional runtime work.

Completed: inspected the existing Explorer UI, shared music-rules boundary, backend Explorer row metadata, frontend tests, and prior handoffs. This handoff records whether the existing Explorer can support a useful v1, what deterministic contract is needed, what must not be overclaimed, and the smallest safe next implementation slice.

Intentionally not changed:

- No backend code.
- No UI/runtime code.
- No tests.
- No melody input.
- No corpus, scraping, embeddings, Chroma/vector stores, source-inbox, auth, DNS, deployment, secrets, private transcripts, licensing metadata, or assets.

Task type: docs-only readiness audit / product contract.

Lane: `18 Product / Architecture`.

Task mode: GREEN for this handoff. Future implementation is YELLOW because it would change Explorer UI/tests and possibly shared deterministic music rules.

## Current Readiness

Status: **ready for a small v1 hardening slice, not a broad new feature**.

The Explorer already contains a functional Voicing Identifier path:

- `ui/e9-fretboard-explorer.html`
  - visible `Identify a voicing` task card,
  - `Voicing identifier` mode option,
  - `#explorer-voicing-identifier` render surface,
  - copy that says the identifier explains one shape.
- `ui/e9-fretboard-explorer.js`
  - fret selector,
  - string chip selector,
  - individual pedal/lever chips,
  - computed one-row fretboard highlight,
  - selected-detail panel,
  - per-string before/after details,
  - no combined `A+B` / `B+C` preset buttons in the identifier controls.
- `ui/e9-music-rules.js`
  - deterministic pitch resolution,
  - control-change resolution,
  - note spelling,
  - scale/function labeling,
  - `identifyVoicing(...)`,
  - chord quality patterns,
  - partial/omitted-tone labels,
  - confidence labels,
  - dominant/V7 special handling,
  - Chord / Voicing Finder helpers.
- `steel_guitar_rag/fretboard_explorer.py`
  - deterministic Explorer row validation,
  - interval metadata,
  - `classify_inversion(...)`,
  - `voicing_status`,
  - `omitted_intervals`,
  - warnings for partial diminished / partial half-diminished claims.
- `tests/test_frontend_answer_ui.py`
  - focused browser/VM coverage for current Voicing Identifier behavior,
  - coverage for major, minor, partial major 7, partial dominant 7, diminished, V7, E-lower pocket, and 5-7-8 behavior.
- `tests/test_fretboard_explorer.py`
  - backend Explorer metadata coverage for intervals, partial rows, omitted intervals, inversion, and 5-7-8/pocket behavior.

The existing pieces are enough for a useful v1 if the next slice is scoped to contract hardening and UI clarity.

## Audit Answers

### 1. Existing UI affordances for selecting multiple notes

Existing affordances:

- key selector,
- copedent selector,
- `Voicing identifier` Explorer mode,
- fret selector currently limited to frets 1-10 in the visible identifier panel,
- string chips allowing 1-4 selected strings,
- individual pedal/lever control chips,
- clear control button,
- computed single result card,
- one SVG/fretboard marker row,
- selected-detail explanation,
- per-string details.

Important limitation:

- The current UI does not appear to support direct click-to-pick arbitrary notes from the fretboard grid. Selection is parameter-based: fret + selected strings + selected pedals/levers.

That is acceptable for v1. Direct fretboard note picking should be a later UX slice.

### 2. Existing deterministic chord/interval helpers

Existing helpers cover most v1 needs:

- `resolveE9Note(...)` in `ui/e9-music-rules.js`.
- E9 open string and control-change maps.
- grip metadata and grip tiers.
- chord quality definitions:
  - major,
  - minor,
  - dominant 7,
  - major 7,
  - minor 7,
  - dominant 9,
  - major 9,
  - minor 9,
  - minor 7 flat 5,
  - diminished,
  - major 6,
  - minor 6,
  - sus2,
  - sus4,
  - 5/no third.
- omitted-tone labels such as `no3`, `no5`.
- confidence labels.
- selected-key function labels.
- dominant-color / V7 special handling.
- backend row metadata for interval maps, voicing status, omitted intervals, and inversion.

Gap:

- The frontend identifier and backend Explorer row validation are related but not one contract. The frontend identifies arbitrary selected notes; the backend validates generated rows. v1 should define an explicit identifier result shape and test it directly.

### 3. Identification capability

Current capability assessment:

- Major/minor triads: **yes**. Existing tests cover G, C, Am, and F/C function examples.
- Inversions: **partial**. Backend Explorer rows classify inversion for generated rows, but the frontend Voicing Identifier result does not prominently expose inversion as a contract field. v1 should either display inversion when confident or explicitly defer inversion display.
- Partials: **yes, with caveat**. Partial extended voicings and omitted tones are supported, but v1 should standardize labels and avoid saying "chord" without the partial/no-tone qualifier where that matters.
- No-3rd colors: **partial**. The quality pattern includes `5/no third`, and 5-7-8 correctness work prevents plain-major overclaims. v1 needs explicit no-3rd regression tests in Voicing Identifier mode.
- Dominant/6th/add9 colors: **partial to good**. Dominant 7 and 6th qualities exist; 5-7-8/add9/no-3rd behavior exists in backend answer/fretboard logic. v1 needs explicit UI tests for add9/no-3rd and 6th partial labels before claiming broad support.
- Rootless voicings: **limited**. Chord / Voicing Finder has rootless confidence handling for cases such as minor 9 candidates. Voicing Identifier can produce partial/context-dependent labels, but rootless naming should be conservative in v1.

## Guardrails Against Overclaiming

Voicing Identifier v1 should follow these rules:

1. Do not promote a partial to a complete chord.
2. Do not call a shape `major` or `minor` unless the 3rd quality is present.
3. Do not call `1-b3-b5` a full `m7b5`; label it diminished or partial half-diminished color unless b7 is present.
4. Do not treat 9th-string involvement as dominant by itself.
5. Do not treat 5-7-8 open at fret 3 as a full G major grip.
6. Do not show inert pedal/lever labels for selected strings.
7. Do not label rootless voicings as high-confidence complete chords.
8. Do not collapse multiple plausible readings into one unqualified answer.
9. Do not use SGF/forum/source material to justify deterministic identity unless a source specifically supports a teaching concept separately.
10. Do not show source cards for deterministic identifier results.

Recommended confidence labels:

- `high`: complete triad/seventh where required tones are present and label is unambiguous.
- `medium-high`: partial extended voicing with root and 3rd present, missing 5th or other non-defining tone.
- `medium`: partial extended voicing missing root or missing 3rd but still mechanically/musically plausible.
- `low`: ambiguous pitch set, dyad, no 3rd, no root, or no clear common name.

## Multiple Plausible Names

When several chord names are plausible, v1 should show:

- primary label,
- confidence,
- why this label was chosen,
- omitted tones,
- alternate readings,
- context note against selected key.

Recommended learner copy:

- "Best reading in G: D7 color / partial V7."
- "Alternate readings: F6(no5), Bdim."
- "Context matters: this shape is a partial/color grip, not a full four-note chord."

Do not hide alternates when confidence is below `high`.

## Proposed v1 Result Contract

Conceptual frontend/backend-neutral result shape:

```json
{
  "schema_version": "voicing_identifier_v1",
  "input": {
    "key": "G",
    "scale_type": "major",
    "tuning": "E9",
    "copedent_id": "emmons_e9",
    "fret": 3,
    "strings": [5, 7, 8],
    "controls": []
  },
  "computed": {
    "notes": ["D", "A", "G"],
    "notes_with_register": [],
    "intervals_by_candidate": []
  },
  "identity": {
    "label": "G5/add9(no3)",
    "quality": "partial color",
    "root": "G",
    "function": "I color in G",
    "confidence": "medium",
    "voicing_status": "partial",
    "inversion": "partial_or_implied",
    "present_tones": ["1", "5", "9"],
    "omitted_tones": ["3"],
    "alternate_readings": [],
    "warnings": [
      "This is not a full major triad because it omits the 3rd."
    ]
  },
  "display": {
    "summary": "This is a G5/add9 color, not a full G major grip.",
    "why": "The selected strings spell G, D, and A against G: root, 5th, and 9th. Without B, the major 3rd is not present.",
    "per_string": []
  }
}
```

This can remain an internal UI contract first. It does not require a public API route in v1.

## UI Behavior Contract

For v1, the UI should:

- keep fret + strings + pedals/levers as the primary input,
- keep direct fretboard click selection out of scope,
- display notes and per-string details,
- show a single primary identity only when confidence is clear,
- show alternates when confidence is medium or lower,
- show omitted tones in the primary summary for partials,
- show "not enough notes" for one-note selections,
- show "dyad / interval, not a full chord" for two-note selections unless context supports a named shell,
- keep source cards hidden,
- keep result and SVG marker synchronized,
- avoid stale markers when a selection becomes invalid,
- never render `[object Object]`.

Recommended copy changes for the next UI slice:

- Rename "Identified G" style headers to "Best reading" when confidence is below high.
- Add a visible "Complete / partial / ambiguous" badge.
- Add a compact "Why this is not a full chord" warning for no-3rd/no-root cases.

## Test Requirements

Required tests to prevent another 5-7-8 style misclassification:

- `G / fret 3 / strings 5-7-8 / open`:
  - notes `D, A, G`;
  - label must include no-3rd/add9/color semantics;
  - must not identify as full `G major`;
  - must not show A+B or inert controls.
- `G / fret 8 / strings 5-7-8 / E-lower`:
  - notes `G, D, B`;
  - can identify as G major;
  - grip type remains E-lower pocket.
- `G / fret 10 / strings 4-5-6-9 / open`:
  - identifies D7 / V7 in G;
  - dominant label is justified by b7 content.
- `G / fret 3 / strings 5-6-9 / A+B`:
  - Fmaj7(no3), not dominant/V7.
- `G / fret 3 / strings 5-7-9 / A+B`:
  - Fmaj7(no5), not dominant/V7.
- `G / fret 3 / strings 3-5-9 / open`:
  - B diminished or partial color, with 9th-string context warning.
- one-note selection:
  - no chord overclaim.
- two-note selection:
  - dyad/partial wording.
- rootless extended case:
  - confidence is medium/context-dependent and omitted/rootless state is visible.
- invalid fourth/fifth string selection:
  - v1 currently allows up to four strings; attempts beyond that must show a clear warning and preserve the previous valid state.

Checks for future Lane 05/06 implementation:

- `node --check ui/e9-music-rules.js`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py -q` if touched/available.
- local browser smoke for Voicing Identifier mode.
- protected-preview smoke if runtime/static browser files change.

## Smallest Useful Implementation Slice

Recommended next slice: **Voicing Identifier v1 contract hardening**, not a new mode.

Scope:

1. Keep the existing Voicing Identifier UI.
2. Add a small internal result-shape helper around `identifyVoicing(...)`.
3. Add explicit `voicing_status`, `present_tones`, `omitted_tones`, `confidence`, and `alternate_readings` to the rendered identity path.
4. Add no-3rd/add9/color handling for 5-7-8 open G in the frontend identifier path.
5. Add focused tests for the required cases above.
6. Update copy to distinguish "complete", "partial", and "ambiguous."
7. Run local browser smoke.
8. Commit separately.

Do not:

- add direct fretboard note picking,
- add melody input,
- add arbitrary song/solo/tab behavior,
- add backend answer routing,
- add source-card behavior,
- touch corpus or deployment.

## Likely Future Files

Lane 06 / frontend:

- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- possibly `tests/test_explorer_musical_red_team.py`

Lane 05 / backend only if parity is needed:

- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`

Docs:

- `docs/handoffs/task-completions/<new Lane 06 handoff>.md`
- `docs/handoffs/task-completions/integration-status.md` after smoke.

## Recommended Next Implementation Prompt

Lane 06 UX/UI Design:

```text
Use AGENTS.md autopilot mode.

Primary lane: Lane 06 UX/UI Design
Reasoning level: High

Implement Voicing Identifier v1 contract hardening from docs/handoffs/task-completions/2026-07-04-1045-18-voicing-identifier-v1-readiness-audit.md.

Scope:
- Keep the existing E9 Fretboard Explorer Voicing Identifier mode.
- Add or normalize an internal identifier result shape with voicing_status, confidence, present tones, omitted tones, alternate readings, and warnings.
- Make no-3rd/add9/color cases explicit, especially G / fret 3 / strings 5-7-8 / open.
- Preserve valid E-lower 5-7-8 G major at fret 8.
- Preserve D7/V7, Fmaj7(no3), Fmaj7(no5), F7(no5), diminished, dyad, and not-enough-notes behavior.
- Do not add melody input, direct fretboard note picking, song tab, source-card behavior, backend answer routing, corpus work, scraping, embeddings, Chroma/vector changes, auth, DNS, deployment, private transcripts, licensing metadata, secrets, or assets.

Tests:
- node --check ui/e9-music-rules.js
- node --check ui/e9-fretboard-explorer.js
- focused frontend Explorer tests
- local browser smoke for Voicing Identifier mode
- git diff --check

Write a Lane 06 handoff and exact-path commit if green.
```

## Tests And Checks Run

Read/inspection:

- `AGENTS.md`
- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log --oneline -5`
- `git diff --cached --name-only`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-music-rules.js`
- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_fretboard_explorer.py`
- prior Voicing Identifier, Chord / Voicing Finder, shared music-rules, and 5-7-8 handoffs.

Pending after file write:

- `git diff --check`
- exact-path staged diff checks if committing.

Skipped:

- Runtime tests and browser smoke were skipped because this task is docs-only and did not change runtime code.

## Risk Assessment

Risk: low.

Why:

- Docs-only audit.
- No runtime files changed.
- The audit explicitly narrows the next implementation slice and preserves existing behavior boundaries.

Main future risk:

- Voicing names are inherently ambiguous on pedal steel. The implementation must expose confidence, omitted tones, alternates, and context rather than presenting every pitch set as one definitive chord.

Rollback:

- Revert this handoff and any matching integration-status note.

## Human Decision Needed

No for this readiness audit.

Yes before expanding beyond v1 hardening into direct fretboard note picking, backend answer routing, melody input, or source-backed/song-related behavior.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-07-04-1045-18-voicing-identifier-v1-readiness-audit.md`
- `docs/handoffs/task-completions/integration-status.md` if refreshed for this docs-only audit.

## Files That Must Not Be Staged

All unrelated parked files shown by `git status --short`, especially:

- `README.md`
- `corpus_metadata/**`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_*.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- `corpus-private/**`
- `corpus-v2/**`
- Chroma/vector stores
- private/generated/source/license artifacts
- unrelated untracked handoffs/assets

## Recommended Next Lane

Lane 06 UX/UI Design for the scoped Voicing Identifier v1 hardening slice.

## Commit Readiness

Safe to commit after `git diff --check`, exact-path staging, staged diff review, and `git diff --cached --check`.

## Suggested Next Step

Run the recommended Lane 06 prompt above when ready to implement. Do not combine it with Melody Input, Arrangement Assistant, or unrelated Explorer product slices.
