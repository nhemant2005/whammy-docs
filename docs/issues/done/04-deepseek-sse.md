# Issue 4 — DeepSeek client + SSE streaming (README only)

**Label:** done  
**Blocked by:** #3  
**User stories:** US 8, 9, 10

## What to build

`GET /stream/<session_id>` endpoint that streams a `text/event-stream` response. For this slice: call DeepSeek for the README section only, stream tokens as `data:` SSE events. Frontend uses HTMX SSE extension to display tokens in real time in the README section card.

API key loaded from `DEEPSEEK_API_KEY` env var via `python-dotenv`. Use `httpx` async client with `stream=True` against DeepSeek's OpenAI-compatible endpoint.

## Acceptance criteria

- [x] `GET /stream/<session_id>` returns `Content-Type: text/event-stream`
- [x] README tokens appear character-by-character in the browser
- [x] HTMX SSE extension wired up correctly (`hx-ext="sse"`, `sse-connect`, `sse-swap`)
- [x] API key read from env, never hardcoded

## Work done

**Files created/modified:**
- `generator.py` — `stream_readme(session_dir)` async generator; httpx streaming call to DeepSeek OpenAI-compatible endpoint; parses `data:` SSE lines; yields text deltas; API key from `DEEPSEEK_API_KEY` env var via `python-dotenv`
- `main.py` — added `GET /generate/{session_id}` (serves generate.html); `GET /stream/{session_id}` (StreamingResponse text/event-stream, wraps tokens as `data:` events, 404 for unknown session); imports `StreamingResponse` and `stream_readme`
- `templates/generate.html` — HTMX 1.9 + SSE extension CDN; `sse-connect="/stream/{{ session_id }}"`, `sse-swap="message"`; marked.js renders accumulated markdown; done badge on `[DONE]` event
- `tests/test_generator.py` — 5 behavioral tests: content-type, data-line format, HTML page, sse-connect attr, 404 unknown session; DeepSeek API mocked via `patch("main.stream_readme")`

**Commit:** 38b62cd
