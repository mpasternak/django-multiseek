# django-multiseek — Variant 4 (htmx)

Server-rendered fragments via [htmx](https://htmx.org/). **Zero custom
JavaScript in this project** — htmx is the only JS dependency, loaded from a
CDN.

Every add/remove/edit on the search form is one HTTP round-trip. The user's
session holds the canonical `form_data` JSON; htmx swaps server-rendered
HTML fragments into the page. No widget tree, no in-browser JSON
serialisation, no Alpine.

This is the architecturally most interesting of the four reference frontends
described in `docs/FRONTENDS.md` — and the heaviest in terms of round-trips.

## Quick start

From the repository root:

```bash
cd examples/htmx
uv run python manage.py migrate
uv run python manage.py initial_data
uv run python manage.py runserver
```

Then open <http://127.0.0.1:8000/multiseek/>.

> The example imports `multiseek` from the repository root via
> `sys.path` manipulation in `manage.py` — no `pip install` of the package
> is required.

## How it works

```
+-------------------+   POST /htmx/add-field/0/   +-----------------+
|  Browser          |  -------------------------> |  Django         |
|                   |                             |                 |
|  htmx waits for   |  <-------------------------+|  Mutate session |
|  the response and |    <div class="ms-field">   |  Render fragment|
|  swaps it into the|         ...                 |                 |
|  field list.      |    </div>                   +-----------------+
+-------------------+
```

### Path-based addressing

Each frame/field is identified by a dotted path string such as `"0.2.1"`,
meaning "the 1st child under the 2nd child of the root frame". Paths are
stable as long as no element is added or removed at an earlier index in the
same level — which is fine because every mutation returns a re-rendered
subtree.

We chose path-based addressing over per-element UUIDs because:

- It needs nothing extra in the session JSON shape (the bundled multiseek
  views read the same JSON).
- It keeps the URL human-readable for debugging (`/htmx/add-field/0.3/`).
- After a mutation we always swap back HTML that carries the new paths, so
  stale paths are never used.

### Endpoints

All under `/htmx/`:

| Method | URL                       | Effect                                                                |
|--------|---------------------------|-----------------------------------------------------------------------|
| POST   | `add-field/<path>/`       | Append a field to the frame at `<path>`. Returns the field fragment.  |
| POST   | `add-frame/<path>/`       | Append a sub-frame. Returns the sub-frame fragment.                   |
| DELETE | `element/<path>/`         | Remove the element at `<path>`. Returns empty body.                   |
| POST   | `field-type/<path>/`      | User picked a different field type; returns the re-rendered field.    |
| POST   | `field-value/<path>/`     | Persist the user-typed value. Empty body.                             |
| POST   | `field-prev-op/<path>/`   | Persist the and/or/andnot dropdown. Empty body.                       |

### Send query

The "Send query" button is a plain `<form method="post"
action="/multiseek/results/">` with a hidden `json` input pre-populated
from the session. Because the session is already in sync (every mutation
wrote to it), this works without any JS.

## What's functional, what's TODO

| Field type     | Status                                                                |
|----------------|-----------------------------------------------------------------------|
| `string`       | Fully functional — text input, all operators, send-query end to end.  |
| `integer`      | Generic text input; works if user types a number.                     |
| `date`         | TODO — needs date-picker widget; users see a plain text box.          |
| `range`        | TODO — needs two-value widget; users see a plain text box.            |
| `autocomplete` | TODO — needs select2/dal integration without JS state.                |
| `value-list`   | TODO — should render a `<select>` populated from the registry values. |
| `boolean`      | TODO — should render a checkbox / yes-no select.                      |

The scope cap for the first cut of Variant 4 is "string fields end to end".
Other types are still discoverable through the type-select dropdown but show
a generic text input with a "TODO" hint until typed widgets land.

Other known gaps:

- No save/load-form UI (the bundled endpoints still exist at
  `/multiseek/save_form/` and `/multiseek/load_form/<pk>` but there's no
  button for them in this example).
- No report-type or ordering selectors yet — the registry's default
  ordering is used.
- No "removed by hand" UI on the results page.
- Styling is intentionally minimal (a small `<style>` block in `base.html`).

## Why this exists

The Python core of django-multiseek is UI-agnostic. The frontend's job is to
build the same nested-list JSON wire format and POST it to
`/multiseek/results/`. This variant proves the JSON can be built entirely
server-side — your project ships zero JavaScript of its own.

Trade-off: every interaction is a round-trip. On a local-network deploy this
feels snappy; on a high-latency link, less so. See `docs/FRONTENDS.md` for
the full comparison.
