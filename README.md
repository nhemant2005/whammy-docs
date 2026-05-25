# WhammyDocs

AI-powered documentation generator. Upload your project as a `.zip`, get a complete MkDocs documentation site — README, API reference, architecture overview, getting started guide, and deployment docs — streamed token-by-token in real time, then previewed, edited, and downloaded.

Built for the [Hackathon AI Builders](https://github.com/nhemant2005/whammy-docs) hackathon. Deadline: May 25, 2026 IST.

---

## What it does

1. **Upload** a `.zip` of any project (Python, JS, Go, Rust, Java, and more)
2. **Choose** Quick (README + API ref, ~10–20s) or Comprehensive (all 5 sections, ~30–60s)
3. **Watch** the AI write each section live, token by token
4. **Edit** any section inline, or regenerate it with AI
5. **Download** a ready-to-host MkDocs Material site + raw markdown source

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | HTMX + Tailwind CSS (CDN) + Jinja2 |
| AI | DeepSeek Flash API (`deepseek-chat`) |
| Streaming | Server-Sent Events (SSE) via `httpx` async |
| Docs output | MkDocs + Material theme |
| Markdown preview | `marked.js` (CDN) |

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
# Create a .env file with your DeepSeek key
echo "DEEPSEEK_API_KEY=sk-..." > .env
```

### Run

```bash
uvicorn main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000).

---

## Project structure

```
hackathon-ai-builders/
├── main.py              # FastAPI app — all routes
├── scanner.py           # File scanner + section→file mapping
├── generator.py         # DeepSeek streaming + skeleton extraction
├── requirements.txt
├── pytest.ini
├── .env                 # DEEPSEEK_API_KEY (never committed)
│
├── templates/
│   ├── upload.html      # Upload page (drag-drop, mode select)
│   ├── generate.html    # Real-time SSE streaming progress
│   └── preview.html     # Preview + edit + download (in progress)
│
├── static/              # CSS overrides, static assets
├── samples/
│   └── todo-app/        # Bundled sample FastAPI project
│
└── tests/
    ├── test_upload_page.py
    ├── test_upload_endpoint.py
    ├── test_scanner.py
    └── test_generator.py
```

---

## Architecture

### Request flow

```
POST /upload   → validate + extract zip → scan files → session.json + mapping.json
               → redirect to /generate/<session_id>

GET /generate  → serve streaming progress page

GET /stream    → StreamingResponse (text/event-stream)
               → for each section: section-start → DeepSeek tokens → section-complete
               → event: done → client redirects to /preview/<session_id>

POST /edit     → write markdown to session dir → return updated card HTML
POST /regenerate → narrow DeepSeek call on mapped files → SSE into one card
GET /download  → zip site/ + markdown → return site.zip
```

### Session state

Each upload gets a UUID. Everything lives under `/tmp/whammy-<session_id>/`:

```
/tmp/whammy-<uuid>/
├── <extracted project files>
├── session.json          # { session_id, mode }
├── mapping.json          # section → [source file paths]
├── docs/
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

Large files are summarised before being sent to the LLM:

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
| `gen-error` | error string | DeepSeek failure — retry shown |
| `done` | _(empty)_ | All sections done, redirect to preview |

---

## Generation modes

**Comprehensive** (5 sections): README → API Reference → Architecture → Getting Started → Deployment

**Quick** (2 sections): README → API Reference

---

## Build progress

| Issue | Description | Status |
|---|---|---|
| #1 | Project scaffold + upload page | Done |
| #2 | Upload endpoint + zip extraction + error states | Done |
| #3 | File scanner + section→file mapping | Done |
| #4 | DeepSeek client + SSE streaming (README) | Done |
| #5 | Full multi-section pipeline + skeleton extraction | Done |
| #6 | Preview + download page | In progress |
| #7 | Edit + save flow | Pending |
| #8 | Per-section regenerate | Pending |
| #9 | Sample project button | Pending |
| #10 | UI polish | Pending |

---

## Running tests

```bash
pytest
```

49 tests across upload, scanner, and generator modules. All passing.

---

## Cost

Each Comprehensive generation costs approximately **$0.03–0.05** in DeepSeek API calls at `$0.50/M` input tokens.

---

## License

MIT
