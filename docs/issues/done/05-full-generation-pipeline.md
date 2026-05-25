# Issue 5 — Full generation pipeline: all sections + mode routing + redirect

**Label:** done  
**Blocked by:** #4  
**User stories:** US 11, 12, 13, 15, 16, 18, 28

## What to build

Extend the SSE stream to generate all sections sequentially. Read `mode` from `session.json` — Comprehensive generates all 5 sections (README → API Reference → Architecture → Getting Started → Deployment), Quick generates 2 (README → API Reference). Emit `event: section-start` and `event: section-complete` named events around each section. Apply skeleton extraction (see tiers below). Use section-specific prompts. After all sections complete, emit `event: done` and trigger a client-side redirect to the preview page. Handle DeepSeek API failures with a visible error state and retry option.

**Skeleton extraction tiers:**
- < 5KB → full content
- 5–20KB → function/class signatures + docstrings only
- > 20KB → filename + first 30 lines

## Acceptance criteria

- [x] Comprehensive mode generates exactly 5 sections; Quick generates exactly 2
- [x] `section-start` event fires before each section with the section name as data
- [x] Skeleton extraction applied for files above thresholds
- [x] `event: done` fires after last section and redirects browser to `/preview/<session_id>`
- [x] DeepSeek failure shows a retry button, does not crash the stream

## Bug fix — SSE newline stripping

`message` tokens were embedded in the SSE body as bare strings: `data: {token}\n\n`. When a token contained a literal `\n` (e.g. at the end of a markdown line), the newline terminated the SSE `data:` field early and was silently dropped by the browser's EventSource parser. The accumulated buffer in JS had all newlines stripped, so `marked.parse()` received a single line of text and could not recognise headers, lists, or code fences — everything rendered as plain text.

**Fix:** `main.py`'s `/stream/{session_id}` event generator now wraps `message` tokens with `json.dumps()` before embedding: `data: {json.dumps(data)}\n\n`. The JS accumulator calls `JSON.parse(e.data)` to recover the string including its newlines. Named events (`section-start`, `section-complete`, `done`, `gen-error`) are unaffected — they carry only plain keys, never freeform text.
