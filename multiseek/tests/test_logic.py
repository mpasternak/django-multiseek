# -*- encoding: utf-8 -*-

import json
from builtins import str as text
from unittest import TestCase

import pytest
from django.contrib.contenttypes.models import ContentType
from mock import MagicMock

from multiseek.logic import (
    AND,
    CONTAINS,
    DIFFERENT,
    EQUAL,
    EQUALITY_OPS_ALL,
    GREATER_OR_EQUAL,
    LESSER_OR_EQUAL,
    MULTISEEK_ORDERING_PREFIX,
    NOT_CONTAINS,
    NOT_STARTS_WITH,
    OR,
    RANGE,
    RANGE_OPS,
    STRING,
    AbstractNumberQueryObject,
    AutocompleteQueryObject,
    DecimalQueryObject,
    IntegerQueryObject,
    MultiseekRegistry,
    Ordering,
    ParseError,
    QueryObject,
    RangeQueryObject,
    ReportType,
    StringQueryObject,
    UnknownField,
    UnknownOperation,
    create_registry,
    get_registry,
)
from multiseek.models import SearchForm
from multiseek.util import make_field

test_json = json.dumps(
    {
        "form_data": [
            None,
            dict(
                field="foo",
                operator=text(EQUALITY_OPS_ALL[0]),
                value="foo",
                prev_op=None,
            ),
        ]
    }
)

test_buggy_json = json.dumps({"form_data": [None]})


def py3k_test_string(s):
    return s.replace("u'", "'").replace('u"', '"').replace(", u'", ", '")


class TestQueryObject(TestCase):
    def setUp(self):
        class MyQueryObject(QueryObject):
            field_name = "foo"

        self.q = MyQueryObject()

    def test_value_from_web(self):
        self.assertEqual(123, self.q.value_from_web(123))

    def test_query_for(self):
        res = self.q.query_for("foobar", DIFFERENT)
        self.assertEqual(py3k_test_string("(NOT (AND: (u'foo', u'foobar')))"), str(res))

    def test_query_for_raises(self):
        self.assertRaises(
            UnknownOperation, self.q.query_for, "foobar", "unknown operation"
        )


class TestStringQueryObject(TestCase):
    def setUp(self):
        class MyStringQueryObject(StringQueryObject):
            field_name = "foo"

        self.q = MyStringQueryObject()

    def test_query_for(self):
        args = [
            (DIFFERENT, "(NOT (AND: (u'foo', u'foobar')))"),
            (NOT_CONTAINS, "(NOT (AND: (u'foo__icontains', u'foobar')))"),
            (NOT_STARTS_WITH, "(NOT (AND: (u'foo__startswith', u'foobar')))"),
        ]

        for param, result in args:
            res = self.q.real_query("foobar", param)
            self.assertEqual(str(res), py3k_test_string(result))

    def test_query_for_raises(self):
        self.assertRaises(UnknownOperation, self.q.real_query, "lol", "bad operation")


class TestAutocompleteQueryObject(TestCase):
    def test_value_from_web(self):
        q = AutocompleteQueryObject("foo")

        q.model = MagicMock()
        q.model.objects.get.return_value = True
        self.assertEqual(q.value_from_web(None), None)
        self.assertEqual(q.value_from_web("foo"), None)
        self.assertEqual(q.value_from_web(1), True)

    def test_value_to_web(self):
        q = AutocompleteQueryObject("foo")
        q.model = MagicMock()
        q.model.objects.get.return_value = True

        self.assertEqual(q.value_to_web(1), '[1, "True"]')

    def test_value_to_web_None(self):
        q = AutocompleteQueryObject("foo")
        q.model = ContentType
        self.assertEqual(q.value_to_web("null"), '[null, ""]')

    @pytest.mark.django_db
    def test_value_to_web_bug(self):
        q = AutocompleteQueryObject("fo", model=SearchForm)
        self.assertEqual(q.value_to_web(1), '[null, ""]')


class TestAbstractNumberQueryObject(TestCase):
    def test_real_query(self):
        a = AbstractNumberQueryObject("f")
        b = a.real_query(10, DIFFERENT)
        assert str(b) == "(NOT (AND: ('f', 10)))"
        b = a.real_query(10, EQUAL)
        assert str(b) == "(AND: ('f', 10))"


class TestRangeQueryObject(TestCase):
    def test_value_from_web(self):
        r = RangeQueryObject("foo")
        self.assertEqual(r.value_from_web("[1,2]"), [1, 2])
        self.assertEqual(r.value_from_web('["1","2"]'), [1, 2])
        self.assertEqual(r.value_from_web("[1,2,3]"), None)
        self.assertEqual(r.value_from_web('["foo","bar"]'), None)
        self.assertEqual(r.value_from_web("123"), None)

        self.assertRaises(UnknownOperation, r.real_query, [1, 2], "foo")

        res = r.real_query([1, 2], RANGE_OPS[1])

        s1 = "(NOT (AND: (u'foo__gte', 1), (u'foo__lte', 2)))"
        maybe_this = str(res) == py3k_test_string(s1)

        s2 = "(NOT (AND: (u'foo__lte', 2), (u'foo__gte', 1)))"
        maybe_that = str(res) == py3k_test_string(s2)

        self.assert_(maybe_that or maybe_this)


class TestIntegerQueryObject(TestCase):
    def test_value_from_web(self):
        r = IntegerQueryObject("foo")
        self.assertEqual(r.value_from_web("123"), 123)

        self.assertRaises(UnknownOperation, r.real_query, 123, "foo")

        res = r.real_query(123, text(LESSER_OR_EQUAL))
        self.assertEqual(str(res), py3k_test_string("(AND: (u'foo__lte', 123))"))


class _user:
    def return_true(self):
        return True

    is_authenticated = property(return_true)


class FakeRequest:
    def __init__(self):
        self.user = _user()


class TestMultiseekRegistry(TestCase):
    def setUp(self):
        self.registry = MultiseekRegistry()
        self.registry.add_field(StringQueryObject("foo"))
        self.registry.add_field(RangeQueryObject("bar"))
        self.registry.add_field(RangeQueryObject("quux", public=False))
        self.registry.report_types = [
            ReportType("list", "List"),
            ReportType("table", "Table"),
        ]
        self.registry.ordering = [
            Ordering("foo", "Foo"),
            Ordering("bar", "Bar"),
        ]

    def test_add_field_raises(self):
        self.assertRaises(
            AssertionError, self.registry.add_field, StringQueryObject("foo")
        )

    def test_field_by_type(self):
        self.assertEqual(len(self.registry.field_by_type(STRING)), 1)

        self.assertEqual(len(self.registry.field_by_type(RANGE, FakeRequest())), 2)

    def test_extract(self):
        self.assertEqual(self.registry.extract("field_name"), ["foo", "bar"])

        self.assertEqual(
            self.registry.extract("field_name", FakeRequest()), ["foo", "bar", "quux"]
        )

    def test_parse_field(self):
        self.assertRaises(ParseError, self.registry.parse_field, {})

        self.assertRaises(
            UnknownField,
            self.registry.parse_field,
            dict(field="XXX", operator="IS", value="LOL", prev_op=None),
        )

        self.assertRaises(
            UnknownOperation,
            self.registry.parse_field,
            dict(field="foo", operator="XXX", value="FO", prev_op=None),
        )

        res = self.registry.parse_field(
            dict(field="foo", operator=EQUALITY_OPS_ALL[0], value="foo", prev_op=None)
        )

        self.assertEqual(str(res), py3k_test_string("(AND: (u'foo', u'foo'))"))

    def test_get_recursive_list(self):
        input = [
            None,
            [
                None,
                [
                    None,
                    dict(
                        field="foo",
                        operator=text(EQUALITY_OPS_ALL[0]),
                        value="foo",
                        prev_op=None,
                    ),
                ],
            ],
            dict(
                field="foo",
                operator=text(EQUALITY_OPS_ALL[0]),
                value="bar",
                prev_op="BAD OP",
            ),
        ]

        self.assertRaises(UnknownOperation, self.registry.get_query_recursive, input)

        input[2]["prev_op"] = OR

        res = self.registry.get_query_recursive(input)
        self.assertEqual(
            str(res), py3k_test_string("(OR: (u'foo', u'foo'), (u'foo', u'bar'))")
        )

    def test_get_query(self):
        gq = self.registry.get_query(json.loads(test_json)["form_data"])
        self.assertEqual(str(gq), py3k_test_string("(AND: (u'foo', u'foo'))"))

    def test_get_query_for_model(self):
        self.registry.model = MagicMock()
        self.registry.get_query_for_model(json.loads(test_json))
        self.registry.get_query_for_model(None)

    def test_get_query_for_model_bug(self):
        self.registry.model = MagicMock()
        self.registry.get_query_for_model(json.loads(test_buggy_json))

    def test_recreate_form(self):
        op = text(EQUALITY_OPS_ALL[0])
        fld_noop = dict(field="foo", operator=op, value=u"foo", prev_op=None)
        fld_and = dict(field="foo", operator=op, value=u"foo", prev_op=AND)
        fld_or = dict(field="foo", operator=op, value=u"foo", prev_op=OR)
        res = self.registry.recreate_form(
            {
                "form_data": [
                    None,
                    fld_noop,
                    fld_or,
                    [AND, fld_noop, fld_or],
                    fld_and,
                    [OR, fld_noop, fld_or],
                ],
                "ordering": {
                    "%s1" % MULTISEEK_ORDERING_PREFIX: "1",
                    "%s1_dir" % MULTISEEK_ORDERING_PREFIX: "1",
                },
                "report_type": "1",
            }
        )

        self.maxDiff = None

        ex = u"""$('#frame-0').multiseekFrame('addField', 'foo', 'equals', 'foo', null);
$('#frame-0').multiseekFrame('addField', 'foo', 'equals', 'foo', 'or');
$('#frame-0').multiseekFrame('addFrame', 'and');
$('#frame-1').multiseekFrame('addField', 'foo', 'equals', 'foo', null);
$('#frame-1').multiseekFrame('addField', 'foo', 'equals', 'foo', 'or');
$('#frame-0').multiseekFrame('addField', 'foo', 'equals', 'foo', 'and');
$('#frame-0').multiseekFrame('addFrame', 'or');
$('#frame-2').multiseekFrame('addField', 'foo', 'equals', 'foo', null);
$('#frame-2').multiseekFrame('addField', 'foo', 'equals', 'foo', 'or');
\t\t$("select[name=order_1] option").eq(1).prop("selected", true);
\t\t$("input[name=order_1_dir]").attr("checked", true);
\t\t$("select[name=_ms_report_type] option").eq(1).prop("selected", true);
\t\tif (window.Foundation) {
\t\t\t$("input[name=order_1_dir]").next().toggleClass("checked", true)
\t\t}\n""" % dict(
            equal=EQUAL
        )

        self.assertEqual(ex, res)

    def test_create_registry(self):
        create_registry(None, StringQueryObject("foo"))

    def test_get_registry(self):
        r = get_registry("test_app.multiseek_registry")
        from test_app.multiseek_registry import registry

        self.assertEqual(r, registry)

    def test_bug_3(self):
        f = self.registry.fields[0]
        v = self.registry.fields[0].ops[0]
        value = "foo"

        field = make_field(f, v, value)
        field_or = make_field(f, v, value, "lol")

        form = {"form_data": [None, field, field, field, field_or]}

        self.assertRaises(ParseError, self.registry.recreate_form, form)


def test_impacts_query_IntegerQueryObject():
    a = IntegerQueryObject("foo")
    assert a.impacts_query(None, EQUAL)
    assert a.impacts_query(None, DIFFERENT)
    assert not a.impacts_query(None, GREATER_OR_EQUAL)


def test_impacts_query_DecimalQueryObject():
    a = DecimalQueryObject("foo")
    assert a.impacts_query(None, EQUAL)
    assert a.impacts_query(None, DIFFERENT)
    assert not a.impacts_query(None, GREATER_OR_EQUAL)


def test_impacts_query_StringQueryObject():
    a = StringQueryObject("foo")
    assert a.impacts_query(None, EQUAL)
    assert a.impacts_query(None, DIFFERENT)
    assert not a.impacts_query(None, CONTAINS)
    assert not a.impacts_query(None, NOT_CONTAINS)
