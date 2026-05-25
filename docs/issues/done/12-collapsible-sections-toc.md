# Issue 12 — Collapsible section cards + right-side TOC on preview page

**Label:** ready-for-agent
**Blocked by:** None

## What to build

Add collapse/expand behaviour to section cards on `preview.html` and a sticky right-side table of contents for quick navigation.

**Collapsible cards:** First section is expanded by default. Remaining sections render collapsed with a visible "Click to expand" hint in the card header. Clicking the card header (or a chevron toggle) expands or collapses the content area.

**Right-side TOC:** A sticky sidebar listing the top-level section names (README, API Reference, Architecture, Getting Started, Deployment). Clicking a name smooth-scrolls to that card. Hidden on screens narrower than 768px — full-width content layout on mobile.

## Acceptance criteria

- [x] First section card is expanded on page load; all others are collapsed
- [x] Collapsed cards show a "Click to expand" hint in the card header
- [x] Clicking the card header toggles collapse/expand with a chevron indicator
- [x] Right-side TOC is visible on screens ≥ 768px, listing all section names
- [x] Clicking a TOC entry smooth-scrolls to the corresponding card
- [x] TOC is hidden on screens < 768px; sections stack full-width
- [x] Edit, Save, and Regenerate with AI buttons still function correctly inside expanded cards
- [x] All 74 existing tests still pass

## Blocked by

None — can start immediately.
