# Issue 16 — Visual redesign: dark mode, Unageo font, gradient generation experience

**GitHub:** #16
**Label:** done
**Sub-issues:** 16.1 (#17), 16.2 (#18), 16.3 (#19), 16.4 (#20)

## Problem Statement

WhammyDocs previously presented a generic light-mode UI — white cards, indigo accents, system fonts — that read as a standard web form rather than a premium AI-native tool. The generation experience offered no visual momentum. The preview page looked like a text editor, not a high-fidelity documentation product.

## Solution

A full visual redesign implementing the Lumina Docs aesthetic across all pages. Core experience: a deep dark interface built on Jet Black (`#292F36`), with a Tea Green → Periwinkle gradient that first appears as a subtle radial glow on the upload page, then animates upward in sync with generation progress, and finally sits fully revealed on the completed preview page — creating a seamless visual arc from upload through to final review. Unageo typography and 8px rounded components complete the premium, immersive feel.

## What was built

Delivered across four vertical slices in dependency order:

### 16.1 — Shared design token layer
`static/css/theme.css` created with 7 CSS custom properties, `@font-face` for Unageo Regular/Medium/ExtraBold, and a `body` base rule. FastAPI `StaticFiles` mount added to `main.py` (was missing). Linked from all three templates. 2 new tests in `tests/test_theme.py`.

### 16.2 — Upload page dark mode
`upload.html` fully rewritten with the dark palette. Jet Black background, Periwinkle primary button, Thistle borders, dark mode selector, error banner in rose-on-dark. Fixed Tea Green radial glow div (`gradient-seed`) at viewport bottom seeds the brand colour before generation.

### 16.3 — Preview page dark shell
`preview.html` fully rewritten in dark theme. Section cards (`section-card` CSS class), dark prose overrides, Periwinkle primary buttons, dark ghost secondary buttons, Periwinkle regen button, dark feedback panel + textarea, Tea Green unsaved bar, dark error banner, dark skeleton bars, frosted dark header with Periwinkle Download ZIP.

### 16.4 — Gradient layer
`div#gradient-layer` added as first child of `<body>` in `preview.html`. `clip-path: inset(calc(100% - var(--gradient-progress, 0%)) 0 0 0)` drives bottom-up reveal with 600ms ease-out transition. `opacity: 0.18` keeps it subtle behind dark UI. JS sets `--gradient-progress` proportionally on each `section-complete` event, to 100% on `done`, and initialises to 100% on non-generating page load. 1 new test for DOM ID presence. 77 tests total, all passing.

## Implementation notes

- StaticFiles was not pre-mounted — added `from fastapi.staticfiles import StaticFiles` + `app.mount("/static", StaticFiles(directory="static"), name="static")` to `main.py`
- Gradient layer uses `opacity: 0.18` (not in original spec) to prevent the full-saturation gradient from overwhelming the dark surface
- No raw hex values in any template HTML — all colours via CSS custom properties
- Tailwind CDN retained for layout utilities only; theme.css handles all colour and typography overrides
- Unageo spelled with one `n` throughout — matching actual font filenames (`Unageo-Regular.ttf` etc.)
- `generate.html` (legacy, out of user-facing flow) received only the `<link>` tag — no visual restyling

## Files changed

- `static/css/theme.css` — new file
- `main.py` — StaticFiles import + mount
- `templates/upload.html` — full dark rewrite
- `templates/preview.html` — full dark rewrite + gradient layer
- `templates/generate.html` — theme.css link only
- `tests/test_theme.py` — new file, 3 tests (static serving × 2, gradient-layer DOM × 1)

## Test count

74 → 77 (3 new tests added across 16.1 and 16.4)
