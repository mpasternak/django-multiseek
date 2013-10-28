# -*- encoding: utf-8 -*-

from django.conf.urls import patterns, url
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from multiseek import views
from multiseek.views import load_form, MultiseekModelRouter

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('multiseek',),
}

urlpatterns = patterns(
    '',

    url(r'^jsi18n/$',
        'django.views.i18n.javascript_catalog',
        js_info_dict,
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

    url(r'^load_form/(?P<search_form_pk>\d+)',
        load_form,
        name="load_form"),

    url(r'^autocomplete/(?P<model>.*)/$', MultiseekModelRouter.as_view(
        registry=settings.MULTISEEK_REGISTRY
    ))

)