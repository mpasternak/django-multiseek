# -*- encoding: utf-8 -*-

from builtins import str as text


def make_field(klass, operation, value, prev_op="and"):
    return {
        'field': text(klass.label),
        'operator': text(operation),
        'value': value,
        'prev_op': prev_op}