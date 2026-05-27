# Answer API Contract

The frontend answer UI talks to the backend retrieval/RAG layer through two JSON endpoints:

- `GET /api/search`
- `POST /api/answer`

This contract is for The Turnaround UI and the local backend API. The API reads from existing retrieval indexes only. It must not run SGF scraping, rebuild embeddings, reset vector stores, or mutate source corpus files.

## Shared Types

Backend shared type definitions live in `pocketsteel/api_contract.py`.

### AnswerMode

`AnswerMode` is one of:

```json
"ask" | "gear" | "copedent" | "tab" | "practice"
```

Unknown modes are normalized to `ask`.

### SearchResult

`SearchResult` is the canonical retrieval result returned by `/api/search` and consumed internally by `/api/answer`.

Required fields:

- `score`: number from `0` to `1`, higher is stronger
- `excerpt`: short source text excerpt safe for display
- `source_system`: source system ID, such as `sgf_phpbb_current`
- `forum_name`: display forum name
- `thread_title`: source thread title
- `thread_url`: canonical source thread URL
- `chunk_id`: retrieval chunk ID
- `post_uid`: source post ID when available
- `source_kind`: source type, such as `forum_post`
- `forum_id`: current phpBB forum ID when available
- `legacy_forum_number`: legacy UBB forum number when available
- `thread_id`: current phpBB thread ID when available
- `legacy_thread_uid`: legacy UBB thread ID when available
- `thread_category`: source category label
- `thread_quality_score`: numeric quality score or `null`
- `chunk_index`: numeric chunk index or `null`
- `warnings`: per-result metadata fallback warnings

### SourceCitation

`SourceCitation` is the smaller source card shape returned by `/api/answer` for frontend display.

Required fields:

- `title`
- `forumName`
- `url`
- `excerpt`
- `score`
- `chunkId`
- `postUid`

The answer UI also accepts older snake_case aliases while normalizing live responses, but the backend should emit this canonical citation shape.

### AnswerResponse

`AnswerResponse` is the canonical response from `/api/answer`.

Required fields:

- `answer`: source-grounded answer text
- `mode`: `AnswerMode`
- `sources`: `SourceCitation[]`
- `warnings`: response-level warnings
- `sections`: display sections derived from the answer text

## GET /api/search

Request:

```text
GET /api/search?q=why+does+touching+the+changer+reduce+hum
```

Response:

```json
{
  "query": "why does touching the changer reduce hum",
  "results": [
    {
      "score": 0.8125,
      "excerpt": "Touching the changer can change the ground reference, so check the cable, jack, pickup ground, volume pedal, and amp input before replacing parts.",
      "source_system": "sgf_phpbb_current",
      "forum_name": "Electronics",
      "thread_title": "Grounding a pedal steel",
      "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=123",
      "chunk_id": "sgf_phpbb_current:electronics:123:0",
      "post_uid": "p12345",
      "source_kind": "forum_post",
      "forum_id": "11",
      "legacy_forum_number": "",
      "thread_id": "123",
      "legacy_thread_uid": "",
      "thread_category": "Electronics",
      "thread_quality_score": 0.92,
      "chunk_index": 0,
      "warnings": []
    }
  ],
  "warnings": []
}
```

Empty or whitespace-only search queries return `200 OK` with no results:

```json
{
  "query": "",
  "results": [],
  "warnings": []
}
```

## POST /api/answer

Request:

```http
POST /api/answer
Content-Type: application/json
```

```json
{
  "question": "Why does touching the changer reduce hum?",
  "mode": "gear",
  "topK": 6,
  "sourceSystem": "sgf_phpbb_current",
  "forumName": "Electronics"
}
```

Required request field:

- `question`

Optional request fields:

- `mode`: `AnswerMode`, defaults to `ask`
- `topK`: retrieval count, clamped by the backend
- `sourceSystem`: source-system filter
- `forumName`: forum-name filter

Response:

```json
{
  "answer": "The retrieved forum sources point to a grounding or signal-chain issue. Start by bypassing the volume pedal, trying a known-good cable, and checking whether the hum changes when you touch the strings, changer, jack plate, and amp chassis. [1]",
  "mode": "gear",
  "sources": [
    {
      "title": "Grounding a pedal steel",
      "forumName": "Electronics",
      "url": "https://bb.steelguitarforum.com/viewtopic.php?t=123",
      "excerpt": "Touching the changer can change the ground reference, so check the cable, jack, pickup ground, volume pedal, and amp input before replacing parts.",
      "score": 0.8125,
      "chunkId": "sgf_phpbb_current:electronics:123:0",
      "postUid": "p12345"
    }
  ],
  "warnings": [],
  "sections": [
    {
      "title": "Answer",
      "style": "lead",
      "body": "The retrieved forum sources point to a grounding or signal-chain issue. Start by bypassing the volume pedal, trying a known-good cable, and checking whether the hum changes when you touch the strings, changer, jack plate, and amp chassis. [1]"
    }
  ]
}
```

If retrieval finds no strong source match, `/api/answer` still returns `200 OK` with an explanatory answer, an empty `sources` array, and a warning:

```json
{
  "answer": "No strong source match found in the current corpus for that question.",
  "mode": "ask",
  "sources": [],
  "warnings": ["no strong source match"],
  "sections": [
    {
      "title": "Answer",
      "style": "lead",
      "body": "No strong source match found in the current corpus for that question."
    }
  ]
}
```

Validation errors return `400 Bad Request`:

```json
{
  "error": "question is required"
}
```

## Fixture

`tests/fixtures/api_contract_mock_response.json` contains mock `/api/search` and `/api/answer` payloads that match this contract.
