# Issue 8 — Per-section regenerate

**Label:** ready-for-agent  
**Blocked by:** #7  
**User stories:** US 24, 25, 26

## What to build

[Regenerate with AI] on a section card opens a new SSE connection scoped to that section only. Server reads `mapping.json` for that section's files, calls DeepSeek with streaming, pipes tokens into the target section card via HTMX (`hx-target="#section-<name>"`). Other cards are untouched. On completion, server writes new content to disk and clears the `edited` flag for that section in `session.json`.

## Acceptance criteria

- [x] Regenerating one section does not alter any other section card in the DOM
- [x] Tokens stream in real time into the target section card
- [x] New content written to disk after regeneration completes
- [x] `edited` flag cleared for the regenerated section in `session.json`

## Bug fix — SSE newline stripping (same root cause as Issue 5)

The `/regenerate/{session_id}/{section_key}` endpoint had the same encoding bug: `message` tokens were written as `data: {token}\n\n`, causing any `\n` within a token to terminate the SSE field and be dropped. The `regenSection()` accumulator in `preview.html` received stripped text, and `marked.parse()` could not render structure.

**Fix:** Same as Issue 5 — `json.dumps()` on the server, `JSON.parse(e.data)` in the `regenSection()` message listener in `preview.html`.
