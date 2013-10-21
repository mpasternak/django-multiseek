from django.conf.urls import patterns, include, url

import autocomplete_light
autocomplete_light.autodiscover()

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'test_app.views.root'),
    url(r'^multiseek/', include('multiseek.urls', namespace='multiseek')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
