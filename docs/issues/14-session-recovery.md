# Issue 14 — Session recovery after Start over

**Label:** ready-for-agent
**Blocked by:** None

## What to build

Two complementary mechanisms so users can recover their generated docs after accidentally clicking "Start over".

**1. Confirmation dialog (active warning):** Intercept the "Start over" anchor on `generate.html` and `preview.html`. On click, show a modal overlay that displays the `/preview/<session_id>` URL with a copy-to-clipboard button. The modal has a "Yes, start over" button (navigates to `/`) and a "Cancel" button (dismisses modal, stays on page).

**2. localStorage resume banner (passive recovery):** On every `/preview/<id>` page load, save `{ session_id, project_name }` to `localStorage` under a fixed key (`whammy_last_session`). On the upload page (`/`), read localStorage on load — if a saved session exists, render a dismissible banner at the top of the page linking to `/preview/<session_id>`. Clicking the dismiss (×) button hides the banner for that page load but does not clear localStorage.

## Acceptance criteria

- [ ] Clicking "Start over" on `generate.html` shows the confirmation modal with the preview URL and a working copy button
- [ ] Clicking "Start over" on `preview.html` shows the same modal
- [ ] "Yes, start over" navigates to `/`; "Cancel" dismisses the modal and stays on the current page
- [ ] On `preview.html` load, `whammy_last_session` is written to localStorage with `session_id` and `project_name`
- [ ] Upload page (`/`) reads localStorage on load and renders a resume banner when a session exists
- [ ] Resume banner link navigates to `/preview/<session_id>`
- [ ] Dismiss button hides the banner without clearing localStorage
- [ ] All 74 existing tests still pass

## Blocked by

None — can start immediately.
