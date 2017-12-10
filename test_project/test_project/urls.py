from django.conf import settings
from django.conf.urls import include, url, static

from django.contrib import admin
from django.views.i18n import JavaScriptCatalog

from test_app.views import root

admin.autodiscover()


urlpatterns = [
    url(r'^$', root),
    url(r'^multiseek/', include(('multiseek.urls', 'multiseek'), namespace="multiseek")),

    url(r'^admin/', admin.site.urls),

    url(r'^i18n/$',
        JavaScriptCatalog.as_view(packages=['multiseek']),
        name="js_i18n_catalog")

] + static.static(settings.STATIC_URL,
                  document_root=settings.STATIC_ROOT,
                  show_indexes=True)
