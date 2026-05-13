import json
from unittest.mock import MagicMock

from django.contrib.auth.models import AnonymousUser, User
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.urls import resolve
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
    MULTISEEK_SESSION_KEY_REMOVED,
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
                        operator=str(EQUALITY_OPS_ALL[0]),
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
            "$('#frame-0').multiseekFrame('addField', 'foo', 'equals', 'foo', 'or');\n",
        )

    def test_reset_form(self):
        self.request.session[MULTISEEK_SESSION_KEY] = "123"
        reset_form(self.request)

        self.assertEqual(self.request.session, {})

        # No error on subsequent calls
        reset_form(self.request)

    def test_get_registry(self):
        self.assertEqual(get_registry({}), {})

        self.assertEqual(get_registry("test_app.multiseek_registry"), multiseek_registry.registry)

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
        self.assertEqual(self.msp.get_context_data(), dict(result=str(ERR_NO_FORM_DATA)))

        self.request.POST["json"] = "wcale, nie, json"
        self.assertEqual(self.msp.get_context_data(), dict(result=str(ERR_PARSING_DATA)))

        self.request.POST["json"] = '[{"field": "foo", "bad": "field"}]'
        self.assertEqual(self.msp.get_context_data(), dict(result=str(ERR_LOADING_DATA)))

        self.request.POST["json"] = (
            '{"form_data": [{"field": "foo", "operation": "' + str(EQUAL) + '", "value": "foo"}]}'
        )
        self.request.POST["name"] = ""
        self.assertEqual(self.msp.get_context_data(), dict(result=str(ERR_FORM_NAME)))

        baker.make(SearchForm, name="foo")
        self.request.POST["name"] = "foo"
        self.assertEqual(self.msp.get_context_data(), dict(result=OVERWRITE_PROMPT))

        self.request.POST["overwrite"] = "true"
        self.request.user = baker.make(User)
        self.assertEqual(self.msp.get_context_data()["result"], "saved")  # dict(result=SAVED, pk=1))

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
        sf = SearchForm.objects.create(name="foo", owner=self.user, public=True, data="some data")
        res = load_form(self.anon_req, sf.pk)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.anon_req.session[MULTISEEK_SESSION_KEY], sf.data)

    def test_load_form_forbidden(self):
        sf = SearchForm.objects.create(name="foo", owner=self.user, public=False, data="some data")
        res = load_form(self.anon_req, sf.pk)
        self.assertEqual(res.status_code, 403)

    def test_load_form_non_public_logged_in_user(self):
        sf = SearchForm.objects.create(name="foo", owner=self.user, public=False, data="some data")
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
                        "field": str(self.registry.fields[0].label),
                        "operator": str(self.registry.fields[0].ops[0]),
                        "value": "foobar",
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

    def test_describe_multiseek_data_escapes_xss_in_prev_op(self):
        """Issue #4: prev_op from user JSON must be HTML-escaped before being
        concatenated into description, which the template renders with `|safe`.

        Pre-fix, gettext_lazy(prev_op).upper() passes through the malicious
        string, then it's wrapped in <b>...</b> and returned raw.
        """
        self.request.session[MULTISEEK_SESSION_KEY] = json.dumps(
            {
                "form_data": [
                    None,
                    {
                        "field": str(self.registry.fields[0].label),
                        "operator": str(self.registry.fields[0].ops[0]),
                        "value": "x",
                        "prev_op": None,
                    },
                    {
                        "field": str(self.registry.fields[0].label),
                        "operator": str(self.registry.fields[0].ops[0]),
                        "value": "y",
                        "prev_op": "<script>alert(1)</script>",
                    },
                ]
            }
        )
        self.mr.post(self.request)
        res = self.mr.describe_multiseek_data()
        self.assertNotIn("<script>", res.lower())

    def test_remove_by_hand_returns_400_when_list_full(self):
        """Issue #10: the 'manual exclusion list' cap at 2048 returned 403
        (Forbidden) for what is actually a request-shape problem. Bad
        Request is the correct semantic; clients can distinguish 400
        from real auth failures."""
        from django.test import Client

        client = Client()
        # Pre-populate the cap with a fresh session.
        session = client.session
        session[MULTISEEK_SESSION_KEY_REMOVED] = list(range(2048))
        session.save()
        # Adding one more must be rejected with 400, not 403.
        resp = client.get("/multiseek/remove-from-results/9999")
        self.assertEqual(resp.status_code, 400)

    def test_describe_multiseek_data_escapes_xss_in_operator(self):
        """Issue #4: operator from user JSON must be HTML-escaped.

        StringQueryObject.impacts_query() returns True for any non-empty
        value paired with any operator string, so an arbitrary operator
        reaches the description concatenation.
        """
        self.request.session[MULTISEEK_SESSION_KEY] = json.dumps(
            {
                "form_data": [
                    None,
                    {
                        "field": str(self.registry.fields[0].label),
                        "operator": "<img src=x onerror=alert(1)>",
                        "value": "y",
                        "prev_op": None,
                    },
                ]
            }
        )
        self.mr.post(self.request)
        res = self.mr.describe_multiseek_data()
        self.assertNotIn("<img", res.lower())


class TestCSRFProtection(TestCase):
    """Regression tests for Issue #2.

    Pre-fix every multiseek URL was wrapped in csrf_exempt, so POSTs
    succeeded without a token — letting any cross-site request ride a
    staff user's session to overwrite saved searches or pollute the
    results-session JSON. Post-fix the views are CSRF-protected and
    POSTs without a valid token must return 403.
    """

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def test_results_post_without_csrf_token_is_forbidden(self):
        resp = self.client.post("/multiseek/results/", {"json": "{}"})
        self.assertEqual(resp.status_code, 403)

    def test_save_form_post_without_csrf_token_is_forbidden(self):
        staff = baker.make(User, is_staff=True)
        self.client.force_login(staff)
        resp = self.client.post(
            "/multiseek/save_form/",
            {"json": '{"form_data": [null]}', "name": "x"},
        )
        self.assertEqual(resp.status_code, 403)

    def test_results_post_with_csrf_token_is_allowed(self):
        # Visiting the form page renders {% csrf_token %}, which sets
        # the csrftoken cookie via Django's CSRF middleware.
        self.client.get("/multiseek/")
        token = self.client.cookies["csrftoken"].value
        resp = self.client.post(
            "/multiseek/results/",
            {"json": "{}", "csrfmiddlewaretoken": token},
        )
        self.assertNotEqual(resp.status_code, 403)

    def test_save_form_post_with_csrf_token_is_allowed(self):
        staff = baker.make(User, is_staff=True)
        self.client.force_login(staff)
        self.client.get("/multiseek/")
        token = self.client.cookies["csrftoken"].value
        resp = self.client.post(
            "/multiseek/save_form/",
            {
                "json": '{"form_data": [null]}',
                "name": "x",
                "csrfmiddlewaretoken": token,
            },
        )
        self.assertNotEqual(resp.status_code, 403)


class TestLoadFormURLPattern(TestCase):
    """Regression tests for Issue #8: load_form URL routing.

    The original pattern `r"^load_form/(?P<search_form_pk>\\d+)"` had two
    issues:
    1. No `$` anchor, so /load_form/<pk>/anything matched, the view ran
       with the matching pk, and the trailing path was silently discarded.
    2. The regex group captured pk as a string; switching to a `<int:>`
       path converter resolves it as a proper int.
    """

    def test_load_form_url_rejects_trailing_path(self):
        # Create a SearchForm so the view would succeed (return 302) if the
        # URL pattern wrongly accepted the trailing junk. Post-fix the URL
        # pattern itself rejects the request → 404 before the view runs.
        user = baker.make(User)
        sf = SearchForm.objects.create(name="x", owner=user, public=True, data="{}")
        resp = self.client.get(f"/multiseek/load_form/{sf.pk}/extra-junk")
        self.assertEqual(resp.status_code, 404)

    def test_load_form_url_resolves_pk_as_int(self):
        match = resolve("/multiseek/load_form/123")
        self.assertEqual(match.url_name, "load_form")
        self.assertEqual(match.kwargs, {"search_form_pk": 123})


class TestPublicAPI(TestCase):
    """Issue #10: the package's public API should be importable from
    `multiseek` directly, not only via `multiseek.logic`."""

    def test_public_api_re_exports(self):
        from multiseek import (
            AND,
            ANDNOT,
            OR,
            AutocompleteQueryObject,
            BooleanQueryObject,
            DateQueryObject,
            DecimalQueryObject,
            IntegerQueryObject,
            MultiseekRegistry,
            QueryObject,
            RangeQueryObject,
            StringQueryObject,
            ValueListQueryObject,
            create_registry,
            get_registry,
        )

        self.assertTrue(callable(create_registry))
        self.assertTrue(callable(get_registry))
        self.assertTrue(issubclass(StringQueryObject, QueryObject))
        self.assertEqual({AND, OR, ANDNOT}, {"and", "or", "andnot"})
        # Other symbols referenced to silence ruff F401 — they should all
        # be re-exported via multiseek/__init__.py.
        _ = (
            AutocompleteQueryObject,
            BooleanQueryObject,
            DateQueryObject,
            DecimalQueryObject,
            IntegerQueryObject,
            MultiseekRegistry,
            RangeQueryObject,
            ValueListQueryObject,
        )
