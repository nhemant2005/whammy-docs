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
