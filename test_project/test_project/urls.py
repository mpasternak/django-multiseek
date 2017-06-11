from django.conf import settings
from django.conf.urls import include, url, static

from django.contrib import admin
from django.views.i18n import javascript_catalog
from test_app.views import root

admin.autodiscover()

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('multiseek',),
}

urlpatterns = [
    url(r'^$', root),
    url(r'^multiseek/', include('multiseek.urls', namespace='multiseek')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^i18n/$',
        javascript_catalog,
        js_info_dict,
        name="js_i18n_catalog")

] + static.static(settings.STATIC_URL,
                  document_root=settings.STATIC_ROOT,
                  show_indexes=True)
