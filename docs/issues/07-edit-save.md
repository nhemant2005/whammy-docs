# Issue 7 — Edit + Save flow

**Label:** ready-for-agent  
**Blocked by:** #6  
**User stories:** US 21, 22, 23, 27

## What to build

[Edit] replaces the rendered section card with a `<textarea>` containing raw markdown. [Save] sends `POST /edit` with `session_id`, `section`, and `content`. Server writes the new content to the section's markdown file, sets `edited: true` in `session.json` for that section, and returns an HTML fragment. HTMX swaps only the affected card. An unsaved-changes indicator appears after any edit.

**The `edited` flag in `session.json` is required by Issue #8 (regenerate must not overwrite manually edited sections unless the user explicitly clicks Regenerate).**

## Acceptance criteria

- [ ] [Edit] shows a `<textarea>` with the current raw markdown
- [ ] [Save] persists the edit to disk and updates the card via HTMX swap
- [ ] `session.json` records `"edited": true` for the saved section
- [ ] Other section cards are not touched during a save
- [ ] Unsaved-changes indicator visible after editing before saving
