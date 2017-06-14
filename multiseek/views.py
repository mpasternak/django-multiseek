# -*- encoding: utf-8 -*-
import json

from django.http.response import HttpResponse, Http404, HttpResponseServerError, \
    HttpResponseRedirect
from django.views.generic.base import View
from django import shortcuts, http
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.views.generic import TemplateView, ListView
from django.utils.translation import ugettext_lazy as _, ugettext_lazy

import simplejson
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
MULTISEEK_SESSION_KEY_REMOVED = 'multiseek_json_removed'


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

        def get_values(values):
            if callable(values):
                return values()
            return values

        js_value_lists = json.dumps(
            dict([
                (unicode(field.label), [unicode(x) for x in get_values(field.values)])
                for field in registry.field_by_type(VALUE_LIST, public)]))

        initialize_empty_form = True
        form_data = self.request.session.get(MULTISEEK_SESSION_KEY, {})
        if form_data:
            form_data = json.loads(form_data)
            initialize_empty_form = False
        js_init = registry.recreate_form(form_data)

        js_removed = ",".join('"%s"' %x for x in self.request.session.get(MULTISEEK_SESSION_KEY_REMOVED, []))

        return dict(
            js_fields=js_fields, js_ops=js_ops, js_types=js_types,
            js_autocompletes=js_autocompletes, js_value_lists=js_value_lists,
            js_and=AND, js_or=OR, js_init=js_init,
            js_remove_message=LAST_FIELD_REMOVE_MESSAGE,
            js_removed=js_removed,
            user_allowed_to_save_forms=user_allowed_to_save_forms(
                self.request.user),
            initialize_empty_form=initialize_empty_form,
            order_boxes=registry.order_boxes,
            ordering=registry.ordering,
            report_types=registry.get_report_types(only_public=public),
            saved_forms=SearchForm.objects.get_for_user(self.request.user),
            MULTISEEK_ORDERING_PREFIX=MULTISEEK_ORDERING_PREFIX,
            MULTISEEK_REPORT_TYPE=MULTISEEK_REPORT_TYPE)


def reset_form(request):
    for key in [MULTISEEK_SESSION_KEY, MULTISEEK_SESSION_KEY_REMOVED]:
        if request.session.has_key(key):
            del request.session[key]
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

    @transaction.atomic
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
            if self._json_cache is None:
                self._json_cache = {}
            if self._json_cache.get("ordering") is None:
                self._json_cache['ordering'] = get_registry(self.registry).default_ordering
        return self._json_cache

    def get_removed_records(self):
        return self.request.session.get(MULTISEEK_SESSION_KEY_REMOVED, [])

    def describe_multiseek_data(self):
        """Returns a string with a nicely-formatted query, so you can
        display the query to the user, in a results window, for example.
        """
        data = self.get_multiseek_data()
        registry = get_registry(self.registry)

        ugettext_lazy("andnot") # Leave this line.

        def _recur(d):
            cur = 0
            ret = u''

            while cur < len(d):

                if type(d[cur]) == list:
                    if d[cur][0] != None:
                        ret += u' <b>' + unicode(
                            ugettext_lazy(d[cur][0])).upper() + u'</b> '
                    ret += u'(' + _recur(d[cur][1:]) + u')'
                else:
                    f = registry.get_field_by_name(d[cur]['field'])

                    impacts_query = f.impacts_query(
                        d[cur]['operator'], d[cur]['value'])

                    value = f.value_for_description(d[cur]['value'])

                    if impacts_query:

                        if d[cur].has_key('prev_op') and d[cur]['prev_op'] != None:
                            tmp = d[cur]['prev_op']
                            ret += u' <b>' + unicode(
                                ugettext_lazy(tmp)).upper() + u'</b> '


                        ret += '%s %s %s' % (d[cur]['field'].lower(),
                                             d[cur]['operator'],
                                             value)

                cur += 1

            return ret



        if data is None:
            return u''
        if not data.get('form_data'):
            return u''

        return _recur(data['form_data'][1:])

    def get_context_data(self, **kwargs):
        public = self.request.user.is_anonymous()
        report_type = get_registry(self.registry) \
            .get_report_type(self.get_multiseek_data(),
                             only_public=public)
        description = self.describe_multiseek_data()
        removed_ids = self.get_removed_records()

        return super(ListView, self).get_context_data(
            report_type=report_type, description=description,
            removed_ids=removed_ids, **kwargs)

    def get_queryset(self):
        # TODO: jeżeli w sesji jest obiekt, którego NIE DA się sparse'ować, to wówczas błąd podnoś i to samo w klasie MultiseekFormPage
        return get_registry(self.registry).get_query_for_model(
            self.get_multiseek_data(),
            self.request.session.get(MULTISEEK_SESSION_KEY_REMOVED, []))


class MultiseekModelRouter(View):
    registry = None

    def get(self, request, model, *args, **kw):
        registry = get_registry(self.registry)
        for field in registry.fields:
            if field.type == AUTOCOMPLETE:
                if model == field.model.__name__:
                    return MultiseekModelAutocomplete(original=field).get(request)
        raise Http404


class MultiseekModelAutocomplete(View):
    # TODO: JSONResponseMixin
    qobj = None
    max_items = 10

    def get_queryset(self, request):
        return self.qobj.model.objects.all()

    def get(self, request, *args, **kwargs):
        q = request.GET.get('term', '').encode('utf-8')

        qset = self.original.get_autocomplete_query(q)

        ret = []
        for elem in qset[:self.max_items]:
            ret.append(
                {'id': elem.pk,
                 'label': self.original.get_autocomplete_label(elem),
                 'value': self.original.get_autocomplete_label(elem)})

        return HttpResponse(simplejson.dumps(ret),
                            content_type='application/json')


JSON_OK = HttpResponse(simplejson.dumps({'status':"OK"}), content_type='application/json')

def manually_add_or_remove(request, pk, add=True):
    data = request.session.get(MULTISEEK_SESSION_KEY_REMOVED, [])
    data = set(data)

    if add:
        if len(data) < 2048:
            data.add(pk)
        else:
            # Prevent DOS OOM attack
            return HttpResponseForbidden()

    else:
        try:
            data.remove(pk)
        except KeyError:
            pass

    request.session[MULTISEEK_SESSION_KEY_REMOVED] = list(data)

    return JSON_OK


def remove_by_hand(request, pk):
    """Add a record's PK to a list of manually removed records.

    User, via the web ui, can add or remove a record to a list of records
    removed "by hand". Those records will be explictly removed
    from the search results in the query function. The list of those
    records is cleaned when there is a form reset.
    """
    return manually_add_or_remove(request, pk)

def remove_from_removed_by_hand(request, pk):
    """Cancel manual record removal."""
    return manually_add_or_remove(request, pk, add=False)

def reenable_removed_by_hand(request):
    request.session[MULTISEEK_SESSION_KEY_REMOVED] = []
    return HttpResponseRedirect(request.META.get('HTTP_REFERER') or '..')
