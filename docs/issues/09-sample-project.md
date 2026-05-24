# Issue 9 — Sample project button

**Label:** ready-for-agent  
**Blocked by:** #5  
**User stories:** US 6, 7

## What to build

Bundle a minimal FastAPI todo app (~8 files) under `samples/todo-app/` in the repo. "Try with sample project" button on the upload page POSTs to `/upload-sample`. Server zips the sample folder on-the-fly and runs it through the same pipeline as a regular upload (same session creation, same SSE stream, same preview page).

## Acceptance criteria

- [ ] Sample project files committed under `samples/todo-app/`
- [ ] Button triggers live AI generation (not pre-baked output)
- [ ] Full pipeline runs identically to a user upload
