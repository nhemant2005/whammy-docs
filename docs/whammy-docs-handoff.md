# WhammyDocs — Session Handoff

**Date:** 2026-05-24  
**Project dir:** `C:\Users\nhema\Desktop\practice\hackathon-ai-builders`  
**Deadline:** May 25, EOD IST  
**GitHub repo name:** `whammy-docs` (user: nhemant2005)

---

## What was done this session

1. **`/init`** — created `CLAUDE.md` with tech stack, commands, and architecture overview.
2. **`/grill-me`** — exhaustive design interview. All architectural decisions are locked. See `PRD_updated.md` for the full record.
3. **`/to-prd`** — created `PRD_updated.md` with 34 user stories, all architectural decisions, and a 7-phase build order.
4. **`/setup-matt-pocock-skills`** — configured GitHub as issue tracker, default triage labels, single-context domain docs. Wrote `docs/agents/` files and appended `## Agent skills` to `CLAUDE.md`.
5. **`/to-issues`** — drafted, reviewed (user caught 4 real bugs in the breakdown), and approved 10 vertical slice issues. **Issues have NOT been published yet** — blocked on `gh` CLI PATH issue.

---

## Immediate next step: publish issues

The user installed `gh` CLI via winget and logged in via `gh auth login` in their terminal. However, the agent's shell sessions don't see `gh` on PATH yet (likely needs a fresh shell).

**Do this first:**
```
! gh auth status
```
If that works, proceed. If not, ask the user to run `! gh auth status` themselves and confirm it shows `Logged in to github.com`.

Then:
```
! git init
! git remote add origin https://github.com/nhemant2005/whammy-docs.git
! gh repo create whammy-docs --public --source=. --remote=origin
```

Then publish the 10 issues below in order (blockers first).

---

## Approved issue breakdown

Publish in this exact order. Use `--label "ready-for-agent"` on every issue.

### Issue 1 — Project scaffold + upload page
**Blocked by:** None  
**User stories:** US 1, 2

**What to build:** FastAPI app init with Jinja2 and Tailwind via CDN (no npm). Upload page with `.zip` file input, HTML5 drag-drop zone, and Quick/Comprehensive mode radio selector. Basic routing only — no backend logic yet.

**Acceptance criteria:**
- [ ] `uvicorn main:app --reload` serves the upload page
- [ ] File input accepts `.zip` only (`accept=".zip"`)
- [ ] Mode selector (Quick / Comprehensive) is present and submits with the form
- [ ] Page is styled with Tailwind CDN (not local build)

---

### Issue 2 — Upload endpoint + zip extraction + error states
**Blocked by:** #1  
**User stories:** US 3, 4, 5

**What to build:** `POST /upload` endpoint that validates the file (`.zip` only, 50MB max), generates a UUID `session_id`, saves the zip to `/tmp/whammy-<session_id>/`, extracts it with Python's `zipfile` module, writes `session.json` (containing `session_id` and `mode`), and redirects to the generation page. Inline error messages (not full error pages) for oversized or wrong-type files — enforced at both browser (JS pre-check) and FastAPI layers.

**Acceptance criteria:**
- [ ] Uploading a valid `.zip` creates `/tmp/whammy-<uuid>/` with extracted contents
- [ ] `session.json` written with `session_id` and `mode` fields
- [ ] Files > 50MB show an inline error on the upload form without a page reload
- [ ] Non-`.zip` files show an inline error on the upload form
- [ ] Corrupted or password-protected zips are caught and return a user-friendly error (no 500)

---

### Issue 3 — File scanner + section→file mapping
**Blocked by:** #2  
**User stories:** US 12, 14, 17

**What to build:** After extraction, walk the session directory and produce a `mapping.json` file that maps each doc section to the relevant source files. Apply a universal ignore list. Detect and skip binary files. Use path-pattern matching (not language detection) to assign files to sections.

**Ignore list:** `node_modules/`, `__pycache__/`, `.git/`, `venv/`, `env/`, `dist/`, `build/`, `*.pyc`, `*.class`, `*.lock`, `package-lock.json`, `yarn.lock`, `Pipfile.lock`, and any file that fails UTF-8 decoding.

**Section→file patterns:**
- API Reference → `routes/`, `controllers/`, `api/`, `views/`, `*router*`, `*endpoint*`, `*handler*`
- Getting Started → `requirements.txt`, `package.json`, `Pipfile`, `go.mod`, `*.env.example`, top-level `README*`
- Deployment → `Dockerfile`, `docker-compose*`, `.github/workflows/`, `nginx.conf`
- Architecture → directory tree only (no file content)
- README → top-level files + detected entry point

**Acceptance criteria:**
- [ ] `mapping.json` written to session folder after upload
- [ ] No files from the ignore list appear in any mapping
- [ ] Binary files (images, compiled artifacts) are excluded
- [ ] A FastAPI project correctly maps route files to API Reference

---

### Issue 4 — DeepSeek client + SSE streaming (README only)
**Blocked by:** #3  
**User stories:** US 8, 9, 10

**What to build:** `GET /stream/<session_id>` endpoint that streams a `text/event-stream` response. For this slice: call DeepSeek for the README section only, stream tokens as `data:` SSE events. Frontend uses HTMX SSE extension to display tokens in real time in the README section card.

API key loaded from `DEEPSEEK_API_KEY` env var via `python-dotenv`. Use `httpx` async client with `stream=True` against DeepSeek's OpenAI-compatible endpoint.

**Acceptance criteria:**
- [ ] `GET /stream/<session_id>` returns `Content-Type: text/event-stream`
- [ ] README tokens appear character-by-character in the browser
- [ ] HTMX SSE extension wired up correctly (`hx-ext="sse"`, `sse-connect`, `sse-swap`)
- [ ] API key read from env, never hardcoded

---

### Issue 5 — Full generation pipeline: all sections + mode routing + redirect
**Blocked by:** #4  
**User stories:** US 11, 12, 13, 15, 16, 18, 28

**What to build:** Extend the SSE stream to generate all sections sequentially. Read `mode` from `session.json` — Comprehensive generates all 5 sections (README → API Reference → Architecture → Getting Started → Deployment), Quick generates 2 (README → API Reference). Emit `event: section-start` and `event: section-complete` named events around each section. Apply skeleton extraction (see tiers below). Use section-specific prompts. After all sections complete, emit `event: done` and trigger a client-side redirect to the preview page. Handle DeepSeek API failures with a visible error state and retry option.

**Skeleton extraction tiers:**
- < 5KB → full content
- 5–20KB → function/class signatures + docstrings only
- > 20KB → filename + first 30 lines

**Acceptance criteria:**
- [ ] Comprehensive mode generates exactly 5 sections; Quick generates exactly 2
- [ ] `section-start` event fires before each section with the section name as data
- [ ] Skeleton extraction applied for files above thresholds
- [ ] `event: done` fires after last section and redirects browser to `/preview/<session_id>`
- [ ] DeepSeek failure shows a retry button, does not crash the stream

---

### Issue 6 — Preview page + marked.js rendering + MkDocs build + download
**Blocked by:** #5  
**User stories:** US 19, 20, 29, 30, 31, 32

**What to build:** Jinja2 preview template with section cards (stable IDs: `section-readme`, `section-api-reference`, `section-architecture`, `section-getting-started`, `section-deployment`). `marked.js` via CDN renders markdown to HTML on page load. Each card has Edit, Save, and Regenerate buttons.

`GET /download/<session_id>`: generate `mkdocs.yml` from a template (Material theme, nav matching the generated sections), run `subprocess.run(["mkdocs", "build", ...])`, zip `site/` + markdown source files, return as `FileResponse` with `Content-Disposition: attachment`.

**MkDocs build happens at download time, NOT during the SSE stream.**

**Acceptance criteria:**
- [ ] Preview page renders all generated sections as formatted HTML via `marked.js`
- [ ] Each section card has a stable HTML ID
- [ ] Download returns a `.zip` containing the built `site/` folder and raw markdown files
- [ ] The unzipped HTML site opens correctly in a browser with navigation and search

---

### Issue 7 — Edit + Save flow
**Blocked by:** #6  
**User stories:** US 21, 22, 23, 27

**What to build:** [Edit] replaces the rendered section card with a `<textarea>` containing raw markdown. [Save] sends `POST /edit` with `session_id`, `section`, and `content`. Server writes the new content to the section's markdown file, sets `edited: true` in `session.json` for that section, and returns an HTML fragment. HTMX swaps only the affected card. An unsaved-changes indicator appears after any edit.

**The `edited` flag in `session.json` is required by Issue #8 (regenerate must not overwrite manually edited sections unless the user explicitly clicks Regenerate).**

**Acceptance criteria:**
- [ ] [Edit] shows a `<textarea>` with the current raw markdown
- [ ] [Save] persists the edit to disk and updates the card via HTMX swap
- [ ] `session.json` records `"edited": true` for the saved section
- [ ] Other section cards are not touched during a save
- [ ] Unsaved-changes indicator visible after editing before saving

---

### Issue 8 — Per-section regenerate
**Blocked by:** #7  
**User stories:** US 24, 25, 26

**What to build:** [Regenerate with AI] on a section card opens a new SSE connection scoped to that section only. Server reads `mapping.json` for that section's files, calls DeepSeek with streaming, pipes tokens into the target section card via HTMX (`hx-target="#section-<name>"`). Other cards are untouched. On completion, server writes new content to disk and clears the `edited` flag for that section in `session.json`.

**Acceptance criteria:**
- [ ] Regenerating one section does not alter any other section card in the DOM
- [ ] Tokens stream in real time into the target section card
- [ ] New content written to disk after regeneration completes
- [ ] `edited` flag cleared for the regenerated section in `session.json`

---

### Issue 9 — Sample project button
**Blocked by:** #5  
**User stories:** US 6, 7

**What to build:** Bundle a minimal FastAPI todo app (~8 files) under `samples/todo-app/` in the repo. "Try with sample project" button on the upload page POSTs to `/upload-sample`. Server zips the sample folder on-the-fly and runs it through the same pipeline as a regular upload (same session creation, same SSE stream, same preview page).

**Acceptance criteria:**
- [ ] Sample project files committed under `samples/todo-app/`
- [ ] Button triggers live AI generation (not pre-baked output)
- [ ] Full pipeline runs identically to a user upload

---

### Issue 10 — UI polish
**Blocked by:** #6  
**User stories:** US 28 (visual only)

**What to build:** Tailwind polish pass across all pages — upload page hero, drag-drop zone styling, generation progress screen, section cards on preview page. Do not change any backend behavior.

**Acceptance criteria:**
- [ ] Upload page looks presentable for a demo recording
- [ ] Generation progress screen clearly shows which section is active
- [ ] Section cards are clearly delineated with visible Edit/Save/Regenerate actions
- [ ] No backend routes or business logic changed

---

## Key architectural decisions (summary)

Full details in `PRD_updated.md`. Do not re-litigate these:

- **Session state:** UUID temp files in `/tmp/whammy-<session_id>/`. No database.
- **Mode routing:** `mode` stored in `session.json` during upload, read by stream endpoint.
- **SSE:** token-level streaming within each section. Named events: `section-start`, `section-complete`, `done`.
- **MkDocs build:** runs at download time inside `GET /download`, not during SSE stream.
- **Skeleton extraction:** tiered by file size (< 5KB full, 5–20KB signatures, > 20KB first 30 lines).
- **Language detection:** none. LLM infers from code. Universal ignore list for all languages.
- **Edit/Save:** save-on-click via `POST /edit`. Edited state tracked in `session.json`.
- **Upload limit:** 50MB, inline error, enforced at browser + FastAPI layers.
- **Deployment:** uvicorn in tmux on user-owned VPS. No Docker/nginx/systemd.

---

## Artifacts in the workspace

| File | Purpose |
|---|---|
| `CLAUDE.md` | Guidance for Claude Code — tech stack, commands, architecture, agent skills config |
| `PRD_updated.md` | Full PRD with 34 user stories, all decisions, 7-phase build order |
| `PRD.md` | Original PRD (superseded by PRD_updated.md) |
| `PS.md` | Hackathon problem statements (reference only) |
| `rules.md` | Hackathon rules (reference only) |
| `docs/agents/issue-tracker.md` | GitHub `gh` CLI conventions for issue operations |
| `docs/agents/triage-labels.md` | Triage label mapping (all defaults) |
| `docs/agents/domain.md` | Single-context domain doc consumer rules |

---

## Suggested skills for next session

- **`/to-issues`** — if any issues need to be re-published or modified after `gh` is confirmed working
- **`/triage`** — once issues are live, to move them through the state machine
- **`/prototype`** — useful before starting Issue #4 (SSE streaming) to sanity-check the async generator + HTMX wiring before committing to the full implementation
- **`/tdd`** — for the file scanner and skeleton extractor (pure functions, good candidates for tests)
- **`/run`** — to verify the app is working end-to-end after each phase
