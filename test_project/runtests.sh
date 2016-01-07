#!/bin/bash -e

export PYTHONPATH=..:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=test_project.settings

python manage.py test multiseek -v 3
py.test test_app/tests.py -vvv


