# -*- encoding: utf-8 -*-
import json

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.test.client import RequestFactory
from mock import MagicMock
from model_mommy import mommy

from multiseek.logic import create_registry, StringQueryObject, \
    ValueListQueryObject, AutocompleteQueryObject, EQUALITY_OPS_ALL, EQUAL
from multiseek.models import SearchForm
from multiseek.views import MultiseekFormPage, MULTISEEK_SESSION_KEY, \
    reset_form, get_registry, user_allowed_to_save_forms, MultiseekSaveForm, \
    ERR_NO_FORM_DATA, ERR_PARSING_DATA, ERR_LOADING_DATA, ERR_FORM_NAME, \
    OVERWRITE_PROMPT, SAVED, load_form, MultiseekResults
from test_app import multiseek_registry
from test_app.models import Author


class Session(dict):
    def save(self):
        return None


def setup_anonymous_session(request):
    request.user = AnonymousUser()
    request.session = Session()
    return request


class RegistryMixin:

    def setUp(self):
        self.registry = create_registry(
            None,
            StringQueryObject('foo'),
            StringQueryObject('bar'),
            ValueListQueryObject(field_name='baz', values=['a', 'b', 'c']),
            AutocompleteQueryObject(field_name='quux', url='/LOL/', model=Author)
            )

        self.request = setup_anonymous_session(RequestFactory().get('/'))


class TestViews(RegistryMixin, TestCase):

    def test_new_page(self):
        mfp = MultiseekFormPage(registry=self.registry)
        mfp.request = self.request
        ret = mfp.get_context_data()

    def test_multiseek(self):
        self.request.session[MULTISEEK_SESSION_KEY] = json.dumps(
            {'form_data':
                 [None, dict(field="foo", prev_op="or", operator=unicode(EQUALITY_OPS_ALL[0]), value="foo")]})

        mfp = MultiseekFormPage(registry=self.registry)
        mfp.request = self.request

        ret = mfp.get_context_data()

        self.assertEquals(ret['js_fields'], '["foo", "bar", "baz", "quux"]')
        self.assertEquals(ret['js_autocompletes'], '{"quux": "/LOL/"}')
        self.assertEquals(ret['js_value_lists'], '{"baz": ["a", "b", "c"]}')
        self.assertEquals(
            ret['js_init'],
            u"$('#frame-0').multiseekFrame('addField', 'foo', 'equals', 'foo', 'or');\n")

    def test_reset_form(self):
        self.request.session[MULTISEEK_SESSION_KEY] = '123'
        ret = reset_form(self.request)

        self.assertEquals(self.request.session, {})

        # No error on subsequent calls
        reset_form(self.request)

    def test_get_registry(self):
        self.assertEquals(get_registry({}), {})

        self.assertEquals(
            get_registry('test_app.multiseek_registry'),
            multiseek_registry.registry)

    def test_user_allowed_to_save_forms(self):
        class MockUser:
            is_staff = True

        self.assertEquals(user_allowed_to_save_forms(MockUser), MockUser.is_staff)
        MockUser.is_staff = False
        self.assertEquals(user_allowed_to_save_forms(MockUser), MockUser.is_staff)

        class MockUserWithout:
            pass

        self.assertEquals(user_allowed_to_save_forms(MockUserWithout), None)

class TestMultiseekSaveForm(RegistryMixin, TestCase):

    def setUp(self):
        RegistryMixin.setUp(self)
        self.msp = MultiseekSaveForm(registry=self.registry)
        self.msp.request = self.request

    def test_save_form_anon_user(self):
        res = self.msp.post(self.request)
        self.assertEquals(res.status_code, 403)

        self.assertEquals(self.msp.post, self.msp.get)

    def test_get_context_data(self):
        self.request.POST = {}
        
        self.request.POST['json'] = None
        self.assertEquals(
            self.msp.get_context_data(), 
            dict(result=unicode(ERR_NO_FORM_DATA)))
        
        self.request.POST['json'] = "wcale, nie, json"
        self.assertEquals(
            self.msp.get_context_data(),
            dict(result=unicode(ERR_PARSING_DATA)))
        
        self.request.POST['json'] = '[{"field": "foo", "bad": "field"}]'
        self.assertEquals(
            self.msp.get_context_data(),
            dict(result=unicode(ERR_LOADING_DATA)))
        
        self.request.POST['json'] = \
            '{"form_data": [{"field": "foo", "operation": "' \
            + unicode(EQUAL) \
            + '", "value": "foo"}]}'
        self.request.POST['name'] = ''
        self.assertEquals(
            self.msp.get_context_data(),
            dict(result=unicode(ERR_FORM_NAME)))

        sf = mommy.make(SearchForm, name='foo')
        self.request.POST['name'] = 'foo'
        self.assertEquals(
            self.msp.get_context_data(),
            dict(result=OVERWRITE_PROMPT))

        self.request.POST['overwrite'] = 'true'
        self.request.user = mommy.make(User)
        self.assertEquals(
            self.msp.get_context_data()['result'],
            'saved') # dict(result=SAVED, pk=1))

        self.assertEquals(SearchForm.objects.all().count(), 1)
        self.assertEquals(SearchForm.objects.all()[0].public, False)

        self.request.POST['public'] = 'true'
        self.msp.get_context_data()
        self.assertEquals(SearchForm.objects.all()[0].public, True)


class TestMultiseekLoadForm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@foo.pl', 'test')

        self.anon_req = setup_anonymous_session(RequestFactory().get('/'))

        self.normal_req = RequestFactory().get('/')
        self.normal_req.user = self.user
        self.normal_req.session = Session()

    def test_load_form_unexistent(self):
        res = load_form(self.anon_req, 1)
        self.assertEquals(res.status_code, 404)

    def test_load_form_existent_public_ok(self):
        sf = SearchForm.objects.create(
            name='foo', owner=self.user, public=True, data='some data')
        res = load_form(self.anon_req, sf.pk)
        self.assertEquals(res.status_code, 302)
        self.assertEquals(
            self.anon_req.session[MULTISEEK_SESSION_KEY],
            sf.data)

    def test_load_form_forbidden(self):
        sf = SearchForm.objects.create(
            name='foo', owner=self.user, public=False, data='some data')
        res = load_form(self.anon_req, sf.pk)
        self.assertEquals(res.status_code, 403)

    def test_load_form_non_public_logged_in_user(self):
        sf = SearchForm.objects.create(
            name='foo', owner=self.user, public=False, data='some data')
        res = load_form(self.normal_req, sf.pk)
        self.assertEquals(res.status_code, 302)


class TestMultiseekResults(RegistryMixin, TestCase):

    def setUp(self):
        RegistryMixin.setUp(self)
        self.registry.model = MagicMock()
        self.mr = MultiseekResults(registry=self.registry)
        self.mr.request = self.request
        self.request.session[MULTISEEK_SESSION_KEY] = json.dumps(
            {'form_data': [{'field': unicode(self.registry.fields[0].label),
              'operation': unicode(self.registry.fields[0].ops[0]),
              'value': u'foobar'}]})

    def test_post(self):
        res = self.mr.post(self.request)
        self.assertEquals(res.status_code, 200)

    def test_get_queryset(self):
        res = self.mr.get_queryset()
