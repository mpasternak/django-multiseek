from django.conf.urls import patterns, include, url

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'test_app.views.root'),
    url(r'^multiseek/', include('multiseek.urls', namespace='multiseek')),

    url(r'^admin/', include(admin.site.urls)),
)
