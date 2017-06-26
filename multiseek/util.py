# -*- encoding: utf-8 -*-
from builtins import str as text


def make_field(klass, operation, value, prev_op="and"):
    return {
        u'field': text(klass.label),
        u'operator': text(operation),
        u'value': value,
        u'prev_op': prev_op}