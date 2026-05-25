# Issue 10 — UI polish

**Label:** ready-for-agent  
**Blocked by:** #6  
**User stories:** US 28 (visual only)

## What to build

Tailwind polish pass across all pages — upload page hero, drag-drop zone styling, generation progress screen, section cards on preview page. Do not change any backend behavior.

## Acceptance criteria

- [x] Upload page looks presentable for a demo recording
- [x] Generation progress screen clearly shows which section is active
- [x] Section cards are clearly delineated with visible Edit/Save/Regenerate actions
- [x] No backend routes or business logic changed

## Work notes

- `upload.html`: gradient background, document logo icon in hero, "Recommended" chip on comprehensive mode, gradient submit button with lightning-bolt icon
- `generate.html`: active section card uses indigo border + elevated shadow + pulsing dot; on completion transitions to standard border with green checkmark badge; step counter in status text; gradient progress bar
- `preview.html`: sticky header with backdrop-blur and Download ZIP always visible; pencil icon on Edit, checkmark on Save, refresh icon on Regenerate with AI; amber unsaved-changes indicator; card header shaded `bg-gray-50/50`
- All 74 tests pass; no backend code touched
