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

## Follow-up change (generating mode)

The collapsible and TOC behaviour was adapted to work alongside the new unified generation flow (see Issue 6 follow-up).

- **During generation** (`generating=True`): all section bodies are expanded from the start so every card is visible as its skeleton fills in. The TOC is present and functional from first load. `handleHeaderClick()` is a no-op while `isGenerating` is true, so cards cannot be accidentally collapsed mid-stream.
- **After generation completes**: `isGenerating` is set to false, restoring normal toggle behaviour. Chevrons and "Click to expand" hints are rendered with Jinja conditionals so they appear in the correct initial state without a JS init pass.
- The expand-hint `<span>` is always present in the DOM (needed by `toggleSection`) but conditionally hidden via Jinja (`hidden` class) so it only shows for non-first sections in non-generating mode.
