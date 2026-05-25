# Issue 13 — Progress bar faithful to generation progress

**Label:** ready-for-agent
**Blocked by:** None

## What to build

Fix the progress bar on `generate.html` so it advances proportionally across all sections instead of jumping to 100% when the first section completes.

**Root cause:** `totalSections` is incremented as each `section-start` event fires sequentially, so when section 1 completes, the JS sees `completedCount=1 / totalSections=1 = 100%` even though sections 2–5 haven't started.

**Fix:** Hard-code the expected total per mode in the frontend. Read the mode from the session (already available via template variable or a data attribute on the page) and set `knownTotal` before the SSE stream opens. Calculate progress as `completedCount / knownTotal`.

- Quick mode: 2 sections
- Comprehensive mode: 5 sections

No backend changes required.

## Acceptance criteria

- [ ] Comprehensive mode: bar reaches ~20% after section 1 completes, ~40% after section 2, ~60% after section 3, ~80% after section 4, 100% on `done`
- [ ] Quick mode: bar reaches ~50% after section 1 completes, 100% on `done`
- [ ] Bar reaches 100% when the `done` SSE event fires (existing behaviour preserved)
- [ ] No backend routes or `generator.py` changes
- [ ] All 74 existing tests still pass

## Blocked by

None — can start immediately.
