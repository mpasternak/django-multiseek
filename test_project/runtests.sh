#!/bin/bash -e

export PYTHONPATH=..:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=test_project.settings
export PYTHONIOENCODING=utf_8

yarn install
python manage.py compress --force -v0
python manage.py collectstatic --noinput -v0

py.test -sv ../multiseek test_app/tests.py


