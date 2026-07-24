# 2026-06-27 11:38 - Lane 18 - Copedent Naming Cleanup Contract

## Pass / Warn / Fail

Warn.

The product contract is complete as a docs-only Lane 18 artifact. The runtime model is usable, but naming drift remains a monetization and user-trust risk until implementation separates stable IDs, mechanical names, player shorthand, physical positions, and per-string action descriptions.

## Branch And HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `3b9cdb9`
- Final HEAD / commit hash if committed: pending at handoff creation; report after exact-path docs commit.
- Task type: docs-only product/architecture contract.
- Lane: `18 Product / Architecture`.
- Task mode: GREEN for this report only.

## Task Summary

Requested: define a copedent naming cleanup contract for the E9 Fretboard Explorer after the Lane 18 musical product audit identified naming drift between current app labels (`E-raise`, `E-lower`, `D-lower`, `G-lower`) and player/product shorthand (`F`, `E`, `G+`, `G-`, `D-`, `D--`, `V`, `B-to-Bb`).

Completed:

- Inspected repo guidance, integration status, the Lane 18 audit, copedent models, Explorer payload generation, Explorer UI rendering, generated Explorer data, and focused tests.
- Defined canonical naming layers and control-specific rules.
- Defined what Emmons, Day, Custom E9 with LKV, and future My Copedent may claim.
- Recommended next implementation and QA scope.

Intentionally not changed:

- No backend implementation.
- No UI implementation.
- No tests.
- No auth, DNS, deployment, scraping, embeddings, Chroma/vector stores, corpus, private transcripts, source records, secrets, or visual assets.

## Files Inspected

- `AGENTS.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-27-1110-18-fretboard-musical-product-audit.md`
- `steel_guitar_rag/e9_copedents.py`
- `steel_guitar_rag/fretboard_explorer.py`
- `steel_guitar_rag/user_copedent.py`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`

## Current Naming Problems

The current implementation correctly models useful E9 controls, but several fields are carrying multiple meanings:

- `id` values such as `E-raise`, `E-lower`, `D-lower`, and `G-lower` are used as stable IDs, UI labels, serialized payload values, and row mechanics.
- Player shorthand such as `F lever`, `E lever`, `D-`, `D--`, `G+`, `G-`, and `V` is not consistently represented as a separate alias layer.
- `G-lower` is misleading as a learner-facing label because the current app-default profile combines string 1 `F# -> G` with string 6 `G# -> F#`. That is one represented app control, but the label describes only the lower.
- `D-lower` can mean string 2 half-stop, string 2 full-stop, string 9 lower, or a combined 2/9 lower depending on profile and travel. The current default profile represents string 2 `D# -> D` plus string 9 `D -> C#`; Custom has both half and full states.
- `B-to-Bb`, `V`, `vertical`, `LKV`, and `vertical/Bb` refer to the same family but should not all become stable serialized IDs.
- Emmons and Day differ mainly in physical pedal order, not in named A/B/C semantics; copy must not imply that A/B/C note changes differ.
- Custom E9 with LKV exposes user-specific controls. It must not pollute the standard Emmons profile, public source claims, or "standard E9" copy.
- Future `My Copedent (E9)` must not be described as generating user-profile positions until row generation, note finding, chord finding, and answer guidance actually use the selected user profile.

## Canonical Naming Layers

Every control should have separate fields for these concepts:

1. `id`
   - Stable internal serialization key.
   - Used in payloads, tests, saved settings, answer contracts, tab events, and profile references.
   - Must not change casually after release.
   - Should be machine-oriented and profile-neutral where possible.
2. `mechanicalName`
   - What the control does mechanically, such as `E-to-F raise` or `B-to-Bb lower`.
   - Must be derived from string actions, not player slang.
3. `displayName`
   - Primary UI label for the selected profile.
   - Should be short but not misleading.
4. `playerShorthand`
   - Optional common shorthand, such as `F lever`, `E lever`, `D-`, `D--`, `G+`, `G-`, `V`.
   - Must be shown as alias/context, not as the sole source of truth.
5. `physicalPosition`
   - Physical location such as `P1`, `P2`, `P3`, `LKL`, `LKR`, `LKV`, `RKL`, `RKR`.
   - Must be profile-specific.
6. `travel`
   - Optional state such as `full`, `half-stop`, `full-stop`, `vertical`, `double-stop`.
   - Required when one physical control has multiple travel states.
7. `stringActions`
   - Authoritative per-string mechanics.
   - Required for every control.
   - Example shape:

```json
{
  "string": 4,
  "from": "E",
  "to": "F",
  "semitones": 1,
  "direction": "raise"
}
```

## Canonical Internal ID Rules

### Stable ID Principles

- Pedals remain `A`, `B`, and `C`.
- Mechanical E raise remains `E-raise` as the stable ID.
- Mechanical E lower remains `E-lower` as the stable ID.
- Half-stop/full-stop controls must not collapse into one ID if they produce different notes.
- IDs should represent the app's modeled control state, not every possible player nickname.
- Backward-compatible aliases may be accepted at input boundaries, but payloads should emit canonical IDs.

### Recommended Canonical IDs

For standard Emmons/Day app profiles:

| Canonical ID | Control Type | Mechanical Name | Primary Display | Player Shorthand / Alias |
| --- | --- | --- | --- | --- |
| `A` | pedal | B-to-C# raise on strings 5 and 10 | A pedal | A |
| `B` | pedal | G#-to-A raise on strings 3 and 6 | B pedal | B |
| `C` | pedal | E-to-F# and B-to-C# raise on strings 4 and 5 | C pedal | C |
| `E-raise` | lever | E-to-F raise on strings 4 and 8 | E raise (F lever) | F, F lever |
| `E-lower` | lever | E-to-Eb/D# lower on strings 4 and 8 | E lower | E, E lever, E-lower |
| `D-lower-half` | lever/travel state | D#-to-D on string 2; optional string 9 D-to-C# if profile includes it | D lower half-stop | D-, D half-stop |
| `D-lower-full` | lever/travel state | D#-to-C# on string 2; optional string 9 D-to-C# if profile includes it | D lower full-stop | D--, D full-stop |
| `G-raise` | lever/travel state | F#-to-G raise family, commonly string 1 and sometimes string 2/7 by profile | G raise | G+ |
| `G-lower` | lever/travel state | G#-to-F# or G#-to-G lower family by profile | G lower | G- |
| `B-to-Bb` | lever | B-to-Bb/A# lower on strings 5 and 10 | B-to-Bb vertical | V, vertical, LKV |

Compatibility note:

- Existing payloads currently emit `D-lower`, `RKL-half`, `G-lower`, and `RKR-full`. A migration can support these as legacy aliases while moving to explicit half/full IDs.
- If implementation chooses not to rename IDs in the first code slice, it must at least add explicit alias/display/mechanical fields so the UI stops relying on IDs as copy.

## User-Facing Label Rules

Labels should be learner-readable and mechanically explicit.

- Use `A pedal`, `B pedal`, `C pedal` for named pedals.
- Use `E raise (F lever)` for the E-to-F control when the profile uses standard F-lever shorthand.
- Use `E lower` for the E-to-Eb/D# control.
- Use `D lower half-stop` and `D lower full-stop` when travel is known.
- Use `G raise` and `G lower` separately when they are separate actions.
- Use `RKL half-stop` or `RKL full-stop` only as physical/travel context, not as the musical name.
- Use `B-to-Bb vertical` for the vertical lever, with `V` as shorthand if the UI needs compact chips.

Compact chips may use shorthand only if tooltip/detail text gives the mechanical action:

- Chip: `F`
  - Tooltip/detail: `E raise: strings 4 and 8 E -> F`.
- Chip: `E`
  - Tooltip/detail: `E lower: strings 4 and 8 E -> Eb/D#`.
- Chip: `D-`
  - Tooltip/detail: `D lower half-stop: string 2 D# -> D; string 9 D -> C# on this profile`.
- Chip: `D--`
  - Tooltip/detail: `D lower full-stop: string 2 D# -> C#; string 9 D -> C# on this profile`.
- Chip: `G+`
  - Tooltip/detail: `G raise: string 1 F# -> G on this profile`.
- Chip: `G-`
  - Tooltip/detail: `G lower: string 6 G# -> F# on this profile`.
- Chip: `V`
  - Tooltip/detail: `B-to-Bb vertical: strings 5 and 10 B -> Bb/A#`.

## Mechanical Description Rules

The app should make string actions the source of truth.

Required display patterns:

- Copedent chart cells: `B -> C#`, `E -> F`, `E -> Eb/D#`, `F# -> G`, `G# -> F#`.
- Impact preview header: primary display name plus affected strings.
- Impact preview detail: one row per affected string.
- Voicing/note finder detail: if a selected control does not affect a string, say `no change`.
- Any control with mixed directions, such as the current `G-lower` profile control, must show both actions before using shorthand.

Forbidden patterns:

- Do not describe a mixed raise/lower control only as `G-lower`.
- Do not say `D-lower` without half/full context when the distinction matters.
- Do not expose raw implementation IDs as the only learner-facing text.
- Do not imply that physical knee labels are universal.

## Emmons And Day Rules

Emmons and Day should preserve named pedal semantics:

- `A` always means strings 5 and 10 B -> C#.
- `B` always means strings 3 and 6 G# -> A.
- `C` always means string 4 E -> F# and string 5 B -> C#.

Physical pedal order is profile-specific:

- Emmons display order: `A`, `B`, `C` as `P1`, `P2`, `P3`.
- Day display order: `C`, `B`, `A` as `P1`, `P2`, `P3`.

UI copy:

- Correct: `Day E9 changes pedal order, not named A/B/C musical changes.`
- Correct: `A pedal (P3 on Day): strings 5 and 10 B -> C#.`
- Incorrect: `Day A pedal does a different change.`

Answer/fretboard/tab payloads should serialize named pedals as `A`, `B`, `C`; physical location can be included separately when the selected profile is Day.

## Custom E9 With LKV Rules

`Custom E9 (with LKV)` is an app-supported profile, not the default standard.

Rules:

- It may expose `B-to-Bb` / `V` / `LKV` because this profile includes that vertical.
- It may expose half/full travel states from the user-specific profile, including RKL and RKR states.
- It must not add `B-to-Bb` to Emmons or Day payloads.
- It must not imply that all Emmons guitars have LKV.
- It must not cite private/user-specific copedent data as public source evidence.
- It must display per-string changes because Custom has profile-specific behaviors such as string 7 not raising on RKL/RKLL.

Recommended naming for current Custom rows:

| Current ID | Recommended Display | Recommended Alias | Required Detail |
| --- | --- | --- | --- |
| `B-to-Bb` | B-to-Bb vertical | V / LKV | strings 5 and 10 B -> Bb/A# |
| `RKL-half` | RKL half-stop | G raise / partial RKL | string 1 F# -> G; string 6 G# -> G |
| `G-lower` | RKL full-stop / G lower | G- / RKLL | string 1 F# -> G; string 6 G# -> F# |
| `D-lower` | D lower half-stop | D- / RKR | string 2 D# -> D; string 9 D -> C# |
| `RKR-full` | D lower full-stop | D-- / RKRR | string 2 D# -> C#; string 9 D -> C# |

The mixed RKL full-stop case should not be presented only as `G-lower`; it is more accurate as `RKL full-stop / G lower`, with explicit string actions.

## Future My Copedent Rules

`My Copedent (E9)` remains disabled until user-profile data drives actual logic.

The app must not claim:

- `Your exact copedent drives every generated position.`
- `Chord Finder uses your guitar.`
- `All tab/fretboard output adapts to your setup.`
- `Your custom changes are included in answer guidance.`

The app may claim before full implementation:

- `My Copedent (E9) is coming soon in Backstage.`
- `This chart shows the selected app-supported setup.`
- `Copedents vary; check the string-action chart against your guitar.`

Minimum criteria before enabling:

- User profile can serialize controls with stable IDs, physical positions, travel, string actions, display names, aliases, and warnings.
- Pitch engine uses selected user profile for note finding.
- Chord/voicing finder uses selected user profile for candidate generation.
- Explorer generated rows either regenerate from the selected profile or clearly mark unavailable/standard-only rows.
- Answer payloads and tab events carry selected profile metadata.
- QA has fixtures for at least one non-standard profile.

## UI Copy Examples

Selector/helper:

```text
Choose the copedent that matches your guitar.
Emmons and Day mainly differ in pedal order.
Copedents vary; this chart shows the setup currently used for guidance.
```

Day pedal chart:

```text
A pedal (P3 on Day): strings 5 and 10 B -> C#.
```

E raise:

```text
E raise (F lever): strings 4 and 8 E -> F.
```

E lower:

```text
E lower: strings 4 and 8 E -> Eb/D#.
```

D lower half/full:

```text
D lower half-stop: string 2 D# -> D; string 9 D -> C# on this profile.
D lower full-stop: string 2 D# -> C#; string 9 D -> C# on this profile.
```

Mixed G control:

```text
RKL full-stop / G lower: string 1 F# -> G; string 6 G# -> F#.
This control has mixed string actions, so check the chart before using shorthand.
```

Vertical:

```text
B-to-Bb vertical (V): strings 5 and 10 B -> Bb/A#.
```

Standard-only warning:

```text
This row is generated from the app's standard E9 rules. Custom copedent row generation is not enabled yet.
```

## Test Cases Required

Backend/data tests:

- Emmons payload includes `A`, `B`, `C`, `E-raise`, `E-lower`, explicit D-lower half-state, and explicit G raise/lower action metadata.
- Emmons payload does not include `B-to-Bb`.
- Day payload orders pedals as `C`, `B`, `A` but keeps `A` string actions as 5/10 B -> C#.
- Custom LKV payload includes `B-to-Bb` and does not alter Emmons defaults.
- Any control with mixed raise/lower actions includes all per-string actions and a warning/description field.
- Half-stop/full-stop controls serialize distinct IDs or distinct `travel` values.
- Legacy aliases still parse if backwards compatibility is required.

Frontend tests:

- Copedent chart displays primary names, physical positions, and per-string string-action cells.
- Impact preview uses display labels but details show actual string actions.
- Note finder control chips either use clear labels or shorthand with tooltip/detail text.
- Voicing identifier control chips do not rely on raw IDs alone.
- No `[object Object]`.
- No `G-lower`-only copy for mixed RKL full-stop behavior.
- No `D-lower`-only copy when half/full stop distinction appears.

QA/browser smoke:

- Emmons chart: no `B-to-Bb`.
- Day chart: `C/B/A` physical order and stable named A/B/C mechanics.
- Custom chart: LKV visible and RKL/RKR half/full states understandable.
- Mobile chart remains readable or horizontally scrollable.
- Switching copedents does not imply generated custom rows unless implemented.

## Implementation Recommendations

### Recommended Lane 05 Slice

Implement a normalized copedent-control contract in `steel_guitar_rag/e9_copedents.py`.

Exact scope:

- Add fields equivalent to `display_name`, `mechanical_name`, `player_shorthand`, `aliases`, `travel`, and `string_actions`.
- Keep current canonical IDs stable for the first migration unless tests and UI can migrate safely.
- Add explicit half/full metadata for D/RKR and RKL cases.
- Add warnings/notes for mixed-direction controls.
- Update payload tests without changing Explorer musical behavior.
- Do not change row generation, answer routing, corpus, Chroma, auth, deployment, or source records.

Suggested prompt:

```text
Lane 05 Backend / RAG Integration: Implement the copedent naming cleanup data contract from docs/handoffs/task-completions/2026-06-27-1138-18-copedent-naming-cleanup-contract.md. Keep runtime musical behavior unchanged. Add display/mechanical/shorthand/travel/string-action fields to E9 copedent payloads, preserve A/B/C semantics for Emmons and Day, keep B-to-Bb only in Custom E9 with LKV, and add focused tests for mixed G control and D half/full naming. Do not touch UI rendering, answer routing, corpus, Chroma, auth, DNS, deployment, scraping, embeddings, or source records.
```

### Recommended Lane 06 Slice

After Lane 05 payload fields exist, update Explorer UI labels.

Exact scope:

- Render display names and shorthand separately.
- Add tooltip/detail copy for compact shorthand chips.
- Make mixed controls visibly string-action-first.
- Preserve current layout and behavior.
- Add focused frontend tests and local browser smoke.

Suggested prompt:

```text
Lane 06 UX/UI Design: Consume the normalized copedent naming payload from Lane 05 and update the E9 Fretboard Explorer chart, impact preview, note finder, voicing identifier, and chord finder controls so labels distinguish display name, shorthand, physical position, and string actions. Do not change music rules. Verify Emmons, Day, and Custom E9 with LKV; no raw IDs as sole learner-facing copy; no [object Object].
```

## Risks And Blockers

Risks:

- Renaming stable IDs directly could break existing Explorer data, tests, answer payloads, tab events, or saved URLs. Prefer additive fields first.
- Leaving current labels unchanged risks paid/custom-copedent copy overclaiming precision.
- Player shorthand varies by guitar and player; string actions must remain the source of truth.
- Custom E9 currently uses private/user-specific source data and must not be presented as public source evidence.

Blockers:

- No blocker for the docs contract.
- Implementation should wait for a deliberate Lane 05 payload/data slice.
- Paid `My Copedent` claims are blocked until generated rows, note finding, chord finding, answer guidance, and tab events use user-profile data.

## Checks Run

Commands run before editing:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git diff --cached --name-only
```

Commands to run before commit:

```bash
git diff --check
git diff --cached --name-only
git diff --cached --check
```

Results at handoff creation:

- `git status --short`: broad unrelated dirty/untracked files remain parked.
- `git branch --show-current`: `feature/answer-api`.
- `git rev-parse --short HEAD`: `3b9cdb9`.
- `git diff --cached --name-only`: empty before this handoff was staged.

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-27-1138-18-copedent-naming-cleanup-contract.md`

No implementation, UI, test, corpus, deployment, auth, DNS, source, secret, or asset files changed.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-27-1138-18-copedent-naming-cleanup-contract.md`

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

## Human Decision Needed

No for this contract.

Yes before implementation if the team wants to rename existing stable IDs instead of adding compatibility fields. The recommended path is additive fields first.

## Recommended Next Lane

Lane 05 Backend / RAG Integration for the normalized copedent naming payload/data slice.

## Commit Readiness

Safe to commit as an exact-path docs-only handoff after `git diff --check`, cached-name review, cached diff review, and `git diff --cached --check`.

## Suggested Next Step

Run the Lane 05 implementation prompt above, then Lane 06 UI consumption, then Lane 15 focused QA/browser smoke.
