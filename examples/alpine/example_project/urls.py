from django.conf import settings
from django.conf.urls import static
from django.contrib import admin
from django.urls import include, re_path
from django.views.i18n import JavaScriptCatalog

from books.views import AuthorAutocomplete, root

admin.autodiscover()


urlpatterns = [
    re_path(r"^$", root),
    re_path(
        r"^author_autocomplete/$",
        AuthorAutocomplete.as_view(),
        name="author-autocomplete",
    ),
    re_path(r"^multiseek/", include(("multiseek.urls", "multiseek"), namespace="multiseek")),
    re_path(r"^admin/", admin.site.urls),
    re_path(
        r"^i18n/$",
        JavaScriptCatalog.as_view(packages=["multiseek"]),
        name="js_i18n_catalog",
    ),
] + static.static(settings.STATIC_URL, document_root=settings.STATIC_ROOT, show_indexes=True)
