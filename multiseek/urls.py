# -*- encoding: utf-8 -*-

from django.conf.urls import  url
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.i18n import JavaScriptCatalog

from multiseek import views
from multiseek.views import load_form


urlpatterns = [

    url(r'^jsi18n/$',
        JavaScriptCatalog.as_view(packages=['multiseek']),
        name="js_i18n"),

    url(r'^$', csrf_exempt(views.MultiseekFormPage.as_view(
        registry=settings.MULTISEEK_REGISTRY,
        template_name="multiseek/index.html"
    )), name="index"),

    url(r'^results/$',
        csrf_exempt(views.MultiseekResults.as_view(
            registry=settings.MULTISEEK_REGISTRY,
            template_name="multiseek/results.html"
        )), name="results"),

    url(r'^save_form/$',
        csrf_exempt(views.MultiseekSaveForm.as_view(
            registry=settings.MULTISEEK_REGISTRY
        )), name="save_form"),

    url(r'^reset/$',
        csrf_exempt(views.reset_form),
        name="reset"),

    url(r'^remove-from-results/(?P<pk>\d+)$',
        views.remove_by_hand,
        name="remove_from_results"),

    url(r'^remove-from-removed-results/(?P<pk>\d+)$',
        views.remove_from_removed_by_hand,
        name="remove_from_removed_results"),

    url(r'^reenable-removed-ids/$',
        views.reenable_removed_by_hand,
        name="reenable_removed_ids"),

   url(r'^load_form/(?P<search_form_pk>\d+)',
        load_form,
        name="load_form")
]