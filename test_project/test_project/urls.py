from django.conf.urls import patterns, include, url

from django.contrib import admin

admin.autodiscover()

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('multiseek',),
}

urlpatterns = patterns(
    '',
    url(r'^$', 'test_app.views.root'),
    url(r'^multiseek/', include('multiseek.urls', namespace='multiseek')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^i18n/$',
        'django.views.i18n.javascript_catalog',
        js_info_dict,
        name="js_i18n_catalog")
)
