# Issue 2 — Upload endpoint + zip extraction + error states

**Label:** done  
**Blocked by:** #1  
**User stories:** US 3, 4, 5

## What to build

`POST /upload` endpoint that validates the file (`.zip` only, 50MB max), generates a UUID `session_id`, saves the zip to `/tmp/whammy-<session_id>/`, extracts it with Python's `zipfile` module, writes `session.json` (containing `session_id` and `mode`), and redirects to the generation page. Inline error messages (not full error pages) for oversized or wrong-type files — enforced at both browser (JS pre-check) and FastAPI layers.

## Acceptance criteria

- [x] Uploading a valid `.zip` creates `/tmp/whammy-<uuid>/` with extracted contents
- [x] `session.json` written with `session_id` and `mode` fields
- [x] Files > 50MB show an inline error on the upload form without a page reload
- [x] Non-`.zip` files show an inline error on the upload form
- [x] Corrupted or password-protected zips are caught and return a user-friendly error (no 500)

## Work done

**Files created/modified:**
- `main.py` — `POST /upload`: validates extension + size, extracts zip, writes session.json, redirects to `/generate/<session_id>`
- `tests/test_upload_endpoint.py` — 7 tests covering all acceptance criteria

Committed in: `05fe43a`
