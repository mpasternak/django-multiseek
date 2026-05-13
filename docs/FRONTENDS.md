# Frontend variants

The Python core of django-multiseek — `multiseek/logic.py`, `multiseek/views.py`, `multiseek/models.py` — is UI-agnostic. The frontend's only job is to:

1. Collect user input.
2. Produce the same JSON wire format the registry expects (`form_data = [prev_op, …elements]` nested lists).
3. POST that JSON to `/multiseek/results/` (or render the description and call individual endpoints).

That means **the UI is a pluggable concern**. This document describes four reference frontends that can be selected per-project, all sharing the same Python core.

## Pluggable UI mechanism

Each example project under `examples/<name>/` is a standalone Django project. It overrides multiseek's bundled templates and static files by:

- Including its own template directory **before** multiseek's in `DIRS`/`APP_DIRS` order.
- Shipping its own `static/multiseek/...` files.
- Wiring the same `MULTISEEK_REGISTRY` setting.

No changes to the multiseek package itself are required.

## Wire-format invariants

| Endpoint | Method | Payload | Notes |
|---|---|---|---|
| `GET /multiseek/` | GET | — | Renders the form page. Sets `csrftoken` cookie via `{% csrf_token %}`. |
| `POST /multiseek/results/` | POST | `json={"form_data": [...]}` + `csrfmiddlewaretoken` | Server stores JSON in session, renders results list. |
| `POST /multiseek/save_form/` | POST (staff) | `json`, `name`, `public`, `overwrite`, `csrfmiddlewaretoken` | Persists a `SearchForm` row. |
| `GET /multiseek/load_form/<int:pk>` | GET | — | Loads a saved form into session, redirects to `/`. |
| `GET /multiseek/reset/` | GET | — | Clears session form data. |
| `GET /multiseek/remove-from-results/<int:pk>` | GET | — | Adds pk to the manually-excluded set. |
| `GET /multiseek/reenable-removed-ids/` | GET | — | Clears the excluded set. |

The `form_data` JSON shape is `[prev_op, …elements]`. An element is either:
- a `dict` with keys `field` (registered field label), `operator` (translated operator), `value` (web-shaped value), `prev_op` (`null` for first element in a group, otherwise `"and"|"or"|"andnot"`); or
- a nested list following the same `[prev_op, …elements]` shape for sub-frames.

Any UI variant that produces this JSON works with the Python core.

## Variant 1 — Minimal (Foundation 6 vendored, no yarn)

**Goal:** Drop the `yarn` + `node_modules` requirement without changing the UI itself.

**What changes:**
- Vendor only the Foundation CSS classes actually used (`grid-x`, `cell`, `button-group`, button colors, form inputs, table base). Ship a single 4-5 KB hand-curated `foundation-minimal.css`.
- Vendor `foundation-datepicker.js` + matching CSS as a single file.
- Vendor `jquery.min.js` and `jquery-ui.min.js` as static assets (or pull from CDN).
- CI no longer installs yarn or runs `yarn` (`.github/workflows/tests.yml`).

**What stays:** `multiseek.js` is unchanged. All existing Playwright tests pass without modification.

**Effort:** ~½ day. **Risk:** low.

**Best for:** Teams who like the current UI but want to drop the JS build step.

## Variant 2 — Bootstrap 5 + jQuery (imperative DOM)

**Goal:** Replace Foundation with Bootstrap 5 while keeping the existing widget logic.

**What changes:**
- Templates: swap Foundation classes for Bootstrap (`grid-x` → `row`, `cell` → `col`, `button-group` → `btn-group`, `button warning` → `btn btn-warning`, etc.).
- CSS: pull Bootstrap 5 from CDN (or vendor).
- Replace `foundation-datepicker` with `flatpickr` or `bootstrap-datepicker`.
- Update `multiseek.js` to use Bootstrap-compatible class names where it touches the DOM.

**What stays:** The widget tree (`multiseekFrame`, `multiseekField`, …) and the JSON serialization logic.

**Effort:** 1-2 days. **Risk:** low — Bootstrap is well-tested everywhere.

**Best for:** Projects that already use Bootstrap 5 elsewhere; teams comfortable with jQuery.

## Variant 3 — Bootstrap 5 + Alpine.js (declarative, no jQuery)

**Goal:** Drop jQuery entirely; use Alpine.js for state management.

**What changes:**
- Replace the jQuery widget tree with an Alpine.js component tree. Each frame and field is an `x-data` component. The form_data tree is the component's reactive state.
- `serialize()` becomes a one-line `JSON.stringify(this.frames)` — no DOM walking.
- Add/remove field is a state-mutation operation (`this.frames.push({...})`) instead of a DOM manipulation.
- Bootstrap 5 CSS.

**What stays:** The wire format. The JSON the frontend POSTs is identical.

**Effort:** 2-4 days. **Risk:** medium — the widget logic is rewritten.

**Best for:** Teams who want a modern JS stack without a build step (Alpine ships as a single CDN script).

## Variant 4 — htmx (server-rendered, no client state)

**Goal:** Eliminate frontend JavaScript almost entirely. State lives on the server.

**What changes (significantly):**
- New view endpoints that render *fragments*:
  - `GET /multiseek/fragments/field/?frame_id=X&type=Y` → renders a single field input row.
  - `POST /multiseek/fragments/add-field/?frame_id=X` → appends a field; returns the rendered field HTML.
  - `POST /multiseek/fragments/add-frame/?frame_id=X` → appends a sub-frame.
  - `DELETE /multiseek/fragments/field/<field_id>/` → removes a field; returns empty (or 200 OK with `hx-swap="outerHTML"`).
- The form page renders the current `form_data` from session as nested HTML, with htmx attributes on each "add field"/"add frame"/"remove" button.
- The Send Query button is a standard `<form>` submit (no JS). The session already holds the form_data because every add/remove updated it.
- `MultiseekFormPage` and `MultiseekResults` reuse the existing Python — they just consume an HTML-shaped session payload instead of a JS-shaped one.

**The trade-off:** every add/remove field is an HTTP round-trip. For a 5-row form, that's 5 round-trips during construction. With htmx's `hx-swap` and `hx-target`, the experience is still snappy on a local-network deploy. On high-latency links it'd feel laggy.

**What stays:** The Python registry, query parsing, results rendering, save/load form, CSRF protection.

**What's interesting:** there's effectively zero JavaScript in the project's own code (htmx itself is ~14 KB and not "your code"). No `multiseek.js`, no widget tree, no JSON serialization in the browser. The session is the single source of truth.

**Effort:** 3-5 days. **Risk:** medium-high — it's a different architecture; the test suite changes shape (Playwright tests still apply but assertions look different).

**Best for:** Teams committed to "HTML-over-the-wire" / no-JS-state-management.

## Comparison matrix

| | JS in your project | Build step | Wire format | Round-trips per add/remove |
|---|---|---|---|---|
| Foundation (current) | ~26 KB jQuery widgets | yarn | JSON POST | 0 (in-browser) |
| Variant 1 — Minimal | ~26 KB jQuery widgets | none | JSON POST | 0 |
| Variant 2 — Bootstrap+jQuery | ~26 KB jQuery widgets | none | JSON POST | 0 |
| Variant 3 — Alpine | ~6 KB Alpine components | none | JSON POST | 0 |
| Variant 4 — htmx | ~0 KB | none | HTML fragments | 1 per action |

## Example project layout

```
examples/
├── README.md                    # quick start for all four
├── minimal/
│   ├── manage.py
│   ├── example_project/         # settings, urls, wsgi
│   ├── books/                   # demo app: Book/Author/Language models + registry
│   ├── templates/multiseek/     # overrides bundled templates
│   └── static/multiseek/        # vendored Foundation + jQuery
├── bootstrap/
│   ├── manage.py
│   ├── ...
│   └── static/multiseek/        # Bootstrap CSS + multiseek.js (Bootstrap-flavored)
├── alpine/
│   ├── manage.py
│   ├── ...
│   └── static/multiseek/        # Bootstrap CSS + multiseek-alpine.js (Alpine components)
└── htmx/
    ├── manage.py
    ├── ...
    ├── multiseek_fragments/     # local app providing the new endpoints
    └── templates/multiseek/     # fragment templates (one per HTML chunk)
```

Each `examples/<name>/manage.py runserver` starts an isolated demo.

## Shared "books" domain

To keep the four examples comparable, each registers the same registry:

```python
# examples/<name>/books/multiseek_registry.py
from multiseek import create_registry, StringQueryObject, IntegerQueryObject, Ordering
from books.models import Book

registry = create_registry(
    Book,
    StringQueryObject("title", label="Title"),
    StringQueryObject("author", label="Author"),
    IntegerQueryObject("year", label="Year"),
    ordering=[Ordering("title", "Title"), Ordering("year", "Year")],
    default_ordering=["title"],
)
```

Same model, same registered fields, same demo data. Each example only differs in templates/static.

## Implementation order

1. **Pre-work:** verify the existing `test_project/` keeps working as the Foundation reference. (Already true — nothing in this plan touches it.)
2. **Scaffold:** `examples/{minimal,bootstrap,alpine,htmx}/` with shared structure and READMEs.
3. **Variant 1 (Minimal):** smallest, validates the override mechanism works.
4. **Variant 4 (htmx):** the architecturally interesting one — wire it up before the other CSS-only variants so the fragment endpoints (which live in the *example* project, not in multiseek) are well-tested.
5. **Variants 2 & 3:** parallelizable since they're CSS swaps + (for Alpine) a JS rewrite.

## Out of scope for the example projects

- Production deployment (no `STATIC_ROOT` config, no `gunicorn`, no real auth).
- Translation catalogs (English-only).
- Custom database backends (SQLite only).

Each example is meant to be `python manage.py runserver` and look at the resulting page.
