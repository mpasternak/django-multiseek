# examples/alpine — django-multiseek frontend variant 3

Bootstrap 5 + Alpine.js. **No jQuery, no build step.**

This is the third reference frontend for `django-multiseek` (see
`docs/FRONTENDS.md` for the full variant matrix). It demonstrates that the
multiseek wire format — `[prev_op, …elements]` JSON POSTed to
`/multiseek/results/` — is fully decoupled from the bundled jQuery UI, by
rebuilding the same form-builder UX as a single Alpine.js component tree.

## What's different vs. Variants 1 & 2

| | Bundle | DOM model |
|---|---|---|
| Variant 1 (Foundation) / Variant 2 (Bootstrap + jQuery) | jQuery + jQuery-UI ≈ 110 KB | Imperative widgets manipulate the DOM |
| **Variant 3 (this)** | Alpine.js ≈ 16 KB | Declarative; the `form_data` tree IS the Alpine state |

`serialize()` becomes a small recursive walk over the reactive `frames` tree.
`addField`, `addFrame`, `removeField` are plain array mutations — Alpine
re-renders the DOM. There is no `$.widget`, no `multiseekField`, no DOM walk
to extract values.

## Quickstart

```bash
cd examples/alpine
uv sync
uv run python manage.py migrate
uv run python manage.py initial_data
uv run python manage.py runserver
```

Open <http://127.0.0.1:8000/multiseek/>. Add a field, pick a type, type a
value, click "Send query". The results iframe shows the matching books.

## Architecture

- **`example_project/`** — settings/urls/wsgi. `INSTALLED_APPS` includes
  `books` and `multiseek`. `MULTISEEK_REGISTRY = 'books.multiseek_registry'`.
  Templates `DIRS` is configured to look in this project's `templates/`
  *before* the bundled multiseek templates, so the overrides win.
- **`books/`** — Book/Author/Language demo domain. Identical to the other
  example projects so the variants are directly comparable. Uses the new
  public API: `from multiseek import StringQueryObject, …` etc.
- **`templates/multiseek/`** — overrides bundled multiseek templates with
  Bootstrap 5 + Alpine markup. Several legacy partials (buttons,
  field-list, ordering, report-type) are inlined directly into
  `index.html` because the Alpine root component renders them declaratively.
- **`static/multiseek/js/multiseek-alpine.js`** — the new component tree.
  Registers a single Alpine `Alpine.data("multiseekForm", ...)` factory.
  ~6 KB of source.

The view layer (`MultiseekFormPage`, `MultiseekResults`, `MultiseekSaveForm`)
is the bundled multiseek code, unmodified. The Python core renders the same
context variables (`js_fields`, `js_ops`, `js_types`, `js_value_lists`,
`js_autocompletes`, …) it always has — the Alpine component reads them from
embedded `<script type="application/json">` tags.

## Wire format

When the user clicks **Send query**, the Alpine component:

1. Walks `frames` and produces `[prev_op, …elements]` JSON.
2. Wraps it as `{form_data, ordering, report_type}`.
3. Builds a `<form method="post" action="./results/">` with `name="json"`
   carrying the JSON and `csrfmiddlewaretoken`.
4. Submits with `target="list_frame"`, so the response renders inside the
   results iframe.

`saveForm()` POSTs the same JSON to `./save_form/` via `fetch()` (vanilla,
no jQuery) with `X-CSRFToken` header.

## Field types — what works

The Alpine widget tree implements the field types most projects actually
use:

| Type        | Widget                              | Status |
|-------------|-------------------------------------|--------|
| string      | `<input type="text">`               | works  |
| integer     | `<input type="number">`             | works  |
| decimal     | `<input type="number" step="0.001">`| works  |
| range       | two `<input type="number">`         | works  |
| date        | flatpickr (vanilla, no jQuery)      | works  |
| value-list  | `<select>` from server-rendered options | works |
| boolean     | falls back to string widget         | works (string-style operator/value) |

## Known gaps

The Variant-3 demo deliberately leaves out a few niceties to keep the bundle
small and the JS file readable:

- **Autocomplete (django-autocomplete-light)**. The library is jQuery /
  select2-flavored, which is exactly what this variant set out to remove.
  Autocomplete fields render as a plain `<input type="text">` placeholder.
  Replacing this with a vanilla-JS combobox (e.g. `tom-select`,
  `accessible-autocomplete`, or a small custom `fetch()`-driven dropdown)
  is the natural next step.
- ~~**Session-restore via `js_init`**~~ — **fixed**. A custom
  `AlpineMultiseekFormPage` (in `books/views.py`) overrides the bundled
  index URL and exposes the session's `form_data` JSON to the template
  via `<script id="ms-form-data" type="application/json">…</script>`.
  Alpine's `init()` then walks it with `_hydrateFrame`/`_hydrateField`,
  rebuilding the reactive state — including parsing range / date JSON
  values back into per-input bindings (`value_min`/`value_max`, etc.).
  Reloading the page now preserves the form. `Load form` works correctly
  because `./load_form/<pk>` writes to the session that the next render
  reads from.
- **Nested-frame rendering depth**. The template renders one level of
  nested frames inline with a "Sub-frame" placeholder. Deeply nested
  frames (3+ levels) render but show only a textual description for
  inner-most elements. Most real queries use 0–1 levels of nesting.

These are all surface-level gaps — the wire format is fully compatible
with multiseek's Python core, so a server-side query produced via the
existing API will still parse against this UI.

## Why no jQuery?

- Bundle size: Alpine.js minified is ~16 KB vs. ~90 KB for jQuery +
  jQuery-UI.
- API: Alpine's `x-data` / `x-model` declarative bindings remove the
  imperative DOM-walking that comprises most of `multiseek.js`.
- No build step. CDN-loaded; works without `yarn`, `npm`, or `webpack`.
