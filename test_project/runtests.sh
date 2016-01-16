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

python manage.py collectstatic --noinput > /dev/null

if [ "$NO_DJANGO" == "0" ]; then
    python manage.py test multiseek
fi

if [ "$NO_PYTEST" == "0" ]; then
    py.test $PYTEST_OPTIONS test_app/tests.py
fi
