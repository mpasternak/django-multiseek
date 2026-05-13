"""URL configuration for the htmx example project.

We replace multiseek's bundled ``index`` view with our own htmx-aware view
so the form page has the context it needs to render server-side. All other
multiseek endpoints (results, reset, save_form, ...) remain unchanged.
"""
from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path, reverse
from django.views.i18n import JavaScriptCatalog

from multiseek import views as multiseek_views
from multiseek.views import load_form

from books.views import AuthorAutocomplete
from htmx_fragments.views_form import HtmxMultiseekFormPage


def root(request):
    return redirect(reverse("multiseek:index"))


admin.autodiscover()


# Re-implement multiseek.urls inline so we can swap the index view.
multiseek_patterns = [
    path("jsi18n/", JavaScriptCatalog.as_view(packages=["multiseek"]), name="js_i18n"),
    path(
        "",
        HtmxMultiseekFormPage.as_view(
            registry=settings.MULTISEEK_REGISTRY,
            template_name="multiseek/index.html",
        ),
        name="index",
    ),
    path(
        "results/",
        multiseek_views.MultiseekResults.as_view(
            registry=settings.MULTISEEK_REGISTRY,
            template_name="multiseek/results.html",
        ),
        name="results",
    ),
    path(
        "save_form/",
        multiseek_views.MultiseekSaveForm.as_view(registry=settings.MULTISEEK_REGISTRY),
        name="save_form",
    ),
    path("reset/", multiseek_views.reset_form, name="reset"),
    path(
        "remove-from-results/<int:pk>",
        multiseek_views.remove_by_hand,
        name="remove_from_results",
    ),
    path(
        "remove-from-removed-results/<int:pk>",
        multiseek_views.remove_from_removed_by_hand,
        name="remove_from_removed_results",
    ),
    path(
        "reenable-removed-ids/",
        multiseek_views.reenable_removed_by_hand,
        name="reenable_removed_ids",
    ),
    path("load_form/<int:search_form_pk>", load_form, name="load_form"),
]


urlpatterns = [
    path("", root),
    path("author_autocomplete/", AuthorAutocomplete.as_view(), name="author-autocomplete"),
    path("multiseek/", include((multiseek_patterns, "multiseek"), namespace="multiseek")),
    path("htmx/", include(("htmx_fragments.urls", "htmx_fragments"), namespace="htmx_fragments")),
    path("admin/", admin.site.urls),
]
