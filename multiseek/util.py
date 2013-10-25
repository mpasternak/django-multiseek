# -*- encoding: utf-8 -*-


def make_field(klass, operation, value, prev_op="and"):
    return {
        u'field': unicode(klass.label),
        u'operator': unicode(operation),
        u'value': value,
        u'prev_op': prev_op}