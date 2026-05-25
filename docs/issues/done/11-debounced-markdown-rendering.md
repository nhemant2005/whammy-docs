# Issue 11 — Debounced markdown rendering on generate and regenerate pages

**Label:** done
**Blocked by:** None

## What to build

Replace per-token `marked.parse()` calls with a debounced ~400ms batch render on both the generation page (`generate.html`) and the regenerate SSE handler (`preview.html`).

On `generate.html`: tokens accumulate in `sectionBuffers` as today, but the re-render fires on a 400ms interval rather than on every `message` event. The interval is cleared and a final render fires immediately when `section-complete` arrives.

On `preview.html` `regenSection()`: the same debounce pattern replaces the current per-token `marked.parse(accumulated)` call.

This eliminates flickering broken partial-markdown (dangling code fences, half-formed headers) that the user currently sees during streaming.

## Acceptance criteria

- [x] `generate.html`: section card content re-renders at most once every ~400ms during streaming
- [x] `preview.html` `regenSection()`: accumulated markdown re-renders at most once every ~400ms
- [x] Markdown is always structurally sound at each render — no dangling code blocks or half-headers visible mid-stream
- [x] Final render fires immediately when `section-complete` / `done` event fires (no 400ms lag on completion)
- [x] All 74 existing tests still pass

## Work notes

- `generate.html`: added `sectionTimers` map; each `message` event clears+resets a 400ms `setTimeout` for the active section; `section-complete` clears the timer and renders immediately before marking done.
- `preview.html` `regenSection()`: added local `renderTimer`; same debounce on `message`; `done` clears timer and renders immediately, then re-enables the button.
- No backend changes required.

## Follow-up change (post-QA)

Debounce approach replaced with **render-on-complete only** after QA found that even batched partial markdown is jarring to users.

- `generate.html`: removed `sectionTimers`, removed `renderSection()`. `message` events now buffer silently into `sectionBuffers` with no rendering. Pulsing skeleton replaces "Waiting for tokens…" placeholder. Full `marked.parse()` fires once on `section-complete`.
- `preview.html` `regenSection()`: removed `renderTimer`. `message` events buffer into `accumulated` with no rendering. Section rendered at `opacity-30` during streaming as a loading signal. Full render fires once on `done`, opacity restored.
- 74 tests still pass.
- Root cause of "plain text on generate page": `generate.html` had no explicit prose CSS and relied on Tailwind CDN's typography plugin, which does not apply to content injected via `innerHTML` at runtime. Fixed by adding the same `.prose` `<style>` block that `preview.html` already had.

## Follow-up change (generate page removed)

`generate.html` and the intermediate `/generate/{session_id}` step were removed from the user-facing flow. Upload now redirects directly to `/preview/{session_id}`.

The render-on-complete SSE logic that lived in `generate.html` was moved into `preview.html` as a `generating` mode, gated by a Jinja `generating` variable set by the server when no docs exist yet. Behaviour is identical: tokens buffer silently in `sectionBuffers`, `marked.parse()` fires once on `section-complete`. The `generate.html` template and the `/generate/` route remain in the codebase but are no longer part of the normal flow.
