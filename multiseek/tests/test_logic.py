# -*- encoding: utf-8 -*-

import json
from unittest import TestCase

import pytest
from mock import MagicMock

from multiseek.logic import UnknownOperation, AutocompleteQueryObject, \
    RangeQueryObject, RANGE_OPS, StringQueryObject, QueryObject, DIFFERENT, \
    NOT_CONTAINS, NOT_STARTS_WITH, MultiseekRegistry, STRING, ParseError, \
    UnknownField, EQUALITY_OPS_ALL, OR, AND, create_registry, get_registry, \
    EQUAL, IntegerQueryObject, LESSER_OR_EQUAL, RANGE, ReportType, Ordering, MULTISEEK_ORDERING_PREFIX
from multiseek.models import SearchForm
from multiseek.util import make_field
import six
from builtins import str as text

test_json = json.dumps({'form_data': [None,
    dict(field='foo', operator=text(EQUALITY_OPS_ALL[0]), value='foo', prev_op=None)]})

def py3k_test_string(s):
    if six.PY3:
        return s.replace("u'", "'").replace('u"', '"').replace(", u'", ", '")
    return s

class TestQueryObject(TestCase):
    def setUp(self):
        class MyQueryObject(QueryObject):
            field_name = "foo"

        self.q = MyQueryObject()

    def test_value_from_web(self):
        self.assertEquals(123, self.q.value_from_web(123))


    def test_query_for(self):
        res = self.q.query_for("foobar", DIFFERENT)
        self.assertEquals(
            py3k_test_string("(NOT (AND: (u'foo', u'foobar')))"),
            str(res))

    def test_query_for_raises(self):
        self.assertRaises(
            UnknownOperation, self.q.query_for, 'foobar', 'unknown operation')


class TestStringQueryObject(TestCase):
    def setUp(self):
        class MyStringQueryObject(StringQueryObject):
            field_name = "foo"

        self.q = MyStringQueryObject()

    def test_query_for(self):
        args = [
            (DIFFERENT, "(NOT (AND: (u'foo', u'foobar')))"),
            (NOT_CONTAINS, "(NOT (AND: (u'foo__icontains', u'foobar')))"),
            (NOT_STARTS_WITH,
             "(NOT (AND: (u'foo__startswith', u'foobar')))")
        ]

        for param, result in args:
            res = self.q.real_query("foobar", param)
            self.assertEquals(
                str(res),
                py3k_test_string(result))

    def test_query_for_raises(self):
        self.assertRaises(
            UnknownOperation,
            self.q.real_query, 'lol', 'bad operation')


class TestAutocompleteQueryObject(TestCase):
    def test_value_from_web(self):
        q = AutocompleteQueryObject('foo')

        q.model = MagicMock()
        q.model.objects.get.return_value = True
        self.assertEquals(q.value_from_web(None), None)
        self.assertEquals(q.value_from_web('foo'), None)
        self.assertEquals(q.value_from_web(1), True)

    def test_value_to_web(self):
        q = AutocompleteQueryObject('foo')
        q.model = MagicMock()
        q.model.objects.get.return_value = True

        self.assertEquals(q.value_to_web(1), '[1, "True"]')

    @pytest.mark.django_db
    def test_value_to_web_bug(self):
        q = AutocompleteQueryObject('fo', model=SearchForm)
        self.assertEquals(q.value_to_web(1), '[null, ""]')

class TestRangeQueryObject(TestCase):
    def test_value_from_web(self):
        r = RangeQueryObject('foo')
        self.assertEquals(r.value_from_web("[1,2]"), [1, 2])
        self.assertEquals(r.value_from_web('["1","2"]'), [1, 2])
        self.assertEquals(r.value_from_web("[1,2,3]"), None)
        self.assertEquals(r.value_from_web('["foo","bar"]'), None)
        self.assertEquals(r.value_from_web('123'), None)

        self.assertRaises(
            UnknownOperation, r.real_query, [1, 2], 'foo')

        res = r.real_query([1, 2], RANGE_OPS[1])

        s1 = "(NOT (AND: (u'foo__gte', 1), (u'foo__lte', 2)))"
        maybe_this = str(res) == py3k_test_string(s1)

        s2 = "(NOT (AND: (u'foo__lte', 2), (u'foo__gte', 1)))"
        maybe_that = str(res) == py3k_test_string(s2)

        self.assert_(maybe_that or maybe_this)


class TestIntegerQueryObject(TestCase):
    def test_value_from_web(self):
        r = IntegerQueryObject('foo')
        self.assertEquals(r.value_from_web('123'), 123)

        self.assertRaises(
            UnknownOperation, r.real_query, 123, 'foo')

        res = r.real_query(123, text(LESSER_OR_EQUAL))
        self.assertEquals(
            str(res),
            py3k_test_string("(AND: (u'foo__lte', 123))"))


class TestMultiseekRegistry(TestCase):
    def setUp(self):
        self.registry = MultiseekRegistry()
        self.registry.add_field(StringQueryObject('foo'))
        self.registry.add_field(RangeQueryObject('bar'))
        self.registry.add_field(RangeQueryObject('quux', public=False))
        self.registry.report_types = [
            ReportType("list", "List"),
            ReportType("table", "Table")
        ]
        self.registry.ordering = [
            Ordering("foo", "Foo"),
            Ordering("bar", "Bar"),
        ]

    def test_add_field_raises(self):
        self.assertRaises(
            AssertionError, self.registry.add_field, StringQueryObject('foo'))

    def test_field_by_type(self):
        self.assertEquals(
            len(self.registry.field_by_type(STRING)),
            1)

        self.assertEquals(
            len(self.registry.field_by_type(RANGE, public=False)),
            2)

    def test_extract(self):
        self.assertEquals(
            self.registry.extract('field_name'), ['foo', 'bar'])

        self.assertEquals(
            self.registry.extract('field_name', public=False),
            ['foo', 'bar', 'quux'])

    def test_parse_field(self):
        self.assertRaises(
            ParseError,
            self.registry.parse_field, {})

        self.assertRaises(
            UnknownField,
            self.registry.parse_field,
            dict(field='XXX', operator='IS', value='LOL', prev_op=None))

        self.assertRaises(
            UnknownOperation,
            self.registry.parse_field,
            dict(field='foo', operator='XXX', value='FO', prev_op=None))

        res = self.registry.parse_field(
            dict(field='foo', operator=EQUALITY_OPS_ALL[0], value='foo', prev_op=None))

        self.assertEquals(str(res),
                          py3k_test_string("(AND: (u'foo', u'foo'))"))

    def test_get_recursive_list(self):
        input = [None,
            [None, [None, dict(field='foo', operator=text(EQUALITY_OPS_ALL[0]), value='foo', prev_op=None)]],
            dict(field='foo', operator=text(EQUALITY_OPS_ALL[0]), value='bar', prev_op="BAD OP")]

        self.assertRaises(
            UnknownOperation,
            self.registry.get_query_recursive,
            input)

        input[2]['prev_op'] = OR

        res = self.registry.get_query_recursive(input)
        self.assertEquals(
            str(res),
            py3k_test_string("(OR: (u'foo', u'foo'), (u'foo', u'bar'))"))

    def test_get_query(self):
        gq = self.registry.get_query(json.loads(test_json)['form_data'])
        self.assertEquals(
            str(gq),
            py3k_test_string("(AND: (u'foo', u'foo'))"))

    def test_get_query_for_model(self):
        self.registry.model = MagicMock()
        self.registry.get_query_for_model(json.loads(test_json))
        self.registry.get_query_for_model(None)

    def test_recreate_form(self):
        op = text(EQUALITY_OPS_ALL[0])
        fld_noop = dict(field='foo', operator=op, value=u'foo', prev_op=None)
        fld_and = dict(field='foo', operator=op, value=u'foo', prev_op=AND)
        fld_or = dict(field='foo', operator=op, value=u'foo', prev_op=OR)
        res = self.registry.recreate_form(
            {'form_data':
                 [None,
                  fld_noop,
                  fld_or, [
                     AND,
                     fld_noop,
                     fld_or],
                  fld_and,
                  [OR,
                   fld_noop,
                   fld_or]
                 ],
             'ordering': {
                 '%s1' % MULTISEEK_ORDERING_PREFIX: "1",
                 '%s1_dir' % MULTISEEK_ORDERING_PREFIX: "1",
             },
             'report_type': '1'})

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
\t\t}\n""" % dict(equal=EQUAL)

        self.assertEquals(ex, res)

    def     test_create_registry(self):
        create_registry(None, StringQueryObject('foo'))

    def test_get_registry(self):
        r = get_registry('test_app.multiseek_registry')
        from test_app.multiseek_registry import registry

        self.assertEquals(r, registry)

    def test_bug_3(self):
        f = self.registry.fields[0]
        v = self.registry.fields[0].ops[0]
        value = 'foo'

        field = make_field(f, v, value)
        field_or = make_field(f, v, value, "lol")

        form = {'form_data': [None, field, field, field, field_or]}

        self.assertRaises(
            ParseError, self.registry.recreate_form, form)
