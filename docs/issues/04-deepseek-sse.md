# Issue 4 — DeepSeek client + SSE streaming (README only)

**Label:** ready-for-agent  
**Blocked by:** #3  
**User stories:** US 8, 9, 10

## What to build

`GET /stream/<session_id>` endpoint that streams a `text/event-stream` response. For this slice: call DeepSeek for the README section only, stream tokens as `data:` SSE events. Frontend uses HTMX SSE extension to display tokens in real time in the README section card.

API key loaded from `DEEPSEEK_API_KEY` env var via `python-dotenv`. Use `httpx` async client with `stream=True` against DeepSeek's OpenAI-compatible endpoint.

## Acceptance criteria

- [ ] `GET /stream/<session_id>` returns `Content-Type: text/event-stream`
- [ ] README tokens appear character-by-character in the browser
- [ ] HTMX SSE extension wired up correctly (`hx-ext="sse"`, `sse-connect`, `sse-swap`)
- [ ] API key read from env, never hardcoded
