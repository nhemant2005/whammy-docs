What is WhammyDocs?

WhammyDocs turns any codebase into a polished documentation site in under a minute — no manual writing required.

You drop in a .zip of your project. The app scans every source file, figures out what language you're using, and feeds the code to an AI (DeepSeek) to write up to five documentation sections: a README, an API reference, an architecture overview, a getting-started guide, and a deployment guide. The writing streams back to you live, token by token, so you can watch it happen in real time rather than staring at a loading spinner.

Once generation finishes you land on a preview screen. Every section is rendered as a readable card. You can edit any section inline (no AI call, instant), or hit "Regenerate with AI" on just that one section — the app knows exactly which source files fed that section, so it only re-sends those files instead of the whole project.

When you're happy, you download a single zip that contains both the raw markdown files and a pre-built MkDocs Material site you can host anywhere with one command.

Features at a glance

    Drag-and-drop .zip upload, or use the built-in sample project to try it immediately
    Two generation modes — Quick (README + API ref, ~10–20 s) and Comprehensive (all 5 sections, ~30–60 s)
    Live token-by-token streaming via Server-Sent Events so you see progress immediately
    Inline editing of any section without touching the AI
    Per-section AI regeneration that only re-reads the relevant source files (saves cost and time)
    Download as a ready-to-host MkDocs Material site + raw markdown
    Dark-mode UI with a custom Jet Black / Periwinkle / Tea Green palette

How it was built

The backend is a single FastAPI app (main.py). On upload it extracts the zip into a temp folder, runs a file scanner (scanner.py) that maps each doc section to the subset of source files it needs, then streams DeepSeek completions over SSE to the browser. Large files are summarised before being sent to the LLM — only signatures and docstrings for files 5–20 KB, just the first 30 lines for anything bigger — so the context window stays manageable. The frontend is plain HTMX + Tailwind with Jinja2 templates; marked.js renders markdown client-side. No database, no user accounts — every session lives in a UUID-named temp directory and is gone when the server restarts.