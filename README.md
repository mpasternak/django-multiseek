django-multiseek
================

[![Build Status](https://travis-ci.org/mpasternak/django-multiseek.svg?branch=master)](https://travis-ci.org/mpasternak/django-multiseek)
[![Coverage Status](https://coveralls.io/repos/github/mpasternak/django-multiseek/badge.svg?branch=master)](https://coveralls.io/github/mpasternak/django-multiseek?branch=master)

Graphical query builder for Django. 

Supported configurations: 
* Django 1.10
* Python 3.6

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

    yarn install
    python manage.py compress --force -v0
    python manage.py collectstatic --noinput -v0

    python manage.py migrate
    python manage.py initial_data
    python manage.py runserver
