django-multiseek
================

[![Tests](https://github.com/mpasternak/django-multiseek/actions/workflows/tests.yml/badge.svg)](https://github.com/mpasternak/django-multiseek/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/mpasternak/django-multiseek/badge.svg?branch=master)](https://coveralls.io/github/mpasternak/django-multiseek?branch=master)
[![PyPI version](https://badge.fury.io/py/django-multiseek.svg)](https://badge.fury.io/py/django-multiseek)

Graphical query builder for Django. Lets your end users compose nested AND/OR/AND-NOT searches across multiple fields, save and load form presets, and pick the result rendering — without writing any SQL.

The Python core (`multiseek/logic.py`, `multiseek/views.py`, `multiseek/models.py`) is UI-agnostic. Four reference frontends ship as runnable example projects under [`examples/`](examples/).

Depends on:
* Django
* django-autocomplete-light

Supported configurations:

| Django | Python 3.10 | Python 3.11 | Python 3.12 | Python 3.13 |
|--------|:-----------:|:-----------:|:-----------:|:-----------:|
| 4.2    |      +      |      +      |      +      |      +      |
| 5.1    |      +      |      +      |      +      |      +      |
| 5.2    |      +      |      +      |      +      |      +      |
| 6.0    |             |             |      +      |      +      |

Installation
------------

    pip install django-multiseek

Or with uv:

    uv add django-multiseek

Example projects (recommended starting point)
---------------------------------------------

Four runnable Django projects under [`examples/`](examples/), each demonstrating a different UI on top of the same Python core. Run any of them — or all four — with the helper script at the repo root:

    ./run_example.sh setup           # prepare all four (idempotent)
    ./run_example.sh run htmx        # setup + start dev server on :8000
    ./run_example.sh test            # run every example's Playwright suite
    ./run_example.sh test bootstrap  # one example's tests

| Example | UI stack | Project JS | When to pick it |
|---|---|---|---|
| [`examples/minimal`](examples/minimal/) | Foundation 6 + jQuery | ~26 KB jQuery widgets | You like the original look, but want no `yarn` build step |
| [`examples/bootstrap`](examples/bootstrap/) | Bootstrap 5 + jQuery | ~26 KB jQuery widgets | Your project already uses Bootstrap |
| [`examples/alpine`](examples/alpine/) | Bootstrap 5 + Alpine.js | ~14 KB Alpine components | Drop jQuery, keep a small declarative JS layer |
| [`examples/htmx`](examples/htmx/) | htmx (server-rendered fragments) | **0 KB** project JS | Eliminate JS state management entirely |

### What `run_example.sh` does

* `setup [name]` — for one example, or all four:
  * `uv sync --all-extras` (only for examples that ship their own `pyproject.toml`; currently `alpine`)
  * `manage.py migrate` (creates the SQLite DB)
  * `manage.py fetch_assets` — downloads JS/CSS deps from CDN into `static/multiseek/vendor/` so the example renders **without depending on a public CDN at runtime**. Idempotent; skips files already present.
  * `manage.py initial_data` — seeds 7 languages, 8 authors, 27 books (varied titles/years/multi-author/dates so every field type has something interesting to filter on).
* `run <name>` — runs `setup` then `manage.py runserver` for that example. Open <http://127.0.0.1:8000/multiseek/>.
* `test [name]` — runs `setup` then `pytest --browser chromium`. With no name, runs all four in sequence and exits non-zero if any failed (drop-in for CI).

### Manual setup (without `run_example.sh`)

If you'd rather run the steps yourself:

    cd examples/<minimal|bootstrap|alpine|htmx>
    uv sync                              # only required for alpine (own pyproject.toml)
    uv run python manage.py migrate
    uv run python manage.py fetch_assets
    uv run python manage.py initial_data
    uv run python manage.py runserver

### Architecture: how the UI variants share one core

`multiseek/logic.py` exports a JSON wire format. Each frontend's job is to:

1. let the user build a nested form,
2. produce the JSON the registry expects (or, for htmx, mutate the session JSON one fragment at a time),
3. POST or GET it back to multiseek's bundled views.

See [`docs/FRONTENDS.md`](docs/FRONTENDS.md) for the full design, per-variant tradeoffs, and the wire-format invariants.

`test_project/` — full-feature reference
----------------------------------------

The repo also contains `test_project/` — the canonical full-feature Foundation/jQuery demo. Unlike the example projects, it uses `yarn` to fetch its frontend assets and is the home of the Playwright test suite that runs in CI against the multiseek package itself. To run it:

    uv sync --all-extras
    cd test_project
    yarn
    uv run python manage.py collectstatic --noinput -v0
    uv run python manage.py migrate
    uv run python manage.py initial_data
    uv run python manage.py runserver

License
-------

MIT License. See [LICENSE](LICENSE) for details.
