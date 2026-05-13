"""Settings for the Alpine.js variant of the django-multiseek example.

Adapted from `test_project/test_project/settings.py`. The project lives in
`examples/alpine/` and is meant to be run with:

    cd examples/alpine
    uv run python manage.py migrate
    uv run python manage.py initial_data
    uv run python manage.py runserver
"""

import os

DEBUG = True

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

ALLOWED_HOSTS = ["*"]

TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
SITE_ID = 1

USE_I18N = True
USE_L10N = True
USE_TZ = True

MEDIA_ROOT = ""
MEDIA_URL = ""

STATIC_ROOT = os.path.join(BASE_DIR, "collected_static")
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

SECRET_KEY = "alpine-example-not-for-production-only-a-demo"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Put the local templates dir FIRST so we override the bundled
        # multiseek templates (multiseek/index.html, base.html, ...).
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

ROOT_URLCONF = "example_project.urls"
WSGI_APPLICATION = "example_project.wsgi.application"

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "books",
    "multiseek",
)

MULTISEEK_REGISTRY = "books.multiseek_registry"

ATOMIC_REQUESTS = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
