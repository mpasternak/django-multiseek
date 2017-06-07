#!/bin/bash -e

export PYTHONPATH=..:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=test_project.settings
export PYTHONIOENCODING=utf_8

NO_PYTEST=0
NO_DJANGO=0

while test $# -gt 0
do
    case "$1" in
        --no-pytest) NO_PYTEST=1
            ;;
        --no-django) NO_DJANGO=1
            ;;
	--help) echo "Usage: runtests.sh [--no-pytest] [--no-django]"
	    exit 1
	    ;;
        --*) echo "bad option $1"
	    exit 1
            ;;
    esac
    shift
done

yarn install
python manage.py compress --force -v0
python manage.py collectstatic --noinput -v0

if [ "$NO_DJANGO" == "0" ]; then
    python manage.py test multiseek
fi

if [ "$NO_PYTEST" == "0" ]; then
    py.test -v test_app/tests.py
fi

