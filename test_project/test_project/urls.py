from django.conf import settings
from django.conf.urls import include, static
try:
    from django.conf.urls import url
except ImportError:
    from django.urls import re_path as url

from django.contrib import admin
from django.views.i18n import JavaScriptCatalog

from test_app.views import root, AuthorAutocomplete

admin.autodiscover()


urlpatterns = [
    url(r'^$', root),
    url(r'^author_autocomplete/$', AuthorAutocomplete.as_view(), name="author-autocomplete"),
    url(r'^multiseek/', include(('multiseek.urls', 'multiseek'), namespace="multiseek")),

    url(r'^admin/', admin.site.urls),

    url(r'^i18n/$',
        JavaScriptCatalog.as_view(packages=['multiseek']),
        name="js_i18n_catalog")

] + static.static(settings.STATIC_URL,
                  document_root=settings.STATIC_ROOT,
                  show_indexes=True)
