django-multiseek
================

[![Tests](https://github.com/mpasternak/django-multiseek/actions/workflows/tests.yml/badge.svg)](https://github.com/mpasternak/django-multiseek/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/mpasternak/django-multiseek/badge.svg?branch=master)](https://coveralls.io/github/mpasternak/django-multiseek?branch=master)
[![PyPI version](https://badge.fury.io/py/django-multiseek.svg)](https://badge.fury.io/py/django-multiseek)

Graphical query builder for Django. Uses Foundation 6.

Depends on:
* Django
* django-autocomplete-light
* Foundation 6

Supported configurations:

| Django | Python 3.10 | Python 3.11 | Python 3.12 | Python 3.13 |
|--------|:-----------:|:-----------:|:-----------:|:-----------:|
| 4.2    |      +      |      +      |      +      |      +      |
| 5.1    |      +      |      +      |      +      |      +      |
| 5.2    |      +      |      +      |      +      |      +      |
| 6.0    |             |             |      +      |      +      |

django-multiseek's purpose is to enable end-user of the web page to build a query form and query the database using multiple parameters.

Launch the demo, then look for a book called "A book with a title" written by John Smith.

Installation
------------

    pip install django-multiseek

Or with uv:

    uv add django-multiseek

To run the demo
---------------

`test_project` demo uses yarn to handle javascript dependencies, so:

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
