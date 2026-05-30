# Frontend Refactoring Priority List

## Context

No build step, no npm, vanilla JS, Jinja2 server-rendered templates. All changes must work as plain files served by Flask.

Principles:

- Each commit leaves the app in a fully working state
- Write or update a test before each commit
- Server-rendered Jinja2 values (`{{ }}`) may not move to external JS files
- CSS class names must not change (would break visual regression)

## Status

| #   | Name                                                 | Status  | Commit                                                              |
| --- | ---------------------------------------------------- | ------- | ------------------------------------------------------------------- |
| P1  | Remove dead HTMX                                     | Done    | `3f32fdf`                                                           |
| P2  | Lazy-load dashboard thumbnails                       | Done    | `9d1d50e`                                                           |
| P3  | `extra_head`/`extra_js` blocks + scope `camera.js`   | Done    | `c5bc078`                                                           |
| P4a | Extract `dashboard.css` from `style.css`             | Done    | `6ee15bd`                                                           |
| P4b | Extract `add-item.css` from `style.css`              | Done    | `ca1202d`                                                           |
| P4c | Extract `edit-photos.css` from `style.css`           | Done    | `eef3340`                                                           |
| P4d | Extract `recipes.css` from `style.css`               | Skipped | shared with `landing.html` — `recipe-card` class used on both pages |
| P4e | Extract `audit.css` from `style.css`                 | Skipped | `audit-banner` used on `dashboard.html` too                         |
| P4f | Extract `landing.css` from `style.css`               | Pending | —                                                                   |
| P5  | Extract dashboard inline JS to `static/dashboard.js` | Done    | `0d943b3`                                                           |
| P6  | DOM-as-state → JS state object in `dashboard.js`     | Pending | —                                                                   |

## Target file layout (after P5)

```
static/
  style.css          — shared: design tokens, base, nav, buttons, flash, auth
  dashboard.css      — dashboard-only styles
  add-item.css       — add-item-only styles
  recipes.css        — recipe page styles
  audit.css          — audit page styles
  edit-photos.css    — edit-photos page styles
  landing.css        — landing page styles
  camera.js          — shared camera helper (scoped to add_item + edit_photos)
  dashboard.js       — dashboard interactive behaviour
  sortable.min.js    — SortableJS, dashboard only
  sw.js              — service worker
```

## Per-increment notes

### P1 — Remove dead HTMX

- Confirmed: `grep -r "hx-" templates/` returns zero results. Safe pure deletion.

### P2 — Lazy-load thumbnails

- Only one `<img>` with user content on dashboard: line 247, class `item-row__thumb-img`.

### P3 — Scope `camera.js`

- `createCameraCapture` is defined in `camera.js` but never called in any template — both `add_item.html` and `edit_photos.html` implement their own inline camera logic. Scoping it prevents loading it on every page.

### P4 — CSS split

- CSS sections are delimited by `═══` comments — use these as cut points.
- Before moving each section: `grep -r "<class-names>" templates/` to confirm the selectors appear only on the target page.
- Always update `app/__init__.py`'s `inject_css_version` context processor in the same commit as the template that references the new version variable.

### P5 — Extract dashboard JS

- The main IIFE (`lines ~338–654`) contains zero `{{ }}` Jinja variables — all data is in `data-*` HTML attributes. Safe to extract.
- The onboarding block (`lines ~35–105`) contains `{{ vapid_public_key }}` — must stay inline.
- Wrap extracted code in `DOMContentLoaded` instead of an IIFE.
- Load order in `{% block extra_js %}`: `sortable.min.js` before `dashboard.js`.

### P6 — DOM-as-state (deferred until P5 is done)

- Search filter and location filter toggle `element.hidden` by iterating all `.card-wrap` nodes.
- Fix: a small state object `{ search, location, sort }` whose changes trigger a single render pass over the item data.
