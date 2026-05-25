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
