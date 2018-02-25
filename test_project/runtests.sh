#!/bin/bash -e

echo "TRAVIS_JOB_ID=$TRAVIS_JOB_ID"
echo "DJANGO_LIVE_TEST_SERVER_ADDRESS=$DJANGO_LIVE_TEST_SERVER_ADDRESS"

export PYTHONPATH=..:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=test_project.settings
export PYTHONIOENCODING=utf_8

yarn

python manage.py compress --force -v0
python manage.py collectstatic --noinput -v0

py.test --cov=../multiseek --junitxml=../junit.xml test_app/tests.py ../multiseek
