from django.conf import settings
from django.urls import path
from django.views.i18n import JavaScriptCatalog

from multiseek import views
from multiseek.views import load_form

urlpatterns = [
    path("jsi18n/", JavaScriptCatalog.as_view(packages=["multiseek"]), name="js_i18n"),
    path(
        "",
        views.MultiseekFormPage.as_view(registry=settings.MULTISEEK_REGISTRY, template_name="multiseek/index.html"),
        name="index",
    ),
    path(
        "results/",
        views.MultiseekResults.as_view(registry=settings.MULTISEEK_REGISTRY, template_name="multiseek/results.html"),
        name="results",
    ),
    path("save_form/", views.MultiseekSaveForm.as_view(registry=settings.MULTISEEK_REGISTRY), name="save_form"),
    path("reset/", views.reset_form, name="reset"),
    path("remove-from-results/<int:pk>", views.remove_by_hand, name="remove_from_results"),
    path(
        "remove-from-removed-results/<int:pk>",
        views.remove_from_removed_by_hand,
        name="remove_from_removed_results",
    ),
    path("reenable-removed-ids/", views.reenable_removed_by_hand, name="reenable_removed_ids"),
    path("load_form/<int:search_form_pk>", load_form, name="load_form"),
]
