"""
Django settings for the django-multiseek "minimal" example project.

Variant 1: Foundation 6 + jQuery UI, all assets vendored under
`static/multiseek/vendor/`. No yarn / node_modules build step.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True
SECRET_KEY = "minimal-example-not-a-secret-do-not-use-in-prod"

ALLOWED_HOSTS = ["*"]

ADMINS = (("Example", "root@localhost"),)
MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_TZ = True

# django.contrib.sites is included to mirror parent test_project; multiseek
# doesn't strictly need it but admin-related apps don't complain.
SITE_ID = 1

MEDIA_ROOT = ""
MEDIA_URL = ""

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "_collected_static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Project-level `templates/` is searched BEFORE app templates,
        # so `templates/multiseek/base.html` overrides the one bundled in
        # the multiseek package.
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

INSTALLED_APPS = [
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
]

MULTISEEK_REGISTRY = "books.multiseek_registry"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ATOMIC_REQUESTS = False
