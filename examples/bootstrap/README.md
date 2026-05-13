# Variant 2 — Bootstrap 5 + jQuery

This is a self-contained Django project that demonstrates how to swap
django-multiseek's bundled Foundation 6 frontend for a Bootstrap 5 skin
while keeping the existing imperative jQuery widget logic.

The Python core (registries, views, JSON wire format, session handling)
is unchanged. Only the UI is re-skinned.

## What changed vs. the bundled UI

- Templates: Foundation classes replaced with Bootstrap 5 equivalents
  (`grid-x` → `row`, `cell` → `col`, `button-group` → `btn-group`,
  `button` → `btn btn-primary`, `button alert` → `btn btn-danger`,
  `button warning` → `btn btn-warning`).
- Inputs and selects pick up `form-control` / `form-select`.
- foundation-datepicker (`.fdatepicker(...)`) is replaced by flatpickr
  pulled from a CDN.
- The widget JS (`static/multiseek/js/multiseek.js`) is the same ~26 KB
  jQuery widget tree — only the class strings emitted into the DOM and
  the datepicker initializer changed.

## Quick start

```bash
cd examples/bootstrap
uv run python manage.py migrate
uv run python manage.py initial_data
uv run python manage.py runserver
```

Then open <http://127.0.0.1:8000/multiseek/>.

## Layout

- `example_project/` — Django settings, URLs, WSGI.
- `books/` — sample domain (`Book`, `Author`, `Language`) and a
  `multiseek_registry` mirroring the bundled test project.
- `templates/multiseek/` — Bootstrap 5 overrides for every multiseek
  template. Picked up first because `TEMPLATES[0]["DIRS"]` is set.
- `static/multiseek/js/multiseek.js` — Bootstrap-flavored copy of the
  bundled `multiseek.js`. Picked up first because the project's
  `static/` directory leads `STATICFILES_DIRS`.

The project depends on the in-repo `multiseek` package; `manage.py`
prepends the repo root to `sys.path`, so no install step is needed.
