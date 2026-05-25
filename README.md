# WhammyDocs

AI-powered documentation generator. Upload your project as a `.zip`, get a complete MkDocs documentation site — README, API reference, architecture overview, getting started guide, and deployment docs — streamed token-by-token in real time, then previewed, edited, and downloaded. Dark-mode UI with Jet Black / Periwinkle / Tea Green palette and Unageo typeface.

---

## Demo video

[![WhammyDocs Demo](https://img.youtube.com/vi/0v5cc95evUM/0.jpg)](https://youtu.be/0v5cc95evUM)

---

## What is WhammyDocs?

WhammyDocs turns any codebase into a polished documentation site in under a minute — no manual writing required.

You drop in a `.zip` of your project. The app scans every source file, figures out what language you're using, and feeds the code to an AI (DeepSeek) to write up to five documentation sections: a README, an API reference, an architecture overview, a getting-started guide, and a deployment guide. The writing streams back to you live, token by token, so you can watch it happen in real time rather than staring at a loading spinner.

Once generation finishes you land on a preview screen. Every section is rendered as a readable card. You can edit any section inline (no AI call, instant), or hit "Regenerate with AI" on just that one section — the app knows exactly which source files fed that section, so it only re-sends those files instead of the whole project.

When you're happy, you download a single zip that contains both the raw markdown files and a pre-built MkDocs Material site you can host anywhere with one command.

**Features at a glance**

- Drag-and-drop `.zip` upload, or use the built-in sample project to try it immediately
- Two generation modes — Quick (README + API ref, ~10–20 s) and Comprehensive (all 5 sections, ~30–60 s)
- Live token-by-token streaming via Server-Sent Events so you see progress immediately
- Inline editing of any section without touching the AI
- Per-section AI regeneration that only re-reads the relevant source files (saves cost and time)
- Download as a ready-to-host MkDocs Material site + raw markdown
- Dark-mode UI with a custom Jet Black / Periwinkle / Tea Green palette

**How it was built**

The backend is a single FastAPI app (`main.py`). On upload it extracts the zip into a temp folder, runs a file scanner (`scanner.py`) that maps each doc section to the subset of source files it needs, then streams DeepSeek completions over SSE to the browser. Large files are summarised before being sent to the LLM — only signatures and docstrings for files 5–20 KB, just the first 30 lines for anything bigger — so the context window stays manageable. The frontend is plain HTMX + Tailwind with Jinja2 templates; `marked.js` renders markdown client-side. No database, no user accounts — every session lives in a UUID-named temp directory and is gone when the server restarts.

---

## What it does

1. **Upload** a `.zip` of any project (Python, JS, Go, Rust, Java, and more) — or try the built-in sample project
2. **Choose** Quick (README + API ref, ~10–20s) or Comprehensive (all 5 sections, ~30–60s)
3. **Watch** the AI write each section live, token by token
4. **Edit** any section inline, or regenerate individual sections with AI
5. **Download** a ready-to-host MkDocs Material site + raw markdown source

To preview the downloaded site locally:

```bash
cd Documentation-<your-project>
python -m http.server 8080
# open http://localhost:8080
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | HTMX + Tailwind CSS (CDN) + Jinja2 |
| AI | DeepSeek API (`deepseek-chat`) |
| Streaming | Server-Sent Events (SSE) via `httpx` async |
| Docs output | MkDocs + Material theme |
| Markdown preview | `marked.js` (CDN) |
| UI theme | Custom dark-mode — Jet Black, Periwinkle, Tea Green, Unageo typeface |

---

## Getting started

### Prerequisites

- Python 3.10+
- A DeepSeek API key → [platform.deepseek.com](https://platform.deepseek.com)

### Install

```bash
git clone https://github.com/nhemant2005/whammy-docs
cd whammy-docs
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env   # then fill in your key
# or manually:
echo "DEEPSEEK_API_KEY=sk-..." > .env
```

### Run

```bash
uvicorn main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000).

---

## Production VPS Deployment

For hosting WhammyDocs publicly and securely on a Linux VPS (e.g., Ubuntu/Debian), we provide robust automated deployment assets under the `deploy/` directory:

* **Automated Installation**: Run `sudo bash deploy/setup-vps.sh` on your VPS to automatically install Python system packages, establish a virtual environment, configure reverse proxies, and handle daemon settings.
* **Unprivileged Sandboxing**: The service is sandboxed to run under a restricted, unprivileged system user to ensure host security.
* **Nginx Reverse Proxy**: A ready-to-use Nginx block pre-configured for 50MB file uploads, optimized static caching, and buffering-free SSE streaming.
* **Free Dynamic DNS**: Integrates with DuckDNS via a lightweight cron script to keep your domain mapped to your VPS IP dynamically.
* **Automatic SSL**: Completely compatible with Let's Encrypt Certbot for fast, free HTTPS certificates.

For complete, step-by-step setup instructions, please read our [VPS Deployment Guide](docs/deployment-vps.md).

---

## Project structure

```
hackathon-ai-builders/
├── main.py                   # FastAPI app — all routes
├── scanner.py                # File scanner + section→file mapping
├── generator.py              # DeepSeek streaming + skeleton extraction
├── requirements.txt
├── pytest.ini
├── .env                      # DEEPSEEK_API_KEY (never committed)
│
├── deploy/
│   ├── nginx.conf            # Nginx reverse proxy configuration template
│   ├── setup-vps.sh          # Automated interactive bash installer
│   └── whammy-docs.service   # systemd process control service template
│
├── templates/
│   ├── upload.html           # Upload page (drag-drop, mode select)
│   ├── generate.html         # Real-time SSE streaming progress
│   └── preview.html          # Preview + edit + download
│
├── static/
│   ├── css/theme.css         # Design tokens + Unageo @font-face
│   └── unageo/               # Unageo font files (ttf + variable)
├── samples/
│   └── todo-app/             # Bundled sample FastAPI project
│
└── tests/
    ├── test_upload_page.py
    ├── test_upload_endpoint.py
    ├── test_scanner.py
    ├── test_generator.py
    ├── test_issue5_pipeline.py
    ├── test_preview_download.py
    ├── test_edit.py
    └── test_sample_project.py
```

---

## Architecture

### Request flow

```
POST /upload         → validate + extract zip → scan files → session.json + mapping.json
                     → redirect to /generate/<session_id>

POST /upload-sample  → zip samples/todo-app/ in-memory → same pipeline as above

GET  /generate       → serve streaming progress page

GET  /stream         → StreamingResponse (text/event-stream)
                     → section-start → DeepSeek tokens → section-complete → (repeat)
                     → event: done → client redirects to /preview/<session_id>

GET  /preview        → render section cards with marked.js

POST /edit           → write markdown to session dir → 200

GET  /regenerate     → narrow DeepSeek SSE call for one section → write to disk

GET  /download       → build MkDocs site → zip site/ + docs/ → return zip
```

### Session state

Each upload gets a UUID. Everything lives under `/tmp/whammy-<session_id>/`:

```
/tmp/whammy-<uuid>/
├── <extracted project files>
├── session.json          # { session_id, mode, project_name, edited: {} }
├── mapping.json          # section → [source file paths]
├── docs/
│   ├── index.md          # copy of readme (MkDocs home page)
│   ├── readme.md
│   ├── api_reference.md
│   ├── architecture.md
│   ├── getting_started.md
│   └── deployment.md
├── mkdocs.yml
└── site/                 # built MkDocs HTML
```

No database. No Redis. Session data is temp-file only.

### Skeleton extraction

Large files are summarised before being sent to the LLM to stay within context limits:

| File size | What is sent |
|---|---|
| < 5 KB | Full content |
| 5 – 20 KB | Function/class signatures + docstrings |
| > 20 KB | Filename + first 30 lines |

### SSE events

| Event | Data | Meaning |
|---|---|---|
| `section-start` | section key (e.g. `api_reference`) | Section about to start |
| `message` | markdown token | Streamed content chunk |
| `section-complete` | section key | Section finished, written to disk |
| `gen-error` | error string | DeepSeek failure — error banner shown |
| `done` | _(empty)_ | All sections done, redirect to preview |

---

## Generation modes

**Comprehensive** (5 sections): README → API Reference → Architecture → Getting Started → Deployment

**Quick** (2 sections): README → API Reference

---

## Running tests

```bash
pytest
```

77 tests across all modules. All passing.

---

## Cost

Each Comprehensive generation costs approximately **$0.03–0.05** in DeepSeek API calls at `$0.50/M` input tokens.

---

## License

MIT
