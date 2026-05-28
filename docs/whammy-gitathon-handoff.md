# WhammyDocs — GitHub Finish-Up-A-Thon Handoff

**Generated:** 2026-05-28  
**GitHub:** https://github.com/nhemant2005/whammy-docs  
**Branch:** `master`  
**Test suite:** 77/77 passing (run `python -m pytest`)  
**Deadline:** June 7, 2026  
**Prize:** $3,000 pool (10 winners) + DEV++ membership

---

## 📋 Project Summary

WhammyDocs is an AI-powered documentation generator. Upload a `.zip` of any codebase → get a complete MkDocs Material documentation site (README, API Reference, Architecture, Getting Started, Deployment) streamed token-by-token via SSE, previewed and edited in a dark-mode UI, then downloaded as a `.zip` with built HTML + raw markdown.

**Tech stack:**
- **Backend:** FastAPI (Python), Uvicorn, Jinja2
- **Frontend:** HTMX + Tailwind CSS (CDN) + `marked.js`, no JS framework
- **AI:** DeepSeek API (`deepseek-chat`) via `httpx` async SSE streaming
- **Output:** MkDocs + Material theme
- **UI:** Custom dark-mode design — Jet Black (#292F36), Periwinkle (#E4D9FF), Tea Green (#C8FFBE), Unageo typeface

---

## ✅ What's Built — Working Features

### Request Pipeline

```
POST /upload or /upload-sample
  → extract zip → scan() → session.json + mapping.json
  → 303 redirect to /preview/<uuid>

GET /preview/<uuid>
  → detects generating state (no docs_dir yet)
  → passes sections + generating flag to preview.html
  → if generating: opens SSE to /stream/<uuid>
  → tokens JSON-encoded (json.dumps / JSON.parse) for newline preservation

GET /stream/<uuid>
  → stream_all_sections() yields (event_type, data) tuples
  → events: section-start / message / section-complete / done / gen-error

GET /regenerate/<uuid>/<section_key>?feedback=<url-encoded>
  → stream_one_section() with optional feedback appended to user prompt

POST /edit  → write markdown to disk + set edited flag in session.json
GET /download/<uuid> → build MkDocs site, return Documentation-<project>.zip
```

### 5 Doc Sections (Comprehensive Mode)
- **README** — project overview, features, installation, usage, config
- **API Reference** — public functions, classes, endpoints with params & return types
- **Architecture** — high-level design, data flow, tech choices
- **Getting Started** — prerequisites, installation, first-run steps
- **Deployment** — building, containerisation, CI/CD, production setup

### 2 Doc Sections (Quick Mode)
- README + API Reference only

### Skeleton Extraction (Cost Control)
| File Size | What's sent to LLM |
|-----------|-------------------|
| < 5 KB | Full content |
| 5–20 KB | Function/class signatures + docstrings |
| > 20 KB | First 30 lines only |

### Scanner
- Auto-detects language from file extensions
- Maps files to appropriate sections (routes → API ref, Dockerfile → deployment, etc.)
- Excludes `node_modules`, `__pycache__`, `.git`, `venv`, binary files, lock files
- Builds directory tree string for Architecture section

### Visual Design (Issue 16 — Complete)
- Dark-mode rebrand: Jet Black surface, Periwinkle accent, Tea Green progress
- Unageo font family (Regular, Medium, ExtraBold + Italic variants)
- Gradient layer synced to generation progress (`clip-path` on CSS variable)
- Collapsible section cards with sticky TOC sidebar
- Frosted-glass sticky header
- Dark prose rendering via `marked.js`
- Upload page: drag-drop `.zip` zone, Quick/Comprehensive mode selector, "Try sample" button

### SSE Events Architecture
| Event | Data | Meaning |
|-------|------|---------|
| `section-start` | section key | About to generate this section |
| `message` | markdown token | Streamed content chunk |
| `section-complete` | section key | Written to disk |
| `gen-error` | error string | DeepSeek failure |
| `done` | (empty) | All done → redirect to preview |

### Tests — Full Coverage
- `test_upload_page.py` — 6 tests (root, zip input, modes, form action, Tailwind)
- `test_upload_endpoint.py` — 9 tests (valid zip, session dir, error states, password-protected)
- `test_scanner.py` — 18 tests (section mapping, ignore rules, binary exclusion, architecture tree)
- `test_generator.py` — 6 tests (skeleton extraction, SSE output)
- `test_issue5_pipeline.py` — 8 tests (mode routing, SSE events, pipeline iteration)
- `test_preview_download.py` — 8 tests (preview rendering, section IDs, download zip)
- `test_edit.py` — 5 tests (edit, save, edited flag, other sections untouched, 404)
- `test_regenerate.py` — 7 tests (SSE stream, done event, content written, flag cleared)
- `test_sample_project.py` — 5 tests (redirect, session dir, session.json, mapping.json, files)
- `test_theme.py` — 3 tests (CSS served, font served, gradient layer in preview)

---

## 🔴 What's Missing — To Be Built

### 1. Issue 14: Session Recovery After "Start Over" (Frontend Only)
[Spec: `docs/issues/14-session-recovery.md`]

Two frontend-only mechanisms:

**a) Confirmation modal on "Start over"**
- Intercept `<a>` in preview.html header
- Show modal with `/preview/<session_id>` URL + copy-to-clipboard
- "Yes, start over" → `/` ; "Cancel" → dismiss

**b) localStorage resume banner on upload page**
- On preview load: `localStorage.setItem('whammy_last_session', JSON.stringify({ session_id, project_name }))`
- On upload page load: read localStorage → show dismissible banner linking to `/preview/<session_id>`
- Dismiss hides for page load, doesn't clear localStorage

### 2. Security Hardening (PRD Complete — Not Implemented)
[Spec: `docs/PRD-security-hardening.md`]

Seven modules to build under `middleware/`:

| Module | Priority | What it does |
|--------|----------|--------------|
| `middleware/auth.py` | Critical | Nginx `auth_basic` with `.htpasswd` |
| `middleware/rate_limit.py` | Critical | Nginx `limit_req_zone` — 5 req/min on `/upload` |
| `middleware/security.py` | Critical | Zip bomb detection, path traversal prevention, file type allowlist |
| `middleware/cost_control.py` | High | Per-session $0.50 DeepSeek spending cap |
| `middleware/audit.py` | Medium | Structured JSON audit logging with rotation |
| Session cleanup | Medium | Auto-delete `/tmp/whammy-*/` sessions older than 2 hours |
| `.env` permissions | Quick | `chmod 600` on `.env` file |

**Critical urgency:** WhammyDocs was deployed on this VPS at `localhost:8000` directly exposed to the internet (no nginx auth, no rate limiting) — the service is stopped now but the API key was potentially exposed.

### 3. Deployment Fixes
- Nginx config in `sites-available/whammy-docs` is **not symlinked** to `sites-enabled/`
- Service was binding to `0.0.0.0:8000` (not `127.0.0.1`) — port was directly exposed
- Deploy script creates DuckDNS + systemd service + nginx but needs auth layer applied
- The `.env` permissions were world-readable

---

## 🚀 GitAThon Pitch Angle

### "Before vs After" Story

**Before:** WhammyDocs worked but was dangerously exposed — no auth, no rate limiting, no spending cap. Anyone who found the port could burn through API budget. No session recovery if you clicked "Start over." No audit trail.

**After (what Claude Code + Copilot can ship):** A production-ready documentation generator with:
- 🔒 Auth + rate limiting + spending caps (safe to deploy)
- 🛡️ Zip bomb / path traversal protection
- 💾 Session recovery (no more lost work on accidental nav)
- 📊 Audit logging for abuse detection
- 🧹 Auto-cleanup of orphaned sessions

### How Copilot Helped (Template)
> "GitHub Copilot was used to rapidly scaffold test suites, implement SSE streaming patterns, and refactor the visual redesign across 4 vertical slices — the `generator.py` SSE pipeline and `preview.html` gradient animation were accelerated significantly by Copilot's real-time completions."

### Suggested Demo Flow
1. Show the **before** state: open the app → upload a zip → generate docs → accidentally click "Start over" → all progress lost
2. Show the **after** state: confirmation dialog blocks accidental nav, resume banner brings you back
3. Show security in action: unauthorized request → 401, zip bomb → rejected, rate limit → 429
4. Show the dark-mode UI with gradient progress animation
5. Download the final docs site and open it

---

## 📁 Project Structure (Key Files)

```
whammy-docs/
├── main.py                    # FastAPI app — all 6 routes
├── scanner.py                 # File scanner + section→file mapping (150 lines)
├── generator.py               # DeepSeek SSE streaming + skeleton extraction (345 lines)
├── requirements.txt           # 11 dependencies
├── pytest.ini                 # asyncio_mode = auto
├── .gitignore                 # .env, __pycache__, etc.
├── CLAUDE.md                  # Agent guidance
├── DESIGN.md                  # Full design PRD
├── whammydocs_stitch_design.md # Visual identity spec
│
├── templates/
│   ├── upload.html            # Drag-drop, mode selector, sample link
│   ├── generate.html          # SSE progress page (pulsing, skeleton, progress bar)
│   └── preview.html           # Dark-mode preview + edit + regenerate + TOC (713 lines)
│
├── static/
│   ├── css/theme.css          # Design tokens + Unageo @font-face (45 lines)
│   └── unageo/                # Unageo font family (ttf + variable)
│
├── deploy/
│   ├── nginx.conf             # Nginx server block (with auth/rate-limit placeholders)
│   ├── whammy-docs.service    # systemd unit — 2 uvicorn workers
│   └── setup-vps.sh           # Full VPS deployment script (DuckDNS + systemd + nginx)
│
├── samples/todo-app/          # Bundled sample FastAPI project (7 files)
│
├── tests/                     # 10 test files, 77 total tests
│   ├── test_upload_page.py
│   ├── test_upload_endpoint.py
│   ├── test_scanner.py
│   ├── test_generator.py
│   ├── test_issue5_pipeline.py
│   ├── test_preview_download.py
│   ├── test_edit.py
│   ├── test_regenerate.py
│   ├── test_sample_project.py
│   └── test_theme.py
│
└── docs/
    ├── PRD.md                 # Full product requirements
    ├── PRD-security-hardening.md  # Security hardening plan (NOT IMPLEMENTED)
    ├── PS.md                  # Product spec
    ├── whammy-handoff.md      # Previous handoff (for reference)
    ├── agents/                # Agent configuration docs
    └── issues/
        ├── 14-session-recovery.md  # Open — next task
        └── done/               # Completed issues with ticked ACs
```

---

## ⚙️ Running Locally

```bash
# Install
pip install -r requirements.txt

# Configure
echo "DEEPSEEK_API_KEY=sk-..." > .env

# Run
uvicorn main:app --reload
# → http://localhost:8000

# Tests
python -m pytest  # 77 passed
```

## Cost Profile
- DeepSeek Flash pricing: $0.50/M input tokens
- Each Comprehensive generation: ~$0.03–0.05 (varies by project size)
- Each Quick generation: ~$0.01–0.02

---

## 🎯 Suggested Implementation Order (GitAThon)

1. **Issue 14 — Session Recovery** (~45 min, frontend-only)
   - Modal overlay in preview.html
   - localStorage resume banner in upload.html
   - No Python changes needed

2. **Security Hardening — Auth + Rate Limit** (~1 hr)
   - nginx `auth_basic` config + `.htpasswd` generation
   - nginx `limit_req_zone` — test with 401/429 responses
   - Update deploy script to generate credentials

3. **Security Hardening — Zip Bomb + Path Traversal** (~1.5 hr)
   - `middleware/security.py` validation module
   - Uncompressed size check, file count check, traversal check
   - File type allowlist
   - ~6 new tests

4. **Security Hardening — Cost Control + Audit** (~1 hr)
   - In-memory per-session spending cap
   - Structured JSON audit logging
   - Session cleanup background task

5. **Deploy safely** (~30 min)
   - Fix nginx config (symlink + auth + rate limit)
   - Fix uvicorn bind to 127.0.0.1
   - Secure `.env` permissions
   - `systemctl restart whammy-docs && systemctl reload nginx`

6. **Record before/after** (~30 min)
   - Screen recording: insecure → secured
   - Screen recording: session recovery flow
   - Write GitAThon submission post

## 🧠 Key Gotchas for the Next Agent

- **`generator.py` uses `deepseek-chat` model** — not the latest `deepseek-v4-flash`. Update `_MODEL` in generator.py if you want the newer model.
- **Preview.html is 713 lines** — most of it is inline `<script>` for SSE handling and JS interactivity. It's the most complex file.
- **All routes live in `main.py`** — convention is to add new middleware/security logic in separate files under `middleware/` and import into main.
- **Session state is temp-file only** — `/tmp/whammy-<uuid>/` with no database. This means `key` names in dictionaries matter but there's no serialization layer.
- **Tests mock `_stream_section`** with async generators — any new DeepSeek-related code must maintain this pattern for test compatibility.
- **The deployed version at `/var/www/whammy-docs/` is a copy** — always edit files in `/root/whammy-docs/` (the git repo), then rsync + restart.

## 🔗 Suggested Skills for the Next Session
- `handoff` — to compact this handoff for further delegation
- `writing-plans` — to break security hardening into sub-tasks
- `to-issues` — to create GitHub issues for each security module
- `spike` — to prototype the zip bomb detection before building middleware
