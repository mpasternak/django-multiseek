from django.conf import settings
from django.conf.urls import static
from django.contrib import admin
from django.urls import include, re_path
from django.views.i18n import JavaScriptCatalog

from books.views import AlpineMultiseekFormPage, AuthorAutocomplete, root

admin.autodiscover()


urlpatterns = [
    re_path(r"^$", root),
    re_path(
        r"^author_autocomplete/$",
        AuthorAutocomplete.as_view(),
        name="author-autocomplete",
    ),
    # Override the bundled multiseek index with a subclass that exposes the
    # session form_data as JSON so Alpine can hydrate from it on page load.
    re_path(
        r"^multiseek/$",
        AlpineMultiseekFormPage.as_view(registry=settings.MULTISEEK_REGISTRY, template_name="multiseek/index.html"),
        name="multiseek-index-override",
    ),
    re_path(r"^multiseek/", include(("multiseek.urls", "multiseek"), namespace="multiseek")),
    re_path(r"^admin/", admin.site.urls),
    re_path(
        r"^i18n/$",
        JavaScriptCatalog.as_view(packages=["multiseek"]),
        name="js_i18n_catalog",
    ),
] + static.static(settings.STATIC_URL, document_root=settings.STATIC_ROOT, show_indexes=True)
