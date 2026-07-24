# 08 Smoke Test Playbook

## Local API Smoke Expectations

Use local API smoke for backend-only checks, but label it clearly as API fallback if browser behavior is not tested.

Typical local answer request:

```bash
curl -sS \
  -X POST http://127.0.0.1:8770/api/answer \
  -H "Content-Type: application/json" \
  -H "X-Steel-Rag-Dev-Access-Role: beta_user" \
  --data '{"question":"Show me a G to C move"}'
```

Expected:

- HTTP 200 for authorized local smoke,
- deterministic answers source-free where appropriate,
- tab payload only for safe movement/sequence prompts,
- fretboard payload for static positions,
- no raw SGF/forum fragments in primary answer text.

## Local Browser Smoke Expectations

Use a local same-origin server when UI behavior matters:

```text
http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=<cachebuster>
```

Expected:

- app shell loads,
- Q&A input unlocks through local scaffold access,
- fretboard cards and filters behave in the DOM,
- tab cards preserve fixed-width monospace spacing,
- source cards do not dominate deterministic answers,
- console has no relevant errors.

## Protected-Preview Smoke Expectations

Protected-preview smoke must record an explicit Smoke Target block:

- target type,
- exact browser URL tested,
- cache-busted URL,
- auth required,
- Cloudflare Access login result,
- expected git HEAD,
- `/api/version` result when available,
- root URL behavior,
- `/ui/steel-guitar-rag-mock.html` behavior,
- API fallback status.

API fallback does not prove protected-preview browser behavior.

## Cloudflare Access Caveats

- Test only after Cloudflare Access login succeeds.
- Record whether Q&A unlocks.
- Record whether root `/` works or redirects.
- Use the exact cache-busted URL from the current handoff.
- Do not infer protected-preview behavior from `127.0.0.1`.

## Cache-Bust Direct UI Pattern

Use:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<slice-or-commit>
```

Root may also be used when the task explicitly targets root:

```text
https://app.steelguitarrag.com/?v=<slice-or-commit>
```

Do not say only "test app.steelguitarrag.com" when a specific path is required.

## Common Test Prompts

### Static Grip

- `Show me a G major grip.`
- `Show me a 4-5-6 grip.`
- `Where is G on E9?`

Expected: fretboard-first, no tab by default.

### Movement Tab

- `Show me a G to C move.`
- `How do I use A+B pedals?`
- `Show me an E-lower move.`
- `Give me a beginner lick in G.`

Expected: direct prose plus deterministic tab and matching fretboard when supported.

### Negative / Copyright

- `Give me the full tab for a modern copyrighted song.`
- `Tab the whole solo from Together Again.`
- `Transcribe this YouTube recording into tab.`

Expected: no generated full-song tab, no solo transcription, safe alternative offered.

### Non-Tab Gear Question

- `What are good Fender Steel King settings?`
- `Why does my amp buzz at idle?`

Expected: no stale tab/fretboard payload; source-backed answer is allowed when relevant.

## Standard Checks

Run the checks relevant to the touched surface:

```bash
git diff --check
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m py_compile steel_guitar_rag/tab_engine.py steel_guitar_rag/api.py steel_guitar_rag/answer_tab_examples.py
.venv/bin/python -m pytest tests/test_tab_engine.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
.venv/bin/python -m pytest tests/test_api_search.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
```

Do not run deployment, protected-preview restart, scraping, embeddings, Chroma rebuilds, or auth/DNS changes unless the task explicitly names that lane and action.
