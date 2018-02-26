# -*- encoding: utf-8 -*-


from decimal import Decimal
import decimal
import importlib

import json
import re
from datetime import timedelta, datetime
from dateutil.parser import parse
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.urls import reverse
from django.utils import html
try:
    from django.db.models.options import get_verbose_name
except ImportError:
    from django.utils.text import camel_case_to_spaces as get_verbose_name
from django.utils.translation import ugettext_lazy as _
from collections import namedtuple
from builtins import str as text

import six
if six.PY3:
    unicode = str

MULTISEEK_REPORT_TYPE = '_ms_report_type'
MULTISEEK_ORDERING_PREFIX = "order_"

AND = "and"
OR = "or"
ANDNOT = "andnot"

STRING = "string"
INTEGER = "integer"
DECIMAL = "decimal"
AUTOCOMPLETE = "autocomplete"
RANGE = "range"
DATE = "date"
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

IN_RANGE = _("in range")              # u'zawiera się w'
NOT_IN_RANGE = _("outside range")      # u'nie zawiera się w'

STRING_OPS = [CONTAINS, NOT_CONTAINS,
              EQUAL, DIFFERENT,
              STARTS_WITH, NOT_STARTS_WITH]

INTEGER_OPS_MALE = [EQUAL, DIFFERENT, GREATER, LESSER]
INTEGER_OPS_FEMALE = [EQUAL_FEMALE, DIFFERENT_FEMALE, GREATER_FEMALE,
                      LESSER_FEMALE]
INTEGER_OPS_NONE = [EQUAL_NONE, DIFFERENT_NONE, GREATER_NONE, LESSER_NONE]
INTEGER_OPS_ALL = INTEGER_OPS_FEMALE + INTEGER_OPS_MALE + INTEGER_OPS_NONE

RANGE_OPS = [IN_RANGE, NOT_IN_RANGE]
DATE_OPS = [EQUAL_FEMALE, DIFFERENT_FEMALE, GREATER_FEMALE,
            GREATER_OR_EQUAL_FEMALE, LESSER_FEMALE, LESSER_OR_EQUAL_FEMALE,
            IN_RANGE, NOT_IN_RANGE]
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

    def impacts_query(self, operator, value):
        """Returns True or False, depending on the operator and value.

        For some fields, combination of operator and value does not
        change the results. For example, if you have a string field,
        you have an empty value and you use operator EQUALS - this
        will find you every empty field in the database, which is
        OK. But, if you use operator CONTAINS, this query will not
        have any impact on the results, as looking doing
        SELECT ... WHERE field LIKE '%%' will not do anything.

        So, if given operator, value pair can impact query results,
        return True here.

        """

        # By default we return True here, feel free to override this
        # in subclasses.
        return True

    def value_for_description(self, value):
        """Return value for description - readable for end-user, for placement
        on web page."""
        return self.value_from_web(value)

    def value_to_web(self, value):
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

        if operation in [text(x) for x in EQUALITY_OPS_ALL]:
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
    empty_value_description = _("(empty)")

    def impacts_query(self, operator, value):
        if operator in [CONTAINS, NOT_CONTAINS, STARTS_WITH, NOT_STARTS_WITH] \
                and not value:
            return False
        return True

    def value_from_web(self, value):
        if type(value) == str or type(value) == unicode:
            return value
        if type(value) == bytes:
            return value.decode("utf-8")

    def value_for_description(self, value):
        value = super(StringQueryObject, self).value_for_description(value)
        if not value:
            return self.empty_value_description
        return u'"%s"' % html.escape(value)

    def real_query(self, value, operation):
        ret = QueryObject.real_query(
            self, value, operation, validate_operation=False)

        if ret is not None:
            return ret

        elif operation in [text(x) for x in [CONTAINS, NOT_CONTAINS]]:
            ret = Q(**{self.field_name + "__icontains": value})

        elif operation in [text(x) for x in [STARTS_WITH, NOT_STARTS_WITH]]:
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

    def get_url(self):
        if self.url is None:
            raise ImproperlyConfigured(
                "Please specify the autocomplete URL for %r" % self)

        return reverse(self.url)

    @classmethod
    def get_label(cls, model):
        return text(model)

    def value_from_web(self, value):
        # The value should be an integer:
        try:
            value_i = int(value)
        except (TypeError, ValueError):
            return

        try:
            ret = self.model.objects.get(pk=value_i)
        except self.model.DoesNotExist:
            return

        return ret

    def value_to_web(self, value):
        try:
            model = self.model.objects.get(pk=value)
        except self.model.DoesNotExist:
            return json.dumps([None, ''])
        return json.dumps([value, self.get_label(model)])


class DateQueryObject(QueryObject):
    type = DATE
    ops = DATE_OPS

    def value_from_web(self, value):
        value = json.loads(value)
        if len(value) == 1:
            if not value[0]:
                # assume 'today'
                return datetime.now().date()
            return parse(value[0]).date()

        ret = []
        for elem in value:
            if not elem:
                # assume 'today'
                ret.append(datetime.now().date())
                continue
            ret.append(parse(elem).date())
        return ret

    def real_query(self, value, operation):
        if operation in RANGE_OPS:
            ret = Q(**{self.field_name + '__gte': value[0],
                       self.field_name + '__lte': value[1]})
        elif operation in EQUALITY_OPS_ALL:
            return Q(**{self.field_name + "__range": (value, value + timedelta(days=1))})
        elif operation in DIFFERENT_ALL:
            return ~Q(**{self.field_name + "__range": (value, value + timedelta(days=1))})
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

        if operation == RANGE_OPS[1]:
            return ~ret

        return ret


class RangeQueryObject(QueryObject):
    type = RANGE
    ops = RANGE_OPS

    def value_from_web(self, value):
        # value should be a list of integers

        value = json.loads(value)

        try:
            int(value[0])
            int(value[1])
        except (ValueError, TypeError, IndexError):
            return

        if len(value) > 2:
            return

        return [int(value[0]), int(value[1])]

    def real_query(self, value, operation):

        if value is None:
            return

        if operation in RANGE_OPS:
            ret = Q(**{self.field_name + '__gte': value[0],
                       self.field_name + '__lte': value[1]})
        else:
            raise UnknownOperation(operation)

        if operation == RANGE_OPS[1]:
            return ~ret

        return ret


class AbstractNumberQueryObject(QueryObject):
    ops = [EQUAL, DIFFERENT, GREATER, LESSER,
           GREATER_OR_EQUAL, LESSER_OR_EQUAL]

    def impacts_query(self, operator, value):
        if value is None and operator in [GREATER, LESSER,
                                          GREATER_OR_EQUAL,
                                          LESSER_OR_EQUAL]:
            return False
        return True

    def real_query(self, value, operation):
        if operation in [text(x) for x in EQUALITY_OPS_ALL]:
            return Q(**{self.field_name: value})
        elif operation in [text(x) for x in DIFFERENT_ALL]:
            return ~Q(**{self.field_name: value})
        elif operation in [text(x) for x in GREATER_OPS_ALL]:
            return Q(**{self.field_name + "__gt": value})
        elif operation in [text(x) for x in LESSER_OPS_ALL]:
            return Q(**{self.field_name + "__lt": value})
        elif operation in [text(x) for x in GREATER_OR_EQUAL_OPS_ALL]:
            return Q(**{self.field_name + "__gte": value})
        elif operation in [text(x) for x in LESSER_OR_EQUAL_OPS_ALL]:
            return Q(**{self.field_name + "__lte": value})
        else:
            raise UnknownOperation(operation)


class IntegerQueryObject(AbstractNumberQueryObject):
    type = INTEGER

    def value_from_web(self, value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return


class DecimalQueryObject(AbstractNumberQueryObject):
    type = DECIMAL

    def value_from_web(self, value):
        try:
            return Decimal(value)
        except (TypeError, decimal.InvalidOperation):
            return



class ValueListQueryObject(QueryObject):
    type = VALUE_LIST
    ops = [EQUAL, DIFFERENT]
    values = None

    def __init__(self, field_name=None, label=None, values=None, public=None):
        super(ValueListQueryObject, self).__init__(
            field_name, label, public=public)
        if values is not None:
            self.values = values

BOOLEAN_TRUE_LABEL = _("yes")
BOOLEAN_FALSE_LABEL = _("no")

class BooleanQueryObject(QueryObject):
    type = VALUE_LIST
    ops = [EQUAL, DIFFERENT]

    true_label = BOOLEAN_TRUE_LABEL
    false_label = BOOLEAN_FALSE_LABEL

    values = [true_label, false_label]

    def value_from_web(self, value):
        if value == self.true_label:
            return True
        if value == self.false_label:
            return False
        return None

    def value_for_description(self, value):
        return value

Ordering = namedtuple("Ordering", ["field", "label"])


class ReportType(namedtuple("ReportType", "id label public")):
    def __new__(cls, id, label, public=True):
        return super(ReportType, cls).__new__(cls, id, label, public)


class _FrameInfo:
    frame = None
    field = None

    def __init__(self, frame=-1, field=0):
        self.frame = frame
        self.field = field

def get_ordering_key_name(no):
    key = "%s%s" % (MULTISEEK_ORDERING_PREFIX, no)
    key_dir = key + "_dir"
    return key, key_dir

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

    report_types = None
    default_ordering = None

    def __init__(self):
        self.fields = []
        self.field_by_name = {}
        self.default_ordering = {}
        self.report_types = []

    def set_default_ordering(self, *args):
        self.default_ordering = {}
        ordering_dict = dict(
            (x.field, no) for no, x in enumerate(self.ordering))

        for no, elem in enumerate(args):
            key, key_dir = get_ordering_key_name(no)

            desc = False
            if elem.startswith("-"):
                desc = True
                elem = elem[1:]

            self.default_ordering[key] = ordering_dict[elem]
            if desc is True:
                self.default_ordering[key_dir] = "1"

    def get_fields(self, public=True):
        """Returns a list of fields, by default returning only public fields.
        """
        if public:
            return [x for x in self.fields if x.public]
        return self.fields

    def get_field_by_name(self, name):
        for field in self.fields:
            if text(field.label) == name:
                return field

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
        assert (len(self.field_by_name.keys()) == len(self.fields)), \
            "All fields must have unique names"

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
        # prev_op key is OPTIONAL
        for key in ['field', 'operator', 'value']:
            if key not in field:
                raise ParseError("Key %s not found in field %r" % (key, field))

        f = self.get_field_by_name(field['field'])
        if f is None:
            raise UnknownField("Field type %r not found!" % field)

        if field['operator'] not in [text(x) for x in f.ops]:
            raise UnknownOperation(
                "Operation %r not valid for field %r" % (
                    field['operator'], field['field']))

        if field.get('prev_op', None) not in [AND, OR, ANDNOT, None]:
            raise UnknownOperation("%r" % field)

        if f.impacts_query(field['value'], field['operator']):
            return f.query_for(field['value'], field['operator'])

    def get_query_recursive(self, data):
        """Recursivley get query, basing on a list of elements.
        """

        ret = None

        for elem in data[1:]:
            if type(elem) == list:
                qobj = self.get_query_recursive(elem)
                prev_op = elem[0]
            else:
                qobj = self.parse_field(elem)
                prev_op = elem.get('prev_op', None)

            if ret is None:
                ret = qobj
                continue

            if prev_op == AND:
                ret = ret & qobj
            elif prev_op == OR:
                ret = ret | qobj
            elif prev_op == ANDNOT:
                ret = ret & ~Q(qobj);
            else:
                raise UnknownOperation(
                    "%s not expected" % elem.get('prev_op', None))

        return ret

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

        if data is None or type(data) == list or 'report_type' not in data:
            return default_retval

        try:
            idx = int(data['report_type'])
        except (ValueError, IndexError, TypeError):
            return default_retval

        try:
            return report_types[idx].id
        except IndexError:
            return default_retval

    def get_query_for_model(self, data, removed_manually=None):
        if data is None:
            return self.model.objects.all()

        # Fix for pre-0.8 versions
        if type(data) != dict:
            data = {'form_data': data}

        if 'form_data' in data:
            query = self.get_query(data['form_data'])
            retval = self.model.objects.filter(query)
        else:
            retval = self.model.objects.all()

        if removed_manually:
            retval = retval.exclude(pk__in=removed_manually)

        sb = []

        ordering  = data.get("ordering")
        if ordering:
            for no, element in enumerate(self.order_boxes):
                key, key_dir = get_ordering_key_name(no)
                if key in ordering:
                    try:
                        sort_idx = int(ordering[key])
                    except (TypeError, ValueError):
                        continue

                    try:
                        srt = self.ordering[sort_idx].field
                    except (IndexError, TypeError, ValueError):
                        continue

                    if not srt:
                        continue

                    if key_dir in ordering and ordering[key_dir] == "1":
                        srt = "-" + srt

                    sb.append(srt)

            if sb:
                retval = retval.order_by(*sb)

        return retval

    def recreate_form_recursive(self, element, info):
        result = []
        info.frame += 1

        current_frame = info.frame

        for elem in element[1:]:
            if type(elem) == list:
                result.append(
                    "$('#frame-%s').multiseekFrame('addFrame', '%s')" % (
                        current_frame, elem[0]))
                result.extend(self.recreate_form_recursive(elem, info))

            else:
                if elem.get("prev_op", None) not in [AND, OR, ANDNOT, None]:
                    raise ParseError("prev_op = %r" % elem.get("prev_op", None))

                prev_op = elem.get('prev_op', None)
                if prev_op == None or prev_op == 'None':
                    prev_op = 'null';
                else:
                    prev_op = "'" + prev_op + "'"
                s = "$('#frame-%i').multiseekFrame('addField', '%s', '%s', '%s', %s)"
                value = self.get_field_by_name(elem['field']).value_to_web(
                    elem['value'])

                result.append(s % (
                    current_frame, elem['field'], elem['operator'], value,
                    prev_op))
                info.field += 1

        return result

    def recreate_form(self, data):
        """Recreate a JavaScript code to create a given form, basing
        on a list.

        :returns: Javascript code to embed on the multiseek form page, which
        will recreate form
        :rtype: safestr
        """

        info = _FrameInfo()
        result = []
        if type(data) != dict:
            raise ParseError

        if 'form_data' in data:
            result = self.recreate_form_recursive(data['form_data'], info)
        foundation = []

        ordering = data.get("ordering")
        if ordering is None:
            if self.default_ordering:
                ordering = self.default_ordering

        if ordering:
            for no, elem in enumerate(self.order_boxes):
                key = "%s%s" % (MULTISEEK_ORDERING_PREFIX, no)
                if key in ordering:
                    result.append(
                        '\t\t'
                        '$("select[name=%s] option").eq(%s).prop("selected", true)' % (
                            key, ordering[key]))
                    # foundation.append(
                    #     '\t\t\t'
                    #     'Foundation.libs.forms.refresh_custom_select($("select[name=%s]"), true)' % key
                    # )
                key = key + "_dir"
                if key in ordering:
                    if ordering[key] == "1":
                        result.append(
                            '\t\t'
                            '$("input[name=%s]").attr("checked", true)' % key)
                        foundation.append(
                            '\t\t\t'
                            '$("input[name=%s]").next().toggleClass("checked", true)' % key
                        )

        if 'report_type' in data:
            if data['report_type']:
                result.append(
                    '\t\t'
                    '$("select[name=%s] option").eq(%s).prop("selected", true)'
                    % (
                        MULTISEEK_REPORT_TYPE, data['report_type']))
                # foundation.append(
                #     '\t\t\t'
                #     'Foundation.libs.forms.refresh_custom_select($("select[name=%s]"), true)' % MULTISEEK_REPORT_TYPE
                # )

        ret = u";\n".join(result) + u";\n"
        if foundation:
            ret += u"\t\tif (window.Foundation) {\n" + u";\n".join(
                foundation) + u"\n\t\t}\n"
        return ret



def create_registry(model, *args, **kw):
    r = MultiseekRegistry()
    r.model = model
    for field in args:
        r.add_field(field)

    known_kwargs =['ordering', 'report_types']
    for arg in known_kwargs:
        if arg in kw:
            setattr(r, arg, kw.pop(arg))

    if 'default_ordering' in kw:
        r.set_default_ordering(*kw.pop("default_ordering"))
    if kw.keys():
        raise Exception("Unknown kwargs passed")
    return r


_cached_registry = {}

def get_registry(registry):
    """
    :rtype: MultiseekRegistry
    """

    if type(registry) is str or type(registry) is unicode:
        if registry not in _cached_registry:
            m = importlib.import_module(registry).registry
            _cached_registry[registry] = m
        return _cached_registry[registry]

    return registry
