# -*- encoding: utf-8 -*-
import json
from builtins import str as text

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.test.client import RequestFactory
from mock import MagicMock
from model_bakery import baker
from test_app import multiseek_registry
from test_app.models import Author

from multiseek.logic import (
    EQUAL,
    EQUALITY_OPS_ALL,
    AutocompleteQueryObject,
    StringQueryObject,
    ValueListQueryObject,
    create_registry,
)
from multiseek.models import SearchForm
from multiseek.views import (
    ERR_FORM_NAME,
    ERR_LOADING_DATA,
    ERR_NO_FORM_DATA,
    ERR_PARSING_DATA,
    MULTISEEK_SESSION_KEY,
    OVERWRITE_PROMPT,
    MultiseekFormPage,
    MultiseekResults,
    MultiseekSaveForm,
    get_registry,
    load_form,
    reset_form,
    user_allowed_to_save_forms,
)


class Session(dict):
    def save(self):
        return None


def setup_anonymous_session(request):
    request.user = AnonymousUser()
    request.session = Session()
    return request


class MockupAutocompleteQueryObject(AutocompleteQueryObject):
    def get_url(self):
        return "/LOL/"


class RegistryMixin:
    def setUp(self):
        self.registry = create_registry(
            None,
            StringQueryObject("foo"),
            StringQueryObject("bar"),
            ValueListQueryObject(field_name="baz", values=["a", "b", "c"]),
            MockupAutocompleteQueryObject(field_name="quux", model=Author),
        )

        self.request = setup_anonymous_session(RequestFactory().get("/"))


class TestViews(RegistryMixin, TestCase):
    def test_new_page(self):
        mfp = MultiseekFormPage(registry=self.registry)
        mfp.request = self.request
        mfp.get_context_data()

    def test_multiseek(self):
        self.request.session[MULTISEEK_SESSION_KEY] = json.dumps(
            {
                "form_data": [
                    None,
                    dict(
                        field="foo",
                        prev_op="or",
                        operator=text(EQUALITY_OPS_ALL[0]),
                        value="foo",
                    ),
                ]
            }
        )

        mfp = MultiseekFormPage(registry=self.registry)
        mfp.request = self.request

        ret = mfp.get_context_data()

        self.assertEqual(ret["js_fields"], '["foo", "bar", "baz", "quux"]')
        self.assertEqual(ret["js_autocompletes"], '{"quux": "/LOL/"}')
        self.assertEqual(ret["js_value_lists"], '{"baz": ["a", "b", "c"]}')
        self.assertEqual(
            ret["js_init"],
            u"$('#frame-0').multiseekFrame('addField', 'foo', 'equals', 'foo', 'or');\n",
        )

    def test_reset_form(self):
        self.request.session[MULTISEEK_SESSION_KEY] = "123"
        reset_form(self.request)

        self.assertEqual(self.request.session, {})

        # No error on subsequent calls
        reset_form(self.request)

    def test_get_registry(self):
        self.assertEqual(get_registry({}), {})

        self.assertEqual(
            get_registry("test_app.multiseek_registry"), multiseek_registry.registry
        )

    def test_user_allowed_to_save_forms(self):
        class MockUser:
            is_staff = True

        self.assertEqual(user_allowed_to_save_forms(MockUser), MockUser.is_staff)
        MockUser.is_staff = False
        self.assertEqual(user_allowed_to_save_forms(MockUser), MockUser.is_staff)

        class MockUserWithout:
            pass

        self.assertEqual(user_allowed_to_save_forms(MockUserWithout), None)


class TestMultiseekSaveForm(RegistryMixin, TestCase):
    def setUp(self):
        RegistryMixin.setUp(self)
        self.msp = MultiseekSaveForm(registry=self.registry)
        self.msp.request = self.request

    def test_save_form_anon_user(self):
        res = self.msp.post(self.request)
        self.assertEqual(res.status_code, 403)

        self.assertEqual(self.msp.post, self.msp.get)

    def test_get_context_data(self):
        self.request.POST = {}

        self.request.POST["json"] = None
        self.assertEqual(
            self.msp.get_context_data(), dict(result=text(ERR_NO_FORM_DATA))
        )

        self.request.POST["json"] = "wcale, nie, json"
        self.assertEqual(
            self.msp.get_context_data(), dict(result=text(ERR_PARSING_DATA))
        )

        self.request.POST["json"] = '[{"field": "foo", "bad": "field"}]'
        self.assertEqual(
            self.msp.get_context_data(), dict(result=text(ERR_LOADING_DATA))
        )

        self.request.POST["json"] = (
            '{"form_data": [{"field": "foo", "operation": "'
            + text(EQUAL)
            + '", "value": "foo"}]}'
        )
        self.request.POST["name"] = ""
        self.assertEqual(self.msp.get_context_data(), dict(result=text(ERR_FORM_NAME)))

        baker.make(SearchForm, name="foo")
        self.request.POST["name"] = "foo"
        self.assertEqual(self.msp.get_context_data(), dict(result=OVERWRITE_PROMPT))

        self.request.POST["overwrite"] = "true"
        self.request.user = baker.make(User)
        self.assertEqual(
            self.msp.get_context_data()["result"], "saved"
        )  # dict(result=SAVED, pk=1))

        self.assertEqual(SearchForm.objects.all().count(), 1)
        self.assertEqual(SearchForm.objects.all()[0].public, False)

        self.request.POST["public"] = "true"
        self.msp.get_context_data()
        self.assertEqual(SearchForm.objects.all()[0].public, True)


class TestMultiseekLoadForm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("test", "test@foo.pl", "test")

        self.anon_req = setup_anonymous_session(RequestFactory().get("/"))

        self.normal_req = RequestFactory().get("/")
        self.normal_req.user = self.user
        self.normal_req.session = Session()

    def test_load_form_unexistent(self):
        res = load_form(self.anon_req, 1)
        self.assertEqual(res.status_code, 404)

    def test_load_form_existent_public_ok(self):
        sf = SearchForm.objects.create(
            name="foo", owner=self.user, public=True, data="some data"
        )
        res = load_form(self.anon_req, sf.pk)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.anon_req.session[MULTISEEK_SESSION_KEY], sf.data)

    def test_load_form_forbidden(self):
        sf = SearchForm.objects.create(
            name="foo", owner=self.user, public=False, data="some data"
        )
        res = load_form(self.anon_req, sf.pk)
        self.assertEqual(res.status_code, 403)

    def test_load_form_non_public_logged_in_user(self):
        sf = SearchForm.objects.create(
            name="foo", owner=self.user, public=False, data="some data"
        )
        res = load_form(self.normal_req, sf.pk)
        self.assertEqual(res.status_code, 302)


class TestMultiseekResults(RegistryMixin, TestCase):
    def setUp(self):
        RegistryMixin.setUp(self)
        self.registry.model = MagicMock()
        self.mr = MultiseekResults(registry=self.registry)
        self.mr.request = self.request
        self.request.session[MULTISEEK_SESSION_KEY] = json.dumps(
            {
                "form_data": [
                    None,
                    {
                        "field": text(self.registry.fields[0].label),
                        "operator": text(self.registry.fields[0].ops[0]),
                        "value": u"foobar",
                    },
                ]
            }
        )

    def test_post(self):
        res = self.mr.post(self.request)
        self.assertEqual(res.status_code, 200)

    def test_get_queryset(self):
        self.mr.get_queryset()

    def test_describe_multiseek_data(self):
        self.mr.post(self.request)
        res = self.mr.describe_multiseek_data()
        self.assertEqual(res, 'foo contains "foobar"')
