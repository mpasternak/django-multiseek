# Example projects

Four standalone Django projects, each demonstrating one UI variant on top of the same `multiseek` Python core. See [`../docs/FRONTENDS.md`](../docs/FRONTENDS.md) for the full design rationale.

| Directory | UI variant | JS in project | Build step | Best for |
|---|---|---|---|---|
| [`minimal/`](minimal/) | Foundation 6 + jQuery (vendored) | ~26 KB jQuery widgets | none | "Same UI as `test_project/` but drop yarn" |
| [`bootstrap/`](bootstrap/) | Bootstrap 5 + jQuery | ~26 KB jQuery widgets | none | Already use Bootstrap; comfortable with jQuery |
| [`alpine/`](alpine/) | Bootstrap 5 + Alpine.js | ~14 KB Alpine components | none | Want a modern JS stack without jQuery |
| [`htmx/`](htmx/) | htmx (server-rendered) | 0 KB project JS | none | Eliminate JS state management; server is the source of truth |

## Run any of them

```bash
cd examples/<variant>
uv sync
uv run python manage.py migrate
uv run python manage.py initial_data
uv run python manage.py runserver
# Open http://127.0.0.1:8000/multiseek/
```

Each example uses a private SQLite database (`db.sqlite3`) and seeds the same demo data (3 languages, 3 authors, 52 books).

## The shared "books" domain

All four examples register the same registry against the same `Book` model. Only the templates and static assets differ. That's the point — `multiseek/logic.py`, `multiseek/views.py`, `multiseek/models.py` are UI-agnostic.

If you're shopping for a UI: run all four locally, click around, pick the one that matches your project's existing stack.
