# -*- encoding: utf-8 -*-

import json
from unittest import TestCase

from ludibrio import Mock, Dummy

from multiseek.logic import UnknownOperation, AutocompleteQueryObject, \
    RangeQueryObject, RANGE_OPS, StringQueryObject, QueryObject, DIFFERENT, \
    NOT_CONTAINS, NOT_STARTS_WITH, MultiseekRegistry, STRING, ParseError, \
    UnknownField, EQUALITY_OPS_ALL, OR, AND, create_registry, get_registry, \
    EQUAL, IntegerQueryObject, LESSER_OR_EQUAL, RANGE
from multiseek.util import make_field

test_json = json.dumps([
    dict(field='foo', operation=unicode(EQUALITY_OPS_ALL[0]), value='foo')])


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
            """(AND: (NOT (AND: ('foo', 'foobar'))))""",
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
            (DIFFERENT, "(AND: (NOT (AND: ('foo', 'foobar'))))"),
            (NOT_CONTAINS, "(AND: (NOT (AND: ('foo__icontains', 'foobar'))))"),
            (NOT_STARTS_WITH, "(AND: (NOT (AND: ('foo__startswith', 'foobar'))))")
        ]

        for param, result in args:
            res = self.q.real_query("foobar", param)
            self.assertEquals(str(res), result)

    def test_query_for_raises(self):
        self.assertRaises(
            UnknownOperation,
            self.q.real_query, 'lol', 'bad operation')


class TestAutocompleteQueryObject(TestCase):
    def test_value_from_web(self):
        q = AutocompleteQueryObject('foo')

        with Mock() as model:
            model.objects.get(pk=1) >> True

        q.model = model
        self.assertEquals(q.value_from_web(None), None)
        self.assertEquals(q.value_from_web('foo'), None)
        self.assertEquals(q.value_from_web(1), True)


class TestRangeQueryObject(TestCase):
    def test_value_from_web(self):
        r = RangeQueryObject('foo')
        self.assertEquals(r.value_from_web(['1', '2']), [1, 2])
        self.assertEquals(r.value_from_web(['1', '2', '3']), None)
        self.assertEquals(r.value_from_web(['foo', 'bar']), None)
        self.assertEquals(r.value_from_web('123'), None)

        self.assertRaises(
            UnknownOperation, r.real_query, [1,2], 'foo')

        res = r.real_query([1,2], RANGE_OPS[1])
        self.assertEquals(
            str(res), "(AND: (NOT (AND: ('foo__gte', 1), ('foo__lte', 2))))")


class TestIntegerQueryObject(TestCase):
    def test_value_from_web(self):
        r = IntegerQueryObject('foo')
        self.assertEquals(r.value_from_web('123'), 123)

        self.assertRaises(
            UnknownOperation, r.real_query, 123, 'foo')

        res = r.real_query(123, unicode(LESSER_OR_EQUAL))
        self.assertEquals(
            str(res), "(AND: ('foo__lte', 123))")


class TestMultiseekRegistry(TestCase):
    def setUp(self):
        self.registry = MultiseekRegistry()
        self.registry.add_field(StringQueryObject('foo'))
        self.registry.add_field(RangeQueryObject('bar'))
        self.registry.add_field(RangeQueryObject('quux', public=False))

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
            self.registry.extract('field_name', public=False), ['foo', 'bar', 'quux'])

    def test_parse_field(self):
        self.assertRaises(
            ParseError,
            self.registry.parse_field, {})

        self.assertRaises(
            UnknownField,
            self.registry.parse_field,
            dict(field='XXX', operation='IS', value='LOL'))

        self.assertRaises(
            UnknownOperation,
            self.registry.parse_field,
            dict(field='foo', operation='XXX', value='FO'))

        res = self.registry.parse_field(
            dict(field='foo', operation=EQUALITY_OPS_ALL[0], value='foo'))

        self.assertEquals(str(res), "(AND: ('foo', 'foo'))")

    def test_get_recursive_list(self):
        input = [
            [[dict(field='foo', operation=EQUALITY_OPS_ALL[0], value='foo')]],
            "BAD OP",
            dict(field='foo', operation=EQUALITY_OPS_ALL[0], value='bar')]

        self.assertRaises(
            UnknownOperation,
            self.registry.get_query_recursive,
            input)

        input[1] = OR

        res = self.registry.get_query_recursive(input)

        self.assertEquals(str(res), "(OR: ('foo', 'foo'), ('foo', 'bar'))")

    def test_get_query(self):
        self.assertEquals(str(self.registry.get_query(json.loads(test_json))),
                          "(AND: ('foo', u'foo'))")

    def test_get_query_for_model(self):
        self.registry.model = Dummy()
        self.registry.get_query_for_model(json.loads(test_json))
        self.registry.get_query_for_model(None)

    def test_recreate_form(self):
        op = EQUALITY_OPS_ALL[0]
        fld = dict(field='foo', operation=op, value=u'foo')
        res = self.registry.recreate_form(
            [fld, OR, fld, AND, [fld, OR, fld], AND, fld, AND, [fld, OR, fld]])

        self.maxDiff = None

        ex = u"""addField($("#frame-0"), "foo", "%(equal)s", "foo");
addField($("#frame-0"), "foo", "%(equal)s", "foo");
addFrame($("#frame-0"));
addField($("#frame-1"), "foo", "%(equal)s", "foo");
addField($("#frame-1"), "foo", "%(equal)s", "foo");
set_join($("#field-2"), "or");
addField($("#frame-0"), "foo", "%(equal)s", "foo");
addFrame($("#frame-0"));
addField($("#frame-2"), "foo", "%(equal)s", "foo");
addField($("#frame-2"), "foo", "%(equal)s", "foo");
set_join($("#field-5"), "or");
set_join($("#field-0"), "or");
set_join($("#field-1"), "and");
set_join($("#frame-1"), "and");
set_join($("#field-4"), "and");
""" % dict(equal=EQUAL)

        self.assertEquals(ex, res)

    def test_create_registry(self):
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

        form = [field, field, field, OR, field]

        self.assertRaises(
            ParseError, self.registry.recreate_form, form)

    def test_add_field(self):
        r = self.registry
        q = QueryObject("_ms_ordering_5")
        self.assertRaises(AssertionError, r.add_field, q)