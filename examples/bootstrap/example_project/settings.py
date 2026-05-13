"""Django settings for the Bootstrap 5 + jQuery multiseek example."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = True
ALLOWED_HOSTS = ["*"]

SECRET_KEY = "example-project-not-for-production-use"  # noqa: S105

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_TZ = True

SITE_ID = 1

MEDIA_ROOT = ""
MEDIA_URL = ""

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# The "static" directory at the project root is searched first; this is where
# the Bootstrap-flavored multiseek.js lives and shadows the bundled one.
STATICFILES_DIRS = [BASE_DIR / "static"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # DIRS comes BEFORE APP_DIRS lookup, so local overrides win over
        # multiseek/templates/multiseek/*.html.
        "DIRS": [BASE_DIR / "templates"],
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

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

MULTISEEK_REGISTRY = "books.multiseek_registry"
