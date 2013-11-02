# -*- encoding: utf-8 -*-
from django.db.models.query_utils import Q
from django.http.response import HttpResponse, Http404
from django.utils import simplejson
from django.views.generic.base import View

import json

from django import shortcuts, http
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.views.generic import TemplateView, ListView
from django.utils.translation import ugettext_lazy as _

from .logic import VALUE_LIST, AUTOCOMPLETE, AND, OR, get_registry, \
    UnknownOperation, ParseError, UnknownField, MULTISEEK_ORDERING_PREFIX
from multiseek.logic import MULTISEEK_REPORT_TYPE
from multiseek.models import SearchForm

SAVED = 'saved'
OVERWRITE_PROMPT = 'overwrite-prompt'

ERR_FORM_NAME = _("Form name must not be empty")
ERR_LOADING_DATA = _("Error while loading form data")
ERR_PARSING_DATA = _("Error while parsing form data")
ERR_NO_FORM_DATA = _("No form data provided")

MULTISEEK_SESSION_KEY = 'multiseek_json'


def reverse_or_just_url(s):
    if s.startswith('/'):
        return s
    return reverse(s)


LAST_FIELD_REMOVE_MESSAGE = \
    _("The ability to remove the last field has been disabled.")


def user_allowed_to_save_forms(user):
    if hasattr(user, 'is_staff'):
        return user.is_staff


class MultiseekPageMixin:
    registry = None


class MultiseekFormPage(MultiseekPageMixin, TemplateView):
    """
    This view renders multiseek form and javascript required to manipulate
    it.
    """

    def get_context_data(self):
        registry = get_registry(self.registry)

        public = self.request.user.is_anonymous()

        fields = registry.get_fields(public)

        js_fields = json.dumps([unicode(x.label) for x in fields])
        js_ops = json.dumps(dict(
            [(unicode(f.label), [unicode(x) for x in f.ops]) for f in fields]))
        js_types = json.dumps(
            dict([(unicode(f.label), f.type) for f in fields]))

        js_autocompletes = json.dumps(
            dict([(unicode(field.label), reverse_or_just_url(field.get_url()))
                  for field in registry.field_by_type(
                    AUTOCOMPLETE, public)]))

        js_value_lists = json.dumps(
            dict([
                (unicode(field.label), [unicode(x) for x in field.values])
                for field in registry.field_by_type(VALUE_LIST, public)]))

        js_init = None
        if self.request.session.get(MULTISEEK_SESSION_KEY):
            js_init = registry.recreate_form(json.loads(
                self.request.session.get(MULTISEEK_SESSION_KEY)))

        return dict(
            js_fields=js_fields, js_ops=js_ops, js_types=js_types,
            js_autocompletes=js_autocompletes, js_value_lists=js_value_lists,
            js_and=AND, js_or=OR, js_init=js_init,
            js_remove_message=LAST_FIELD_REMOVE_MESSAGE,
            user_allowed_to_save_forms=user_allowed_to_save_forms(
                self.request.user),
            order_boxes=registry.order_boxes,
            ordering=registry.ordering,
            report_types=registry.get_report_types(only_public=public),
            saved_forms=SearchForm.objects.get_for_user(self.request.user),
            MULTISEEK_ORDERING_PREFIX=MULTISEEK_ORDERING_PREFIX,
            MULTISEEK_REPORT_TYPE=MULTISEEK_REPORT_TYPE)


def reset_form(request):
    try:
        del request.session[MULTISEEK_SESSION_KEY]
    except KeyError:
        pass
    return shortcuts.redirect("..")


def load_form(request, search_form_pk):
    try:
        sf = SearchForm.objects.get(pk=search_form_pk)
    except SearchForm.DoesNotExist:
        return HttpResponseNotFound()

    if request.user.is_anonymous() and not sf.public:
        return HttpResponseForbidden()

    request.session[MULTISEEK_SESSION_KEY] = sf.data
    return shortcuts.redirect("..")


class JSONResponseMixin(object):
    def render_to_response(self, context):
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        return http.HttpResponse(
            content, content_type='application/json', **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        return json.dumps(context)


class MultiseekSaveForm(MultiseekPageMixin, JSONResponseMixin, TemplateView):
    def get(self, request, *args, **kw):
        if not user_allowed_to_save_forms(request.user):
            return HttpResponseForbidden()
        return super(MultiseekSaveForm, self).get(request, *args, **kw)

    post = get

    @transaction.commit_on_success
    def get_context_data(self):
        _json = self.request.POST.get('json')
        name = self.request.POST.get("name")
        public = self.request.POST.get("public") == 'true'
        overwrite = self.request.POST.get('overwrite') == 'true'

        if not _json:
            return dict(result=unicode(ERR_NO_FORM_DATA))

        try:
            json.loads(_json)
        except ValueError:
            return dict(result=unicode(ERR_PARSING_DATA))

        try:
            get_registry(self.registry).recreate_form(json.loads(_json))
        except (TypeError, UnknownField, ParseError, UnknownOperation):
            return dict(result=unicode(ERR_LOADING_DATA))

        if not name:
            return dict(result=unicode(ERR_FORM_NAME))

        if SearchForm.objects.filter(name=name).count():
            if not overwrite:
                return dict(result=OVERWRITE_PROMPT)

            obj = SearchForm.objects.get(name=name)
            obj.public = public
            obj.data = _json
            obj.owner = self.request.user
            obj.save()

        else:
            obj = SearchForm.objects.create(
                name=name, public=public, data=_json, owner=self.request.user)

        return dict(result=SAVED, pk=obj.pk)


class MultiseekResults(MultiseekPageMixin, ListView):
    registry = None
    _json_cache = None

    def post(self, request, *args, **kwargs):
        if 'json' in request.POST:
            j = request.POST['json']
            session = request.session
            session[MULTISEEK_SESSION_KEY] = j
            session.save()
        return super(MultiseekResults, self).get(request, *args, **kwargs)

    def get_multiseek_data(self):
        if not self._json_cache:
            _json = self.request.session.get(MULTISEEK_SESSION_KEY)
            if _json is not None:
                self._json_cache = json.loads(_json)
        return self._json_cache

    def get_context_data(self, **kwargs):
        public = self.request.user.is_anonymous()
        report_type = get_registry(
            self.registry).get_report_type(
            self.get_multiseek_data(),
            only_public=public)

        return super(ListView, self).get_context_data(
            report_type=report_type, **kwargs)

    def get_queryset(self):
        # TODO: jeżeli w sesji jest obiekt, którego NIE DA się sparse'ować, to wówczas błąd podnoś i to samo w klasie MultiseekFormPage
        return get_registry(self.registry).get_query_for_model(
            self.get_multiseek_data())


class MultiseekModelRouter(View):
    registry = None
    def get(self, request, model, *args, **kw):
        registry = get_registry(self.registry)
        for field in registry.fields:
            if field.type == AUTOCOMPLETE:
                if field.model.__name__ == model:
                    return MultiseekModelAutocomplete(qobj=field).get(request)
        raise Http404


class MultiseekModelAutocomplete(View):
    # TODO: JSONResponseMixin
    qobj = None
    max_items = 10

    def get_queryset(self, request):
        return self.qobj.model.objects.all()

    def prepare_search_query(self, data):

        def args(fld, elem):
            return {fld + "__icontains": elem}

        # split by comma, space, etc.
        data = data.split(" ")

        ret = Q(**args(self.qobj.search_fields[0], data[0]))
        for f, v in zip(self.qobj.search_fields[1:], data[1:]):
            ret = ret & Q(**args(f, v))
        return ret

    def get(self, request, *args, **kwargs):
        q = request.GET.get('term', None)

        qset = self.get_queryset(request)
        if q:
            qset = qset.filter(self.prepare_search_query(q))

        ret = []
        for elem in qset[:self.max_items]:
            ret.append(
                {'id': elem.pk,
                 'label': self.qobj.get_label(elem),
                 'value': self.qobj.get_label(elem)})

        return HttpResponse(simplejson.dumps(ret),
                            mimetype='application/json')