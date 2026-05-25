# Issue 15 — Unified generation view, markdown rendering fix, regenerate feedback

**Label:** done
**Blocked by:** None

## What was built

Three UX improvements made in one session:

### 1. Unified generation + preview page

The intermediate `/generate/{session_id}` page was removed from the user-facing flow. Upload now redirects directly to `/preview/{session_id}`. The preview page detects whether docs exist yet (`generating` mode) and handles the full SSE streaming lifecycle inline:

- All section cards and the TOC are present from the first page load
- Each card shows a grey skeleton placeholder until its section starts generating
- Active section: indigo border + spinner badge + indigo skeleton pulse
- Completed section: rendered markdown + green "Done" badge
- After `done` event: all Edit / Regenerate with AI / Download buttons revealed at once; progress bar and status line hide; page title updates to "Documentation Preview"
- Download ZIP button is disabled (pointer-events-none) until generation completes
- Collapse/expand toggle is gated by `isGenerating` flag — re-enabled after generation

**Files changed:** `main.py` (upload redirects, `preview_page` generating-state detection), `templates/preview.html` (full generating-mode SSE handling), `tests/test_upload_endpoint.py`, `tests/test_sample_project.py` (redirect assertions updated from `/generate/` to `/preview/`)

### 2. SSE newline stripping bug fix

**Root cause:** Message tokens were embedded in SSE as bare strings: `data: {token}\n\n`. When a token contained a literal `\n` (e.g. at the end of a markdown line), the newline terminated the SSE `data:` field and was silently dropped by the browser's EventSource parser. The JS accumulator received stripped text; `marked.parse()` saw one long line and rendered everything as plain text — headers, lists, and code fences all lost.

**Fix:** Both SSE event generators in `main.py` (`/stream/` and `/regenerate/`) now wrap `message` tokens with `json.dumps()`: `data: {json.dumps(data)}\n\n`. Both JS message listeners call `JSON.parse(e.data)` to recover the string including its newlines. Named events (`section-start`, `section-complete`, `done`, `gen-error`) are unaffected.

**Files changed:** `main.py` (both event generators), `templates/preview.html` (generating-mode SSE listener + `regenSection`), `tests/test_regenerate.py`, `tests/test_issue5_pipeline.py` (assertions updated to expect JSON-encoded strings)

### 3. Regenerate with AI — user feedback input

Clicking "Regenerate with AI" now opens an inline feedback panel inside the card (between the header and content area) instead of triggering generation immediately.

- The button transforms to "Cancel" (grey, X icon) in place
- A 2-row textarea appears with placeholder "e.g. Make it more concise, focus on error handling…"
- A "Generate" button inside the panel confirms; Cancel dismisses and clears the input
- Edit button is hidden while the panel is open, restored on cancel or confirm
- On confirm: feedback is URL-encoded into `?feedback=` on the `GET /regenerate/` request; textarea clears
- Empty feedback sends no query param — existing behaviour preserved

**Backend:** `main.py` reads `feedback: str = Query(default="")` and passes it to `stream_one_section`. `generator.py`'s `_build_prompt` appends `"Additional instructions: {feedback}"` after "Generate the documentation now." when feedback is non-empty. `stream_one_section` signature updated to `feedback: str = ""`.

**Files changed:** `templates/preview.html` (feedback panel HTML + `openRegenPanel` / `cancelRegen` / `confirmRegen` / `handleRegenBtnClick` JS), `main.py` (`Query` import, feedback param on regenerate endpoint), `generator.py` (`_build_prompt`, `stream_one_section`)

## Acceptance criteria

- [x] Upload redirects directly to preview page with no intermediate generation page
- [x] TOC and all section cards visible from first load during generation
- [x] Cards animate through Pending → Generating → Done as SSE events arrive
- [x] Buttons hidden during generation, revealed together after `done`
- [x] Markdown renders with correct structure (headers, lists, code fences) — newlines preserved through SSE
- [x] "Regenerate with AI" opens inline feedback panel; button becomes "Cancel"
- [x] Feedback is optional — empty submit regenerates with original prompt
- [x] Feedback appended to user prompt for DeepSeek call
- [x] Textarea clears after generation begins
- [x] All 74 tests pass
