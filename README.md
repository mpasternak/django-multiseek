django-multiseek
================

[![Build Status](https://github.com/mpasternak/django-multiseek/actions/workflows/tests.yml/badge.svg)](https://github.com/mpasternak/django-multiseek/actions)
[![Coverage Status](https://coveralls.io/repos/github/mpasternak/django-multiseek/badge.svg?branch=master)](https://coveralls.io/github/mpasternak/django-multiseek?branch=master)
[![PyPI version](https://badge.fury.io/py/django-multiseek.svg)](https://badge.fury.io/py/django-multiseek)

Graphical query builder for Django. Uses Foundation 6.

Depends on:
* Django
* django-autocomplete-light
* Foundation 6

Supported configurations:
* Django 3.2
* Python 3.8, 3.9, 3.10

django-multiseek's purpose is to enable end-user of the web page to build a query form and query the database using multiple parameters.

Launch the demo, then look for a book called "A book with a title" written by John Smith.

To run the demo
---------------

`test_project` demo uses yarn to handle javascript dependencies, so:


    mkvirtualenv django-multiseek
    pip install -r requirements_dev.txt

    cd test_project
    export PYTHONPATH=..:$PYTHONPATH
    export DJANGO_SETTINGS_MODULE=test_project.settings

    yarn
    python manage.py collectstatic --noinput -v0

    python manage.py migrate
    python manage.py initial_data
    python manage.py runserver
