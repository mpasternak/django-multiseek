django-multiseek
================

[![Build Status](https://travis-ci.org/mpasternak/django-multiseek.svg?branch=master)](https://travis-ci.org/mpasternak/django-multiseek)
[![Coverage Status](https://img.shields.io/coveralls/mpasternak/django-multiseek.svg)](https://coveralls.io/r/mpasternak/django-multiseek?branch=master)

Graphical query builder for Django. Supports Django versions 1.7 and 1.8. 

django-multiseek's purpose is to enable end-user of the web page to build a query form and query the database using multiple parameters.

Launch the demo, then look for a book called "A book with a title" written by John Smith in 2013!

To install the demo
-------------------

`test_project` demo uses django-bower to handle javascript dependencies, so:

    $ cd test_project
    $ pip install -r requirements.txt
    $ python manage.py bower install
