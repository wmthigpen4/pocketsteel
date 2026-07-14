# Melody Studio copedent-transfer rule contract

## Runtime contract

Melody Studio separates a reviewed player's physical execution from the musical decision being learned:

1. Decode source tab with `sourceCopedentId`.
2. Store control actions as string, starting pitch, destination pitch, and semitone change.
3. Learn and rank abstract choices such as texture, phrase role, pocket continuity, voice leading, sustain, release, and repick.
4. Enumerate candidates only from `targetCopedentId` or the validated saved E9 profile sent by the client.
5. Validate every sounding pitch, preserve the melody's exact register as the highest voice, and render the target profile's labels.

The source and target IDs must remain distinct in imported events and output routes. A source control letter is never treated as proof of a target control's effect.

## Source profile

`source-e9-abc-defg-v1` is the reviewed decoding profile for the supplied photograph collection:

| Control | Exact changes |
| --- | --- |
| A | strings 5 and 10, B to C# |
| B | strings 3 and 6, G# to A |
| C | string 4, E to F#; string 5, B to C# |
| D | string 2 only, D# to D |
| E | strings 4 and 8, E to Eb |
| F | strings 4 and 8, E to F |
| G | strings 1 and 7, F# to G |

This profile is source-only. It is not shown as a normal app choice and does not modify the app default or a saved user profile.

## Hard constraints

- Preserve exact melody pitch and register.
- Keep that melody pitch at the top of every sounding grip.
- Use one fret per event until slants are explicitly supported.
- Reject unknown, inert, or mechanically impossible controls.
- Validate all sounding and sustained strings when a control is engaged or released.
- Keep tab, score, fretboard, and playback on the same event-level mechanical pitches.

## Control transfer

Controls map by mechanical effect on protected strings. Protected strings are all sounding or sustained voices during the action.

- A differently named target control is valid when its per-string semitone effects match on every protected string.
- Extra target effects are valid only on strings outside the protected set.
- An identically named control with a different required effect is invalid.
- A source G raise on string 7 cannot map to a target lever that raises string 1 and lowers string 6.

## Ordered fallback

1. Find the same pitch and harmonic function in another target position.
2. Preserve melody and texture with a different target grip.
3. Reduce three voices to two, then one, without changing the melody pitch.
4. Report that the original technique needs a capability absent from the target profile.

Fallback is explicit in the rule contract and must never become a label-only lever substitution.

## One-, two-, and three-voice preferences

- One voice is favored for pickups, fast motion, non-chord tension, and passing notes.
- Two voices are favored for sustained singing support, thirds or sixths, and vocal-steel continuity.
- Three voices are favored for chord arrivals, resolutions, and cadences when the target copedent has a mechanically valid grip.

These are soft preferences. Exact melody and mechanical validity always win.

## Style families

The versioned ranker supports `auto`, `vocal_steel`, `chord_melody`, `harmonized`, `single_note_run`, `lever_driven`, and `fixed_pocket`. Style changes candidate ranking, not pitch validity or copedent mechanics.

The runtime's checked-in seed policy is `melody-decision-ranker-v1`. Reviewed private annotations can train updated copedent-neutral weights through `scripts/train_melody_decision_ranker.py`. Training features exclude source control letters, literal tab, copyrighted passage text, and profile-specific fret identities.

## Rule record fields

Every maintained hard constraint or learned preference records:

- stable rule ID;
- musical context and phrase role;
- hard constraint or soft preference;
- source evidence and style families;
- abstract intent;
- required capabilities;
- transfer behavior;
- fallback behavior;
- confidence;
- model version.

The runtime emits this contract with each Melody Studio exercise so an arrangement can be audited against the model version and selected style.

## Privacy boundary

Reviewed decisions and trained model artifacts live under ignored `corpus-private/melody-decisions/`. They are not RAG documents, Chroma records, source cards, public fixtures, or public answer text. Public code contains only the abstract schema, deterministic mechanics, reviewed rule contract, and tests using invented musical examples.
