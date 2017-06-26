django-multiseek
================

[![Build Status](https://travis-ci.org/mpasternak/django-multiseek.svg?branch=master)](https://travis-ci.org/mpasternak/django-multiseek)


Graphical query builder for Django. 

Supported configurations: 
* Django 1.8, 1.10,
* Python 2.7, 3.6

django-multiseek's purpose is to enable end-user of the web page to build a query form and query the database using multiple parameters.

Launch the demo, then look for a book called "A book with a title" written by John Smith.

To run the demo
---------------

`test_project` demo uses yarn to handle javascript dependencies, so:


    export PYTHONPATH=..:$PYTHONPATH
    export DJANGO_SETTINGS_MODULE=test_project.settings

    yarn install
    python manage.py compress --force -v0
    python manage.py collectstatic --noinput -v0

    python manage.py migrate
    python manage.py initial_data
    python manage.py runserver