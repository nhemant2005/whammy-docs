# Issue 5 — Full generation pipeline: all sections + mode routing + redirect

**Label:** ready-for-agent  
**Blocked by:** #4  
**User stories:** US 11, 12, 13, 15, 16, 18, 28

## What to build

Extend the SSE stream to generate all sections sequentially. Read `mode` from `session.json` — Comprehensive generates all 5 sections (README → API Reference → Architecture → Getting Started → Deployment), Quick generates 2 (README → API Reference). Emit `event: section-start` and `event: section-complete` named events around each section. Apply skeleton extraction (see tiers below). Use section-specific prompts. After all sections complete, emit `event: done` and trigger a client-side redirect to the preview page. Handle DeepSeek API failures with a visible error state and retry option.

**Skeleton extraction tiers:**
- < 5KB → full content
- 5–20KB → function/class signatures + docstrings only
- > 20KB → filename + first 30 lines

## Acceptance criteria

- [ ] Comprehensive mode generates exactly 5 sections; Quick generates exactly 2
- [ ] `section-start` event fires before each section with the section name as data
- [ ] Skeleton extraction applied for files above thresholds
- [ ] `event: done` fires after last section and redirects browser to `/preview/<session_id>`
- [ ] DeepSeek failure shows a retry button, does not crash the stream
