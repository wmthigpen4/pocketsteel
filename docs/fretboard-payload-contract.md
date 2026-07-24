# Fretboard Payload Contract

This document defines the MVP `response.fretboard` contract for Steel Guitar RAG answer responses. It is a product and architecture contract only. Backend generation, UI rendering changes, and validation code are separate implementation tasks.

The contract lets the answer layer describe musical intent while the UI owns fretboard geometry. The backend sends frets, strings, grips, controls, and display labels. The UI calculates all SVG/grid coordinates.

## Current Repo Conventions

Existing answer responses may already include `payload["fretboard"]` from `steel_guitar_rag/api.py`.

Current lightweight shapes found in the repo:

- `steel_guitar_rag/fretboard_examples.py`: returns `title`, `description`, and `highlights`.
- `steel_guitar_rag/api_contract.py`: defines `FretboardPayload` with `title`, optional `description`, and `highlights`.
- `ui/answer-client.js`: normalizes `title`, `description`, `maxFret`, `stringCount`, `tuningLabels`, and `highlights`.
- `tests/test_fretboard_examples.py`: validates stable IDs such as `g-open-3`, `g-af-6`, and `g-ab-10`.
- `tests/test_frontend_answer_ui.py`: mocks response-level `fretboard` payloads.

This contract promotes the existing `highlights` concept into a stable `positions` contract. During migration, the backend may emit both `positions` and legacy `highlights`, or the UI may adapt `positions` into existing highlight options.

## Contract Summary

`response.fretboard` is optional. When present, it describes one static E9 teaching diagram.

Required for MVP rendering:

- `type`
- `title`
- `tuning`
- `strings`
- `positions`

Optional but recommended:

- `subtitle`
- `copedent`
- `key`
- `legend`
- `notes`
- `warnings`
- `sourceContext`

The MVP supports only:

- `tuning: "E9"`
- `strings.count: 10`
- frets `0` through `24`
- string numbers `1` through `10`, where string `1` is top/highest and string `10` is bottom/lowest
- static positions, grips, pedals, levers, note labels, and interval labels

## Top-Level Shape

```json
{
  "fretboard": {
    "type": "e9-fretboard-diagram",
    "title": "G major positions",
    "subtitle": "Three common E9 locations for a G chord.",
    "tuning": "E9",
    "copedent": {
      "id": "mvp-e9-standard",
      "label": "MVP standard 10-string E9",
      "status": "assumed"
    },
    "key": "G",
    "strings": {
      "count": 10,
      "labels": {
        "1": "F#",
        "2": "D#",
        "3": "G#",
        "4": "E",
        "5": "B",
        "6": "G#",
        "7": "F#",
        "8": "E",
        "9": "D",
        "10": "B"
      }
    },
    "positions": [],
    "legend": [],
    "notes": [],
    "warnings": [],
    "sourceContext": []
  }
}
```

## Field Definitions

### `type`

Required string. MVP value:

```json
"e9-fretboard-diagram"
```

The UI should ignore unknown fretboard types and show the text answer normally.

### `title`

Required string. Human-readable diagram title, such as `G major positions`.

If missing, the UI may render the fallback title `Fretboard view`, but contract validation should treat it as invalid for backend-produced MVP payloads.

### `subtitle`

Optional string. Short explanation shown near the diagram.

If missing, the UI should render no subtitle.

### `tuning`

Required string. MVP value:

```json
"E9"
```

If another tuning is sent, the UI should not attempt to adapt the geometry. It should hide the fretboard or show a non-blocking fallback message.

### `copedent`

Optional object. Describes the setup assumption behind the positions.

Recommended fields:

- `id`: stable identifier, such as `mvp-e9-standard` or `user-profile`
- `label`: display label
- `status`: one of `assumed`, `user-profile`, `unknown`, or `draft`

For MVP, the backend should not invent custom copedent changes. If the setup is unknown, use:

```json
{
  "id": "mvp-e9-standard",
  "label": "MVP standard 10-string E9",
  "status": "assumed"
}
```

### `key`

Optional string. Musical key or center, such as `G` or `C`.

If missing, the UI should still render positions.

### `strings`

Required object.

Required fields:

- `count`: must be `10` for MVP

Optional fields:

- `labels`: map of string number strings to open-note labels

If `labels` is missing, the UI should use its default E9 open string labels. If `count` is not `10`, the UI should reject the diagram for MVP.

### `positions`

Required non-empty array of position objects. This replaces guessing from prose.

Each position describes one musical location or grip. Multiple positions in one payload represent alternate places to play the same musical idea.

### `legend`

Optional array of legend items. The UI may also render a default legend when omitted.

Recommended shape:

```json
{
  "id": "primary",
  "label": "Primary position",
  "color": "primary",
  "description": "Start here first."
}
```

### `notes`

Optional array of plain strings for diagram-level teaching notes.

Use this for non-positional explanation, not source citations.

### `warnings`

Optional array of plain strings for safe fallback warnings.

Examples:

- `This diagram assumes standard 10-string E9.`
- `No slants are represented in this MVP diagram.`

### `sourceContext`

Optional array of lightweight references connecting the diagram to answer evidence or rules.

Recommended fields:

- `kind`: `rule`, `source`, or `answer`
- `label`: short display label
- `sourceId`: optional stable ID
- `url`: optional URL

Do not put raw transcript text, private metadata, licensing dumps, or corpus records in this field.

## Position Object

Required fields:

- `id`
- `label`
- `fret`
- `strings`
- `grip`
- `pedals`
- `levers`
- `color`

Optional fields:

- `role`
- `notes`
- `intervals`
- `bar`
- `warnings`
- `explanation`
- `sourceContext`

Example:

```json
{
  "id": "g-ab-10",
  "label": "G major",
  "fret": 10,
  "strings": [4, 5, 6],
  "grip": "4-5-6",
  "pedals": ["A", "B"],
  "levers": [],
  "color": "secondary",
  "role": "A+B position",
  "notes": {
    "4": "B",
    "5": "G",
    "6": "D"
  },
  "intervals": {
    "4": "3",
    "5": "1",
    "6": "5"
  },
  "explanation": "A+B at fret 10 gives another G major position on strings 4-5-6."
}
```

### `id`

Required stable string unique within `positions`.

Use deterministic IDs based on musical intent, not array order. Existing repo examples use IDs such as:

- `g-open-3`
- `g-af-6`
- `g-ab-10`

### `label`

Required string. Human-readable musical label, such as `G major`.

### `fret`

Required integer. Must be `0` through `24` for MVP.

The backend must not send raw `x` coordinates. The UI calculates position from `fret`.

### `strings`

Required array of integers. Each value must be `1` through `10`.

The backend must not send raw `y` coordinates. The UI calculates position from string number.

### `grip`

Required string. Human-readable grip label, usually the hyphenated version of `strings`, such as `4-5-6`.

For MVP, `grip` should match `strings` unless a future teaching convention needs a friendlier label.

### `pedals`

Required array of strings. Empty array means no pedals.

MVP canonical pedal names:

- `A`
- `B`
- `C`

### `levers`

Required array of strings. Empty array means no levers.

MVP canonical lever names for the user's E9 setup:

| Canonical | Meaning |
| --- | --- |
| `F` | E raises |
| `E` | E lowers |
| `G+` | strings 1 and 2 raise |
| `G-` | string 6 lower |
| `D-` | string 2 half-step lower and 9 lower |
| `D--` | string 2 full-step lower |
| `V` | strings 5 and 10 A-to-Bb vertical |

Existing repo seed data currently uses older display labels. Recommended migration mapping:

| Existing label | Canonical contract label |
| --- | --- |
| `E-raise/F` | `F` |
| `E-lower` | `E` |
| `6-lower` | `G-` |
| `2/9-lower` | `D-` |
| `vertical/Bb` | `V` |

The backend should emit canonical labels. The UI may temporarily accept existing labels during migration, but new fixtures should use canonical labels.

### `color`

Required string role, not a raw CSS value.

Allowed MVP values:

- `primary`
- `secondary`
- `alternate`
- `reference`
- `warning`

The UI owns actual colors.

### `role`

Optional string. Short teaching role for the position, such as `Open position`, `A+F position`, or `A+B position`.

This maps to the existing legacy `highlights[].role` field and is useful for labels, legends, and screen-reader summaries. If omitted, the UI should derive a simple role from pedals/levers or only show `label`.

### `notes`

Optional object mapping string numbers to note labels.

Keys must be stringified string numbers from the `strings` array. Values should be short note names, such as `G`, `B`, or `D`.

If omitted, the UI should render markers without note labels.

### `intervals`

Optional object mapping string numbers to interval labels.

Keys must be stringified string numbers from the `strings` array. Values should be short interval labels, such as `1`, `3`, `5`, `b7`, or `6`.

If omitted, the UI should render markers without interval labels.

### `bar`

Optional object. MVP should omit it unless there is a warning.

Allowed MVP shape:

```json
{
  "type": "straight",
  "warning": "Slants are not represented in the MVP fretboard."
}
```

Do not use this field to implement slants yet.

### `warnings`

Optional array of strings for position-level caveats.

Example:

```json
["Assumes the F lever raises both E strings."]
```

### `explanation`

Optional string. One short sentence explaining the position.

### `sourceContext`

Optional array using the same shape as top-level `sourceContext`, scoped to this position.

## Validation Rules

Backend validation should enforce:

- `response.fretboard` is optional, but if present it must be an object.
- `type` must be `e9-fretboard-diagram`.
- `tuning` must be `E9`.
- `strings.count` must be `10`.
- `positions` must contain at least one item.
- `positions[].id` must be stable and unique within the diagram.
- `positions[].fret` must be an integer from `0` through `24`.
- `positions[].strings` must contain integers from `1` through `10`.
- `positions[].strings` should be unique.
- `positions[].grip` should match the strings, such as `[4, 5, 6]` -> `4-5-6`.
- `positions[].pedals` must use known pedal names: `A`, `B`, `C`.
- `positions[].levers` must use known lever names: `F`, `E`, `G+`, `G-`, `D-`, `D--`, `V`.
- `positions[].color` must be a known role, not an arbitrary color token.
- `positions[].notes` keys must correspond to strings in that position.
- `positions[].intervals` keys must correspond to strings in that position.
- Standard positions must not include raw `x`, `y`, pixel, SVG, or CSS coordinate fields.
- Fret markers should not be sent unless a future override field is explicitly added.

UI fallback behavior:

- Missing optional fields should not block rendering.
- Missing `notes` or `intervals`: render markers and labels without those annotations.
- Missing `legend`: render a default legend from the distinct `color`, pedal, and lever roles.
- Missing `subtitle`, `notes`, `warnings`, or `sourceContext`: omit those sections.
- Invalid required fields: hide the fretboard and preserve the text answer.
- Unknown `type`, tuning, string count, pedals, levers, or out-of-range fret/string values: reject the diagram for MVP.

## JSON Schema Proposal

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://steelguitarrag.com/schemas/fretboard-payload-mvp.schema.json",
  "title": "Steel Guitar RAG response.fretboard MVP",
  "type": "object",
  "additionalProperties": false,
  "required": ["type", "title", "tuning", "strings", "positions"],
  "properties": {
    "type": { "const": "e9-fretboard-diagram" },
    "title": { "type": "string", "minLength": 1 },
    "subtitle": { "type": "string" },
    "tuning": { "const": "E9" },
    "copedent": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "label", "status"],
      "properties": {
        "id": { "type": "string", "minLength": 1 },
        "label": { "type": "string", "minLength": 1 },
        "status": {
          "type": "string",
          "enum": ["assumed", "user-profile", "unknown", "draft"]
        }
      }
    },
    "key": { "type": "string", "minLength": 1 },
    "strings": {
      "type": "object",
      "additionalProperties": false,
      "required": ["count"],
      "properties": {
        "count": { "const": 10 },
        "labels": {
          "type": "object",
          "additionalProperties": { "type": "string", "minLength": 1 },
          "propertyNames": { "pattern": "^(10|[1-9])$" }
        }
      }
    },
    "positions": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "label", "fret", "strings", "grip", "pedals", "levers", "color"],
        "properties": {
          "id": { "type": "string", "minLength": 1 },
          "label": { "type": "string", "minLength": 1 },
          "fret": { "type": "integer", "minimum": 0, "maximum": 24 },
          "strings": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": true,
            "items": { "type": "integer", "minimum": 1, "maximum": 10 }
          },
          "grip": { "type": "string", "minLength": 1 },
          "pedals": {
            "type": "array",
            "items": { "type": "string", "enum": ["A", "B", "C"] }
          },
          "levers": {
            "type": "array",
            "items": { "type": "string", "enum": ["F", "E", "G+", "G-", "D-", "D--", "V"] }
          },
          "color": {
            "type": "string",
            "enum": ["primary", "secondary", "alternate", "reference", "warning"]
          },
          "role": { "type": "string" },
          "notes": {
            "type": "object",
            "additionalProperties": { "type": "string", "minLength": 1 },
            "propertyNames": { "pattern": "^(10|[1-9])$" }
          },
          "intervals": {
            "type": "object",
            "additionalProperties": { "type": "string", "minLength": 1 },
            "propertyNames": { "pattern": "^(10|[1-9])$" }
          },
          "bar": {
            "type": "object",
            "additionalProperties": false,
            "required": ["type"],
            "properties": {
              "type": { "const": "straight" },
              "warning": { "type": "string" }
            }
          },
          "warnings": {
            "type": "array",
            "items": { "type": "string" }
          },
          "explanation": { "type": "string" },
          "sourceContext": {
            "type": "array",
            "items": { "$ref": "#/$defs/sourceContextItem" }
          }
        }
      }
    },
    "legend": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "label"],
        "properties": {
          "id": { "type": "string", "minLength": 1 },
          "label": { "type": "string", "minLength": 1 },
          "color": {
            "type": "string",
            "enum": ["primary", "secondary", "alternate", "reference", "warning"]
          },
          "description": { "type": "string" }
        }
      }
    },
    "notes": {
      "type": "array",
      "items": { "type": "string" }
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" }
    },
    "sourceContext": {
      "type": "array",
      "items": { "$ref": "#/$defs/sourceContextItem" }
    }
  },
  "$defs": {
    "sourceContextItem": {
      "type": "object",
      "additionalProperties": false,
      "required": ["kind", "label"],
      "properties": {
        "kind": { "type": "string", "enum": ["rule", "source", "answer"] },
        "label": { "type": "string", "minLength": 1 },
        "sourceId": { "type": "string" },
        "url": { "type": "string" }
      }
    }
  }
}
```

The schema cannot express every cross-field rule, such as `notes` keys matching `strings`; implementation should add those checks in code.

## Sample Payload A: G Major Positions

Question: `Where can I play a G chord?`

Important MVP convention: `A+F` is fret `6` for this G example, and `A+B` is fret `10`.

```json
{
  "type": "e9-fretboard-diagram",
  "title": "G major positions",
  "subtitle": "Three common E9 locations for a G chord.",
  "tuning": "E9",
  "copedent": {
    "id": "mvp-e9-standard",
    "label": "MVP standard 10-string E9",
    "status": "assumed"
  },
  "key": "G",
  "strings": {
    "count": 10,
    "labels": {
      "1": "F#",
      "2": "D#",
      "3": "G#",
      "4": "E",
      "5": "B",
      "6": "G#",
      "7": "F#",
      "8": "E",
      "9": "D",
      "10": "B"
    }
  },
  "positions": [
    {
      "id": "g-open-3",
      "label": "G major",
      "fret": 3,
      "strings": [4, 5, 6],
      "grip": "4-5-6",
      "pedals": [],
      "levers": [],
      "color": "primary",
      "role": "Open position",
      "notes": {
        "4": "G",
        "5": "D",
        "6": "B"
      },
      "intervals": {
        "4": "1",
        "5": "5",
        "6": "3"
      },
      "explanation": "No-pedal fret 3 gives a G major grip on strings 4-5-6."
    },
    {
      "id": "g-af-6",
      "label": "G major",
      "fret": 6,
      "strings": [4, 5, 6],
      "grip": "4-5-6",
      "pedals": ["A"],
      "levers": ["F"],
      "color": "secondary",
      "role": "A+F position",
      "notes": {
        "4": "B",
        "5": "G",
        "6": "D"
      },
      "intervals": {
        "4": "3",
        "5": "1",
        "6": "5"
      },
      "explanation": "A+F at fret 6 gives another G major position on strings 4-5-6."
    },
    {
      "id": "g-ab-10",
      "label": "G major",
      "fret": 10,
      "strings": [4, 5, 6],
      "grip": "4-5-6",
      "pedals": ["A", "B"],
      "levers": [],
      "color": "alternate",
      "role": "A+B position",
      "notes": {
        "4": "B",
        "5": "G",
        "6": "D"
      },
      "intervals": {
        "4": "3",
        "5": "1",
        "6": "5"
      },
      "explanation": "A+B at fret 10 gives another G major position on strings 4-5-6."
    }
  ],
  "legend": [
    {
      "id": "primary",
      "label": "Open/no-pedal position",
      "color": "primary",
      "description": "A straight-bar position without pedals or levers."
    },
    {
      "id": "secondary",
      "label": "A+F position",
      "color": "secondary",
      "description": "A pedal plus F lever."
    },
    {
      "id": "alternate",
      "label": "A+B position",
      "color": "alternate",
      "description": "A and B pedals together."
    }
  ],
  "notes": [
    "String 1 is the top/highest string; string 10 is the bottom/lowest string.",
    "Fret markers are supplied by the UI, not by this payload."
  ],
  "warnings": [
    "This diagram assumes standard 10-string E9."
  ],
  "sourceContext": [
    {
      "kind": "rule",
      "label": "MVP deterministic E9 major-position rule",
      "sourceId": "steel_guitar_rag.fretboard_examples.major_positions"
    }
  ]
}
```

## Sample Payload B: C Major Positions

Question: `Where can I play a C chord?`

This sample follows the existing repo's deterministic `major_positions` pattern. It is safe as an MVP contract example, but QA should still verify any note/interval labels before promoting it to a musical gold fixture.

```json
{
  "type": "e9-fretboard-diagram",
  "title": "C major positions",
  "subtitle": "Three common E9 locations for a C chord.",
  "tuning": "E9",
  "copedent": {
    "id": "mvp-e9-standard",
    "label": "MVP standard 10-string E9",
    "status": "assumed"
  },
  "key": "C",
  "strings": {
    "count": 10
  },
  "positions": [
    {
      "id": "c-open-8",
      "label": "C major",
      "fret": 8,
      "strings": [4, 5, 6],
      "grip": "4-5-6",
      "pedals": [],
      "levers": [],
      "color": "primary",
      "role": "Open position",
      "notes": {
        "4": "C",
        "5": "G",
        "6": "E"
      },
      "intervals": {
        "4": "1",
        "5": "5",
        "6": "3"
      },
      "explanation": "No-pedal fret 8 gives a C major grip on strings 4-5-6."
    },
    {
      "id": "c-af-11",
      "label": "C major",
      "fret": 11,
      "strings": [4, 5, 6],
      "grip": "4-5-6",
      "pedals": ["A"],
      "levers": ["F"],
      "color": "secondary",
      "role": "A+F position",
      "notes": {
        "4": "E",
        "5": "C",
        "6": "G"
      },
      "intervals": {
        "4": "3",
        "5": "1",
        "6": "5"
      },
      "explanation": "A+F at fret 11 gives another C major position on strings 4-5-6."
    },
    {
      "id": "c-ab-3",
      "label": "C major",
      "fret": 3,
      "strings": [4, 5, 6],
      "grip": "4-5-6",
      "pedals": ["A", "B"],
      "levers": [],
      "color": "alternate",
      "role": "A+B position",
      "notes": {
        "4": "G",
        "5": "C",
        "6": "E"
      },
      "intervals": {
        "4": "5",
        "5": "1",
        "6": "3"
      },
      "explanation": "A+B at fret 3 gives another C major position on strings 4-5-6."
    }
  ],
  "legend": [
    {
      "id": "primary",
      "label": "Open/no-pedal position",
      "color": "primary"
    },
    {
      "id": "secondary",
      "label": "A+F position",
      "color": "secondary"
    },
    {
      "id": "alternate",
      "label": "A+B position",
      "color": "alternate"
    }
  ],
  "warnings": [
    "This diagram assumes standard 10-string E9."
  ]
}
```

## Sample Payload C: Single-Position Answer

Question: `Show A+B at fret 10 for G major.`

```json
{
  "type": "e9-fretboard-diagram",
  "title": "G major at fret 10",
  "subtitle": "A+B position on strings 4-5-6.",
  "tuning": "E9",
  "copedent": {
    "id": "mvp-e9-standard",
    "label": "MVP standard 10-string E9",
    "status": "assumed"
  },
  "key": "G",
  "strings": {
    "count": 10
  },
  "positions": [
    {
      "id": "g-ab-10",
      "label": "G major",
      "fret": 10,
      "strings": [4, 5, 6],
      "grip": "4-5-6",
      "pedals": ["A", "B"],
      "levers": [],
      "color": "primary",
      "role": "A+B position",
      "notes": {
        "4": "B",
        "5": "G",
        "6": "D"
      },
      "intervals": {
        "4": "3",
        "5": "1",
        "6": "5"
      },
      "explanation": "A+B at fret 10 gives G major on strings 4-5-6."
    }
  ],
  "legend": [
    {
      "id": "primary",
      "label": "Selected position",
      "color": "primary"
    }
  ],
  "notes": [
    "The UI calculates marker positions from fret 10 and strings 4, 5, and 6."
  ]
}
```

## Legacy Highlight Compatibility

Existing UI code consumes:

```json
{
  "title": "G major positions on E9",
  "description": "Common places to find G major.",
  "maxFret": 24,
  "stringCount": 10,
  "tuningLabels": ["F#", "D#", "G#", "E", "B", "G#", "F#", "E", "D", "B"],
  "highlights": [
    {
      "id": "g-open-3",
      "label": "G major",
      "fret": 3,
      "strings": [4, 5, 6],
      "pedals": [],
      "levers": [],
      "role": "Open position"
    }
  ]
}
```

Recommended migration:

1. Backend/rules layer emits the new `positions` contract for known E9 cases.
2. Backend may temporarily include derived `highlights` for the current UI.
3. UI consumes `positions` directly and stops guessing from older `highlights`.
4. QA adds fixture-based evals for accepted payloads.
5. Remove legacy `highlights` only after tests cover the new contract end to end.

## Non-Goals For MVP

- No automatic tab generation.
- No arbitrary melody rendering.
- No bar slants unless explicitly supported by a later contract.
- No LLM-invented copedent changes.
- No raw pixel, SVG, or CSS positions from the backend.
- No live audio.
- No full chord engine.
- No custom copedent reasoning in this contract.
- No fret-marker overrides from the backend.

## Recommended Implementation Sequence

1. Backend/rules layer produces this contract for known E9 cases.
2. UI consumes `positions` without guessing musical intent.
3. QA adds fixture-based evals for G major, C major, and single-position answers.
4. API contract types are updated after fixtures are accepted.
5. Later: expand note/interval calculation and lesson-backed examples.
6. Later: add user-profile copedent support under a versioned contract.

## Open Questions

- Should `description` remain as a legacy alias for `subtitle`, or should new payloads use only `subtitle`?
- Should `positions` replace `highlights` in one change, or should both be emitted during a migration window?
- Should `notes` and `intervals` be backend-provided only for curated examples, or computed later by a rules engine?
- Should the canonical lever labels be displayed exactly as `F`, `E`, `G+`, `G-`, `D-`, `D--`, and `V`, or should the UI translate them into longer teaching labels?
- Should C major sample positions become QA gold fixtures immediately, or remain documentation examples until a musician review pass?
