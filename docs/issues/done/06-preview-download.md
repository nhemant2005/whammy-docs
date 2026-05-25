# Issue 6 — Preview page + marked.js rendering + MkDocs build + download

**Label:** ready-for-agent  
**Blocked by:** #5  
**User stories:** US 19, 20, 29, 30, 31, 32

## What to build

Jinja2 preview template with section cards (stable IDs: `section-readme`, `section-api-reference`, `section-architecture`, `section-getting-started`, `section-deployment`). `marked.js` via CDN renders markdown to HTML on page load. Each card has Edit, Save, and Regenerate buttons.

`GET /download/<session_id>`: generate `mkdocs.yml` from a template (Material theme, nav matching the generated sections), run `subprocess.run(["mkdocs", "build", ...])`, zip `site/` + markdown source files, return as `FileResponse` with `Content-Disposition: attachment`.

**MkDocs build happens at download time, NOT during the SSE stream.**

## Acceptance criteria

- [x] Preview page renders all generated sections as formatted HTML via `marked.js`
- [x] Each section card has a stable HTML ID
- [x] Download returns a `.zip` containing the built `site/` folder and raw markdown files
- [ ] The unzipped HTML site opens correctly in a browser with navigation and search — **not verified; `subprocess.run` is mocked in tests, real MkDocs build requires manual check**

## Follow-up change (preview page unified with generation)

`preview.html` was extended to serve as both the generation page and the preview page, eliminating the separate `generate.html` intermediate step.

The server now passes a `generating` boolean (true when `docs/` doesn't exist yet) and a `mode` string to the template. In `generating` mode:

- All section cards are pre-rendered with skeleton placeholders and a "Pending" status badge; the TOC is present from the start.
- The page opens an `EventSource` to `/stream/{session_id}` on load and animates each card through Pending → Generating (indigo border + spinner) → Done (rendered markdown + green badge) as SSE events arrive.
- Edit, Save, and Regenerate buttons are hidden and revealed all at once after the `done` event.
- The Download ZIP button is disabled (pointer-events-none) until generation completes.

In normal (non-generating) mode the page behaves identically to before. The `preview_page` route in `main.py` was updated to detect the generating state and pass section metadata (with empty content) when docs don't exist yet. Upload and upload-sample redirects were changed from `/generate/` to `/preview/`. Tests that asserted the `/generate/` redirect prefix were updated to `/preview/`.
