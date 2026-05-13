# examples/minimal — Variant 1 (Foundation 6 + jQuery, no yarn)

The same Foundation 6 + jQuery UI as the parent `test_project/`, but loaded
from CDN instead of through a `yarn` build. Zero local JS / CSS assets.

> **Note on naming:** this variant is "minimal" in the sense of **minimal
> setup** — no `node_modules`, no `yarn install`, no `collectstatic` step
> for client assets. It is *not* a stripped-down Foundation. The styling is
> the upstream Foundation 6 build, served verbatim from jsdelivr.

## Quickstart

```bash
cd examples/minimal
uv sync
uv run python manage.py migrate
uv run python manage.py initial_data
uv run python manage.py runserver
```

Then open <http://127.0.0.1:8000/multiseek/>.

`uv run` resolves the `django-multiseek` package against the source tree
two levels up (`manage.py` adjusts `sys.path`) and pulls in `Django`,
`django-autocomplete-light`, and `python-dateutil`.

## What gets loaded from CDN

| URL | Purpose |
|---|---|
| `cdn.jsdelivr.net/npm/foundation-sites@6.8.1/.../foundation.min.css` | Layout, grid, buttons, forms |
| `cdn.jsdelivr.net/npm/foundation-datepicker@1.5.4/...` (css + js) | Date picker for `DateQueryObject` |
| `code.jquery.com/jquery-3.7.1.min.js` | Required by multiseek.js widgets |
| `code.jquery.com/ui/1.13.2/jquery-ui.min.js` | Some multiseek.js code paths |

If you want a fully offline build, mirror those four URLs into your own
`static/multiseek/vendor/` and switch the `href`s in
`templates/multiseek/base.html`. The hand-curated `foundation-minimal.css`
that an earlier version of this example tried is *not* recommended —
curating only the classes that show up in the templates produced visible
styling gaps. Vendor the upstream Foundation 6 build if you need it local.

## Demo data

`initial_data` seeds:

- 3 Languages: `english`, `polish`, `french`
- 3 Authors: John Smith, Ian Kovalsky, Stephan Novak
- 52 Books (2 named + 50 `Book no N` bulk entries)

Matches the parent `test_project/` fixture so behavior is directly comparable.

## Functional parity

Functionally identical to `test_project/`. The only differences:

1. Client assets come from CDN instead of a yarn build.
2. Templates and Python code use the new public API
   (`from multiseek import …`) instead of `from multiseek.logic import …`.

The Python core (`multiseek.logic`, `multiseek.views`, `multiseek.models`)
is unchanged.

## Layout

```
examples/minimal/
├── README.md
├── manage.py
├── example_project/                 Django project settings/urls/wsgi
├── books/                           demo app — Book/Author/Language
│   ├── models.py
│   ├── multiseek_registry.py
│   ├── views.py                     AuthorAutocomplete + root redirect
│   ├── migrations/0001_initial.py
│   └── management/commands/initial_data.py
└── templates/multiseek/
    ├── base.html                    overrides bundled base — loads CDN assets
    └── multiseek_head.html          trimmed head
```

## Admin access for saved-form testing

To exercise the "Save form" button you need a logged-in staff user:

```bash
uv run python manage.py createsuperuser
```

Then log in at `/admin/` and re-visit `/multiseek/`.
