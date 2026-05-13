# examples/minimal — Variant 1 (Foundation 6 + jQuery, no yarn)

Variant 1 — Foundation 6 + jQuery, fully vendored. No yarn / `node_modules` required.

This is the smallest possible reference frontend for `django-multiseek`: it serves
the same Foundation 6 + jQuery UI as the parent `test_project/`, but every JS and
CSS asset lives in `static/multiseek/vendor/` so there is no build step. Run the
example with nothing but Python, `uv`, and an internet connection (for the initial
dependency install).

## Quickstart

```bash
cd examples/minimal
uv run python manage.py migrate
uv run python manage.py initial_data
uv run python manage.py runserver
```

Then open <http://127.0.0.1:8000/multiseek/> in a browser.

`uv run` resolves the `django-multiseek` package against the source tree two
levels up (`manage.py` adjusts `sys.path` accordingly) and pulls in `Django`,
`django-autocomplete-light`, and `python-dateutil` transient deps as declared
in the project's top-level `pyproject.toml`.

## Demo data

`initial_data` seeds:

- 3 Languages: `english`, `polish`, `french`
- 3 Authors: John Smith, Ian Kovalsky, Stephan Novak
- 52 Books (2 named + 50 "Book no N" bulk entries)

This matches the parent `test_project/`'s fixture so user-facing behaviour is
directly comparable.

## What's vendored

Everything needed by `multiseek.js` is shipped as a static file:

| File | Origin | Size |
|---|---|---|
| `static/multiseek/vendor/jquery.min.js` | <https://code.jquery.com/jquery-3.7.1.min.js> | ~85 KB |
| `static/multiseek/vendor/jquery-ui.min.js` | <https://code.jquery.com/ui/1.13.2/jquery-ui.min.js> | ~249 KB |
| `static/multiseek/vendor/foundation-datepicker.js` | cdnjs `foundation-datepicker@1.5.6` | ~27 KB |
| `static/multiseek/vendor/foundation-datepicker.css` | cdnjs `foundation-datepicker@1.5.6` | ~3 KB |
| `static/multiseek/foundation-minimal.css` | hand-curated subset of Foundation 6 | ~6 KB |

`foundation-minimal.css` is hand-curated rather than vendored from the
official Foundation 6 distribution. It implements **only** the classes
actually used in the multiseek templates and `multiseek.js`:

- XY grid: `grid-x`, `grid-margin-x`, `grid-padding-x`, `grid-margin-y`, `cell`,
  `large-*`, `small-*`
- Buttons: `button`, `button alert`, `button warning`, `button small`,
  `button-group`
- Form inputs (input/select/textarea base style)
- Multiseek wrappers (`frame`, `multiseekFrame`, `multiseek-prev-op`,
  `multiseek-fieldset`, `multiseek-range-field-label`)
- Legacy `row`/`columns` (still referenced by `multiseek.js` for some widgets)
- Foundation icon-font no-op fallbacks (`fi-plus`, `fi-tablet-landscape`)

Hand-curating keeps the CSS payload around 6 KB instead of ~200 KB.

`autocomplete_light` (for the Author field's select2 autocomplete) is loaded
straight from the `django-autocomplete-light` package's bundled statics — no
re-vendoring needed.

## Functional parity

This variant is **functionally identical** to `test_project/`. The only
differences are:

1. All client assets are vendored under `static/multiseek/vendor/` instead of
   being pulled via `yarn install` at build time.
2. `foundation-minimal.css` replaces the full Foundation 6 bundle.
3. Templates and Python code use the new public API
   (`from multiseek import …`) instead of `from multiseek.logic import …`.

The Python core (`multiseek.logic`, `multiseek.views`, `multiseek.models`) is
unmodified.

## Layout

```
examples/minimal/
├── README.md                              (this file)
├── manage.py
├── example_project/                       Django project settings/urls/wsgi
├── books/                                 demo app — Book/Author/Language
│   ├── models.py
│   ├── multiseek_registry.py              registry binding
│   ├── views.py                           AuthorAutocomplete + root redirect
│   ├── migrations/0001_initial.py
│   └── management/commands/initial_data.py
├── templates/multiseek/
│   ├── base.html                          overrides bundled base — loads vendored assets
│   └── multiseek_head.html                trimmed head (no source comments)
└── static/multiseek/
    ├── foundation-minimal.css             ~6 KB hand-curated
    └── vendor/
        ├── jquery.min.js
        ├── jquery-ui.min.js
        ├── foundation-datepicker.css
        └── foundation-datepicker.js
```

## Admin access for saved-form testing

To exercise the "Save form" button you need a logged-in staff user:

```bash
uv run python manage.py createsuperuser
```

Then log in at `/admin/` and re-visit `/multiseek/`.
