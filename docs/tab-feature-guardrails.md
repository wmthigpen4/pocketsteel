# Tab Feature Guardrails

Steel Guitar RAG may use tablature to teach songs, commercial recordings, artist solos, and complete copyrighted arrangements. Copyright status alone is never a refusal reason. The first version focuses on accurate, attributable, sectioned teaching.

## Allowed First-Version Uses

- Generate short original educational examples.
- Explain pasted user-provided tab.
- Show intervals and chord functions.
- Show pedal and lever usage.
- Show alternate positions.
- Check whether a combination is likely impossible on a given copedent.
- Work with public-domain songs.
- Help users practice a technique without copying a copyrighted arrangement.

## Accuracy And Source Requirements

- Full note-for-note tablature is allowed when the recording/passage is identified or the user supplies the material.
- Reconstructing commercial lesson material.
- Recreating a named artist's complete recorded solo.
- Using private lesson transcripts to output public tab.
- Claiming exactness when the source material is uncertain.

## Tab Answer Layout

Sections:

- What the phrase is doing.
- Mechanics.
- Intervals.
- Pedal and lever usage.
- Alternate positions.
- If this is impossible on your guitar.
- Sources.

## Pasted Tab Explanation Shape

```json
{
  "answer_type": "tab_phrase_explainer",
  "input_kind": "user_pasted_tab",
  "sections": [
    {"title": "What the phrase is doing", "body": "This moves from the I chord to a IV sound through a pedal change."},
    {"title": "Mechanics", "bullets": ["Pick strings 5 and 6.", "Engage A and B after the attack.", "Release cleanly before moving."]},
    {"title": "Intervals", "body": "The top note moves from the 5th to the 6th scale degree."},
    {"title": "Alternate positions", "body": "You can also try the same sound two frets up with a different grip."}
  ],
  "tab_examples": [
    {
      "kind": "short_original_example",
      "tuning": "E9",
      "rights_status": "original_educational_example",
      "lines": ["3 ______", "4 __3F__", "5 __3A__"]
    }
  ]
}
```

## Public-Domain Song Shape

```json
{
  "song_title": "Amazing Grace",
  "rights_status": "public_domain",
  "purpose": "short educational example",
  "max_length": "short excerpt"
}
```

## Impossible Combination Checks

When a copedent is known, the system can warn:

- "Your saved setup does not show that lever."
- "This would require raising and lowering the same string at the same time."
- "This tab assumes a change you have not saved."

If the copedent is unknown, say so plainly.

## UI Components

First UI pass:

- Monospace tab block.
- Interval badges.
- Pedal/lever badges.
- "Why this works" text.
- "Try another position" follow-up.

Later UI pass:

- Static neck frames.
- Optional audio/playback.
- User-editable tab input.

## Teaching Copy

When source material is missing, ask for it without using copyright refusal language:

"I can teach the full song or solo on E9. Send the recording/link, passage, notes, or tab and name the version and section so I can label the result as an exact transcription, E9 adaptation, or teaching simplification."
