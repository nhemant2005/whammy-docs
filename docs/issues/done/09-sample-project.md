# Issue 9 — Sample project button

**Label:** done  
**Blocked by:** #5  
**User stories:** US 6, 7

## What to build

Bundle a minimal FastAPI todo app (~8 files) under `samples/todo-app/` in the repo. "Try with sample project" button on the upload page POSTs to `/upload-sample`. Server zips the sample folder on-the-fly and runs it through the same pipeline as a regular upload (same session creation, same SSE stream, same preview page).

## Acceptance criteria

- [x] Sample project files committed under `samples/todo-app/`
- [x] Button triggers live AI generation (not pre-baked output)
- [x] Full pipeline runs identically to a user upload

## Work notes

- 8 files: `main.py`, `schemas.py`, `database.py`, `config.py`, `requirements.txt`, `README.md`, `.env.example`, `tests/test_todos.py`
- `POST /upload-sample` in `main.py`: zips `samples/todo-app/` in-memory, creates session (mode=comprehensive, project_name=todo-app), extracts, runs `scan()`, redirects to `/generate/{id}`
- Upload page button + hidden form were already wired in a previous issue
- 5 tests added in `tests/test_sample_project.py`; 74 total tests passing
