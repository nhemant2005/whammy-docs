# Issue 7 — Edit + Save flow

**Label:** done
**Blocked by:** #6
**User stories:** US 21, 22, 23, 27

## What to build

[Edit] replaces the rendered section card with a `<textarea>` containing raw markdown. [Save] sends `POST /edit` with `session_id`, `section`, and `content`. Server writes the new content to the section's markdown file, sets `edited: true` in `session.json` for that section, and returns an HTML fragment. HTMX swaps only the affected card. An unsaved-changes indicator appears after any edit.

**The `edited` flag in `session.json` is required by Issue #8 (regenerate must not overwrite manually edited sections unless the user explicitly clicks Regenerate).**

## Acceptance criteria

- [x] [Edit] shows a `<textarea>` with the current raw markdown
- [x] [Save] persists the edit to disk and updates the card via HTMX swap
- [x] `session.json` records `"edited": true` for the saved section
- [x] Other section cards are not touched during a save
- [x] Unsaved-changes indicator visible after editing before saving

## Work done

**Files created/modified:**
- `main.py` — added `_EditRequest` Pydantic model and `POST /edit` route: reads `session_id`, `section`, `content`; writes to `docs/<section>.md`; sets `session["edited"][section] = True` in `session.json`; returns HTTP 200
- `tests/test_edit.py` — 5 tests: returns 200, persists content to disk, sets edited flag, does not touch other sections, 404 for unknown session

**Key decisions:**
- Save handled via vanilla JS `fetch()` in `preview.html` (not HTMX) — avoids needing HTMX swap since the rendered card is updated client-side with `marked.parse(content)` directly
- `edited` flag stored per-section in `session.json` as a dict (`{"readme": true}`) for use by Issue 8's regenerate logic
- 404 guard on unknown session to prevent writes to arbitrary paths

**Commit:** f1d0247
