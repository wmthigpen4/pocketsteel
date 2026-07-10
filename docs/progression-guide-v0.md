# Progression Guide v0

Progression Guide v0 is a deterministic E9 answer contract for static chord-route teaching. It can support a section of a song or arrangement, but it does not use SGF/forum retrieval to choose frets, strings, pedals, or levers.

## Route Ownership

- Static chord locations and grips remain fretboard-first.
- Tab examples remain reserved for movement over time: licks, slides, pedal choreography, releases, fills, and short exercises.
- Progression Guide routes are deterministic educational routes. They may be used inside a song or copyrighted arrangement when the route matches the requested harmony; copyright status is not a refusal gate.

## Response Shape

`/api/answer` may return:

```json
{
  "answer": "...",
  "sources": [],
  "warnings": [],
  "progression_guide": {
    "type": "e9-progression-guide-v0",
    "key": "C",
    "progression": "I-IV-V-I",
    "recommendedRouteId": "c-i-iv-v-i-home-pocket",
    "recommendedRoute": {},
    "routes": []
  },
  "fretboard": {
    "type": "e9-fretboard-diagram",
    "positions": []
  }
}
```

`progression_guide.routes[].events[]` must reference renderable fretboard positions by `renderablePositionId`. The matching `fretboard.positions[]` payload remains the primary SVG contract.

## Current Deterministic Coverage

- C I-IV-V-I home-pocket route: C at fret 8, F at fret 8 A+B, G at fret 10 A+B, C at fret 8.
- C I-IV-V-I alternatives: ascending same-grip, pedals-down, and dominant-shell route.
- C diatonic home-pocket route: C, Am, Em, F, Dm, G7 shell, C.
- G I-IV-V-I home-pocket route: G at fret 3, C at fret 3 A+B, D at fret 5 A+B, G at fret 3.
- G I-IV-V-I pedals-down alternate.
- V7-to-I shell resolution in C or G.

## Guardrails

- Song, arrangement, recording, and whole-solo requests route to Melody Exercise teaching. Progression Guide may supply validated harmonic sections, while transcription accuracy and source identity remain owned by the Melody Exercise contract.
- Source cards are suppressed for deterministic progression answers.
- `tab_example` is not attached for Progression Guide answers by default.
- Two-chord movement prompts such as "Show me a G to C move" remain owned by the tab/movement engine.
