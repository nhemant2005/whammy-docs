# WhammyDocs — Design PRD

## Product Overview

WhammyDocs is an AI-powered documentation generator. A developer uploads a `.zip` of their project and receives a complete, editable documentation website in real time. The product has three screens that form a linear flow: **Upload → Generate → Preview**.

The design goal is to feel fast, technical, and trustworthy — like a tool built by engineers for engineers. The aesthetic is clean SaaS: white cards, an indigo/violet accent palette, generous whitespace, and subtle micro-animations that communicate progress without being distracting.

---

## Design Language

### Color Palette

| Role | Token | Value |
|---|---|---|
| Primary accent | indigo-600 | `#4f46e5` |
| Primary hover | indigo-700 | `#4338ca` |
| Gradient end | violet-600 | `#7c3aed` |
| Background base | slate-50 / white | `#f8fafc` / `#ffffff` |
| Background tint | indigo-50/30 | subtle indigo wash |
| Card border | gray-200 | `#e5e7eb` |
| Card border active | indigo-300 | `#a5b4fc` |
| Body text | gray-900 | `#111827` |
| Secondary text | gray-500 | `#6b7280` |
| Muted text | gray-400 | `#9ca3af` |
| Success | green-100 / green-700 | badge background / text |
| Warning | amber-50 / amber-700 | unsaved indicator |
| Error | red-50 / red-600 | error states |
| Code background | gray-100 | `#f3f4f6` |

### Typography

- **Font family:** System sans-serif (Tailwind default — Inter-like rendering)
- **Page headings:** `text-4xl font-bold tracking-tight` (Upload hero), `text-3xl font-bold` (Generate), `text-lg font-bold` (Preview header)
- **Section titles:** `text-base font-semibold text-gray-900`
- **Body / descriptions:** `text-sm text-gray-500`
- **Badges / labels:** `text-xs font-medium`
- **Code / editor:** `font-mono text-sm`
- **Prose (rendered markdown):** custom `.prose` class — h1 1.5rem/700, h2 1.25rem/600, h3 1.1rem/600, body line-height 1.6

### Spacing and Layout

- **Max content width:** `max-w-xl` (Upload), `max-w-3xl` (Generate), `max-w-6xl` (Preview)
- **Page padding:** `px-4 py-12` (Upload/Generate), `px-4 py-8` (Preview)
- **Card padding:** `p-8` (Upload form), `p-6` (section cards)
- **Card radius:** `rounded-2xl` throughout
- **Vertical gap between cards:** `space-y-4` (Generate), `space-y-6` (Preview)

### Elevation and Shadow

| State | Class |
|---|---|
| Resting card | `shadow-sm border border-gray-200` |
| Active / generating card | `shadow-lg border-2 border-indigo-300` |
| Sticky header | `shadow-sm` + `backdrop-blur-sm` |
| Upload form | `shadow-sm border border-gray-200` |
| CTA button | `shadow-sm` |

### Motion

- **Card state transitions:** `transition-all duration-300` — cards animate between active (indigo border, large shadow) and done (gray border, small shadow) states
- **Progress bar:** `transition-all duration-500` — smooth width interpolation
- **Chevron rotate:** `transition-transform duration-200` — `-rotate-90` for collapsed, `rotate-0` for expanded
- **Loading skeleton:** `animate-pulse` — gray placeholder bars before content arrives
- **Generating dot:** dual-layer with `animate-ping` outer ring + solid inner dot
- **Spinning badge icon:** `animate-spin` during generation
- **Drag-drop hover:** `hover:border-indigo-400 hover:bg-indigo-50 transition-colors`
- **Regenerate dimming:** `opacity-30` on the rendered section while SSE tokens stream in

---

## Screen 1 — Upload

**URL:** `/`
**Max width:** `max-w-xl`
**Background:** `bg-gradient-to-br from-slate-50 via-indigo-50/30 to-white`
**Layout:** Single centered column, vertically centered in viewport

### Hero Block

- **Icon container:** `w-16 h-16 rounded-2xl bg-indigo-600 shadow-lg` — holds a white document SVG icon
- **Headline:** `text-4xl font-bold text-gray-900 tracking-tight` — "WhammyDocs"
- **Subline:** `text-gray-500 text-lg` — "Upload your project zip — get a complete docs site in seconds."
- **Bottom margin below hero:** `mb-10`

### Upload Form Card

`bg-white rounded-2xl shadow-sm border border-gray-200 p-8 space-y-6`

#### Drag-Drop Zone

`border-2 border-dashed border-gray-300 rounded-xl p-10 text-center cursor-pointer`

- **Icon:** Large upload arrow SVG, `h-12 w-12 text-gray-400`
- **Primary label:** `text-gray-600 font-medium` — "Drop your .zip here" (with `.zip` in `text-indigo-600`)
- **Secondary label:** `text-sm text-gray-400 mt-1` — "or click to browse — max 50 MB"
- **File name display:** `text-sm font-semibold text-indigo-700` — appears below after file selection (hidden by default)
- **Hover state:** `hover:border-indigo-400 hover:bg-indigo-50 transition-colors`
- **Drag-over state:** JS adds `border-indigo-400 bg-indigo-50` classes on dragover, removes on dragleave/drop

#### Error States

- **Server error:** `text-red-600 text-sm font-medium bg-red-50 border border-red-200 rounded-lg px-4 py-3` (Jinja2 conditional)
- **Client error:** `text-red-600 text-sm` hidden `p` shown via JS on bad file type or oversized file

#### Mode Selector

`fieldset` with `space-y-3`. Each mode option is a styled `label` wrapping a hidden radio input:

`flex items-start gap-3 p-4 rounded-xl border border-gray-200 cursor-pointer hover:border-indigo-300 hover:bg-indigo-50 transition-colors`

**Selected state** (CSS `:has([:checked])`): `has-[:checked]:border-indigo-500 has-[:checked]:bg-indigo-50`

- **Quick:** Title + `text-sm text-gray-500` — "README + API reference — ~10-20 seconds"
- **Comprehensive (default):** Same layout + a "Recommended" badge: `text-xs font-medium px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700`

#### CTA Button

`w-full py-3 px-6 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white font-semibold rounded-xl transition-all shadow-sm`

- Lightning bolt SVG icon left of text — "Generate docs"
- Disabled state: `disabled:opacity-50 disabled:cursor-not-allowed`

### Sample Project Link

Below the card: `text-center mt-6 text-sm text-gray-500`
Inline link button: `text-indigo-600 hover:underline font-medium` — "Try with a sample project"

---

## Screen 2 — Generate (Progress)

**URL:** `/generate/<session_id>`
**Max width:** `max-w-3xl`
**Background:** Same gradient as Upload
**Layout:** Single column, top-aligned

### Header Block

- Back link: `text-sm text-indigo-600 hover:underline` — "← Start over"
- Heading: `text-3xl font-bold text-gray-900` — "Generating your docs…"
- Status line: `text-gray-500` — dynamic text (e.g., "Generating API Reference… (section 2 of 5)")

### Progress Bar

`w-full bg-gray-200 rounded-full h-2.5 mb-8 overflow-hidden`
Inner fill: `bg-gradient-to-r from-indigo-500 to-violet-500 h-2.5 rounded-full transition-all duration-500`

Width driven by JS: `(completedCount / KNOWN_TOTAL) * 100` — KNOWN_TOTAL is 2 (Quick) or 5 (Comprehensive).

### Section Cards (dynamically created by JS as SSE events arrive)

**Generating state (active card):**
`rounded-2xl border-2 border-indigo-300 bg-white shadow-lg p-6 transition-all duration-300`

- Title row: section name + pulsing dot indicator
  - Dot: outer `animate-ping` ring (indigo-400, 75% opacity) + inner solid `h-2.5 w-2.5 bg-indigo-500`
  - Badge: `bg-indigo-100 text-indigo-700` with `animate-spin` SVG + "Generating…"
- Content area: loading skeleton — 4 gray bars at varying widths with `animate-pulse`
  `h-3 bg-gray-200 rounded` at widths `w-3/4`, `w-full`, `w-5/6`, `w-2/3`

**Done state:**
`rounded-2xl border border-gray-200 bg-white shadow-sm p-6 transition-all duration-300`

- Dot removed, badge becomes `bg-green-100 text-green-700` + checkmark SVG + "Done"
- Skeleton replaced with `marked.parse()` rendered HTML inside `.prose.prose-sm`

### Error Banner (hidden by default)

`bg-red-50 border border-red-200 rounded-xl p-4`
Red alert SVG + "Generation error" heading + dynamic error message + "Retry" link.

---

## Screen 3 — Preview and Edit

**URL:** `/preview/<session_id>`
**Max width:** `max-w-6xl`
**Background:** `bg-gray-50`
**Layout:** Two-column — main content (flex-1) + sticky TOC sidebar (w-52, desktop only)

### Sticky Header

`sticky top-0 z-10 bg-white/90 backdrop-blur-sm border-b border-gray-200 shadow-sm`

- Back link: `text-sm text-indigo-600 hover:underline`
- Title: `text-lg font-bold text-gray-900` — "Documentation Preview"
- Download button (right): `px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition-colors shadow-sm` + download icon + "Download ZIP"

### TOC Sidebar

`hidden md:block w-52 flex-shrink-0` / `sticky top-20`

- Section label: `text-xs font-semibold text-gray-500 uppercase tracking-wider` — "Contents"
- Nav links: `block px-3 py-1.5 text-sm text-gray-600 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-colors`
- Anchors link to section card id attributes (`#section-readme`, etc.)

### Section Cards

`bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden`

**Card Header** (clickable — toggles body collapse):
`flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50/50 cursor-pointer select-none`

- **Chevron indicator:** `h-4 w-4 text-gray-400 transition-transform duration-200` — `-rotate-90` collapsed, `rotate-0` expanded
- **Section title:** `text-base font-semibold text-gray-900`
- **Expand hint:** `text-xs text-gray-400 italic` — "Click to expand" (collapsed cards only, not first card)
- **Action buttons (right):** wrapped in `onclick="event.stopPropagation()"`

**Edit button:** `text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100` + pencil icon
**Save button (hidden initially):** `text-white bg-indigo-600 rounded-lg hover:bg-indigo-700` + checkmark icon
**Regenerate button:** `text-indigo-600 border border-indigo-300 rounded-lg hover:bg-indigo-50` + rotate icon + "Regenerate with AI"

**Card Body (collapsible — first section expanded, rest collapsed):**

- **Unsaved indicator** (hidden initially): `px-6 py-2 bg-amber-50 border-b border-amber-100` — `text-xs text-amber-700 font-medium` — "Unsaved changes — click Save to keep your edits"
- **Rendered view:** `.prose max-w-none px-6 py-5 text-gray-800 text-sm` — `marked.parse()` output
- **Editor textarea** (hidden initially): `w-full px-6 py-4 font-mono text-sm text-gray-800 bg-gray-50 border-t border-gray-200 resize-y focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-400` at `rows="20"`

### Edit / Save Interaction States

1. **[Edit] clicked:** hide rendered div → show textarea (pre-filled with raw markdown) → hide Edit btn → show Save btn
2. **Typing in textarea:** `oninput` shows amber unsaved indicator bar
3. **[Save] clicked:** `fetch POST /edit` → on success: hide textarea → show updated rendered HTML → hide Save btn → show Edit btn → hide unsaved indicator
4. **Auto-expand:** if section collapsed when Edit or Regenerate is clicked, it auto-expands first

### Regenerate Interaction States

1. Button becomes disabled + spinning icon + "Regenerating…"
2. Rendered div gets `opacity-30`
3. SSE stream opens at `/regenerate/<session_id>/<key>` — tokens accumulate, debounced `marked.parse()` on 400ms timeout
4. On `done` event: full parse, opacity restored, textarea value synced, button re-enabled

---

## Component Inventory

| Component | Location | Key Classes |
|---|---|---|
| Indigo icon card | Upload hero | `w-16 h-16 rounded-2xl bg-indigo-600 shadow-lg` |
| Drag-drop zone | Upload | `border-2 border-dashed rounded-xl` + hover/drag states |
| Mode radio card | Upload | `has-[:checked]:border-indigo-500` CSS selector |
| "Recommended" badge | Upload | `bg-indigo-100 text-indigo-700 rounded-full` |
| Gradient CTA button | Upload | `bg-gradient-to-r from-indigo-600 to-violet-600` |
| Gradient progress bar | Generate | `bg-gradient-to-r from-indigo-500 to-violet-500` |
| Pulsing dot | Generate (active card) | `animate-ping` + solid inner |
| Spinning badge | Generate | `animate-spin` icon inside pill |
| Loading skeleton | Generate | `animate-pulse h-3 bg-gray-200 rounded` |
| Done badge | Generate | `bg-green-100 text-green-700` + checkmark |
| Error banner | Generate / Preview | `bg-red-50 border-red-200 rounded-xl` |
| Sticky glass header | Preview | `bg-white/90 backdrop-blur-sm` |
| TOC sidebar | Preview | `sticky top-20 hidden md:block` |
| Collapsible section card | Preview | `overflow-hidden` + chevron rotate |
| Unsaved indicator bar | Preview | `bg-amber-50 border-b border-amber-100` |
| Mono textarea editor | Preview | `font-mono bg-gray-50 resize-y` |
| Prose renderer | Preview | `.prose` custom CSS class |

---

## User Flow

```
/ (Upload)
  down  drag-drop or browse → select mode → "Generate docs"
  POST /upload
  down
/generate/<id> (Progress)
  down  SSE stream: section-start → tokens → section-complete (×N)
  down  done event → redirect after 800ms
/preview/<id> (Preview and Edit)
  down  cards: [Edit] → textarea → [Save]  or  [Regenerate with AI] → SSE
  GET /download/<id> → whammy-docs.zip
```

---

## Responsive Behavior

- Upload and Generate pages are single-column and fully responsive at all widths.
- Preview page: TOC sidebar is `hidden md:block` — hidden on mobile, visible from `md` (768px) breakpoint.
- All cards use `max-w-6xl` with `px-4` padding — safe down to 320px viewport.
- No horizontal scroll at any supported viewport width.

---

## Implementation Notes

- **CSS framework:** Tailwind CSS via CDN — no build step required
- **Markdown rendering:** `marked.js` via CDN — renders markdown strings to HTML client-side
- **No custom CSS file** — all styles are Tailwind utility classes or minimal style blocks for `.prose` typography
- **SSE events:** `section-start`, `message` (default), `section-complete`, `done`, `gen-error`, `building`
- **Jinja2 templating:** Server renders section data into template; JS handles all client-side state transitions
- **Debounced rendering:** During section regeneration, `marked.parse()` is called at most once per 400ms to avoid layout jank while tokens stream in
- **State management:** All UI state is class-based (hidden/visible, opacity, border color) — no framework, no virtual DOM
