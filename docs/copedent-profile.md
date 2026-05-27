# Copedent Profile

Steel Guitar RAG should eventually tailor answers to a logged-in player’s actual guitar setup. The first UI scaffold lives in Backstage → My Setup / Copedent and saves a local browser draft only. It does not connect to auth, billing, profile storage, or answer generation yet.

## UX Scope

- Create, view, edit, and save one local copedent profile draft.
- Start from common templates: E9 10-string, C6 10-string, 12-string Universal, 12-string Extended E9, 12-string Extended C6, or Other / Custom.
- Let custom setups feel normal, not exceptional.
- Model pedals and levers as controls with one or more string changes.
- Allow half-stops, splits, optional changes, and notes.
- Provide a “Don’t see your setup?” request area that can be connected to feedback later.

## Draft Data Shape

```ts
export interface CopedentProfile {
  id: string;
  userId: string | null;
  name: string;
  tuningFamily: "E9" | "C6" | "Universal" | "Extended" | "Other";
  stringCount: number;
  templateKey?: string;
  guitar?: string;
  strings: StringDefinition[];
  controls: ControlDefinition[];
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface StringDefinition {
  stringNumber: number;
  openNote: string;
  gauge?: string;
  notes?: string;
}

export interface ControlDefinition {
  id: string;
  label: string;
  type: "pedal" | "knee_lever" | "vertical" | "other";
  side?: "left" | "right";
  position?: string;
  changes: StringChange[];
}

export interface StringChange {
  stringNumber: number;
  fromNote: string;
  toNote: string;
  direction: "raise" | "lower";
  amount?: string;
  isHalfStop?: boolean;
  isSplit?: boolean;
  changeType?: "raise" | "lower" | "half-stop" | "split" | "optional";
  notes?: string;
}
```

## Future RAG Context Injection

When account storage exists, answer generation should load the active `CopedentProfile` for the signed-in user and include a compact summary in the answer prompt/context.

Example context block:

```text
User copedent profile:
- Setup: Cory's main E9
- Family: E9, 10 strings
- Open tuning: 1 F#, 2 D#, 3 G#, 4 E, 5 B, 6 G#, 7 F#, 8 E, 9 D, 10 B
- Controls:
  - A pedal: 5 B→C#, 10 B→C#
  - B pedal: 3 G#→A, 6 G#→A
  - RKL: 6 G#→F# lowered
```

Future answer behavior:

- “On your E9 setup, your RKL lowers string 6 from G# to F#…”
- “Since your C6 setup has this change on P5…”
- “Your guitar does not appear to have that change saved.”

Guardrails:

- Do not infer unsaved changes as if they are present.
- If the profile is incomplete, say what is missing.
- Keep source-grounded retrieval separate from user-profile personalization.
- The copedent profile should guide explanation and applicability, not replace retrieved evidence.
