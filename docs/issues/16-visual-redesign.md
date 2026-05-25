## Problem Statement

WhammyDocs currently presents a generic light-mode UI — white cards, indigo accents, system fonts — that reads as a standard web form rather than a premium AI-native tool. The generation experience offers no visual momentum: a progress bar and spinning dots give no sense of something powerful happening. The preview page looks like a text editor, not a high-fidelity documentation product. Users land on an experience that undersells what the tool actually does.

## Solution

A full visual redesign implementing the Lumina Docs aesthetic across all pages. The core experience: a deep dark interface built on Jet Black, with a Tea Green → Periwinkle gradient that first appears as a subtle glow on the upload page, then animates upward in sync with generation progress, and finally sits fully revealed on the completed review page — creating a seamless visual arc from upload through to final review. Unageo typography and 8px rounded components complete the premium, immersive feel.

## User Stories

1. As a user, I want the upload page to feel premium and dark so the product makes a strong first impression.
2. As a user, I want to see a Tea Green glow at the bottom of the upload page so the brand gradient is introduced before I even start generating.
3. As a user, I want the drag-drop zone to use the brand color palette so the interaction feels intentional and designed.
4. As a user, I want Unageo typography throughout so the product has a distinct, consistent visual identity.
5. As a user, I want headers to use Unageo Extra Bold so they feel authoritative and high-contrast.
6. As a user, I want body and generated text to use Unageo Regular so it remains readable at length.
7. As a user, I want all UI chrome (navigation, labels, buttons) to use Unageo Medium so there is a clear typographic hierarchy.
8. As a user, I want the entire interface to be dark mode so the gradient pops and the experience feels premium.
9. As a user, I want section cards to have a dark surface slightly lighter than the page background so I can distinguish layers without harsh contrast.
10. As a user, I want Thistle-coloured borders and dividers so card edges are visible without being jarring.
11. As a user, I want primary buttons in Periwinkle with dark text so call-to-action elements are immediately legible.
12. As a user, I want all components to have 8px border radius so the interface feels consistently rounded and modern.
13. As a user, I want the generation page to show a Tea Green → Periwinkle gradient that fills from the bottom of the screen upward so I feel the AI is actively building something.
14. As a user, I want the gradient fill to be directly in sync with how many sections have completed so the animation is meaningful, not decorative.
15. As a user, I want the gradient to animate smoothly between progress steps so the fill feels organic rather than jumping.
16. As a user, I want the gradient to sit behind the UI content so section cards remain fully readable during generation.
17. As a user, I want the active section card during generation to be visually highlighted so I know which section is being worked on.
18. As a user, I want completed section cards to show rendered markdown against the dark surface so I can read content as it arrives.
19. As a user, I want the review page to show the gradient fully revealed so I understand generation is complete without reading a status message.
20. As a user, I want the TOC sidebar to be styled in the dark palette so navigation feels part of the same design system.
21. As a user, I want the Download ZIP button to use the Periwinkle accent so the primary action is always easy to find.
22. As a user, I want the Edit and Regenerate with AI buttons to be clearly styled in the dark theme so secondary actions do not compete with primary ones.
23. As a user, I want the feedback textarea (Regenerate with AI panel) to be dark-themed so the inline editor feels native to the page.
24. As a user, I want the unsaved-changes indicator to remain visible in dark mode so I do not accidentally lose edits.
25. As a user, I want the error banner to be clearly distinguishable in dark mode so failures are never missed.
26. As a user, I want the page transition from upload to generation to feel continuous so the Tea Green glow on upload flows naturally into the rising gradient.

## Implementation Decisions

### Design token CSS file (`static/css/theme.css`)
A single shared stylesheet loaded by every template defines:
- `@font-face` declarations for Unageo Regular (400), Medium (500), and ExtraBold (800) pointing to `static/unageo/ttf/`
- CSS custom properties: `--color-base` (#292F36), `--color-surface` (~#363c45), `--color-border` (Thistle at low opacity), `--color-primary` (#E4D9FF), `--color-accent` (#C8FFBE), `--color-text` (near-white), `--color-text-muted` (muted lavender-gray)
- Base `font-family: Unageo, sans-serif` on `body`
- Tailwind CDN stays for layout utilities; design tokens override colour and typography

This is the single source of truth for the palette. All templates reference custom properties — no raw hex values in template HTML.

### Gradient layer
A fixed full-viewport `div#gradient-layer` inserted as the first child of `body` in `preview.html`, z-index behind all content:
- Background: `linear-gradient(to top, var(--color-accent), var(--color-primary))`
- Clip-path controlled by CSS custom property `--gradient-progress` (0% to 100%)
- `clip-path: inset(calc(100% - var(--gradient-progress)) 0 0 0)` reveals from bottom up
- JS sets `--gradient-progress` on `:root` on each `section-complete` event and to 100% on `done`
- `transition: clip-path 600ms ease-out` animates each step smoothly
- Must be `pointer-events: none` so it does not intercept clicks

### Upload page gradient seed
`upload.html` gets a fixed div at the bottom of the viewport with a radial Tea Green glow (`radial-gradient(ellipse at bottom, #C8FFBE40, transparent 70%)`). This introduces the brand colour before the gradient animation starts, making the transition feel continuous.

### Dark mode component tokens
- Page background: `var(--color-base)` (#292F36)
- Card surface: `var(--color-surface)` (~#363c45)
- Card borders: 1px solid Thistle at 25% opacity
- Primary button: `background: var(--color-primary)`, `color: var(--color-base)` (dark text on light button)
- Secondary/ghost buttons: dark surface, Thistle border, light text
- All rounded corners standardised to 8px (`rounded-lg`) throughout

### Typography hierarchy
- Page titles, section headings: Unageo Extra Bold (800)
- Navigation labels, button text, card titles: Unageo Medium (500)
- Body copy, generated markdown, textarea content, status text: Unageo Regular (400)
- Markdown prose inside `.prose` updated for dark-mode text colors

### FastAPI static mount
`main.py` already mounts `StaticFiles(directory="static")` — no changes needed. `theme.css` at `static/css/theme.css` is available at `/static/css/theme.css` immediately.

## Testing Decisions

This is a purely frontend change — no Python logic is modified. The existing 74 pytest tests must continue to pass unchanged.

Good tests for this feature:
- **Static file serving**: assert `GET /static/css/theme.css` returns 200 and `GET /static/unageo/ttf/Unageo-Regular.ttf` returns 200 — confirms fonts and theme file are reachable
- **Template structure integrity**: assert that key DOM IDs referenced by JS (`gradient-layer`, `section-body-*`, `rendered-*`) are still present in rendered template output — prevents accidental breakage during HTML restructuring
- Manual visual testing: gradient animation smoothness, font rendering, dark card legibility, upload to generation transition continuity

Prior art: `tests/test_upload_page.py` asserts HTML structure of the upload page and is the model for template structure tests.

## Out of Scope

- Mobile / responsive layout (spec is desktop-optimised)
- Light mode toggle or system preference detection
- Converting TTF files to woff2
- Redesigning `generate.html` (legacy template, no longer in the user-facing flow)
- Animation beyond the gradient fill (no particle effects, no JS router transitions)
- Accessibility / WCAG colour contrast audit (post-hackathon)

## Further Notes

- Tailwind CDN stays for layout utilities. The design token CSS file overrides only colour and typography — no full Tailwind config rewrite needed.
- The `--gradient-progress` variable is set on `:root` so any element can read it.
- Unageo is spelled with one n in the font files — not Unnageo as in the Stitch brief. All font-family references must use the correct spelling.
- The gradient layer sits at `z-index: 0`; page content sits at `z-index: 1` or above.
