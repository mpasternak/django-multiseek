# -*- encoding: utf-8 -*-
import importlib

import json
import re
from django.db.models import Q
from django.db.models.options import get_verbose_name
from django.utils.translation import ugettext_lazy as _
from collections import namedtuple

MULTISEEK_REPORT_TYPE = '_ms_report_type'
MULTISEEK_ORDERING_PREFIX = "order_"

AND = "and"
OR = "or"

STRING = "string"
INTEGER = "integer"
AUTOCOMPLETE = "autocomplete"
RANGE = "range"
VALUE_LIST = 'value-list'

EQUAL = _("equals")         # u"równy"
EQUAL_FEMALE = _("equals (female geder)")  # u"równa"
EQUAL_NONE = _("equals (no gender)")    # u'równe'
EQUAL_BOTH = _("equals (both genders)")    #u'równy/a'

GREATER = _("greater, than")
GREATER_FEMALE = _("greater, than (female gender)")
GREATER_NONE = _("greater, than (no gender)")
GREATER_OPS_ALL = [GREATER, GREATER_FEMALE, GREATER_NONE]

LESSER = _("lesser, than")
LESSER_FEMALE = _("lesser, than (female gender)")
LESSER_NONE = _("lesser, than (no gender)")
LESSER_OPS_ALL = [LESSER, LESSER_FEMALE, LESSER_NONE]

GREATER_OR_EQUAL = _("greater or equal to")
GREATER_OR_EQUAL_FEMALE = _("greater or equal to(female gender)")
GREATER_OR_EQUAL_NONE = _("greater or equal to (no gender)")
GREATER_OR_EQUAL_OPS_ALL = [GREATER_OR_EQUAL, GREATER_OR_EQUAL_FEMALE,
                            GREATER_OR_EQUAL_NONE]

LESSER_OR_EQUAL = _("lesser or equal to")
LESSER_OR_EQUAL_FEMALE = _("lesser or equal to (female gender)")
LESSER_OR_EQUAL_NONE = _("lesser or equal to (no gender)")
LESSER_OR_EQUAL_OPS_ALL = [LESSER_OR_EQUAL, LESSER_OR_EQUAL_FEMALE,
                           LESSER_OR_EQUAL_NONE]

DIFFERENT = _("differs")        # u"różny"
DIFFERENT_FEMALE = _("differs (female gender)") # u'różna'
DIFFERENT_NONE = _("differs (no gender)")   # u'różne'
DIFFERENT_BOTH = _("differs (both gender)")   # u'różny/a'

CONTAINS = _("contains")        # u"zawiera"
NOT_CONTAINS = _("not contains")    # u"nie zawiera"
STARTS_WITH = _("starts with")  # u"zaczyna się od"
NOT_STARTS_WITH = _("not starts with")  # u"nie zaczyna się od"

IN_RANGE = _("in")              # u'zawiera się w'
NOT_IN_RANGE = _("not in")      # u'nie zawiera się w'

STRING_OPS = [CONTAINS, NOT_CONTAINS,
              EQUAL, DIFFERENT,
              STARTS_WITH, NOT_STARTS_WITH]

INTEGER_OPS_MALE = [EQUAL, DIFFERENT, GREATER, LESSER]
INTEGER_OPS_FEMALE = [EQUAL_FEMALE, DIFFERENT_FEMALE, GREATER_FEMALE,
                      LESSER_FEMALE]
INTEGER_OPS_NONE = [EQUAL_NONE, DIFFERENT_NONE, GREATER_NONE, LESSER_NONE]
INTEGER_OPS_ALL = INTEGER_OPS_FEMALE + INTEGER_OPS_MALE + INTEGER_OPS_NONE

RANGE_OPS = [IN_RANGE, NOT_IN_RANGE]

EQUALITY_OPS_MALE = [EQUAL, DIFFERENT]
EQUALITY_OPS_FEMALE = [EQUAL_FEMALE, DIFFERENT_FEMALE]
EQUALITY_OPS_NONE = [EQUAL_NONE, DIFFERENT_NONE]
EQUALITY_OPS_BOTH = [EQUAL_BOTH, DIFFERENT_BOTH]

EQUALITY_OPS_ALL = EQUALITY_OPS_MALE + EQUALITY_OPS_FEMALE + \
                   EQUALITY_OPS_NONE + EQUALITY_OPS_BOTH

DIFFERENT_ALL = DIFFERENT, DIFFERENT_FEMALE, DIFFERENT_NONE, DIFFERENT_BOTH


class UnknownOperation(Exception):
    pass


class UnknownField(Exception):
    pass


class ParseError(Exception):
    pass


class QueryObject(object):
    """This is a Query Object!

    This object replaces the parameters that it gets from the web UI, which
    is the multiseek main form (field, operation, value) to a list of
    Q objects that can be used to query the database with Django.
    """

    field_name = None
    label = None
    type = None
    ops = None

    # By default, all QueryObjects are available for non-logged in users.
    public = True

    def __init__(self, field_name=None, label=None, public=None):
        if field_name is not None:
            self.field_name = field_name

        if label is not None:
            self.label = label

        if self.label is None:
            self.label = get_verbose_name(self.field_name)

        if public is not None:
            self.public = public

    def value_from_web(self, value):
        """
        Prepare the value from web for use in self.real_query function.
        """
        return value

    def query_for(self, value, operation):
        return self.real_query(self.value_from_web(value), operation)

    def real_query(self, value, operation, validate_operation=True):
        """
        Prepare a real query - return a Q object.

        :param value: value which will be used in the query
        :param validate_operation: if operation is not found in
        EQUALITY_OPS_ALL, raise UnknownOperation.
        :ptype validate_operation: bool
        :rtype: django.db.models.Q
        """
        ret = None

        if operation in EQUALITY_OPS_ALL:
            ret = Q(**{self.field_name: value})

        else:
            if validate_operation:
                raise UnknownOperation(operation)

        if operation in DIFFERENT_ALL:
            return ~ret

        return ret


class StringQueryObject(QueryObject):
    type = STRING
    ops = STRING_OPS

    def real_query(self, value, operation):
        ret = QueryObject.real_query(
            self, value, operation, validate_operation=False)

        if ret is not None:
            return ret

        elif operation in [CONTAINS, NOT_CONTAINS]:
            ret = Q(**{self.field_name + "__icontains": value})

        elif operation in [STARTS_WITH, NOT_STARTS_WITH]:
            ret = Q(**{self.field_name + "__startswith": value})

        else:
            raise UnknownOperation(operation)

        if operation in [NOT_CONTAINS, NOT_STARTS_WITH]:
            return ~ret

        return ret


class AutocompleteQueryObject(QueryObject):
    type = AUTOCOMPLETE
    ops = EQUALITY_OPS_MALE
    model = None
    url = None

    def __init__(
            self, field_name=None, label=None, model=None, url=None,
            public=None):
        super(AutocompleteQueryObject, self).__init__(
            field_name, label, public=public)

        if model is not None:
            self.model = model

        if url is not None:
            self.url = url

    def value_from_web(self, value):
        # The value should be an integer:
        try:
            value = int(value)
        except (TypeError, ValueError):
            return

        try:
            value = self.model.objects.get(pk=value)
        except self.model.DoesNotExist:
            return

        return value


class RangeQueryObject(QueryObject):
    type = RANGE
    ops = RANGE_OPS

    def value_from_web(self, value):
        # value should be a list of integers
        try:
            int(value[0])
            int(value[1])
        except (ValueError, TypeError, IndexError):
            return

        if len(value) > 2:
            return

        return [int(value[0]), int(value[1])]

    def real_query(self, value, operation):
        if operation in RANGE_OPS:
            ret = Q(**{self.field_name + '__gte': value[0],
                       self.field_name + '__lte': value[1]})
        else:
            raise UnknownOperation(operation)

        if operation == RANGE_OPS[1]:
            return ~ret

        return ret


class IntegerQueryObject(QueryObject):
    type = INTEGER
    ops = [EQUAL, DIFFERENT, GREATER, LESSER, GREATER_OR_EQUAL, LESSER_OR_EQUAL]

    def value_from_web(self, value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return

    def real_query(self, value, operation):
        if operation in EQUALITY_OPS_ALL:
            return Q(**{self.field_name: value})
        elif operation in DIFFERENT_ALL:
            return ~Q(**{self.field_name: value})
        elif operation in GREATER_OPS_ALL:
            return Q(**{self.field_name + "__gt": value})
        elif operation in LESSER_OPS_ALL:
            return Q(**{self.field_name + "__lt": value})
        elif operation in GREATER_OR_EQUAL_OPS_ALL:
            return Q(**{self.field_name + "__gte": value})
        elif operation in LESSER_OR_EQUAL_OPS_ALL:
            return Q(**{self.field_name + "__lte": value})
        else:
            raise UnknownOperation(operation)


class ValueListQueryObject(QueryObject):
    type = VALUE_LIST
    ops = [EQUAL, DIFFERENT]
    values = None

    def __init__(self, field_name=None, label=None, values=None, public=None):
        super(ValueListQueryObject, self).__init__(
            field_name, label, public=public)
        if values is not None:
            self.values = values


Ordering = namedtuple("Ordering", ["field", "label"])


class ReportType(namedtuple("ReportType", "id label public")):
    def __new__(cls, id, label, public=True):
        return super(ReportType, cls).__new__(cls, id, label, public)


class MultiseekRegistry:
    """This is a base class for multiseek registry. A registry is a list
    of registered fields, that will be used to render the multiseek form
    and to query the database.
    """

    model = None

    # This is a list of Ordering (namedtuples of field, label) with
    # information about fields, that can be used to sort results of your query.
    # Label will be used on web ui. Field name is the part, that gets passed
    # to queryset.order_by
    ordering = None
    order_boxes = [_("Sort by:"), _("then by"), _("then by")]
    report_types = []

    def __init__(self):
        self.fields = []
        self.field_by_name = {}

    def get_fields(self, public=True):
        """Returns a list of fields, by default returning only public fields.
        """
        if public:
            return [x for x in self.fields if x.public]
        return self.fields

    def add_field(self, field):
        """Add a field to multiseek registry.

        "ptype field: multiseek.logic.QueryObject
        """
        if field.field_name:
            for pfx in [MULTISEEK_ORDERING_PREFIX, MULTISEEK_REPORT_TYPE]:
                assert (not field.field_name.startswith(pfx)), \
                    "Field names cannot start with '" + pfx + "'"
        self.fields.append(field)
        self.field_by_name = dict([(f.label, f) for f in self.fields])

        # Check if every label is unique
        assert (len(self.field_by_name.keys()) == len(self.fields))

    def field_by_type(self, type, public=True):
        """Return a list of fields by type.
        """
        return [field for field in self.get_fields(public) if
                field.type == type]

    def extract(self, attr, public=True):
        """Extract an attribute out of every field.
        """
        return [getattr(field, attr) for field in self.get_fields(public)]

    def parse_field(self, field):
        """Parse a field (from JSON)

        :param field: dict containing 'field', 'operation' and 'value' elements.
        :type field: dict
        :returns: QueryObject
        :rtype: multiseek.logic.QueryObject subclass
        """
        for key in ['field', 'operation', 'value']:
            if key not in field:
                raise ParseError("Key %s not found in field %r" % (key, field))

        f = self.field_by_name.get(field['field'])
        if f is None:
            raise UnknownField("Field type %r not found!" % field)

        if field['operation'] not in f.ops:
            raise UnknownOperation(
                "Operation %r not valid for field %r" % (
                    field['operation'], field['field']))

        return f.query_for(field['value'], field['operation'])

    def get_query_recursive(self, lst):
        """Recursivley get query, basing on a list of elements.
        """

        if not lst:
            return None

        count = -1

        previous = None
        operation = None

        while count < len(lst) - 1:

            count += 1

            elem = lst[count]
            d = type(elem)

            if d == list:
                res = self.get_query_recursive(elem)

            elif d == dict:
                res = self.parse_field(elem)

            elif d == str or d == unicode:
                if elem not in [AND, OR]:
                    raise UnknownOperation("%r" % elem)

                if elem == AND:
                    operation = '__and__'
                elif elem == OR:
                    operation = '__or__'
                else:
                    raise Exception

                continue

            if previous is None:
                previous = res
                continue

            method = getattr(previous, operation)
            previous = method(res)

        return previous

    def get_query(self, data):
        """Return a query for a given JSON.
        """
        return self.get_query_recursive(data)

    def get_report_types(self, only_public=False):
        if only_public:
            return [x for x in self.report_types if x.public]
        return self.report_types

    def get_report_type(self, data, only_public=False):
        default_retval = ''
        report_types = self.get_report_types(only_public=only_public)

        if report_types:
            default_retval = self.report_types[0].id

        if data is None or not data.has_key('report_type'):
            return default_retval

        try:
            idx = int(data['report_type'])
        except (ValueError, IndexError, TypeError):
            return default_retval

        try:
            return report_types[idx].id
        except IndexError:
            return default_retval

    def get_query_for_model(self, data):
        if data is None:
            return self.model.objects.all()

        # Fix for pre-0.8 versions
        if type(data) != dict:
            data = {'form_data': data}

        query = self.get_query(data['form_data'])
        retval = self.model.objects.filter(query)
        sb = []
        if data.has_key('ordering'):
            for no, element in enumerate(self.order_boxes):
                key = "%s%s" % (MULTISEEK_ORDERING_PREFIX, no)
                key_dir = key + "_dir"

                if data['ordering'].has_key(key):
                    try:
                        sort_idx = int(data['ordering'][key])
                    except (TypeError, ValueError):
                        continue

                    try:
                        srt = self.ordering[sort_idx].field
                    except (IndexError, TypeError, ValueError):
                        continue

                    if not srt:
                        continue

                    if data['ordering'].has_key(key_dir) and \
                                    data['ordering'][key_dir] == "1":
                        srt = "-" + srt

                    sb.append(srt)

            if sb:
                retval = retval.order_by(*sb)
        return retval

    def recreate_form_recursive(self, element, frame_counter, field_counter):
        ret = []
        ops = []

        expect_operation = False
        last_element = None
        cur_frame = frame_counter

        for piece in element:
            et = type(piece)

            if et == list:
                if expect_operation:
                    raise ParseError("Operation expected")

                frame_counter += 1

                if frame_counter >= 0:
                    # Frame "zero" is created, so:
                    ret.append(u'addFrame($("#frame-%s"))' % (cur_frame))

                result, frame_counter, field_counter = \
                    self.recreate_form_recursive(
                        piece, frame_counter, field_counter)

                ret.extend(result)

                pre_last_element = last_element
                last_element = "frame-%s" % frame_counter

                expect_operation = True

            elif et == dict:
                if expect_operation:
                    raise ParseError("Operation expected")

                field = self.field_by_name.get(piece['field'])

                if field is None:
                    raise UnknownField(piece['field'])

                if field.type == AUTOCOMPLETE:
                    try:
                        value = json.dumps([int(piece['value']), unicode(
                            field.model.objects.get(pk=piece['value']))])
                    except field.model.DoesNotExist:
                        value = ''
                else:
                    try:
                        value = json.dumps(piece['value'])
                    except KeyError:
                        raise ParseError(
                            "Field %r has no value" % piece['field'])

                ret.append(
                    u'addField($("#frame-%(cur_frame)s"), "%(type)s", '
                    u'"%(op)s", %(value)s)' % dict(
                        cur_frame=cur_frame,
                        type=re.escape(piece['field']),
                        op=re.escape(piece['operation']),
                        value=value))

                field_counter += 1

                last_element = "field-%s" % field_counter

                expect_operation = True

            elif et == unicode or et == str:
                # last OPERATION
                if not expect_operation:
                    raise ParseError("Operation NOT expected")

                ops.append(u'set_join($("#%(last)s"), "%(piece)s")' % dict(
                    last=last_element, piece=piece))

                expect_operation = False
                pass

            else:
                raise TypeError(et)

        ret.extend(ops)

        return ret, frame_counter, field_counter

    def recreate_form(self, data):
        """Recreate a JavaScript code to create a given form, basing
        on a list.

        :returns: Javascript code to embed on the multiseek form page, which
        will recreate form
        :rtype: safestr
        """

        frame_counter = 0
        field_counter = -1

        result, frame_counter, field_counter = self.recreate_form_recursive(
            data['form_data'], frame_counter, field_counter)

        if data.has_key("ordering"):
            for no, elem in enumerate(self.order_boxes):
                key = "%s%s" % (MULTISEEK_ORDERING_PREFIX, no)
                if data['ordering'].has_key(key):
                    result.append(
                        '\t\t\t'
                        '$($("select[name=%s]").children()[%s]).attr("selected", "")' % (
                            key, data['ordering'][key]))
                key = key + "_dir"
                if data['ordering'].has_key(key):
                    if data['ordering'][key] == "1":
                        result.append(
                            '\t\t\t'
                            '$("input[name=%s]").attr("checked", "")' % (
                                key))

        if data.has_key('report_type'):
            if data['report_type']:
                result.append(
                    '\t\t\t'
                    '$($("select[name=%s]").children()[%s]).attr("selected", "")'
                    % (
                    MULTISEEK_REPORT_TYPE, data['report_type']))


        return u";\n".join(result) + u";\n"


def create_registry(model, *args, **kw):
    r = MultiseekRegistry()
    r.model = model
    for field in args:
        r.add_field(field)
    if 'ordering' in kw:
        r.ordering = kw.pop('ordering')
    if 'report_types' in kw:
        r.report_types = kw.pop('report_types')
    if kw.keys():
        raise Exception("Unknown kwargs passed")
    return r


def get_registry(registry):
    """
    :rtype: MultiseekRegistry
    """
    if type(registry) is str or type(registry) is unicode:
        return importlib.import_module(registry).registry

    return registry
